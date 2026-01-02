# Code Style Guide

## Code Quality

- All .cs files must have valid syntax
- Imports must be resolvable
- Type hints are preferred for function signatures

### EntityId example implementation 
```csharp
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