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