"""Configuration management for Ansible MCP Server."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProjectDefinition:
    """Definition of an Ansible project."""

    name: str
    root: str
    inventory: str | None = None
    roles_path: list[str] | None = None
    collections_paths: list[str] | None = None
    env_vars: dict[str, str] = field(default_factory=dict)


@dataclass
class ServerConfiguration:
    """Server configuration with multiple projects."""

    projects: dict[str, ProjectDefinition] = field(default_factory=dict)
    default_project: str | None = None


def _config_path() -> Path:
    """Get configuration file path.

    Returns:
        Path to configuration file
    """
    if env_path := os.getenv("MCP_ANSIBLE_CONFIG"):
        return Path(env_path)

    local_config = Path.cwd() / ".ansible-mcp-config.json"
    if local_config.exists():
        return local_config

    return Path.home() / ".ansible-mcp-config.json"


def load_config() -> ServerConfiguration:
    """Load server configuration from file.

    Returns:
        ServerConfiguration object
    """
    config_file = _config_path()

    if not config_file.exists():
        return ServerConfiguration()

    try:
        with open(config_file) as f:
            data = json.load(f)

        projects = {}
        for name, proj_data in data.get("projects", {}).items():
            projects[name] = ProjectDefinition(
                name=name,
                root=proj_data["root"],
                inventory=proj_data.get("inventory"),
                roles_path=proj_data.get("roles_path"),
                collections_paths=proj_data.get("collections_paths"),
                env_vars=proj_data.get("env_vars", {}),
            )

        return ServerConfiguration(
            projects=projects,
            default_project=data.get("default_project"),
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {e}")


def save_config(config: ServerConfiguration) -> None:
    """Save server configuration to file.

    Args:
        config: ServerConfiguration to save
    """
    from typing import Any

    config_file = _config_path()

    data: dict[str, Any] = {
        "projects": {},
        "default_project": config.default_project,
    }

    for name, proj in config.projects.items():
        data["projects"][name] = {
            "root": proj.root,
            "inventory": proj.inventory,
            "roles_path": proj.roles_path,
            "collections_paths": proj.collections_paths,
            "env_vars": proj.env_vars,
        }

    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(data, f, indent=2)


def project_env(project: ProjectDefinition) -> dict[str, str]:
    """Build environment variables for a project.

    Args:
        project: ProjectDefinition to build env for

    Returns:
        Dictionary of environment variables
    """
    env = os.environ.copy()

    if project.roles_path:
        env["ANSIBLE_ROLES_PATH"] = ":".join(project.roles_path)

    if project.collections_paths:
        env["ANSIBLE_COLLECTIONS_PATH"] = ":".join(project.collections_paths)

    # Add custom env vars from project
    env.update(project.env_vars)

    # Add MCP-specific env vars that can be forwarded
    for key, value in os.environ.items():
        if key.startswith("MCP_ANSIBLE_ENV_"):
            actual_key = key.replace("MCP_ANSIBLE_ENV_", "")
            env[actual_key] = value

    return env


def resolve_project(
    config: ServerConfiguration, project_name: str | None = None
) -> ProjectDefinition | None:
    """Resolve which project to use.

    Args:
        config: ServerConfiguration
        project_name: Optional explicit project name

    Returns:
        ProjectDefinition if found, None otherwise
    """
    # Explicit project name
    if project_name:
        return config.projects.get(project_name)

    # Environment override
    if env_project := os.getenv("MCP_ANSIBLE_PROJECT_NAME"):
        return config.projects.get(env_project)

    # Default project
    if config.default_project:
        return config.projects.get(config.default_project)

    # Single project shortcut
    if len(config.projects) == 1:
        return list(config.projects.values())[0]

    return None
