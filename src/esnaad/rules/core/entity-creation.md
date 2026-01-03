# Entity Creation Rules

## When to Create an Entity

**Trigger:** When user requests to create a new entity with patterns like:
- "Create a new Entity for [ModuleName]"
- "Add [EntityName] entity to [Domain]"
- "Create entity for [Feature] in [Domain] domain"

**You MUST follow the complete workflow below.**

---

## Step-by-Step Workflow

### Step 1: Identify Location

Determine the correct paths based on:
- **Domain**: Which domain? (Admin, Logistic, Ammo, Maintenance, Operation, etc.)
- **Module**: What is the module/feature name?
- **Entity Name**: What is the entity class name?

**File Locations:**
```
ID Class:     src/modules/NextGen.[Domain]/NextGen.[Domain].Core/Shared/[Domain]/[Module]/[EntityName]Id.cs
Entity Class: src/modules/NextGen.[Domain]/NextGen.[Domain].Core/[Module]/Entity/[EntityName].cs
```

### Step 2: Create ID Class FIRST

**ALWAYS create the ID class before the entity class.**

**Template:**
```csharp
// Location: NextGen.[Domain].Core/Shared/[Domain]/[Module]/[EntityName]Id.cs
using System;
using NextGen.Support.Base.Entity;

namespace NextGen.[Domain].Core.Shared.[Domain].[Module]
{
    public class [EntityName]Id : EntityId
    {
        private [EntityName]Id(Guid value) : base(value) { }

        public static [EntityName]Id Of(Guid value)
        {
            return new [EntityName]Id(value);
        }
    }
}
```

### Step 3: Create Entity Class

**Template:**
```csharp
// Location: NextGen.[Domain].Core/[Module]/Entity/[EntityName].cs
using System;
using NextGen.Admin.Core.Entity;
using NextGen.Support.Base.Entity;
using NextGen.[Domain].Core.Shared.[Domain].[Module];

namespace NextGen.[Domain].Core.[Module].Entity
{
    public class [EntityName] : EntityBase<[EntityName]Id>, INgAuditable
    {
        public virtual NgAuditEntry AuditEntry { get; protected set; }
        public virtual string Code { get; protected set; }
        public virtual string Name { get; protected set; }
        // Add other domain-specific properties here

        protected [EntityName]()
        {
            // ReSharper disable DoNotCallOverridableMethodsInConstructor
            Id = [EntityName]Id.Of(Guid.NewGuid());
            // ReSharper restore DoNotCallOverridableMethodsInConstructor
        }

        public [EntityName](string code, string name)
            : this()
        {
            // ReSharper disable DoNotCallOverridableMethodsInConstructor
            Code = code;
            Name = name;
            // Initialize other properties
            // ReSharper restore DoNotCallOverridableMethodsInConstructor
        }
    }
}
```

---

## Pattern Requirements (MANDATORY)

**Every entity MUST follow these rules:**

- ✅ Inherit from `EntityBase<[EntityName]Id>` with strongly-typed ID
- ✅ Implement `INgAuditable` interface
- ✅ All properties declared as `virtual` with `protected set` (for NHibernate)
- ✅ Protected parameterless constructor for NHibernate proxy creation
- ✅ Public constructor with required parameters
- ✅ ID initialization: `Id = [EntityName]Id.Of(Guid.NewGuid())` in protected constructor
- ✅ ReSharper comments: `// ReSharper disable/restore DoNotCallOverridableMethodsInConstructor`
- ✅ Create companion ID class in `Shared/[Domain]/[Module]/` directory
- ✅ ID class inherits from `EntityId` with private constructor and static `Of()` factory method

**Common Properties:**
- `NgAuditEntry AuditEntry` - Required for all auditable entities
- `string Code` - Usually required for master data entities
- `string Name` - Usually required for master data entities

---

## Property Types and Import Resolution

### Property Type Classification

Entity properties can be one of three types:

1. **Primitive Types** - No imports needed
   - `string`, `int`, `int?`, `bool`, `bool?`, `decimal`, `decimal?`, `DateTime`, `DateTime?`
   - Example: `public virtual string Name { get; protected set; }`

2. **ObjectId of Primitive Type** - Import from Admin domain Shared
   - Used for dropdown/lookup values (categories, codes, types, etc.)
   - **ALWAYS** in: `NextGen.Admin.Core.Shared.[Domain].[Module]`
   - Example: `IntervalCategory`, `WorkUnitCode`, `VehicleType`
   - Example property: `public virtual IntervalCategory IntervalCategory { get; set; }`

3. **Entity References** - Import from actual entity location
   - References to other domain entities
   - Can be from same domain or different domain
   - Search required to find import path
   - Example: `Platform`, `Item`, `DataRestriction`
   - Example property: `public virtual Platform Platform { get; protected set; }`

### Import Resolution Rules

**Rule 1: Primitive Types**
- No import needed
- Use directly in properties

**Rule 2: ObjectId of Primitive Type (Lookup Values)**
- **Always import from**: `NextGen.Admin.Core.Shared.[Domain].[Module]`
- Pattern: `using NextGen.Admin.Core.Shared.[Domain].[Module];`
- Examples:
  ```csharp
  using NextGen.Admin.Core.Shared.Maintenance._2408_16_1;  // IntervalCategory, WorkUnitCode
  using NextGen.Admin.Core.Shared.Logistic.Master;          // UnitOfMeasureCategory
  using NextGen.Admin.Core.Shared.Operation.Mission;        // MissionType, MissionStatus
  ```

**Rule 3: Entity References**

You MUST search for the entity to find its import path:

**Step 1: Search for the entity file**
```
Use search_files tool: search_files(pattern="Platform.cs", path="src/modules")
```

**Step 2: Determine import namespace from file path**
- If found in: `src/modules/NextGen.Admin/NextGen.Admin.Core/Shared/Logistic/ItemCatalogue/Entity/Platform.cs`
- Import namespace: `NextGen.Admin.Core.Shared.Logistic.ItemCatalogue.Entity`

**Step 3: Add using statement**
```csharp
using NextGen.Admin.Core.Shared.Logistic.ItemCatalogue.Entity;  // Platform
```

### Common Entity Reference Locations

| Entity | Typical Location | Import Namespace |
|--------|-----------------|------------------|
| `DataRestriction` (Command) | Admin/Security | `NextGen.Admin.Core.Security.Entity` |
| `Platform` | Admin/Logistic/ItemCatalogue | `NextGen.Admin.Core.Shared.Logistic.ItemCatalogue.Entity` |
| `Item` | Admin/Logistic/ItemCatalogue | `NextGen.Admin.Core.Shared.Logistic.ItemCatalogue.Entity` |
| `Unit` | Admin/Organization | `NextGen.Admin.Core.Organization.Entity` |
| `User` | Admin/Security | `NextGen.Admin.Core.Security.Entity` |

### Import Resolution Workflow

When you encounter a non-primitive property type:

1. **Check if it's a primitive ObjectId (lookup value)**:
   - Ends with common patterns: `Category`, `Type`, `Status`, `Code`
   - Import from: `NextGen.Admin.Core.Shared.[Domain].[Module]`

2. **Otherwise, it's an entity reference**:
   - Use `search_files` to find `[EntityName].cs`
   - Extract namespace from file path
   - Add appropriate using statement

3. **Self-reference (same entity)**:
   - No import needed
   - Example: `public virtual D161Master ParentMaster { get; protected set; }`

### Example: Complex Entity with Mixed Property Types

```csharp
using System;
using NextGen.Admin.Core.Entity;                                      // NgAuditEntry
using NextGen.Admin.Core.Security.Entity;                             // DataRestriction (entity)
using NextGen.Admin.Core.Shared.Logistic.ItemCatalogue.Entity;       // Platform, Item (entities)
using NextGen.Admin.Core.Shared.Maintenance._2408_16_1;              // IntervalCategory, WorkUnitCode (ObjectIds)
using NextGen.Maintenance.Core._2408_16.Entity;                      // D161Fault (entity, same domain)
using NextGen.Support.Base.Entity;                                    // EntityBase

namespace NextGen.Maintenance.Core._2408_16_1.Entity
{
    public class D161Master : EntityBase<D161MasterId>, INgAuditable
    {
        // Standard auditable property
        public virtual NgAuditEntry AuditEntry { get; protected set; }

        // Entity references (from other domains)
        public virtual DataRestriction Command { get; protected set; }      // Admin.Security
        public virtual Platform Platform { get; protected set; }            // Admin.Logistic
        public virtual Item EndItem { get; protected set; }                 // Admin.Logistic
        public virtual Item Component { get; protected set; }               // Admin.Logistic

        // Primitive types
        public virtual int? Level { get; protected set; }
        public virtual int? Overhaul { get; set; }
        public virtual int? Replace { get; set; }
        public virtual bool IsReplaceNha { get; set; }
        public virtual string HierarchyCode { get; set; }

        // ObjectId of primitive type (lookup values)
        public virtual IntervalCategory IntervalCategory { get; set; }     // Admin.Shared
        public virtual WorkUnitCode WorkUnitCode { get; set; }             // Admin.Shared

        // Entity reference (same domain)
        public virtual D161Fault FaultInfo { get; set; }                   // Maintenance._2408_16

        // Self-reference
        public virtual D161Master ParentMaster { get; protected set; }

        protected D161Master()
        {
            Id = D161MasterId.Of(Guid.NewGuid());
        }

        public D161Master(
            DataRestriction command,
            Platform platform,
            Item endItem,
            Item component,
            int? level,
            D161Master parentMaster = null)
        {
            Command = command;
            Platform = platform;
            EndItem = endItem;
            Component = component;
            Level = level;
            ParentMaster = parentMaster;
        }
    }
}
```

### Quick Decision Tree

When adding a property to an entity:

```
Is the type a C# primitive (string, int, bool, DateTime)?
├─ YES → No import needed
└─ NO → Continue...

Does it end with Category/Type/Status/Code and is a lookup value?
├─ YES → Import from: NextGen.Admin.Core.Shared.[Domain].[Module]
└─ NO → Continue...

Is it the same entity (self-reference)?
├─ YES → No import needed
└─ NO → Continue...

It's an entity reference:
└─ Use search_files to find [EntityName].cs
   └─ Extract namespace from file path
      └─ Add using statement
```

---

## File Naming Conventions

| Component | Pattern | Example (WeightBalance in Maintenance) |
|-----------|---------|----------------------------------------|
| Entity File | `[EntityName].cs` | `WeightBalance.cs` |
| ID File | `[EntityName]Id.cs` | `WeightBalanceId.cs` |
| Entity Path | `NextGen.[Domain].Core/[Module]/Entity/` | `NextGen.Maintenance.Core/WeightBalance/Entity/` |
| ID Path | `NextGen.[Domain].Core/Shared/[Domain]/[Module]/` | `NextGen.Maintenance.Core/Shared/Maintenance/WeightBalance/` |
| Entity Namespace | `NextGen.[Domain].Core.[Module].Entity` | `NextGen.Maintenance.Core.WeightBalance.Entity` |
| ID Namespace | `NextGen.[Domain].Core.Shared.[Domain].[Module]` | `NextGen.Maintenance.Core.Shared.Maintenance.WeightBalance` |

---

## Complete Examples

### Example 1: UnitOfMeasure (Logistic Domain, Master Module)

**ID Class:**
```csharp
// Location: NextGen.Logistic.Core/Shared/Logistic/Master/UnitOfMeasureId.cs
using System;
using NextGen.Support.Base.Entity;

namespace NextGen.Logistic.Core.Shared.Logistic.Master
{
    public class UnitOfMeasureId : EntityId
    {
        private UnitOfMeasureId(Guid value) : base(value) { }

        public static UnitOfMeasureId Of(Guid value)
        {
            return new UnitOfMeasureId(value);
        }
    }
}
```

**Entity Class:**
```csharp
// Location: NextGen.Logistic.Core/Master/Entity/UnitOfMeasure.cs
using System;
using NextGen.Admin.Core.Entity;
using NextGen.Admin.Core.Master.Entity;
using NextGen.Logistic.Core.Shared.Logistic.Master;
using NextGen.Support.Base.Entity;

namespace NextGen.Logistic.Core.Master.Entity
{
    public class UnitOfMeasure : EntityBase<UnitOfMeasureId>, INgAuditable
    {
        public virtual NgAuditEntry AuditEntry { get; protected set; }
        public virtual string Code { get; protected set; }
        public virtual string Name { get; protected set; }
        public virtual UnitOfMeasureCategory Category { get; protected set; }
        public virtual bool IsBase { get; protected set; }

        protected UnitOfMeasure()
        {
            // ReSharper disable DoNotCallOverridableMethodsInConstructor
            Id = UnitOfMeasureId.Of(Guid.NewGuid());
            // ReSharper restore DoNotCallOverridableMethodsInConstructor
        }

        public UnitOfMeasure(string code, string name, UnitOfMeasureCategory category)
            : this()
        {
            // ReSharper disable DoNotCallOverridableMethodsInConstructor
            Code = code;
            Name = name;
            Category = category;
            // ReSharper restore DoNotCallOverridableMethodsInConstructor
        }
    }
}
```

### Example 2: WeightBalance (Maintenance Domain, WeightBalance Module)

**User Request:** "Create a new Entity for Weight & Balance module under Maintenance domain."

**ID Class:**
```csharp
// Location: NextGen.Maintenance.Core/Shared/Maintenance/WeightBalance/WeightBalanceId.cs
using System;
using NextGen.Support.Base.Entity;

namespace NextGen.Maintenance.Core.Shared.Maintenance.WeightBalance
{
    public class WeightBalanceId : EntityId
    {
        private WeightBalanceId(Guid value) : base(value) { }

        public static WeightBalanceId Of(Guid value)
        {
            return new WeightBalanceId(value);
        }
    }
}
```

**Entity Class:**
```csharp
// Location: NextGen.Maintenance.Core/WeightBalance/Entity/WeightBalance.cs
using System;
using NextGen.Admin.Core.Entity;
using NextGen.Support.Base.Entity;
using NextGen.Maintenance.Core.Shared.Maintenance.WeightBalance;

namespace NextGen.Maintenance.Core.WeightBalance.Entity
{
    public class WeightBalance : EntityBase<WeightBalanceId>, INgAuditable
    {
        public virtual NgAuditEntry AuditEntry { get; protected set; }
        public virtual string Code { get; protected set; }
        public virtual string Name { get; protected set; }
        public virtual string Description { get; protected set; }

        protected WeightBalance()
        {
            // ReSharper disable DoNotCallOverridableMethodsInConstructor
            Id = WeightBalanceId.Of(Guid.NewGuid());
            // ReSharper restore DoNotCallOverridableMethodsInConstructor
        }

        public WeightBalance(string code, string name, string description = null)
            : this()
        {
            // ReSharper disable DoNotCallOverridableMethodsInConstructor
            Code = code;
            Name = name;
            Description = description;
            // ReSharper restore DoNotCallOverridableMethodsInConstructor
        }
    }
}
```

---

## Quick Reference: Creation Checklist

When creating an entity, verify:

### Structure
1. ☐ Determined correct Domain and Module
2. ☐ Created ID class in `Shared/[Domain]/[Module]/` directory
3. ☐ ID class inherits from `EntityId` with private constructor
4. ☐ ID class has static `Of(Guid)` factory method
5. ☐ Created Entity class in `[Module]/Entity/` directory
6. ☐ Entity inherits from `EntityBase<[EntityName]Id>`
7. ☐ Entity implements `INgAuditable`

### Properties
8. ☐ All properties are `virtual` with `protected set`
9. ☐ Identified primitive types (no import needed)
10. ☐ Identified ObjectId properties (import from Admin.Core.Shared)
11. ☐ Identified entity references (searched for import paths)
12. ☐ Added all necessary using statements at the top

### Constructors
13. ☐ Protected parameterless constructor exists
14. ☐ Public constructor with parameters exists
15. ☐ ID initialized in protected constructor
16. ☐ ReSharper comments added

### Final Checks
17. ☐ Correct namespaces used
18. ☐ All imports resolved correctly
19. ☐ Used `write_file` tool to create both files

---

## Notes

- **Code Formatting**:
  - **CRITICAL:** Do NOT add extra blank lines between code lines
  - Code should be compact and follow standard C# formatting
  - Only one blank line between using statements and namespace
  - Only one blank line between class members (properties, methods, constructors)
  - Bad example: `using System;\n\nusing NextGen...` (extra blank line)
  - Good example: `using System;\nusing NextGen...` (single newline)

- **Directory Creation**: Use Windows commands to create directories if needed:
  ```cmd
  mkdir src\modules\NextGen.Maintenance\NextGen.Maintenance.Core\WeightBalance\Entity
  mkdir src\modules\NextGen.Maintenance\NextGen.Maintenance.Core\Shared\Maintenance\WeightBalance
  ```

- **Namespace Conventions**: Namespace must match the physical directory structure

- **Always Create Both Files**: An entity is incomplete without its ID class
