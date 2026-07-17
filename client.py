import time
import webbrowser
import requests
import speech_recognition as sr

RENDER_API_URL = "https://YOUR_RENDER_URL.onrender.com/agent"

def listen_and_execute():
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("\n🔴 Listening... State your command (e.g., 'Open YouTube and search music')")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
        
    try:
        # 1. Convert Voice to Text locally (No browser security blocks!)
        print("🔄 Transcribing voice...")
        user_command = recognizer.recognize_google(audio)
        print(f"🎤 You said: \"{user_command}\"")
        
        # 2. Send the text to your AI Agent on Render
        print("🚀 Sending to Render AI Agent...")
        response = requests.post(RENDER_API_URL, json={"text_command": user_command})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("action") == "open_tab":
                target_url = data.get("url")
                print(f"🎯 Agent Directive Received! Opening: {target_url}")
                
                # 3. Open a physical new tab on YOUR system
                webbrowser.open_new_tab(target_url)
        else:
            print("❌ Agent couldn't process this command.")
            
    except sr.UnknownValueError:
        print("😢 Could not understand the audio.")
    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    while True:
        listen_and_execute()
        time.sleep(2)
