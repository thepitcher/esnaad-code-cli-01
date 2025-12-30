# Esnaad Code

AI-powered agentic coding assistant - Claude Code style.

## Features

- **ReAct Loop**: Reason → Act → Observe execution cycle
- **Tool System**: File operations, search, shell commands
- **Parallel Execution**: Sub-agents for concurrent tasks
- **State Management**: File locking, memory store, caching
- **CLI Interface**: Rich terminal UI with Typer

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Start interactive chat
esnaad chat

# Send a single message
esnaad chat "What files are in this project?"

# Initialize in current directory
esnaad init

# View configuration
esnaad config --list
```

## Configuration

Create a `.env` file or set environment variables:

```bash
ESNAAD_LLM__BASE_URL=http://localhost:3000/api
ESNAAD_LLM__MODEL=gpt-4
ESNAAD_LLM__API_KEY=your-api-key
```

## Available Tools

- `read_file` - Read file contents
- `write_file` - Create or overwrite files
- `edit_file` - Precise text replacements
- `list_directory` - List files and folders
- `search_files` - Find files by pattern
- `search_content` - Search inside files (grep)
- `run_command` - Execute shell commands

## License

MIT
