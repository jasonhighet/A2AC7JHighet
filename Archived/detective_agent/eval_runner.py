import asyncio
import json
import time
from pathlib import Path
from typing import List
from .agent import DetectiveAgent
from .models import EvalScenario, EvalResult, Message
from .provider import LLMStudioProvider
from .persistence import FilePersistence
from .config import settings

class EvalRunner:
    def __init__(self, scenarios_path: str = "detective_agent/eval_scenarios.json"):
        self.scenarios_path = Path(scenarios_path)
        self.results: List[EvalResult] = []

    def load_scenarios(self) -> List[EvalScenario]:
        with open(self.scenarios_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [EvalScenario(**s) for s in data]

    async def run_scenario(self, scenario: EvalScenario, agent: DetectiveAgent) -> EvalResult:
        start_time = time.perf_counter()
        
        # In a real eval, we might want to mock the provider more strictly
        # or use a deterministic seed if supported.
        conversation = await agent.send_message(scenario.user_input)
        
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        # Analyze the conversation to determine if it passed
        assistant_msgs = [m for m in conversation.messages if m.role == "assistant"]
        tool_msgs = [m for m in conversation.messages if m.role == "tool"]
        
        actual_tools = []
        for msg in conversation.messages:
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    actual_tools.append(tc.name)
        
        last_response = assistant_msgs[-1].content.lower() if assistant_msgs else ""
        
        # Heuristic check for risk level in response
        actual_risk = "unknown"
        if any(word in last_response for word in ["high", "blocked", "fail", "risk: high"]):
            actual_risk = "high"
        elif any(word in last_response for word in ["low", "approve", "pass", "risk: low"]):
            actual_risk = "low"
            
        # Basic pass/fail criteria
        # 1. Did it call the expected tools?
        tools_passed = all(t in actual_tools for t in scenario.expected_tools)
        # 2. Did the risk level match (if expected)?
        risk_passed = scenario.expected_risk == actual_risk if scenario.expected_risk != "unknown" else True
        
        passed = tools_passed and risk_passed
        
        return EvalResult(
            scenario_id=scenario.id,
            passed=passed,
            actual_risk=actual_risk,
            actual_tools=actual_tools,
            reasoning=assistant_msgs[-1].content if assistant_msgs else "No response",
            latency_ms=latency_ms,
            tokens_used=0 # Would need to extract from traces or provider response
        )

    async def run_all(self):
        scenarios = self.load_scenarios()
        provider = LLMStudioProvider(base_url=settings.llm_base_url, model=settings.llm_model)
        persistence = FilePersistence(directory=".eval_conversations")
        
        print(f"Starting evaluation of {len(scenarios)} scenarios...")
        
        for scenario in scenarios:
            # New agent for each scenario to avoid context leakage
            agent = DetectiveAgent(provider=provider, persistence=persistence)
            print(f"Running scenario: {scenario.name}...", end="", flush=True)
            result = await self.run_scenario(scenario, agent)
            self.results.append(result)
            status = "PASS" if result.passed else "FAIL"
            print(f" {status} ({result.latency_ms:.0f}ms)")

        self.save_report()

    def save_report(self):
        report = {
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed),
                "pass_rate": sum(1 for r in self.results if r.passed) / len(self.results) if self.results else 0
            },
            "results": [r.model_dump() for r in self.results]
        }
        with open("eval_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nEvaluation complete. Pass rate: {report['summary']['pass_rate']*100:.1f}%")
        print("Report saved to eval_report.json")

if __name__ == "__main__":
    runner = EvalRunner()
    asyncio.run(runner.run_all())
