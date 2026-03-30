import pytest
import os
import shutil
from pathlib import Path
from .persistence import FilePersistence
from .models import Conversation

@pytest.fixture
def temp_persistence():
    temp_dir = "test_conversations"
    persistence = FilePersistence(temp_dir)
    yield persistence
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def test_save_and_load(temp_persistence):
    conv = Conversation(system_prompt="test prompt")
    temp_persistence.save(conv)
    
    loaded = temp_persistence.load(conv.id)
    assert loaded is not None
    assert loaded.id == conv.id
    assert loaded.system_prompt == conv.system_prompt

def test_load_nonexistent(temp_persistence):
    assert temp_persistence.load("nonexistent") is None

def test_list_conversations(temp_persistence):
    conv1 = Conversation(system_prompt="p1")
    conv2 = Conversation(system_prompt="p2")
    temp_persistence.save(conv1)
    temp_persistence.save(conv2)
    
    ids = temp_persistence.list_conversations()
    assert len(ids) == 2
    assert conv1.id in ids
    assert conv2.id in ids
