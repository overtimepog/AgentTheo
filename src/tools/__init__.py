"""
Tools Package

This package automatically discovers and loads all tools from Python files
in this directory and all subdirectories. Simply create a new .py file with
@theo_tool decorated functions and they will be automatically registered.

Example:
    # src/tools/my_tools.py
    from src.registry import theo_tool

    @theo_tool
    def my_custom_tool(param: str) -> str:
        '''Description of what the tool does.'''
        return "result"

Nested directories are also supported:
    # src/tools/dope_tools/tool.py
    from src.registry import theo_tool

    @theo_tool
    def dope_tool(param: str) -> str:
        '''A tool in a nested directory.'''
        return "dope result"
"""

import importlib
from pathlib import Path


def discover_tools() -> None:
    """
    Automatically import all Python modules in the tools directory and subdirectories.

    This triggers the @theo_tool decorator for each tool function,
    registering them in the global tool registry.

    Supports nested directories like:
        - src/tools/my_tools.py -> src.tools.my_tools
        - src/tools/dope_tools/tool.py -> src.tools.dope_tools.tool
    """
    package_dir = Path(__file__).parent

    # Find all .py files recursively
    for py_file in package_dir.rglob("*.py"):
        # Skip private modules (starting with _)
        if py_file.name.startswith("_"):
            continue

        # Convert file path to module path
        # e.g., /path/to/src/tools/dope_tools/tool.py -> src.tools.dope_tools.tool
        relative_path = py_file.relative_to(package_dir.parent.parent)
        module_path = str(relative_path.with_suffix("")).replace("/", ".").replace("\\", ".")

        # Import the module, which triggers @theo_tool decorators
        try:
            importlib.import_module(module_path)
        except Exception as e:
            # Log but don't fail on individual module import errors
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to import tool module '{module_path}': {e}"
            )


# Auto-discover tools when this package is imported
discover_tools()
