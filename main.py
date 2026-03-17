import json
import webbrowser
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from groq import AsyncGroq
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# ADD THIS: Allows your frontend to talk to your backend safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

app.mount("/static", StaticFiles(directory="static"), name="static")

SYSTEM_PROMPT = """
ROLE:
You are "Aura," an elite, world-class private tutor. You are standing at a large digital whiteboard. You architect "Lightbulb Moments" with extreme efficiency.

THE AURA PERSONA:
- BRAIN: Deep expertise, mentor-level clarity.
- VOICE: Warm, conversational, and ultra-concise. Use human fillers sparingly (e.g., "Right," "So," "Check this out").
- VIBE: A high-energy peer-mentor who values the student's time.

WHITEBOARD ARCHITECTURE (whiteboard_text):
- VISUAL ANCHORS: Use the board for the "Heavy Lifting." Use ## for headers and > for "Pro-Tips."
- CLEANLINESS: Use bullet points and $LaTeX$ for all math/science. 
- FORMATTING: Strict Markdown. The board should be a "Cheat Sheet" of the concept.

SPOKEN NARRATIVE (voice_script):
- THE 3-SENTENCE RULE: Aim for absolute brevity. Explain the "Why," reference the board, and ask a question. 
- SPATIAL REFERENCE: Briefly point to the board: "Notice the formula at the top," or "I've listed the three steps here."
- NO FLUFF: Skip introductory phrases like "I would be happy to explain..." or "Let's dive into the world of..."
- RAPID PACING: Use punchy, short sentences. If it takes more than 20 seconds to read, it's too long.
- THE MIC-DROP: Always end with a sharp, engaging check-in question.

STRICT LOGIC:
The `voice_script` is the 'Quick Guide'; the `whiteboard_text` is the 'Deep Record'. Do not read the board. Explain the intuition behind what is written as fast as possible.

CRITICAL RULE:
Even for greetings (like 'Hi' or 'Hello'), you MUST use the 'render_whiteboard_and_speak' function. 
Put a friendly welcome message on the whiteboard and say hello in the voice script. 
Never respond with plain text.
"""


# Define the Tool (Function)
tools = [
    {
        "type": "function",
        "function": {
            "name": "render_whiteboard_and_speak",
            "description": "Updates the tutor's whiteboard and provides the spoken explanation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "whiteboard_text": {
                        "type": "string",
                        "description": "The Markdown/LaTeX content to display on the board."
                    },
                    "voice_script": {
                        "type": "string",
                        "description": "The natural, human-like script to be spoken by the tutor."
                    }
                },
                "required": ["whiteboard_text", "voice_script"]
            }
        }
    }
]

@app.get("/")
async def get_index():
    return FileResponse('static/index.html')

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw_data = await websocket.receive_text()
            user_message = json.loads(raw_data)["message"]
            print("user_message:", user_message)

            # If it's just a heartbeat, skip the Groq call
            if user_message == "ping":
                continue

            # Force the model to use the tool
            response = await client.chat.completions.create(
                model=os.getenv("GROQ_MODEL"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "render_whiteboard_and_speak"}},
                stream=False # Function calling is more reliable without streaming for specific UI updates
            )

            # Extract the tool call arguments
            tool_call = response.choices[0].message.tool_calls[0]
            arguments = json.loads(tool_call.function.arguments)
            
            whiteboard_data = arguments.get("whiteboard_text", "")
            voice_data = arguments.get("voice_script", "")

            # Send to Frontend
            print(f"Board Update: {whiteboard_data[:50]}...")
            print(f"Voice Script: {voice_data[:50]}...")

            await websocket.send_json({"type": "whiteboard", "data": whiteboard_data})
            await websocket.send_json({"type": "voice", "data": voice_data})

    except Exception as e:
        print(f"Socket error: {e}")
    finally:
        # Ensure the socket is cleaned up properly
        if not websocket.client_state.name == "DISCONNECTED":
            await websocket.close()


if __name__ == "__main__":
    # Get the port from the environment (Render sets this)
    # Default to 8000 if running locally
    port = int(os.environ.get("PORT", 8000))
    
    # Only open browser if NOT running on a server (local dev)
    if not os.environ.get("RENDER"):
        webbrowser.open(f"http://127.0.0.1:{port}")
        
    uvicorn.run(app, host="0.0.0.0", port=port)
