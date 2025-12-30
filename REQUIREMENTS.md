# REQUIREMENTS.md — Esnaad Code - Claude Code-Style Agent Architecture

## Overview

Esnaad Code is an agentic system that mirrors Claude Code's architecture: a **single orchestrator agent** with the ability to spawn **parallel sub-agents** for independent subtasks, using a ReAct-style (Reasoning + Acting) loop with tool use.

Currently it will be used to connect to Open WebUI rest API or OpenAI-compatible. Mostly used in windows environment. 

---

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
    │           │   │           │   │           │
    │ Own loop  │   │ Own loop  │   │ Own loop  │
    │ Own tools │   │ Own tools │   │ Own tools │
    └───────────┘   └───────────┘   └───────────┘
          │               │               │
          └───────────────┴───────────────┘
                          │
                    ┌─────▼─────┐
                    │  Shared   │
                    │  State    │
                    │ (files,   │
                    │  memory)  │
                    └───────────┘
```

---

## Core Components

### 1. Orchestrator Agent

**Responsibilities:**
- Parse and understand user intent
- Decompose complex tasks into subtasks
- Determine task dependencies (what can run in parallel)
- Dispatch subtasks to sub-agents
- Aggregate and synthesize results
- Handle errors and retries
- Maintain conversation history

**Implementation Requirements:**
- Single entry point for all user requests
- ReAct loop: Reason → Act → Observe → Repeat
- Maximum iteration limit (default: 50 iterations)
- Timeout handling (default: 5 minutes per task)

### 2. Sub-Agent Pool

**Responsibilities:**
- Execute isolated subtasks
- Run own ReAct loop with scoped tools
- Return structured results to orchestrator
- Handle task-specific errors

**Implementation Requirements:**
- Stateless execution (all context passed in)
- Scoped tool access (only tools relevant to subtask)
- Structured output format (JSON)
- Independent context window (no shared conversation history)

### 3. Tool System

**Core Tools Required:**

| Tool | Description | Parallel Safe |
|------|-------------|---------------|
| `read_file` | Read file contents with line range support | ✅ |
| `write_file` | Create or overwrite files | ⚠️ Lock required |
| `edit_file` | Surgical edits (search/replace) | ⚠️ Lock required |
| `list_directory` | List files and folders | ✅ |
| `search_files` | Find files by name pattern | ✅ |
| `search_content` | Grep/search inside files | ✅ |
| `run_command` | Execute shell commands | ⚠️ Depends on command |
| `web_search` | Search the internet | ✅ |
| `web_fetch` | Fetch URL contents | ✅ |

**Tool Definition Schema:**
```json
{
  "name": "tool_name",
  "description": "Clear description of what the tool does",
  "input_schema": {
    "type": "object",
    "properties": {
      "param1": { "type": "string", "description": "..." }
    },
    "required": ["param1"]
  }
}
```

### 4. Shared State Manager

**Responsibilities:**
- File system access (read/write coordination)
- Memory/context storage
- Lock management for write operations
- Result caching

**Implementation Requirements:**
- File-based state (working directory)
- Optional: Key-value store for cross-agent memory
- Mutex/lock for concurrent writes to same file

---

## Agent Loop Specification

### Main Orchestrator Loop

```
FUNCTION orchestrator_loop(user_message):
    messages = [user_message]
    iteration = 0
    
    WHILE iteration < MAX_ITERATIONS:
        response = call_llm(messages, tools=ORCHESTRATOR_TOOLS)
        
        IF response.stop_reason == "end_turn":
            RETURN response.content
        
        IF response.has_tool_calls:
            FOR tool_call IN response.tool_calls:
                IF tool_call.name == "spawn_subtasks":
                    results = execute_parallel_subtasks(tool_call.input)
                ELSE:
                    result = execute_tool(tool_call)
                
                messages.append(tool_result)
        
        iteration += 1
    
    RETURN "Max iterations reached"
```

### Sub-Agent Loop

```
FUNCTION subtask_loop(task_prompt, allowed_tools):
    messages = [task_prompt]
    iteration = 0
    
    WHILE iteration < SUBTASK_MAX_ITERATIONS:
        response = call_llm(messages, tools=allowed_tools)
        
        IF response.stop_reason == "end_turn":
            RETURN {
                "status": "complete",
                "result": response.content
            }
        
        IF response.has_tool_calls:
            FOR tool_call IN response.tool_calls:
                result = execute_tool(tool_call)
                messages.append(tool_result)
        
        iteration += 1
    
    RETURN {"status": "incomplete", "partial": messages}
```

---

## Parallel Execution System

### Task Decomposition

The orchestrator uses a special tool to decompose and parallelize:

```json
{
  "name": "spawn_subtasks",
  "description": "Decompose current task into independent subtasks that can run in parallel. Only use when subtasks have no dependencies on each other.",
  "input_schema": {
    "type": "object",
    "properties": {
      "subtasks": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": { "type": "string" },
            "description": { "type": "string" },
            "prompt": { "type": "string" },
            "tools": { 
              "type": "array", 
              "items": { "type": "string" },
              "description": "List of tool names this subtask needs"
            }
          },
          "required": ["id", "description", "prompt", "tools"]
        }
      }
    },
    "required": ["subtasks"]
  }
}
```

### Parallel Execution Requirements

- Use async/await for concurrent execution
- Fan-out: dispatch all independent subtasks simultaneously  
- Fan-in: wait for all subtasks, aggregate results
- Timeout per subtask (default: 2 minutes)
- Retry failed subtasks (max 2 retries)
- Return partial results if some subtasks fail

### Dependency Handling

For tasks with dependencies, use sequential chaining:

```
Task A ──► Task B ──► Task C (sequential, B needs A's output)
              │
              └──► Task D ──┐
              └──► Task E ──┼──► Task F (D,E parallel, F needs both)
                            │
```

---

## Interactive Clarification System

### Overview

Before diving into planning or execution, the agent can gather requirements through a **structured questionnaire interface**. This is triggered when:

- Task is ambiguous or underspecified
- Multiple valid approaches exist
- User preferences are needed (tech stack, style, etc.)
- Scope needs to be defined

This reduces back-and-forth and produces better plans by frontloading key decisions.

### Flow

```
┌──────────────────┐
│   User Request   │
│  "Build a login  │
│     system"      │
└────────┬─────────┘
         ▼
┌──────────────────────────────────────┐
│     AMBIGUITY DETECTION              │
│  - Is task well-specified?           │
│  - Are there major decision points?  │
│  - Multiple valid approaches?        │
└────────┬─────────────────────────────┘
         ▼
┌──────────────────────────────────────┐
│     GENERATE CLARIFICATIONS          │
│  - Identify key questions (max 5)    │
│  - Determine question types          │
│  - Provide sensible defaults         │
└────────┬─────────────────────────────┘
         ▼
┌──────────────────────────────────────┐
│     PRESENT TABBED INTERFACE         │
│                                      │
│  [Tab 1] [Tab 2] [Tab 3] [Tab 4]     │
│  ┌────────────────────────────────┐  │
│  │ Authentication Method?         │  │
│  │                                │  │
│  │ ○ Email/Password              │  │
│  │ ○ OAuth (Google, GitHub)      │  │
│  │ ○ Magic Link                  │  │
│  │ ● All of the above            │  │
│  └────────────────────────────────┘  │
│                                      │
│           [Submit All]               │
└────────┬─────────────────────────────┘
         ▼
┌──────────────────────────────────────┐
│     PROCEED TO PLANNING              │
│  (with user preferences locked in)   │
└──────────────────────────────────────┘
```

### Question Types

| Type | Use Case | UI Element |
|------|----------|------------|
| `single_select` | One option from list | Radio buttons |
| `multi_select` | Multiple options allowed | Checkboxes |
| `yes_no` | Binary decision | Toggle or two buttons |
| `text_input` | Free-form answer | Text field |
| `scale` | Priority or importance | Slider (1-5) |
| `confirm` | Verify assumption | Yes/No with context |

### Clarification Tool

```json
{
  "name": "request_clarifications",
  "description": "Present a structured questionnaire to gather requirements before planning. Use when task is ambiguous or has multiple valid approaches. Maximum 5 questions.",
  "input_schema": {
    "type": "object",
    "properties": {
      "context": {
        "type": "string",
        "description": "Brief explanation of why clarification is needed"
      },
      "questions": {
        "type": "array",
        "maxItems": 5,
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "string",
              "description": "Unique identifier for the question"
            },
            "question": {
              "type": "string",
              "description": "The question to ask"
            },
            "type": {
              "type": "string",
              "enum": ["single_select", "multi_select", "yes_no", "text_input", "scale", "confirm"]
            },
            "options": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "value": { "type": "string" },
                  "label": { "type": "string" },
                  "description": { "type": "string" }
                },
                "required": ["value", "label"]
              },
              "description": "Options for single_select and multi_select types"
            },
            "default": {
              "type": ["string", "array", "boolean"],
              "description": "Default value if user skips"
            },
            "required": {
              "type": "boolean",
              "default": false
            },
            "help_text": {
              "type": "string",
              "description": "Additional context shown below the question"
            }
          },
          "required": ["id", "question", "type"]
        }
      },
      "allow_skip": {
        "type": "boolean",
        "default": true,
        "description": "Allow user to skip with defaults"
      }
    },
    "required": ["context", "questions"]
  }
}
```

### Example Clarification Request

**User Input:** "Build me an authentication system"

**Agent Clarification:**

```json
{
  "context": "I'll build an authentication system for you. A few quick questions to make sure I build exactly what you need:",
  "questions": [
    {
      "id": "auth_method",
      "question": "Which authentication methods do you need?",
      "type": "multi_select",
      "options": [
        {"value": "email_password", "label": "Email/Password", "description": "Traditional login"},
        {"value": "oauth_google", "label": "Google OAuth", "description": "Sign in with Google"},
        {"value": "oauth_github", "label": "GitHub OAuth", "description": "Sign in with GitHub"},
        {"value": "magic_link", "label": "Magic Link", "description": "Passwordless email link"},
        {"value": "passkey", "label": "Passkeys", "description": "WebAuthn biometric"}
      ],
      "default": ["email_password"],
      "help_text": "You can always add more methods later"
    },
    {
      "id": "session_strategy",
      "question": "How should sessions be managed?",
      "type": "single_select",
      "options": [
        {"value": "jwt", "label": "JWT Tokens", "description": "Stateless, good for APIs"},
        {"value": "session", "label": "Server Sessions", "description": "Traditional, stored in DB/Redis"},
        {"value": "hybrid", "label": "Hybrid", "description": "JWT for API, sessions for web"}
      ],
      "default": "jwt"
    },
    {
      "id": "include_2fa",
      "question": "Include two-factor authentication (2FA)?",
      "type": "yes_no",
      "default": false,
      "help_text": "TOTP-based (Google Authenticator, etc.)"
    },
    {
      "id": "tech_stack",
      "question": "What's your backend stack?",
      "type": "single_select",
      "options": [
        {"value": "node_express", "label": "Node.js + Express"},
        {"value": "node_fastify", "label": "Node.js + Fastify"},
        {"value": "nextjs", "label": "Next.js (App Router)"},
        {"value": "python_fastapi", "label": "Python + FastAPI"},
        {"value": "python_django", "label": "Python + Django"}
      ],
      "required": true
    },
    {
      "id": "additional_features",
      "question": "Any additional features?",
      "type": "multi_select",
      "options": [
        {"value": "password_reset", "label": "Password Reset Flow"},
        {"value": "email_verify", "label": "Email Verification"},
        {"value": "rate_limit", "label": "Rate Limiting"},
        {"value": "audit_log", "label": "Audit Logging"},
        {"value": "admin_panel", "label": "Admin User Management"}
      ],
      "default": ["password_reset", "email_verify"]
    }
  ],
  "allow_skip": true
}
```

### CLI Rendering

```
╔══════════════════════════════════════════════════════════════════════╗
║                     BEFORE WE START                                  ║
║  I'll build an authentication system for you. A few quick questions  ║
║  to make sure I build exactly what you need:                         ║
╠══════════════════════════════════════════════════════════════════════╣

  [1/5] [2/5] [3/5] [4/5] [5/5]              ← Tab navigation
  ━━━━━

  Authentication Methods? (select multiple)
  
  [x] Email/Password          Traditional login
  [ ] Google OAuth            Sign in with Google  
  [ ] GitHub OAuth            Sign in with GitHub
  [ ] Magic Link              Passwordless email link
  [ ] Passkeys                WebAuthn biometric
  
  ℹ️  You can always add more methods later

  [Space] Toggle  [Enter] Next  [Tab] Skip to end  [Esc] Use defaults
  
╚══════════════════════════════════════════════════════════════════════╝
```

### Clarification Response Schema

```json
{
  "clarification_id": "uuid",
  "responses": {
    "auth_method": ["email_password", "oauth_google"],
    "session_strategy": "jwt",
    "include_2fa": true,
    "tech_stack": "nextjs",
    "additional_features": ["password_reset", "email_verify", "rate_limit"]
  },
  "skipped": false,
  "used_defaults": ["additional_features"]
}
```

### When to Request Clarification

The agent should request clarification when:

| Trigger | Example |
|---------|---------|
| Ambiguous scope | "Build a dashboard" — what kind? |
| Multiple valid approaches | "Add auth" — JWT vs sessions? |
| Tech stack unknown | "Create an API" — language/framework? |
| Conflicting requirements | Detected incompatible choices |
| High-effort task | >30 min estimated — confirm scope first |
| Missing critical info | "Deploy this" — where? |

The agent should **NOT** request clarification when:

- Task is specific enough ("Add a logout button to the navbar")
- Context provides answers (AGENT.md has tech stack)
- User said "just use defaults" or "your choice"
- Follow-up to previous clarified task
- Simple queries or questions

### Integration with Plan Mode

```
User Request
     │
     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Clarify?    │────►│ Clarifi-    │────►│   Plan      │
│ (analyze)   │ Yes │ cations     │     │   Mode      │
└─────────────┘     └─────────────┘     └─────────────┘
     │ No                                      │
     └────────────────────────────────────────►│
                                               ▼
                                        ┌─────────────┐
                                        │  Execute    │
                                        └─────────────┘
```

### Orchestrator Loop with Clarifications

```
FUNCTION orchestrator_loop_with_clarifications(user_message, mode):
    
    # STEP 1: Check if clarification needed
    analysis = call_llm(
        messages=[user_message],
        tools=[analyze_task_tool],
        system="Analyze if this task needs clarification before planning."
    )
    
    IF analysis.needs_clarification:
        
        # STEP 2: Generate and present questions
        clarification_request = call_llm(
            messages=[user_message],
            tools=[request_clarifications_tool],
            system="Generate up to 5 clarifying questions."
        )
        
        # STEP 3: Get user responses (blocking)
        responses = present_clarification_ui(clarification_request)
        
        # STEP 4: Enrich original message with responses
        enriched_message = f"""
            Original request: {user_message}
            
            User preferences:
            {format_responses(responses)}
        """
        
        RETURN orchestrator_loop_with_plan_mode(enriched_message, mode)
    
    ELSE:
        RETURN orchestrator_loop_with_plan_mode(user_message, mode)
```

### Configuration

```bash
# Clarification settings
CLARIFY_ENABLED=true                    # Enable/disable clarification step
CLARIFY_MAX_QUESTIONS=5                 # Maximum questions per clarification
CLARIFY_SKIP_FOR_SIMPLE_TASKS=true      # Skip for well-specified tasks
CLARIFY_AUTO_USE_DEFAULTS_TIMEOUT=300   # Auto-proceed with defaults after 5min
CLARIFY_REMEMBER_PREFERENCES=true       # Learn from past responses
```

### Preference Learning (Optional Enhancement)

Store user responses to build preference profile:

```json
{
  "user_preferences": {
    "tech_stack": {
      "backend": "nextjs",
      "confidence": 0.9,
      "last_used": "2024-01-15"
    },
    "auth_method": {
      "preferred": ["email_password", "oauth_google"],
      "confidence": 0.8
    },
    "coding_style": {
      "typescript": true,
      "testing": "jest",
      "formatting": "prettier"
    }
  }
}
```

Future clarifications can use these as smarter defaults or skip questions entirely.

---
