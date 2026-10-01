"""Export installed versions for advisory lookup, documenting CPU-wheel mapping."""
import argparse
from importlib.metadata import distributions
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, help="Optional installed site-packages directory")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to(ROOT / "outputs"):
        raise ValueError("Reports must stay under infra/outputs")
    packages = {}
    mapping = []
    excluded = []
    for package in distributions(path=[str(args.path)] if args.path else None):
        name, version = package.metadata["Name"], package.version
        normalized_name = re.sub(r"[-_.]+", "-", name).lower()
        if normalized_name == "sanjeevani-member4":
            excluded.append({"name": name, "reason": "Unpublished local package; third-party dependencies retained"})
            continue
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or not re.fullmatch(r"[A-Za-z0-9_.+!-]+", version):
            raise ValueError("Invalid distribution metadata")
        if "+" in version:
            if normalized_name != "torch" or version.split("+", 1)[1] != "cpu":
                raise ValueError("Unrecognized local version cannot be silently mapped")
            mapping.append({"name": name, "installed": version, "advisory_version": version.split("+", 1)[0],
                            "limitation": "Upstream version lookup; not a CPU-wheel-specific security assessment"})
            version = version.split("+", 1)[0]
        if normalized_name in packages:
            raise ValueError("Duplicate installed distribution")
        packages[normalized_name] = version
    if not packages:
        raise ValueError("No installed packages found")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(f"{name}=={version}\n" for name, version in sorted(packages.items())), encoding="utf-8")
    target.with_suffix(".mapping.json").write_text(json.dumps({"mapping": mapping, "excluded": excluded}, indent=2), encoding="utf-8")
    print(f"Exported {len(packages)} versions; {len(mapping)} documented CPU-wheel mappings.")


if __name__ == "__main__":
    main()
