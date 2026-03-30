import os
from .config import Settings
from .prompts import DEFAULT_SYSTEM_PROMPT

def test_default_settings():
    s = Settings()
    assert s.llm_base_url == "http://localhost:1234/v1"
    assert s.system_prompt == DEFAULT_SYSTEM_PROMPT

def test_env_override():
    os.environ["DETECTIVE_LLM_MODEL"] = "gpt-4-test"
    os.environ["DETECTIVE_SYSTEM_PROMPT"] = "You are a test agent."
    
    s = Settings()
    assert s.llm_model == "gpt-4-test"
    assert s.system_prompt == "You are a test agent."
    
    # Cleanup
    del os.environ["DETECTIVE_LLM_MODEL"]
    del os.environ["DETECTIVE_SYSTEM_PROMPT"]
