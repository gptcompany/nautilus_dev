#!/usr/bin/env python3
"""
Setup Sentry Alert Rules via API

Creates standardized alert rules for the nautilus-trading project.
Requires SENTRY_AUTH_TOKEN with alerts:write scope.

Usage:
    export SENTRY_AUTH_TOKEN="your-token-here"
    python scripts/setup_sentry_alerts.py

Get token from: https://sentry.io/settings/account/api/auth-tokens/
Required scopes: project:read, alerts:write
"""

import os
import sys
from dataclasses import dataclass

import requests


@dataclass
class SentryConfig:
    """Sentry API configuration."""

    auth_token: str
    org_slug: str = "your-org"  # Update with your org
    project_slug: str = "nautilus-trading"
    base_url: str = "https://sentry.io/api/0"

    @classmethod
    def from_env(cls) -> "SentryConfig":
        token = os.environ.get("SENTRY_AUTH_TOKEN")
        if not token:
            print("ERROR: SENTRY_AUTH_TOKEN not set")
            print("Get token from: https://sentry.io/settings/account/api/auth-tokens/")
            sys.exit(1)

        org = os.environ.get("SENTRY_ORG", "your-org")
        project = os.environ.get("SENTRY_PROJECT", "nautilus-trading")

        # Support regional Sentry instances (de.sentry.io, us.sentry.io, etc.)
        # Auto-detect from DSN if available
        dsn = os.environ.get("SENTRY_DSN", "")
        if "de.sentry.io" in dsn:
            base_url = "https://de.sentry.io/api/0"
        elif "us.sentry.io" in dsn:
            base_url = "https://us.sentry.io/api/0"
        else:
            base_url = os.environ.get("SENTRY_URL", "https://sentry.io/api/0")

        return cls(auth_token=token, org_slug=org, project_slug=project, base_url=base_url)


# Alert rule definitions
ALERT_RULES = [
    {
        "name": "High Error Rate",
        "actionMatch": "all",
        "filterMatch": "all",
        "frequency": 60,  # 1 hour
        "conditions": [
            {
                "id": "sentry.rules.conditions.event_frequency.EventFrequencyCondition",
                "value": 10,
                "interval": "1h",
            }
        ],
        "actions": [
            {
                "id": "sentry.mail.actions.NotifyEmailAction",
                "targetType": "IssueOwners",
                "fallthroughType": "ActiveMembers",
            }
        ],
        "filters": [],
    },
    {
        "name": "Critical Trading Error",
        "actionMatch": "all",
        "filterMatch": "all",
        "frequency": 5,  # 5 minutes - immediate
        "conditions": [
            {
                "id": "sentry.rules.conditions.first_seen_event.FirstSeenEventCondition",
            }
        ],
        "actions": [
            {
                "id": "sentry.mail.actions.NotifyEmailAction",
                "targetType": "IssueOwners",
                "fallthroughType": "ActiveMembers",
            }
        ],
        "filters": [
            {
                "id": "sentry.rules.filters.tagged_event.TaggedEventFilter",
                "key": "trading.critical",
                "match": "eq",
                "value": "true",
            }
        ],
    },
    {
        "name": "Risk Limit Breach",
        "actionMatch": "all",
        "filterMatch": "any",
        "frequency": 5,
        "conditions": [
            {
                "id": "sentry.rules.conditions.first_seen_event.FirstSeenEventCondition",
            }
        ],
        "actions": [
            {
                "id": "sentry.mail.actions.NotifyEmailAction",
                "targetType": "IssueOwners",
                "fallthroughType": "ActiveMembers",
            }
        ],
        "filters": [
            {
                "id": "sentry.rules.filters.event_attribute.EventAttributeFilter",
                "attribute": "message",
                "match": "co",  # contains
                "value": "kill switch",
            },
            {
                "id": "sentry.rules.filters.event_attribute.EventAttributeFilter",
                "attribute": "message",
                "match": "co",
                "value": "drawdown",
            },
            {
                "id": "sentry.rules.filters.event_attribute.EventAttributeFilter",
                "attribute": "message",
                "match": "co",
                "value": "max position",
            },
        ],
    },
    {
        "name": "Connection Errors",
        "actionMatch": "all",
        "filterMatch": "all",
        "frequency": 30,  # 30 minutes
        "conditions": [
            {
                "id": "sentry.rules.conditions.event_frequency.EventFrequencyCondition",
                "value": 5,
                "interval": "15m",
            }
        ],
        "actions": [
            {
                "id": "sentry.mail.actions.NotifyEmailAction",
                "targetType": "IssueOwners",
                "fallthroughType": "ActiveMembers",
            }
        ],
        "filters": [
            {
                "id": "sentry.rules.filters.event_attribute.EventAttributeFilter",
                "attribute": "message",
                "match": "co",
                "value": "connection",
            }
        ],
    },
]


def create_alert_rule(config: SentryConfig, rule: dict) -> bool:
    """Create a single alert rule."""
    url = f"{config.base_url}/projects/{config.org_slug}/{config.project_slug}/rules/"

    headers = {
        "Authorization": f"Bearer {config.auth_token}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, json=rule, timeout=30)

    if response.status_code == 201:
        print(f"  ✅ Created: {rule['name']}")
        return True
    elif response.status_code == 400 and "already exists" in response.text.lower():
        print(f"  ⚠️  Already exists: {rule['name']}")
        return True
    else:
        print(f"  ❌ Failed: {rule['name']}")
        print(f"     Status: {response.status_code}")
        print(f"     Response: {response.text[:200]}")
        return False


def list_existing_rules(config: SentryConfig) -> list:
    """List existing alert rules."""
    url = f"{config.base_url}/projects/{config.org_slug}/{config.project_slug}/rules/"

    headers = {"Authorization": f"Bearer {config.auth_token}"}

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 200:
        return response.json()
    return []


def main():
    """Main entry point."""
    print("=" * 50)
    print("  Sentry Alert Rules Setup")
    print("=" * 50)
    print()

    config = SentryConfig.from_env()
    print(f"Organization: {config.org_slug}")
    print(f"Project: {config.project_slug}")
    print()

    # Check existing rules
    print("Checking existing rules...")
    existing = list_existing_rules(config)
    existing_names = {r["name"] for r in existing}
    print(f"Found {len(existing)} existing rules")
    print()

    # Create new rules
    print("Creating alert rules...")
    created = 0
    skipped = 0
    failed = 0

    for rule in ALERT_RULES:
        if rule["name"] in existing_names:
            print(f"  ⏭️  Skipping (exists): {rule['name']}")
            skipped += 1
            continue

        if create_alert_rule(config, rule):
            created += 1
        else:
            failed += 1

    # Summary
    print()
    print("=" * 50)
    print("  Summary")
    print("=" * 50)
    print(f"  Created: {created}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {failed}")
    print()

    if failed > 0:
        print("⚠️  Some rules failed to create.")
        print("   Check your SENTRY_AUTH_TOKEN has 'alerts:write' scope.")
        print("   Verify org/project slugs are correct.")
        sys.exit(1)

    print("✅ Alert rules setup complete!")
    print()
    print("Next steps:")
    print("1. Add Discord integration in Sentry UI:")
    print("   Settings → Integrations → Discord")
    print()
    print("2. Update alert actions to use Discord:")
    print("   Alerts → Edit rule → Add Discord action")


if __name__ == "__main__":
    main()
