"""
SSE Event Schema for AgentTheo Streaming
Defines the structure and types of Server-Sent Events
"""

from typing import Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class StreamEventType(str, Enum):
    """Enumeration of SSE event types"""
    TOKEN = "token"                # LLM token output
    PROGRESS = "progress"          # Task progress update
    TOOL_START = "tool_start"      # Tool execution started
    TOOL_END = "tool_end"          # Tool execution completed
    CUSTOM = "custom"              # Custom event
    ERROR = "error"                # Error event
    START = "start"                # Stream started
    COMPLETE = "complete"          # Stream completed
    STATUS = "status"              # Status update


class BaseStreamEvent(BaseModel):
    """Base model for all SSE events"""
    id: str = Field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    event: str  # Changed to str to avoid Pydantic issues
    data: Dict[str, Any]
    retry: Optional[int] = 15000  # Client retry interval in ms
    timestamp: datetime = Field(default_factory=datetime.now)


class TokenEvent(BaseStreamEvent):
    """Event for streaming LLM tokens"""
    event: Literal["token"] = StreamEventType.TOKEN.value
    data: Dict[str, Any] = Field(description="Contains 'content' (token) and optional 'metadata'")
    
    @classmethod
    def create(cls, token: str, metadata: Optional[Dict] = None):
        return cls(
            data={
                "content": token,
                "metadata": metadata or {}
            }
        )


class ProgressEvent(BaseStreamEvent):
    """Event for task progress updates"""
    event: Literal["progress"] = StreamEventType.PROGRESS.value
    data: Dict[str, Any] = Field(description="Contains progress info: step, total, percentage, message")
    
    @classmethod
    def create(cls, step: int, total: int, message: str, metadata: Optional[Dict] = None):
        percentage = (step / total * 100) if total > 0 else 0
        return cls(
            data={
                "step": step,
                "total": total,
                "percentage": round(percentage, 2),
                "message": message,
                "metadata": metadata or {}
            }
        )


class ToolEvent(BaseStreamEvent):
    """Event for tool execution updates"""
    event: Union[Literal["tool_start"], Literal["tool_end"]]
    data: Dict[str, Any] = Field(description="Contains tool name, input/output, and metadata")
    
    @classmethod
    def create_start(cls, tool_name: str, tool_input: str, metadata: Optional[Dict] = None):
        return cls(
            event=StreamEventType.TOOL_START.value,
            data={
                "tool": tool_name,
                "input": tool_input,
                "metadata": metadata or {}
            }
        )
    
    @classmethod
    def create_end(cls, tool_name: str, tool_output: str, metadata: Optional[Dict] = None):
        return cls(
            event=StreamEventType.TOOL_END.value,
            data={
                "tool": tool_name,
                "output": tool_output,
                "metadata": metadata or {}
            }
        )


class StatusEvent(BaseStreamEvent):
    """Event for status updates"""
    event: Literal["status"] = StreamEventType.STATUS.value
    data: Dict[str, Any] = Field(description="Contains status message and optional details")
    
    @classmethod
    def create(cls, message: str, details: Optional[Dict] = None):
        return cls(
            data={
                "message": message,
                "details": details or {}
            }
        )


class ErrorEvent(BaseStreamEvent):
    """Event for errors"""
    event: Literal["error"] = StreamEventType.ERROR.value
    data: Dict[str, Any] = Field(description="Contains error message, type, and traceback")
    
    @classmethod
    def create(cls, message: str, error_type: str = "Unknown", traceback: Optional[str] = None):
        return cls(
            data={
                "message": message,
                "type": error_type,
                "traceback": traceback
            }
        )


class StreamStartEvent(BaseStreamEvent):
    """Event for stream start"""
    event: Literal["start"] = StreamEventType.START.value
    data: Dict[str, Any] = Field(description="Contains stream configuration and metadata")
    
    @classmethod
    def create(cls, command: str, stream_mode: str, metadata: Optional[Dict] = None):
        return cls(
            data={
                "command": command,
                "stream_mode": stream_mode,
                "metadata": metadata or {}
            }
        )


class StreamCompleteEvent(BaseStreamEvent):
    """Event for stream completion"""
    event: Literal["complete"] = StreamEventType.COMPLETE.value
    data: Dict[str, Any] = Field(description="Contains final result and summary")
    
    @classmethod
    def create(cls, result: str, summary: Optional[Dict] = None, metadata: Optional[Dict] = None):
        return cls(
            data={
                "result": result,
                "summary": summary or {},
                "metadata": metadata or {}
            }
        )


def format_sse_event(event: BaseStreamEvent) -> str:
    """Format an event for SSE transmission
    
    Args:
        event: The event to format
        
    Returns:
        SSE-formatted string
    """
    lines = []
    
    # Add event ID
    lines.append(f"id: {event.id}")
    
    # Add event type
    lines.append(f"event: {event.event}")
    
    # Add retry interval
    if event.retry:
        lines.append(f"retry: {event.retry}")
    
    # Add data (JSON encoded)
    import json
    data_json = json.dumps(event.data, default=str)
    lines.append(f"data: {data_json}")
    
    # SSE events end with double newline
    return "\n".join(lines) + "\n\n"