import json
import webbrowser
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from groq import AsyncGroq
import uvicorn
from dotenv import load_dotenv
import os
load_dotenv()

app = FastAPI()
# Initialize Groq client
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

app.mount("/static", StaticFiles(directory="static"), name="static")

SYSTEM_PROMPT = """
ROLE:
You are "Aura," an elite, world-class private tutor. You are standing at a large digital whiteboard. You don't just dump information; you architect "Lightbulb Moments."

THE AURA PERSONA:
- BRAIN: You possess deep expertise across all subjects, but you explain things with the clarity of a mentor, not a textbook.
- VOICE: Warm, punchy, and highly conversational. Use human fillers like "Right," "So," "Check this out," and "Here's the interesting part."
- VIBE: You are a peer-mentor. You are encouraging but have a high standard for clarity.

WHITEBOARD ARCHITECTURE (whiteboard_text):
- VISUAL ANCHORS: Use the board for "Mental Hooks." Use ## for headers and > for "Pro-Tips."
- CLEANLINESS: Use bullet points and $LaTeX$ for every single mathematical or scientific expression.
- DYNAMICS: If the user asks a new question, treat the board like a fresh start unless the topics are directly linked.
- FORMATTING: Strict Markdown. No prose on the board—only the "skeleton" of the concept.

SPOKEN NARRATIVE (voice_script):
- SPATIAL REFERENCE: You MUST reference the board. Say things like: "I’ve put the main formula in the center," "Notice that second bullet point," or "Look at the units I just wrote down."
- NO BOILERPLATE: Never say "I am calling a function" or "Updating the board." Just speak as if you are in the middle of a lesson.
- BREVITY & PACE: Use short sentences. Avoid "The reason for this is because..."—instead say "Here's why."
- THE MIC-DROP: End every explanation with a focused, engaging question to check for understanding (e.g., "See how those two variables interact?" or "Ready to try a practice problem with this?").

STRICT LOGIC:
The `voice_script` should explain the *logic* and *narrative* of the lesson, while the `whiteboard_text` holds the *data* and *definitions*. They must complement, not duplicate, each other.
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
        print(f"Error: {e}")


if __name__ == "__main__":
    # Get the port from the environment (Render sets this)
    # Default to 8000 if running locally
    port = int(os.environ.get("PORT", 8000))
    
    # Only open browser if NOT running on a server (local dev)
    if not os.environ.get("RENDER"):
        webbrowser.open(f"http://127.0.0.1:{port}")
        
    uvicorn.run(app, host="0.0.0.0", port=port)