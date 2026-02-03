# Project Structure for ansible-mcp-server

## Directory Layout

```
ansible-mcp-server/
├── src/
│   └── ansible_mcp_server/
│       ├── __init__.py           # Package initialization
│       ├── server.py             # Main MCP server with all tools
│       ├── config.py             # Project configuration management
│       ├── utils.py              # Utility functions
│       └── tools/                # (Reserved for future modularization)
│           └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_config.py            # Configuration tests
├── playbooks/                     # Example playbooks
│   ├── ping.yml
│   └── system_info.yml
├── inventory/                     # Example inventory
│   └── hosts.ini
├── pyproject.toml                # Package configuration
├── README.md                     # Full documentation
├── QUICKSTART.md                 # Quick start guide
├── PROJECT_STRUCTURE.md          # This file
├── claude_desktop_config.example.json  # Example Claude config
└── .gitignore
```

## Core Components

### server.py (Main Server)
The main MCP server implementation containing all tools organized by category:
- **Inventory Tools**: List, graph, find hosts
- **Playbook Tools**: Execute, validate, create playbooks
- **Project Management**: Register, list, discover playbooks
- **Vault Operations**: Encrypt, decrypt, view vaulted files
- **Galaxy Integration**: Install dependencies
- **Diagnostics**: Gather facts, health checks, service management

### config.py (Configuration)
Project configuration and persistence:
- `ProjectDefinition`: Dataclass for project configuration
- `ServerConfiguration`: Manages multiple projects
- Configuration file handling (~/.ansible-mcp-config.json)
- Environment variable resolution
- Project environment building

### utils.py (Utilities)
Helper functions used across the server:
- `run_command()`: Execute shell commands
- `serialize_playbook()`: YAML formatting
- `dict_to_module_args()`: Convert dicts to Ansible args
- `extract_hosts_from_inventory_json()`: Parse inventory data
- `discover_playbooks()`: Find playbook files
- `calculate_health_score()`: Compute system health metrics
- `parse_log_timestamp()`: Extract timestamps from logs

## Tool Categories

### 1. Inventory Management (4 tools)
- `ansible_inventory` - List all hosts and groups
- `inventory_graph` - Show inventory relationships
- `inventory_find_host` - Find specific host details
- [Future: `inventory_diff` - Compare inventories]

### 2. Playbook Operations (5 tools)
- `ansible_playbook` - Execute playbooks
- `ansible_task` - Run ad-hoc commands
- `ansible_ping` - Test connectivity
- `validate_playbook` - Syntax checking
- `create_playbook` - Generate playbook files

### 3. Project Management (3 tools)
- `register_project` - Register Ansible projects
- `list_projects` - Show all registered projects
- `project_playbooks` - List playbooks in a project

### 4. Vault Operations (3 tools)
- `vault_encrypt` - Encrypt files
- `vault_decrypt` - Decrypt files
- `vault_view` - View encrypted content

### 5. Galaxy Operations (1 tool)
- `galaxy_install` - Install from requirements.yml

### 6. Diagnostics (3 tools)
- `ansible_gather_facts` - Collect system facts
- `ansible_diagnose_host` - Comprehensive health check
- `ansible_service_manager` - Manage services

**Total: 19 tools implemented**

## Architecture Decisions

### 1. Stdio Transport
- Uses `mcp.server.stdio` for communication
- Compatible with Claude Desktop and Cursor
- No HTTP server needed
- Simpler deployment

### 2. Project-Based Configuration
- Multiple projects with separate configurations
- Persistent storage in JSON config file
- Environment variable support
- Per-project inventory, roles, and collections paths

### 3. Direct Ansible CLI Integration
- Uses ansible-playbook, ansible, ansible-inventory commands
- Maximum compatibility with existing Ansible installations
- No Python API dependencies that might break
- Works with any Ansible version 2.16+

### 4. Modular Organization
- Tools organized by category in server.py
- Utilities separated into utils.py
- Configuration isolated in config.py
- Easy to add new tools

## Comparison with bsahane/mcp-ansible

### Similarities
✅ Stdio-based MCP transport
✅ Project registration and management
✅ Direct CLI integration
✅ Vault operations
✅ Galaxy integration
✅ Inventory management tools
✅ Diagnostic capabilities

### Differences

| Feature | This Implementation | bsahane |
|---------|-------------------|---------|
| **Code Organization** | Modular (server.py, config.py, utils.py) | Single server.py file |
| **Configuration** | Dataclasses with type hints | Dict-based |
| **Documentation** | Comprehensive README + Quick Start | README only |
| **Testing** | Test suite with pytest | Limited tests |
| **Examples** | Example playbooks and inventory included | Not included |
| **Tool Count** | 19 tools | 30+ tools |
| **Advanced Features** | Basic diagnostics | Full troubleshooting suite |

### Enhancements Over Template

This implementation extends the Red Hat template by:
1. **Switching to stdio transport** - Better for AI assistant integration
2. **Simplifying deployment** - No HTTP server, containers, or complex setup
3. **Adding Ansible-specific features** - Vault, Galaxy, project management
4. **Project-based configuration** - Multi-project support
5. **Comprehensive tool set** - 19 tools covering common Ansible operations

## Future Enhancements

### Planned Tools
- `inventory_diff` - Compare two inventories
- `ansible_test_idempotence` - Test playbook idempotence
- `ansible_auto_heal` - Automated remediation
- `ansible_network_matrix` - Network connectivity testing
- `ansible_security_audit` - Security auditing
- `ansible_log_hunter` - Advanced log analysis
- `create_role_structure` - Scaffold Ansible roles

### Planned Improvements
- Async command execution for long-running playbooks
- Progress reporting for playbook execution
- Better error handling and user feedback
- Integration with Ansible Galaxy API
- AWX/Tower integration
- Molecule test integration

## Development Workflow

### Adding a New Tool

1. Add tool function in `server.py` under appropriate category
2. Decorate with `@mcp.tool()`
3. Add comprehensive docstring
4. Use utilities from `utils.py` where applicable
5. Return JSON string for complex data
6. Add tests in `tests/`
7. Update README.md documentation

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ansible_mcp_server

# Run specific test
pytest tests/test_config.py -v
```

### Code Quality

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy src/ansible_mcp_server
```

## Configuration Examples

### Single Project Setup
```bash
export MCP_ANSIBLE_PROJECT_ROOT=/path/to/project
export MCP_ANSIBLE_INVENTORY=inventory
```

### Multi-Project Setup
Use `register_project` tool to register multiple projects, then:
```bash
export MCP_ANSIBLE_PROJECT_NAME=production
```

### Custom Roles/Collections
```bash
export MCP_ANSIBLE_ROLES_PATH=roles:/usr/share/ansible/roles
export MCP_ANSIBLE_COLLECTIONS_PATHS=collections:~/.ansible/collections
```

## Integration Points

### Claude Desktop
- stdio communication via Python module
- Tools appear as available functions
- Environment variables passed via config

### Cursor IDE
- Similar stdio integration
- Workspace-specific configuration
- Project detection from workspace root

### Other MCP Clients
Any MCP client supporting stdio transport can use this server.
