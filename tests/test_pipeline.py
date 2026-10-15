import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from commcare_pipeline.client import CommCareClient, SyntheticSource
from commcare_pipeline.loader import connect, flatten, last_sync, load_forms
from commcare_pipeline.quality import run_checks


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, pages):
        self.pages = list(pages)
        self.headers = {}
        self.urls = []

    def get(self, url, params=None, timeout=None):
        self.urls.append(url)
        return FakeResponse(self.pages.pop(0))


class ClientTests(unittest.TestCase):
    def test_follows_pagination_and_sets_auth(self):
        session = FakeSession([
            {"objects": [{"id": "a"}], "meta": {"next": "/a/d/api/v0.5/form/?offset=1"}},
            {"objects": [{"id": "b"}], "meta": {"next": None}},
        ])
        client = CommCareClient("d", "me@x.org", "KEY", session=session)
        ids = [f["id"] for f in client.iter_forms()]
        self.assertEqual(ids, ["a", "b"])
        self.assertEqual(len(session.urls), 2)
        self.assertEqual(session.headers["Authorization"], "ApiKey me@x.org:KEY")


class LoaderTests(unittest.TestCase):
    def test_flatten(self):
        form = next(SyntheticSource(n=1).iter_forms())
        row = flatten(form)
        self.assertEqual(row["form_id"], "form-0000")
        self.assertIn("site", row)

    def test_load_is_idempotent(self):
        conn = connect()
        forms = list(SyntheticSource(n=30).iter_forms())
        load_forms(conn, forms)
        first = conn.execute("SELECT COUNT(*) FROM household_visit").fetchone()[0]
        load_forms(conn, forms)
        second = conn.execute("SELECT COUNT(*) FROM household_visit").fetchone()[0]
        self.assertEqual(first, second)
        self.assertEqual(first, 30)  # duplicate submission collapsed
        self.assertIsNotNone(last_sync(conn))


class QualityTests(unittest.TestCase):
    def test_detects_seeded_problems(self):
        conn = connect()
        load_forms(conn, SyntheticSource(n=50).iter_forms())
        counts = run_checks(conn)
        self.assertGreater(counts["invalid_household_size"], 0)
        self.assertGreater(counts["missing_site"], 0)

    def test_clean_data_has_no_issues(self):
        conn = connect()
        load_forms(conn, [{
            "id": "ok", "received_on": "2026-02-01T10:00:00+00:00",
            "form": {"site": "Nairobi", "household_size": 4, "children_under_5": 1,
                     "visit_date": "2026-02-01", "case": {"@case_id": "c1"}},
            "metadata": {"userID": "u1"},
        }])
        self.assertEqual(sum(run_checks(conn).values()), 0)


if __name__ == "__main__":
    unittest.main()
