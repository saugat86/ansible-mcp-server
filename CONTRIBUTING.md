# Contributing to Ansible MCP Server

Thank you for your interest in contributing! This guide will help you get started.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/saugat86/ansible-mcp-server.git
cd ansible-mcp-server

# Set up development environment
make setup

# Verify setup
make verify
```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Ansible Core 2.16.0 or higher
- Git
- Make (optional, but recommended)

### Installation

1. **Fork and clone** the repository

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   make install-dev
   # Or: pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Development Workflow

### 1. Create a Branch

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### 2. Make Changes

Write your code following our coding standards (see below).

### 3. Run Tests

```bash
# Run all checks
make verify

# Or run individually
make test          # Run tests
make lint          # Check code style
make typecheck     # Check types
make security      # Security scan
```

### 4. Commit Changes

```bash
# Pre-commit hooks will run automatically
git add .
git commit -m "feat: add new feature"

# If hooks fail, fix issues and try again
make format        # Auto-format code
make lint-fix      # Auto-fix linting issues
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## Coding Standards

### Python Code Style

We use **Ruff** for linting and formatting:

```bash
# Check style
make lint

# Auto-fix issues
make lint-fix

# Format code
make format
```

**Style guidelines:**
- Line length: 88 characters
- Use type hints for function signatures
- Follow PEP 8 conventions
- Use descriptive variable names

### Type Hints

Use type hints for all public functions:

```python
from typing import Dict, List, Optional

def my_function(
    param1: str,
    param2: Optional[int] = None,
) -> Dict[str, Any]:
    """Function docstring."""
    ...
```

### Documentation

All public functions must have docstrings:

```python
def my_function(param1: str, param2: int) -> str:
    """Brief description of what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
    """
    ...
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Build/tooling changes

**Examples:**
```
feat: add inventory diff tool
fix: handle empty inventory gracefully
docs: update README with new tools
test: add tests for config module
```

## Adding New Tools

### 1. Implement the Tool

Add your tool function in `src/ansible_mcp_server/server.py`:

```python
@mcp.tool()
def my_new_tool(
    param1: str,
    param2: Optional[int] = None,
    project: Optional[str] = None,
) -> str:
    """Brief description of what the tool does.

    Args:
        param1: Description
        param2: Optional parameter
        project: Project name (optional)

    Returns:
        JSON string with results
    """
    # Get project config if needed
    proj = resolve_project(config, project)

    # Implement tool logic
    result = {"status": "success", "data": "..."}

    # Return JSON string
    return json.dumps(result, indent=2)
```

### 2. Add Tests

Create tests in `tests/test_tools.py`:

```python
def test_my_new_tool():
    """Test my new tool."""
    result = my_new_tool(param1="test")
    data = json.loads(result)

    assert data["status"] == "success"
    assert "data" in data
```

### 3. Update Documentation

- Add tool description to `README.md`
- Update `CHANGELOG.md` with the change
- Add example usage if applicable

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_config.py -v

# Run specific test
pytest tests/test_config.py::TestProjectDefinition::test_create_project -v
```

### Writing Tests

- Use descriptive test names
- Test both success and error cases
- Aim for >80% coverage for new code
- Use fixtures for common setup

**Example:**

```python
import pytest
from ansible_mcp_server.config import ProjectDefinition

class TestMyFeature:
    """Test cases for my feature."""

    def test_success_case(self):
        """Test successful operation."""
        result = my_function("valid input")
        assert result is not None

    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            my_function("invalid input")

    @pytest.fixture
    def sample_project(self):
        """Fixture for test project."""
        return ProjectDefinition(
            name="test",
            root="/test",
        )

    def test_with_fixture(self, sample_project):
        """Test using fixture."""
        assert sample_project.name == "test"
```

## Pull Request Guidelines

### Before Submitting

- [ ] All tests pass (`make verify`)
- [ ] Code is formatted (`make format`)
- [ ] Tests added for new features
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow convention

### PR Description

Include:

1. **What** - Brief description of changes
2. **Why** - Reason for the changes
3. **How** - How it was implemented
4. **Testing** - How you tested it

**Template:**

```markdown
## Description
Brief description of changes.

## Motivation
Why this change is needed.

## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests added
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### Review Process

1. Automated checks must pass
2. At least one maintainer approval required
3. Address review comments
4. Squash commits if requested
5. Maintainer will merge when ready

## Code Review

### As a Reviewer

- Be respectful and constructive
- Focus on code quality and correctness
- Suggest improvements, don't demand
- Approve when satisfied

### As an Author

- Respond to all comments
- Make requested changes or explain why not
- Ask questions if unclear
- Thank reviewers for their time

## Release Process

Maintainers handle releases:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create and push tag
4. GitHub Actions handles the rest

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security**: Email maintainers directly
- **Chat**: Join our community (link TBD)

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the community

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal or political attacks
- Spam or off-topic content

### Enforcement

Report violations to maintainers. Consequences may include:
- Warning
- Temporary ban
- Permanent ban

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes (for significant contributions)
- CHANGELOG.md (for all contributions)

## Questions?

Don't hesitate to ask! Open an issue or discussion, we're here to help.

Thank you for contributing! 🎉
