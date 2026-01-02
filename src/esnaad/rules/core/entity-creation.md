### Entity Creation example 

When creating an entity, used this example and follow the pattern
```csharp
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