from domain_agents.base import BaseDomainAgent


class DataAgent(BaseDomainAgent):
    agent_name = "Data Agent"
    permissions = ("tool:data", "tool:analysis")

    def clean(self, file_id: str, task_id=None):
        return self.run_tool("data.clean_csv", {"file_id": file_id}, task_id=task_id)
