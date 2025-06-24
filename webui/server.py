#!/usr/bin/env python3
"""
AgentTheo Web UI Server - FastAPI application with WebSocket support
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import uvicorn

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.core.main import MainOrchestrator
from webui.streaming_schema import (
    TokenEvent, ProgressEvent, ToolEvent, StatusEvent, 
    ErrorEvent, StreamStartEvent, StreamCompleteEvent,
    format_sse_event
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the webui directory
WEBUI_DIR = Path(__file__).parent
STATIC_DIR = WEBUI_DIR / "static"
TEMPLATES_DIR = WEBUI_DIR / "templates"

app = FastAPI(title="AgentTheo Web UI")

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()

# Global agent instance and task management
agent_instance: Optional[MainOrchestrator] = None
agent_queue = asyncio.Queue()
current_task = None
stop_requested = False


class AgentTaskManager:
    """Manages agent tasks with CAPTCHA detection and error handling"""
    
    def __init__(self):
        self.current_task_id = None
        self.captcha_detected = False
        self.error_count = 0
        self.max_errors = 3
    
    async def process_command(self, command: str) -> Dict:
        """Process a command and return result with metadata"""
        global agent_instance, stop_requested
        
        self.current_task_id = datetime.now().isoformat()
        self.captcha_detected = False
        result = {
            "success": False,
            "message": "",
            "captcha_detected": False,
            "task_id": self.current_task_id
        }
        
        try:
            # Check for stop command
            if command == "__STOP__":
                stop_requested = True
                result["message"] = "Stop requested"
                return result
            
            # Reset stop flag
            stop_requested = False
            
            # Execute the task
            if agent_instance:
                # Monitor for CAPTCHA during execution
                task_result = await self._execute_with_monitoring(command)
                
                if self.captcha_detected:
                    result["captcha_detected"] = True
                    result["message"] = "CAPTCHA detected! Manual intervention may be required."
                elif stop_requested:
                    result["message"] = "Task stopped by user"
                else:
                    result["success"] = True
                    result["message"] = task_result
            else:
                result["message"] = "Agent not initialized"
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            self.error_count += 1
            result["message"] = f"Error: {str(e)}"
            
            # Check if error might be CAPTCHA-related
            error_msg = str(e).lower()
            if any(word in error_msg for word in ['captcha', 'cloudflare', 'security', 'blocked', 'forbidden']):
                self.captcha_detected = True
                result["captcha_detected"] = True
                result["message"] = f"Possible CAPTCHA or security check: {str(e)}"
        
        return result
    
    async def _execute_with_monitoring(self, command: str) -> str:
        """Execute command while monitoring for CAPTCHAs"""
        # This would be enhanced with actual CAPTCHA detection logic
        # For now, we'll use the agent's execute_task method
        
        try:
            result = await agent_instance.execute_task(command)
            return result
        except Exception as e:
            # Check for common CAPTCHA indicators
            error_msg = str(e).lower()
            if any(indicator in error_msg for indicator in [
                'captcha', 'cloudflare', 'recaptcha', 'hcaptcha',
                'security check', 'access denied', 'forbidden'
            ]):
                self.captcha_detected = True
            raise


task_manager = AgentTaskManager()


@app.get("/")
async def home(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Don't echo back the command - this was the issue
            # Just process it
            if message_data.get('command'):
                # Put command in queue for agent processing
                await agent_queue.put(message_data['command'])
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.get("/stream")
async def stream_endpoint(
    request: Request,
    command: str = Query(..., description="Command to execute"),
    messageId: str = Query(..., description="Message ID for tracking"),
    stream_mode: str = Query("messages", description="Streaming mode: messages, updates, custom")
):
    """Production SSE endpoint for streaming agent responses"""
    
    async def event_generator():
        """Generate SSE events for streaming response"""
        streaming_agent = None
        
        try:
            # Send start event
            start_event = StreamStartEvent.create(
                command=command,
                stream_mode=stream_mode,
                metadata={"messageId": messageId}
            )
            yield format_sse_event(start_event)
            
            # Use the global orchestrator instance
            global agent_instance
            if not agent_instance:
                # Initialize if not already done
                agent_instance = await initialize_agent()
            
            streaming_agent = agent_instance
            
            # Send status update
            status_event = StatusEvent.create("Agent initialized, starting task...")
            yield format_sse_event(status_event)
            
            # Track progress
            step_count = 0
            total_steps = 0
            tokens_streamed = 0
            start_time = asyncio.get_event_loop().time()
            
            # Stream agent responses
            async for event in streaming_agent.astream(command, stream_mode=stream_mode):
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected for message {messageId}")
                    break
                
                # Process different event types
                if event["type"] == "token":
                    tokens_streamed += 1
                    token_event = TokenEvent.create(
                        token=event["content"],
                        metadata={
                            "count": tokens_streamed,
                            "messageId": messageId,
                            **event.get("metadata", {})
                        }
                    )
                    yield format_sse_event(token_event)
                    
                elif event["type"] == "progress":
                    step_count += 1
                    progress_event = ProgressEvent.create(
                        step=step_count,
                        total=total_steps or 10,  # Estimate if not known
                        message=str(event["content"]),
                        metadata=event.get("metadata", {})
                    )
                    yield format_sse_event(progress_event)
                    
                elif event["type"] == "tool_start":
                    tool_event = ToolEvent.create_start(
                        tool_name=event.get("metadata", {}).get("tool", "unknown"),
                        tool_input=event["content"],
                        metadata=event.get("metadata", {})
                    )
                    yield format_sse_event(tool_event)
                    
                elif event["type"] == "tool_end":
                    tool_event = ToolEvent.create_end(
                        tool_name=event.get("metadata", {}).get("tool", "unknown"),
                        tool_output=event["content"],
                        metadata=event.get("metadata", {})
                    )
                    yield format_sse_event(tool_event)
                    
                elif event["type"] == "status":
                    status_event = StatusEvent.create(
                        message=event["content"],
                        details=event.get("metadata", {})
                    )
                    yield format_sse_event(status_event)
                    
                elif event["type"] == "error":
                    error_event = ErrorEvent.create(
                        message=event["content"],
                        error_type=event.get("metadata", {}).get("type", "StreamError")
                    )
                    yield format_sse_event(error_event)
                    
                elif event["type"] == "complete":
                    # Calculate final metrics
                    elapsed_time = asyncio.get_event_loop().time() - start_time
                    
                    complete_event = StreamCompleteEvent.create(
                        result=event["content"],
                        summary={
                            "tokens_streamed": tokens_streamed,
                            "steps_completed": step_count,
                            "elapsed_time": round(elapsed_time, 2),
                            "messageId": messageId
                        },
                        metadata=event.get("metadata", {})
                    )
                    yield format_sse_event(complete_event)
                    break
                    
                # Small yield to prevent blocking
                await asyncio.sleep(0)
                
        except asyncio.CancelledError:
            logger.info(f"Stream cancelled for message {messageId}")
            error_event = ErrorEvent.create("Stream cancelled by client")
            yield format_sse_event(error_event)
            
        except Exception as e:
            logger.error(f"Stream error for message {messageId}: {e}", exc_info=True)
            error_event = ErrorEvent.create(
                message=str(e),
                error_type=type(e).__name__,
                traceback=None  # Don't expose traceback in production
            )
            yield format_sse_event(error_event)
            
        finally:
            # Cleanup
            if streaming_agent:
                try:
                    await streaming_agent.cleanup()
                except Exception as e:
                    logger.error(f"Error during streaming agent cleanup: {e}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
            "Access-Control-Allow-Origin": "*"  # Configure appropriately for production
        }
    )


async def initialize_agent():
    """Initialize the main orchestrator agent"""
    global agent_instance
    try:
        logger.info("Initializing main orchestrator...")
        agent_instance = MainOrchestrator()
        await agent_instance.initialize()
        logger.info("Main orchestrator initialized successfully")
        return agent_instance
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        return None


async def agent_task_processor():
    """Background task to process agent commands"""
    global agent_instance, stop_requested
    
    # Initialize agent once at startup
    if not agent_instance:
        agent_instance = await initialize_agent()
        if agent_instance:
            await manager.broadcast(
                json.dumps({
                    "message": "AgentTheo orchestrator is ready! I'll analyze your requests and use appropriate tools.",
                    "type": "system"
                })
            )
        else:
            await manager.broadcast(
                json.dumps({
                    "message": "Failed to initialize agent. Check logs for details.",
                    "type": "error"
                })
            )
    
    while True:
        try:
            # Get command from queue
            command = await agent_queue.get()
            logger.info(f"Processing command: {command}")
            
            # Process command with task manager
            result = await task_manager.process_command(command)
            
            # Send appropriate response based on result
            if result.get("captcha_detected"):
                await manager.broadcast(
                    json.dumps({
                        "message": result["message"],
                        "type": "error",
                        "captcha": True
                    })
                )
            elif result.get("success"):
                await manager.broadcast(
                    json.dumps({
                        "message": f"Task completed: {result['message']}",
                        "type": "agent"
                    })
                )
            else:
                await manager.broadcast(
                    json.dumps({
                        "message": result["message"],
                        "type": "error" if "error" in result["message"].lower() else "system"
                    })
                )
            
        except Exception as e:
            logger.error(f"Error in task processor: {e}")
            await manager.broadcast(
                json.dumps({
                    "message": f"Task processor error: {str(e)}",
                    "type": "error"
                })
            )
            await asyncio.sleep(1)


@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    # Start background task processor
    asyncio.create_task(agent_task_processor())
    logger.info("Web UI started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global agent_instance
    if agent_instance:
        try:
            await agent_instance.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    # Run the FastAPI server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )