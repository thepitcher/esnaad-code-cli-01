## Naming Conventions

### Class Naming
| Pattern | Example | Location |
|---------|---------|----------|
| `I{Name}Service` | `IEmailNotificationService` | Core/Service/ |
| `{Name}Service` | `EmailNotificationService` | Core/Service/ |
| `{Name}Facade` | `AssetManagementFacade` | App/Facade/ |
| `I{Name}Repository` | `IAssetTransactionRepository` | Core/Repository/ |
| `Nh{Name}Repository` | `NhAssetTransactionRepository` | Core/Repository/NHibernate/ |
| `{Name}Api` | `UserApi` | App/API/ |
| `{Name}Vo` | `AssetBreakDownListVo` | App/{Feature}/Vo/ |
| `{Name}Finder` | `IAccessManagementFinder` | App/ |
| `{Name}CommandHandler` | `AssetManagementCommandHandler` | Core/ |
| `{Name}EventHandler` | `AssetManagementEventHandler` | Core/ |
| `{Name}Map` | `AirBaseMap` | Core/Config/EntityMap/ |
| `{Name}Id` | `AssetTransactionId` | Core/Shared/ |

### Method Naming
- **API methods**: Prefix with HTTP verb (`Get`, `Post`, `Put`, `Delete`)
- **Handler methods**: `Handle(TCommand command)`
- **Repository methods**: `Get()`, `Add()`, `Remove()`, `GetAndCheckVersion()`

### File Organization
- One class per file
- File name matches class name exactly
- Namespace mirrors directory structure

---