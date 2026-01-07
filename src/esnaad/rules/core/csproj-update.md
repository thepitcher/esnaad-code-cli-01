# .csproj File Update Rules

**CRITICAL**: Whenever you create or generate a `.cs` file in the project, you MUST automatically update the corresponding `.csproj` file to include that file in the project.

---

## When to Update .csproj (MANDATORY)

Update the .csproj file IMMEDIATELY after creating ANY of these file types:

1. **Entity ID class** (`[EntityName]Id.cs`)
2. **Entity class** (`[EntityName].cs`)
3. **Entity map class** (`[EntityName]Map.cs`)
4. **Repository interface** (`I[EntityName]Repository.cs`)
5. **Repository implementation** (`Nh[EntityName]Repository.cs`)
6. **Any other .cs file** created in NextGen modules

**Exception**: Do NOT update .csproj for files created outside `src\modules\NextGen.*` directories.

---

## Workflow: Update .csproj After Creating .cs File

### Step 1: Identify the .csproj File Location

After creating a `.cs` file, locate the corresponding `.csproj` file using this pattern:

**Pattern**: `src\modules\NextGen.[Domain]\NextGen.[Domain].Core\NextGen.[Domain].Core.csproj`

**Examples**:
- Created: `src\modules\NextGen.Logistic\NextGen.Logistic.Core\AssetManagement\Entity\Pbo.cs`
- .csproj: `src\modules\NextGen.Logistic\NextGen.Logistic.Core\NextGen.Logistic.Core.csproj`

- Created: `src\modules\NextGen.Admin\NextGen.Admin.Core\Config\EntityMap\System\UserMap.cs`
- .csproj: `src\modules\NextGen.Admin\NextGen.Admin.Core\NextGen.Admin.Core.csproj`

### Step 2: Calculate Relative Path

The `Include` attribute in the .csproj must contain the **relative path from the .csproj directory** to the .cs file.

**Formula**: Remove the .csproj directory path from the full .cs file path.

**Examples**:

| Full .cs File Path | .csproj Directory | Relative Path (Include) |
|--------------------|-------------------|-------------------------|
| `src\modules\NextGen.Logistic\NextGen.Logistic.Core\AssetManagement\Entity\Pbo.cs` | `src\modules\NextGen.Logistic\NextGen.Logistic.Core\` | `AssetManagement\Entity\Pbo.cs` |
| `src\modules\NextGen.Logistic\NextGen.Logistic.Core\AssetManagement\Entity\PboId.cs` | `src\modules\NextGen.Logistic\NextGen.Logistic.Core\` | `AssetManagement\Entity\PboId.cs` |
| `src\modules\NextGen.Logistic\NextGen.Logistic.Core\Config\EntityMap\AssetManagement\PboMap.cs` | `src\modules\NextGen.Logistic\NextGen.Logistic.Core\` | `Config\EntityMap\AssetManagement\PboMap.cs` |
| `src\modules\NextGen.Logistic\NextGen.Logistic.Core\AssetManagement\Repository\IPboRepository.cs` | `src\modules\NextGen.Logistic\NextGen.Logistic.Core\` | `AssetManagement\Repository\IPboRepository.cs` |
| `src\modules\NextGen.Logistic\NextGen.Logistic.Core\AssetManagement\Repository\NHibernate\NhPboRepository.cs` | `src\modules\NextGen.Logistic\NextGen.Logistic.Core\` | `AssetManagement\Repository\NHibernate\NhPboRepository.cs` |

**Important**: Use backslashes (`\`) for Windows paths in .csproj files.

### Step 3: Read the Existing .csproj File

Before making changes, read the current .csproj file content:

```xml
<!-- Use read_file tool -->
```

### Step 4: Check for Existing Entry

**CRITICAL**: Before adding a new `<Compile Include="..." />` entry, verify it doesn't already exist in the .csproj file.

Search for the relative path in the .csproj content. If found, SKIP the update.

### Step 5: Locate or Create `<ItemGroup>` for Compile Entries

Find an existing `<ItemGroup>` that contains `<Compile Include="..." />` entries.

**Typical .csproj structure**:

```xml
<Project ToolsVersion="15.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <Import Project="$(MSBuildExtensionsPath)\$(MSBuildToolsVersion)\Microsoft.Common.props" />
  <PropertyGroup>
    <!-- Properties here -->
  </PropertyGroup>
  <ItemGroup>
    <Reference Include="System" />
    <!-- References here -->
  </ItemGroup>
  <ItemGroup>
    <Compile Include="Properties\AssemblyInfo.cs" />
    <Compile Include="AssetManagement\Entity\Pbo.cs" />
    <!-- Other .cs files here -->
  </ItemGroup>
  <Import Project="$(MSBuildToolsPath)\Microsoft.CSharp.targets" />
</Project>
```

**If no `<ItemGroup>` with `<Compile>` entries exists**:
- Create a new `<ItemGroup>` section before the final `<Import>` tag

### Step 6: Insert the New Entry

Add the new `<Compile Include="..." />` entry to the ItemGroup.

**Rules for insertion**:
1. Insert alphabetically within the ItemGroup (optional but recommended for organization)
2. Use proper indentation (2 spaces per level)
3. Self-closing tag format: `<Compile Include="..." />`

**Example insertion**:

```xml
<ItemGroup>
  <Compile Include="Properties\AssemblyInfo.cs" />
  <Compile Include="AssetManagement\Entity\Pbo.cs" />
  <Compile Include="AssetManagement\Entity\PboId.cs" />
  <Compile Include="Config\EntityMap\AssetManagement\PboMap.cs" />
</ItemGroup>
```

### Step 7: Write the Updated .csproj File

Use `edit_file` tool to insert the new entry in the correct location.

**Example**:

```
Old text (find this in the .csproj):
  <ItemGroup>
    <Compile Include="Properties\AssemblyInfo.cs" />
  </ItemGroup>

New text (replace with this):
  <ItemGroup>
    <Compile Include="Properties\AssemblyInfo.cs" />
    <Compile Include="AssetManagement\Entity\Pbo.cs" />
  </ItemGroup>
```

---

## Complete Example: Entity Creation

### Scenario

Creating `Pbo` entity in AssetManagement module, Logistic domain.

### Files Created

1. **Entity ID**: `src\modules\NextGen.Logistic\NextGen.Logistic.Core\AssetManagement\Entity\PboId.cs`
2. **Entity**: `src\modules\NextGen.Logistic\NextGen.Logistic.Core\AssetManagement\Entity\Pbo.cs`

### .csproj Updates

**Target .csproj**: `src\modules\NextGen.Logistic\NextGen.Logistic.Core\NextGen.Logistic.Core.csproj`

**Step 1**: Create PboId.cs using `write_file`

**Step 2**: Update .csproj to include PboId.cs

1. Read .csproj using `read_file`
2. Check if `AssetManagement\Entity\PboId.cs` already exists → NOT found
3. Locate `<ItemGroup>` with `<Compile>` entries
4. Insert `<Compile Include="AssetManagement\Entity\PboId.cs" />` using `edit_file`

**Step 3**: Create Pbo.cs using `write_file`

**Step 4**: Update .csproj to include Pbo.cs

1. Read .csproj using `read_file`
2. Check if `AssetManagement\Entity\Pbo.cs` already exists → NOT found
3. Insert `<Compile Include="AssetManagement\Entity\Pbo.cs" />` using `edit_file`

**Final .csproj ItemGroup**:

```xml
<ItemGroup>
  <Compile Include="Properties\AssemblyInfo.cs" />
  <Compile Include="AssetManagement\Entity\Pbo.cs" />
  <Compile Include="AssetManagement\Entity\PboId.cs" />
  <!-- Other files... -->
</ItemGroup>
```

---

## Complete Example: Entity + Map + Repository

### Scenario

Creating complete entity stack for `Pbo` (entity + map + repository).

### Files Created

1. `AssetManagement\Entity\PboId.cs`
2. `AssetManagement\Entity\Pbo.cs`
3. `Config\EntityMap\AssetManagement\PboMap.cs`
4. `AssetManagement\Repository\IPboRepository.cs`
5. `AssetManagement\Repository\NHibernate\NhPboRepository.cs`

### .csproj Updates Required

For EACH file created above, update the .csproj:

```xml
<ItemGroup>
  <Compile Include="Properties\AssemblyInfo.cs" />
  <Compile Include="AssetManagement\Entity\Pbo.cs" />
  <Compile Include="AssetManagement\Entity\PboId.cs" />
  <Compile Include="AssetManagement\Repository\IPboRepository.cs" />
  <Compile Include="AssetManagement\Repository\NHibernate\NhPboRepository.cs" />
  <Compile Include="Config\EntityMap\AssetManagement\PboMap.cs" />
  <!-- Other files... -->
</ItemGroup>
```

---

## Edge Cases and Error Handling

### Case 1: .csproj File Not Found

If the .csproj file doesn't exist at the expected location:

1. Search for `.csproj` files in parent directories using `search_files` tool
2. If still not found, warn the user and skip .csproj update
3. Do NOT fail the entire operation - creating the .cs file is still valid

### Case 2: Duplicate Entry

If the `<Compile Include="..." />` entry already exists:

- **Action**: Skip the update (no-op)
- **Do NOT**: Add duplicate entries or throw errors

### Case 3: Malformed .csproj

If the .csproj file is malformed or doesn't contain `<ItemGroup>`:

1. Create a new `<ItemGroup>` section before the `</Project>` closing tag
2. Insert the new entry there

**Example**:

```xml
<Project ToolsVersion="15.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <!-- Existing content -->

  <ItemGroup>
    <Compile Include="AssetManagement\Entity\Pbo.cs" />
  </ItemGroup>

  <Import Project="$(MSBuildToolsPath)\Microsoft.CSharp.targets" />
</Project>
```

### Case 4: Multiple ItemGroups

If the .csproj has multiple `<ItemGroup>` sections:

- **Action**: Insert into the first `<ItemGroup>` that contains `<Compile>` entries
- **Fallback**: If no `<ItemGroup>` has `<Compile>` entries, insert into the first `<ItemGroup>`

---

## Integration with Other Rules

### Entity Creation

After creating entity ID and entity files (per `entity-creation.md`):

1. Update .csproj to include `[EntityName]Id.cs`
2. Update .csproj to include `[EntityName].cs`

### Entity Map Creation

After creating entity map file (per `entity-map-creation.md`):

1. Update .csproj to include `Config\EntityMap\[Module]\[EntityName]Map.cs`

### Repository Creation

After creating repository interface and implementation (per `repository-creation.md`):

1. Update .csproj to include `[Module]\Repository\I[EntityName]Repository.cs`
2. Update .csproj to include `[Module]\Repository\NHibernate\Nh[EntityName]Repository.cs`

---

## Verification Checklist

After updating .csproj, verify:

- [ ] .csproj file exists at expected location
- [ ] Read .csproj content before editing
- [ ] Checked for duplicate entry (skip if exists)
- [ ] Calculated correct relative path (no absolute paths!)
- [ ] Used backslashes (`\`) for Windows paths
- [ ] Inserted entry in correct `<ItemGroup>`
- [ ] Used proper indentation (2 spaces)
- [ ] Used self-closing tag format: `<Compile Include="..." />`
- [ ] No duplicate entries added
- [ ] .csproj file is still valid XML after edit

---

## Quick Reference: .csproj Update Workflow

```
For EACH .cs file created:

1. Calculate relative path from .csproj directory to .cs file
2. Read existing .csproj content
3. Check if entry already exists → SKIP if yes
4. Find <ItemGroup> with <Compile> entries (or create new one)
5. Insert: <Compile Include="[RelativePath]" />
6. Use edit_file tool to update .csproj
7. Continue with next file
```

---

## Common Mistakes to Avoid

| Mistake | Correct Approach |
|---------|------------------|
| Using absolute path in Include | Use relative path from .csproj directory |
| Using forward slashes (`/`) | Use backslashes (`\`) for Windows paths |
| Adding duplicate entries | Always check if entry exists before adding |
| Forgetting to update .csproj | ALWAYS update after creating .cs file |
| Wrong .csproj location | Use pattern: `src\modules\NextGen.[Domain]\NextGen.[Domain].Core\NextGen.[Domain].Core.csproj` |
| Not reading .csproj first | Always read before editing to check for duplicates |
| Incorrect indentation | Use 2 spaces per level, match existing format |
| Adding to wrong ItemGroup | Find ItemGroup with existing `<Compile>` entries |

---

## Example: Step-by-Step for Pbo Entity

**User Request**: "Create Pbo entity in AssetManagement module, Logistic domain"

**Execution Flow**:

1. **Create PboId.cs**
   - Write file: `src\modules\NextGen.Logistic\NextGen.Logistic.Core\AssetManagement\Entity\PboId.cs`
   - Read .csproj: `src\modules\NextGen.Logistic\NextGen.Logistic.Core\NextGen.Logistic.Core.csproj`
   - Check for duplicate: Search for `AssetManagement\Entity\PboId.cs` → NOT FOUND
   - Edit .csproj: Add `<Compile Include="AssetManagement\Entity\PboId.cs" />`

2. **Create Pbo.cs**
   - Write file: `src\modules\NextGen.Logistic\NextGen.Logistic.Core\AssetManagement\Entity\Pbo.cs`
   - Read .csproj: `src\modules\NextGen.Logistic\NextGen.Logistic.Core\NextGen.Logistic.Core.csproj`
   - Check for duplicate: Search for `AssetManagement\Entity\Pbo.cs` → NOT FOUND
   - Edit .csproj: Add `<Compile Include="AssetManagement\Entity\Pbo.cs" />`

3. **If user chose "Complete" option** (Entity + Map + Repository + Migration):
   - Repeat above steps for PboMap.cs, IPboRepository.cs, NhPboRepository.cs
   - Each file creation followed by .csproj update

**Final result**: 5 .cs files created, 5 .csproj updates performed, project stays in sync.

---

## Summary

**CRITICAL RULE**: Every .cs file creation MUST be immediately followed by a .csproj update.

**Pattern**:
1. Create .cs file using `write_file`
2. Read .csproj using `read_file`
3. Check for duplicate entry
4. Update .csproj using `edit_file` (if not duplicate)
5. Repeat for next file

This ensures the C# project stays in sync and Visual Studio recognizes all new files automatically.
