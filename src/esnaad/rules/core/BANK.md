

---

## Error Handling

### Error Code Convention
Format: `[DOMAIN].[USECASE].[SEQUENCE]`

```csharp
// Location: NextGen.[Module].Core/{Module}CoreErrorCodes.cs
public class AdminCoreErrorCodes
{
    public static class LoginErrorCodes
    {
        public const string RegistrationUnderProcess = "ADM.001.001";
        public const string DeactivatedUser = "ADM.001.009";
    }

    public static class ItemUnitManagement
    {
        public const string SerialNoAlreadyExists = "E.LOG.001.39.001";
    }
}
```

### Exception Handling
```csharp
try
{
    CommandBus.Send(command);
}
catch (NextGenException ex)
{
    // Handle domain exceptions
    return false;
}
```

---

## Security Pattern

### Resource-Based Authorization
```csharp
[Secured(ResourceCodes = new[] { View, Print, Export, Manage, Approve })]
public virtual IList<LabelValue<string, long>> FindCommands()
{
    // Protected method
}

// Security constants
private const string View = SecuredResourceCodes.LogisticsDomain.AssetManagementModule.View;
private const string Manage = SecuredResourceCodes.LogisticsDomain.AssetManagementModule.Manage;
```

---



---

## Key Rules for Implementation

1. **Always use property injection** with private getters, never constructor injection
2. **Use `[Managed]` attribute** on Spring-managed classes
3. **Use `[Transaction]` attribute** on methods that modify data
4. **Use `[Transaction(ReadOnly = true)]`** on read-only methods
5. **DTOs are called VOs** (Value Objects) with `Vo` suffix
6. **Entities inherit from `EntityBase<TId>`** with strongly-typed IDs
7. **Implement `INgAuditable`** for entities that need audit trails
8. **Validation logic goes in entity classes** using factory methods
9. **Use `Assertions.Check()`** for domain validation
10. **Error codes follow the format** `[DOMAIN].[USECASE].[SEQ]`
11. **Repository interfaces go in Core**, implementations in `NHibernate/` subfolder
12. **Commands and Events go in `Shared/`** directory
13. **API classes end with `Api`**, use `[RestService]` and `[Uri]` attributes
14. **Facades coordinate between layers** and handle cross-cutting concerns
15. **Use `ICommandBus.Send()`** for executing commands

---

## File Locations Summary

| Component | Location Pattern |
|-----------|------------------|
| API Controllers | `NextGen.[Module].App/API/{Name}Api.cs` |
| Facades | `NextGen.[Module].App/{Feature}/{Name}Facade.cs` |
| Value Objects | `NextGen.[Module].App/{Feature}/Vo/{Name}Vo.cs` |
| Entities | `NextGen.[Module].Core/{Function}/Entity/{Name}.cs` |
| Entity Maps | `NextGen.[Module].Core/Config/EntityMap/{Function}/{Name}Map.cs` |
| Entity ID Classes | `NextGen.Admin.Core/Shared/{Domain}/{Function}/{Name}Id.cs` |
| Repositories (Interface) | `NextGen.[Module].Core/{Function}/Repository/I{Name}Repository.cs` |
| Repositories (Impl) | `NextGen.[Module].Core/{Function}/Repository/NHibernate/Nh{Name}Repository.cs` |
| Command Handlers | `NextGen.[Module].Core/{Function}/{Name}CommandHandler.cs` |
| Event Handlers | `NextGen.[Module].Core/{Function}/{Name}EventHandler.cs` |
| Commands | `NextGen.Admin.Core/Shared/{Domain}/{Function}/Command/{Name}.cs` |
| Events | `NextGen.Admin.Core/Shared/{Domain}/{Function}/Event/{Name}.cs` |
| Error Codes | `NextGen.[Module].Core/{Module}CoreErrorCodes.cs` |
| DB Migrations | `db/fw/sql/` |

---





### Database Table Naming Convention

Format: `[ModuleCode]_[TypeCode]_[FunctionCode]_[EntityName]`

| Module Code | Module |
|-------------|--------|
| ADM | Admin |
| LOG | Logistic |
| AMO | Ammo |
| MNT | Maintenance |
| OPN | Operation |
| PMC | Pmco |

| Type Code | Meaning |
|-----------|---------|
| MST | Master (reference data) |
| TRN | Transaction (operational data) |
| HST | History (audit data) |

**Column Naming:**
- All columns end with underscore: `ID_`, `NAME_`, `CODE_`, `STATUS_`
- Foreign keys: `[ENTITY]_ID` (e.g., `COMMAND_ID`, `PLATFORM_ID`)

### Entity Inheritance Pattern

**For derived entities (subclasses), use:**

Base Entity Map:
```csharp
public class AssetTransactionMap : ClassMap<AssetTransaction>
{
    public AssetTransactionMap()
    {
        // ... common mappings
        DiscriminateSubClassesOnColumn<string>("PBO_MOVEMENT_TYPE_");
        Table("LOG_TRN_ASM_ASSET_TRANSACTION");
    }
}
```

Derived Entity Map:
```csharp
public class AssetReturnRequestMap : SubclassMap<AssetReturnRequest>
{
    public AssetReturnRequestMap()
    {
        DiscriminatorValue(PboTransactionType.AssetReturn);
    }
}
```

### Child/Value Objects (Non-Aggregate Entities)

For child objects that belong to a parent entity:
- Do NOT inherit from `EntityBase<TId>`
- Do NOT implement `INgAuditable`
- Map as `HasMany(...).Component(...)` in parent's map

```csharp
// Child object - no base class, no audit
public class AmmoExerciseItem
{
    public virtual AmmunitionItemId AmmoItemId { get; protected set; }
    public virtual int? Quantity { get; protected set; }
}
```

**File 9 - Flyway migration script example:**
```
Path: src/modules/NextGen.Ammo/NextGen.Ammo.Core/Config/EntityMap/AmmunitionExercise/AmmoExerciseMap.cs
```
```csharp
namespace NextGen.Ammo.Core.Config.EntityMap.AmmunitionExercise
{
    public class AmmoExerciseMap : ClassMap<AmmoExercise>
    {
        public AmmoExerciseMap()
        {
            CompositeId(x => x.Id).KeyProperty(x => x.Value, "ID_");
            Version(x => x.Version).Column("VERSION_");

            Map(x => x.ExerciseNo, "EXERCISE_NO_").Not.Nullable();
            Map(x => x.Category, "CATEGORY_").Not.Nullable();
            Map(x => x.IsActive, "IS_ACTIVE_").Not.Nullable();

            Component(x => x.AuditEntry);
            Table("AMO_TRN_EXC_EXERCISE");
        }
    }
}

## Repository Creation Guide

### CRITICAL: When creating a Repository for an Entity, create these 2 files:

```
1. INTERFACE:       NextGen.[Module].Core/[Function]/Repository/I[Entity]Repository.cs
2. IMPLEMENTATION:  NextGen.[Module].Core/[Function]/Repository/NHibernate/Nh[Entity]Repository.cs
```

### Repository Interface Template

```csharp
// Location: NextGen.[Module].Core/[Function]/Repository/I[Entity]Repository.cs
using NextGen.Support.Base.Repository;

namespace NextGen.[Module].Core.[Function].Repository
{
    public interface I[Entity]Repository : ISpecificRepository<[Entity], [Entity]Id>
    {
        // Add custom query methods as needed
        [Entity] GetByCode(string code);
        IEnumerable<[Entity]> FindByStatus(bool isActive);
    }
}
```

### Repository Implementation Template

```csharp
// Location: NextGen.[Module].Core/[Function]/Repository/NHibernate/Nh[Entity]Repository.cs
using NHibernate;
using NextGen.Support.Base.Ioc.Attributes;
using NextGen.Support.Data.NHibernate;

namespace NextGen.[Module].Core.[Function].Repository.NHibernate
{
    [Managed]  // Required for IoC registration
    public class Nh[Entity]Repository : AbstractNhSpecificRepository<[Entity], [Entity]Id>, I[Entity]Repository
    {
        [Inject]  // Required for constructor injection
        public Nh[Entity]Repository(ISessionFactory sessionFactory) : base(sessionFactory)
        {
        }

        public [Entity] GetByCode(string code)
        {
            return CurrentSession.CreateQuery("from [Entity] where Code = :code")
                .SetString("code", code)
                .UniqueResult<[Entity]>();
        }

        public IEnumerable<[Entity]> FindByStatus(bool isActive)
        {
            return CurrentSession.QueryOver<[Entity]>()
                .Where(x => x.IsActive == isActive)
                .Future();
        }
    }
}
```

### Key Repository Attributes

| Attribute | Purpose |
|-----------|---------|
| `[Managed]` | Registers class with IoC container (required on implementation class) |
| `[Inject]` | Marks constructor for dependency injection |

### NHibernate Query Patterns

**QueryOver API (Type-Safe):**
```csharp
CurrentSession.QueryOver<Entity>()
    .Where(x => x.Property == value)
    .WhereRestrictionOn(x => x.Id).IsIn(ids)
    .Cacheable()
    .Future();
```

**HQL (Hibernate Query Language):**
```csharp
CurrentSession.CreateQuery("from Entity where Property = :value")
    .SetString("value", value)
    .UniqueResult<Entity>();
```

**Native SQL:**
```csharp
CurrentSession.CreateSQLQuery("SELECT * FROM TABLE WHERE ID = :id")
    .SetInt64("id", id)
    .UniqueResult<int>();
```

### Using Repositories in Command Handlers

```csharp
public class [Entity]CommandHandler : IHandler<Save[Entity]>
{
    // Property injection (NOT constructor injection for handlers)
    public I[Entity]Repository [Entity]Repository { private get; set; }

    [Transaction]
    public void Handle(Save[Entity] command)
    {
        var entity = [Entity]Repository.Get(command.Id);
        if (entity == null)
        {
            entity = new [Entity](command.Name, command.Code);
            [Entity]Repository.Add(entity);
        }
        else
        {
            entity.Update(command.Name);
        }
    }
}
```

### Base Repository Methods (Inherited from ISpecificRepository)

| Method | Description |
|--------|-------------|
| `Get(TId id)` | Get entity by ID |
| `Add(TEntity entity)` | Add new entity |
| `Remove(TEntity entity)` | Delete entity |
| `GetAndCheckVersion(TId id, long version)` | Get with optimistic locking check |
```




