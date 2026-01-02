# Esnaad Core Backend - Coding Agent Rules

## Executive Summary
Esnaad is a **legacy .NET Framework 4.0.1 enterprise application** for military systems consist of Logistics, Maintenance, Operations, and many more modules. It uses a modular monolith architecture with Domain-Driven Design elements, CQRS pattern, and Spring.NET for dependency injection.

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

<!-- #include examples-entity.md -->


<!-- #include code-style.md -->

<!-- #include workflow.md -->