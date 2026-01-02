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

1. ☐ Determined correct Domain and Module
2. ☐ Created ID class in `Shared/[Domain]/[Module]/` directory
3. ☐ ID class inherits from `EntityId` with private constructor
4. ☐ ID class has static `Of(Guid)` factory method
5. ☐ Created Entity class in `[Module]/Entity/` directory
6. ☐ Entity inherits from `EntityBase<[EntityName]Id>`
7. ☐ Entity implements `INgAuditable`
8. ☐ All properties are `virtual` with `protected set`
9. ☐ Protected parameterless constructor exists
10. ☐ Public constructor with parameters exists
11. ☐ ID initialized in protected constructor
12. ☐ ReSharper comments added
13. ☐ Correct namespaces used
14. ☐ Used `write_file` tool to create both files

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
