"""BigQuery access to the free public Solana dataset (read-only, sandbox, no billing).

Sign-in is the user's own consent through Google's Cloud CLI (`scripts/gcloud.sh auth
application-default login`); the token stays on D: in data/secrets/gcloud and is revoked with
`scripts/gcloud.sh auth application-default revoke`. Every query is dry-run first and refused
if it would scan more than --max-gb, so the free 1 TiB/month is never exceeded by accident.

    python -m gemtracker.bq --project <id> check
"""
from __future__ import annotations

import argparse
import json

from .config import DATA_DIR

DATASET = "bigquery-public-data.crypto_solana_mainnet_us"
ADC_FILE = DATA_DIR / "secrets" / "gcloud" / "application_default_credentials.json"  # git-ignored
USAGE = DATA_DIR / "history" / "bq_usage.jsonl"


def client(project: str):
    import google.auth
    from google.cloud import bigquery
    if not ADC_FILE.exists():
        raise SystemExit(f"not signed in: run  bash scripts/gcloud.sh auth application-default login")
    creds, _ = google.auth.load_credentials_from_file(str(ADC_FILE), quota_project_id=project)
    return bigquery.Client(project=project, credentials=creds)


def run(bq, sql: str, max_gb: float):
    """Dry-run, refuse above max_gb, then run and log the bytes billed."""
    from google.cloud import bigquery
    dry = bq.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    gb = dry.total_bytes_processed / 1e9
    if gb > max_gb:
        raise SystemExit(f"refused: query would scan {gb:.1f} GB > {max_gb} GB")
    job = bq.query(sql, job_config=bigquery.QueryJobConfig(maximum_bytes_billed=int(max_gb * 1e9)))
    rows = [dict(r) for r in job.result()]
    USAGE.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"job": job.job_id, "gb_billed": (job.total_bytes_billed or 0) / 1e9,
                             "gb_est": gb, "sql": sql[:300]}) + "\n")
    return rows, gb


def check(bq, max_gb: float) -> None:
    """Which tables exist and how fresh they are (metadata queries scan ~0 bytes)."""
    rows, _ = run(bq, f"SELECT table_id, row_count, size_bytes, TIMESTAMP_MILLIS(last_modified_time) AS modified "
                      f"FROM `{DATASET}.__TABLES__` ORDER BY size_bytes DESC", max_gb)
    for r in rows:
        print(f"{r['table_id']:28} rows={r['row_count']:>16,} TB={r['size_bytes'] / 1e12:8.1f} modified={r['modified']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="free BigQuery Solana access, dry-run guarded")
    ap.add_argument("--project", required=True, help="your Google Cloud project id (not a secret)")
    ap.add_argument("--max-gb", type=float, default=50.0, help="refuse any query scanning more than this")
    ap.add_argument("cmd", choices=["check"])
    args = ap.parse_args(argv)
    bq = client(args.project)
    if args.cmd == "check":
        check(bq, args.max_gb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
