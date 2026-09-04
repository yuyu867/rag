from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_input: str
    image_base64: str | None
    intent: dict
    bmi_result: str | None
    knowledge_results: list[str]
    food_analysis: str | None
    final_response: str
