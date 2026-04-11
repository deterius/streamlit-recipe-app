"""Bootstrap a new Grasshopper repository from local scaffold templates.

Usage:
    python helpers/bootstrap_grasshopper_repo.py --target ../grasshopper-scripts
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def copy_tree(src: Path, dst: Path) -> None:
    for path in src.rglob("*"):
        relative = path.relative_to(src)
        out_path = dst / relative
        if path.is_dir():
            out_path.mkdir(parents=True, exist_ok=True)
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap a Grasshopper repo scaffold.")
    parser.add_argument("--target", required=True, help="Target directory for scaffold output")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into an existing non-empty directory",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    scaffold_dir = repo_root / "scaffolds" / "grasshopper-scripts"
    target = Path(args.target).expanduser().resolve()

    if not scaffold_dir.exists():
        raise SystemExit(f"Scaffold not found: {scaffold_dir}")

    target.mkdir(parents=True, exist_ok=True)

    if any(target.iterdir()) and not args.force:
        raise SystemExit(
            "Target directory is not empty. Use --force to copy scaffold into an existing directory."
        )

    copy_tree(scaffold_dir, target)
    print(f"✅ Scaffold copied to: {target}")
    print("Next steps:")
    print("  1) cd <target>")
    print("  2) git init")
    print("  3) git add . && git commit -m 'chore: initial scaffold'")


if __name__ == "__main__":
    main()
