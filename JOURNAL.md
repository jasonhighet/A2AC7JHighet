# Project Journal

## Entry 1: Meta-Prompt Generation
- **Prompt**: Read @/prompts/1-web-api-specs.md and follow the instructions at the top of the file
- **Tool**: Antigravity
- **Mode**: Plan
- **Model**: Claude 4.6 Sonnet
- **Cost**: Free!
- **Reflections**: Had to use another AI to understand the instructions for the module. The agent generated a solid prompt that correctly captured key constraints like "No ORM" and pinned dependency versions.


## Entry 2: Journal Entry: Meta-Prompting & Local Environment Pivot
-   **Prompt**: "Read @/prompts/1-web-api-specs.md and follow the instructions at the top of the file to generate an implementation prompt."
-   **Tool**: Google Antigravity
-   **Mode**: Plan
-   **Context**: Clean
-   **Model**: Claude 4.6 Sonnet
-   **Input**: `prompts/1-web-api-specs.md`
-   **Output**: `prompts/2-web-api-prompt.md`
-   **Cost**:  Free

### Reflections

-   **What frustrated you?**: Moving away from the course-standard Docker/Linux setup required manual overrides in the spec file to ensure the AI didn't hallucinate a containerised environment. It took extra effort to explicitly define a native Windows PostgreSQL path and `uv` execution.
-   **What surprised you?**: The "meta-prompting" (using AI to write a prompt for another AI) resulted in a much more pedantic and structured set of instructions than I would have written manually.
-   **How will this influence you going forward?**: In a real-world engineering lead role, this level of multi-step ceremony feels high-friction for a simple CRUD service. However, as a mechanism for **automated governance**, I see the value in "locking down" architectural choices (like the "No ORM" rule) before code generation begins.
-   **Planning efforts**: Rating: 8/10. The plan is now robust enough to handle the Windows environment, but the process of "prompting to prompt" still feels slightly academic compared to direct iteration.

## Entry 3: Initializing the Admin UI Prompt
## Entry 3: Initializing the Admin UI Prompt
- **Prompt Source**: Hand-crafted/AI-assisted draft for `prompts/4-admin-ui-prompt.md`.
- **Goal**: Define the constraints for a framework-less Web Component frontend.
- **Reflections**: Decided to stick with the `pnpm` requirement from the course brief despite `npm` being in the README, as it's a good test of the AI's ability to switch package managers.
- **Challenge**: Ensuring the AI understands it must look at the Python files in `config-service/` to determine the API contract for the TypeScript types.


Prompt: Read @/prompts/4-admin-ui-prompt.md and follow the instructions at the top of the file.
Tool: Cline
Mode: Plan
Context: Clean
Model: Claude 4.6 Sonnet
Input: prompts/4-admin-ui-prompt.md
Output: prompts/5-admin-ui-plan.md


## Module 2: Context Framework Setup
- **Prompt**: Initialize memory/ and .agent/rules/
- **Tool**: Antigravity (Windows Native)
- **Model**: Gemini Flash 3
- **Cost**: free
- **Reflections**:
  - The agent correctly linked the memory files in the rule?
  - I am not sure if having a persistent `TECHNICAL.md` reduces the need for long repetitive prompts?  Does it help the AI to remember the constraints? Does it waste context?


  ## Module 3: Reflections

  1. Were you able to successfully get your assistant to pick up where you left off (with an empty context window) with just "what's the next step?" or "what is our status?"
The memory files effectively managed the state. Upon starting a new session, the agent identified the Windows-native configuration and uv dependencies without prompting. The pointer logic in WORKFLOW_STATUS.md made the "what is our status?" recovery trivial, as it immediately directed the agent to the active story file.

2. Were you able to get your assistant to behave properly during the transitions?
Transitions through the four-stage loop—Planning, Building, Reflecting, and Done—were consistent. The protocol demonstrated its utility when make was found to be missing; the agent reverted to the documented uv run commands specified in the scripts file rather than improvising or failing. It maintained clean gates between planning and implementation.

3. Did your assistant continue to adhere to your directives in other parts of its memory?
Adherence was steady. The agent respected the "no Docker" and "uv" constraints consistently, even across long sessions. A sync-memory exercise identified a minor documentation gap where a rule was present in ENV_SCRIPTS.md but missing from TECHNICAL.md. This provided a practical test of the reflect-and-adapt stage and reinforced the need for a centralised source of truth.

4. What was a behaviour that your assistant took a lot of work to get right?
Establishing a clean separation of concerns within the memory bank required the most iteration. It took some effort to ensure WORKFLOW_STATUS.md governed the process while TECHNICAL.md governed the constraints. Initial versions suffered from state duplication between the work item files and the status dashboard, which caused ambiguity. Explicitly defining where the "authority" lives for each category was necessary to resolve the friction.


## Module 4: Reflections


### Which MCP servers did you attempt to use? Were you unsuccessful with any of them? Why?

I successfully implemented three different types of MCP servers: Context7 for real-time documentation, Postgres-mcp-pro for database introspection, and a Trello server for backlog management. While all three were eventually successful, the Trello integration was significantly more difficult to configure. Navigating the Trello developer portal to generate a Power-Up, API key, and manual token involved a level of administrative friction that felt disproportionate to the task, though the resulting connectivity to the backlog was worth the effort.

### Did you install any local servers? Docker or on the metal? What are your reflections between the two?
I installed the Postgres-mcp-pro server "on the metal" using uv. In my Windows-native environment, avoiding Docker for local developer tools reduces significant overhead and potential filesystem performance issues. Running these tools directly on the host OS feels more aligned with a lightweight, high-flow developer experience. The "metal" approach is easier to maintain for local databases, whereas Docker's value seems more evident for complex, multi-dependency services that I don't want to pollute my primary machine with.  (Basically I am, I can't be bothered with docker.)

### Which MCP servers do you suspect would be useful to run locally? What about remotely and/or team shared?
Local execution is ideal for Postgres or filesystem tools where the agent needs direct, low-latency access to private data and local architectural context. Conversely, Context7 is a perfect candidate for a remote service; documentation is a global resource that doesn't need to live on my machine and benefits from being centralised and updated by a third party. For team-shared environments, SaaS integrations like Trello or internal API browsers provide a shared source of truth that keeps the entire squad's agentic workflows synchronised.

### Are there any obvious candidates for useful MCP servers in your organisation? Is this supporting an existing need, or a new opportunity?

In my organisation, we already have established MCPs for Jira, Confluence, GitHub, Office, Teams, and many others, which support our current operational needs. For my personal projects, I would like to implement integration with Google Workspace (Tasks, Calendar, Docs) to better support my individual requirements.

Beyond these standard integrations, there is a significant new opportunity to develop custom MCP servers for our centralised architectural standards and engineering practice playbooks. Instead of engineers manually searching through internal wikis, an MCP could provide our agents with real-time "compliance-as-context," ensuring that new service designs automatically align with our specific engineering practices as they are being written.

## Module 5: Reflections - HTTP MCP Server & Integration

1.  **How smooth was the process of getting your first tool working in the MCP Inspector?**
    The process was logically straightforward but required attention to environmental details. Using `npx` to launch the Inspector made it easy to get a visual interface quickly. The main "speed bumps" were local port conflicts (like port 6277 already being in use) and ensuring the Python environment had all dependencies installed. Once the server connected, the ability to see the tool schemas and test them with a single click was incredibly satisfying and much faster than manual terminal testing.

2.  **How did you find the difference between building and using a stdio server versus the http one?**
    Building the **stdio server** felt more direct for local development. We used the "Subprocess Wrapper" pattern, which allowed me to reuse an existing CLI tool without rewriting business logic—this is a huge efficiency gain for legacy code. The **HTTP server**, while requiring more setup (like a running API background process), felt more like a modern web service. It required more robust error handling for network issues (timeouts, 404s) but offered better scalability. The biggest "aha!" moment was realizing that while the transport layer changed, the MCP tool definitions remained almost identical, showing how flexible the protocol is.

3.  **How successful was your assistant at knowing when and how to use the tools?**
    The assistant was very proactive in chaining tools together. For example, it "knew" to call `get_deployment_status` to find a version number before it attempted a `promote_release`. The success largely came down to the quality of the docstrings in the `@mcp.tool()` decorators. When we added explicit environment validation at the MCP layer, the assistant became even more helpful because it could provide immediate corrections if I made a typo, rather than waiting for an API error.

4.  **Have you identified an MCP server that might be good to build for yourself or your org?**
    Beyond the standard integrations we already use, I think a custom **"Compliance-as-Context" MCP server** for our engineering standards and playbooks would be a significant opportunity. Instead of engineers manually searching through internal wikis, 

## Module 6: Detective Agent Implementation (Steps 1-7)

  - **What frustrated you?**: Pydantic validation errors! I accidentally broke the `Conversation` model during Step 7 and basically nuked every single existing test. Lesson learned: always check the default factories before stripping out "extra" fields. Also, my first "Mandatory Reporting" prompt caused an infinite tool loop—the agent was so eager to be thorough that it just kept filing reports until the token limit hit.
  - **What surprised you?**: Seeing the OpenTelemetry spans in a local `.traces/` folder was surprisingly satisfying. It’s one thing to talk about observability, but seeing the JSON payloads of the LLM calls and tool execution times makes debugging the "black box" much easier.
  - **Tool Chaining**: The agent "figuring out" it needs to call the release summary before the risk report felt like a solid win for the system prompt. It wasn't just following a script; it was actually trying to gather evidence.
  - **Evaluation**: The 66.7% pass rate was a wake-up call. It's easy to assume the agent "knows" what to do, but without the evaluation runner, I wouldn't have spotted the cases where it skipped critical tools because it was being "too efficient."
  - **Windows Native**: Still holding strong. `uv run pytest` is blazing fast compared to booting up a Docker container every time. (I still can't be bothered installing Docker)
## Module 7: Investigator Agent Implementation

- **What frustrated you?**: Unicode characters on Windows! Fighting with cp1252 encoding errors while trying to print a simple "?" or "?" checkmark in the CLI was a reminder that "on the metal" Windows development has its own unique tax. I eventually had to scrub all emojis from the CLI to ensure a stable experience.
- **What surprised you?**: The power of LangGraph's cyclic state. In previous modules, we built linear tools, but seeing the agent "think," realize it missed a metric, and loop back to the analysis tool autonomously felt like a step up in "agency."
- **Aha! Moment**: The evaluation suite's "ground truth" scenarios. It's one thing to see the agent work once; it's another to see it hit an 83% success rate across 7 diverse scenarios. Realizing that evaluate() returns a nested 
esults list inside evaluation_results was a bit of a debugging detour, but it made the final summary stats much more rewarding.
- **Observability**: Integrating OpenTelemetry was a game-changer. Being able to see exactly why a tool failed or what the LLM was "thinking" by looking at a local JSON span file makes debugging non-deterministic agent behavior feel deterministic.
- **Reliability**: Exponential back-off with jitter in the tool layer saved several runs when I accidentally had the analysis JSON file open in another editor (causing a transient permission error). The agent just waited a beat and successfully retried.
- **Final Verdict**: uv + LangGraph + OpenTelemetry = A very powerful, lightweight stack for building production-ready agents without the "Docker tax."

## Module 8: Agentic Knowledge Management

### The Holiday Shortcut and the Black Box

I'll be completely honest: I didn't build this module step-by-step. With my holiday coming up, I decided to treat the entire thing as a pure experiment in delegation. I handed the full project context over to Antigravity, let it rip, and essentially one-shotted the requirements so I could get my homework finished in time to get away. On the surface, it was a massive success. The code looks professional, the expanded logic for the Investigator Agent is all there, and every single test is coming back green. As I reflected in my LinkedIn post (https://www.linkedin.com/feed/update/urn:li:activity:7440487263756582912/), the real "program" is the mental model in the builder’s head, not just the code residue on the disk. Right now, I have a high-quality pile of code that passes every test, but I haven't actually possessed the theory of the system yet.

### Code as Residue vs. Theory Building

The problem is that while the code exists, the "program" doesn't---at least not in the way Peter Naur described it. In his 1985 paper, he argued that the real program is the mental model held by the person who built it, and the code is just the residue left behind. Right now, I am staring at a very high-quality pile of residue. I've pushed my "lower bound" of trust so high for the sake of efficiency that the entire system has become a black box. It's a functional outcome for a Friday afternoon, but it means I'm currently operating as a systems designer who has traded understanding for speed.

### The Post-Holiday Debt

The reality is that I have no mental model of how this actually works. If this thing broke right now, I wouldn't have a clue how to debug it or even where to start looking. I've achieved the goal of getting the project finished, but I haven't done the actual work of software engineering yet, which is possessing the theory of the system. Once I'm back from holiday, I'm going to have to spend a lot of time descending back into these layers to initialise a proper map of the logic and actually work out what the AI has put together.

### Risk, Sleep, and Future Research

As I noted on LinkedIn, the depth of the mental model you need is really just a function of risk. For a holiday deadline, treating the module as magic was a gamble I was willing to take to get out the door. But I'm not comfortable leaving it as a permanent black box. The code is functional and passes the evaluations, but until I've done the research to understand the specific choices the agent is making, I'm just drifting. The next phase will be about reclaiming that theory so I'm not the one staring at a terminal in the dark later on.