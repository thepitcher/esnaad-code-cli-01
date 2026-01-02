## Entity Creation Guide

### CRITICAL: When creating a new Entity, you MUST create these files together:

```
1. MAIN ENTITY FILE:                    src/modules/NextGen.[Module]/NextGen.[Module].Core/[Function]/Entity/[EntityName].cs
2. MAP FILE:                            src/modules/NextGen.[Module]/NextGen.[Module].Core/Config/EntityMap/[Function]/[EntityName]Map.cs
3. ID CLASS FILE:                       src/modules/NextGen.Admin/NextGen.Admin.Core/Shared/[Domain]/[Function]/[EntityName]Id.cs
4. ENTITY REPOSITORY INTERFACE FILE     src/modules/NextGen.[Module]/NextGen.[Module].Core/[Function]
5. ENTITY NHIBERNATE REPOSITORY FILE    src/modules/NextGen.[Module]/NextGen.[Module].Core/[Function]/Entity/[EntityName].cs
6. HISTORY FILE                         src/modules/NextGen.[Module]/NextGen.[Module].Core/[Function]/Entity/[History].cs
7. ENTITY REPOSITORY INTERFACE FILE     src/modules/NextGen.[Module]/NextGen.[Module].Core/[Function]
8. ENTITY NHIBERNATE REPOSITORY FILE    src/modules/NextGen.[Module]/NextGen.[Module].Core/[Function]
9. MIGRATION SCRIPT FILE                db/fw/common/V1_[YYYYMMDD]_[HHMM]_1_US_[USER_STORY_NO].sql
```

### Terminology
- **Module**: The top-level project under src/modules (Admin, Logistic, Ammo, Maintenance, Operation, Pmco)
- **Domain**: Module name for shared code (Admin, Logistic, Ammo, etc.)
- **Function**: Business feature/package name (e.g., AmmunitionExercise, AssetManagement, Armament)

### Step-by-Step Checklist

When asked to create a new entity, follow these steps IN ORDER:

- [ ] **Step 1**: Create the ID class in `src/modules/NextGen.Admin/NextGen.Admin.Core/Shared/[Domain]/[Function]/`
- [ ] **Step 2**: Create the Entity class in `src/modules/NextGen.[Module]/NextGen.[Module].Core/[Function]/Entity/`
- [ ] **Step 3**: Create the Map class in `src/modules/NextGen.[Module]/NextGen.[Module].Core/Config/EntityMap/[Function]/`
- [ ] **Step 4**: Create Flyway migration script in `db/fw/sql/common` for the database table
- [ ] **Step 4**: Create Flyway migration script in `db/fw/sql/common` for the database table
- [ ] **Step 4**: Create Flyway migration script in `db/fw/sql/common` for the database table
- [ ] **Step 4**: Create Flyway migration script in `db/fw/sql/common` for the database table
- [ ] **Step 4**: Create Flyway migration script in `db/fw/sql/common` for the database table
- [ ] **Step 9**: Create Flyway migration script in `db/fw/sql/common` for the database table. 
                  The flyway migration script naming follow the pattern V1_[YYYYMMDD]_[HHMM]_1_US_[USER_STORY_NO].sql
                  where YYYYMMDD and HHMM is date time format and USER_STORY_NO is user story number provided by user