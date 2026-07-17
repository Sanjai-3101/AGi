import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class CommandRequest(BaseModel):
    text_command: str

@app.post("/agent")
async def ai_agent_router(request: CommandRequest):
    command = request.text_command.lower()
    
    # Agentic Intent Routing Logic
    if "youtube" in command and "music" in command:
        return {"action": "open_tab", "url": "https://www.youtube.com/results?search_query=feel+good+music"}
    
    elif "gmail" in command or "email" in command:
        return {"action": "open_tab", "url": "https://mail.google.com"}
        
    else:
        raise HTTPException(status_code=400, detail="Command not recognized by AI Agent")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
