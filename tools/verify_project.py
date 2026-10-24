"""Check project artifacts against the committed SHA-256 manifest (stdlib only)."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "project-files.sha256.json"


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true",
                        help="Regenerate the manifest from Git's staged file list.")
    args = parser.parse_args()
    if args.write:
        tracked = subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=ROOT
        ).decode("utf-8").split("\0")
        if not any(name and name != MANIFEST.name for name in tracked):
            raise RuntimeError("No staged project files. Run git add . first.")
        files = []
        for name in sorted(filter(None, tracked)):
            if name == MANIFEST.name:
                continue
            path = ROOT / name
            files.append({"path": name, "bytes": path.stat().st_size,
                          "sha256": digest(path)})
        MANIFEST.write_text(json.dumps(
            {"schema": 1, "algorithm": "sha256", "files": files},
            ensure_ascii=False, indent=2
        ) + "\n", encoding="utf-8")
        print(f"Wrote manifest: {len(files)} files.")
        return 0

    failures = []
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not data["files"]:
        raise RuntimeError("The project manifest is empty.")
    for item in data["files"]:
        path = ROOT / item["path"]
        if not path.is_file():
            failures.append(f"Missing: {item['path']}")
        elif path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]:
            failures.append(f"Changed: {item['path']}")
    if failures:
        print("\n".join(failures))
        return 1
    print(f"OK: {len(data['files'])} project files verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
