from typing import Dict, Iterable, List, Optional

from tools.schemas import RegisteredTool, ToolMetadata


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, RegisteredTool] = {}

    def register(self, metadata: ToolMetadata, handler):
        self._tools[metadata.tool_name] = RegisteredTool(metadata=metadata, handler=handler)
        return metadata

    def get(self, tool_name: str) -> Optional[RegisteredTool]:
        return self._tools.get(tool_name)

    def list_tools(self) -> List[ToolMetadata]:
        return [tool.metadata for tool in self._tools.values()]

    def discover(
        self,
        capability_type: Optional[str] = None,
        permissions: Optional[Iterable[str]] = None,
    ) -> List[ToolMetadata]:
        required_permissions = set(permissions or [])
        tools = []
        for tool in self._tools.values():
            metadata = tool.metadata
            if capability_type and metadata.capability_type != capability_type:
                continue
            if required_permissions and not required_permissions.issubset(set(metadata.permissions)):
                continue
            tools.append(metadata)
        return tools


tool_registry = ToolRegistry()
