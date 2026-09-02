from pydantic import BaseModel, Field
from agent.config import AGENT_NAMES, AGENT_DESCRIPTIONS

_NEXT_AGENT_DESCRIPTION = "The next agent to run. One of:\n" + "\n".join(
    f"- {name}: {description}" for name, description in AGENT_DESCRIPTIONS.items()
)

class OrchestratorDecision(BaseModel):
    """You have to choose the next agent"""
    next_agent: AGENT_NAMES = Field(description=_NEXT_AGENT_DESCRIPTION)
    agent_prompt: str = Field(
        default="",
        description=(
            "Optional extra instructions or context to hand to the chosen agent for "
            "this run only (e.g. narrow the search, focus on a specific angle). "
            "Leave empty if the agent's default behavior is sufficient."
        ),
    )