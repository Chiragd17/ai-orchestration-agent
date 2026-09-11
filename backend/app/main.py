from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="HackerRank Orchestrate Agent API")

# Allow frontend to communicate with backend without CORS errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    task: str

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/agent")
async def run_agent(request: AgentRequest):
    print(f"Received task: {request.task}")
    return {
        "response": "System ready. Awaiting instructions."
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)