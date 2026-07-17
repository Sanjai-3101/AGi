import os
from flask import Flask, request, jsonify, render_template_string, abort

app = Flask(__name__)

# Complete Full-Stack Frontend (runs entirely in the user's browser)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Voice AI Agent (Full Stack)</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 100px; background: #fafafa; }
        .btn { padding: 15px 30px; font-size: 18px; color: white; background: #ff4b4b; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #e04040; }
        #status { margin-top: 20px; font-weight: bold; color: #333; font-size: 1.2rem; }
        #transcript { margin-top: 10px; color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>Cloud Voice AI Agent</h1>
    <p>Click the button and speak. The browser will handle the microphone!</p>
    <button class="btn" id="micBtn" onclick="startSpeech()">🎤 Start Listening</button>
    <div id="status">Ready</div>
    <div id="transcript"></div>

    <script>
        function startSpeech() {
            const statusDiv = document.getElementById('status');
            const transcriptDiv = document.getElementById('transcript');
            const micBtn = document.getElementById('micBtn');

            // 1. Check for Browser Speech Support
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                statusDiv.innerText = "❌ Speech Recognition not supported in this browser. Try Chrome!";
                statusDiv.style.color = "red";
                return;
            }

            // Create a placeholder tab immediately on click to prevent browser popup blocking
            let newTab = null;

            const recognition = new SpeechRecognition();
            recognition.lang = 'en-US';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onstart = () => {
                statusDiv.innerText = "🔴 Listening... Speak now!";
                statusDiv.style.color = "red";
                transcriptDiv.innerText = "";
                micBtn.disabled = true;
                
                // Open blank tab when the user initiates interaction
                newTab = window.open("about:blank", "_blank");
            };

            recognition.onerror = (event) => {
                statusDiv.innerText = "❌ Error occurred: " + event.error;
                statusDiv.style.color = "red";
                micBtn.disabled = false;
                if (newTab) newTab.close();
            };

            recognition.onend = () => {
                micBtn.disabled = false;
            };

            recognition.onresult = (event) => {
                const speechToText = event.results[0][0].transcript;
                transcriptDiv.innerText = `You said: "${speechToText}"`;
                statusDiv.innerText = "🚀 Processing request...";
                statusDiv.style.color = "orange";

                // 2. Send the captured text straight to our Flask backend route
                fetch('/agent', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text_command: speechToText })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error("Command not recognized by Agent");
                    }
                    return response.json();
                })
                .then(data => {
                    statusDiv.innerText = "🟢 Success!";
                    statusDiv.style.color = "green";
                    
                    if (data.action === "open_tab") {
                        if (newTab) {
                            // Safely navigate the pre-opened tab to the target URL
                            newTab.location.href = data.url;
                        } else {
                            window.open(data.url, '_blank');
                        }
                    } else {
                        if (newTab) newTab.close();
                    }
                })
                .catch(err => {
                    statusDiv.innerText = "❌ Error: " + err.message;
                    statusDiv.style.color = "red";
                    if (newTab) newTab.close();
                });
            };

            // Start recording audio
            recognition.start();
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    """Serves the frontend page to the user's browser."""
    return render_template_string(HTML_TEMPLATE)

@app.route("/agent", methods=["POST"])
def ai_agent_router():
    """Agent Routing Logic backend."""
    data = request.get_json(silent=True)
    
    if not data or "text_command" not in data:
        abort(400, description="Missing 'text_command' in request body")
        
    command = data["text_command"].lower()
    
    # 1. Flexible YouTube matching
    if "youtube" in command:
        if "music" in command:
            return jsonify({
                "action": "open_tab", 
                "url": "https://www.youtube.com/results?search_query=feel+good+music"
            })
        else:
            return jsonify({
                "action": "open_tab", 
                "url": "https://www.youtube.com"
            })
    
    # 2. Gmail / Email matching
    elif "gmail" in command or "email" in command:
        return jsonify({
            "action": "open_tab", 
            "url": "https://mail.google.com"
        })
        
    else:
        abort(400, description="Command not recognized by AI Agent")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
