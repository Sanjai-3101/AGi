import os
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

@app.route("/agent", methods=["POST"])
def ai_agent_router():
    # 1. Parse the incoming JSON body
    data = request.get_json(silent=True)
    
    # 2. Validate that data exists and contains 'text_command' (similar to Pydantic)
    if not data or "text_command" not in data:
        abort(400, description="Missing 'text_command' in request body")
        
    command = data["text_command"].lower()
    
    # Agentic Intent Routing Logic
    if "youtube" in command and "music" in command:
        return jsonify({
            "action": "open_tab", 
            "url": "https://www.youtube.com/results?search_query=feel+good+music"
        })
    
    elif "gmail" in command or "email" in command:
        return jsonify({
            "action": "open_tab", 
            "url": "https://mail.google.com"
        })
        
    else:
        abort(400, description="Command not recognized by AI Agent")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Flask runs on 127.0.0.1 by default; host="0.0.0.0" makes it externally accessible
    app.run(host="0.0.0.0", port=port)
