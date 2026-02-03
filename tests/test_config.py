"""Tests for configuration module."""

import tempfile
from pathlib import Path

from ansible_mcp_server.config import (
    ProjectDefinition,
    ServerConfiguration,
    load_config,
    project_env,
    resolve_project,
    save_config,
)


class TestProjectDefinition:
    """Test cases for ProjectDefinition."""

    def test_create_project(self):
        """Test creating a project definition."""
        project = ProjectDefinition(
            name="test",
            root="/path/to/project",
            inventory="inventory",
        )

        assert project.name == "test"
        assert project.root == "/path/to/project"
        assert project.inventory == "inventory"

    def test_project_with_roles(self):
        """Test project with roles path."""
        project = ProjectDefinition(
            name="test",
            root="/path/to/project",
            roles_path=["roles", "/usr/share/ansible/roles"],
        )

        assert len(project.roles_path) == 2
        assert "roles" in project.roles_path


class TestServerConfiguration:
    """Test cases for ServerConfiguration."""

    def test_empty_config(self):
        """Test empty configuration."""
        config = ServerConfiguration()

        assert len(config.projects) == 0
        assert config.default_project is None

    def test_config_with_projects(self):
        """Test configuration with projects."""
        project = ProjectDefinition(name="test", root="/test")
        config = ServerConfiguration(
            projects={"test": project},
            default_project="test",
        )

        assert len(config.projects) == 1
        assert config.default_project == "test"


class TestConfigPersistence:
    """Test cases for configuration save/load."""

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        project = ProjectDefinition(
            name="test",
            root="/path/to/project",
            inventory="inventory",
            roles_path=["roles"],
        )

        config = ServerConfiguration(
            projects={"test": project},
            default_project="test",
        )

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            # Save config
            import os

            os.environ["MCP_ANSIBLE_CONFIG"] = temp_path
            save_config(config)

            # Load config
            loaded_config = load_config()

            assert len(loaded_config.projects) == 1
            assert "test" in loaded_config.projects
            assert loaded_config.default_project == "test"
            assert loaded_config.projects["test"].root == "/path/to/project"

        finally:
            # Cleanup
            if "MCP_ANSIBLE_CONFIG" in os.environ:
                del os.environ["MCP_ANSIBLE_CONFIG"]
            Path(temp_path).unlink(missing_ok=True)


class TestProjectResolution:
    """Test cases for project resolution."""

    def test_resolve_explicit_project(self):
        """Test resolving with explicit project name."""
        project = ProjectDefinition(name="test", root="/test")
        config = ServerConfiguration(projects={"test": project})

        resolved = resolve_project(config, "test")

        assert resolved is not None
        assert resolved.name == "test"

    def test_resolve_default_project(self):
        """Test resolving default project."""
        project = ProjectDefinition(name="test", root="/test")
        config = ServerConfiguration(
            projects={"test": project},
            default_project="test",
        )

        resolved = resolve_project(config)

        assert resolved is not None
        assert resolved.name == "test"

    def test_resolve_single_project(self):
        """Test resolving when only one project exists."""
        project = ProjectDefinition(name="test", root="/test")
        config = ServerConfiguration(projects={"test": project})

        resolved = resolve_project(config)

        assert resolved is not None
        assert resolved.name == "test"

    def test_resolve_no_project(self):
        """Test resolving with no projects."""
        config = ServerConfiguration()

        resolved = resolve_project(config)

        assert resolved is None


class TestProjectEnv:
    """Test cases for project environment building."""

    def test_basic_env(self):
        """Test basic environment creation."""
        project = ProjectDefinition(name="test", root="/test")

        env = project_env(project)

        assert env is not None
        assert isinstance(env, dict)

    def test_env_with_roles_path(self):
        """Test environment with roles path."""
        project = ProjectDefinition(
            name="test",
            root="/test",
            roles_path=["roles", "/usr/share/ansible/roles"],
        )

        env = project_env(project)

        assert "ANSIBLE_ROLES_PATH" in env
        assert "roles:/usr/share/ansible/roles" == env["ANSIBLE_ROLES_PATH"]

    def test_env_with_custom_vars(self):
        """Test environment with custom variables."""
        project = ProjectDefinition(
            name="test",
            root="/test",
            env_vars={"CUSTOM_VAR": "value"},
        )

        env = project_env(project)

        assert "CUSTOM_VAR" in env
        assert env["CUSTOM_VAR"] == "value"
