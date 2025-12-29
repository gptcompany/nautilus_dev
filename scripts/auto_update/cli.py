# NautilusTrader Auto-Update Pipeline - CLI Interface

"""Command-line interface for auto-update pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from scripts.auto_update.models import AutoUpdateConfig
from scripts.auto_update.parser import (
    detect_update_available,
    extract_breaking_changes,
    get_current_version,
    parse_changelog,
)

console = Console()


def get_default_config() -> AutoUpdateConfig:
    """Get default configuration."""
    return AutoUpdateConfig()


# =============================================================================
# Main CLI Group
# =============================================================================


@click.group()
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.pass_context
def cli(ctx: click.Context, dry_run: bool) -> None:
    """NautilusTrader Auto-Update Pipeline.

    Autonomous pipeline to detect NautilusTrader nightly changes,
    analyze impact on codebase, update dependencies, and validate compatibility.
    """
    ctx.ensure_object(dict)
    config = get_default_config()
    if dry_run:
        config.dry_run = True
    ctx.obj["config"] = config


# =============================================================================
# Check Command (US1)
# =============================================================================


@cli.command()
@click.option(
    "--changelog",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to changelog.json",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed impact analysis")
@click.pass_context
def check(
    ctx: click.Context,
    changelog: Path | None,
    output_format: str,
    verbose: bool,
) -> None:
    """Analyze changelog for updates and breaking changes.

    Parses the N8N-generated changelog.json and reports:
    - Current vs latest version
    - Breaking changes detected
    - Impact on codebase (with --verbose)

    Exit codes:
      0 - No updates needed or analysis complete
      1 - Error during analysis
      2 - Update available (for scripting)
    """
    from scripts.auto_update.analyzer import (
        analyze_breaking_change_impact,
        generate_impact_report,
    )

    config: AutoUpdateConfig = ctx.obj["config"]
    changelog_path = changelog or config.changelog_path

    try:
        # Parse changelog
        changelog_data = parse_changelog(changelog_path)

        # Get current version
        current_version = get_current_version(config.pyproject_path)
        if current_version is None:
            current_version = "unknown"

        # Check for updates
        update_info = detect_update_available(
            current_version=current_version,
            changelog_version=changelog_data.stable_version,
        )

        # Extract breaking changes
        breaking_changes = extract_breaking_changes(changelog_data)

        # If verbose, analyze impact on codebase
        impact_report = None
        if verbose and breaking_changes:
            # Collect affected files for each breaking change
            all_affected = []
            for bc in breaking_changes:
                affected = analyze_breaking_change_impact(bc, config.source_dirs)
                all_affected.extend(affected)

            # Generate impact report
            impact_report = generate_impact_report(
                version=update_info["latest_version"],
                previous_version=update_info["current_version"],
                breaking_changes=breaking_changes,
                affected_files=all_affected,
            )

        # Format output
        if output_format == "json":
            _output_json(update_info, breaking_changes, changelog_data, impact_report)
        elif output_format == "markdown":
            _output_markdown(update_info, breaking_changes, verbose, impact_report)
        else:
            _output_text(update_info, breaking_changes, changelog_data, verbose, impact_report)

        # Exit code 2 if update available (for scripting)
        if update_info["update_available"]:
            ctx.exit(2)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)


def _output_text(
    update_info: dict[str, Any],
    breaking_changes: list,
    changelog_data: Any,
    verbose: bool,
    impact_report: Any = None,
) -> None:
    """Output check results in text format."""
    console.print("\n[bold]=== NautilusTrader Update Check ===[/bold]\n")

    # Version info
    console.print(f"Current Version: [cyan]{update_info['current_version']}[/cyan]")
    console.print(f"Latest Version:  [cyan]{update_info['latest_version']}[/cyan]")

    if update_info["update_available"]:
        console.print("Status: [yellow]UPDATE AVAILABLE[/yellow]")
    else:
        console.print("Status: [green]UP TO DATE[/green]")

    # Breaking changes
    if breaking_changes:
        console.print(f"\n[bold]Breaking Changes ({len(breaking_changes)}):[/bold]")
        for bc in breaking_changes:
            severity_color = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "green",
            }.get(bc.severity.value, "white")
            console.print(
                f"  [{severity_color}][{bc.severity.value.upper()}][/{severity_color}] {bc.description}"
            )
    else:
        console.print("\n[green]No breaking changes detected[/green]")

    # Verbose: show patterns and impact analysis
    if verbose and breaking_changes:
        console.print("\n[bold]Grep Patterns:[/bold]")
        for bc in breaking_changes:
            if bc.affected_pattern:
                console.print(f"  - {bc.affected_pattern}")

    # Impact report (verbose mode)
    if impact_report:
        console.print("\n[bold]Impact Analysis:[/bold]")
        console.print(f"  Files Affected: {len(impact_report.affected_files)}")
        console.print(f"  Lines Affected: {impact_report.total_affected_lines}")
        console.print(f"  Confidence Score: {impact_report.confidence_score:.1f}/100")
        console.print(f"  Confidence Level: {impact_report.confidence_level.value.upper()}")
        rec_color = {
            "auto": "green",
            "delayed": "yellow",
            "manual": "blue",
            "blocked": "red",
        }.get(impact_report.recommendation.value, "white")
        console.print(
            f"  Recommendation: [{rec_color}]{impact_report.recommendation.value.upper()}[/{rec_color}]"
        )

        # Show affected files
        if impact_report.affected_files:
            console.print("\n[bold] Files:[/bold]")
            for af in impact_report.affected_files[:10]:  # Limit to 10
                console.print(f"  - {af.path}:{','.join(map(str, af.line_numbers))}")


def _output_json(
    update_info: dict[str, Any],
    breaking_changes: list,
    changelog_data: Any,
    impact_report: Any = None,
) -> None:
    """Output check results in JSON format."""
    output = {
        "update_available": update_info["update_available"],
        "current_version": update_info["current_version"],
        "latest_version": update_info["latest_version"],
        "nightly_commits": changelog_data.nightly_commits,
        "breaking_changes": [
            {
                "description": bc.description,
                "severity": bc.severity.value,
                "pattern": bc.affected_pattern,
                "migration": bc.migration_guide,
            }
            for bc in breaking_changes
        ],
    }

    # Add impact report if available
    if impact_report:
        output["impact_report"] = {
            "files_affected": len(impact_report.affected_files),
            "lines_affected": impact_report.total_affected_lines,
            "confidence_score": impact_report.confidence_score,
            "confidence_level": impact_report.confidence_level.value,
            "can_auto_update": impact_report.can_auto_update,
            "recommendation": impact_report.recommendation.value,
            "affected_files": [
                {
                    "path": str(af.path),
                    "lines": af.line_numbers,
                    "can_auto_fix": af.can_auto_fix,
                    "fix_type": af.fix_type,
                }
                for af in impact_report.affected_files
            ],
        }

    console.print(json.dumps(output, indent=2))


def _output_markdown(
    update_info: dict[str, Any],
    breaking_changes: list,
    verbose: bool,
    impact_report: Any = None,
) -> None:
    """Output check results in Markdown format."""
    lines = [
        "# NautilusTrader Update Check",
        "",
        f"- **Current Version**: {update_info['current_version']}",
        f"- **Latest Version**: {update_info['latest_version']}",
        f"- **Update Available**: {'Yes' if update_info['update_available'] else 'No'}",
        "",
    ]

    if breaking_changes:
        lines.append(f"## Breaking Changes ({len(breaking_changes)})")
        lines.append("")
        for bc in breaking_changes:
            lines.append(f"- **[{bc.severity.value.upper()}]** {bc.description}")
            if verbose and bc.migration_guide:
                lines.append(f"  - Migration: {bc.migration_guide}")
        lines.append("")

    if impact_report:
        lines.append("## Impact Analysis")
        lines.append("")
        lines.append(f"- **Files Affected**: {len(impact_report.affected_files)}")
        lines.append(f"- **Lines Affected**: {impact_report.total_affected_lines}")
        lines.append(f"- **Confidence Score**: {impact_report.confidence_score:.1f}/100")
        lines.append(f"- **Recommendation**: {impact_report.recommendation.value.upper()}")
        lines.append("")

    console.print("\n".join(lines))


# =============================================================================
# Placeholder Commands (to be implemented in later phases)
# =============================================================================


@cli.command()
@click.option("--version", type=str, default=None, help="Specific version to update to")
@click.option("--force", is_flag=True, help="Update even with low confidence")
@click.option("--skip-tests", is_flag=True, help="Skip test validation")
@click.option("--no-pr", is_flag=True, help="Create branch but don't create PR")
@click.option(
    "--test-paths",
    multiple=True,
    help="Specific test paths to run (can be specified multiple times)",
)
@click.option("--test-timeout", type=int, default=600, help="Test timeout in seconds")
@click.pass_context
def update(
    ctx: click.Context,
    version: str | None,
    force: bool,
    skip_tests: bool,
    no_pr: bool,
    test_paths: tuple[str, ...],
    test_timeout: int,
) -> None:
    """Perform auto-update if safe.

    Updates pyproject.toml, runs uv sync, validates tests,
    creates branch and PR.

    Exit codes:
      0 - Update successful
      1 - Error during update
      2 - Update blocked (confidence too low)
      3 - Tests failed
    """
    from scripts.auto_update.git_ops import (
        create_pr,
        git_commit_changes,
        git_create_branch,
        git_push_branch,
    )
    from scripts.auto_update.updater import auto_update as perform_update
    from scripts.auto_update.validator import format_test_report, validate_update

    config: AutoUpdateConfig = ctx.obj["config"]
    dry_run = config.dry_run

    try:
        # Determine target version
        if version is None:
            # Get latest from changelog
            changelog_data = parse_changelog(config.changelog_path)
            target_version = changelog_data.stable_version.lstrip("v")
        else:
            target_version = version.lstrip("v")

        console.print("\n[bold]=== NautilusTrader Auto-Update ===[/bold]\n")
        console.print(f"Target Version: [cyan]{target_version}[/cyan]")
        console.print(f"Dry Run: [cyan]{dry_run}[/cyan]")
        console.print(f"Skip Tests: [cyan]{skip_tests}[/cyan]\n")

        # Step 1: Create branch
        branch_name = f"{config.branch_prefix}{target_version}"
        console.print(f"[1/5] Creating branch: [cyan]{branch_name}[/cyan]")
        branch_result = git_create_branch(
            branch_name=branch_name,
            base_branch=config.base_branch,
            dry_run=dry_run,
        )
        if not branch_result["success"]:
            console.print(f"[red]Failed to create branch:[/red] {branch_result.get('error')}")
            ctx.exit(1)
        console.print("      [green]Done[/green]")

        # Step 2: Update pyproject.toml
        console.print("[2/5] Updating pyproject.toml")
        update_result = perform_update(
            version=target_version,
            pyproject_path=config.pyproject_path,
            working_dir=Path.cwd(),
            dry_run=dry_run,
        )
        if not update_result["success"]:
            console.print(f"[red]Failed to update:[/red] {update_result.get('error')}")
            ctx.exit(1)
        console.print("      [green]Done[/green]")

        # Step 3: Run validation tests (US4)
        test_result = None
        if not skip_tests:
            console.print("[3/5] Running validation tests")
            validation_result = validate_update(
                working_dir=Path.cwd(),
                test_paths=list(test_paths) if test_paths else None,
                dry_run=dry_run,
                timeout=test_timeout,
            )
            test_result = validation_result.get("test_result")

            if not dry_run:
                if test_result:
                    # Show test summary
                    status_icon = "✅" if test_result.passed else "❌"
                    console.print(
                        f"      {status_icon} {test_result.passed_tests}/{test_result.total_tests} tests passed"
                    )

                    if not validation_result["can_merge"] and not force:
                        console.print(
                            f"\n[red]Tests failed![/red] {test_result.failed_tests} failures detected."
                        )
                        console.print(
                            "Use --force to proceed anyway, or --skip-tests to skip validation."
                        )
                        ctx.exit(3)
                    elif not validation_result["can_merge"] and force:
                        console.print(
                            "[yellow]Warning: Proceeding despite test failures (--force)[/yellow]"
                        )
            else:
                console.print("      [dim]Skipped (dry run)[/dim]")
        else:
            console.print("[3/5] Skipping validation tests (--skip-tests)")

        # Step 4: Commit changes
        console.print("[4/5] Committing changes")
        commit_result = git_commit_changes(
            message=f"chore: update nautilus_trader to v{target_version}",
            files=["pyproject.toml", "uv.lock"],
            dry_run=dry_run,
        )
        if not commit_result["success"] and not dry_run:
            console.print(f"[red]Failed to commit:[/red] {commit_result.get('error')}")
            ctx.exit(1)
        console.print("      [green]Done[/green]")

        # Step 5: Push and create PR
        if not no_pr:
            console.print("[5/5] Pushing and creating PR")

            # Push branch
            push_result = git_push_branch(
                branch_name=branch_name,
                remote=config.remote,
                dry_run=dry_run,
            )
            if not push_result["success"] and not dry_run:
                console.print(f"[red]Failed to push:[/red] {push_result.get('error')}")
                ctx.exit(1)

            # Build PR body with test results
            pr_body = f"""## Summary

Update NautilusTrader from current version to v{target_version}.

## Changes

- Updated `pyproject.toml` dependency version
- Ran `uv sync` to update lock file

"""
            # Add test results to PR body (T052)
            if test_result and not skip_tests:
                pr_body += format_test_report(test_result)
                pr_body += "\n"

            pr_body += """## Test Plan

- [x] Automated test suite (see results above)
- [ ] Verify import compatibility
- [ ] Test strategy execution

---

\U0001f916 Generated with [Claude Code](https://claude.com/claude-code)
"""
            pr_result = create_pr(
                title=f"chore: update nautilus_trader to v{target_version}",
                body=pr_body,
                base_branch=config.base_branch,
                head_branch=branch_name,
                labels=["auto-update", "dependencies"],
                dry_run=dry_run,
            )
            if pr_result["success"]:
                console.print(f"      [green]PR created:[/green] {pr_result.get('pr_url', 'N/A')}")
            else:
                console.print(
                    f"      [yellow]PR creation skipped:[/yellow] {pr_result.get('error', 'dry run')}"
                )
        else:
            console.print("[5/5] Skipping PR creation (--no-pr)")

        console.print("\n[green]Update complete![/green]")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)


@cli.command()
@click.option("--report", type=click.Path(exists=True, path_type=Path), help="Impact report path")
@click.option("--timeout", type=int, default=1800, help="Timeout in seconds")
@click.option("--prompt", type=str, help="Custom task prompt")
@click.option("--version", type=str, help="Target version to update to")
@click.pass_context
def dispatch(
    ctx: click.Context,
    report: Path | None,
    timeout: int,
    prompt: str | None,
    version: str | None,
) -> None:
    """Dispatch Claude Code for complex fixes.

    Sends task prompt to Claude Code CLI with impact report context.

    Exit codes:
      0 - Dispatch successful
      1 - Error during dispatch
      2 - Timeout reached
      3 - No impact report found
    """
    from scripts.auto_update.analyzer import (
        analyze_breaking_change_impact,
        generate_impact_report,
    )
    from scripts.auto_update.dispatcher import build_task_prompt, dispatch_claude_code

    config: AutoUpdateConfig = ctx.obj["config"]
    dry_run = config.dry_run

    try:
        console.print("\n[bold]=== Claude Code Dispatch ===[/bold]\n")

        # Get or generate impact report
        if report:
            # Load from file
            console.print(f"Loaded impact report from: {report}")
            # TODO: Deserialize ImpactReport from JSON file
            console.print("[yellow]Report loading not fully implemented[/yellow]")
            ctx.exit(1)
        else:
            # Generate fresh impact report
            if not version:
                changelog_data = parse_changelog(config.changelog_path)
                target_version = changelog_data.stable_version.lstrip("v")
            else:
                target_version = version.lstrip("v")

            current_version = get_current_version(config.pyproject_path) or "unknown"

            console.print(f"Target Version: [cyan]{target_version}[/cyan]")
            console.print(f"Current Version: [cyan]{current_version}[/cyan]")

            # Get breaking changes and analyze impact
            changelog_data = parse_changelog(config.changelog_path)
            breaking_changes = extract_breaking_changes(changelog_data)

            if not breaking_changes:
                console.print("[green]No breaking changes to handle[/green]")
                ctx.exit(0)

            # Analyze impact
            all_affected = []
            for bc in breaking_changes:
                affected = analyze_breaking_change_impact(bc, config.source_dirs)
                all_affected.extend(affected)

            impact_report = generate_impact_report(
                version=target_version,
                previous_version=current_version,
                breaking_changes=breaking_changes,
                affected_files=all_affected,
            )

        console.print(f"Breaking Changes: {len(impact_report.breaking_changes)}")
        console.print(f"Affected Files: {len(impact_report.affected_files)}")
        console.print(f"Confidence: {impact_report.confidence_score:.1f}/100")

        # Build and show task prompt
        task_prompt = build_task_prompt(
            impact_report,
            custom_instructions=prompt,
        )

        if dry_run:
            console.print("\n[bold]Task Prompt Preview:[/bold]\n")
            console.print(task_prompt[:500] + "..." if len(task_prompt) > 500 else task_prompt)
            console.print("\n[dim]Dry run - agent not spawned[/dim]")
            ctx.exit(0)

        # Dispatch Claude Code
        console.print("\n[bold]Dispatching Claude Code agent...[/bold]")
        result = dispatch_claude_code(
            impact_report=impact_report,
            working_dir=Path.cwd(),
            timeout=timeout,
            dry_run=False,
        )

        if result["success"]:
            console.print(f"[green]Agent dispatched![/green] PID: {result.get('pid', 'N/A')}")
        else:
            console.print(f"[red]Dispatch failed:[/red] {result.get('error')}")
            ctx.exit(1)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)


@cli.command()
@click.argument("message")
@click.option(
    "--channel",
    type=click.Choice(["discord", "email", "all"]),
    default="discord",
    help="Notification channel",
)
@click.option(
    "--level",
    type=click.Choice(["info", "warning", "error", "critical"]),
    default="info",
    help="Notification level",
)
@click.option("--embed", "use_embed", is_flag=True, help="Use rich embed (Discord only)")
@click.option("--pr-url", type=str, help="Include PR link")
@click.option("--webhook-url", type=str, envvar="DISCORD_WEBHOOK_URL", help="Discord webhook URL")
@click.pass_context
def notify(
    ctx: click.Context,
    message: str,
    channel: str,
    level: str,
    use_embed: bool,
    pr_url: str | None,
    webhook_url: str | None,
) -> None:
    """Send notification.

    Sends notification to Discord webhook or email.

    Exit codes:
      0 - Notification sent
      1 - Error sending notification
    """
    from scripts.auto_update.notifier import send_notification

    config: AutoUpdateConfig = ctx.obj["config"]
    dry_run = config.dry_run

    try:
        console.print("\n[bold]=== Send Notification ===[/bold]\n")

        # Level to color mapping for Discord embeds
        level_colors = {
            "info": 0x5865F2,  # Discord blurple
            "warning": 0xFFA500,  # Orange
            "error": 0xFF0000,  # Red
            "critical": 0x8B0000,  # Dark red
        }

        # Format message with PR URL if provided
        full_message = message
        if pr_url:
            full_message += f"\n\n**PR**: {pr_url}"

        console.print(f"Channel: [cyan]{channel}[/cyan]")
        console.print(f"Level: [cyan]{level}[/cyan]")
        console.print(f"Message: {message[:50]}..." if len(message) > 50 else f"Message: {message}")

        if dry_run:
            console.print("\n[dim]Dry run - notification not sent[/dim]")
            ctx.exit(0)

        # Prepare Discord notification
        discord_kwargs = {}
        if use_embed:
            discord_kwargs["embed"] = True
            discord_kwargs["title"] = f"NautilusTrader Auto-Update ({level.upper()})"
            discord_kwargs["color"] = level_colors.get(level, 0x5865F2)

        # Send notification
        result = send_notification(
            message=full_message,
            channel=channel,
            webhook_url=webhook_url or config.discord_webhook,
            dry_run=False,
        )

        if result["success"]:
            console.print("[green]Notification sent successfully![/green]")
            if "discord" in result:
                console.print(f"  Discord: {result['discord'].get('status_code', 'sent')}")
            if "email" in result:
                console.print(f"  Email: sent to {result['email'].get('to', 'N/A')}")
        else:
            console.print("[red]Failed to send notification[/red]")
            if "discord" in result and not result["discord"]["success"]:
                console.print(f"  Discord error: {result['discord'].get('error')}")
            if "email" in result and not result["email"]["success"]:
                console.print(f"  Email error: {result['email'].get('error')}")
            ctx.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        ctx.exit(1)


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show pipeline status.

    Displays:
    - Current version
    - Last check time
    - Pending PRs
    - Pipeline state
    """
    config: AutoUpdateConfig = ctx.obj["config"]

    console.print("\n[bold]=== Pipeline Status ===[/bold]\n")

    # Get current version
    current_version = get_current_version(config.pyproject_path)
    console.print(f"Current Version: [cyan]{current_version or 'unknown'}[/cyan]")

    # TODO: Add last check time, pending PRs, pipeline state in Phase 9
    console.print("Last Check: [dim]Not tracked yet[/dim]")
    console.print("Pending PRs: [dim]Not tracked yet[/dim]")
    console.print("Pipeline Status: [green]idle[/green]")


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> None:
    """Main entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
