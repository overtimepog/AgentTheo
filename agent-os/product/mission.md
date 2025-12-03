# Product Mission

## Pitch

**Theo Agent** is an agentic security research assistant that helps penetration testers, red team operators, and security researchers automate reconnaissance and exploitation workflows by providing an intelligent orchestration layer over security tools with real-time reasoning visibility in a rich terminal interface.

Think of it as talking to a brilliant hacker friend who can run tools for you, explain what they find, and chain together complex attack workflows—all while showing you exactly how they think.

## Users

### Primary Customers

- **Security Researchers & Penetration Testers**: Professionals conducting authorized security assessments who need to orchestrate multiple tools efficiently while maintaining situational awareness across findings.
- **Red Team Operators**: Operators running adversary simulation engagements who need automated tool chaining for complex attack paths without losing visibility into each step.
- **Security Students & CTF Players**: Learners building penetration testing skills who benefit from an assistant that explains tool output and teaches methodology through interaction.
- **DevSecOps Engineers**: Engineers integrating security testing into CI/CD pipelines who need programmable security automation with clear, auditable output.

### User Personas

**Alex the Pentester** (28-40)
- **Role:** Senior Penetration Tester at a security consultancy
- **Context:** Runs 2-3 concurrent engagements, needs to move fast without missing findings
- **Pain Points:** Context-switching between tools; forgetting to run follow-up scans; documenting findings is tedious; junior team members need hand-holding on methodology
- **Goals:** Automate routine reconnaissance; never miss low-hanging fruit; generate preliminary findings faster; have an "extra brain" to suggest next steps

**Jordan the Red Teamer** (30-45)
- **Role:** Red Team Lead at a Fortune 500 company
- **Context:** Runs long-term adversary simulations; needs stealth and precision
- **Pain Points:** Tool orchestration for multi-stage attacks is manual and error-prone; tracking state across sessions is hard; explaining attack chains to stakeholders is time-consuming
- **Goals:** Automate tool chaining while maintaining control; persist context across sessions; generate clear attack narratives for reports

**Sam the Security Student** (20-28)
- **Role:** Cybersecurity student, active CTF competitor
- **Context:** Learning penetration testing methodology; competing in CTFs on weekends
- **Pain Points:** Doesn't know which tool to use when; struggles to interpret scan output; lacks the intuition that comes with experience
- **Goals:** Learn by doing with expert guidance; understand the "why" behind each step; build muscle memory for common attack patterns

**Morgan the DevSecOps Engineer** (28-38)
- **Role:** Security Engineer embedding security into CI/CD
- **Context:** Needs to automate security scans in pipelines; must balance thoroughness with build times
- **Pain Points:** Security tools are hard to script; output formats vary wildly; false positives flood the team; no intelligent triage
- **Goals:** Programmable security automation; intelligent result filtering; clear, actionable output for developers

## The Problem

### Tool Orchestration Chaos

Security professionals juggle dozens of specialized tools—nmap for network scanning, Burp for web testing, Metasploit for exploitation, custom scripts for everything else. Each tool has its own syntax, output format, and quirks. Context-switching between them is mentally exhausting and leads to missed findings.

**Impact:** A typical penetration test involves 15-30 different tools. Practitioners spend more time on tool mechanics than actual analysis.

**Our Solution:** Theo Agent provides a conversational interface to orchestrate tools through natural language. The agent understands pentesting methodology and chains tools together intelligently, handling output parsing and context preservation automatically.

### Disorganized Findings

Security assessments generate mountains of data—scan results, screenshots, exploit output, notes. Keeping track of what's been found, what's been exploited, and what remains to investigate is a manual, error-prone process.

**Impact:** Critical findings get lost in the noise. Follow-up scans get forgotten. Reports take days to compile.

**Our Solution:** Theo Agent maintains persistent state across interactions, tracking discovered assets, identified vulnerabilities, and exploitation status. The agent remembers what it's found and suggests logical next steps.

### Expert Knowledge Barrier

Interpreting security tool output requires deep expertise. A raw nmap scan or Metasploit session output is meaningless to anyone without years of experience. This creates bottlenecks around senior practitioners.

**Impact:** Junior team members are blocked waiting for senior review. Security students struggle to learn without mentorship.

**Our Solution:** Theo Agent explains findings in context, translating raw tool output into actionable intelligence. The agent's visible reasoning process teaches methodology through demonstration.

### Black Box Automation

Existing security automation tools operate as black boxes—you provide a target, they produce a report, but you have no visibility into the process. This makes debugging failures difficult and learning impossible.

**Impact:** Users don't trust automated results. Customization requires reverse-engineering the tool.

**Our Solution:** Theo Agent streams its reasoning process in real-time. Users see exactly what the agent is thinking, what tools it's considering, and why it made each decision. Full transparency builds trust and enables learning.

## Differentiators

### Reasoning Transparency

Unlike traditional security automation tools that hide their decision-making, Theo Agent exposes its complete thought process through streaming reasoning traces. Users see the agent think through methodology, consider tool options, and justify its choices.

**Result:** Users learn from every interaction and can intervene when the agent's reasoning diverges from their intent.

### Persistent Context

Unlike stateless CLI tools or chatbots that forget between messages, Theo Agent maintains a persistent Kali Linux container with accumulated state. Discovered hosts, open ports, and exploitation progress persist across sessions.

**Result:** Complex multi-session engagements remain coherent without manual state management.

### Claude Code-Style Interface

Unlike clunky security tool GUIs or raw terminal output, Theo Agent presents a rich terminal interface with collapsible panels, streaming output, and markdown rendering—the same interaction model that has made Claude Code beloved by developers.

**Result:** Professionals get power-user efficiency without sacrificing usability.

### Methodology-Aware Orchestration

Unlike scripted automation that follows rigid playbooks, Theo Agent understands penetration testing methodology and adapts its approach based on findings. The agent reasons about what to do next, not just how to run the next tool.

**Result:** Intelligent assistance that augments human expertise rather than replacing human judgment.

## Key Features

### Core Features

- **Conversational Tool Orchestration:** Control security tools through natural language conversation. Ask the agent to scan a network, enumerate services, or exploit a vulnerability—it handles the tool mechanics.

- **Streaming Reasoning Traces:** Watch the agent think in real-time. See it consider options, plan approaches, and explain its decisions as they happen.

- **Persistent Kali Container:** A long-lived Docker container with pre-installed security tools maintains state across interactions. Your reconnaissance progress persists between sessions.

- **Rich Terminal Interface:** A Claude Code-style TUI with collapsible panels, markdown rendering, and syntax highlighting makes complex output readable and navigable.

### Security Tool Suite

- **Network Reconnaissance:** Integrated nmap scanning with intelligent target discovery, service enumeration, and vulnerability detection.

- **Web Application Testing:** Playwright-based browser automation for authenticated scanning, screenshot capture, and interactive web app testing.

- **Exploitation Framework:** Metasploit integration via pymetasploit3 for automated exploitation workflows with session management.

- **Shell Command Execution:** Direct shell access to the Kali container with streaming output for tools not explicitly integrated.

### Advanced Features

- **Multi-Agent Orchestration:** Specialized sub-agents for different phases (recon, exploitation, post-exploitation) coordinate complex attack chains.

- **Finding Aggregation:** Automatic correlation and deduplication of findings across tools into a coherent vulnerability inventory.

- **Report Generation:** Transform accumulated findings into structured reports with evidence and remediation recommendations.

- **Extensible Tool Framework:** Add new tools through a simple Python interface—define inputs, outputs, and the agent handles the rest.
