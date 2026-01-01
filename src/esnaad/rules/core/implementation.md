### Entity example implementation 
```csharp
// Location: src/modules/NextGen.[Domain]/NextGen.[Domain].Core/[Module]/Entity/UnitOfMeasure.cs
using System;
using NextGen.Admin.Core.Entity;
using NextGen.Admin.Core.Master.Entity;
using NextGen.Admin.Core.Shared.Logistic.Master;
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

### EntityId example implementation 
```csharp
// Location: src/modules/NextGen.Admin/NextGen.Admin.Core/Shared/Logistic/Master/UnitOfMeasureId.cs
using System;
using NextGen.Support.Base.Entity;

namespace NextGen.Admin.Core.Shared.Logistic.Master
{
    public class UnitOfMeasureId : ComponentId<Guid?>
    {
        protected UnitOfMeasureId()
        {
        }

        public static UnitOfMeasureId Of(Guid? value)
        {
            return new UnitOfMeasureId { Value = value };
        }
    }
}


```