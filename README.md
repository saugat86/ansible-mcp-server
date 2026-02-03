# Ansible MCP Server

Advanced Model Context Protocol (MCP) server for Ansible automation. Integrate Ansible with AI assistants like Claude Desktop and Cursor for intelligent infrastructure management.

## Features

### Core Ansible Operations
- **Playbook Execution**: Run playbooks with full parameter control (tags, limits, extra vars, check mode)
- **Ad-hoc Commands**: Execute one-off Ansible tasks across your infrastructure
- **Syntax Validation**: Validate playbook syntax before execution
- **Ping Testing**: Test host connectivity

### Inventory Management
- **List Inventory**: View all hosts and groups
- **Inventory Graph**: Visualize inventory relationships
- **Find Host**: Look up specific hosts with their groups and variables
- **Parse Inventory**: Full inventory parsing with variable resolution

### Vault Operations
- **Encrypt/Decrypt**: Secure sensitive data with Ansible Vault
- **View**: Display encrypted file contents without decrypting
- **Rekey**: Change vault passwords

### Project Management
- **Register Projects**: Manage multiple Ansible projects with different configurations
- **Project Discovery**: Automatically discover playbooks in project directories
- **Environment Isolation**: Each project maintains its own inventory, roles, and collections paths

### Galaxy Integration
- **Install Dependencies**: Install roles and collections from requirements files
- **Lock Files**: Generate dependency lockfiles for reproducible deployments

### Diagnostics & Troubleshooting
- **Gather Facts**: Collect comprehensive system information
- **Host Diagnostics**: Run health checks with scoring
- **Service Management**: Control systemd services remotely

## Installation

### Prerequisites

- Python 3.10 or higher
- Ansible Core 2.16.0 or higher

### Install from Source

```bash
# Clone the repository
cd ansible-mcp-server

# Install with pip
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Configuration

### Quick Start

The server works out of the box without configuration. It will use:
- Current directory as project root
- `inventory` file/directory in current directory
- Environment variables for ansible configuration

### Project Registration

For better organization, register your Ansible projects:

```python
# The MCP client will call this tool
register_project(
    name="production",
    root="/path/to/ansible/project",
    inventory="/path/to/inventory",
    set_as_default=True
)
```

### Environment Variables

Configure behavior with these optional environment variables:

- `MCP_ANSIBLE_PROJECT_ROOT`: Default project root directory
- `MCP_ANSIBLE_INVENTORY`: Default inventory path
- `MCP_ANSIBLE_PROJECT_NAME`: Default project name
- `MCP_ANSIBLE_ROLES_PATH`: Colon-separated roles paths
- `MCP_ANSIBLE_COLLECTIONS_PATHS`: Colon-separated collections paths
- `MCP_ANSIBLE_CONFIG`: Custom config file location
- `MCP_ANSIBLE_ENV_*`: Forward environment variables (e.g., `MCP_ANSIBLE_ENV_ANSIBLE_HOST_KEY_CHECKING=False`)

### Configuration File

Projects are stored in `~/.ansible-mcp-config.json` or `.ansible-mcp-config.json` in the current directory.

Example configuration:
```json
{
  "default_project": "production",
  "projects": {
    "production": {
      "root": "/path/to/prod",
      "inventory": "inventory/production",
      "roles_path": ["roles", "/usr/share/ansible/roles"],
      "collections_paths": ["collections"],
      "env_vars": {
        "ANSIBLE_HOST_KEY_CHECKING": "False"
      }
    },
    "staging": {
      "root": "/path/to/staging",
      "inventory": "inventory/staging"
    }
  }
}
```

## Integration

### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "ansible": {
      "command": "python",
      "args": ["-m", "ansible_mcp_server.server"],
      "env": {
        "MCP_ANSIBLE_PROJECT_ROOT": "/path/to/your/ansible/project",
        "MCP_ANSIBLE_INVENTORY": "inventory"
      }
    }
  }
}
```

Or if installed globally:

```json
{
  "mcpServers": {
    "ansible": {
      "command": "ansible-mcp-server"
    }
  }
}
```

### Cursor IDE

Add to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "ansible": {
      "command": "python",
      "args": ["/path/to/ansible-mcp-server/src/ansible_mcp_server/server.py"],
      "env": {
        "MCP_ANSIBLE_PROJECT_ROOT": "/path/to/project"
      }
    }
  }
}
```

## Available Tools

### Inventory Tools

**ansible_inventory**
- List all hosts and groups
- Optional hostvars inclusion

**inventory_graph**
- Visual graph of inventory structure

**inventory_find_host**
- Find specific host with details

### Playbook Tools

**ansible_playbook**
- Execute playbooks with full control
- Parameters: playbook, inventory, extra_vars, tags, skip_tags, limit, check, diff, verbose

**ansible_task**
- Run ad-hoc commands
- Parameters: hosts, module, args, inventory, become, check, verbose

**ansible_ping**
- Test host connectivity
- Quick connectivity verification

**validate_playbook**
- Syntax checking before execution

**create_playbook**
- Generate new playbook files from YAML

### Project Tools

**register_project**
- Register Ansible projects
- Parameters: name, root, inventory, roles_path, collections_paths, set_as_default

**list_projects**
- Show all registered projects

**project_playbooks**
- List playbooks in a project

### Vault Tools

**vault_encrypt**
- Encrypt files with Ansible Vault

**vault_decrypt**
- Decrypt vault-encrypted files

**vault_view**
- View encrypted content without decrypting

### Galaxy Tools

**galaxy_install**
- Install from requirements.yml
- Force reinstall option

### Diagnostic Tools

**ansible_gather_facts**
- Collect system facts
- Optional fact filtering

**ansible_diagnose_host**
- Comprehensive host health check
- Returns health score 0-100

**ansible_service_manager**
- Manage systemd services
- States: started, stopped, restarted, reloaded

## Usage Examples

### Using with Claude

Once configured, you can ask Claude to:

```
"Use Ansible to check if all production servers are reachable"
"Run the deploy.yml playbook on the staging environment"
"Show me all hosts in the webservers group"
"Gather system facts from the database servers"
"Encrypt the secrets.yml file with Ansible Vault"
"Install all required roles from requirements.yml"
```

### Direct Tool Usage

The tools can also be called programmatically:

```python
# List inventory
ansible_inventory(project="production")

# Run playbook
ansible_playbook(
    playbook="deploy.yml",
    inventory="production",
    extra_vars={"version": "1.2.3"},
    tags="deploy",
    check=True  # Dry run first
)

# Check host health
ansible_diagnose_host(
    hostname="web01",
    inventory="production"
)
```

## Architecture

The server uses:
- **stdio transport** for MCP communication (not HTTP)
- **Project-based configuration** with persistent storage
- **Environment isolation** per project
- **Direct Ansible CLI integration** for maximum compatibility

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking
mypy src/ansible_mcp_server

# Format code
ruff format .
```

## Security Considerations

- **Vault Passwords**: Pass via environment or use vault ID files
- **SSH Keys**: Use ssh-agent or specify private key in inventory
- **Privilege Escalation**: Tools support become/sudo when needed
- **Project Isolation**: Each project maintains separate configuration
- **No Credential Storage**: Server doesn't store passwords or keys

## Troubleshooting

### Server Not Connecting

1. Check the command path in your MCP client configuration
2. Verify Python environment has all dependencies
3. Check environment variables are set correctly

### Playbook Fails to Run

1. Test with `ansible-playbook` command directly
2. Verify inventory path is correct
3. Check project configuration if using projects
4. Ensure SSH keys are available

### Inventory Not Found

1. Verify `MCP_ANSIBLE_INVENTORY` environment variable
2. Check project inventory path in configuration
3. Use absolute paths for clarity

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure code quality checks pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

- GitHub Issues: [Report Issues](https://github.com/yourusername/ansible-mcp-server/issues)
- Documentation: [Full Docs](https://github.com/yourusername/ansible-mcp-server)
