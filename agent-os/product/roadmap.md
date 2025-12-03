# Product Roadmap

## Development Phases

This roadmap prioritizes building a functional agent core first, then layering security tools incrementally. Each item represents a complete, testable feature that delivers user value.

---

1. [x] **LangGraph Agent Core** — Implement a ReAct agent using LangGraph's StateGraph API with streaming message output, tool calling capability, and conversation memory. The agent should process user messages, invoke tools, and return structured responses. `M`

2. [x] **Basic Terminal UI** — Create a Textual-based TUI with a message input area, scrollable conversation history, and a collapsible panel showing the agent's reasoning traces. Must support streaming text display as the agent generates output. `M`

3. [x] **Persistent Kali Container** — Implement Docker container lifecycle management using docker-py: create a long-lived kalilinux/kali-rolling container on startup, execute commands inside it, stream stdout/stderr back to the agent, and persist state across TUI restarts. `S`

4. [x] **Shell Command Tool** — Create a LangGraph-compatible tool that executes arbitrary shell commands inside the Kali container with streaming output. Include command sanitization, timeout handling, and structured result formatting. `S`

5. [x] **OpenRouter LLM Integration** — Configure the agent to use OpenRouter's API with the arcee-ai/trinity-mini model. Support model switching, API key management via environment variables, and graceful error handling for rate limits. `S`

6. [ ] **Nmap Reconnaissance Tool** — Build a tool wrapping python-nmap for network scanning with support for common scan types (SYN, service detection, OS detection). Parse nmap output into structured findings and display formatted results in the TUI. `M`

7. [ ] **Browser Automation Tool** — Implement Playwright-based browser automation inside the container for web application testing. Support navigation, screenshot capture, form interaction, and JavaScript execution with results streamed back to the agent. `M`

8. [ ] **Conversation Persistence** — Save and restore conversation history and agent state to disk. Allow users to resume previous sessions with full context including discovered findings and container state. `S`

9. [ ] **Finding Tracker System** — Create a structured data model for tracking security findings (hosts, ports, services, vulnerabilities). The agent should automatically extract and store findings from tool output and reference them in future reasoning. `M`

10. [ ] **Metasploit Integration** — Integrate pymetasploit3 for Metasploit RPC automation. Support module search, exploit execution, and session management. Implement safety controls requiring user confirmation before exploitation. `L`

11. [ ] **Multi-Agent Orchestration** — Implement specialized sub-agents for reconnaissance, exploitation, and post-exploitation phases. The primary agent delegates to sub-agents based on the current task and aggregates their findings. `L`

12. [ ] **Extensible Tool Framework** — Create a plugin architecture allowing users to add custom tools via Python modules. Provide a base class, configuration schema, and auto-discovery mechanism for tools in a designated directory. `M`

---

## Effort Scale

| Label | Duration |
|-------|----------|
| XS | 1 day |
| S | 2-3 days |
| M | 1 week |
| L | 2 weeks |
| XL | 3+ weeks |

## Notes

- Items are ordered by technical dependencies and iterative value delivery
- Each item produces a testable, demonstrable capability
- Phase boundaries are implicit: items 1-5 form the MVP, 6-9 add core security value, 10-12 enable advanced use cases
- All features must work together—the agent orchestrates tools through natural language with visible reasoning
