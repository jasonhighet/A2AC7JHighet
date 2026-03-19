
import asyncio
import sys
import json
import os
from pathlib import Path

# Hardcoded data dir for debugging
project_root = Path(r"E:\Github\HyprCourse\Project")
os.environ["ACME_DATA_DIR"] = str(project_root / "acme-devops-cli" / "data")

async def test_cmd():
    # Construct the command using current python interpreter
    # Print sys.path and __file__ from within the CLI if possible
    full_cmd = [
        sys.executable, "-c", "import acme_devops_cli; print(f'CLI Location: {acme_devops_cli.__file__}')"
    ]
    print(f"Running: {' '.join(full_cmd)}")
    
    process = await asyncio.create_subprocess_exec(
        *full_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(project_root)
    )
    
    stdout, stderr = await process.communicate()
    print(f"STDOUT: {stdout.decode()}")
    print(f"STDERR: {stderr.decode()}")

if __name__ == "__main__":
    asyncio.run(test_cmd())
