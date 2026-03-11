from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from subprocess import run
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a PostgreSQL/pgvector backup for the current runtime.")
    parser.add_argument("--database-url", default=settings.database_url, help="SQLAlchemy PostgreSQL URL.")
    parser.add_argument("--output-dir", type=Path, default=settings.backup_output_dir, help="Backup output directory.")
    parser.add_argument("--docker-container", help="Optional container name to execute pg_dump inside Docker.")
    parser.add_argument("--pg-dump-binary", default=settings.pg_dump_binary, help="Local pg_dump binary path.")
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("DATABASE_URL nao configurada.")

    parsed = parse_database_url(args.database_url)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dump_path = args.output_dir / f"{parsed['database']}-{timestamp}.dump"
    metadata_path = args.output_dir / f"{parsed['database']}-{timestamp}.json"

    if args.docker_container:
        command = [
            "docker",
            "exec",
            "-e",
            f"PGPASSWORD={parsed['password'] or ''}",
            args.docker_container,
            "pg_dump",
            "-U",
            parsed["username"],
            "-d",
            parsed["database"],
            "-Fc",
        ]
    else:
        command = [args.pg_dump_binary, args.database_url, "-Fc"]

    with dump_path.open("wb") as dump_file:
        result = run(command, check=False, stdout=dump_file, stderr=-1)
    if result.returncode != 0:
        if dump_path.exists():
            dump_path.unlink()
        raise SystemExit(result.stderr.decode("utf-8", errors="ignore") or "Falha ao executar pg_dump.")

    metadata = {
        "created_at": timestamp,
        "database": parsed["database"],
        "host": parsed["hostname"],
        "port": parsed["port"],
        "docker_container": args.docker_container,
        "dump_file": str(dump_path),
        "command": command[:-1] + ["-Fc"],
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


def parse_database_url(database_url: str) -> dict[str, str | int | None]:
    normalized = database_url.replace("postgresql+psycopg://", "postgresql://")
    parsed = urlparse(normalized)
    return {
        "hostname": parsed.hostname,
        "port": parsed.port or 5432,
        "username": parsed.username or "postgres",
        "password": parsed.password,
        "database": parsed.path.lstrip("/"),
    }


if __name__ == "__main__":
    main()
