# Project Journal

## Entry 1: Meta-Prompt Generation
- **Prompt**: Read @/prompts/1-web-api-specs.md and follow the instructions at the top of the file
- **Tool**: Antigravity
- **Mode**: Plan
- **Model**: Claude 4.6 Sonnet
- **Cost**: Free!
- **Reflections**: Had to use another AI to understand the instructions for the module. The agent generated a solid prompt that correctly captured key constraints like "No ORM" and pinned dependency versions.


## Entry 1: Journal Entry: Meta-Prompting & Local Environment Pivot
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