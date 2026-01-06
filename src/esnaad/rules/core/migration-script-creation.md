# Migration Script Creation Rules

## When to Create a Migration Script

**Trigger:** When user requests to create a database migration script for an entity with patterns like:
- "Create migration script for [EntityName]"
- "Generate SQL migration for [EntityName] entity"
- "Create database table for [EntityName]"
- "Add migration for [EntityName] in [Domain]"

**You MUST follow the complete workflow below.**

---

## Step-by-Step Workflow

### Step 1: Read the Entity File and Gather Migration Info

**ALWAYS read the entity C# file first** to understand:
- Entity properties and their types
- Whether entity implements `INgAuditable`
- Entity namespace to determine domain and module
- Property constraints (nullable, required, etc.)

**Example:**
```bash
read_file("src/modules/NextGen.Logistic/NextGen.Logistic.Core/Master/Entity/UnitOfMeasure.cs")
```

**Then, gather file naming information from user (if not already provided):**
- User ID (default: `XXXX` if not provided)
- User Story Number (default: `US_XXXX` if not provided) OR Bug Number (default: `BUG_XXXX` if not provided)
- Current date and time for file naming

**Note:** If user hasn't provided USER_ID, USER_STORY_NO, or BUG_NO in their request, use the defaults. Do NOT prompt the user unless they specifically ask.

### Step 2: Determine Domain Code

Map the domain from entity namespace to 3-letter domain code:

| Domain Name | Domain Code | Namespace Pattern |
|-------------|-------------|-------------------|
| Admin | ADM | NextGen.Admin.Core |
| Logistic | LOG | NextGen.Logistic.Core |
| Ammo | AMM | NextGen.Ammo.Core |
| Maintenance | MNT | NextGen.Maintenance.Core |
| Operation | OPS | NextGen.Operation.Core |
| Budget | BGT | NextGen.Budget.Core |
| Vehicle | VEH | NextGen.Vehicle.Core |
| Pmco | COE | NextGen.Pmco.Core |
| Dashboard | DAS | NextGen.Dashboard.Core |
| Eis | EIS | NextGen.Eis.Core |

**Example:**
- Namespace: `NextGen.Logistic.Core.Master.Entity`
- Domain Code: **LOG**

### Step 3: Determine Table Names

**Master Table:** `[DOMAIN_CODE]_MST_[ENTITY_NAME_UPPERCASE]`
**History Table:** `[DOMAIN_CODE]_HST_[ENTITY_NAME_UPPERCASE]`

**Entity Name to Table Name Conversion:**
- Convert PascalCase to UPPER_SNAKE_CASE
- Insert underscore before each uppercase letter (except first)
- Examples:
  - `UnitOfMeasure` → `UNIT_OF_MEASURE`
  - `WeightBalance` → `WEIGHT_BALANCE`
  - `MasterEquipment` → `MASTER_EQUIPMENT`
  - `D161Master` → `D161_MASTER`

**Example:**
- Entity: `UnitOfMeasure`
- Domain: `Logistic` (LOG)
- Master Table: `LOG_MST_UNIT_OF_MEASURE`
- History Table: `LOG_HST_UNIT_OF_MEASURE`

### Step 4: Map Entity Properties to Table Columns

**Column Naming Convention:**
- All column names in UPPERCASE with underscores
- All column names end with underscore `_`
- Property name converted to UPPER_SNAKE_CASE with trailing `_`

**Examples:**
- `Code` → `CODE_`
- `Name` → `NAME_`
- `IsBase` → `IS_BASE_`
- `Category` → `CATEGORY_`
- `CreatedDate` → `CREATED_DATE_`

---

## Data Type Mapping

Map C# types to SQL Server types:

| C# Type | SQL Server Type | Collation | Nullable | Notes |
|---------|----------------|-----------|----------|-------|
| `string` (Code) | `nvarchar(50)` | `Arabic_CI_AS` | NOT NULL | Standard code field |
| `string` (Name) | `nvarchar(100)` | `Arabic_CI_AS` | NOT NULL | Standard name field |
| `string` (Description) | `nvarchar(max)` | `Arabic_CI_AS` | NULL | Long text |
| `string` (general) | `nvarchar(255)` | `Arabic_CI_AS` | NULL | Default string |
| `bool` | `bit` | - | NOT NULL | Boolean flag |
| `int` | `int` | - | NOT NULL | Integer |
| `long` / `bigint` | `bigint` | - | NOT NULL | Large number |
| `decimal` | `decimal(18,2)` | - | NOT NULL | Currency/precision |
| `DateTime` | `datetime` | - | NULL | Date and time |
| `Guid` | `uniqueidentifier` | - | NOT NULL | GUID/UUID |
| EntityId (e.g., `UnitOfMeasureId`) | `uniqueidentifier` | - | NOT NULL | Strongly-typed ID |
| Enum (e.g., `UnitOfMeasureCategory`) | `nvarchar(100)` | `Arabic_CI_AS` | NULL | Enum as string |
| Entity Reference | `uniqueidentifier` | - | NULL | Foreign key |
| `NgAuditEntry` | (See audit columns below) | - | - | Expands to multiple columns |

**Important Notes:**
- All `string` columns MUST use `COLLATE Arabic_CI_AS` (case-insensitive Arabic collation)
- Code fields default to `nvarchar(50)`
- Name fields default to `nvarchar(100)`
- Description/Remarks fields use `nvarchar(max)`
- Enum types stored as `nvarchar(100)` with enum value name

---

## Standard Columns (Every Table)

**Every master table MUST have these columns:**

```sql
[ID_] [uniqueidentifier] NOT NULL,
[VERSION_] [bigint] NOT NULL,
```

- `ID_`: Primary key (maps to entity `Id` property)
- `VERSION_`: Optimistic locking version (inherited from `EntityBase`)

---

## Audit Columns (INgAuditable Interface)

**If entity implements `INgAuditable`, add these columns:**

```sql
[CREATED_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
[PID_CREATED_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
[FULL_NAME_CREATED_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
[CREATED_ON_] [datetime] NULL,
[MOD_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
[PID_MOD_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
[FULL_NAME_MOD_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
[MOD_ON_] [datetime] NULL,
[TERM_] [nvarchar](255) COLLATE Arabic_CI_AS NULL
```

**These map to the `NgAuditEntry` property in the entity.**

---

## Master Table Structure

### Complete Template

```sql
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[{DOMAIN_CODE}_MST_{ENTITY_NAME}](
    [ID_] [uniqueidentifier] NOT NULL,
    [VERSION_] [bigint] NOT NULL,
    -- Entity-specific columns here
    [CODE_] [nvarchar](50) COLLATE Arabic_CI_AS NOT NULL,
    [NAME_] [nvarchar](100) COLLATE Arabic_CI_AS NOT NULL,
    -- Add other properties as columns
    -- Audit columns (if INgAuditable)
    [CREATED_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [PID_CREATED_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [FULL_NAME_CREATED_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [CREATED_ON_] [datetime] NULL,
    [MOD_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [PID_MOD_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [FULL_NAME_MOD_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [MOD_ON_] [datetime] NULL,
    [TERM_] [nvarchar](255) COLLATE Arabic_CI_AS NULL
PRIMARY KEY CLUSTERED
(
    [ID_] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
```

### Primary Key (Always Required)

```sql
PRIMARY KEY CLUSTERED
(
    [ID_] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
```

**Every table has clustered primary key on `ID_` column.**

### Unique Index on Code (If Entity Has Code Property)

**If entity has `Code` property, create unique index:**

```sql
CREATE UNIQUE NONCLUSTERED INDEX [UQ_{DOMAIN_CODE}_MST_{ENTITY_NAME}_CODE_] ON [dbo].[{DOMAIN_CODE}_MST_{ENTITY_NAME}]
(
    [CODE_] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
GO
```

**Index Name Pattern:** `UQ_{TABLE_NAME}_CODE_`

---

## History Table Structure

**History tables track all changes to master table records.**

### Complete Template

```sql
CREATE TABLE [dbo].[{DOMAIN_CODE}_HST_{ENTITY_NAME}](
    [ID_] [uniqueidentifier] NOT NULL,
    [VERSION_] [bigint] NOT NULL,
    [TRN_ID_] [uniqueidentifier] NOT NULL,
    [ACTION_] [nvarchar](255) NOT NULL,
    [FIELD_NAME_] [nvarchar](255) NULL,
    [FROM_VALUE_] [nvarchar](255) NULL,
    [TO_VALUE_] [nvarchar](255) NULL,
    [REMARKS_] [nvarchar](max) NULL,
    [CREATED_BY_] [nvarchar](255) NULL,
    [PID_CREATED_BY_] [nvarchar](255) NULL,
    [FULL_NAME_CREATED_BY_] [nvarchar](255) NULL,
    [CREATED_ON_] [datetime] NULL,
    [MOD_BY_] [nvarchar](255) NULL,
    [PID_MOD_BY_] [nvarchar](255) NULL,
    [FULL_NAME_MOD_BY_] [nvarchar](255) NULL,
    [MOD_ON_] [datetime] NULL,
    [TERM_] [nvarchar](255) NULL,
PRIMARY KEY CLUSTERED
(
    [ID_] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
```

### History Table Columns (Fixed Structure)

**History tables have FIXED structure regardless of entity:**

- `ID_`: Unique ID for this history record (not the entity ID)
- `VERSION_`: Version number
- `TRN_ID_`: Transaction ID linking to master table `ID_`
- `ACTION_`: Action type (INSERT, UPDATE, DELETE)
- `FIELD_NAME_`: Name of field that changed
- `FROM_VALUE_`: Previous value (as string)
- `TO_VALUE_`: New value (as string)
- `REMARKS_`: Additional notes
- All audit columns (same as master table)

**Important:** History table structure is the SAME for all entities. Do not add entity-specific columns.

---

## Complete Example: UnitOfMeasure

### Entity Analysis

**File:** `NextGen.Logistic.Core/Master/Entity/UnitOfMeasure.cs`

**Properties:**
- `Id` (UnitOfMeasureId) - EntityBase
- `Version` (long) - EntityBase (implicit)
- `AuditEntry` (NgAuditEntry) - INgAuditable
- `Code` (string)
- `Name` (string)
- `Category` (UnitOfMeasureCategory - enum)
- `IsBase` (bool)

**Namespace:** `NextGen.Logistic.Core.Master.Entity`
**Domain Code:** LOG

### Generated Migration Script

```sql
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[LOG_MST_UNIT_OF_MEASURE](
    [ID_] [uniqueidentifier] NOT NULL,
    [VERSION_] [bigint] NOT NULL,
    [CODE_] [nvarchar](50) COLLATE Arabic_CI_AS NOT NULL,
    [NAME_] [nvarchar](100) COLLATE Arabic_CI_AS NOT NULL,
    [IS_BASE_] [bit] NOT NULL,
    [CATEGORY_] [nvarchar](100) COLLATE Arabic_CI_AS NULL,
    [CREATED_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [PID_CREATED_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [FULL_NAME_CREATED_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [CREATED_ON_] [datetime] NULL,
    [MOD_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [PID_MOD_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [FULL_NAME_MOD_BY_] [nvarchar](255) COLLATE Arabic_CI_AS NULL,
    [MOD_ON_] [datetime] NULL,
    [TERM_] [nvarchar](255) COLLATE Arabic_CI_AS NULL
PRIMARY KEY CLUSTERED
(
    [ID_] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
CREATE UNIQUE NONCLUSTERED INDEX [UQ_LOG_MST_UNIT_OF_MEASURE_CODE_] ON [dbo].[LOG_MST_UNIT_OF_MEASURE]
(
    [CODE_] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
GO


CREATE TABLE [dbo].[LOG_HST_UNIT_OF_MEASURE](
    [ID_] [uniqueidentifier] NOT NULL,
    [VERSION_] [bigint] NOT NULL,
    [TRN_ID_] [uniqueidentifier] NOT NULL,
    [ACTION_] [nvarchar](255) NOT NULL,
    [FIELD_NAME_] [nvarchar](255) NULL,
    [FROM_VALUE_] [nvarchar](255) NULL,
    [TO_VALUE_] [nvarchar](255) NULL,
    [REMARKS_] [nvarchar](max) NULL,
    [CREATED_BY_] [nvarchar](255) NULL,
    [PID_CREATED_BY_] [nvarchar](255) NULL,
    [FULL_NAME_CREATED_BY_] [nvarchar](255) NULL,
    [CREATED_ON_] [datetime] NULL,
    [MOD_BY_] [nvarchar](255) NULL,
    [PID_MOD_BY_] [nvarchar](255) NULL,
    [FULL_NAME_MOD_BY_] [nvarchar](255) NULL,
    [MOD_ON_] [datetime] NULL,
    [TERM_] [nvarchar](255) NULL,
PRIMARY KEY CLUSTERED
(
    [ID_] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
```

---

## Migration Script File Naming and Location

**Default Location:** `db/fw/common`

**Flyway Naming Pattern:** `V1_[YYYYMMDD]_[HHMM]_[USER_ID]__[USER_STORY_NO or BUG_NO]_[SHORT_DESC].sql`

**Components:**
- `V1_` - Flyway version prefix (always V1_)
- `[YYYYMMDD]` - Date when script created (e.g., 20260106)
- `[HHMM]` - Time when script created in 24h format (e.g., 1430)
- `[USER_ID]` - User ID (use `XXXX` if not provided)
- `__` - Double underscore separator
- `[USER_STORY_NO]` - User story number (use `US_XXXX` if not provided)
- `[BUG_NO]` - Bug number (use `BUG_XXXX` if not provided, or omit if user story provided)
- `[SHORT_DESC]` - Short description (e.g., UnitOfMeasure_Table)

**Examples:**
- User provides all info: `V1_20260106_1430_GAL7634__US_12345_UnitOfMeasure_Table.sql`
- User provides user story: `V1_20260106_1430_GAL7634__US_12345_UnitOfMeasure_Table.sql`
- User provides bug number: `V1_20260106_1430_GAL7634__BUG_67890_UnitOfMeasure_Table.sql`
- No user info provided: `V1_20260106_1430_XXXX__US_XXXX_UnitOfMeasure_Table.sql`
- With bug instead of US: `V1_20260106_1430_XXXX__BUG_XXXX_UnitOfMeasure_Table.sql`

**Short Description Format:**
- Use entity name + "_Table" (e.g., `UnitOfMeasure_Table`, `WeightBalance_Table`)
- Keep it concise and descriptive

---

## Property Handling Special Cases

### Entity References (Foreign Keys)

**If property is an Entity reference** (e.g., `public virtual Platform Platform { get; protected set; }`):
- Column name: `[PLATFORM_ID_]` (add `_ID_` suffix)
- SQL Type: `uniqueidentifier NULL`
- This is a foreign key to the referenced entity's `ID_` column

**Example:**
```csharp
public virtual Platform Platform { get; protected set; }
```
**Becomes:**
```sql
[PLATFORM_ID_] [uniqueidentifier] NULL,
```

### EntityId Properties (ID-only references)

**If property is an EntityId** (e.g., `public virtual DataRestrictionId CommandId { get; set; }`):
- Property already ends with `Id`
- Column name: Convert property name to UPPER_SNAKE_CASE (e.g., `COMMAND_ID_`)
- SQL Type: `uniqueidentifier NULL` (or NOT NULL if required)

**Example:**
```csharp
public virtual DataRestrictionId CommandId { get; set; }
```
**Becomes:**
```sql
[COMMAND_ID_] [uniqueidentifier] NULL,
```

### Collection Properties (One-to-Many)

**Do NOT create columns for collection properties:**
```csharp
public virtual IList<EquipmentItem> Items { get; protected set; }
```
**No column created** - this is a navigation property managed by NHibernate

---

## Column Ordering

**Order columns in migration script as follows:**

1. **Standard columns** (ID_, VERSION_)
2. **Business columns** (CODE_, NAME_, other entity properties in declaration order)
3. **Audit columns** (CREATED_BY_, PID_CREATED_BY_, ..., TERM_)

**Do not alphabetize** - preserve entity property declaration order.

---

## Quick Reference: Migration Creation Checklist

**Before Writing:**
1. ✅ Read entity C# file to understand properties
2. ✅ Identify domain code from namespace
3. ✅ Determine master and history table names
4. ✅ Check if entity implements INgAuditable

**Master Table:**
5. ✅ Add standard columns (ID_, VERSION_)
6. ✅ Map each entity property to SQL column (correct type and collation)
7. ✅ Add audit columns if INgAuditable
8. ✅ Create PRIMARY KEY CLUSTERED on ID_
9. ✅ Create UNIQUE INDEX on CODE_ (if Code property exists)
10. ✅ Verify all string columns have COLLATE Arabic_CI_AS
11. ✅ Verify all column names end with underscore _

**History Table:**
12. ✅ Use fixed history table structure (do not customize)
13. ✅ Include all audit columns
14. ✅ Use TEXTIMAGE_ON [PRIMARY] for nvarchar(max) columns

**File:**
15. ✅ Create file in `db/fw/common` directory
16. ✅ Use Flyway naming: `V1_[YYYYMMDD]_[HHMM]_[USER_ID]__[USER_STORY_NO]_[SHORT_DESC].sql`
17. ✅ Use defaults if not provided: XXXX for USER_ID, US_XXXX for USER_STORY_NO
18. ✅ Include both master and history table in same file
19. ✅ Separate master and history with blank lines and GO statements

---

## Common Mistakes to Avoid

❌ **Wrong:** Forgetting trailing underscore on column names (`CODE` instead of `CODE_`)
✅ **Correct:** All column names end with `_`

❌ **Wrong:** Missing collation on string columns
✅ **Correct:** All `nvarchar` columns have `COLLATE Arabic_CI_AS`

❌ **Wrong:** Adding entity-specific columns to history table
✅ **Correct:** History table has fixed structure (same for all entities)

❌ **Wrong:** Using lowercase or mixed case in table/column names
✅ **Correct:** All table and column names in UPPERCASE

❌ **Wrong:** Creating foreign key constraints
✅ **Correct:** No foreign key constraints (NHibernate manages relationships)

❌ **Wrong:** Using wrong data types (e.g., `varchar` instead of `nvarchar`)
✅ **Correct:** Use exact data type mappings from table above

❌ **Wrong:** Missing unique index on CODE_ column
✅ **Correct:** Always create unique index if entity has Code property

---

## Code Formatting

**CRITICAL:** Follow proper SQL formatting:
- Use consistent indentation (4 spaces)
- One column definition per line
- Align data types and constraints
- Add GO statements between table creation and index creation
- Use single newlines between sections (no double newlines)
