"""Utility functions for Ansible MCP Server."""

import hashlib
import json
import subprocess  # nosec B404 - Required for running Ansible CLI commands
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def run_command(
    cmd: list[str],
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 300,
) -> tuple[int, str, str]:
    """Run a command and return output.

    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        env: Environment variables
        timeout: Command timeout in seconds

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        # nosec B603 - Command args are controlled, not from user input
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            text=True,
        )

        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr

    except subprocess.TimeoutExpired:
        process.kill()
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -1, "", str(e)


def serialize_playbook(playbook: Any) -> str:
    """Convert playbook object to YAML string.

    Args:
        playbook: Playbook as dict or list

    Returns:
        YAML formatted string
    """
    return yaml.dump(playbook, default_flow_style=False, sort_keys=False)


def dict_to_module_args(args: dict[str, Any]) -> str:
    """Convert dict to Ansible module arguments.

    Args:
        args: Dictionary of module arguments

    Returns:
        Space-separated key=value string
    """
    parts = []
    for key, value in args.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif isinstance(value, bool):
            value = str(value).lower()
        parts.append(f"{key}={value}")
    return " ".join(parts)


def split_paths(path_str: str | None) -> list[str]:
    """Split colon-separated path string.

    Args:
        path_str: Colon-separated paths

    Returns:
        List of paths
    """
    if not path_str:
        return []
    return [p.strip() for p in path_str.split(":") if p.strip()]


def extract_hosts_from_inventory_json(inventory_data: dict) -> tuple[list[str], list[str]]:
    """Extract hosts and groups from ansible-inventory JSON output.

    Args:
        inventory_data: Parsed JSON from ansible-inventory

    Returns:
        Tuple of (hosts, groups)
    """
    hosts = []
    groups = []

    # Get all hosts from _meta.hostvars
    if "_meta" in inventory_data and "hostvars" in inventory_data["_meta"]:
        hosts = list(inventory_data["_meta"]["hostvars"].keys())

    # Get all groups (excluding _meta)
    for key in inventory_data.keys():
        if key != "_meta" and isinstance(inventory_data[key], dict):
            groups.append(key)

    return hosts, groups


def discover_playbooks(root_dir: str) -> list[str]:
    """Discover all playbook files in a directory.

    Args:
        root_dir: Root directory to search

    Returns:
        List of playbook file paths
    """
    playbooks = []
    root_path = Path(root_dir)

    # Directories to exclude
    exclude_dirs = {
        ".git", "group_vars", "host_vars", "roles",
        "collections", "venv", ".venv", "__pycache__"
    }

    for yml_file in root_path.rglob("*.yml"):
        if yml_file.is_file():
            # Skip if in excluded directory
            if any(excluded in yml_file.parts for excluded in exclude_dirs):
                continue
            playbooks.append(str(yml_file.relative_to(root_path)))

    for yaml_file in root_path.rglob("*.yaml"):
        if yaml_file.is_file():
            # Skip if in excluded directory
            if any(excluded in yaml_file.parts for excluded in exclude_dirs):
                continue
            playbooks.append(str(yaml_file.relative_to(root_path)))

    return sorted(playbooks)


def generate_snapshot_id() -> str:
    """Generate unique snapshot ID.

    Returns:
        Unique snapshot identifier
    """
    timestamp = datetime.now().isoformat()
    hash_input = f"{timestamp}".encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()[:8]
    return f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash_digest}"


def create_temp_file(content: str, suffix: str = ".txt") -> str:
    """Create a temporary file with content.

    Args:
        content: File content
        suffix: File suffix

    Returns:
        Path to temporary file
    """
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=suffix,
        delete=False
    ) as f:
        f.write(content)
        return f.name


def calculate_health_score(metrics: dict[str, Any]) -> int:
    """Calculate health score from system metrics.

    Args:
        metrics: Dictionary of system metrics

    Returns:
        Health score (0-100)
    """
    score = 100

    # CPU usage
    cpu_usage = int(metrics.get("cpu_usage", 0))
    if cpu_usage > 90:
        score -= 30
    elif cpu_usage > 70:
        score -= 15

    # Memory usage
    mem_usage = int(metrics.get("memory_usage", 0))
    if mem_usage > 90:
        score -= 30
    elif mem_usage > 80:
        score -= 15

    # Disk usage
    disk_usage = int(metrics.get("disk_usage", 0))
    if disk_usage > 95:
        score -= 25
    elif disk_usage > 85:
        score -= 10

    # Failed services
    failed_services = int(metrics.get("failed_services", 0))
    score -= failed_services * 10

    return max(0, min(100, score))


def parse_log_timestamp(line: str) -> str | None:
    """Extract timestamp from log line.

    Args:
        line: Log line

    Returns:
        Timestamp string if found, None otherwise
    """
    import re

    # Common timestamp patterns
    patterns = [
        r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}",  # ISO format
        r"\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}",    # Apache format
        r"\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}",     # Syslog format
    ]

    for pattern in patterns:
        if match := re.search(pattern, line):
            return match.group(0)

    return None
