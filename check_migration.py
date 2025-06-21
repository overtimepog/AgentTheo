#!/usr/bin/env python3
"""Quick check to verify LangGraph is installed and working"""

import sys

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")
    
    dependencies = {
        "langchain": "LangChain",
        "langchain_core": "LangChain Core", 
        "langgraph": "LangGraph",
        "playwright": "Playwright",
        "httpx": "HTTPX (for OpenRouter)",
        "pydantic": "Pydantic"
    }
    
    missing = []
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {name} is installed")
        except ImportError:
            print(f"✗ {name} is NOT installed")
            missing.append(module)
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies are installed!")
    return True

def check_langgraph_imports():
    """Check if LangGraph imports work correctly"""
    print("\nChecking LangGraph imports...")
    
    try:
        from langgraph.prebuilt import create_react_agent
        print("✓ create_react_agent imported successfully")
        
        from langgraph.checkpoint.memory import MemorySaver
        print("✓ MemorySaver imported successfully")
        
        from langgraph.graph import StateGraph
        print("✓ StateGraph imported successfully")
        
        print("\n✅ LangGraph imports working correctly!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("LangGraph Migration Dependency Check")
    print("=" * 60)
    
    deps_ok = check_dependencies()
    imports_ok = check_langgraph_imports() if deps_ok else False
    
    print("\n" + "=" * 60)
    if deps_ok and imports_ok:
        print("✅ System ready for LangGraph!")
        print("\nYou can now run:")
        print("  python test_migration.py    # Test the migration")
        print("  ./run.sh task 'your task'   # Run browser tasks")
    else:
        print("❌ Please fix the issues above before proceeding")
        sys.exit(1)

if __name__ == "__main__":
    main()