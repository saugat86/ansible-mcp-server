## Quick Start Guide

Get the Ansible MCP Server running in 5 minutes.

## Installation

```bash
# Install the package
pip install -e .
```

## Setup for Claude Desktop

### 1. Find Your Config File

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

### 2. Add Server Configuration

Edit the config file:

```json
{
  "mcpServers": {
    "ansible": {
      "command": "python",
      "args": [
        "-m",
        "ansible_mcp_server.server"
      ],
      "env": {
        "MCP_ANSIBLE_INVENTORY": "inventory"
      }
    }
  }
}
```

Or if you want to use a specific project directory:

```json
{
  "mcpServers": {
    "ansible": {
      "command": "python",
      "args": [
        "-m",
        "ansible_mcp_server.server"
      ],
      "env": {
        "MCP_ANSIBLE_PROJECT_ROOT": "/path/to/your/ansible/project",
        "MCP_ANSIBLE_INVENTORY": "inventory"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the MCP server.

### 4. Test It

Ask Claude:
```
"Can you ping all my Ansible hosts?"
"List all hosts in my inventory"
"Show me all available playbooks"
```

## Setup for Cursor IDE

### 1. Open Cursor Settings

Open Command Palette (Cmd/Ctrl+Shift+P) and search for "MCP Settings"

### 2. Add Configuration

```json
{
  "mcpServers": {
    "ansible": {
      "command": "python",
      "args": [
        "/absolute/path/to/ansible-mcp-server/src/ansible_mcp_server/server.py"
      ],
      "env": {
        "MCP_ANSIBLE_PROJECT_ROOT": "/path/to/project"
      }
    }
  }
}
```

## Basic Usage Examples

### Check Connectivity
```
"Ping all hosts in my inventory"
```

### Run a Playbook
```
"Run the deploy.yml playbook in check mode"
```

### Get Inventory Info
```
"Show me all hosts in the webservers group"
"What are the variables for host web01?"
```

### Gather Facts
```
"Get system information from all database servers"
```

### Manage Services
```
"Restart nginx on all webservers"
```

## Project Registration

For better organization, you can register projects:

```
"Register an Ansible project named 'production'
 at /path/to/prod with inventory at inventory/production
 and set it as default"
```

Then you can refer to it:
```
"List all playbooks in the production project"
"Run deploy.yml from the production project"
```

## Directory Structure

The server expects this basic structure:

```
your-ansible-project/
├── inventory/
│   └── hosts.ini
├── playbooks/
│   ├── deploy.yml
│   └── maintenance.yml
├── roles/
└── group_vars/
```

But it's flexible! You can configure any directory structure using project registration.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_ANSIBLE_PROJECT_ROOT` | Project root directory | Current directory |
| `MCP_ANSIBLE_INVENTORY` | Inventory file/directory | `inventory` |
| `MCP_ANSIBLE_PROJECT_NAME` | Project to use | None (auto-detect) |

## Troubleshooting

### Server doesn't appear in Claude

1. Check the config file path is correct
2. Verify JSON syntax is valid
3. Restart Claude Desktop completely
4. Check Claude's log files for errors

### Can't find inventory

1. Set `MCP_ANSIBLE_INVENTORY` in the env section
2. Use absolute paths
3. Register your project with full paths

### Playbooks won't run

1. Test the playbook with `ansible-playbook` directly
2. Check SSH keys are configured
3. Verify inventory contains valid hosts

## Next Steps

- Read the full [README.md](README.md) for all features
- Explore vault operations for secrets
- Set up multiple projects for different environments
- Try the diagnostic tools for troubleshooting

## Quick Reference

### Most Common Tools

- `ansible_ping` - Test connectivity
- `ansible_inventory` - List hosts/groups
- `ansible_playbook` - Run playbooks
- `ansible_task` - Run ad-hoc commands
- `ansible_gather_facts` - Get system info
- `validate_playbook` - Check syntax
- `register_project` - Save project config

### Get Help

Ask Claude:
```
"What Ansible tools are available?"
"How do I run a playbook with extra variables?"
"Show me the syntax for ansible_task"
```
