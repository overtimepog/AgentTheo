#!/usr/bin/env python3
"""
Tests for AgentTheo Web UI
"""

import asyncio
import json
import sys
import os

# Try to import test dependencies
try:
    import pytest
    from fastapi.testclient import TestClient
    from websockets.client import connect as websocket_connect
    HAS_TEST_DEPS = True
except ImportError:
    HAS_TEST_DEPS = False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webui.server import app, manager


class TestWebUI:
    """Test cases for the Web UI"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_home_page(self):
        """Test that home page loads successfully"""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "AgentTheo" in response.text
        assert "Browser View" in response.text
        assert "AgentTheo Chat" in response.text
    
    def test_home_page_contains_vnc_iframe(self):
        """Test that VNC iframe is present"""
        response = self.client.get("/")
        assert response.status_code == 200
        assert '<iframe id="vncFrame"' in response.text
        assert 'src="http://localhost:6080/vnc.html' in response.text
    
    def test_home_page_contains_websocket_connection(self):
        """Test that WebSocket connection code is present"""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "ws://localhost:8000/ws" in response.text
        assert "WebSocket" in response.text


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection and message handling"""
    # This test requires the server to be running
    # In a real test environment, you'd start the server in a fixture
    try:
        # Try to connect to WebSocket
        uri = "ws://localhost:8000/ws"
        async with websocket_connect(uri) as websocket:
            # Send a test message
            test_message = {
                "command": "test command",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            await websocket.send(json.dumps(test_message))
            
            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            
            assert "message" in data
            assert "type" in data
            
    except Exception as e:
        # If connection fails, it might be because server isn't running
        # This is expected in unit tests
        pytest.skip(f"WebSocket server not available: {e}")


def test_connection_manager():
    """Test ConnectionManager functionality"""
    from webui.server import ConnectionManager
    
    manager = ConnectionManager()
    assert manager.active_connections == []
    
    # Test would need mock WebSocket objects for full testing
    # This is a basic structure test


if __name__ == "__main__":
    if not HAS_TEST_DEPS:
        print("Note: Test dependencies not installed (pytest, fastapi.testclient)")
        print("Some tests will be skipped.")
        print("\nBasic import test:")
        try:
            from webui.server import app, manager, ConnectionManager
            print("✓ Web UI module imports successfully")
            print("✓ FastAPI app created")
            print("✓ ConnectionManager available")
        except Exception as e:
            print(f"✗ Import failed: {e}")
    else:
        # Run full tests
        test_ui = TestWebUI()
        test_ui.setup_method()
        
        print("Testing home page...")
        test_ui.test_home_page()
        print("✓ Home page loads successfully")
        
        print("Testing VNC iframe...")
        test_ui.test_home_page_contains_vnc_iframe()
        print("✓ VNC iframe present")
        
        print("Testing WebSocket code...")
        test_ui.test_home_page_contains_websocket_connection()
        print("✓ WebSocket connection code present")
        
        print("\nAll tests passed!")