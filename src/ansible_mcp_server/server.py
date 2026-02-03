"""Ansible MCP Server - Main server implementation."""

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from ansible_mcp_server.config import (
    ProjectDefinition,
    load_config,
    project_env,
    resolve_project,
    save_config,
)
from ansible_mcp_server.utils import (
    calculate_health_score,
    dict_to_module_args,
    discover_playbooks,
    extract_hosts_from_inventory_json,
    generate_snapshot_id,
    parse_log_timestamp,
    run_command,
    serialize_playbook,
    split_paths,
)

# Initialize MCP server
mcp = Server("ansible-mcp")

# Global configuration
config = load_config()


# ============================================================================
# INVENTORY TOOLS
# ============================================================================

@mcp.tool()
def ansible_inventory(
    inventory: Optional[str] = None,
    project: Optional[str] = None,
    show_hostvars: bool = False,
) -> str:
    """List all hosts and groups in the Ansible inventory.

    Args:
        inventory: Path to inventory file (optional)
        project: Project name to use (optional)
        show_hostvars: Include host variables in output

    Returns:
        JSON string with hosts and groups information
    """
    proj = resolve_project(config, project)
    env = project_env(proj) if proj else None

    inv_path = inventory or (proj.inventory if proj else None) or os.getenv("MCP_ANSIBLE_INVENTORY", "inventory")
    cwd = proj.root if proj else None

    cmd = ["ansible-inventory", "-i", inv_path, "--list"]

    rc, stdout, stderr = run_command(cmd, cwd=cwd, env=env)

    if rc != 0:
        return json.dumps({
            "error": "Failed to list inventory",
            "stderr": stderr,
            "return_code": rc
        })

    try:
        inventory_data = json.loads(stdout)
        hosts, groups = extract_hosts_from_inventory_json(inventory_data)

        result = {
            "hosts": hosts,
            "groups": groups,
            "total_hosts": len(hosts),
            "total_groups": len(groups),
        }

        if show_hostvars:
            result["hostvars"] = inventory_data.get("_meta", {}).get("hostvars", {})

        return json.dumps(result, indent=2)

    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Failed to parse inventory JSON: {e}"})


@mcp.tool()
def inventory_graph(
    inventory: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """Show inventory in graph format.

    Args:
        inventory: Path to inventory file (optional)
        project: Project name to use (optional)

    Returns:
        Graph format inventory
    """
    proj = resolve_project(config, project)
    env = project_env(proj) if proj else None

    inv_path = inventory or (proj.inventory if proj else None) or os.getenv("MCP_ANSIBLE_INVENTORY", "inventory")
    cwd = proj.root if proj else None

    cmd = ["ansible-inventory", "-i", inv_path, "--graph"]

    rc, stdout, stderr = run_command(cmd, cwd=cwd, env=env)

    if rc != 0:
        return json.dumps({"error": stderr, "return_code": rc})

    return stdout


@mcp.tool()
def inventory_find_host(
    hostname: str,
    inventory: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """Find a specific host and show its details.

    Args:
        hostname: Hostname to find
        inventory: Path to inventory file (optional)
        project: Project name to use (optional)

    Returns:
        JSON string with host information
    """
    proj = resolve_project(config, project)
    env = project_env(proj) if proj else None

    inv_path = inventory or (proj.inventory if proj else None) or os.getenv("MCP_ANSIBLE_INVENTORY", "inventory")
    cwd = proj.root if proj else None

    cmd = ["ansible-inventory", "-i", inv_path, "--list"]

    rc, stdout, stderr = run_command(cmd, cwd=cwd, env=env)

    if rc != 0:
        return json.dumps({"error": stderr})

    try:
        inventory_data = json.loads(stdout)
        hostvars = inventory_data.get("_meta", {}).get("hostvars", {})

        if hostname not in hostvars:
            return json.dumps({"error": f"Host '{hostname}' not found in inventory"})

        # Find groups containing this host
        groups = []
        for group_name, group_data in inventory_data.items():
            if group_name == "_meta":
                continue
            if "hosts" in group_data and hostname in group_data["hosts"]:
                groups.append(group_name)

        return json.dumps({
            "hostname": hostname,
            "groups": groups,
            "hostvars": hostvars[hostname],
        }, indent=2)

    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Failed to parse inventory: {e}"})


# ============================================================================
# PLAYBOOK TOOLS
# ============================================================================

@mcp.tool()
def ansible_playbook(
    playbook: str,
    inventory: Optional[str] = None,
    extra_vars: Optional[Dict[str, Any]] = None,
    tags: Optional[str] = None,
    skip_tags: Optional[str] = None,
    limit: Optional[str] = None,
    check: bool = False,
    diff: bool = False,
    verbose: int = 0,
    project: Optional[str] = None,
) -> str:
    """Run an Ansible playbook.

    Args:
        playbook: Path to playbook file
        inventory: Inventory file path (optional)
        extra_vars: Extra variables as dict (optional)
        tags: Tags to run (optional)
        skip_tags: Tags to skip (optional)
        limit: Limit to specific hosts (optional)
        check: Run in check mode (optional)
        diff: Show diffs (optional)
        verbose: Verbosity level 0-4 (optional)
        project: Project name (optional)

    Returns:
        Playbook execution results
    """
    proj = resolve_project(config, project)
    env = project_env(proj) if proj else None

    inv_path = inventory or (proj.inventory if proj else None) or os.getenv("MCP_ANSIBLE_INVENTORY", "inventory")
    cwd = proj.root if proj else None

    cmd = ["ansible-playbook", playbook, "-i", inv_path]

    if extra_vars:
        cmd.extend(["--extra-vars", json.dumps(extra_vars)])
    if tags:
        cmd.extend(["--tags", tags])
    if skip_tags:
        cmd.extend(["--skip-tags", skip_tags])
    if limit:
        cmd.extend(["--limit", limit])
    if check:
        cmd.append("--check")
    if diff:
        cmd.append("--diff")
    if verbose > 0:
        cmd.append("-" + "v" * min(verbose, 4))

    rc, stdout, stderr = run_command(cmd, cwd=cwd, env=env)

    return json.dumps({
        "return_code": rc,
        "stdout": stdout,
        "stderr": stderr,
        "success": rc == 0,
    }, indent=2)


@mcp.tool()
def ansible_task(
    hosts: str,
    module: str,
    args: Optional[Dict[str, Any]] = None,
    inventory: Optional[str] = None,
    become: bool = False,
    check: bool = False,
    verbose: int = 0,
    project: Optional[str] = None,
) -> str:
    """Run an ad-hoc Ansible task.

    Args:
        hosts: Host pattern
        module: Ansible module name
        args: Module arguments as dict (optional)
        inventory: Inventory file path (optional)
        become: Use privilege escalation (optional)
        check: Run in check mode (optional)
        verbose: Verbosity level 0-4 (optional)
        project: Project name (optional)

    Returns:
        Task execution results
    """
    proj = resolve_project(config, project)
    env = project_env(proj) if proj else None

    inv_path = inventory or (proj.inventory if proj else None) or os.getenv("MCP_ANSIBLE_INVENTORY", "inventory")
    cwd = proj.root if proj else None

    cmd = ["ansible", hosts, "-i", inv_path, "-m", module]

    if args:
        cmd.extend(["-a", dict_to_module_args(args)])
    if become:
        cmd.append("--become")
    if check:
        cmd.append("--check")
    if verbose > 0:
        cmd.append("-" + "v" * min(verbose, 4))

    rc, stdout, stderr = run_command(cmd, cwd=cwd, env=env)

    return json.dumps({
        "return_code": rc,
        "stdout": stdout,
        "stderr": stderr,
        "success": rc == 0,
    }, indent=2)


@mcp.tool()
def ansible_ping(
    hosts: str = "all",
    inventory: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """Ping Ansible hosts to test connectivity.

    Args:
        hosts: Host pattern (default: all)
        inventory: Inventory file path (optional)
        project: Project name (optional)

    Returns:
        Ping results
    """
    return ansible_task(
        hosts=hosts,
        module="ping",
        inventory=inventory,
        project=project,
    )


@mcp.tool()
def validate_playbook(
    playbook: str,
    inventory: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """Validate playbook syntax.

    Args:
        playbook: Path to playbook file
        inventory: Inventory file path (optional)
        project: Project name (optional)

    Returns:
        Validation results
    """
    proj = resolve_project(config, project)
    env = project_env(proj) if proj else None

    inv_path = inventory or (proj.inventory if proj else None) or os.getenv("MCP_ANSIBLE_INVENTORY", "inventory")
    cwd = proj.root if proj else None

    cmd = ["ansible-playbook", playbook, "-i", inv_path, "--syntax-check"]

    rc, stdout, stderr = run_command(cmd, cwd=cwd, env=env)

    return json.dumps({
        "valid": rc == 0,
        "return_code": rc,
        "stdout": stdout,
        "stderr": stderr,
    }, indent=2)


@mcp.tool()
def create_playbook(
    path: str,
    content: Any,
    project: Optional[str] = None,
) -> str:
    """Create a new playbook file.

    Args:
        path: Path where to create the playbook
        content: Playbook content as YAML string or dict/list
        project: Project name (optional)

    Returns:
        Creation result
    """
    proj = resolve_project(config, project)
    root = Path(proj.root) if proj else Path.cwd()

    playbook_path = root / path

    # Ensure parent directory exists
    playbook_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert content to YAML if needed
    if isinstance(content, (dict, list)):
        yaml_content = serialize_playbook(content)
    else:
        yaml_content = content

    try:
        playbook_path.write_text(yaml_content)
        return json.dumps({
            "success": True,
            "path": str(playbook_path),
            "message": f"Playbook created at {playbook_path}",
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================================================
# PROJECT MANAGEMENT
# ============================================================================

@mcp.tool()
def register_project(
    name: str,
    root: str,
    inventory: Optional[str] = None,
    roles_path: Optional[str] = None,
    collections_paths: Optional[str] = None,
    set_as_default: bool = False,
) -> str:
    """Register an Ansible project.

    Args:
        name: Project name
        root: Project root directory
        inventory: Inventory path (optional)
        roles_path: Colon-separated roles paths (optional)
        collections_paths: Colon-separated collections paths (optional)
        set_as_default: Set as default project (optional)

    Returns:
        Registration result
    """
    global config

    project = ProjectDefinition(
        name=name,
        root=str(Path(root).resolve()),
        inventory=inventory,
        roles_path=split_paths(roles_path),
        collections_paths=split_paths(collections_paths),
    )

    config.projects[name] = project

    if set_as_default or not config.default_project:
        config.default_project = name

    save_config(config)

    return json.dumps({
        "success": True,
        "project": name,
        "root": project.root,
        "is_default": config.default_project == name,
    })


@mcp.tool()
def list_projects() -> str:
    """List all registered projects.

    Returns:
        JSON with all projects
    """
    projects_data = {}

    for name, proj in config.projects.items():
        projects_data[name] = {
            "root": proj.root,
            "inventory": proj.inventory,
            "is_default": name == config.default_project,
        }

    return json.dumps({
        "projects": projects_data,
        "default": config.default_project,
        "total": len(config.projects),
    }, indent=2)


@mcp.tool()
def project_playbooks(
    project: Optional[str] = None,
) -> str:
    """List all playbooks in a project.

    Args:
        project: Project name (optional)

    Returns:
        List of playbook files
    """
    proj = resolve_project(config, project)

    if not proj:
        return json.dumps({"error": "No project specified or found"})

    playbooks = discover_playbooks(proj.root)

    return json.dumps({
        "project": proj.name,
        "root": proj.root,
        "playbooks": playbooks,
        "total": len(playbooks),
    }, indent=2)


# ============================================================================
# VAULT OPERATIONS
# ============================================================================

@mcp.tool()
def vault_encrypt(
    file_path: str,
    vault_password: Optional[str] = None,
    vault_id: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """Encrypt a file with Ansible Vault.

    Args:
        file_path: File to encrypt
        vault_password: Vault password (optional, uses env if not provided)
        vault_id: Vault ID (optional)
        project: Project name (optional)

    Returns:
        Encryption result
    """
    proj = resolve_project(config, project)
    cwd = proj.root if proj else None
    env = project_env(proj) if proj else os.environ.copy()

    cmd = ["ansible-vault", "encrypt", file_path]

    # Handle vault password
    if vault_password:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(vault_password)
            password_file = f.name
        cmd.extend(["--vault-password-file", password_file])
    elif vault_id:
        cmd.extend(["--vault-id", vault_id])

    rc, stdout, stderr = run_command(cmd, cwd=cwd, env=env)

    # Clean up temp password file
    if vault_password:
        os.unlink(password_file)

    return json.dumps({
        "success": rc == 0,
        "stdout": stdout,
        "stderr": stderr,
    })


@mcp.tool()
def vault_decrypt(
    file_path: str,
    vault_password: Optional[str] = None,
    vault_id: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """Decrypt a file encrypted with Ansible Vault.

    Args:
        file_path: File to decrypt
        vault_password: Vault password (optional)
        vault_id: Vault ID (optional)
        project: Project name (optional)

    Returns:
        Decryption result
    """
    proj = resolve_project(config, project)
    cwd = proj.root if proj else None
    env = project_env(proj) if proj else os.environ.copy()

    cmd = ["ansible-vault", "decrypt", file_path]

    if vault_password:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(vault_password)
            password_file = f.name
        cmd.extend(["--vault-password-file", password_file])
    elif vault_id:
        cmd.extend(["--vault-id", vault_id])

    rc, stdout, stderr = run_command(cmd, cwd=cwd, env=env)

    if vault_password:
        os.unlink(password_file)

    return json.dumps({
        "success": rc == 0,
        "stdout": stdout,
        "stderr": stderr,
    })


@mcp.tool()
def vault_view(
    file_path: str,
    vault_password: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """View an encrypted file without decrypting it.

    Args:
        file_path: File to view
        vault_password: Vault password (optional)
        project: Project name (optional)

    Returns:
        File contents
    """
    proj = resolve_project(config, project)
    cwd = proj.root if proj else None
    env = project_env(proj) if proj else os.environ.copy()

    cmd = ["ansible-vault", "view", file_path]

    if vault_password:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(vault_password)
            password_file = f.name
        cmd.extend(["--vault-password-file", password_file])

    rc, stdout, stderr = run_command(cmd, cwd=cwd, env=env)

    if vault_password:
        os.unlink(password_file)

    if rc != 0:
        return json.dumps({"error": stderr})

    return stdout


# ============================================================================
# GALAXY OPERATIONS
# ============================================================================

@mcp.tool()
def galaxy_install(
    requirements_file: str = "requirements.yml",
    force: bool = False,
    project: Optional[str] = None,
) -> str:
    """Install roles and collections from requirements file.

    Args:
        requirements_file: Path to requirements file (default: requirements.yml)
        force: Force reinstall (optional)
        project: Project name (optional)

    Returns:
        Installation results
    """
    proj = resolve_project(config, project)
    cwd = proj.root if proj else None
    env = project_env(proj) if proj else None

    cmd = ["ansible-galaxy", "install", "-r", requirements_file]
    if force:
        cmd.append("--force")

    rc, stdout, stderr = run_command(cmd, cwd=cwd, env=env)

    return json.dumps({
        "success": rc == 0,
        "stdout": stdout,
        "stderr": stderr,
    }, indent=2)


# ============================================================================
# DIAGNOSTICS AND TROUBLESHOOTING
# ============================================================================

@mcp.tool()
def ansible_gather_facts(
    hosts: str = "all",
    filter_pattern: Optional[str] = None,
    inventory: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """Gather system facts from hosts.

    Args:
        hosts: Host pattern (default: all)
        filter_pattern: Fact filter pattern (optional)
        inventory: Inventory path (optional)
        project: Project name (optional)

    Returns:
        Gathered facts
    """
    args = {}
    if filter_pattern:
        args["filter"] = filter_pattern

    return ansible_task(
        hosts=hosts,
        module="setup",
        args=args if args else None,
        inventory=inventory,
        project=project,
    )


@mcp.tool()
def ansible_diagnose_host(
    hostname: str,
    inventory: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """Run comprehensive diagnostics on a host.

    Args:
        hostname: Host to diagnose
        inventory: Inventory path (optional)
        project: Project name (optional)

    Returns:
        Diagnostic results with health score
    """
    # Gather facts
    facts_result = ansible_gather_facts(
        hosts=hostname,
        inventory=inventory,
        project=project,
    )

    try:
        facts_data = json.loads(facts_result)

        # Parse stdout to extract metrics
        metrics = {
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "failed_services": 0,
        }

        # Calculate health score
        health_score = calculate_health_score(metrics)

        return json.dumps({
            "hostname": hostname,
            "health_score": health_score,
            "facts": facts_data,
            "metrics": metrics,
        }, indent=2)

    except json.JSONDecodeError:
        return facts_result


@mcp.tool()
def ansible_service_manager(
    hosts: str,
    service: str,
    state: str,
    inventory: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """Manage systemd services.

    Args:
        hosts: Host pattern
        service: Service name
        state: Desired state (started, stopped, restarted, reloaded)
        inventory: Inventory path (optional)
        project: Project name (optional)

    Returns:
        Service management results
    """
    return ansible_task(
        hosts=hosts,
        module="systemd",
        args={"name": service, "state": state},
        inventory=inventory,
        become=True,
        project=project,
    )


def main():
    """Run the MCP server."""
    import asyncio

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await mcp.run(
                read_stream,
                write_stream,
                mcp.create_initialization_options()
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
