## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| .NET Framework | 4.0.1 | Runtime platform (NOT .NET Core) |
| ASP.NET | Classic | Web framework (IIS-hosted) |
| NHibernate | 3.3.3.4001 | ORM |
| FluentNHibernate | 1.4.0.0 | NHibernate mapping |
| Spring.NET | 2.0.0 | IoC/DI container |
| SQL Server | - | Database |
| Flyway | - | Database migrations |
| AutoMapper | 3.2.1 | Object mapping |
| NLog | - | Logging (via Common.Logging) |
| ZeroMQ | clrzmq 2.2.5.1 | Messaging |

---

## Project Structure

```
core/
├── src/
│   ├── modules/                    
│   │   ├── NextGen.Admin/          # Administration Domain
│   │   │   ├── NextGen.Admin.Core/     # Domain logic, entities, repositories, Command Handler, Event Handler, Services
│   │   │   └── NextGen.Admin.App/      # Facades, Finder, VOs
│   │   ├── NextGen.Logistic/       # Logistics Domain
│   │   │   ├── NextGen.Logistic.Core/
│   │   │   └── NextGen.Logistic.App/
│   │   ├── NextGen.Maintenance/    # Maintenance Domain
│   │   ├── NextGen.Operation/      # Operations Domain
│   │   ├── NextGen.Pmco/           # PMCO Domain
│   │   └── NextGen.Ammo/           # Ammunition Domain
│   ├── server/                     # Core server components
│   ├── runtime/                    # HTTP runtime (entry point)
│   │   └── NextGen.Runtime.Http/
│   └── packages/                   # NuGet packages
├── db/
│   └── fw/                         # Flyway migration scripts
└── build/                          # Build output

```

### Domain Pattern
Every domain (Admin, Ammo, Logistic, Operation, etc) reside under src/modules and follows **Core + App** separation:
- **`NextGen.[Domain].Core`** - Domain entities, repositories, command handlers, event handlers, services
- **`NextGen.[Domain].App`** - Facades, APIs, VOs (Value Objects), finders

example project structure for Logistics (LOG) Domain
- main path : src\modules\NextGen.Logistic
- Logistic core path: src\modules\NextGen.Logistic\NextGen.Logistic.Core
- Logistic App path: src\modules\NextGen.Logistic\NextGen.Logistic.App
---

### Module Pattern
Module name should be in Pascal case. Each module live under NextGen.[Domain].Core for core implementation and `NextGen.[Domain].App for App implementation.

This is structure for NextGen.[Domain].Core:
- Entity. Example: src\modules\NextGen.Logistic\NextGen.Logistic.Core\PurchaseOrderManagement\Entity\PurchaseOrder.cs
- Repository interface. Example: src\modules\NextGen.Logistic\NextGen.Logistic.Core\PurchaseOrderManagement\Repository\IPurchaseOrderRepository.cs
- Hibernate Repository. Example: src\modules\NextGen.Logistic\NextGen.Logistic.Core\PurchaseOrderManagement\Repository\NHibernate\NhPurchaseOrderRepository.cs
- Command Handler. Example: src\modules\NextGen.Logistic\NextGen.Logistic.Core\PurchaseOrderManagement\PurchaseOrderManagementCommandHandler.cs
- Event Handler (optional). Example: c:\Workspace\Esnaad\Esnaad_03\core\src\modules\NextGen.Logistic\NextGen.Logistic.Core\PurchaseOrderManagement\PurchaseOrderManagementEventHandler.cs

This is structure for NextGen.[Domain].App:
- Facade. Example: src\modules\NextGen.Logistic\NextGen.Logistic.App\PurchaseManagement\
- Finder interface. Example: src\modules\NextGen.Logistic\NextGen.Logistic.App\PurchaseManagement\IPurchaseManagementFinder.cs
- Finder Hibernate. Example: src\modules\NextGen.Logistic\NextGen.Logistic.App\PurchaseManagement\NhPurchaseManagementFinder.cs
- VO. Example: src\modules\NextGen.Logistic\NextGen.Logistic.App\PurchaseManagement\Vo\POItemsListVo.cs
---

### NextGen.[Domain].App structures

## Shared Code Location

All shared definitions are in: `NextGen.Admin.Core\Shared\`

Structure:
```
Shared/
├── Admin/           # Admin module shared code
├── Logistic/        # Logistic module shared code
│   ├── AssetManagement/
│   │   ├── Command/
│   │   ├── Event/
│   │   └── {Entity}Id.cs
├── Maintenance/
├── Operation/
└── ...
```


## Architecture Patterns

### 1. Layered Architecture
```
API Layer (REST Controllers)
    ↓
Facade Layer (Orchestration)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Entity Layer (Domain Models)
```

### 2. CQRS (Command Query Responsibility Segregation)
- **Commands** are sent via `ICommandBus`
- **Command Handlers** implement `IHandler<TCommand>`
- **Events** implement `IEvent`
- **Event Handlers** implement `IHandler<TEvent>`

### 3. Dependency Injection (Spring.NET)
- Use `[Managed]` attribute on classes
- **Property-based injection** (NOT constructor injection)
- Private setters with public properties

```csharp
[Managed]
public class MyService : IMyService
{
    // Property injection - this is the pattern used throughout
    public IRepository Repository { private get; set; }
    public ICommandBus CommandBus { private get; set; }
}
```