#!/usr/bin/env python3
"""
Extract mathematical formulas from MinerU-parsed markdown files.

Usage:
    python extract_formulas.py <markdown_file> [--output json|yaml]
    python extract_formulas.py docs/research/parsed/2021-russo-adaptive/auto/*.md

Features:
- Extracts inline ($...$) and display ($$...$$) LaTeX
- Classifies formulas by domain (trading, statistics, optimization)
- Identifies known formulas (Sharpe, Kelly, etc.)
- Outputs structured JSON for Neo4j/DuckDB storage
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Formula(NamedTuple):
    """Extracted formula with metadata."""

    latex: str
    display_mode: bool  # True for $$...$$, False for $...$
    domain: str  # trading|statistics|optimization|general
    known_type: str | None  # sharpe_ratio|kelly_criterion|etc
    line_number: int
    context: str  # surrounding text


# Known formula patterns for classification
KNOWN_FORMULAS = {
    "sharpe_ratio": [
        r"\\frac\{.*[Rr].*-.*[Rr]_f\}\{\\sigma",
        r"SR\s*=",
        r"Sharpe",
    ],
    "kelly_criterion": [
        r"f\^?\*?\s*=\s*\\frac\{.*p.*-.*q\}",
        r"Kelly",
        r"\\frac\{p\s*-\s*q\}\{b\}",
    ],
    "sortino_ratio": [
        r"Sortino",
        r"\\frac\{.*-.*\}\{.*downside",
    ],
    "max_drawdown": [
        r"[Dd]rawdown",
        r"MDD",
        r"\\max.*\\min",
    ],
    "volatility": [
        r"\\sigma\^2",
        r"\\sqrt\{.*variance",
        r"[Vv]olatility",
    ],
    "returns": [
        r"[Rr]_t",
        r"\\log.*[Pp]_\{?t",
        r"\\frac\{[Pp]_\{?t.*\}\{[Pp]_\{?t-1",
    ],
    "ema": [
        r"EMA",
        r"\\alpha.*\(1-\\alpha\)",
        r"exponential.*moving",
    ],
    "position_sizing": [
        r"[Pp]osition.*[Ss]ize",
        r"\\frac\{.*[Rr]isk\}\{",
    ],
    "var": [
        r"VaR",
        r"[Vv]alue.*[Aa]t.*[Rr]isk",
        r"\\Phi\^{-1}",
    ],
    "cvar": [
        r"CVaR",
        r"ES\s*=",
        r"[Ee]xpected.*[Ss]hortfall",
    ],
    "covariance": [
        r"\\Sigma",
        r"[Cc]ov\(",
        r"[Cc]ovariance",
    ],
    "correlation": [
        r"\\rho",
        r"[Cc]orr\(",
        r"[Cc]orrelation",
    ],
    "regression": [
        r"\\beta",
        r"[Rr]egression",
        r"y\s*=.*x.*\\epsilon",
    ],
    "optimization": [
        r"\\arg\\min",
        r"\\arg\\max",
        r"\\nabla",
        r"[Mm]inimize",
        r"[Mm]aximize",
    ],
    "probability": [
        r"[Pp]\(.*\|",
        r"\\mathbb\{P\}",
        r"\\mathbb\{E\}",
        r"[Ee]xpectation",
    ],
    "bayesian": [
        r"[Pp]osterior",
        r"[Pp]rior",
        r"[Ll]ikelihood",
        r"\\propto",
    ],
    "bandit": [
        r"UCB",
        r"Thompson",
        r"[Rr]egret",
        r"[Aa]rm",
        r"\\mu_",
    ],
}

# Domain classification based on formula types
DOMAIN_MAPPING = {
    "trading": [
        "sharpe_ratio",
        "kelly_criterion",
        "sortino_ratio",
        "max_drawdown",
        "position_sizing",
        "var",
        "cvar",
        "returns",
    ],
    "statistics": [
        "volatility",
        "covariance",
        "correlation",
        "regression",
        "probability",
        "bayesian",
    ],
    "optimization": ["optimization", "bandit"],
    "indicators": ["ema"],
}


def extract_latex_formulas(markdown_content: str) -> list[Formula]:
    """Extract all LaTeX formulas from markdown content."""
    formulas = []
    lines = markdown_content.split("\n")

    # Pattern for display math: $$...$$
    display_pattern = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)

    # Pattern for inline math: $...$  (but not $$)
    inline_pattern = re.compile(r"(?<!\$)\$([^\$]+?)\$(?!\$)")

    for line_num, line in enumerate(lines, 1):
        # Get context (surrounding lines)
        context_start = max(0, line_num - 2)
        context_end = min(len(lines), line_num + 2)
        context = " ".join(lines[context_start:context_end])

        # Extract display formulas
        for match in display_pattern.finditer(line):
            latex = match.group(1).strip()
            if len(latex) > 3:  # Skip trivial formulas
                formula = classify_formula(latex, True, line_num, context)
                formulas.append(formula)

        # Extract inline formulas
        for match in inline_pattern.finditer(line):
            latex = match.group(1).strip()
            if len(latex) > 3:  # Skip trivial formulas like $x$
                formula = classify_formula(latex, False, line_num, context)
                formulas.append(formula)

    return formulas


def classify_formula(
    latex: str, display_mode: bool, line_num: int, context: str
) -> Formula:
    """Classify a formula by domain and known type."""
    known_type = None
    domain = "general"

    # Check against known formula patterns
    for formula_type, patterns in KNOWN_FORMULAS.items():
        for pattern in patterns:
            if re.search(pattern, latex, re.IGNORECASE) or re.search(
                pattern, context, re.IGNORECASE
            ):
                known_type = formula_type
                break
        if known_type:
            break

    # Determine domain from known type
    if known_type:
        for dom, types in DOMAIN_MAPPING.items():
            if known_type in types:
                domain = dom
                break

    return Formula(
        latex=latex,
        display_mode=display_mode,
        domain=domain,
        known_type=known_type,
        line_number=line_num,
        context=context[:200],  # Truncate context
    )


def formulas_to_dict(formulas: list[Formula], source_file: str) -> dict:
    """Convert formulas to dictionary for JSON output."""
    return {
        "source_file": source_file,
        "total_formulas": len(formulas),
        "by_domain": {
            "trading": len([f for f in formulas if f.domain == "trading"]),
            "statistics": len([f for f in formulas if f.domain == "statistics"]),
            "optimization": len([f for f in formulas if f.domain == "optimization"]),
            "general": len([f for f in formulas if f.domain == "general"]),
        },
        "known_formulas": [f.known_type for f in formulas if f.known_type],
        "formulas": [
            {
                "latex": f.latex,
                "display_mode": f.display_mode,
                "domain": f.domain,
                "known_type": f.known_type,
                "line_number": f.line_number,
                "context": f.context,
            }
            for f in formulas
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract formulas from MinerU markdown"
    )
    parser.add_argument("markdown_file", help="Path to markdown file")
    parser.add_argument(
        "--output",
        choices=["json", "yaml", "summary"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--min-length", type=int, default=3, help="Minimum formula length to extract"
    )
    args = parser.parse_args()

    md_path = Path(args.markdown_file)
    if not md_path.exists():
        print(f"Error: File not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    content = md_path.read_text(encoding="utf-8")
    formulas = extract_latex_formulas(content)

    if args.output == "summary":
        print(f"Source: {md_path}")
        print(f"Total formulas: {len(formulas)}")
        print(f"  Trading: {len([f for f in formulas if f.domain == 'trading'])}")
        print(f"  Statistics: {len([f for f in formulas if f.domain == 'statistics'])}")
        print(
            f"  Optimization: {len([f for f in formulas if f.domain == 'optimization'])}"
        )
        print(f"  General: {len([f for f in formulas if f.domain == 'general'])}")
        print("\nKnown formulas detected:")
        for f in formulas:
            if f.known_type:
                print(f"  - {f.known_type}: {f.latex[:50]}...")
    else:
        result = formulas_to_dict(formulas, str(md_path))
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
