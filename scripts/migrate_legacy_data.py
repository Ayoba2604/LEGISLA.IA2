from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_DIR = ROOT / "IA" / "data"


def main() -> None:
    files = ["base_juridica.json", "situacoes.json", "contratos.json"]
    report = {}
    for name in files:
        path = LEGACY_DIR / name
        if not path.exists():
            report[name] = {"exists": False, "count": 0}
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        report[name] = {"exists": True, "count": len(data)}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

