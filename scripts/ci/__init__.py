# CI/CD Automation Scripts
# Supporting scripts for GitHub Actions workflows

"""
CI/CD automation utilities for NautilusTrader development.

Modules:
- generate_fix_tasks: Convert ImpactReport to tasks.md format
- taskstoissues_with_milestones: Batch issue creation with milestone support
- alpha_debug_to_tasks: Convert alpha-debug findings to tasks
- analyze_backtest_failure: Parse backtest failure logs
- generate_diagnostic_tasks: Create diagnostic tasks from failures
- rollback: Checkpoint and rollback management

Usage:
    # Generate fix tasks from impact report
    python -m scripts.ci.generate_fix_tasks --impact-file analysis.json --output tasks.md

    # Create GitHub issues from tasks.md
    python -m scripts.ci.taskstoissues_with_milestones --tasks-file tasks.md --dry-run

    # Convert alpha-debug output to tasks
    python -m scripts.ci.alpha_debug_to_tasks --input debug.log --output specs/bugs/tasks.md

    # Analyze backtest failure
    python -m scripts.ci.analyze_backtest_failure --log-files *.log --output analysis.json

    # Generate diagnostic tasks
    python -m scripts.ci.generate_diagnostic_tasks --analysis-file analysis.json --output tasks.md

    # Checkpoint management
    python -m scripts.ci.rollback create --name "pre-backtest" --stage 4
    python -m scripts.ci.rollback list
    python -m scripts.ci.rollback rollback --checkpoint abc123
    python -m scripts.ci.rollback cleanup --older-than 24h
"""
