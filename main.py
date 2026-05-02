from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from langchain_core.messages import HumanMessage
from fastapi import HTTPException  # Add this import if not already
from typing import List, Dict, Any, Optional
from langgraph.graph import MessagesState
from fastapi import Form, File, UploadFile



from app import (
    initialize_graph,
    get_graph,
    all_tools,
    SYSTEM_PROMPT
)
from dotenv import load_dotenv
import asyncio
import speech_recognition as sr
import os
import tempfile
import subprocess

DB_URI = "mongodb://admin:password123@localhost:27017"

import json
load_dotenv()

# Allow CORS from your frontend (e.g., localhost:3000)
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003" # Your frontend dev server
    # Add other domains if needed (e.g., deployed frontend)
]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    file_urls: Optional[Dict[str, str]] = None

class ConversationHistory(BaseModel):
    messages: List[ChatMessage]

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        initialize_graph()
        print("🚀 Atlas Backend initialized successfully!")
        yield
    except Exception as e:
        print(f"Error initializing backend: {e}")
        raise

app = FastAPI(
    title="Atlas Cloud Assistant API",
    description="REST API for Atlas, the intelligent cloud infrastructure assistant",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Can also use ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/transcribe/")
async def transcribe(audio: UploadFile = File(...)):
    temp_webm = None
    temp_wav = None

    try:
        print(f"Received audio file: {audio.filename}, content_type: {audio.content_type}")
        audio_bytes = await audio.read()
        print(f"Audio file size: {len(audio_bytes)} bytes")

        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_webm_file:
            temp_webm = temp_webm_file.name
            temp_webm_file.write(audio_bytes)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav_file:
            temp_wav = temp_wav_file.name

        print(f"Converting {temp_webm} to {temp_wav}")

        # Convert webm to wav using ffmpeg with better error handling
        ffmpeg_cmd = [
            'ffmpeg', '-i', temp_webm,
            '-ar', '16000',  # Sample rate
            '-ac', '1',      # Mono
            '-y',            # Overwrite output file
            temp_wav
        ]

        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )

        if result.returncode != 0:
            print(f":x: FFmpeg error: {result.stderr}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Audio conversion failed: {result.stderr}"}
            )

        print(":white_check_mark: Audio conversion successful")

        # Check if the converted file exists and has content
        if not os.path.exists(temp_wav) or os.path.getsize(temp_wav) == 0:
            return JSONResponse(
                status_code=500,
                content={"error": "Converted audio file is empty or doesn't exist"}
            )

        print(f":bar_chart: Converted WAV file size: {os.path.getsize(temp_wav)} bytes")

        # Transcribe using speech recognition
        recognizer = sr.Recognizer()

        # Adjust recognizer settings for better accuracy
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        recognizer.phrase_threshold = 0.3

        with sr.AudioFile(temp_wav) as source:
            print("Loading audio for transcription...")
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)

        print(":speaking_head_in_silhouette: Starting speech recognition...")

        try:
            # Try Google Speech Recognition first
            text = recognizer.recognize_google(audio_data, language='en-US')
            print(f"Transcription successful: '{text}'")

            if not text.strip():
                return JSONResponse(
                    status_code=400,
                    content={"error": "No speech detected in the audio"}
                )

            return {"transcript": text}

        except sr.UnknownValueError:
            print(":x: Speech Recognition could not understand audio")
            return JSONResponse(
                status_code=400,
                content={"error": "Could not understand the audio. Please speak clearly and try again."}
            )
        except sr.RequestError as e:
            print(f":x: Speech Recognition service error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Speech recognition service error: {str(e)}"}
            )

    except subprocess.TimeoutExpired:
        print(":x: FFmpeg conversion timeout")
        return JSONResponse(
            status_code=500,
            content={"error": "Audio conversion timeout"}
        )
    except Exception as e:
        print(f":x: Transcription error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Transcription failed: {str(e)}"}
        )
    finally:
        # Clean up temporary files
        try:
            if temp_webm and os.path.exists(temp_webm):
                os.remove(temp_webm)
                print(f"Cleaned up {temp_webm}")
        except:
            pass
        try:
            if temp_wav and os.path.exists(temp_wav):
                os.remove(temp_wav)
                print(f"Cleaned up {temp_wav}")
        except:
            pass


@app.post("/generate")
async def generate(
    message: str = Form(...),
    thread_id: str = Form(None),
    files: List[UploadFile] = File([])  # if uploading multiple files
):
    graph = get_graph()

    user_input = message
    messages = [{"role": "user", "content": user_input}]

    if not messages or messages[0]["role"] != "system":
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    async def event_generator():
        config = {
            "configurable": {
                "thread_id": thread_id or "1"
            }
        }

        async for chunk in graph.astream(
            {"messages": [HumanMessage(content=user_input)]},
            config,
            stream_mode="values"
        ):
            if "messages" in chunk and chunk["messages"]:
                content = chunk["messages"][-1].content
                role = getattr(chunk["messages"][-1], "type", "")
                if role == "ai" and content.strip():
                    yield json.dumps({"content": content}) + "\n"
                    await asyncio.sleep(0.1)

    return StreamingResponse(event_generator(), media_type="application/json")
    
@app.get("/health")
async def health_check():
    """
    Health check endpoint with more details
    """
    try:
        graph = get_graph()  # Add this line
        return {
            "status": "healthy",
            "database": "memory",  # Or provide actual DB status if available
            "graph_initialized": graph is not None,
            "tools_available": len(all_tools) if all_tools else 0
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")
    