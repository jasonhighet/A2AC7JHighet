import subprocess
import json
import sys
from pathlib import Path

def verify_ripgrep(executable_path: str, query: str, search_path: str):
    print(f"Verifying ripgrep at: {executable_path}")
    print(f"Searching for: '{query}' in: {search_path}")
    
    try:
        # Call ripgrep with JSON output
        result = subprocess.run(
            [executable_path, "--json", query, search_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            matches = []
            for line in lines:
                if not line:
                    continue
                data = json.loads(line)
                if data.get('type') == 'match':
                    matches.append({
                        'file': data['data']['path']['text'],
                        'line_number': data['data']['line_number'],
                        'match': data['data']['lines']['text'].strip()
                    })
            
            print(f"Found {len(matches)} matches.")
            for m in matches[:3]:
                print(f"  {m['file']}:{m['line_number']} - {m['match']}")
        else:
            print("No output received from ripgrep.")
            if result.stderr:
                print(f"Error: {result.stderr}")
                
    except Exception as e:
        print(f"Failed to invoke ripgrep: {str(e)}")

if __name__ == "__main__":
    # Path to rg.exe found earlier
    rg_path = r"C:\Users\jason\AppData\Local\Programs\Microsoft VS Code\cfbea10c5f\resources\app\node_modules\@vscode\ripgrep\bin\rg.exe"
    
    # Path to search (example)
    search_dir = r"e:\Github\HyprCourse\Project\incoming_data\feature1\planning"
    
    if not Path(rg_path).exists():
        print(f"ERROR: rg.exe not found at {rg_path}")
        sys.exit(1)
        
    if not Path(search_dir).exists():
        print(f"ERROR: Search directory not found at {search_dir}")
        sys.exit(1)
        
    verify_ripgrep(rg_path, "Maintenance", search_dir)
