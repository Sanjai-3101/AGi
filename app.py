import os
import urllib.parse
from flask import Flask, request, jsonify, render_template_string, abort

app = Flask(__name__)

# Complete Full-Stack Frontend (runs entirely in the user's browser)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Universal Voice AI Agent (Full Stack)</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 100px; background: #fafafa; }
        .btn { padding: 15px 30px; font-size: 18px; color: white; background: #4CAF50; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #45a049; }
        #status { margin-top: 20px; font-weight: bold; color: #333; font-size: 1.2rem; }
        #transcript { margin-top: 10px; color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>Cloud Universal Voice AI Agent</h1>
    <p>Click the button and speak. (e.g., "Open Amazon and search for torch light", "Open Gmail and search for receipt")</p>
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
                
                // Open blank tab when the user initiates interaction to bypass popup blockers
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
    """Universal Agent Routing Logic backend."""
    data = request.get_json(silent=True)
    
    if not data or "text_command" not in data:
        abort(400, description="Missing 'text_command' in request body")
        
    command = data["text_command"].strip().lower()
    
    # 1. Map apps to their respective search configurations and fallback URLs
    # {app_key: (search_url_template, fallback_url)}
    APP_MAPPING = {
        "youtube": ("https://www.youtube.com/results?search_query={query}", "https://www.youtube.com"),
        "amazon": ("https://www.amazon.com/s?k={query}", "https://www.amazon.com"),
        "gmail": ("https://mail.google.com/mail/u/0/#search/{query}", "https://mail.google.com"),
        "email": ("https://mail.google.com/mail/u/0/#search/{query}", "https://mail.google.com"),
        "netflix": ("https://www.netflix.com/search?q={query}", "https://www.netflix.com"),
        "spotify": ("https://open.spotify.com/search/{query}", "https://open.spotify.com"),
        "google": ("https://www.google.com/search?q={query}", "https://www.google.com"),
        "wikipedia": ("https://en.wikipedia.org/wiki/Special:Search?search={query}", "https://en.wikipedia.org"),
        "github": ("https://github.com/search?q={query}", "https://github.com"),
        "twitter": ("https://x.com/search?q={query}", "https://x.com"),
        "x": ("https://x.com/search?q={query}", "https://x.com"),
    }

    # Common voice pattern triggers to extract search terms
    triggers = ["search for", "search", "find", "look up"]
    
    # 2. Check which app is requested in the command
    for app_name, (search_template, fallback_url) in APP_MAPPING.items():
        if app_name in command:
            search_query = None
            
            # Look for triggers *after* or *before* the app name to extract what to search
            for trigger in triggers:
                if trigger in command:
                    parts = command.split(trigger, 1)
                    if len(parts) > 1 and parts[1].strip():
                        # Extract query and strip out fluff words like "in amazon" or "on netflix" if they linger
                        raw_query = parts[1].strip()
                        raw_query = raw_query.replace(f"in {app_name}", "").replace(f"on {app_name}", "").strip()
                        if raw_query:
                            search_query = raw_query
                            break
            
            # Fallback parsing strategy if no trigger word was matched (e.g. "open amazon torch light")
            if not search_query:
                # Remove the app name and "open" / "and" words to guess the query
                cleaned = command.replace("open", "").replace("and", "").replace(app_name, "").strip()
                if cleaned:
                    search_query = cleaned

            if search_query:
                encoded_query = urllib.parse.quote_plus(search_query)
                target_url = search_template.format(query=encoded_query)
            else:
                target_url = fallback_url
                
            return jsonify({
                "action": "open_tab", 
                "url": target_url
            })
            
    # 3. Ultimate Fallback (if no registered app is detected, Google Search the whole command)
    encoded_command = urllib.parse.quote_plus(command)
    return jsonify({
        "action": "open_tab",
        "url": f"https://www.google.com/search?q={encoded_command}"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
