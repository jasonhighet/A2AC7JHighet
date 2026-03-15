
import os
from pathlib import Path
import sys

def verify():
    # Simulation of server.py path logic
    file_path = Path(r"e:\Github\HyprCourse\Project\acme-devops-mcp\src\acme_devops_mcp\server.py")
    
    print(f"File: {file_path}")
    print(f"P: {file_path.parent}")
    print(f"PP: {file_path.parent.parent}")
    print(f"PPP: {file_path.parent.parent.parent}")
    print(f"PPPP: {file_path.parent.parent.parent.parent}")
    
    project_root = file_path.resolve().parent.parent.parent.parent
    data_dir = project_root / "acme-devops-cli" / "data"
    
    print(f"Calculated project_root: {project_root}")
    print(f"Calculated data_dir: {data_dir}")
    print(f"Data dir exists: {data_dir.exists()}")
    
    if data_dir.exists():
        print("Contents of data_dir:")
        for f in data_dir.iterdir():
            print(f" - {f.name}")

if __name__ == "__main__":
    verify()
