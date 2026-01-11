#!/usr/bin/env python3
"""
Architecture Drift Detector

Detects when actual configurations drift from canonical.yaml (SSOT).
Run manually or as pre-commit hook to keep documentation in sync.

Usage:
    python scripts/architecture_drift_detector.py          # Check for drift
    python scripts/architecture_drift_detector.py --fix    # Auto-update derived files
    python scripts/architecture_drift_detector.py --json   # JSON output for CI

SSOT (Single Source of Truth):
    config/canonical.yaml - All configuration values are defined here.
    Derived files (.env, docker-compose.yml, ARCHITECTURE.md) must match.

Monitors:
    - Port configurations (QuestDB, Grafana, Redis)
    - Container versions
    - NautilusTrader version
    - Catalog paths
    - QuestDB tables
"""

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # Will use regex fallback


# =============================================================================
# SSOT Loader
# =============================================================================


def load_canonical_config(project_root: Path) -> dict:
    """Load canonical.yaml as SSOT.

    Returns dict with all canonical values, or empty dict if not found.
    """
    canonical_path = project_root / "config" / "canonical.yaml"

    if not canonical_path.exists():
        print(f"WARNING: SSOT file not found: {canonical_path}")
        return {}

    content = canonical_path.read_text()

    if yaml:
        return yaml.safe_load(content)
    else:
        # Regex fallback for basic parsing (no PyYAML installed)
        config = {"ports": {}, "versions": {}, "nautilus": {}, "paths": {}}
        for match in re.finditer(r"(\w+):\s*[\"']?([^\s\"'\n#]+)", content):
            key, val = match.groups()
            if key in ("questdb_ilp", "questdb_http", "grafana", "redis"):
                config["ports"][key] = int(val)
            elif key in ("version", "python"):
                config["nautilus"][key] = val
            elif key == "catalog":
                config["paths"]["catalog"] = val
        return config


def build_tracked_configs(canonical: dict) -> list[dict]:
    """Build TRACKED_CONFIGS from canonical.yaml values.

    This is the bridge between SSOT (canonical.yaml) and the detector logic.
    """
    configs = []
    ports = canonical.get("ports", {})
    versions = canonical.get("versions", {})
    nautilus = canonical.get("nautilus", {})
    paths = canonical.get("paths", {})

    # Ports
    if "questdb_ilp" in ports:
        configs.append(
            {
                "name": "QUESTDB_ILP_PORT",
                "source_pattern": rf":{ports['questdb_ilp']}",
                "arch_pattern": r"\|\s*QUESTDB_ILP_PORT\s*\|[^|]+\|\s*(\d+)",
                "canonical_value": str(ports["questdb_ilp"]),
                "sources": [".env", "monitoring/docker-compose.yml"],
            }
        )
    if "questdb_http" in ports:
        configs.append(
            {
                "name": "QUESTDB_HTTP_PORT",
                "source_pattern": rf":{ports['questdb_http']}",
                "arch_pattern": r"\|\s*QUESTDB_HTTP_PORT\s*\|[^|]+\|\s*(\d+)",
                "canonical_value": str(ports["questdb_http"]),
                "sources": [".env", "monitoring/docker-compose.yml"],
            }
        )
    if "grafana" in ports:
        configs.append(
            {
                "name": "GRAFANA_PORT",
                "source_pattern": rf":{ports['grafana']}",
                "arch_pattern": r"\|\s*GRAFANA_PORT\s*\|[^|]+\|\s*(\d+)",
                "canonical_value": str(ports["grafana"]),
                "sources": [".env", "monitoring/docker-compose.yml"],
            }
        )
    if "redis" in ports:
        configs.append(
            {
                "name": "REDIS_PORT",
                "source_pattern": rf":{ports['redis']}",
                "arch_pattern": r"\|\s*REDIS_PORT\s*\|[^|]+\|\s*(\d+)",
                "canonical_value": str(ports["redis"]),
                "sources": [".env", "config/cache/docker-compose.redis.yml"],
            }
        )

    # Versions
    if nautilus.get("version"):
        configs.append(
            {
                "name": "NAUTILUS_VERSION",
                "source_pattern": r"v?1\.\d{3}\.\d+\+?",
                "arch_pattern": r"\|\s*NAUTILUS_VERSION\s*\|[^|]+\|\s*([^\s|]+)",
                "canonical_value": nautilus["version"],
                "sources": [],  # Version from installed package
            }
        )
    if nautilus.get("python"):
        configs.append(
            {
                "name": "PYTHON_VERSION",
                "source_pattern": r'python\s*=\s*["\']([^"\']+)["\']',
                "arch_pattern": r"\|\s*PYTHON_VERSION\s*\|[^|]+\|\s*([^\s|]+)",
                "canonical_value": nautilus["python"],
                "sources": ["pyproject.toml"],
            }
        )
    if paths.get("catalog"):
        configs.append(
            {
                "name": "CATALOG_PATH",
                "source_pattern": r"NAUTILUS_CATALOG_PATH=([^\s]+)",
                "arch_pattern": r"\|\s*CATALOG_PATH\s*\|[^|]+\|\s*([^\s|]+)",
                "canonical_value": paths["catalog"],
                "sources": [".env"],
            }
        )

    # Container versions
    if versions.get("grafana"):
        configs.append(
            {
                "name": "GRAFANA_VERSION",
                "source_pattern": r"grafana[:/]v?(\d+\.\d+\.\d+)",
                "arch_pattern": r"\|\s*GRAFANA_VERSION\s*\|[^|]+\|\s*([^\s|]+)",
                "canonical_value": versions["grafana"],
                "sources": ["monitoring/docker-compose.yml"],
            }
        )
    if versions.get("questdb"):
        configs.append(
            {
                "name": "QUESTDB_VERSION",
                "source_pattern": r"questdb[:/]v?(\d+\.\d+\.\d+)",
                "arch_pattern": r"\|\s*QUESTDB_VERSION\s*\|[^|]+\|\s*([^\s|]+)",
                "canonical_value": versions["questdb"],
                "sources": ["monitoring/docker-compose.yml"],
            }
        )

    return configs


@dataclass
class ConfigValue:
    """A tracked configuration value."""

    name: str
    documented: str | None  # Value in ARCHITECTURE.md
    actual: str | None  # Value from code/env
    source: str  # Where we found the actual value
    line_in_arch: int | None = None  # Line number in ARCHITECTURE.md


@dataclass
class DriftReport:
    """Report of all detected drift."""

    matches: list[ConfigValue] = field(default_factory=list)
    drifts: list[ConfigValue] = field(default_factory=list)
    missing_docs: list[ConfigValue] = field(default_factory=list)
    missing_actual: list[ConfigValue] = field(default_factory=list)
    missing_tables: list[str] = field(default_factory=list)
    extra_tables: list[str] = field(default_factory=list)
    pyproject_mismatches: list[tuple[str, str, str, str]] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return len(self.drifts) > 0 or len(self.missing_docs) > 0

    @property
    def has_schema_drift(self) -> bool:
        return len(self.missing_tables) > 0

    @property
    def has_pyproject_drift(self) -> bool:
        return len(self.pyproject_mismatches) > 0


# =============================================================================
# TRACKED_CONFIGS - Loaded dynamically from config/canonical.yaml (SSOT)
# =============================================================================
# See build_tracked_configs() and load_canonical_config() above.
# Hardcoded fallback only used if canonical.yaml is missing.

TRACKED_CONFIGS_FALLBACK = [
    {
        "name": "QUESTDB_ILP_PORT",
        "source_pattern": r":9009",
        "arch_pattern": r"\|\s*QUESTDB_ILP_PORT\s*\|[^|]+\|\s*(\d+)",
        "canonical_value": "9009",
        "sources": [".env", "monitoring/docker-compose.yml"],
    },
]

# Database tables to track (loaded from canonical.yaml, fallback here)
TRACKED_TABLES_FALLBACK = [
    "trading_pnl",
    "trading_orders",
    "trading_risk",
    "trading_errors",
    "system_health",
    "ralph_iterations",
    "agent_spawns",
]

# All documentation files that may contain config references
# NOTE: ARCHITECTURE.md excluded - it's the canonical source
DOC_FILES_TO_SCAN = [
    "docs/runbooks/*.md",
    "docs/getting_started/*.md",
    "docs/guides/*.md",
    "monitoring/README.md",
    "monitoring/grafana/*.md",
    "specs/*/spec.md",
    "specs/*/quickstart.md",
    "CLAUDE.md",
]


@dataclass
class DocDrift:
    """Drift found in a documentation file."""

    file: str
    line_num: int
    config_name: str
    found_value: str
    canonical_value: str


class ArchitectureDriftDetector:
    """Detects drift between code and documentation.

    Uses config/canonical.yaml as SSOT (Single Source of Truth).
    All other files must match the canonical values.
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.arch_file = project_root / "docs" / "ARCHITECTURE.md"
        self.arch_content = ""
        self.arch_lines: list[str] = []
        self.doc_drifts: list[DocDrift] = []

        # Load SSOT from canonical.yaml
        self.canonical = load_canonical_config(project_root)
        if self.canonical:
            self.tracked_configs = build_tracked_configs(self.canonical)
            self.tracked_tables = self.canonical.get("questdb_tables", TRACKED_TABLES_FALLBACK)
        else:
            self.tracked_configs = TRACKED_CONFIGS_FALLBACK
            self.tracked_tables = TRACKED_TABLES_FALLBACK

    def load_architecture(self) -> bool:
        """Load ARCHITECTURE.md content."""
        if not self.arch_file.exists():
            print(f"ERROR: {self.arch_file} not found")
            return False
        self.arch_content = self.arch_file.read_text()
        self.arch_lines = self.arch_content.split("\n")
        return True

    def scan_all_docs(self) -> list[DocDrift]:
        """Scan all documentation files for outdated config references."""
        drifts = []

        for pattern in DOC_FILES_TO_SCAN:
            if "*" in pattern:
                files = list(self.project_root.glob(pattern))
            else:
                files = [self.project_root / pattern]

            for file_path in files:
                if not file_path.exists():
                    continue

                try:
                    content = file_path.read_text()
                    lines = content.split("\n")

                    for config in self.tracked_configs:
                        canonical = config.get("canonical_value", "")
                        if not canonical:
                            continue

                        # Look for outdated values using source_pattern
                        for i, line in enumerate(lines):
                            match = re.search(config["source_pattern"], line)
                            if match:
                                # Use captured group if available, else full match
                                found = match.group(1) if match.lastindex else match.group(0)
                                # Normalize for comparison (remove Python prefix, operators, etc.)
                                found_norm = re.sub(
                                    r"(?i)python[=\s:\"']*|[v:>=<~^+]", "", found
                                ).strip()
                                canonical_norm = re.sub(
                                    r"(?i)python[=\s:\"']*|[v:>=<~^+]", "", canonical
                                ).strip()

                                # Skip if normalized values match or found satisfies canonical
                                if found_norm == canonical_norm:
                                    continue
                                if canonical_norm in found_norm or found_norm in canonical_norm:
                                    continue

                                # For version comparisons, check if found satisfies canonical
                                try:
                                    found_parts = [
                                        int(x) for x in found_norm.split(".") if x.isdigit()
                                    ]
                                    canon_parts = [
                                        int(x) for x in canonical_norm.split(".") if x.isdigit()
                                    ]
                                    if len(found_parts) >= 2 and len(canon_parts) >= 2:
                                        # If canonical is >= requirement, found >= canon is OK
                                        if ">=" in canonical:
                                            if found_parts >= canon_parts:
                                                continue
                                        # Otherwise only report if found is strictly older
                                        elif found_parts >= canon_parts:
                                            continue
                                except (ValueError, IndexError):
                                    pass

                                drifts.append(
                                    DocDrift(
                                        file=str(file_path.relative_to(self.project_root)),
                                        line_num=i + 1,
                                        config_name=config["name"],
                                        found_value=found,
                                        canonical_value=canonical,
                                    )
                                )
                except Exception:
                    continue

        self.doc_drifts = drifts
        return drifts

    def extract_from_architecture(
        self, name: str, arch_pattern: str
    ) -> tuple[str | None, int | None]:
        r"""Extract a value from ARCHITECTURE.md using arch_pattern.

        The arch_pattern should be a regex with a capture group for the value.
        E.g., r'\|\s*QUESTDB_ILP_PORT\s*\|[^|]+\|\s*(\d+)' captures '9009'.
        """
        for i, line in enumerate(self.arch_lines):
            # Only search lines that contain the config name (optimization)
            if name in line:
                match = re.search(arch_pattern, line, re.IGNORECASE)
                if match:
                    # Return captured group if available, else full match
                    value = match.group(1) if match.lastindex else match.group(0)
                    return value.strip(), i + 1
        return None, None

    def extract_from_source(
        self, sources: list[str], source_pattern: str
    ) -> tuple[str | None, str | None]:
        r"""Extract a value from source files using source_pattern.

        The source_pattern can have a capture group for the value.
        E.g., r'NAUTILUS_CATALOG_PATH=([^\s]+)' captures the path.
        """
        for source_file in sources:
            # Handle glob patterns
            if "*" in source_file:
                files = list(self.project_root.glob(source_file))
            else:
                files = [self.project_root / source_file]

            for file_path in files:
                if file_path.exists():
                    try:
                        content = file_path.read_text()
                        match = re.search(source_pattern, content, re.IGNORECASE)
                        if match:
                            # Return captured group if available, else full match
                            value = match.group(1) if match.lastindex else match.group(0)
                            return value.strip(), str(file_path.relative_to(self.project_root))
                    except Exception:
                        continue

        return None, None

    def extract_nautilus_version(self) -> tuple[str | None, str]:
        """Extract NautilusTrader version from installed package."""
        try:
            result = subprocess.run(
                ["python", "-c", "import nautilus_trader; print(nautilus_trader.__version__)"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip(), "installed package"
        except Exception:
            pass
        return None, "not found"

    def extract_pyproject_versions(self) -> dict[str, str]:
        """Extract version requirements from pyproject.toml."""
        versions = {}
        pyproject = self.project_root / "pyproject.toml"

        if not pyproject.exists():
            return versions

        try:
            content = pyproject.read_text()

            # Python version
            match = re.search(r'python\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                versions["PYTHON_VERSION"] = match.group(1)

            # NautilusTrader version (from dependencies)
            match = re.search(
                r"nautilus[_-]trader\s*(?:>=|==|~=)\s*([0-9]+\.[0-9]+\.[0-9]+)", content
            )
            if match:
                versions["NAUTILUS_VERSION"] = match.group(1)

        except Exception:
            pass

        return versions

    def check_pyproject_sync(self) -> list[tuple[str, str, str, str]]:
        """Check if pyproject.toml versions match installed and documented.

        Returns:
            List of (name, pyproject_val, installed_val, doc_val) tuples for mismatches
        """
        mismatches = []
        pyproject_versions = self.extract_pyproject_versions()

        for name, pyproject_val in pyproject_versions.items():
            # Get installed value
            if name == "NAUTILUS_VERSION":
                installed_val, _ = self.extract_nautilus_version()
            elif name == "PYTHON_VERSION":
                installed_val = f"{sys.version_info.major}.{sys.version_info.minor}"
            else:
                installed_val = None

            # Get documented value from ARCHITECTURE.md
            doc_val = None
            for config in self.tracked_configs:
                if config["name"] == name:
                    doc_val, _ = self.extract_from_architecture(name, config["arch_pattern"])
                    break

            # Check for mismatches (normalize for comparison)
            def normalize(v):
                if not v:
                    return None
                # Remove operators and trailing +
                return re.sub(r"[>=<~^+]", "", str(v)).strip()

            def version_satisfies(requirement: str, actual: str) -> bool:
                """Check if actual version satisfies requirement (e.g., >=3.11 satisfied by 3.12)."""
                if not requirement or not actual:
                    return True
                req_norm = normalize(requirement)
                act_norm = normalize(actual)
                if not req_norm or not act_norm:
                    return True
                # If requirement has >= or similar, check if actual >= requirement
                if ">=" in str(requirement):
                    try:
                        req_parts = [int(x) for x in req_norm.split(".")]
                        act_parts = [int(x) for x in act_norm.split(".")]
                        return act_parts >= req_parts
                    except ValueError:
                        pass
                # Otherwise check if normalized versions match
                return req_norm in act_norm or act_norm in req_norm

            # Only report if installed doesn't satisfy pyproject requirement
            if not version_satisfies(pyproject_val, installed_val):
                mismatches.append((name, pyproject_val, installed_val or "?", doc_val or "?"))

        return mismatches

    def check_questdb_tables(
        self, host: str = "localhost", port: int = 9000
    ) -> tuple[list[str], list[str]]:
        """Check if required QuestDB tables exist.

        Returns:
            Tuple of (missing_tables, extra_tables)
        """
        import urllib.request

        missing = []
        extra = []

        try:
            url = f"http://{host}:{port}/exec?query=SHOW%20TABLES"
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read())

            existing = {row[0] for row in data.get("dataset", [])}

            for table in self.tracked_tables:
                if table not in existing:
                    missing.append(table)

            # Check for unexpected trading tables (potential drift)
            for table in existing:
                if table.startswith(("trading_", "ralph_", "agent_")):
                    if table not in self.tracked_tables:
                        extra.append(table)

        except Exception:
            # QuestDB not reachable, skip table check
            pass

        return missing, extra

    def detect_drift(self) -> DriftReport:
        """Detect all configuration drift."""
        report = DriftReport()

        if not self.load_architecture():
            return report

        for config in self.tracked_configs:
            name = config["name"]
            arch_pattern = config["arch_pattern"]
            source_pattern = config["source_pattern"]
            sources = config["sources"]

            # Get documented value from ARCHITECTURE.md table
            doc_value, doc_line = self.extract_from_architecture(name, arch_pattern)

            # Get actual value from source files
            if name == "NAUTILUS_VERSION":
                actual_value, source = self.extract_nautilus_version()
            else:
                actual_value, source = self.extract_from_source(sources, source_pattern)

            cv = ConfigValue(
                name=name,
                documented=doc_value,
                actual=actual_value,
                source=source or "not found",
                line_in_arch=doc_line,
            )

            # Classify (with smart version comparison)
            if doc_value and actual_value:
                # Normalize for comparison (remove v, +, operators)
                doc_norm = re.sub(r"[v>=<~^+]", "", str(doc_value)).strip()
                actual_norm = re.sub(r"[v>=<~^+]", "", str(actual_value)).strip()

                if doc_norm == actual_norm or doc_norm in actual_norm or actual_norm in doc_norm:
                    report.matches.append(cv)
                else:
                    report.drifts.append(cv)
            elif actual_value and not doc_value:
                report.missing_docs.append(cv)
            elif doc_value and not actual_value:
                report.missing_actual.append(cv)

        # Check QuestDB tables
        missing_tables, extra_tables = self.check_questdb_tables()
        report.missing_tables = missing_tables
        report.extra_tables = extra_tables

        # Check pyproject.toml sync (triple comparison)
        report.pyproject_mismatches = self.check_pyproject_sync()

        return report

    def print_report(self, report: DriftReport) -> None:
        """Print human-readable report."""
        print("\n" + "=" * 60)
        print("  Architecture Drift Report")
        print("=" * 60 + "\n")

        if report.matches:
            print("✅ IN SYNC:")
            for cv in report.matches:
                print(f"   {cv.name}: {cv.actual}")
            print()

        if report.drifts:
            print("⚠️  DRIFT DETECTED:")
            for cv in report.drifts:
                print(f"   {cv.name}:")
                print(f"      Documented: {cv.documented} (line {cv.line_in_arch})")
                print(f"      Actual:     {cv.actual} ({cv.source})")
            print()

        if report.missing_docs:
            print("📝 MISSING FROM DOCS:")
            for cv in report.missing_docs:
                print(f"   {cv.name}: {cv.actual} ({cv.source})")
            print()

        if report.missing_actual:
            print("❓ NOT FOUND IN CODE:")
            for cv in report.missing_actual:
                print(f"   {cv.name}: documented as {cv.documented}")
            print()

        # Print pyproject sync issues
        if report.pyproject_mismatches:
            print("📦 PYPROJECT.TOML MISMATCH:")
            for name, py_val, inst_val, doc_val in report.pyproject_mismatches:
                print(f"   {name}:")
                print(f"      pyproject.toml: {py_val}")
                print(f"      installed:      {inst_val}")
                print(f"      ARCHITECTURE:   {doc_val}")
            print()

        # Print table drift
        if report.missing_tables:
            print("🗄️  MISSING TABLES (QuestDB):")
            for table in report.missing_tables:
                print(f"   - {table}")
            print()

        if report.extra_tables:
            print("🆕 UNDOCUMENTED TABLES (QuestDB):")
            for table in report.extra_tables:
                print(f"   - {table}")
            print()

        # Print doc drift from all scanned files
        if self.doc_drifts:
            print("📄 OUTDATED DOCS (other files):")
            for drift in self.doc_drifts:
                print(f"   {drift.file}:{drift.line_num}")
                print(
                    f"      {drift.config_name}: found '{drift.found_value}', should be '{drift.canonical_value}'"
                )
            print()

        print("-" * 60)
        has_any_drift = (
            report.has_drift
            or report.has_schema_drift
            or report.has_pyproject_drift
            or len(self.doc_drifts) > 0
        )
        if has_any_drift:
            print("❌ DRIFT DETECTED - Update documentation!")
            print("   Run: python scripts/architecture_drift_detector.py --fix")
        else:
            print("✅ All configurations in sync!")
        print()

    def to_json(self, report: DriftReport) -> str:
        """Convert report to JSON for CI."""
        return json.dumps(
            {
                "has_drift": report.has_drift,
                "has_schema_drift": report.has_schema_drift,
                "has_pyproject_drift": report.has_pyproject_drift,
                "matches": [vars(cv) for cv in report.matches],
                "drifts": [vars(cv) for cv in report.drifts],
                "missing_docs": [vars(cv) for cv in report.missing_docs],
                "missing_actual": [vars(cv) for cv in report.missing_actual],
                "missing_tables": report.missing_tables,
                "extra_tables": report.extra_tables,
                "pyproject_mismatches": [
                    {"name": n, "pyproject": p, "installed": i, "docs": d}
                    for n, p, i, d in report.pyproject_mismatches
                ],
            },
            indent=2,
        )

    def auto_fix(self, report: DriftReport) -> bool:
        """Auto-update ARCHITECTURE.md with actual values."""
        if not report.drifts:
            print("No drift to fix!")
            return True

        content = self.arch_content
        fixed = 0

        for cv in report.drifts:
            if cv.line_in_arch and cv.documented and cv.actual:
                # Replace documented with actual
                old_line = self.arch_lines[cv.line_in_arch - 1]
                new_line = old_line.replace(cv.documented, cv.actual)
                content = content.replace(old_line, new_line)
                fixed += 1
                print(f"Fixed: {cv.name} ({cv.documented} → {cv.actual})")

        if fixed > 0:
            # Update date
            today = subprocess.run(
                ["date", "+%Y-%m-%d"], capture_output=True, text=True
            ).stdout.strip()
            content = re.sub(
                r"## Current Environment \(\d{4}-\d{2}-\d{2}\)",
                f"## Current Environment ({today})",
                content,
            )

            self.arch_file.write_text(content)
            print(f"\n✅ Updated {fixed} values in ARCHITECTURE.md")
            return True

        return False


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent

    detector = ArchitectureDriftDetector(project_root)
    report = detector.detect_drift()

    # Also scan all docs for outdated references
    doc_drifts = detector.scan_all_docs()

    has_any_drift = (
        report.has_drift or report.has_schema_drift or report.has_pyproject_drift or doc_drifts
    )

    if "--json" in sys.argv:
        output = json.loads(detector.to_json(report))
        output["doc_drifts"] = [vars(d) for d in doc_drifts]
        print(json.dumps(output, indent=2))
        sys.exit(1 if has_any_drift else 0)

    if "--fix" in sys.argv:
        detector.auto_fix(report)
        if doc_drifts:
            print(f"\n⚠️  {len(doc_drifts)} outdated references in other docs require manual review")
        if report.missing_tables:
            print(
                f"\n⚠️  {len(report.missing_tables)} missing QuestDB tables require manual creation"
            )
        sys.exit(0)

    detector.print_report(report)
    sys.exit(1 if has_any_drift else 0)


if __name__ == "__main__":
    main()
# Test comment for Opus review - 2026-01-11
