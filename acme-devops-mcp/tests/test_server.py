import asyncio
import json
import subprocess
import sys

async def test_ping():
    # Start the server process
    process = subprocess.Popen(
        ["uv", "run", "--quiet", "acme-devops-mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    def send_message(msg):
        process.stdin.write(json.dumps(msg) + "\n")
        process.stdin.flush()

    def read_message():
        while True:
            line = process.stdout.readline()
            if not line:
                return None
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping non-JSON line: {line.strip()}", file=sys.stderr)
                continue

    try:
        # Step 1: Initialize Handshake
        print("Sending initialize request...")
        send_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        })
        init_response = read_message()
        print(f"Initialize Response: {json.dumps(init_response, indent=2)}")

        # Send initialized notification
        send_message({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        })

        # Step 2: List Tools
        print("\nListing tools...")
        send_message({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        })
        tools_response = read_message()
        print(f"Tools Response: {json.dumps(tools_response, indent=2)}")

        # Step 3: Call Ping Tool
        print("\nCalling ping tool...")
        send_message({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "ping",
                "arguments": {"message": "Hello MCP!"}
            }
        })
        call_response = read_message()
        print(f"Call Response: {json.dumps(call_response, indent=2)}")

    finally:
        stdout, stderr = process.communicate()
        if stderr:
            print(f"\nServer Stderr:\n{stderr}", file=sys.stderr)
        if stdout:
            print(f"\nRemaining Server Stdout:\n{stdout}")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_ping())
