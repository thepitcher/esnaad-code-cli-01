# Esnaad Core Backend - Coding Agent Rules

## Executive Summary
Esnaad is a **legacy .NET Framework 4.0.1 enterprise application** for military systems consist of Logistics, Maintenance, Operations, and many more modules. It uses a modular monolith architecture with Domain-Driven Design elements, CQRS pattern, and Spring.NET for dependency injection.

---
## Code Formatting Rules

**CRITICAL:** When generating C# code files:
- **DO NOT add extra blank lines between code lines**
- Use standard C# formatting with proper spacing
- Only ONE blank line between:
  - Groups of using statements and namespace declaration
  - Class members (properties, methods, constructors)
- **Bad:** `using System;\n\nusing NextGen...` (double newline = extra blank line)
- **Good:** `using System;\nusing NextGen...` (single newline = no extra blank line)

---

## Terminology
- **Domain**: The top-level project under src/modules (Admin, Logistic, Ammo, Maintenance, Operation, Pmco, Budget, Vehicle, etc)
- **Modules**: Business feature/package name under specific domain.
               Example:
               - StockManagement is Stock Management module under Logistic domain
               - MissionManagement is Mission Management module under Operation domain
               - ScheduledInspection is Schedule Inspection module under Maintenance domain
               - AmmunitionExercise is Module Ammunition Exercise under Ammo domain
               - AssetManagement is Asset Management module under Logistic domain
---
## List Domain
| Domain Code | Domain Names | Path |
|-------------|--------------|------|
| ADM | Admin | src/modules/NextGen.Admin
| AMM | Weapon and Ammo | src/modules/NextGen.Ammo
| BGT | Budget | src/modules/NextGen.Budget
| COE | CD | src/modules\NextGen.Pmco
| DAS | Dashboards | src/modules/NextGen.Dashboard
| EIS | Executive Information System | src\modules\NextGen.Eis
| LOG | Logistics | src/modules/NextGen.Logistic
| MNT | Maintenance | src/modules/NextGen.Maintenance
| OPS | Operation | src/modules/NextGen.Operation
| VEH | Vehicle | src/modules/NextGen.Vehicle.App or src/modules/NextGen.Vehicle.Core


<!-- #include architecture.md -->

<!-- #include entity-creation.md -->

<!-- #include entity-map-creation.md -->

<!-- #include migration-script-creation.md -->

<!-- #-include code-style.md -->

<!-- #-include workflow.md -->