from pydantic import BaseModel, Field
from config import AGENT_NAMES, AGENT_DESCRIPTIONS

_NEXT_AGENT_DESCRIPTION = "The next agent to run. One of:\n" + "\n".join(
    f"- {name}: {description}" for name, description in AGENT_DESCRIPTIONS.items()
)

class OrchestratorDecision(BaseModel):
    """You have to choose the next agent"""
    next_agent: AGENT_NAMES = Field(description=_NEXT_AGENT_DESCRIPTION)