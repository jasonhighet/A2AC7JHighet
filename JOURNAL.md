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