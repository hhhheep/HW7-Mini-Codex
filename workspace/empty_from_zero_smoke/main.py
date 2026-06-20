from __future__ import annotations

import argparse


def build_message(name: str, excited: bool = False) -> str:
    suffix = "!" if excited else "."
    return f"Hello, {name}{suffix}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Mini-Codex generated CLI")
    parser.add_argument("name", nargs="?", default="student")
    parser.add_argument("--excited", action="store_true")
    args = parser.parse_args()
    print(build_message(args.name, excited=args.excited))


if __name__ == "__main__":
    main()
