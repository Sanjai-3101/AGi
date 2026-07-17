import os
import webbrowser
import requests
import speech_recognition as sr
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

RENDER_API_URL = "https://agi-hzja.onrender.com/agent"  # Updated to point directly to /agent

# Simple HTML Interface for a browser-based trigger
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Voice AI Agent Trigger</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 100px; background: #fafafa; }
        .btn { padding: 15px 30px; font-size: 18px; color: white; background: #ff4b4b; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #e04040; }
        #status { margin-top: 20px; font-weight: bold; color: #333; }
    </style>
</head>
<body>
    <h1>Voice AI Agent</h1>
    <p>Click the button below to trigger your local microphone.</p>
    <button class="btn" onclick="triggerVoice()">🎤 Start Listening</button>
    <div id="status">Ready</div>

    <script>
        function triggerVoice() {
            const statusDiv = document.getElementById('status');
            statusDiv.innerText = "🔴 Listening... Speak into your microphone.";
            statusDiv.style.color = "red";
            
            fetch('/trigger', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    statusDiv.style.color = "green";
                    statusDiv.innerText = data.message || data.error;
                })
                .catch(err => {
                    statusDiv.style.color = "red";
                    statusDiv.innerText = "Error calling local server.";
                });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    """Serves a simple web page to interactively trigger the mic."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/trigger", methods=["POST"])
def listen_and_execute():
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print("\n🔴 Listening... State your command")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
        print("🔄 Transcribing voice...")
        user_command = recognizer.recognize_google(audio)
        print(f"🎤 You said: \"{user_command}\"")
        
        # Send text to Render AI Agent
        print("🚀 Sending to Render AI Agent...")
        response = requests.post(RENDER_API_URL, json={"text_command": user_command})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("action") == "open_tab":
                target_url = data.get("url")
                print(f"🎯 Agent Directive Received! Opening: {target_url}")
                
                # Open a physical new tab on YOUR local system where this Flask app runs
                webbrowser.open_new_tab(target_url)
                return jsonify({
                    "status": "success", 
                    "command_heard": user_command, 
                    "message": f"Opened tab: {target_url}"
                })
            
            return jsonify({"status": "no_action", "command_heard": user_command, "message": "No action required."})
        
        else:
            return jsonify({"status": "error", "error": "Agent couldn't process this command."}), 400
            
    except sr.WaitTimeoutError:
        return jsonify({"status": "error", "error": "Listening timed out. No speech detected."}), 400
    except sr.UnknownValueError:
        return jsonify({"status": "error", "error": "Could not understand the audio."}), 400
    except Exception as e:
        return jsonify({"status": "error", "error": f"Error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    # Standard Flask development server setup running locally
    port = int(os.environ.get("PORT", 5001)) # Using 5001 so it doesn't conflict with your agent
    app.run(host="127.0.0.1", port=port, debug=True)
