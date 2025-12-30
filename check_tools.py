"""Check that all tools are registered properly."""

from esnaad.tools.registry import ToolRegistry

# Initialize registry
ToolRegistry.initialize()

# List all tools
print("Registered Tools:")
print("-" * 50)

for tool in ToolRegistry.get_all():
    print(f"  {tool.name}: {tool.description[:60]}...")

print("-" * 50)
print(f"Total: {len(ToolRegistry.get_all())} tools")

# Check specifically for clarification tool
clarification_tool = ToolRegistry.get("request_clarifications")
if clarification_tool:
    print("\n[OK] request_clarifications tool is registered")
    print(f"     Description: {clarification_tool.description}")
else:
    print("\n[ERROR] request_clarifications tool NOT found!")

# Check for spawn_subtasks tool
spawn_tool = ToolRegistry.get("spawn_subtasks")
if spawn_tool:
    print("\n[OK] spawn_subtasks tool is registered")
else:
    print("\n[ERROR] spawn_subtasks tool NOT found!")
