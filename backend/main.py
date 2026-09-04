import os
import base64
import json
import asyncio
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agent.graph import create_agent
from agent.state import AgentState
from langchain_core.messages import HumanMessage

app = FastAPI(title="AI 智能营养师")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = create_agent()


class ChatRequest(BaseModel):
    text: str
    image_base64: str | None = None


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "AI营养师"}


@app.post("/api/chat/upload")
async def upload_image(file: UploadFile = File(...)):
    content = await file.read()
    encoded = base64.b64encode(content).decode("utf-8")
    return {"image_base64": encoded}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    initial_state: AgentState = {
        "messages": [HumanMessage(content=request.text)],
        "user_input": request.text,
        "image_base64": request.image_base64,
        "intent": {},
        "bmi_result": None,
        "knowledge_results": [],
        "food_analysis": None,
        "final_response": "",
    }

    async def event_stream():
        for event in agent.stream(initial_state, stream_mode="values"):
            final = event.get("final_response", "")
            if final:
                yield {"data": final}
                break

    return EventSourceResponse(event_stream())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
