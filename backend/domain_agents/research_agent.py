from domain_agents.base import BaseDomainAgent


class ResearchAgent(BaseDomainAgent):
    agent_name = "Research Agent"
    permissions = ("tool:retrieval",)

    def retrieve(self, query: str, namespace=None, limit: int = 5, task_id=None):
        return self.run_tool(
            "memory.semantic_search",
            {"query": query, "namespace": namespace, "limit": limit},
            task_id=task_id,
        )
