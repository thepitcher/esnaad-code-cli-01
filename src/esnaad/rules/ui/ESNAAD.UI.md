# Esnaad Code - UI Preset Rules

## Overview

These rules are for frontend/UI development tasks.

## Build Verification

After ANY file modification (create, update, or delete), you MUST:

1. Run the build command to verify compilation succeeds
2. If the build fails, fix the errors before proceeding
3. Do not consider a task complete until the build passes

### Build Command

Run from the working directory root:



If the build fails, analyze the error output and fix the issues before proceeding.

### When to Skip Build

You may skip build verification only when:
- Modifying documentation files (.md, .txt, .rst)
- Modifying configuration files (.env, .gitignore)
- The user explicitly says to skip verification

## Code Quality

- All code files must have valid syntax
- Follow existing code patterns and conventions
- Ensure consistent styling and formatting

## UI Development Guidelines

- Focus on user interface components and styling
- Ensure responsive design principles
- Consider accessibility (a11y) requirements
- Test UI changes across different screen sizes
- Follow the existing design system and patterns
