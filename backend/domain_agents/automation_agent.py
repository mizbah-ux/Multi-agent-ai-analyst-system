from domain_agents.base import BaseDomainAgent


class AutomationAgent(BaseDomainAgent):
    agent_name = "Automation Agent"
    permissions = ("tool:data", "tool:analysis", "tool:visualization", "tool:reporting")

    def route(self, tool_name: str, payload: dict, task_id=None):
        return self.run_tool(tool_name, payload, task_id=task_id)
