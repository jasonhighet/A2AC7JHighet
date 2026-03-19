import pytest
import json
from pathlib import Path
from .eval_runner import EvalRunner
from .models import EvalScenario, Message, Conversation, ToolCall
from .agent import DetectiveAgent
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_eval_runner_pass(tmp_path):
    scenarios_file = tmp_path / "scenarios.json"
    scenarios = [
        {
            "id": "test_1",
            "name": "Test Pass",
            "description": "Test",
            "user_input": "Input",
            "expected_risk": "low",
            "expected_tools": ["tool1"]
        }
    ]
    with open(scenarios_file, "w") as f:
        json.dump(scenarios, f)
        
    runner = EvalRunner(str(scenarios_file))
    
    # Mock agent
    agent = MagicMock(spec=DetectiveAgent)
    agent.send_message = AsyncMock(return_value=Conversation(
        id="conv1",
        system_prompt="sys",
        messages=[
            Message(role="user", content="Input"),
            Message(role="assistant", content="Tool call", tool_calls=[ToolCall(id="tc1", name="tool1", arguments={})]),
            Message(role="tool", content="ok", tool_call_id="tc1"),
            Message(role="assistant", content="The risk is low.")
        ]
    ))
    
    scenario_objs = runner.load_scenarios()
    result = await runner.run_scenario(scenario_objs[0], agent)
    
    assert result.passed is True
    assert result.actual_risk == "low"
    assert "tool1" in result.actual_tools

@pytest.mark.asyncio
async def test_eval_runner_fail(tmp_path):
    scenarios_file = tmp_path / "scenarios.json"
    scenarios = [
        {
            "id": "test_2",
            "name": "Test Fail",
            "description": "Test",
            "user_input": "Input",
            "expected_risk": "high",
            "expected_tools": ["tool1"]
        }
    ]
    with open(scenarios_file, "w") as f:
        json.dump(scenarios, f)
        
    runner = EvalRunner(str(scenarios_file))
    
    # Mock agent - returns low risk instead of high
    agent = MagicMock(spec=DetectiveAgent)
    agent.send_message = AsyncMock(return_value=Conversation(
        id="conv2",
        system_prompt="sys",
        messages=[
            Message(role="user", content="Input"),
            Message(role="assistant", content="The risk is low.")
        ]
    ))
    
    scenario_objs = runner.load_scenarios()
    result = await runner.run_scenario(scenario_objs[0], agent)
    
    assert result.passed is False
    assert result.actual_risk == "low"
