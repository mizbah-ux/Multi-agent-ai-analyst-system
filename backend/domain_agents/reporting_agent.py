from domain_agents.base import BaseDomainAgent


class ReportingAgent(BaseDomainAgent):
    agent_name = "Reporting Agent"
    permissions = ("tool:reporting", "tool:visualization")

    def visualize(self, file_id: str, task_id=None):
        return self.run_tool("visualization.generate_charts", {"file_id": file_id}, task_id=task_id)

    def report(self, task_id: int, analysis: dict, charts: list, user_request=None):
        return self.run_tool(
            "report.generate_exports",
            {
                "task_id": task_id,
                "analysis": analysis,
                "charts": charts,
                "user_request": user_request,
            },
            task_id=task_id,
        )
