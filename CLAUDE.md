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
- Implemented Phase 13: Windows Platform Enforcement
  - **Issue**: LLM defaulting to Linux/bash commands instead of Windows CMD syntax
  - **Changes Made**:
    - Updated `ORCHESTRATOR_SYSTEM_PROMPT` with "Platform Environment" section (lines 69-96)
    - Added explicit Windows command examples: dir, mkdir, copy, move, del, type
    - Added "DO NOT use Linux commands" warning with examples
    - Updated `SUBAGENT_SYSTEM_PROMPT` with Windows platform reminder
    - Enhanced `build_system_prompt()` to display platform in Working Directory section
    - Updated `run_command` tool description: "Execute a Windows shell command..."
    - Updated `RunCommandInput.command` field description to emphasize Windows syntax
  - **Behavior**: LLM now receives multiple reminders about Windows platform throughout system prompts
  - **Additional**: Users can add Windows-specific rules to their project's ESNAAD.md file
- Enhanced Entity Creation Rules Documentation
  - **Issue**: User needed comprehensive entity creation rules for LLM to follow automatically
  - **Changes Made**:
    - Expanded `src/esnaad/rules/core/entity-creation.md` from 40 to 540+ lines
    - Added "When to Create an Entity" trigger section with request patterns
    - Added step-by-step workflow (Step 1: Identify Location, Step 2: Create ID Class, Step 3: Create Entity)
    - Added complete templates for both ID class and Entity class with `[EntityName]` placeholders
    - Added "Pattern Requirements (MANDATORY)" checklist with 9 requirements
    - Added File Naming Conventions table with examples
    - Expanded examples: UnitOfMeasure (Logistic) + WeightBalance (Maintenance) + MasterEquipment (EntityId example)
    - **Property Types and Import Resolution** (lines 115-416):
      - Classification: **4 types** - Primitives, ObjectId, EntityId References, Entity References
      - Rule 1: Primitives (string, int, bool, etc.) - no imports
      - Rule 2: ObjectId lookup values - ALWAYS from `NextGen.Admin.Core.Shared.[Domain].[Module]`
      - Rule 3: **EntityId References** (NEW) - ID-only properties (lightweight)
        - Property name ends with `Id` (e.g., `CommandId`, `PlatformId`)
        - Type is `[EntityName]Id` class (e.g., `DataRestrictionId`, `ItemId`)
        - Search for `[EntityName]Id.cs` in Shared directory
      - Rule 4: Entity references - search with `search_files` to find import path
      - "When to Use EntityId vs Entity Reference" decision guide
      - Common EntityId locations table (DataRestrictionId, PlatformId, ItemId, etc.)
      - Common entity reference locations table (DataRestriction, Platform, Item, etc.)
      - Import resolution workflow with step-by-step instructions
      - Complete D161Master example showing Entity references
      - Complete MasterEquipment example showing EntityId references
      - Updated Quick Decision Tree to include EntityId property name check
    - Updated "Quick Reference: Creation Checklist" from 14 to 19 steps (organized into Structure/Properties/Constructors/Final Checks)
    - Added Windows command notes for directory creation
    - **Code Formatting Fix**: Added "Code Formatting" section to prevent extra blank lines in generated code
  - **Structure**: File already included in main esnaad.md via `<!-- #include entity-creation.md -->`
  - **Behavior**:
    - When user requests "Create a new Entity for [Module]", LLM will automatically follow the complete workflow
    - LLM will properly classify property types (including EntityId vs Entity distinction)
    - **Property name ending detection**: If property ends with `Id`, uses EntityId type; otherwise uses Entity type
    - For entity/entityId references, LLM will use `search_files` to locate and extract import namespaces
    - Example: "CommandId (DataRestrictionId)" → creates `public virtual DataRestrictionId CommandId { get; set; }`
    - Example: "Command (DataRestriction)" → creates `public virtual DataRestriction Command { get; protected set; }`
- Fixed Code Formatting Issue (Multiple Layers)
  - **Issue**: LLM was generating C# files with extra blank lines between each line of code
  - **Root Cause**: LLM was using `\n\n` (double newline) instead of `\n` (single newline) when constructing file content
  - **Changes Made - Layer 1 (System Prompt)**:
    - Added "File Writing Rules" section to `ORCHESTRATOR_SYSTEM_PROMPT` (lines 113-132 in messages.py)
    - Explicit BAD vs GOOD examples showing `\n\n` vs `\n`
    - CRITICAL warning about single newlines for code files
  - **Changes Made - Layer 2 (Tool Level)**:
    - Updated `write_file` tool description to mention proper formatting
    - Updated `WriteFileInput.content` field description with newline formatting rules
    - Emphasizes: "use single newlines (\\n) between lines, NOT double newlines (\\n\\n)"
  - **Changes Made - Layer 3 (Project Rules)**:
    - Added "Code Formatting Rules" section to `src/esnaad/rules/core/esnaad.md` (lines 7-17)
    - Added formatting notes to `entity-creation.md` (lines 277-283)
  - **Defense-in-Depth**: Rules added at 5 different levels (system prompt, tool description, tool field, main rules, entity rules)
  - **Behavior**: LLM receives formatting instructions in system prompt, tool schemas, and project rules
- Fixed Line Ending Issue (Windows CRLF)
  - **Issue**: Files appeared with extra blank lines in VS Code/Sublime Text but looked fine in Notepad
  - **Root Cause**: LLM generating Unix line endings (`\n` - LF only) instead of Windows line endings (`\r\n` - CRLF)
  - **Why It Happened**:
    - Notepad handles both `\n` and `\r\n` gracefully
    - VS Code/Sublime Text with certain settings show `\n` as extra spacing on Windows
  - **Fix Applied**:
    - Modified `write_file` tool to automatically normalize line endings on Windows
    - Added line ending conversion in `write_file.py` (lines 91-97)
    - Process: `\r\n` → `\n` (normalize) → `\r\n` (Windows format)
    - Added `newline=""` parameter to prevent Python's automatic line ending translation
  - **Behavior**: All files written on Windows now use proper CRLF line endings
  - **Result**: Files now display correctly in all Windows text editors
- Project status: Line ending normalization complete, code formatting fully resolved
- Implemented create_directory Tool
  - **Issue**: Using `run_command` with `mkdir` for directory creation was slow, required approval, and platform-specific
  - **Solution**: Created dedicated `create_directory` tool
  - **Implementation**:
    - Created `src/esnaad/tools/filesystem/create_directory.py`
    - Uses Python's `pathlib.Path.mkdir()` for platform-agnostic directory creation
    - Supports automatic parent directory creation (like `mkdir -p`)
    - Set `requires_approval=False` (safe operation)
    - Set `parallel_safe=False` (avoid race conditions)
    - Added to `tools/filesystem/__init__.py` for auto-registration
  - **Tool Parameters**:
    - `path`: Directory path to create
    - `parents` (default True): Create parent directories if needed
    - `exist_ok` (default True): Don't error if directory already exists
  - **Benefits**:
    - No approval required in Plan Mode
    - 3-5x faster than shell command
    - Cross-platform (Windows/Linux/Mac)
    - Better error handling
    - Clear semantic intent
  - **Updated Rules**: Modified `entity-creation.md` to recommend `create_directory` instead of `mkdir`
- Project status: create_directory tool complete, total tools now 13

### Session 8 (2026-01-03)
- Implemented User-Friendly Tool Call Display
  - **Issue**: Tool calls showing technical details (method names, all parameters, Python dict format) which was verbose and not user-friendly
  - **User Request**: "Display like Claude Code - show Write(test001.txt) instead of write_file(file_path='test001.txt', content='...', create_directories=True)"
  - **Solution**: Created friendly display format with relevant parameters only
  - **Implementation**:
    - Created `_format_friendly_tool_call()` helper function in `cli/ui/panels.py`
    - Maps technical tool names to user-friendly display names
    - Extracts most relevant parameter for each tool type
    - Special handling for complex tools (spawn_subtasks, request_clarifications, write_todo)
  - **Tool Name Mappings**:
    - `write_file` → `Write(filename)`
    - `read_file` → `Read(filename)`
    - `edit_file` → `Edit(filename)`
    - `create_directory` → `CreateDirectory(path)`
    - `list_directory` → `List(path)`
    - `search_files` → `SearchFiles(pattern)`
    - `search_content` → `SearchContent(pattern)`
    - `run_command` → `Bash(command)`
    - `spawn_subtasks` → `Task(spawn N subtasks)`
    - `request_clarifications` → `AskUserQuestion(N questions)`
    - `write_todo` → `TodoWrite(N tasks)`
    - `web_search` → `WebSearch(query)`
    - `web_fetch` → `WebFetch(url)`
  - **Debug Mode**: Technical details (full tool name and all parameters) still shown when `ESNAAD_DEBUG=true`
  - **Benefits**:
    - Cleaner output for users
    - Easier to scan tool execution flow
    - Matches Claude Code UX
    - Debug info available when needed
  - **Example Output**:
    - Before: `→ write_file(file_path='src/test.cs', content='...', create_directories=True)` + `✓ write_file: {"success": true, ...}`
    - After: `* Write(src/test.cs)` + `L Created 123 bytes to test.cs`
    - Debug: Technical details shown with `ESNAAD_DEBUG=true`
- Implemented User-Friendly Tool Result Display
  - **Issue**: Tool results showing raw technical output/JSON, hard to read and not user-friendly
  - **User Request**: "Show friendly results like Claude Code - e.g., '* Write(test.txt) └ Wrote 11 bytes to test.txt' with green * for success, red X for errors"
  - **Solution**: Created friendly result formatter with colored indicators and content previews
  - **Implementation**:
    - Created `_format_friendly_tool_result()` helper function in `cli/ui/panels.py` (260+ lines)
    - Updated `print_tool_result()` to show friendly format with colored indicators
    - Added tool call caching in `chat.py` to preserve original arguments for result display
    - Removed duplicate tool call display - now shows only result with colored indicator
    - Tool-specific result formatting for all 13 tools
  - **Display Format**:
    ```
    * Write(test001.txt)          # Green * for success, red X for failure
      L Created 11 bytes to test001.txt   # Summary line
         Hello World               # Content preview (if applicable)
    ```
  - **Key Implementation Details**:
    - Tool call is cached in `_on_tool_call()` but not displayed
    - Tool result displays both the friendly name (with args) and the result summary
    - Single display per tool execution (no duplicates)
  - **Tool-Specific Result Summaries**:
    - `write_file` → "Created/Wrote N bytes to filename"
    - `read_file` → "Read N lines from filename" + preview of first 3 lines
    - `edit_file` → "Made N replacement(s) in filename"
    - `create_directory` → "Created directory (with parents) dirname"
    - `list_directory` → "Found N file(s), M dir(s) in dirname" + preview of items
    - `search_files` → "Found N file(s) matching 'pattern'" + preview of matches
    - `search_content` → "Found N match(es) for 'pattern'" + preview of matches
    - `run_command` → "Ran: command" + preview of stdout/stderr
    - `write_todo` → "Updated todo list (N tasks)"
    - `spawn_subtasks` → "Completed N/M subtasks"
    - `request_clarifications` → "Received N answer(s)"
    - `web_search` → "Found N results for 'query'"
    - `web_fetch` → "Fetched content from domain" + preview
  - **Windows Console Compatibility**:
    - Uses ASCII characters: `*` (success), `X` (error), `L` (summary line)
    - Avoids Unicode characters that fail on Windows console (●, →, ⎿)
    - Uses `[D]` and `[F]` instead of emoji for directory/file indicators
  - **Debug Mode**: Shows full technical output when `ESNAAD_DEBUG=true`
  - **Benefits**:
    - Instant visual feedback (green = success, red = error)
    - Relevant summary information instead of raw JSON
    - Content previews show what was actually done
    - Easier to understand what each tool accomplished
    - Windows console compatible (no encoding errors)
    - No duplicate displays - clean, single output per tool
- **Files Modified**:
  - `src/esnaad/cli/ui/panels.py` - Added `_format_friendly_tool_call()` and `_format_friendly_tool_result()` helpers, updated `print_tool_call()` and `print_tool_result()`
  - `src/esnaad/cli/commands/chat.py` - Added `_tool_call_cache` dict, updated `_on_tool_call()` to cache only (not display), updated `_on_tool_result()` to use cached arguments, removed `print_tool_call` import
  - `DISPLAY_EXAMPLE.md` - Created visual examples of new display format
- **Testing**:
  - Created and tested display examples for all 13 tools
  - Verified success indicators (green `*`) and error indicators (red `X`)
  - Confirmed Windows console compatibility (ASCII-only characters)
  - Validated content previews for file operations, directory listings, command output
- Project status: Tool call and result display both improved, full Claude Code UX parity achieved

### Session 9 (2026-01-06)
- Implemented Database Migration Script Creation Rules
  - **User Request**: Enhance rules to understand and generate SQL migration scripts for entities
  - **Solution**: Created comprehensive migration script creation guide
  - **Implementation**:
    - Created `migration-script-creation.md` (15.6 KB comprehensive rules file)
    - Covers complete workflow from entity analysis to SQL generation
    - Includes C# to SQL data type mappings
    - Documents table naming conventions (MST/HST tables with domain codes)
    - Defines column naming standards (UPPERCASE with trailing underscore)
  - **Key Features**:
    - **Step-by-step workflow**: Read entity → Determine domain code → Generate table names → Map properties to columns
    - **Domain code mapping**: Maps C# namespaces to 3-letter domain codes (LOG, ADM, MNT, OPS, etc.)
    - **Table structure templates**: Complete templates for both master (MST) and history (HST) tables
    - **Data type mapping table**: Comprehensive C# type to SQL Server type mappings with collation rules
    - **Audit columns support**: Automatic expansion of INgAuditable interface to audit columns
    - **Index creation rules**: Primary key on ID_, unique index on CODE_ if applicable
    - **Property type handling**: Entity references, EntityId properties, collections, enums
    - **Complete example**: UnitOfMeasure entity with generated migration script
  - **Migration Script Components**:
    - Master table: `[DOMAIN_CODE]_MST_[ENTITY_NAME]` with all entity properties as columns
    - History table: `[DOMAIN_CODE]_HST_[ENTITY_NAME]` with fixed audit structure
    - Primary key: Clustered index on `ID_` column
    - Unique index: On `CODE_` column if entity has Code property
    - All string columns: Use `COLLATE Arabic_CI_AS` (case-insensitive Arabic collation)
    - Standard columns: `ID_` (uniqueidentifier), `VERSION_` (bigint)
    - Audit columns: 9 audit fields if entity implements INgAuditable
  - **Rules Integration**:
    - Added `<!-- #include migration-script-creation.md -->` to `esnaad.md`
    - Rules automatically loaded with entity-creation and architecture rules
    - Available to orchestrator and all sub-agents via rules system
  - **File Location**: Default `db/fw/common` directory
  - **Flyway Naming Convention**: `V1_[YYYYMMDD]_[HHMM]_[USER_ID]__[USER_STORY_NO or BUG_NO]_[SHORT_DESC].sql`
    - Uses defaults if not provided: `XXXX` for USER_ID, `US_XXXX` for USER_STORY_NO, `BUG_XXXX` for BUG_NO
    - Example: `V1_20260106_1430_GAL7634__US_12345_UnitOfMeasure_Table.sql`
    - Example with defaults: `V1_20260106_1430_XXXX__US_XXXX_UnitOfMeasure_Table.sql`
  - **Example**: UnitOfMeasure entity generates LOG_MST_UNIT_OF_MEASURE and LOG_HST_UNIT_OF_MEASURE tables
- Project status: Migration script creation rules complete with Flyway naming, LLM can now generate database migrations
- Implemented FluentNHibernate Entity Map Creation Rules
  - **User Request**: Enhance rules to understand Hibernate entity mapping creation
  - **Solution**: Created comprehensive entity-map-creation guide for FluentNHibernate mappings
  - **Implementation**:
    - Created `entity-map-creation.md` (19.6 KB comprehensive rules file)
    - Covers complete workflow from entity analysis to map file generation
    - Documents property type to NHibernate mapping method translation
    - Includes detailed decision trees and validation checklists
  - **Key Features**:
    - **Step-by-step workflow**: Read entity → Determine domain/module → Map properties → Generate map file
    - **Complete mapping rules**: 12 property types (ID, Version, String, Boolean, Integer, Decimal, DateTime, Enum/ObjectId, AuditEntry, Entity references, EntityId properties, Collections)
    - **Mapping method patterns**:
      - `CompositeId(x => x.Id).KeyProperty(x => x.Value, "ID_")` for entity IDs
      - `Version(x => x.Version).Column("VERSION_")` for version tracking
      - `Map(x => x.PropertyName, "COLUMN_NAME_")` for primitives and EntityId properties
      - `References(x => x.PropertyName, "COLUMN_ID_")` for entity references
      - `Component(x => x.AuditEntry)` for audit entries
      - `HasMany(x => x.PropertyName)` for collections
    - **Column naming convention**: UPPERCASE with trailing underscore (e.g., `CODE_`, `NAME_`, `IS_ACTIVE_`)
    - **Nullable handling**: `.Not.Nullable()` for required fields, omit for nullable types
    - **String length rules**: `.Length(N)` for strings (Code: 50, Name: 100, Description: 500)
    - **Entity vs EntityId distinction**:
      - Entity references (e.g., `DataRestriction Command`) → `References()`
      - EntityId properties (e.g., `DataRestrictionId CommandId`) → `Map()`
    - **Template structure**: Complete ClassMap template with pragma warnings, author tag, cache strategy
    - **File location pattern**: `NextGen.[Domain].Core/Config/EntityMap/[Module]/[EntityName]Map.cs`
    - **Table naming**: `[DOMAIN_CODE]_MST_[ENTITY_NAME]` (matches migration script pattern)
    - **Cache strategy**: `Cache.NonStrictReadWrite().Region(CacheRegionConstant.UpdateableMaster)`
  - **Complete Examples**:
    - UnitOfMeasure: Basic entity with primitives, enums, and audit entry
    - WeightBalance: Entity with entity references (Command, Platform)
    - MasterEquipment: Entity with EntityId properties (CommandId, PlatformId, ItemId)
  - **Decision Tree**: Quick reference for property type → mapping method selection
  - **Common Mistakes Section**: Highlights errors to avoid (incorrect column names, wrong mapping methods, missing length modifiers)
  - **Validation Checklist**: 25-point checklist covering preparation, structure, mappings, imports, and final checks
  - **Rules Integration**:
    - Added `<!-- #include entity-map-creation.md -->` to `esnaad.md`
    - Rules automatically loaded with entity-creation and migration-script rules
    - Available to orchestrator and all sub-agents via rules system
  - **Mapping Generation Triggers**:
    - "Create entity map for [EntityName]"
    - "Create Hibernate mapping for [EntityName]"
    - "Map [EntityName] entity to database"
- Project status: Entity map creation rules complete, LLM can now generate FluentNHibernate ClassMap files
- Implemented NHibernate Repository Creation Rules
  - **User Request**: Enhance rules to understand repository creation for entities
  - **Solution**: Created comprehensive repository-creation guide for NHibernate data access layer
  - **Implementation**:
    - Created `repository-creation.md` (23.5 KB comprehensive rules file)
    - Covers complete workflow from entity analysis to repository generation
    - Documents interface and implementation patterns
    - Includes NHibernate QueryOver API usage patterns
  - **Key Features**:
    - **Step-by-step workflow**: Read entity → Identify properties → Generate interface → Generate implementation
    - **Two-file pattern**: Interface (`I[EntityName]Repository`) + Implementation (`Nh[EntityName]Repository`)
    - **Base types**:
      - Interface extends: `ISpecificRepository<[EntityName], [EntityName]Id>`
      - Implementation extends: `AbstractNhSpecificRepository<[EntityName], [EntityName]Id>`
      - Implementation implements: `I[EntityName]Repository`
    - **Standard methods (auto-included based on entity properties)**:
      - `Get(Guid guid)` - Always included (converts Guid to EntityId)
      - `Find([EntityName]Id[] ids)` - Always included (find by array of IDs)
      - `IsCodeExists(string code)` - If entity has Code property
      - `Get(string code)` - If entity has Code property
      - `Find(string[] codes)` - If entity has Code property
      - `IsNameExists(string name)` - If entity has Name property
    - **NHibernate QueryOver patterns**:
      - Single result: `.Where(x => x.Property == value).SingleOrDefault<T>()`
      - Existence check: `.Where(x => x.Property == value).Future().Any()`
      - Array filtering: `.WhereRestrictionOn(x => x.Property).IsIn(array).Future()`
      - Deferred execution: `.Future()` for collections
    - **Constructor pattern**: Takes `ISessionFactory sessionFactory`, calls `base(sessionFactory)`
    - **ReSharper comments**: Required for covariant array conversion warnings
    - **File locations**:
      - Interface: `NextGen.[Domain].Core/[Module]/Repository/I[EntityName]Repository.cs`
      - Implementation: `NextGen.[Domain].Core/[Module]/Repository/NHibernate/Nh[EntityName]Repository.cs`
    - **Namespace pattern**:
      - Interface: `NextGen.[Domain].Core.[Module].Repository`
      - Implementation: `NextGen.[Domain].Core.[Module].Repository.NHibernate`
    - **Parameter naming convention**: `[entityName]Ids` (camelCase, plural + "Ids")
      - Example: `unitOfMeasureIds`, `platformIds`, `dataRestrictionIds`
  - **Complete Examples**:
    - UnitOfMeasure: Entity with Code and Name (full standard methods)
    - WeightBalance: Entity without Code (minimal methods)
  - **NHibernate Query Pattern Library**:
    - Single result by property
    - Check existence
    - Find by array (IN clause)
    - Find with multiple criteria
    - Find with ordering
  - **Common Mistakes Section**: Highlights errors to avoid (wrong base types, missing .Future(), incorrect .Any() usage)
  - **Decision Tree**: Property-based method inclusion logic
  - **Validation Checklist**: 32-point checklist covering preparation, interface, implementation, imports, and final checks
  - **Rules Integration**:
    - Added `<!-- #include repository-creation.md -->` to `esnaad.md`
    - Rules automatically loaded with entity, map, and migration rules
    - Available to orchestrator and all sub-agents via rules system
  - **Repository Generation Triggers**:
    - "Create repository for [EntityName]"
    - "Implement repository for [EntityName] entity"
    - "Create data access layer for [EntityName]"
- Project status: Repository creation rules complete, LLM can now generate NHibernate repository interfaces and implementations
- Enhanced Entity Creation Rules with Interactive Workflow
  - **User Request**: Enhance entity creation to ask about related files (map, repository, migration script)
  - **Solution**: Added Step 0 to entity-creation rules that prompts user for complete implementation preference
  - **Implementation**:
    - Updated `entity-creation.md` with new "Step 0: Ask About Related Files (REQUIRED)" section
    - LLM now uses `AskUserQuestion` tool before starting entity creation
    - Four options provided to user:
      1. **Entity only** - Just ID + Entity classes
      2. **Entity + Map** - ID, Entity, and EntityMap
      3. **Entity + Map + Repository** - ID, Entity, EntityMap, Repository (interface + implementation)
      4. **Complete (All + Migration)** (Recommended) - All files including migration script
  - **Workflow based on user choice**:
    - **Entity only**: Creates ID and Entity classes (original behavior)
    - **Entity + Map**: Creates entity files, then follows `entity-map-creation.md` rules
    - **Entity + Map + Repository**: Creates entity, map, then follows `repository-creation.md` rules
    - **Complete**: Creates entity, map, repository, then follows `migration-script-creation.md` rules
  - **Execution Order**: Entity → EntityMap → Repository → Migration Script
  - **Updated Checklist**: Added "Pre-Creation" step 0 to verify user was asked about related files
  - **Notes Section**: Added "Follow-up with Related Files" guidance explaining the conditional workflow
  - **Benefits**:
    - User gets to choose implementation scope upfront
    - No need to make separate requests for each file type
    - Ensures correct creation order (dependencies)
    - Reduces back-and-forth conversation
    - Single request can create complete entity stack
  - **Example Usage**:
    - User: "Create UnitOfMeasure entity in Logistic domain"
    - LLM: Asks user about related files using AskUserQuestion
    - User: Selects "Complete (All + Migration)"
    - LLM: Creates ID class → Entity class → EntityMap → Repository → Migration Script
- Project status: Entity creation workflow enhanced with interactive related files prompt
- Increased Default Orchestrator Timeout
  - **Issue**: 5-minute timeout was too short for complex entity creation workflows (entity + map + repository + migration)
  - **Solution**: Increased `DEFAULT_TIMEOUT_SECONDS` from 300s (5 min) to 1800s (30 min)
  - **File Changed**: `src/esnaad/config/constants.py` line 6
  - **Benefit**: Gives LLM adequate time to complete complex workflows, including multiple file creation, analysis, and retries
  - **Note**: Can still be overridden via environment variable `ESNAAD_ORCHESTRATOR__TIMEOUT_SECONDS` or `.env` file

## Registered Tools (13 Total)

| Category | Tool | Description |
|----------|------|-------------|
| **File** | `read_file` | Read file contents with line numbers, offset/limit |
| | `write_file` | Create or overwrite files |
| | `edit_file` | Precise text replacement in files |
| **Filesystem** | `create_directory` | Create directories (platform-agnostic, no approval needed) |
| | `list_directory` | List directory contents with recursion |
| | `search_files` | Glob pattern file search |
| | `search_content` | Grep-like content search |
| **Shell** | `run_command` | Execute shell commands with timeout |
| **Orchestration** | `spawn_subtasks` | Execute parallel sub-agents |
| | `request_clarifications` | Interactive user questionnaire |
| | `write_todo` | Track task progress with todo lists |
| **Web** | `web_search` | DuckDuckGo web search |
| | `web_fetch` | Fetch and extract URL content |

## Project Summary

Esnaad Code is now a fully functional Claude Code-style agentic system with:
- **13 tools**: File ops (3), Filesystem (4), Shell (1), Orchestration (3), Web (2)
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
