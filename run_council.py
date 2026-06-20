from __future__ import annotations

import argparse
from pathlib import Path

from assignment_core.model_client import ModelClientError
from assignment_core.runner import run_workflow


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the HW7 agentic generative AI experiment orchestrator.")
    parser.add_argument("--idea", help="Project idea text.")
    parser.add_argument("--idea-file", type=Path, help="Path to a text file containing the project idea.")
    parser.add_argument("--output", type=Path, default=Path("outputs/demo_run"), help="Output directory.")
    parser.add_argument("--mode", choices=("mock_test", "api"), default="mock_test")
    args = parser.parse_args()

    if args.idea_file:
        project_idea = args.idea_file.read_text(encoding="utf-8")
    elif args.idea:
        project_idea = args.idea
    else:
        parser.error("Provide --idea or --idea-file.")

    try:
        payload = run_workflow(project_idea=project_idea, output_dir=args.output, mode=args.mode)
    except ModelClientError as exc:
        parser.exit(2, f"API mode failed: {exc}\n")
    print(f"wrote {args.output / 'run.json'}")
    print(f"stages {len(payload['agent_outputs']) + 3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
