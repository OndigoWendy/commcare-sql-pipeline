"""CommCare HQ Form API client with pagination, plus a synthetic data source."""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Iterator

import requests

BASE_URL = "https://www.commcarehq.org"


class CommCareClient:
    """Reads submitted forms from the CommCare HQ Form API (v0.5)."""

    def __init__(self, domain: str, username: str, api_key: str, session=None, page_size: int = 100):
        self.domain = domain
        self.page_size = page_size
        self.session = session or requests.Session()
        self.session.headers["Authorization"] = f"ApiKey {username}:{api_key}"

    def iter_forms(self, received_after: str | None = None) -> Iterator[dict]:
        params = {"limit": self.page_size, "order_by": "received_on"}
        if received_after:
            params["received_on_start"] = received_after
        url = f"{BASE_URL}/a/{self.domain}/api/v0.5/form/"
        while url:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            yield from payload.get("objects", [])
            next_path = (payload.get("meta") or {}).get("next")
            url = f"{BASE_URL}{next_path}" if next_path else None
            params = None  # the next link already carries the query string


class SyntheticSource:
    """Generates fake household-visit forms shaped like CommCare form JSON.

    Includes a few deliberately bad records so the data quality checks have
    something to find. No real data is used.
    """

    SITES = ["Nairobi", "Kisumu", "Mombasa", "Garissa"]

    def __init__(self, n: int = 50, seed: int = 7):
        self.n = n
        self.rng = random.Random(seed)

    def iter_forms(self, received_after: str | None = None) -> Iterator[dict]:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for i in range(self.n):
            received = start + timedelta(hours=i * 6)
            form = {
                "id": f"form-{i:04d}",
                "form": {
                    "@name": "Household Visit",
                    "case": {"@case_id": f"case-{i % 30:03d}"},
                    "site": self.rng.choice(self.SITES),
                    "household_size": self.rng.randint(1, 9),
                    "children_under_5": self.rng.randint(0, 3),
                    "visit_date": received.date().isoformat(),
                },
                "received_on": received.isoformat(),
                "metadata": {"userID": f"user-{i % 5}"},
            }
            if i % 17 == 0:
                form["form"]["household_size"] = -1  # invalid
            if i % 23 == 0:
                form["form"]["site"] = ""  # missing
            if i == 10:
                yield dict(form)  # duplicate submission follows
            yield form
