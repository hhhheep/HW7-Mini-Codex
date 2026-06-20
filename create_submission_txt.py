from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the HW7 submission TXT file.")
    parser.add_argument("--student-id", required=True, help="Student ID used in the required filename.")
    parser.add_argument("--link", required=True, help="Public GitHub repository link or Google Drive sharing link.")
    parser.add_argument(
        "--link-kind",
        choices=("github", "drive"),
        default="github",
        help="Whether --link points to a GitHub repository or Google Drive folder.",
    )
    parser.add_argument(
        "--demo",
        required=True,
        help="Demo video/screenshot filename or public sharing link.",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"{args.student_id}_HW7.txt"
    label = "GitHub repository" if args.link_kind == "github" else "Google Drive folder"
    content = "\n".join(
        [
            f"{label}: {args.link}",
            f"Demo material: {args.demo}",
            "Project title: Agentic Generative AI Experiment Orchestrator",
            "",
        ]
    )
    output_path.write_text(content, encoding="utf-8")
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
