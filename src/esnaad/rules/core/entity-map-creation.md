# Entity Map Creation Rules (FluentNHibernate)

## When to Create an Entity Map

**Trigger:** When user requests to create a Hibernate entity map with patterns like:
- "Create entity map for [EntityName]"
- "Create Hibernate mapping for [EntityName]"
- "Create FluentNHibernate map for [EntityName] entity"
- "Map [EntityName] entity to database"

**You MUST follow the complete workflow below.**

**CRITICAL:** After creating the entity map file, you MUST update the .csproj file to include it in the project. See `csproj-update.md` for detailed instructions.

---

## Step-by-Step Workflow

### Step 1: Locate and Read the Entity File

Before creating a map, you MUST read the entity file to analyze its structure.

**Action:**
1. Use `search_files` to find the entity file: `search_files(pattern="[EntityName].cs", path="src/modules")`
2. Use `read_file` to read the entity file and analyze:
   - Namespace (to determine domain/module)
   - Properties (names and types)
   - Whether it implements `INgAuditable`
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
Entity path: src/modules/NextGen.[Domain]/NextGen.[Domain].Core/[Module]/Entity/[EntityName].cs
Entity namespace: NextGen.[Domain].Core.[Module].Entity

Map path: src/modules/NextGen.[Domain]/NextGen.[Domain].Core/Config/EntityMap/[Module]/[EntityName]Map.cs
Map namespace: NextGen.[Domain].Core.Config.EntityMap.[Module]
```

**Example (UnitOfMeasure):**
```
Entity: NextGen.Logistic.Core/Master/Entity/UnitOfMeasure.cs
Domain: Logistic
Module: Master
Map location: NextGen.Logistic.Core/Config/EntityMap/Master/UnitOfMeasureMap.cs
Map namespace: NextGen.Logistic.Core.Config.EntityMap.Master
```

### Step 3: Determine Table Name

**Table naming follows migration script rules:**

Pattern: `[DOMAIN_CODE]_MST_[ENTITY_NAME]`

**Domain Code Mapping:**
| Domain | Code |
|--------|------|
| Admin | ADM |
| Logistic | LOG |
| Maintenance | MNT |
| Ammo | AMO |
| Operation | OPS |
| Organization | ORG |
| Security | SEC |

**Example:**
- Entity: `UnitOfMeasure` in Logistic domain
- Table: `LOG_MST_UNIT_OF_MEASURE`

### Step 4: Map Properties to Columns

Analyze each property in the entity and map to NHibernate mapping methods.

---

## Property Type to Mapping Method Rules

### 1. ID Mapping (Always Required)

**Entity Pattern:**
```csharp
public class UnitOfMeasure : EntityBase<UnitOfMeasureId>
```

**Map Pattern:**
```csharp
CompositeId(x => x.Id).KeyProperty(x => x.Value, "ID_");
```

**Rules:**
- ALWAYS use `CompositeId(x => x.Id).KeyProperty(x => x.Value, "ID_")`
- Column name is ALWAYS `ID_`

### 2. Version Mapping (Always Required)

**Entity Pattern:**
```csharp
// Inherited from EntityBase
public virtual long Version { get; protected set; }
```

**Map Pattern:**
```csharp
Version(x => x.Version).Column("VERSION_");
```

**Rules:**
- ALWAYS use `Version(x => x.Version).Column("VERSION_")`
- Column name is ALWAYS `VERSION_`

### 3. String Property Mapping

**Entity Pattern:**
```csharp
public virtual string Code { get; protected set; }
public virtual string Name { get; protected set; }
```

**Map Pattern:**
```csharp
Map(x => x.Code, "CODE_").Not.Nullable().Length(50);
Map(x => x.Name, "NAME_").Not.Nullable().Length(100);
```

**Rules:**
- Column name: `[PROPERTY_NAME]_` (uppercase with trailing underscore)
- Add `.Not.Nullable()` if property is NOT nullable
- Add `.Length(N)` for string properties
- **Default lengths:**
  - `Code`: 50
  - `Name`: 100
  - `Description`: 500
  - Other strings: 100 (or analyze usage to determine)

### 4. Boolean Property Mapping

**Entity Pattern:**
```csharp
public virtual bool IsBase { get; protected set; }
public virtual bool? IsActive { get; protected set; }
```

**Map Pattern:**
```csharp
Map(x => x.IsBase, "IS_BASE_").Not.Nullable();
Map(x => x.IsActive, "IS_ACTIVE_");
```

**Rules:**
- Column name: `[PROPERTY_NAME]_` (uppercase with trailing underscore)
- Add `.Not.Nullable()` if property is NOT nullable (`bool`)
- Omit `.Not.Nullable()` if property is nullable (`bool?`)
- **NO `.Length()` for boolean properties**

### 5. Integer Property Mapping

**Entity Pattern:**
```csharp
public virtual int Quantity { get; protected set; }
public virtual int? Level { get; protected set; }
```

**Map Pattern:**
```csharp
Map(x => x.Quantity, "QUANTITY_").Not.Nullable();
Map(x => x.Level, "LEVEL_");
```

**Rules:**
- Column name: `[PROPERTY_NAME]_` (uppercase with trailing underscore)
- Add `.Not.Nullable()` if property is NOT nullable (`int`)
- Omit `.Not.Nullable()` if property is nullable (`int?`)
- **NO `.Length()` for integer properties**

### 6. Decimal Property Mapping

**Entity Pattern:**
```csharp
public virtual decimal Price { get; protected set; }
public virtual decimal? Weight { get; protected set; }
```

**Map Pattern:**
```csharp
Map(x => x.Price, "PRICE_").Not.Nullable();
Map(x => x.Weight, "WEIGHT_");
```

**Rules:**
- Column name: `[PROPERTY_NAME]_` (uppercase with trailing underscore)
- Add `.Not.Nullable()` if property is NOT nullable (`decimal`)
- **NO `.Length()` for decimal properties**

### 7. DateTime Property Mapping

**Entity Pattern:**
```csharp
public virtual DateTime CreatedDate { get; protected set; }
public virtual DateTime? ModifiedDate { get; protected set; }
```

**Map Pattern:**
```csharp
Map(x => x.CreatedDate, "CREATED_DATE_").Not.Nullable();
Map(x => x.ModifiedDate, "MODIFIED_DATE_");
```

**Rules:**
- Column name: `[PROPERTY_NAME]_` (uppercase with trailing underscore)
- Add `.Not.Nullable()` if property is NOT nullable (`DateTime`)
- **NO `.Length()` for DateTime properties**

### 8. Enum/ObjectId Property Mapping (Lookup Values)

**Entity Pattern:**
```csharp
public virtual UnitOfMeasureCategory Category { get; protected set; }
public virtual IntervalCategory IntervalCategory { get; set; }
```

**Map Pattern:**
```csharp
Map(x => x.Category, "CATEGORY_").Not.Nullable().Length(100);
Map(x => x.IntervalCategory, "INTERVAL_CATEGORY_").Not.Nullable().Length(100);
```

**Rules:**
- Column name: `[PROPERTY_NAME]_` (uppercase with trailing underscore)
- Treat as string mapping
- Add `.Not.Nullable()` if required
- Default length: 100

### 9. Audit Entry (INgAuditable)

**Entity Pattern:**
```csharp
public virtual NgAuditEntry AuditEntry { get; protected set; }
```

**Map Pattern:**
```csharp
// ReSharper disable DoNotCallOverridableMethodsInConstructor
Component(x => x.AuditEntry);
// ReSharper restore DoNotCallOverridableMethodsInConstructor
```

**Rules:**
- ALWAYS use `Component(x => x.AuditEntry)` for entities implementing `INgAuditable`
- ALWAYS wrap with ReSharper comments
- This expands to 9 audit columns automatically (see migration rules)

### 10. Entity Reference Mapping (Foreign Keys)

**Entity Pattern:**
```csharp
public virtual DataRestriction Command { get; protected set; }
public virtual Platform Platform { get; protected set; }
```

**Map Pattern:**
```csharp
References(x => x.Command, "COMMAND_ID_").Not.Nullable();
References(x => x.Platform, "PLATFORM_ID_");
```

**Rules:**
- Use `References(x => x.PropertyName, "COLUMN_NAME_")`
- Column name: `[PROPERTY_NAME]_ID_` (entity name + `_ID_`)
- Add `.Not.Nullable()` if reference is required
- **NO `.Length()` for references (they're GUIDs)**

### 11. EntityId Property Mapping (ID References)

**Entity Pattern:**
```csharp
public virtual DataRestrictionId CommandId { get; set; }
public virtual PlatformId PlatformId { get; set; }
```

**Map Pattern:**
```csharp
Map(x => x.CommandId, "COMMAND_ID_").Not.Nullable();
Map(x => x.PlatformId, "PLATFORM_ID_");
```

**Rules:**
- Use `Map(x => x.PropertyName, "COLUMN_NAME_")`
- Column name: `[PROPERTY_NAME]_` (property name already ends with `Id`)
- Add `.Not.Nullable()` if required
- **NO `.Length()` for EntityId properties (they're custom value objects wrapping GUIDs)**

### 12. Collections (One-to-Many)

**Entity Pattern:**
```csharp
public virtual ISet<OrderLine> OrderLines { get; protected set; }
```

**Map Pattern:**
```csharp
HasMany(x => x.OrderLines)
    .KeyColumn("ORDER_ID_")
    .Cascade.AllDeleteOrphan()
    .Inverse();
```

**Rules:**
- Use `HasMany(x => x.PropertyName)` for collections
- Specify foreign key column with `.KeyColumn("[PARENT]_ID_")`
- Add cascade behavior as needed
- Usually mark as `.Inverse()` (child manages relationship)

---

## Table Mapping

**Required Components:**

1. **Table Name:**
```csharp
Table("[DOMAIN_CODE]_MST_[ENTITY_NAME]");
```

2. **Cache Strategy:**
```csharp
Cache.NonStrictReadWrite().Region(CacheRegionConstant.UpdateableMaster);
```

**Full Example:**
```csharp
Table("LOG_MST_UNIT_OF_MEASURE");
Cache.NonStrictReadWrite().Region(CacheRegionConstant.UpdateableMaster);
```

---

## Complete Entity Map Template

```csharp
using FluentNHibernate.Mapping;
using NextGen.Admin.Core.Shared.Admin;
using NextGen.[Domain].Core.[Module].Entity;

namespace NextGen.[Domain].Core.Config.EntityMap.[Module]
{
#pragma warning disable 1591
    /// <summary>
    ///
    /// </summary>
    /// <author>[username]</author>
    public class [EntityName]Map : ClassMap<[EntityName]>
    {
        public [EntityName]Map()
        {
            // ID mapping (ALWAYS REQUIRED)
            CompositeId(x => x.Id).KeyProperty(x => x.Value, "ID_");

            // Version mapping (ALWAYS REQUIRED)
            Version(x => x.Version).Column("VERSION_");

            // Property mappings
            Map(x => x.Code, "CODE_").Not.Nullable().Length(50);
            Map(x => x.Name, "NAME_").Not.Nullable().Length(100);
            // ... other properties ...

            // Audit entry (if INgAuditable)
            // ReSharper disable DoNotCallOverridableMethodsInConstructor
            Component(x => x.AuditEntry);
            // ReSharper restore DoNotCallOverridableMethodsInConstructor

            // Table name
            Table("[DOMAIN_CODE]_MST_[ENTITY_NAME]");

            // Cache strategy
            Cache.NonStrictReadWrite().Region(CacheRegionConstant.UpdateableMaster);
        }
    }
#pragma warning restore 1591
}
```

---

## Required Imports (Using Statements)

**Standard imports for all maps:**
```csharp
using FluentNHibernate.Mapping;
using NextGen.Admin.Core.Shared.Admin;  // For CacheRegionConstant
using NextGen.[Domain].Core.[Module].Entity;  // For the entity class
```

**Additional imports as needed:**
- Entity references: Add using for each referenced entity's namespace
- Custom types: Add using for custom type namespaces

---

## Complete Example: UnitOfMeasure Entity Map

**Entity File (for reference):**
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

**Entity Map File:**
```csharp
// Location: NextGen.Logistic.Core/Config/EntityMap/Master/UnitOfMeasureMap.cs
using FluentNHibernate.Mapping;
using NextGen.Admin.Core.Shared.Admin;
using NextGen.Logistic.Core.Master.Entity;

namespace NextGen.Logistic.Core.Config.EntityMap.Master
{
#pragma warning disable 1591
    /// <summary>
    ///
    /// </summary>
    /// <author>gal7634</author>
    public class UnitOfMeasureMap : ClassMap<UnitOfMeasure>
    {
        public UnitOfMeasureMap()
        {
            CompositeId(x => x.Id).KeyProperty(x => x.Value, "ID_");
            Version(x => x.Version).Column("VERSION_");
            Map(x => x.Code, "CODE_").Not.Nullable().Length(50);
            Map(x => x.Name, "NAME_").Not.Nullable().Length(100);
            Map(x => x.Category, "CATEGORY_").Not.Nullable().Length(100);
            Map(x => x.IsBase, "IS_BASE_").Not.Nullable();
            // ReSharper disable DoNotCallOverridableMethodsInConstructor
            Component(x => x.AuditEntry);
            // ReSharper restore DoNotCallOverridableMethodsInConstructor
            Table("LOG_MST_UNIT_OF_MEASURE");
            Cache.NonStrictReadWrite().Region(CacheRegionConstant.UpdateableMaster);
        }
    }
#pragma warning restore 1591
}
```

---

## Example 2: Entity with References

**Entity File:**
```csharp
namespace NextGen.Maintenance.Core.WeightBalance.Entity
{
    public class WeightBalance : EntityBase<WeightBalanceId>, INgAuditable
    {
        public virtual NgAuditEntry AuditEntry { get; protected set; }
        public virtual DataRestriction Command { get; protected set; }
        public virtual Platform Platform { get; protected set; }
        public virtual string Code { get; protected set; }
        public virtual string Name { get; protected set; }
        public virtual decimal? MaxWeight { get; protected set; }
        public virtual bool IsActive { get; protected set; }
    }
}
```

**Entity Map File:**
```csharp
// Location: NextGen.Maintenance.Core/Config/EntityMap/WeightBalance/WeightBalanceMap.cs
using FluentNHibernate.Mapping;
using NextGen.Admin.Core.Shared.Admin;
using NextGen.Maintenance.Core.WeightBalance.Entity;

namespace NextGen.Maintenance.Core.Config.EntityMap.WeightBalance
{
#pragma warning disable 1591
    /// <summary>
    ///
    /// </summary>
    /// <author>gal7634</author>
    public class WeightBalanceMap : ClassMap<WeightBalance>
    {
        public WeightBalanceMap()
        {
            CompositeId(x => x.Id).KeyProperty(x => x.Value, "ID_");
            Version(x => x.Version).Column("VERSION_");
            References(x => x.Command, "COMMAND_ID_").Not.Nullable();
            References(x => x.Platform, "PLATFORM_ID_").Not.Nullable();
            Map(x => x.Code, "CODE_").Not.Nullable().Length(50);
            Map(x => x.Name, "NAME_").Not.Nullable().Length(100);
            Map(x => x.MaxWeight, "MAX_WEIGHT_");
            Map(x => x.IsActive, "IS_ACTIVE_").Not.Nullable();
            // ReSharper disable DoNotCallOverridableMethodsInConstructor
            Component(x => x.AuditEntry);
            // ReSharper restore DoNotCallOverridableMethodsInConstructor
            Table("MNT_MST_WEIGHT_BALANCE");
            Cache.NonStrictReadWrite().Region(CacheRegionConstant.UpdateableMaster);
        }
    }
#pragma warning restore 1591
}
```

---

## Example 3: Entity with EntityId Properties

**Entity File:**
```csharp
namespace NextGen.Maintenance.Core.MissionEquipment.Entity
{
    public class MasterEquipment : EntityBase<MasterEquipmentId>, INgAuditable
    {
        public virtual NgAuditEntry AuditEntry { get; protected set; }
        public virtual DataRestrictionId CommandId { get; set; }
        public virtual PlatformId PlatformId { get; set; }
        public virtual ItemId MajorEndItemId { get; set; }
        public virtual string Reference { get; set; }
        public virtual string Remarks { get; set; }
    }
}
```

**Entity Map File:**
```csharp
// Location: NextGen.Maintenance.Core/Config/EntityMap/MissionEquipment/MasterEquipmentMap.cs
using FluentNHibernate.Mapping;
using NextGen.Admin.Core.Shared.Admin;
using NextGen.Maintenance.Core.MissionEquipment.Entity;

namespace NextGen.Maintenance.Core.Config.EntityMap.MissionEquipment
{
#pragma warning disable 1591
    /// <summary>
    ///
    /// </summary>
    /// <author>gal7634</author>
    public class MasterEquipmentMap : ClassMap<MasterEquipment>
    {
        public MasterEquipmentMap()
        {
            CompositeId(x => x.Id).KeyProperty(x => x.Value, "ID_");
            Version(x => x.Version).Column("VERSION_");
            Map(x => x.CommandId, "COMMAND_ID_").Not.Nullable();
            Map(x => x.PlatformId, "PLATFORM_ID_").Not.Nullable();
            Map(x => x.MajorEndItemId, "MAJOR_END_ITEM_ID_").Not.Nullable();
            Map(x => x.Reference, "REFERENCE_").Length(100);
            Map(x => x.Remarks, "REMARKS_").Length(500);
            // ReSharper disable DoNotCallOverridableMethodsInConstructor
            Component(x => x.AuditEntry);
            // ReSharper restore DoNotCallOverridableMethodsInConstructor
            Table("MNT_MST_MASTER_EQUIPMENT");
            Cache.NonStrictReadWrite().Region(CacheRegionConstant.UpdateableMaster);
        }
    }
#pragma warning restore 1591
}
```

---

## Quick Decision Tree: Property to Mapping Method

```
What is the property?

Is it "Id" (entity ID)?
├─ YES → CompositeId(x => x.Id).KeyProperty(x => x.Value, "ID_")
└─ NO → Continue...

Is it "Version"?
├─ YES → Version(x => x.Version).Column("VERSION_")
└─ NO → Continue...

Is it "AuditEntry" (NgAuditEntry)?
├─ YES → Component(x => x.AuditEntry) with ReSharper comments
└─ NO → Continue...

Is it an Entity reference (e.g., DataRestriction, Platform)?
├─ YES → References(x => x.PropertyName, "[PROPERTY_NAME]_ID_")
└─ NO → Continue...

Is it a primitive type (string, int, bool, decimal, DateTime)?
├─ YES → Map(x => x.PropertyName, "[PROPERTY_NAME]_")
│   ├─ If string → Add .Length(N)
│   ├─ If NOT nullable → Add .Not.Nullable()
│   └─ If nullable (int?, bool?, decimal?, DateTime?) → Omit .Not.Nullable()
└─ NO → Continue...

Is it an EntityId property (ends with Id: CommandId, PlatformId)?
├─ YES → Map(x => x.PropertyName, "[PROPERTY_NAME]_")
│   └─ Add .Not.Nullable() if required
└─ NO → Continue...

Is it an Enum/ObjectId (Category, Type, Status, Code)?
├─ YES → Map(x => x.PropertyName, "[PROPERTY_NAME]_").Length(100)
│   └─ Add .Not.Nullable() if required
└─ NO → Continue...

Is it a Collection (ISet<T>, IList<T>)?
└─ YES → HasMany(x => x.PropertyName).KeyColumn("[PARENT]_ID_")
```

---

## File Location Patterns

| Component | Pattern | Example (UnitOfMeasure) |
|-----------|---------|-------------------------|
| Entity | `NextGen.[Domain].Core/[Module]/Entity/[EntityName].cs` | `NextGen.Logistic.Core/Master/Entity/UnitOfMeasure.cs` |
| Entity Map | `NextGen.[Domain].Core/Config/EntityMap/[Module]/[EntityName]Map.cs` | `NextGen.Logistic.Core/Config/EntityMap/Master/UnitOfMeasureMap.cs` |
| Entity Namespace | `NextGen.[Domain].Core.[Module].Entity` | `NextGen.Logistic.Core.Master.Entity` |
| Map Namespace | `NextGen.[Domain].Core.Config.EntityMap.[Module]` | `NextGen.Logistic.Core.Config.EntityMap.Master` |

---

## Quick Reference: Creation Checklist

When creating an entity map, verify:

### Preparation
1. ☐ Read entity file to analyze structure
2. ☐ Identified domain and module from entity namespace
3. ☐ Determined table name from domain code and entity name
4. ☐ Analyzed all entity properties and their types

### Map Structure
5. ☐ Created map file in correct location: `Config/EntityMap/[Module]/[EntityName]Map.cs`
6. ☐ Map class inherits from `ClassMap<[EntityName]>`
7. ☐ Added `#pragma warning disable/restore 1591` directives
8. ☐ Added XML summary comment with author tag

### Required Mappings
9. ☐ Added `CompositeId(x => x.Id).KeyProperty(x => x.Value, "ID_")`
10. ☐ Added `Version(x => x.Version).Column("VERSION_")`
11. ☐ Added `Component(x => x.AuditEntry)` if entity implements INgAuditable
12. ☐ Added ReSharper comments around Component mapping

### Property Mappings
13. ☐ Mapped all string properties with `.Length(N)`
14. ☐ Mapped all non-nullable properties with `.Not.Nullable()`
15. ☐ Mapped entity references with `References()`
16. ☐ Mapped EntityId properties with `Map()`
17. ☐ Used correct column names (UPPERCASE with trailing underscore)

### Table and Cache
18. ☐ Added `Table("[DOMAIN_CODE]_MST_[ENTITY_NAME]")`
19. ☐ Added `Cache.NonStrictReadWrite().Region(CacheRegionConstant.UpdateableMaster)`

### Imports
20. ☐ Added `using FluentNHibernate.Mapping;`
21. ☐ Added `using NextGen.Admin.Core.Shared.Admin;`
22. ☐ Added entity namespace import
23. ☐ Added any additional required imports

### Final
24. ☐ Used `write_file` tool to create map file
25. ☐ Verified correct namespace in file
26. ☐ **Updated .csproj to include map file** (`Config\EntityMap\[Module]\[EntityName]Map.cs`)

---

## Common Mistakes to Avoid

1. **❌ Adding `.Length()` to non-string properties**
   ```csharp
   // WRONG
   Map(x => x.IsActive, "IS_ACTIVE_").Not.Nullable().Length(1);

   // CORRECT
   Map(x => x.IsActive, "IS_ACTIVE_").Not.Nullable();
   ```

2. **❌ Using References() for EntityId properties**
   ```csharp
   // Property: public virtual DataRestrictionId CommandId { get; set; }

   // WRONG
   References(x => x.CommandId, "COMMAND_ID_");

   // CORRECT
   Map(x => x.CommandId, "COMMAND_ID_").Not.Nullable();
   ```

3. **❌ Using Map() for Entity references**
   ```csharp
   // Property: public virtual DataRestriction Command { get; protected set; }

   // WRONG
   Map(x => x.Command, "COMMAND_ID_");

   // CORRECT
   References(x => x.Command, "COMMAND_ID_").Not.Nullable();
   ```

4. **❌ Incorrect column naming**
   ```csharp
   // WRONG
   Map(x => x.Code, "Code");  // Lowercase
   Map(x => x.Name, "NAME");  // Missing trailing underscore

   // CORRECT
   Map(x => x.Code, "CODE_");
   Map(x => x.Name, "NAME_");
   ```

5. **❌ Missing ReSharper comments for Component**
   ```csharp
   // WRONG
   Component(x => x.AuditEntry);

   // CORRECT
   // ReSharper disable DoNotCallOverridableMethodsInConstructor
   Component(x => x.AuditEntry);
   // ReSharper restore DoNotCallOverridableMethodsInConstructor
   ```

6. **❌ Wrong table name format**
   ```csharp
   // WRONG
   Table("UnitOfMeasure");
   Table("LOG_UNIT_OF_MEASURE");

   // CORRECT
   Table("LOG_MST_UNIT_OF_MEASURE");
   ```

---

## Notes

- **Code Formatting**:
  - **CRITICAL:** Do NOT add extra blank lines between code lines
  - Code should be compact and follow standard C# formatting
  - Only one blank line between using statements and namespace
  - Only one blank line between class members
  - Mapping statements should be tightly packed (no blank lines between mappings)

- **Directory Creation**: Use `create_directory` tool if needed:
  ```
  create_directory(path="src/modules/NextGen.Logistic/NextGen.Logistic.Core/Config/EntityMap/Master")
  ```

- **Author Tag**: Use the author tag from the entity file (e.g., `gal7634`) or ask the user

- **Nullable Properties**: ONLY omit `.Not.Nullable()` if the property type is nullable (`?` suffix)

- **EntityId vs Entity**:
  - EntityId properties use `Map()` (they're value objects)
  - Entity references use `References()` (they're entity relationships)

- **String Lengths**: Choose appropriate lengths based on property semantics:
  - Code: 50
  - Name: 100
  - Description/Remarks: 500
  - Short identifiers: 50
  - Other strings: 100 (default)
