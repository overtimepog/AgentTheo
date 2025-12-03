# Theo Agent MVP - Raw Idea

**Feature Name**: Theo Agent MVP - Core Agent with TUI and Shell Tool

**Description**: Build the foundational MVP of Theo Agent - an agentic security research assistant with a Claude Code-style terminal interface. This MVP includes:

1. **LangGraph Agent Core**: A ReAct agent using LangGraph's StateGraph API with streaming message output, tool calling, and conversation memory
2. **Basic Terminal UI**: A Textual-based TUI with message input, scrollable conversation history, and collapsible reasoning panel with streaming support
3. **Persistent Kali Container**: Docker container lifecycle management using docker-py with the kalilinux/kali-rolling image
4. **Shell Command Tool**: A tool to execute commands inside the Kali container with streaming stdout/stderr
5. **OpenRouter LLM Integration**: Integration with OpenRouter API using arcee-ai/trinity-mini model

This spec covers roadmap items 1-5 from the product roadmap, forming the complete MVP.

**Target Users**: Security researchers, penetration testers, red team operators, security students

**Key Value**: Natural language interface to security tools with visible AI reasoning in a rich terminal UI

---

**Spec Initiated**: 2025-12-02
**Status**: Planning - Requirements Research Phase
