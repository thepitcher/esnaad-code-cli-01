# Esnaad Code - Tool Display Format

## User-Friendly Display (Default)

When you run `esnaad chat`, tool executions now show like this:

### Example 1: Writing a File (Success)
```
* Write(test001.txt)
  L Created 11 bytes to test001.txt
```

### Example 2: Reading a File (Success)
```
* Read(config.py)
  L Read 6 lines from config.py
     import os
     import sys
     from pathlib import Path
     ...
```

### Example 3: Running a Command (Success)
```
* Bash(dir /b)
  L Ran: dir /b
     test001.txt
     config.py
     README.md
     src
```

### Example 4: Listing a Directory (Success)
```
* List(src/esnaad)
  L Found 2 file(s), 3 dir(s) in esnaad
     [D] core
     [D] tools
     [D] cli
     [F] __init__.py
     [F] config.py
```

### Example 5: Error Case
```
X Write(/readonly/file.txt)
  L Error: Permission denied: /readonly/file.txt
```

## Visual Indicators

- **Green `*`** = Tool executed successfully
- **Red `X`** = Tool failed with error
- **`L`** = Summary line showing what the tool did
- **Indented lines** = Content preview (when applicable)

## Debug Mode

Set `ESNAAD_DEBUG=true` to see technical details:

```
* Write(test001.txt)
  L Created 11 bytes to test001.txt
     Debug: write_file -> {"success": true, "file_path": "c:/workspace/test001.txt", "bytes_written": 11, "created": true}
```

## Tool Name Mappings

| Technical Name | Friendly Display |
|----------------|------------------|
| `write_file` | `Write(filename)` |
| `read_file` | `Read(filename)` |
| `edit_file` | `Edit(filename)` |
| `create_directory` | `CreateDirectory(path)` |
| `list_directory` | `List(path)` |
| `search_files` | `SearchFiles(pattern)` |
| `search_content` | `SearchContent(pattern)` |
| `run_command` | `Bash(command)` |
| `spawn_subtasks` | `Task(spawn N subtasks)` |
| `request_clarifications` | `AskUserQuestion(N questions)` |
| `write_todo` | `TodoWrite(N tasks)` |
| `web_search` | `WebSearch(query)` |
| `web_fetch` | `WebFetch(url)` |
