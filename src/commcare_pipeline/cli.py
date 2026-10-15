"""Command line entry point: python -m commcare_pipeline.cli --source synthetic"""
from __future__ import annotations

import argparse
import os

from .client import CommCareClient, SyntheticSource
from .loader import connect, last_sync, load_forms
from .quality import run_checks


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Sync CommCare forms to SQL and run data quality checks")
    p.add_argument("--source", choices=["synthetic", "commcare"], default="synthetic")
    p.add_argument("--db", default="pipeline.db")
    args = p.parse_args(argv)

    conn = connect(args.db)
    if args.source == "commcare":
        source = CommCareClient(
            os.environ["COMMCARE_DOMAIN"],
            os.environ["COMMCARE_USERNAME"],
            os.environ["COMMCARE_API_KEY"],
        )
    else:
        source = SyntheticSource()

    loaded = load_forms(conn, source.iter_forms(received_after=last_sync(conn)))
    print(f"Loaded {loaded} forms into {args.db}")
    for rule, n in run_checks(conn).items():
        print(f"  DQ {rule}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
