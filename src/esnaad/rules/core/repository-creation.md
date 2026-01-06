# Repository Creation Rules (NHibernate)

## When to Create a Repository

**Trigger:** When user requests to create a repository for an entity with patterns like:
- "Create repository for [EntityName]"
- "Create [EntityName] repository"
- "Implement repository for [EntityName] entity"
- "Create data access layer for [EntityName]"

**You MUST follow the complete workflow below.**

---

## Step-by-Step Workflow

### Step 1: Locate and Read the Entity File

Before creating a repository, you MUST read the entity file to analyze its structure.

**Action:**
1. Use `search_files` to find the entity file: `search_files(pattern="[EntityName].cs", path="src/modules")`
2. Use `read_file` to read the entity file and analyze:
   - Namespace (to determine domain/module)
   - Properties (especially `Code` and `Name` for common repository methods)
   - ID type (e.g., `UnitOfMeasureId`)
   - Base class (should be `EntityBase<[EntityName]Id>`)

**Example:**
```
search_files(pattern="UnitOfMeasure.cs", path="src/modules")
→ Found: src/modules/NextGen.Logistic/NextGen.Logistic.Core/Master/Entity/UnitOfMeasure.cs

read_file(file_path="src/modules/NextGen.Logistic/NextGen.Logistic.Core/Master/Entity/UnitOfMeasure.cs")
```

### Step 2: Determine Domain and Module

Extract from entity file path and namespace:

**Pattern:**
```
Entity path:     src/modules/NextGen.[Domain]/NextGen.[Domain].Core/[Module]/Entity/[EntityName].cs
Entity namespace: NextGen.[Domain].Core.[Module].Entity

Interface path:     src/modules/NextGen.[Domain]/NextGen.[Domain].Core/[Module]/Repository/I[EntityName]Repository.cs
Interface namespace: NextGen.[Domain].Core.[Module].Repository

Implementation path:     src/modules/NextGen.[Domain]/NextGen.[Domain].Core/[Module]/Repository/NHibernate/Nh[EntityName]Repository.cs
Implementation namespace: NextGen.[Domain].Core.[Module].Repository.NHibernate
```

**Example (UnitOfMeasure):**
```
Entity: NextGen.Logistic.Core/Master/Entity/UnitOfMeasure.cs
Domain: Logistic
Module: Master

Interface:     NextGen.Logistic.Core/Master/Repository/IUnitOfMeasureRepository.cs
Implementation: NextGen.Logistic.Core/Master/Repository/NHibernate/NhUnitOfMeasureRepository.cs
```

### Step 3: Identify Common Properties

Analyze entity properties to determine which standard repository methods to include:

**Key Properties to Check:**
- `Code` property → Add `IsCodeExists()`, `Get(string code)`, `Find(string[] codes)` methods
- `Name` property → Add `IsNameExists()` method
- Other unique/searchable properties → Add custom query methods as needed

### Step 4: Create Interface File

Create `I[EntityName]Repository.cs` with standard methods.

### Step 5: Create Implementation File

Create `Nh[EntityName]Repository.cs` with NHibernate implementation.

---

## Repository Interface Structure

### Base Interface

**All repository interfaces inherit from:**
```csharp
ISpecificRepository<TEntity, TEntityId>
```

**Pattern:**
```csharp
public interface I[EntityName]Repository : ISpecificRepository<[EntityName], [EntityName]Id>
{
    // Custom methods here
}
```

### Standard Methods

#### 1. IsCodeExists (if entity has Code property)

**Signature:**
```csharp
bool IsCodeExists(string code);
```

**Purpose:** Check if a code already exists in the database (for validation)

#### 2. IsNameExists (if entity has Name property)

**Signature:**
```csharp
bool IsNameExists(string name);
```

**Purpose:** Check if a name already exists in the database (for validation)

#### 3. Get by Guid

**Signature:**
```csharp
[EntityName] Get(Guid guid);
```

**Purpose:** Retrieve entity by raw GUID (converts to EntityId internally)

#### 4. Get by Code (if entity has Code property)

**Signature:**
```csharp
[EntityName] Get(string code);
```

**Purpose:** Retrieve entity by its unique code

#### 5. Find by IDs

**Signature:**
```csharp
IEnumerable<[EntityName]> Find([EntityName]Id[] [entityName]Ids);
```

**Purpose:** Retrieve multiple entities by their IDs

**Naming Convention:** Parameter name is camelCase plural of entity name + "Ids"
- `UnitOfMeasure` → `unitOfMeasureIds`
- `Platform` → `platformIds`
- `DataRestriction` → `dataRestrictionIds`

#### 6. Find by Codes (if entity has Code property)

**Signature:**
```csharp
IEnumerable<[EntityName]> Find(string[] codes);
```

**Purpose:** Retrieve multiple entities by their codes

---

## Repository Implementation Structure

### Base Class

**All repository implementations inherit from:**
```csharp
AbstractNhSpecificRepository<TEntity, TEntityId>
```

**Pattern:**
```csharp
public class Nh[EntityName]Repository : AbstractNhSpecificRepository<[EntityName], [EntityName]Id>, I[EntityName]Repository
```

### Constructor

**Required constructor pattern:**
```csharp
/// <summary>
///
/// </summary>
/// <param name="sessionFactory"></param>
public Nh[EntityName]Repository(ISessionFactory sessionFactory)
    : base(sessionFactory)
{
}
```

**Rules:**
- Takes `ISessionFactory sessionFactory` as parameter
- Calls `base(sessionFactory)`
- XML summary comment for constructor
- Parameter documentation for `sessionFactory`

### Method Implementations

#### 1. Get by Guid Implementation

**Pattern:**
```csharp
public [EntityName] Get(Guid guid)
{
    return Get([EntityName]Id.Of(guid));
}
```

**Explanation:**
- Converts `Guid` to `[EntityName]Id` using static `Of()` method
- Calls inherited `Get([EntityName]Id)` method from base class

#### 2. Get by Code Implementation

**Pattern:**
```csharp
public [EntityName] Get(string code)
{
    return CurrentSession.QueryOver<[EntityName]>().Where(x => x.Code == code).SingleOrDefault<[EntityName]>();
}
```

**NHibernate Components:**
- `CurrentSession` - inherited property providing current NHibernate session
- `QueryOver<T>()` - NHibernate's type-safe query API
- `.Where(x => x.Property == value)` - lambda-based filtering
- `.SingleOrDefault<T>()` - returns single result or null

#### 3. Find by IDs Implementation

**Pattern:**
```csharp
public IEnumerable<[EntityName]> Find([EntityName]Id[] [entityName]Ids)
{
    return
        CurrentSession.QueryOver<[EntityName]>()
                      .WhereRestrictionOn(x => x.Id)
        // ReSharper disable CoVariantArrayConversion
                      .IsIn([entityName]Ids)
        // ReSharper restore CoVariantArrayConversion
                      .Future();
}
```

**NHibernate Components:**
- `.WhereRestrictionOn(x => x.Property)` - specify property for restriction
- `.IsIn(array)` - SQL IN clause
- `.Future()` - deferred execution (returns `IEnumerable<T>`)
- ReSharper comments suppress covariant array conversion warnings

**Formatting:**
- Multi-line formatting with indentation
- ReSharper comments on separate lines

#### 4. Find by Codes Implementation

**Pattern:**
```csharp
public IEnumerable<[EntityName]> Find(string[] codes)
{
    // ReSharper disable CoVariantArrayConversion
    return CurrentSession.QueryOver<[EntityName]>().WhereRestrictionOn(x => x.Code).IsIn(codes).Future();
    // ReSharper restore CoVariantArrayConversion
}
```

**Alternative compact format:**
- Single-line return statement
- ReSharper comments wrap the return statement

#### 5. IsCodeExists Implementation

**Pattern:**
```csharp
public bool IsCodeExists(string code)
{
    return CurrentSession.QueryOver<[EntityName]>().Where(x => x.Code == code).Future().Any();
}
```

**NHibernate Components:**
- `.Future()` - deferred execution
- `.Any()` - LINQ method to check if any results exist
- Returns `bool`

#### 6. IsNameExists Implementation

**Pattern:**
```csharp
public bool IsNameExists(string name)
{
    return CurrentSession.QueryOver<[EntityName]>().Where(x => x.Name == name).Future().Any();
}
```

---

## Required Imports

### Interface File Imports

**Standard imports:**
```csharp
using System;
using System.Collections.Generic;
using NextGen.[Domain].Core.Shared.[Domain].[Module];  // For [EntityName]Id
using NextGen.[Domain].Core.[Module].Entity;           // For [EntityName]
using NextGen.Support.Base.Repository;                 // For ISpecificRepository
```

**Example (UnitOfMeasure):**
```csharp
using System;
using System.Collections.Generic;
using NextGen.Admin.Core.Shared.Logistic.Master;  // UnitOfMeasureId
using NextGen.Logistic.Core.Master.Entity;        // UnitOfMeasure
using NextGen.Support.Base.Repository;            // ISpecificRepository
```

### Implementation File Imports

**Standard imports:**
```csharp
using System;
using System.Linq;
using System.Collections.Generic;
using NHibernate;                                      // For ISessionFactory
using NextGen.[Domain].Core.Shared.[Domain].[Module]; // For [EntityName]Id
using NextGen.[Domain].Core.[Module].Entity;          // For [EntityName]
using NextGen.Support.Data.NHibernate;                // For AbstractNhSpecificRepository
```

**Example (UnitOfMeasure):**
```csharp
using System;
using System.Linq;
using System.Collections.Generic;
using NHibernate;                                  // ISessionFactory
using NextGen.Admin.Core.Shared.Logistic.Master;  // UnitOfMeasureId
using NextGen.Logistic.Core.Master.Entity;        // UnitOfMeasure
using NextGen.Support.Data.NHibernate;            // AbstractNhSpecificRepository
```

---

## Complete Interface Template

```csharp
using System;
using System.Collections.Generic;
using NextGen.[Domain].Core.Shared.[Domain].[Module];
using NextGen.[Domain].Core.[Module].Entity;
using NextGen.Support.Base.Repository;

namespace NextGen.[Domain].Core.[Module].Repository
{
    /// <summary>
    ///
    /// </summary>
    /// <author>[username]</author>
    public interface I[EntityName]Repository : ISpecificRepository<[EntityName], [EntityName]Id>
    {
        bool IsCodeExists(string code);

        bool IsNameExists(string name);

        [EntityName] Get(Guid guid);

        [EntityName] Get(string code);

        IEnumerable<[EntityName]> Find([EntityName]Id[] [entityName]Ids);

        IEnumerable<[EntityName]> Find(string[] codes);
    }
}
```

---

## Complete Implementation Template

```csharp
using System;
using System.Linq;
using System.Collections.Generic;
using NHibernate;
using NextGen.[Domain].Core.Shared.[Domain].[Module];
using NextGen.[Domain].Core.[Module].Entity;
using NextGen.Support.Data.NHibernate;

namespace NextGen.[Domain].Core.[Module].Repository.NHibernate
{
    /// <summary>
    ///
    /// </summary>
    /// <author>[username]</author>
    public class Nh[EntityName]Repository : AbstractNhSpecificRepository<[EntityName], [EntityName]Id>, I[EntityName]Repository
    {
        /// <summary>
        ///
        /// </summary>
        /// <param name="sessionFactory"></param>
        public Nh[EntityName]Repository(ISessionFactory sessionFactory)
            : base(sessionFactory)
        {
        }

        public [EntityName] Get(Guid guid)
        {
            return Get([EntityName]Id.Of(guid));
        }

        public [EntityName] Get(string code)
        {
            return CurrentSession.QueryOver<[EntityName]>().Where(x => x.Code == code).SingleOrDefault<[EntityName]>();
        }

        public IEnumerable<[EntityName]> Find([EntityName]Id[] [entityName]Ids)
        {
            return
                CurrentSession.QueryOver<[EntityName]>()
                              .WhereRestrictionOn(x => x.Id)
                // ReSharper disable CoVariantArrayConversion
                              .IsIn([entityName]Ids)
                // ReSharper restore CoVariantArrayConversion
                              .Future();
        }

        public IEnumerable<[EntityName]> Find(string[] codes)
        {
            // ReSharper disable CoVariantArrayConversion
            return CurrentSession.QueryOver<[EntityName]>().WhereRestrictionOn(x => x.Code).IsIn(codes).Future();
            // ReSharper restore CoVariantArrayConversion
        }

        public bool IsCodeExists(string code)
        {
            return CurrentSession.QueryOver<[EntityName]>().Where(x => x.Code == code).Future().Any();
        }

        public bool IsNameExists(string name)
        {
            return CurrentSession.QueryOver<[EntityName]>().Where(x => x.Name == name).Future().Any();
        }
    }
}
```

---

## Complete Example: UnitOfMeasure Repository

### Entity File (for reference)

```csharp
// NextGen.Logistic.Core/Master/Entity/UnitOfMeasure.cs
namespace NextGen.Logistic.Core.Master.Entity
{
    public class UnitOfMeasure : EntityBase<UnitOfMeasureId>, INgAuditable
    {
        public virtual NgAuditEntry AuditEntry { get; protected set; }
        public virtual string Code { get; protected set; }
        public virtual string Name { get; protected set; }
        public virtual UnitOfMeasureCategory Category { get; protected set; }
        public virtual bool IsBase { get; protected set; }
        // constructors...
    }
}
```

### Interface File

```csharp
// Location: NextGen.Logistic.Core/Master/Repository/IUnitOfMeasureRepository.cs
using System;
using System.Collections.Generic;
using NextGen.Admin.Core.Shared.Logistic.Master;
using NextGen.Logistic.Core.Master.Entity;
using NextGen.Support.Base.Repository;

namespace NextGen.Logistic.Core.Master.Repository
{
    /// <summary>
    ///
    /// </summary>
    /// <author>gal7634</author>
    public interface IUnitOfMeasureRepository : ISpecificRepository<UnitOfMeasure, UnitOfMeasureId>
    {
        bool IsCodeExists(string code);

        bool IsNameExists(string name);

        UnitOfMeasure Get(Guid guid);

        UnitOfMeasure Get(string code);

        IEnumerable<UnitOfMeasure> Find(UnitOfMeasureId[] unitOfMeasureIds);

        IEnumerable<UnitOfMeasure> Find(string[] codes);
    }
}
```

### Implementation File

```csharp
// Location: NextGen.Logistic.Core/Master/Repository/NHibernate/NhUnitOfMeasureRepository.cs
using System;
using System.Linq;
using System.Collections.Generic;
using NHibernate;
using NextGen.Admin.Core.Shared.Logistic.Master;
using NextGen.Logistic.Core.Master.Entity;
using NextGen.Support.Data.NHibernate;

namespace NextGen.Logistic.Core.Master.Repository.NHibernate
{
    /// <summary>
    ///
    /// </summary>
    /// <author>gal7634</author>
    public class NhUnitOfMeasureRepository : AbstractNhSpecificRepository<UnitOfMeasure, UnitOfMeasureId>, IUnitOfMeasureRepository
    {
        /// <summary>
        ///
        /// </summary>
        /// <param name="sessionFactory"></param>
        public NhUnitOfMeasureRepository(ISessionFactory sessionFactory)
            : base(sessionFactory)
        {
        }

        public UnitOfMeasure Get(Guid guid)
        {
            return Get(UnitOfMeasureId.Of(guid));
        }

        public UnitOfMeasure Get(string code)
        {
            return CurrentSession.QueryOver<UnitOfMeasure>().Where(x => x.Code == code).SingleOrDefault<UnitOfMeasure>();
        }

        public IEnumerable<UnitOfMeasure> Find(UnitOfMeasureId[] unitOfMeasureIds)
        {
            return
                CurrentSession.QueryOver<UnitOfMeasure>()
                              .WhereRestrictionOn(x => x.Id)
                // ReSharper disable CoVariantArrayConversion
                              .IsIn(unitOfMeasureIds)
                // ReSharper restore CoVariantArrayConversion
                              .Future();
        }

        public IEnumerable<UnitOfMeasure> Find(string[] codes)
        {
            // ReSharper disable CoVariantArrayConversion
            return CurrentSession.QueryOver<UnitOfMeasure>().WhereRestrictionOn(x => x.Code).IsIn(codes).Future();
            // ReSharper restore CoVariantArrayConversion
        }

        public bool IsCodeExists(string code)
        {
            return CurrentSession.QueryOver<UnitOfMeasure>().Where(x => x.Code == code).Future().Any();
        }

        public bool IsNameExists(string name)
        {
            return CurrentSession.QueryOver<UnitOfMeasure>().Where(x => x.Name == name).Future().Any();
        }
    }
}
```

---

## Example 2: Entity Without Code Property

**Entity:**
```csharp
namespace NextGen.Maintenance.Core.WeightBalance.Entity
{
    public class WeightBalance : EntityBase<WeightBalanceId>, INgAuditable
    {
        public virtual NgAuditEntry AuditEntry { get; protected set; }
        public virtual DataRestriction Command { get; protected set; }
        public virtual Platform Platform { get; protected set; }
        public virtual string Name { get; protected set; }
        public virtual decimal? MaxWeight { get; protected set; }
    }
}
```

**Interface (No Code-related methods):**
```csharp
using System;
using System.Collections.Generic;
using NextGen.Maintenance.Core.Shared.Maintenance.WeightBalance;
using NextGen.Maintenance.Core.WeightBalance.Entity;
using NextGen.Support.Base.Repository;

namespace NextGen.Maintenance.Core.WeightBalance.Repository
{
    /// <summary>
    ///
    /// </summary>
    /// <author>gal7634</author>
    public interface IWeightBalanceRepository : ISpecificRepository<WeightBalance, WeightBalanceId>
    {
        bool IsNameExists(string name);

        WeightBalance Get(Guid guid);

        IEnumerable<WeightBalance> Find(WeightBalanceId[] weightBalanceIds);
    }
}
```

**Implementation:**
```csharp
using System;
using System.Linq;
using System.Collections.Generic;
using NHibernate;
using NextGen.Maintenance.Core.Shared.Maintenance.WeightBalance;
using NextGen.Maintenance.Core.WeightBalance.Entity;
using NextGen.Support.Data.NHibernate;

namespace NextGen.Maintenance.Core.WeightBalance.Repository.NHibernate
{
    /// <summary>
    ///
    /// </summary>
    /// <author>gal7634</author>
    public class NhWeightBalanceRepository : AbstractNhSpecificRepository<WeightBalance, WeightBalanceId>, IWeightBalanceRepository
    {
        /// <summary>
        ///
        /// </summary>
        /// <param name="sessionFactory"></param>
        public NhWeightBalanceRepository(ISessionFactory sessionFactory)
            : base(sessionFactory)
        {
        }

        public WeightBalance Get(Guid guid)
        {
            return Get(WeightBalanceId.Of(guid));
        }

        public IEnumerable<WeightBalance> Find(WeightBalanceId[] weightBalanceIds)
        {
            return
                CurrentSession.QueryOver<WeightBalance>()
                              .WhereRestrictionOn(x => x.Id)
                // ReSharper disable CoVariantArrayConversion
                              .IsIn(weightBalanceIds)
                // ReSharper restore CoVariantArrayConversion
                              .Future();
        }

        public bool IsNameExists(string name)
        {
            return CurrentSession.QueryOver<WeightBalance>().Where(x => x.Name == name).Future().Any();
        }
    }
}
```

---

## Method Inclusion Decision Tree

```
What methods should be included in the repository?

ALWAYS include:
├─ Get(Guid guid) - Standard method for all repositories
└─ Find([EntityName]Id[] ids) - Standard method for all repositories

Does entity have Code property?
├─ YES → Include:
│   ├─ bool IsCodeExists(string code)
│   ├─ [EntityName] Get(string code)
│   └─ IEnumerable<[EntityName]> Find(string[] codes)
└─ NO → Skip Code-related methods

Does entity have Name property?
├─ YES → Include:
│   └─ bool IsNameExists(string name)
└─ NO → Skip Name-related methods

Does entity have other unique/searchable properties?
└─ YES → Consider adding custom query methods
    Examples:
    ├─ Get by Category: Get(CategoryType category)
    ├─ Find by Status: Find(StatusType status)
    ├─ Find by DateRange: Find(DateTime from, DateTime to)
    └─ Find by Parent: Find(ParentEntityId parentId)
```

---

## NHibernate Query Patterns

### Pattern 1: Single Result by Property

```csharp
// Get single entity by property value
public Entity Get(PropertyType propertyValue)
{
    return CurrentSession.QueryOver<Entity>()
        .Where(x => x.Property == propertyValue)
        .SingleOrDefault<Entity>();
}
```

### Pattern 2: Check Existence

```csharp
// Check if entity exists with property value
public bool IsPropertyExists(PropertyType propertyValue)
{
    return CurrentSession.QueryOver<Entity>()
        .Where(x => x.Property == propertyValue)
        .Future()
        .Any();
}
```

### Pattern 3: Find by Array (IN clause)

```csharp
// Find multiple entities by array of values
public IEnumerable<Entity> Find(PropertyType[] propertyValues)
{
    // ReSharper disable CoVariantArrayConversion
    return CurrentSession.QueryOver<Entity>()
        .WhereRestrictionOn(x => x.Property)
        .IsIn(propertyValues)
        .Future();
    // ReSharper restore CoVariantArrayConversion
}
```

### Pattern 4: Find with Multiple Criteria

```csharp
// Find entities matching multiple conditions
public IEnumerable<Entity> Find(PropertyType prop1, PropertyType prop2)
{
    return CurrentSession.QueryOver<Entity>()
        .Where(x => x.Property1 == prop1 && x.Property2 == prop2)
        .Future();
}
```

### Pattern 5: Find with Ordering

```csharp
// Find entities with ordering
public IEnumerable<Entity> FindOrdered()
{
    return CurrentSession.QueryOver<Entity>()
        .OrderBy(x => x.Code).Asc
        .Future();
}
```

---

## File Location Patterns

| Component | Pattern | Example (UnitOfMeasure) |
|-----------|---------|-------------------------|
| Entity | `NextGen.[Domain].Core/[Module]/Entity/[EntityName].cs` | `NextGen.Logistic.Core/Master/Entity/UnitOfMeasure.cs` |
| Repository Interface | `NextGen.[Domain].Core/[Module]/Repository/I[EntityName]Repository.cs` | `NextGen.Logistic.Core/Master/Repository/IUnitOfMeasureRepository.cs` |
| Repository Implementation | `NextGen.[Domain].Core/[Module]/Repository/NHibernate/Nh[EntityName]Repository.cs` | `NextGen.Logistic.Core/Master/Repository/NHibernate/NhUnitOfMeasureRepository.cs` |

| Component | Namespace Pattern | Example (UnitOfMeasure) |
|-----------|------------------|-------------------------|
| Entity | `NextGen.[Domain].Core.[Module].Entity` | `NextGen.Logistic.Core.Master.Entity` |
| Repository Interface | `NextGen.[Domain].Core.[Module].Repository` | `NextGen.Logistic.Core.Master.Repository` |
| Repository Implementation | `NextGen.[Domain].Core.[Module].Repository.NHibernate` | `NextGen.Logistic.Core.Master.Repository.NHibernate` |

---

## Quick Reference: Creation Checklist

When creating a repository, verify:

### Preparation
1. ☐ Read entity file to analyze structure
2. ☐ Identified domain and module from entity namespace
3. ☐ Identified entity ID type (e.g., `UnitOfMeasureId`)
4. ☐ Checked if entity has `Code` property
5. ☐ Checked if entity has `Name` property
6. ☐ Identified other searchable properties for custom methods

### Interface File
7. ☐ Created interface in correct location: `[Module]/Repository/I[EntityName]Repository.cs`
8. ☐ Interface inherits from `ISpecificRepository<[EntityName], [EntityName]Id>`
9. ☐ Added XML summary comment with author tag
10. ☐ Added `Get(Guid guid)` method
11. ☐ Added `Find([EntityName]Id[] ids)` method
12. ☐ Added Code-related methods if entity has Code property
13. ☐ Added Name-related methods if entity has Name property
14. ☐ Used correct parameter naming (camelCase, plural + "Ids")

### Implementation File
15. ☐ Created implementation in correct location: `[Module]/Repository/NHibernate/Nh[EntityName]Repository.cs`
16. ☐ Class inherits from `AbstractNhSpecificRepository<[EntityName], [EntityName]Id>`
17. ☐ Class implements `I[EntityName]Repository`
18. ☐ Added XML summary comments with author tag
19. ☐ Added constructor with `ISessionFactory` parameter
20. ☐ Constructor calls `base(sessionFactory)`
21. ☐ Implemented all interface methods using NHibernate QueryOver API
22. ☐ Used `CurrentSession.QueryOver<[EntityName]>()`
23. ☐ Used `.SingleOrDefault<[EntityName]>()` for single results
24. ☐ Used `.Future()` for collections and existence checks
25. ☐ Used `.Future().Any()` for boolean existence checks
26. ☐ Added ReSharper comments for covariant array conversion

### Imports
27. ☐ Interface: Added `System`, `System.Collections.Generic`, entity namespace, EntityId namespace, `NextGen.Support.Base.Repository`
28. ☐ Implementation: Added `System`, `System.Linq`, `System.Collections.Generic`, `NHibernate`, entity namespace, EntityId namespace, `NextGen.Support.Data.NHibernate`

### Final
29. ☐ Used `create_directory` tool if directories don't exist
30. ☐ Used `write_file` tool to create interface file
31. ☐ Used `write_file` tool to create implementation file
32. ☐ Verified correct namespaces in both files

---

## Common Mistakes to Avoid

1. **❌ Wrong base interface/class**
   ```csharp
   // WRONG
   public interface IUnitOfMeasureRepository : IRepository<UnitOfMeasure>

   // CORRECT
   public interface IUnitOfMeasureRepository : ISpecificRepository<UnitOfMeasure, UnitOfMeasureId>
   ```

2. **❌ Missing ReSharper comments for array conversions**
   ```csharp
   // WRONG
   return CurrentSession.QueryOver<Entity>()
       .WhereRestrictionOn(x => x.Id)
       .IsIn(ids)
       .Future();

   // CORRECT
   return
       CurrentSession.QueryOver<Entity>()
                     .WhereRestrictionOn(x => x.Id)
       // ReSharper disable CoVariantArrayConversion
                     .IsIn(ids)
       // ReSharper restore CoVariantArrayConversion
                     .Future();
   ```

3. **❌ Using .ToList() instead of .Future()**
   ```csharp
   // WRONG - forces immediate execution
   return CurrentSession.QueryOver<Entity>().List();

   // CORRECT - deferred execution
   return CurrentSession.QueryOver<Entity>().Future();
   ```

4. **❌ Missing .Any() for existence checks**
   ```csharp
   // WRONG - returns IEnumerable, not bool
   public bool IsCodeExists(string code)
   {
       return CurrentSession.QueryOver<Entity>().Where(x => x.Code == code).Future();
   }

   // CORRECT
   public bool IsCodeExists(string code)
   {
       return CurrentSession.QueryOver<Entity>().Where(x => x.Code == code).Future().Any();
   }
   ```

5. **❌ Incorrect parameter naming**
   ```csharp
   // WRONG
   IEnumerable<UnitOfMeasure> Find(UnitOfMeasureId[] ids);

   // CORRECT
   IEnumerable<UnitOfMeasure> Find(UnitOfMeasureId[] unitOfMeasureIds);
   ```

6. **❌ Missing namespace import**
   ```csharp
   // WRONG - NHibernate namespace missing
   using System;
   using System.Linq;

   // CORRECT
   using System;
   using System.Linq;
   using System.Collections.Generic;
   using NHibernate;  // Required for ISessionFactory
   ```

7. **❌ Wrong method signature for Get(Guid)**
   ```csharp
   // WRONG - tries to use Guid directly
   public Entity Get(Guid guid)
   {
       return CurrentSession.QueryOver<Entity>().Where(x => x.Id == guid)...
   }

   // CORRECT - converts Guid to EntityId
   public Entity Get(Guid guid)
   {
       return Get(EntityId.Of(guid));
   }
   ```

---

## Notes

- **Code Formatting**:
  - **CRITICAL:** Do NOT add extra blank lines between code lines
  - Code should be compact and follow standard C# formatting
  - One blank line between methods
  - No blank lines between using statements

- **Directory Creation**: Use `create_directory` tool if needed:
  ```
  create_directory(path="src/modules/NextGen.Logistic/NextGen.Logistic.Core/Master/Repository")
  create_directory(path="src/modules/NextGen.Logistic/NextGen.Logistic.Core/Master/Repository/NHibernate")
  ```

- **Author Tag**: Use the author tag from the entity file or ask the user

- **Method Order**: Follow the standard order in templates (existence checks, Get methods, Find methods)

- **QueryOver vs Criteria**: Always use `QueryOver<T>()` (type-safe, lambda-based) instead of legacy Criteria API

- **Deferred Execution**: Use `.Future()` for collections to enable batch fetching and deferred execution

- **Naming Conventions**:
  - Interface: `I[EntityName]Repository`
  - Implementation: `Nh[EntityName]Repository`
  - Parameter for ID array: `[entityName]Ids` (camelCase, plural)
