from domain_agents.automation_agent import AutomationAgent
from domain_agents.data_agent import DataAgent
from domain_agents.reporting_agent import ReportingAgent
from domain_agents.research_agent import ResearchAgent


class CapabilityRouter:
    def __init__(self):
        self.agents = {
            "data": DataAgent(),
            "reporting": ReportingAgent(),
            "automation": AutomationAgent(),
            "research": ResearchAgent(),
        }

    def select(self, capability: str):
        if capability in {"csv_cleaning", "preprocessing", "eda", "anomaly_detection"}:
            return self.agents["data"]
        if capability in {"dashboard", "pdf", "chart", "report"}:
            return self.agents["reporting"]
        if capability in {"web_retrieval", "summarization", "knowledge_extraction"}:
            return self.agents["research"]
        return self.agents["automation"]


capability_router = CapabilityRouter()

