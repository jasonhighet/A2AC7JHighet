
import asyncio
import sys
import json
import os
from pathlib import Path

# Hardcoded project root
project_root = Path(r"E:\Github\HyprCourse\Project")
cli_src = project_root / "acme-devops-cli" / "src"

# Force ACME_DATA_DIR and PYTHONPATH
env = os.environ.copy()
env["ACME_DATA_DIR"] = str(project_root / "acme-devops-cli" / "data")
env["PYTHONPATH"] = str(cli_src) + os.pathsep + env.get("PYTHONPATH", "")

async def test_cmd():
    # Construct the command using current python interpreter
    full_cmd = [
        sys.executable, "-m", "acme_devops_cli.main", "--format", "json", "--verbose",
        "promote", 
        "--app", "web-app", 
        "--release", "v2.1.4", 
        "--from", "uat", 
        "--to", "prod"
    ]
    print(f"Running: {' '.join(full_cmd)}")
    print(f"PYTHONPATH: {env['PYTHONPATH']}")
    
    process = await asyncio.create_subprocess_exec(
        *full_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(project_root),
        env=env
    )
    
    stdout, stderr = await process.communicate()
    
    print(f"Exit code: {process.returncode}")
    print(f"STDOUT: {stdout.decode()}")
    print(f"STDERR: {stderr.decode()}")

if __name__ == "__main__":
    asyncio.run(test_cmd())
