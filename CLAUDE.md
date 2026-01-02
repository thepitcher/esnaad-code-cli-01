# CLAUDE.md - Esnaad Code Project Context

## Project Overview

**Esnaad Code** is a Claude Code-style agentic system built in Python. It features a single orchestrator agent with the ability to spawn parallel sub-agents for independent subtasks, using a ReAct-style (Reasoning + Acting) loop with tool use.

- **Language**: Python 3.11+
- **LLM Provider**: Open WebUI (OpenAI-compatible REST API)
- **Interface**: CLI only (Typer + Rich)
- **Target OS**: Windows primarily

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR AGENT                       │
│  - Receives user task                                        │
│  - Plans and decomposes into subtasks                        │
│  - Decides: sequential vs parallel execution                 │
│  - Aggregates results                                        │
│  - Maintains conversation state                              │
└─────────────────────────┬────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌───────────┐   ┌───────────┐   ┌───────────┐
    │ Sub-Agent │   │ Sub-Agent │   │ Sub-Agent │
    │  Task A   │   │  Task B   │   │  Task C   │
    └───────────┘   └───────────┘   └───────────┘
          │               │               │
          └───────────────┴───────────────┘
                          │
                    ┌─────▼─────┐
                    │  Shared   │
                    │  State    │
                    └───────────┘
```

## Current Project State (Latest)

### Implementation Status: 100% Complete

#### Phase 1: Foundation ✅ COMPLETE
- [x] `pyproject.toml` with all dependencies
- [x] `.env.example` configuration template
- [x] `config/settings.py` - Pydantic settings with nested config
- [x] `config/constants.py` - Application constants
- [x] `exceptions/` - Full exception hierarchy (base, llm, tool, agent)
- [x] `models/` - All Pydantic models (messages, tool_call, subtask, clarification, result)

#### Phase 2: Tool System ✅ COMPLETE
- [x] `tools/base.py` - BaseTool ABC with OpenAI schema generation
- [x] `tools/registry.py` - Tool registration with decorators
- [x] `tools/file/read_file.py` - Read with line numbers, offset/limit
- [x] `tools/file/write_file.py` - Create/overwrite files
- [x] `tools/file/edit_file.py` - Precise text replacement
- [x] `tools/filesystem/list_directory.py` - List with recursion, patterns
- [x] `tools/filesystem/search_files.py` - Glob pattern file search
- [x] `tools/filesystem/search_content.py` - Grep-like content search
- [x] `tools/shell/run_command.py` - Shell execution with timeout

#### Phase 3: Core Agent ✅ COMPLETE
- [x] `core/react_loop.py` - Generic ReAct implementation
- [x] `core/orchestrator.py` - Main orchestrator with tool execution
- [x] `core/subagent.py` - Sub-agent for parallel tasks
- [x] `llm/client.py` - Async httpx client for OpenAI-compatible API
- [x] `llm/streaming.py` - SSE stream handling
- [x] `llm/messages.py` - Message formatting, system prompts
- [x] `llm/tool_calls.py` - Tool call parsing

#### Phase 4: Parallel Execution ✅ COMPLETE
- [x] `parallel/executor.py` - Timeout and retry logic
- [x] `parallel/coordinator.py` - Fan-out/fan-in coordination
- [x] `state/manager.py` - Central state coordinator
- [x] `state/file_locks.py` - Async read/write locks
- [x] `state/memory.py` - Key-value store
- [x] `state/cache.py` - LRU result cache

#### Phase 5: CLI ✅ COMPLETE
- [x] `cli/app.py` - Typer application with commands
- [x] `cli/commands/chat.py` - Interactive chat with orchestrator
- [x] `cli/commands/config.py` - Configuration viewing
- [x] `cli/commands/init.py` - Project initialization
- [x] `cli/ui/console.py` - Rich console singleton
- [x] `cli/ui/panels.py` - Status panels, tool output
- [x] `cli/ui/prompt.py` - User input with history
- [x] `utils/logging.py` - Structlog configuration

#### Phase 6: Orchestration & Web ✅ COMPLETE
- [x] `tools/orchestration/spawn_subtasks.py` - Parallel subtask spawning tool
- [x] `tools/orchestration/request_clarifications.py` - Clarification tool
- [x] `cli/ui/clarification.py` - Interactive questionnaire UI
- [x] `state/preferences.py` - User preference learning
- [x] `tools/web/web_search.py` - Web search tool (DuckDuckGo)
- [x] `tools/web/web_fetch.py` - URL fetching tool

#### Phase 7: Testing ✅ COMPLETE
- [x] Unit tests for tools (file, filesystem, shell, web, orchestration)
- [x] Unit tests for core agents (orchestrator, subagent, react_loop)
- [x] Unit tests for state management (memory, cache, locks, preferences)
- [x] Integration tests (tool execution, parallel execution)
- [x] Test fixtures and conftest.py

#### Phase 8: Streaming ✅ COMPLETE
- [x] Streaming support in ReAct loop
- [x] Streaming support in Orchestrator
- [x] Streaming callbacks in CLI
- [x] Real-time content output

#### Phase 9: Rules System ✅ COMPLETE
- [x] `config/rules.py` - RulesLoader class with caching
- [x] `ESNAAD.md` file support in project root
- [x] Rules injection in orchestrator system prompt
- [x] Rules inheritance to sub-agents
- [x] Unit tests for RulesLoader (16 tests)

#### Phase 10: UX Improvements & Bug Fixes ✅ COMPLETE
- [x] SSL verification skip option (`verify_ssl` setting)
- [x] Thinking spinner during LLM requests
- [x] Claude Code orange theme (#E57B3A)
- [x] Simplified input prompt (">")
- [x] Dual API format support (OpenAI + Anthropic)
- [x] Pydantic v2 compatibility fixes
- [x] Parallel tool execution for `parallel_safe` tools
- [x] Empty response retry logic

## Project Structure

```
esnaad-code-04/
├── pyproject.toml              # Project config, dependencies
├── README.md                   # User documentation
├── CLAUDE.md                   # This file - AI context
├── REQUIREMENTS.md             # Original requirements spec
├── .env.example                # Environment template
├── check_tools.py              # Tool registration verification script
├── test_clarification.py       # Clarification UI test script
│
└── src/esnaad/
    ├── __init__.py             # Package init, version
    ├── __main__.py             # Entry: python -m esnaad
    │
    ├── cli/                    # CLI Layer
    │   ├── __init__.py
    │   ├── app.py              # Typer app, commands
    │   ├── commands/
    │   │   ├── chat.py         # Main chat command
    │   │   ├── config.py       # Config command
    │   │   └── init.py         # Init command
    │   └── ui/
    │       ├── console.py      # Rich console
    │       ├── panels.py       # Output panels
    │       ├── prompt.py       # User input
    │       └── clarification.py # Clarification questionnaire
    │
    ├── config/                 # Configuration
    │   ├── __init__.py
    │   ├── settings.py         # Pydantic settings
    │   └── constants.py        # Constants
    │
    ├── core/                   # Agent Logic
    │   ├── __init__.py
    │   ├── orchestrator.py     # Main orchestrator
    │   ├── subagent.py         # Sub-agent
    │   └── react_loop.py       # ReAct loop
    │
    ├── llm/                    # LLM Client
    │   ├── __init__.py
    │   ├── client.py           # Async httpx client
    │   ├── streaming.py        # Stream handling
    │   ├── messages.py         # Message formatting
    │   └── tool_calls.py       # Tool call parsing
    │
    ├── tools/                  # Tool System
    │   ├── __init__.py
    │   ├── base.py             # BaseTool ABC
    │   ├── registry.py         # Tool registry
    │   ├── file/
    │   │   ├── read_file.py
    │   │   ├── write_file.py
    │   │   └── edit_file.py
    │   ├── filesystem/
    │   │   ├── list_directory.py
    │   │   ├── search_files.py
    │   │   └── search_content.py
    │   ├── shell/
    │   │   └── run_command.py
    │   ├── orchestration/
    │   │   ├── spawn_subtasks.py
    │   │   └── request_clarifications.py
    │   └── web/
    │       ├── web_search.py
    │       └── web_fetch.py
    │
    ├── state/                  # State Management
    │   ├── __init__.py
    │   ├── manager.py          # Central manager
    │   ├── file_locks.py       # Async locks
    │   ├── memory.py           # KV store
    │   ├── cache.py            # Result cache
    │   └── preferences.py      # User preference learning
    │
    ├── parallel/               # Parallel Execution
    │   ├── __init__.py
    │   ├── executor.py         # Timeout/retry
    │   └── coordinator.py      # Subtask coordination
    │
    ├── models/                 # Data Models
    │   ├── __init__.py
    │   ├── messages.py         # Message models
    │   ├── tool_call.py        # Tool call models
    │   ├── subtask.py          # Subtask models
    │   ├── clarification.py    # Clarification models
    │   └── result.py           # Result models
    │
    ├── exceptions/             # Exceptions
    │   ├── __init__.py
    │   ├── base.py
    │   ├── llm.py
    │   ├── tool.py
    │   └── agent.py
    │
    └── utils/                  # Utilities
        ├── __init__.py
        └── logging.py          # Structlog config

tests/                          # Test Suite
├── conftest.py                 # Shared fixtures
├── tools/
│   ├── test_file_tools.py
│   ├── test_filesystem_tools.py
│   ├── test_shell_tool.py
│   ├── test_web_tools.py
│   ├── test_orchestration_tools.py
│   └── test_registry.py
├── core/
│   ├── test_react_loop.py
│   ├── test_orchestrator.py
│   └── test_subagent.py
├── state/
│   ├── test_memory.py
│   ├── test_cache.py
│   ├── test_file_locks.py
│   ├── test_preferences.py
│   └── test_manager.py
└── integration/
    ├── test_tool_execution.py
    └── test_parallel_execution.py
```

## How to Run

```bash
# Install in development mode
cd c:\Workspace\Claude\esnaad-code-04
uv pip install -e .

# Or with pip
pip install -e .

# Run CLI
esnaad chat                      # Interactive mode
esnaad chat "List files here"    # Single message
esnaad config --list             # Show config
esnaad config --env              # Show env vars
esnaad init                      # Initialize project
```

## Quick Verification

```bash
# Verify all tools are registered
python check_tools.py

# Expected output:
# Registered Tools:
# --------------------------------------------------
#   read_file: Read file contents with optional line range...
#   write_file: Write content to a file...
#   edit_file: Edit a file by replacing text...
#   list_directory: List contents of a directory...
#   search_files: Search for files matching a pattern...
#   search_content: Search for text patterns in files...
#   run_command: Execute a shell command...
#   spawn_subtasks: Execute multiple subtasks in parallel...
#   request_clarifications: Request clarifications from the user...
#   web_search: Search the web using DuckDuckGo...
#   web_fetch: Fetch content from a URL...
# --------------------------------------------------
# Total: 11 tools
# [OK] request_clarifications tool is registered
# [OK] spawn_subtasks tool is registered

# Run tests
pytest tests/ -v

# Test clarification UI (requires interactive terminal)
python test_clarification.py
```

## Configuration

Set in `.env` or environment:

```bash
# General
ESNAAD_DEBUG=false                           # Debug mode (shows logs)
ESNAAD_LOG_LEVEL=INFO                        # Log level when debug=true
ESNAAD_WORKING_DIRECTORY=C:\Projects\my-project  # Working directory

# LLM Settings
ESNAAD_LLM__BASE_URL=http://localhost:3000/api
ESNAAD_LLM__API_KEY=your-key
ESNAAD_LLM__MODEL=gpt-4
ESNAAD_LLM__VERIFY_SSL=true                  # Set to false to skip TLS verification

# Orchestrator
ESNAAD_ORCHESTRATOR__MAX_ITERATIONS=50
ESNAAD_ORCHESTRATOR__TIMEOUT_SECONDS=300
```

## Key Design Decisions

1. **Async-first**: All I/O uses asyncio for parallel execution
2. **Pydantic everywhere**: Type-safe models for all data
3. **Tool registry pattern**: Decorator-based registration
4. **File locking**: Read/write locks for concurrent access
5. **Stateless sub-agents**: Fresh context per subtask
6. **Structured errors**: Exception hierarchy with recoverable flag
7. **Parallel tool execution**: Tools marked `parallel_safe=True` execute concurrently
8. **Dual API format**: Supports both OpenAI and Anthropic response formats
9. **Automatic retry**: Empty responses after tool calls trigger automatic retry

## Dependencies

- `typer[all]` - CLI framework
- `httpx` - Async HTTP client
- `pydantic` / `pydantic-settings` - Data validation
- `aiofiles` - Async file I/O
- `structlog` - Structured logging
- `prompt-toolkit` - Input handling

## Known Issues / TODOs

No major known issues. All core features implemented.

## Session History

### Session 1 (2024-12-29)
- Read REQUIREMENTS.md and created implementation plan
- User chose: Python, Open WebUI, CLI only, Full implementation
- Implemented Phases 1-5 (Foundation, Tools, Core, Parallel, CLI)
- Fixed debug logging issue (logs now suppressed when ESNAAD_DEBUG=false)
- Created README.md and CLAUDE.md

### Session 2 (2024-12-29)
- Implemented Phase 6: Orchestration & Web tools
- Created `spawn_subtasks` tool for parallel sub-agent execution
- Created `request_clarifications` tool for user questionnaires
- Implemented interactive clarification UI with Rich/prompt-toolkit
- Created `web_search` tool using DuckDuckGo HTML API
- Created `web_fetch` tool for URL content retrieval
- Implemented `PreferenceManager` for learning user preferences
- Integrated preference learning with clarification responses
- Updated orchestrator to inject LLM client and clarification handler
- Total tools now: 11 (file: 3, filesystem: 3, shell: 1, orchestration: 2, web: 2)

### Session 3 (2024-12-29)
- Implemented Phase 7: Comprehensive test suite
  - Created test directory structure with conftest.py
  - Unit tests for all tools (file, filesystem, shell, web, orchestration)
  - Unit tests for tool registry
  - Unit tests for core agents (orchestrator, subagent, react_loop)
  - Unit tests for state management (memory, cache, file_locks, preferences, manager)
  - Integration tests for tool execution and parallel execution
- Implemented Phase 8: Streaming responses
  - Added streaming support to ReAct loop
  - Added streaming configuration to Orchestrator
  - Implemented streaming callbacks in CLI
  - Real-time content output during LLM response generation
- Created verification scripts:
  - `check_tools.py` - Verifies all tools are registered correctly
  - `test_clarification.py` - Direct test of clarification UI
- Verification results:
  - All 11 tools registered and working
  - Clarification UI renders correctly (5/5 tests passed)
- Project status: 100% complete

### Session 4 (2024-12-30)
- Implemented Phase 9: Rules System
  - Created `RulesLoader` class in `config/rules.py`
  - Added `RULES_FILE_NAME` constant ("ESNAAD.md")
  - Updated `llm/messages.py` with `project_rules` parameter
  - Integrated rules loading in orchestrator (lazy loading, cached)
  - Added rules inheritance to sub-agents via coordinator
  - Updated `spawn_subtasks` tool to pass rules to sub-agents
  - Created 16 unit tests for RulesLoader
- Rules feature allows project-specific instructions via ESNAAD.md file
- Project status: Feature complete with rules support

### Session 5 (2024-12-30)
- Implemented Phase 10: UX Improvements & Bug Fixes
  - Added `verify_ssl` setting to skip TLS verification for Open WebUI connections
  - Added thinking spinner ("Esnaad Code is thinking...") during LLM requests
  - Changed input prompt from "You:" to ">"
  - Changed color theme from blue to Claude Code orange (#E57B3A)
  - Added `--no-stream` CLI option for debugging
- Fixed streaming/tool call parsing issues:
  - Added dual format support (OpenAI + Anthropic) in LLM client
  - Added `_parse_anthropic_response()` and `_parse_anthropic_stream_chunk()` methods
  - Handles content blocks with type "text" and "tool_use"
- Fixed Pydantic v2 naming conflict:
  - Renamed `ToolResult` classmethods: `success()` → `create_success()`, `error()` → `create_error()`, `timeout()` → `create_timeout()`
  - Updated all usages in orchestrator.py, subagent.py, and tests
- Implemented parallel tool execution:
  - Tools marked `parallel_safe=True` now execute concurrently via `asyncio.gather()`
  - Sequential tools (requiring locks) still execute one at a time
  - Results maintain original order regardless of execution order
- Added empty response retry logic:
  - When model returns empty response after tool calls, automatically prompts to continue
  - Retry limit: 3 attempts or `max_iterations - 1`, whichever is lower
  - Handles inconsistent model behavior (e.g., Qwen via Open WebUI)
- Enhanced `spawn_subtasks` guidance in system prompt:
  - Added JSON example showing subtask structure with dependencies
  - Added explicit triggers for when to use parallel execution
  - LLM now reliably uses spawn_subtasks for multi-directory/file analysis

### Session 6 (2024-12-31)
- Implemented Phase 11: Plan Mode Toggle
  - Added `requires_approval` attribute to `BaseTool` class
  - Created `state/plan_mode.py` with `ExecutionMode` enum and `PlanModeState` class
  - Marked destructive tools as `requires_approval=True`: write_file, edit_file, run_command
  - Created `cli/ui/tool_approval.py` with `ToolApprovalUI` for approval prompts
  - Added mode indicator display functions in `cli/ui/panels.py`
  - Implemented Shift+Tab key binding via prompt-toolkit `KeyBindings`
  - Added `plan_mode` config and `on_tool_approval` callback to ReActLoop and Orchestrator
  - Wired everything together in `cli/commands/chat.py`
  - Added `/mode` command to toggle between Plan Mode and Auto Edit
- Plan Mode feature:
  - **Shift+Tab** or **/mode** toggles between modes during input
  - **Plan Mode**: Destructive tools pause for user approval (y/n/a)
  - **Auto Edit**: All tools execute automatically (default)
  - Mode indicator shows current state in prompt prefix `[PLAN] >`
  - "Approve All" option to approve remaining tools for current message
- Project status: Feature complete with Plan Mode

### Session 7 (2026-01-02)
- Fixed Phase 12: Todo Completion Bug
  - **Issue**: ReAct loop was exiting prematurely when LLM returned text without tool calls, even with incomplete todos
  - **Root Cause**: Exit logic at `react_loop.py:218-257` only checked for empty responses, not incomplete todos
  - **Fix Implemented (First Attempt)**:
    - Added `todo_manager` parameter to `ReActLoop.__init__()`
    - Added todo completion check before exit (lines 250-269 in react_loop.py)
    - If todos exist and are incomplete, prompts LLM to continue
    - Integrated `TodoManager` from orchestrator into ReAct loop
    - Updated `Orchestrator.run()` to pass `_todo_manager` to ReActLoop
    - Updated `SubAgent` to explicitly pass `todo_manager=None`
  - **Bug in First Fix**: Used `retry_limit_not_reached` condition (iteration < 3), causing check to fail after 3 iterations
  - **Second Fix**: Removed retry limit from todo check - now checks ALWAYS when todos are incomplete
  - **Behavior**: System now detects incomplete todos at any iteration and prompts model to continue
  - **Safety**: `max_iterations` limit still prevents infinite loops
- Project status: Bug fix complete, todo tracking now reliable

## Registered Tools (11 Total)

| Category | Tool | Description |
|----------|------|-------------|
| **File** | `read_file` | Read file contents with line numbers, offset/limit |
| | `write_file` | Create or overwrite files |
| | `edit_file` | Precise text replacement in files |
| **Filesystem** | `list_directory` | List directory contents with recursion |
| | `search_files` | Glob pattern file search |
| | `search_content` | Grep-like content search |
| **Shell** | `run_command` | Execute shell commands with timeout |
| **Orchestration** | `spawn_subtasks` | Execute parallel sub-agents |
| | `request_clarifications` | Interactive user questionnaire |
| **Web** | `web_search` | DuckDuckGo web search |
| | `web_fetch` | Fetch and extract URL content |

## Project Summary

Esnaad Code is now a fully functional Claude Code-style agentic system with:
- **11 tools**: File ops (3), Filesystem (3), Shell (1), Orchestration (2), Web (2)
- **Plan Mode**: Toggle via Shift+Tab or /mode to require approval for destructive tools
- **Parallel execution**: Sub-agent coordination with dependency support
- **Parallel tool execution**: Parallel-safe tools run concurrently via `asyncio.gather()`
- **Interactive clarifications**: Rich-based questionnaire UI with preference learning
- **Streaming responses**: Real-time output during LLM generation
- **Rules system**: Project-specific instructions via ESNAAD.md files
- **Dual API format**: Supports both OpenAI and Anthropic response formats
- **Claude Code theme**: Orange accent color (#E57B3A) with thinking spinner
- **Comprehensive tests**: Unit and integration tests for all components

## Plan Mode

Plan Mode allows users to review and approve destructive tool executions before they run.

### Usage

- **Shift+Tab** during input to toggle mode
- **/mode** command to toggle mode
- Mode indicator shown in prompt: `[PLAN] >` or `>`

### Tool Classification

| Tool | Requires Approval |
|------|-------------------|
| `read_file` | No |
| `write_file` | **Yes** |
| `edit_file` | **Yes** |
| `list_directory` | No |
| `search_files` | No |
| `search_content` | No |
| `run_command` | **Yes** |
| `spawn_subtasks` | No |
| `request_clarifications` | No |
| `web_search` | No |
| `web_fetch` | No |

### Approval Options

When a tool requires approval in Plan Mode:
- **y** - Approve and execute
- **n** - Reject (skip this tool)
- **a** - Approve all remaining tools for this message

### Key Components

- `state/plan_mode.py` - `PlanModeState` class with toggle logic
- `cli/ui/tool_approval.py` - `ToolApprovalUI` for approval prompts
- `cli/ui/prompt.py` - Shift+Tab key binding via `KeyBindings`
- `tools/base.py` - `requires_approval` attribute on `BaseTool`

## Rules System

The rules system allows project-specific instructions to be loaded from an `ESNAAD.md` file in the project root.

### Usage

Create an `ESNAAD.md` file in your project root:

```markdown
# Project Rules

## Code Style
- Use type hints for all functions
- Follow PEP 8 conventions

## Testing
- Write tests for all new features
- Maintain 80% code coverage
```

### How It Works

1. **Loading**: Rules are loaded lazily on first orchestrator run
2. **Caching**: Rules are cached per working directory
3. **Injection**: Rules appear in system prompt as `## Project Rules` section
4. **Inheritance**: Sub-agents automatically receive the same rules

### Key Components

- `RulesLoader` class in `config/rules.py`
- `project_rules` parameter in `llm/messages.py`
- Rules metadata in `ToolContext` for sub-agent spawning

## Future Enhancements (Optional)

Potential future improvements:
1. More tool categories (git, database, API integrations)
2. Multi-model support (different LLMs for different tasks)
3. Persistent conversation history
4. Plugin system for custom tools
5. Web UI alternative to CLI
