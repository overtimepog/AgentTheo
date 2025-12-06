"""
Tools Package

This package automatically discovers and loads all tools from Python files
in this directory. Simply create a new .py file with @agent_tool decorated
functions and they will be automatically registered.

Example:
    # src/tools/my_tools.py
    from src.registry import agent_tool
    
    @agent_tool
    def my_custom_tool(param: str) -> str:
        '''Description of what the tool does.'''
        return "result"
"""

import importlib
import pkgutil
from pathlib import Path


def discover_tools() -> None:
    """
    Automatically import all Python modules in the tools directory.
    
    This triggers the @agent_tool decorator for each tool function,
    registering them in the global tool registry.
    """
    package_dir = Path(__file__).parent
    
    for module_info in pkgutil.iter_modules([str(package_dir)]):
        if module_info.name.startswith("_"):
            # Skip private modules like __init__
            continue
        
        # Import the module, which triggers @agent_tool decorators
        importlib.import_module(f"src.tools.{module_info.name}")


# Auto-discover tools when this package is imported
discover_tools()
