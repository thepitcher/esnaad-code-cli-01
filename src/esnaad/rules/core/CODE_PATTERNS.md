## Code Patterns

### 1. REST API Controller
```csharp
// Location: NextGen.[Module].App/API/{Name}Api.cs
[RestService]
public class AssetApi
{
    // Property injection
    public ICommandBus CommandBus { private get; set; }
    public IAssetFacade AssetFacade { private get; set; }

    [Transaction(ReadOnly = true)]
    [Uri(UriTemplate = "/asset/list")]
    public IList<AssetVo> GetAssets()
    {
        return AssetFacade.GetAssets();
    }

    [Uri(UriTemplate = "/asset/save")]
    public void PostSaveAsset(SaveAssetCommand command)
    {
        CommandBus.Send(command);
    }
}
```

**Key Attributes:**
- `[RestService]` - Marks class as REST endpoint
- `[Uri(UriTemplate = "...")]` - Maps method to URI
- `[Transaction]` - Transaction boundary
- `[Transaction(ReadOnly = true)]` - Read-only transaction
- `[Secured(ResourceCodes = new[] { ... })]` - Authorization

### 2. Command Pattern
```csharp
// Location: NextGen.[Module].Core/Shared/{Domain}/Command/{CommandName}.cs
public class SaveConfiguration : ICommand
{
    public string Id { get; set; }
    public long Version { get; set; }
    public string Value { get; set; }
    public string Description { get; set; }
}
```

### 3. Command Handler
```csharp
// Location: NextGen.[Module].Core/{Feature}/{Name}CommandHandler.cs
public class ConfigurationCommandHandler : IHandler<SaveConfiguration>, IHandler<DeleteConfiguration>
{
    public IConfigurationRepository ConfigurationRepository { private get; set; }

    [Transaction]
    public void Handle(SaveConfiguration o)
    {
        var configuration = ConfigurationRepository.Get(o.Id);
        if (configuration == null)
            CreateNewConfiguration(o);
        else
            UpdateConfiguration(o, configuration);
    }
}
```

### 4. Value Object (DTO)
```csharp
// Location: NextGen.[Module].App/{Feature}/Vo/{Name}Vo.cs
public class AssetBreakDownListVo
{
    public string PartNo { get; set; }
    public string MfrCode { get; set; }
    public string Nomenclature { get; set; }
    public string ClassCode { get; set; }
    public int? Qty { get; set; }
}
```

### 5. Facade Pattern
```csharp
// Location: NextGen.[Module].App/{Feature}/{Name}Facade.cs
public class AssetManagementFacade
{
    public IAssetTransactionRepository AssetTransactionRepository { private get; set; }
    public ICommandBus CommandBus { private get; set; }
    public IModelMapper ModelMapper { private get; set; }

    public IList<AssetVo> GetAssets(long commandId)
    {
        var assets = AssetTransactionRepository.FindByCommandId(commandId);
        return ModelMapper.Map<IList<AssetVo>>(assets);
    }
}
```

### 6. AutoMapper Configuration
```csharp
// Location: NextGen.[Module].App/{Feature}/{Name}Mapper.cs
public class AccessManagementLogMapper : IModelMapper
{
    public void Initialize(AutoMapper.IConfiguration cfg)
    {
        cfg.CreateMap<AccessManagementLog, AccessManagementLogVo>()
           .ForMember(x => x.LogDateTime, opt => opt.MapFrom(s => s.DateTime))
           .ReverseMap();
    }
}
```