# Integrate learning through reflection

1. **How do you decide when to use sub-conversations vs direct context?**
   Use direct context for immediate feedback loops and tasks that require low-latency access to the current state. Use sub-conversations (or nodes in a graph that summarize) when the volume of data exceeds the "useful" context window or when a specific sub-task (like data retrieval) can be distilled into a single factual summary before returning to the main logic.

2. **What's the right granularity for a sub-conversation?**
   The granularity should be "one logical objective." For an investigator, a sub-conversation might be "fetch all security-related data and find blockers." Once that's done, only the result (blockers found/not found) needs to return to the main agent.

3. **How do summaries lose information? What mitigations exist?**
   Summaries lose nuance, numerical edge cases, and specific citations. Mitigations include:
   - **Recursive Summarisation**: Building upon the previous summary to maintain the narrative.
   - **"Keep Lat Turn" Logic**: Never summarising the most recent exchange.
   - **Preserving Key Identifiers**: Ensuring prompt-driven summaries always include feature IDs and specific failure counts.

4. **When is memory overhead worth the benefit?**
   It's worth the benefit when the cost of "context drowning" (hallucinations, lost instructions) is higher than the cost of a summarisation call. In production, this is usually when the conversation exceeds 10-15 tool-intensive turns.

5. **How do you evaluate "good enough" for an agent decision?**
   A decision is "good enough" if it is **evidenced and cross-referenced**. If the user asks for readiness, the agent must prove it checked all 5 metrics and both reviews. If a single source is missing, the decision is "incomplete," not just "not ready."

6. **What patterns from this module apply to your domain?**
   High-performance document searching (ripgrep) and context management (summarisation) are universally applicable to any RAG system. The "System Prompt + Summary" pattern is particularly useful for building durable support agents or technical investigators that must handle several days of contextually linked tasks.
