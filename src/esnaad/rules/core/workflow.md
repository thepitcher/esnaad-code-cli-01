# Development Workflow

## Entity Creation Guide

### CRITICAL: When creating a new Entity, you MUST create these files together:

```
1. MAIN ENTITY FILE:                    src/modules/NextGen.[Domain]/NextGen.[Domain].Core/[Module]/Entity/[EntityName].cs
2. ID CLASS FILE:                       src/modules/NextGen.Admin/NextGen.Admin.Core/Shared/[Domain]/[Module]/[EntityName]Id.cs

```

## Build Verification

After ANY file modification (create, update, or delete), you MUST:

1. Run the build command to verify compilation succeeds
2. If the build fails, fix the errors before proceeding
3. Do not consider a task complete until the build passes

### Build Command

Run from the working directory root:

```bash
.\tools\nant\NAnt.exe build
```

If the build fails, analyze the error output and fix the issues before proceeding.

### When to Skip Build

You may skip build verification only when:
- Modifying documentation files (.md, .txt, .rst)
- Modifying configuration files (.env, .gitignore)
- The user explicitly says to skip verification