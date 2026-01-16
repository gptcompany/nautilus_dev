"""
E2E Tests for GitHub Automation Workflows

Tests for:
- Auto-merge Dependabot
- PR Auto-labeling
- Alert Auto-remediation

Run with: pytest tests/e2e/automation/ -v --e2e
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

# Mark all tests in this module as e2e
pytestmark = pytest.mark.e2e


class TestWorkflowFiles:
    """Test that workflow files are valid YAML and have required fields."""

    WORKFLOWS_DIR = Path(__file__).parent.parent.parent.parent / ".github" / "workflows"

    def test_auto_merge_dependabot_exists(self):
        """Verify auto-merge-dependabot.yml exists."""
        workflow_file = self.WORKFLOWS_DIR / "auto-merge-dependabot.yml"
        assert workflow_file.exists(), f"Missing: {workflow_file}"

    def test_pr_automation_exists(self):
        """Verify pr-automation.yml exists."""
        workflow_file = self.WORKFLOWS_DIR / "pr-automation.yml"
        assert workflow_file.exists(), f"Missing: {workflow_file}"

    def test_alert_auto_remediation_exists(self):
        """Verify alert-auto-remediation.yml exists."""
        workflow_file = self.WORKFLOWS_DIR / "alert-auto-remediation.yml"
        assert workflow_file.exists(), f"Missing: {workflow_file}"

    def test_workflows_valid_yaml(self):
        """Verify all workflow files are valid YAML."""
        import yaml

        for workflow_file in self.WORKFLOWS_DIR.glob("*.yml"):
            with open(workflow_file) as f:
                try:
                    data = yaml.safe_load(f)
                    assert data is not None, f"Empty workflow: {workflow_file.name}"
                    assert "name" in data, f"Missing 'name' in {workflow_file.name}"
                    # PyYAML converts 'on' to True (boolean), so check for both
                    assert (
                        "on" in data or True in data
                    ), f"Missing 'on' trigger in {workflow_file.name}"
                    assert "jobs" in data, f"Missing 'jobs' in {workflow_file.name}"
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {workflow_file.name}: {e}")


class TestLabelerConfig:
    """Test labeler configuration."""

    CONFIG_FILE = Path(__file__).parent.parent.parent.parent / ".github" / "labeler.yml"

    def test_labeler_config_exists(self):
        """Verify labeler.yml exists."""
        assert self.CONFIG_FILE.exists(), f"Missing: {self.CONFIG_FILE}"

    def test_labeler_has_key_labels(self):
        """Verify labeler has essential labels configured."""
        import yaml

        with open(self.CONFIG_FILE) as f:
            config = yaml.safe_load(f)

        expected_labels = ["strategies", "tests", "ci", "docs"]
        for label in expected_labels:
            assert label in config, f"Missing label config: {label}"


class TestCodeowners:
    """Test CODEOWNERS file."""

    CODEOWNERS_FILE = Path(__file__).parent.parent.parent.parent / ".github" / "CODEOWNERS"

    def test_codeowners_exists(self):
        """Verify CODEOWNERS exists."""
        assert self.CODEOWNERS_FILE.exists(), f"Missing: {self.CODEOWNERS_FILE}"

    def test_codeowners_has_default_owner(self):
        """Verify CODEOWNERS has a default owner."""
        content = self.CODEOWNERS_FILE.read_text()
        assert "* @" in content, "Missing default owner (* @owner)"


class TestAutoRemediationWorkflow:
    """Test auto-remediation workflow logic."""

    def test_disk_cleanup_command(self):
        """Test disk cleanup commands are valid."""
        # Verify commands exist
        result = subprocess.run(["which", "docker"], capture_output=True, text=True)
        assert result.returncode == 0, "Docker not found"

    def test_dry_run_mode(self):
        """Test that dry run doesn't execute destructive commands."""
        # This would be tested via act or workflow_dispatch with dry_run=true
        # For unit test, verify the workflow file has dry_run option
        workflow_file = (
            Path(__file__).parent.parent.parent.parent
            / ".github"
            / "workflows"
            / "alert-auto-remediation.yml"
        )
        content = workflow_file.read_text()
        assert "dry_run" in content, "Missing dry_run option"
        assert "DRY RUN" in content, "Missing dry run handling"


class TestActLocalExecution:
    """Test workflows can run locally with act (if installed)."""

    @pytest.fixture
    def act_available(self):
        """Check if act is installed."""
        result = subprocess.run(["which", "act"], capture_output=True, text=True)
        if result.returncode != 0:
            pytest.skip("act not installed - skipping local workflow tests")
        return True

    def test_list_workflows_with_act(self, act_available):
        """Test act can list workflows."""
        result = subprocess.run(
            ["act", "-l"],
            cwd=Path(__file__).parent.parent.parent.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"act -l failed: {result.stderr}"
        assert "auto-merge" in result.stdout.lower() or "Auto" in result.stdout


class TestIntegrationWithPrometheus:
    """Test integration with Prometheus alerts."""

    @pytest.fixture
    def prometheus_available(self):
        """Check if Prometheus is available."""
        import requests

        try:
            response = requests.get("http://localhost:9090/api/v1/status/config", timeout=5)
            if response.status_code != 200:
                pytest.skip("Prometheus not available")
        except Exception:
            pytest.skip("Prometheus not reachable")
        return True

    def test_can_query_alerts(self, prometheus_available):
        """Test we can query Prometheus for alerts."""
        import requests

        response = requests.get("http://localhost:9090/api/v1/alerts", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_alert_rules_exist(self, prometheus_available):
        """Test alert rules are configured."""
        import requests

        response = requests.get("http://localhost:9090/api/v1/rules", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["groups"]) > 0, "No alert rule groups found"
