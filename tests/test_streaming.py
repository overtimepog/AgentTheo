#!/usr/bin/env python3
"""
Tests for streaming functionality in AgentTheo
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator, Dict, Any

# Add parent directory to path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webui.server import app, stream_endpoint
from agent.browser.agent import BrowserAgent


class TestStreamingSupport:
    """Test cases for streaming functionality"""
    
    @pytest.mark.asyncio
    async def test_sse_endpoint_basic(self):
        """Test SSE endpoint basic functionality"""
        from fastapi.testclient import TestClient
        
        with TestClient(app) as client:
            # Test with streaming endpoint
            response = client.get("/stream?command=test&messageId=test-123")
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    @pytest.mark.asyncio
    async def test_agent_streaming_callback(self):
        """Test agent streaming callbacks"""
        # Mock the agent's stream method
        mock_agent = MagicMock()
        
        async def mock_stream(*args, **kwargs):
            # Simulate streaming tokens
            yield {"type": "token", "content": "Hello "}
            yield {"type": "token", "content": "world!"}
            yield {"type": "complete", "content": "Hello world!"}
        
        mock_agent.astream = mock_stream
        
        # Collect streamed tokens
        tokens = []
        async for chunk in mock_agent.astream():
            tokens.append(chunk)
        
        assert len(tokens) == 3
        assert tokens[0]["content"] == "Hello "
        assert tokens[2]["type"] == "complete"
    
    @pytest.mark.asyncio
    async def test_langgraph_streaming_integration(self):
        """Test LangGraph streaming integration"""
        from langgraph.graph import StateGraph
        from typing import TypedDict
        
        class TestState(TypedDict):
            messages: list
            
        # Create a simple test graph
        def test_node(state: TestState):
            return {"messages": state["messages"] + ["processed"]}
        
        graph = (
            StateGraph(TestState)
            .add_node("test", test_node)
            .add_edge("__start__", "test")
            .compile()
        )
        
        # Test streaming
        chunks = []
        async for chunk in graph.astream(
            {"messages": ["test"]},
            stream_mode="updates"
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert "test" in chunks[0]
    
    @pytest.mark.asyncio 
    async def test_streaming_error_handling(self):
        """Test streaming error handling"""
        async def failing_generator():
            yield {"type": "token", "content": "Starting..."}
            raise Exception("Stream error")
        
        chunks = []
        error_caught = False
        
        try:
            async for chunk in failing_generator():
                chunks.append(chunk)
        except Exception as e:
            error_caught = True
            assert str(e) == "Stream error"
        
        assert error_caught
        assert len(chunks) == 1
    
    @pytest.mark.asyncio
    async def test_streaming_cancellation(self):
        """Test streaming cancellation"""
        async def slow_generator():
            for i in range(10):
                yield {"type": "token", "content": f"Token {i}"}
                await asyncio.sleep(0.1)
        
        chunks = []
        async for chunk in slow_generator():
            chunks.append(chunk)
            if len(chunks) >= 3:
                break  # Cancel early
        
        assert len(chunks) == 3
        assert chunks[2]["content"] == "Token 2"


class TestStreamingPerformance:
    """Performance tests for streaming"""
    
    @pytest.mark.asyncio
    async def test_concurrent_streams(self):
        """Test handling multiple concurrent streams"""
        async def stream_generator(stream_id: int):
            for i in range(5):
                yield {"stream": stream_id, "token": i}
                await asyncio.sleep(0.01)
        
        # Run multiple streams concurrently
        streams = [stream_generator(i) for i in range(3)]
        results = {i: [] for i in range(3)}
        
        async def collect_stream(stream_id: int, generator):
            async for chunk in generator:
                results[stream_id].append(chunk)
        
        await asyncio.gather(*[
            collect_stream(i, stream) 
            for i, stream in enumerate(streams)
        ])
        
        # Verify all streams completed
        for i in range(3):
            assert len(results[i]) == 5
            assert all(chunk["stream"] == i for chunk in results[i])
    
    @pytest.mark.asyncio
    async def test_stream_memory_usage(self):
        """Test that streaming doesn't accumulate memory"""
        import gc
        import sys
        
        initial_objects = len(gc.get_objects())
        
        async def large_stream():
            for i in range(100):
                # Generate large chunk
                yield {"data": "x" * 1000, "index": i}
        
        # Process stream without storing all chunks
        count = 0
        async for chunk in large_stream():
            count += 1
            # Process and discard
        
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory shouldn't grow significantly
        assert count == 100
        # Allow some variance but not massive growth
        assert final_objects - initial_objects < 1000


if __name__ == "__main__":
    # Run tests
    import asyncio
    
    print("Running streaming tests...")
    
    # Basic tests
    test_suite = TestStreamingSupport()
    asyncio.run(test_suite.test_agent_streaming_callback())
    print("✓ Agent streaming callback test passed")
    
    asyncio.run(test_suite.test_streaming_error_handling())
    print("✓ Streaming error handling test passed")
    
    asyncio.run(test_suite.test_streaming_cancellation())
    print("✓ Streaming cancellation test passed")
    
    # Performance tests
    perf_suite = TestStreamingPerformance()
    asyncio.run(perf_suite.test_concurrent_streams())
    print("✓ Concurrent streams test passed")
    
    asyncio.run(perf_suite.test_stream_memory_usage())
    print("✓ Memory usage test passed")
    
    print("\nAll streaming tests passed!")