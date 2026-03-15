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
        print(f"Ping Response: {json.dumps(call_response, indent=2)}")

        # Step 4: Call get_deployment_status
        print("\nCalling get_deployment_status...")
        send_message({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_deployment_status",
                "arguments": {"environment": "prod"}
            }
        })
        status_response = read_message()
        print(f"Status Response: {json.dumps(status_response, indent=2)}")

        # Step 5: Call check_environment_health
        print("\nCalling check_environment_health...")
        send_message({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "check_environment_health",
                "arguments": {"application": "web-app"}
            }
        })
        health_response = read_message()
        print(f"Health Response: {json.dumps(health_response, indent=2)}")

        # Step 6: Call list_recent_releases
        print("\nCalling list_recent_releases...")
        send_message({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "list_recent_releases",
                "arguments": {"limit": 2}
            }
        })
        releases_response = read_message()
        print(f"Releases Response: {json.dumps(releases_response, indent=2)}")

        # Step 7: Call promote_release
        print("\nCalling promote_release...")
        send_message({
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "promote_release",
                "arguments": {
                    "applicationId": "web-app",
                    "version": "v2.1.3",
                    "fromEnvironment": "prod",
                    "toEnvironment": "uat"
                }
            }
        })
        promote_response = read_message()
        print(f"Promote Response: {json.dumps(promote_response, indent=2)}")

        # Step 8: Call list-releases (subprocess)
        print("\nCalling list-releases...")
        send_message({
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "list-releases",
                "arguments": {"limit": 1}
            }
        })
        list_releases_response = read_message()
        print(f"List Releases (Subprocess) Response: {json.dumps(list_releases_response, indent=2)}")

        # Step 9: Call check-health (subprocess)
        print("\nCalling check-health...")
        send_message({
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "check-health",
                "arguments": {"env": "prod"}
            }
        })
        check_health_response = read_message()
        print(f"Check Health (Subprocess) Response: {json.dumps(check_health_response, indent=2)}")

    except Exception as e:
        print(f"Error during test: {e}", file=sys.stderr)
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
