#!/usr/bin/env python3
"""
Tests for Resizable Panels functionality in AgentTheo Web UI
"""

import asyncio
import json
import sys
import os
import time

# Try to import test dependencies
try:
    import pytest
    from selenium import webdriver
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestResizablePanels:
    """Test cases for resizable panels functionality"""
    
    @pytest.fixture
    def driver(self):
        """Create a Chrome WebDriver instance"""
        if not HAS_SELENIUM:
            pytest.skip("Selenium not installed")
            
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode for CI
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1280, 720)
        yield driver
        driver.quit()
    
    def test_resize_panels_basic(self, driver):
        """Test basic panel resizing functionality"""
        # Navigate to the application
        driver.get("http://localhost:8000")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        resizer = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "panel-resizer")))
        
        # Get initial panel sizes
        vnc_panel = driver.find_element(By.CLASS_NAME, "vnc-panel")
        chat_panel = driver.find_element(By.CLASS_NAME, "chat-panel")
        
        initial_vnc_width = vnc_panel.size['width']
        initial_chat_width = chat_panel.size['width']
        
        # Perform resize by dragging resizer
        actions = ActionChains(driver)
        actions.click_and_hold(resizer).move_by_offset(100, 0).release().perform()
        
        # Check that panels resized
        time.sleep(0.5)  # Wait for animation
        new_vnc_width = vnc_panel.size['width']
        new_chat_width = chat_panel.size['width']
        
        assert new_vnc_width > initial_vnc_width
        assert new_chat_width < initial_chat_width
    
    def test_resize_over_iframe(self, driver):
        """Test that resize continues working when dragging over VNC iframe"""
        driver.get("http://localhost:8000")
        
        wait = WebDriverWait(driver, 10)
        resizer = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "panel-resizer")))
        vnc_frame = wait.until(EC.presence_of_element_located((By.ID, "vncFrame")))
        
        # Get initial panel width
        vnc_panel = driver.find_element(By.CLASS_NAME, "vnc-panel")
        initial_width = vnc_panel.size['width']
        
        # Start resize and drag over iframe area
        actions = ActionChains(driver)
        actions.click_and_hold(resizer)
        
        # Move in steps to simulate dragging over iframe
        for i in range(5):
            actions.move_by_offset(-20, 0)
        
        actions.release().perform()
        
        # Verify resize completed successfully
        time.sleep(0.5)
        final_width = vnc_panel.size['width']
        
        # Panel should be smaller after dragging left
        assert final_width < initial_width
        assert final_width >= 300  # Respects minimum width
    
    def test_double_click_reset(self, driver):
        """Test double-click to reset panel sizes"""
        driver.get("http://localhost:8000")
        
        wait = WebDriverWait(driver, 10)
        resizer = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "panel-resizer")))
        
        # First resize panels
        actions = ActionChains(driver)
        actions.click_and_hold(resizer).move_by_offset(150, 0).release().perform()
        time.sleep(0.5)
        
        # Double click to reset
        actions.double_click(resizer).perform()
        time.sleep(0.5)
        
        # Check panels are back to 50/50
        vnc_panel = driver.find_element(By.CLASS_NAME, "vnc-panel")
        chat_panel = driver.find_element(By.CLASS_NAME, "chat-panel")
        
        container_width = driver.find_element(By.CLASS_NAME, "container").size['width']
        vnc_width = vnc_panel.size['width']
        chat_width = chat_panel.size['width']
        
        # Should be approximately 50% each (minus resizer width)
        assert abs(vnc_width - container_width/2) < 10
        assert abs(chat_width - container_width/2) < 10
    
    def test_minimum_panel_widths(self, driver):
        """Test that panels respect minimum width constraints"""
        driver.get("http://localhost:8000")
        
        wait = WebDriverWait(driver, 10)
        resizer = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "panel-resizer")))
        
        # Try to make VNC panel too small
        actions = ActionChains(driver)
        actions.click_and_hold(resizer).move_by_offset(-500, 0).release().perform()
        time.sleep(0.5)
        
        vnc_panel = driver.find_element(By.CLASS_NAME, "vnc-panel")
        assert vnc_panel.size['width'] >= 400  # Minimum width from JS config
        
        # Try to make chat panel too small
        actions.click_and_hold(resizer).move_by_offset(1000, 0).release().perform()
        time.sleep(0.5)
        
        chat_panel = driver.find_element(By.CLASS_NAME, "chat-panel")
        assert chat_panel.size['width'] >= 400  # Minimum width from JS config


def test_resize_functionality_manual():
    """Manual test instructions for resize functionality"""
    print("\n=== Manual Test Instructions for Resize Functionality ===\n")
    print("1. Open http://localhost:8000 in a browser")
    print("2. Locate the vertical resizer between VNC and Chat panels")
    print("3. Test: Basic Resize")
    print("   - Click and drag the resizer left/right")
    print("   - Verify both panels resize accordingly")
    print("\n4. Test: Resize Over VNC Panel")
    print("   - Start dragging the resizer")
    print("   - Move mouse over the VNC iframe area")
    print("   - Continue dragging")
    print("   - Verify resize continues working (FIXED IN THIS UPDATE)")
    print("\n5. Test: Double-click Reset")
    print("   - Double-click the resizer")
    print("   - Verify panels return to 50/50 split")
    print("\n6. Test: Minimum Widths")
    print("   - Try to make panels very small")
    print("   - Verify they stop at minimum width (400px)")
    print("\n7. Test: Persistence")
    print("   - Resize panels to a custom position")
    print("   - Refresh the page")
    print("   - Verify panels maintain their positions")


if __name__ == "__main__":
    if not HAS_SELENIUM:
        print("Note: Selenium not installed for automated browser tests")
        print("To run automated tests: pip install selenium")
    
    # Run manual test instructions
    test_resize_functionality_manual()
    
    print("\n=== Summary of Changes Made ===\n")
    print("Fixed the resize bug by:")
    print("1. Added a full-screen overlay during resize operations")
    print("2. Set pointer-events: none on iframes during resize")
    print("3. Created a transparent overlay to capture all mouse events")
    print("4. The resizer now works correctly even when dragging over the VNC panel")