#!/usr/bin/env python3
"""
Generic breaking change detector for Python dependencies.
Checks GitHub releases for BREAKING keywords.

Usage:
    python check_breaking_changes.py --owner nautechsystems --repo nautilus_trader --current 1.200.0
    python check_breaking_changes.py --owner nautechsystems --repo nautilus_trader --current 1.200.0 --target 1.210.0
    python check_breaking_changes.py --owner nautechsystems --repo nautilus_trader --current 1.200.0 --output json
"""

import argparse
import json
import os
import sys

try:
    import requests
    from packaging import version
except ImportError:
    print("Missing dependencies. Install with: pip install requests packaging")
    sys.exit(1)

try:
    import tomllib
except ImportError:
    import tomli as tomllib

BREAKING_KEYWORDS = [
    "BREAKING",
    "BREAKING CHANGE",
    "BREAKING-CHANGE",
    "BREAKING:",
    "REMOVED",
    "DEPRECATED AND REMOVED",
    "INCOMPATIBLE",
    "MIGRATION REQUIRED",
]


def get_current_version(package: str, pyproject_path: str = "pyproject.toml") -> str | None:
    """Get current version from pyproject.toml or requirements.txt."""
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            deps = data.get("project", {}).get("dependencies", [])
            for dep in deps:
                if package.lower() in dep.lower():
                    for op in ["==", ">=", "<=", "~=", ">", "<"]:
                        if op in dep:
                            return dep.split(op)[1].strip().split(",")[0].split(";")[0].strip()
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Warning: Could not parse {pyproject_path}: {e}", file=sys.stderr)
    return None


def get_releases(owner: str, repo: str, token: str | None = None) -> list:
    """Fetch releases from GitHub API."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    params = {"per_page": 100}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching releases: {e}", file=sys.stderr)
        return []


def parse_version_safe(ver_str: str) -> version.Version | None:
    """Safely parse a version string."""
    try:
        return version.parse(ver_str.lstrip("v"))
    except Exception:
        return None


def check_breaking_changes(
    owner: str,
    repo: str,
    current: str,
    target: str | None = None,
    token: str | None = None,
) -> dict:
    """Check for breaking changes between versions."""
    releases = get_releases(owner, repo, token)

    if not releases:
        return {
            "package": f"{owner}/{repo}",
            "current": current,
            "target": target,
            "error": "No releases found or API error",
            "breaking_count": 0,
            "total_releases": 0,
            "breaking_changes": [],
            "all_changes": [],
        }

    breaking = []
    all_changes = []

    current_ver = parse_version_safe(current)
    target_ver = parse_version_safe(target) if target else None

    if not current_ver:
        return {
            "package": f"{owner}/{repo}",
            "current": current,
            "target": target,
            "error": f"Invalid current version: {current}",
            "breaking_count": 0,
            "total_releases": 0,
            "breaking_changes": [],
            "all_changes": [],
        }

    for release in releases:
        tag = release.get("tag_name", "").lstrip("v")
        release_ver = parse_version_safe(tag)

        if not release_ver:
            continue

        # Check if release is between current and target
        if release_ver <= current_ver:
            continue
        if target_ver and release_ver > target_ver:
            continue

        body = release.get("body", "") or ""
        name = release.get("name", "") or ""

        # Check for breaking keywords in body and name
        text_to_check = f"{name} {body}".upper()
        is_breaking = any(kw.upper() in text_to_check for kw in BREAKING_KEYWORDS)

        # Also check for common breaking change patterns
        if not is_breaking:
            is_breaking = "MAJOR VERSION" in text_to_check or "API CHANGE" in text_to_check

        change = {
            "version": tag,
            "name": release.get("name", tag),
            "breaking": is_breaking,
            "url": release.get("html_url"),
            "published_at": release.get("published_at"),
            "notes": body[:500] + "..." if len(body) > 500 else body,
        }

        all_changes.append(change)
        if is_breaking:
            breaking.append(change)

    return {
        "package": f"{owner}/{repo}",
        "current": current,
        "target": target or "latest",
        "breaking_count": len(breaking),
        "total_releases": len(all_changes),
        "breaking_changes": breaking,
        "all_changes": all_changes,
    }


def print_text_report(result: dict) -> None:
    """Print human-readable report."""
    print(f"\n{'=' * 60}")
    print(f"Breaking Change Report: {result['package']}")
    print(f"{'=' * 60}")
    print(f"Current: {result['current']}")
    print(f"Target:  {result['target']}")
    print(f"Releases checked: {result['total_releases']}")
    print(f"Breaking changes: {result['breaking_count']}")

    if result.get("error"):
        print(f"\nError: {result['error']}")
        return

    if result["breaking_changes"]:
        print(f"\n{'!' * 60}")
        print("BREAKING CHANGES DETECTED:")
        print(f"{'!' * 60}")
        for bc in result["breaking_changes"]:
            print(f"\n  Version {bc['version']}:")
            print(f"  Name: {bc['name']}")
            print(f"  URL: {bc['url']}")
            print(f"  Published: {bc.get('published_at', 'N/A')}")
            if bc["notes"]:
                # Show first 200 chars of notes
                notes_preview = bc["notes"][:200].replace("\n", "\n    ")
                print(f"  Notes: {notes_preview}...")
    else:
        print(f"\n{'=' * 60}")
        print("No breaking changes detected")
        print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(
        description="Check for breaking changes in GitHub dependencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --owner nautechsystems --repo nautilus_trader --current 1.200.0
  %(prog)s --owner nautechsystems --repo nautilus_trader --current 1.200.0 --target 1.210.0
  %(prog)s --owner pydantic --repo pydantic --current 2.0.0 --output json
        """,
    )
    parser.add_argument("--owner", required=True, help="GitHub owner (e.g., nautechsystems)")
    parser.add_argument("--repo", required=True, help="GitHub repo (e.g., nautilus_trader)")
    parser.add_argument("--current", required=True, help="Current version (e.g., 1.200.0)")
    parser.add_argument("--target", help="Target version (optional, defaults to latest)")
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token for API rate limits (default: $GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with code 1 if breaking changes found",
    )

    args = parser.parse_args()

    result = check_breaking_changes(
        owner=args.owner,
        repo=args.repo,
        current=args.current,
        target=args.target,
        token=args.token,
    )

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print_text_report(result)

    if args.fail_on_breaking and result["breaking_count"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
