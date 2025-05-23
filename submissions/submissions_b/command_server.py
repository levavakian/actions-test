#!/usr/bin/env python3
"""
Command server that runs in the isolated container.
Executes commands and returns results with proper delimiters.
"""

import os
import subprocess
import json
import sys
import time
import uuid

COMMAND_PIPE = "/shared/command_pipe"
RESPONSE_PIPE = "/shared/response_pipe"

def ensure_pipes():
    """Create named pipes if they don't exist"""
    for pipe in [COMMAND_PIPE, RESPONSE_PIPE]:
        if not os.path.exists(pipe):
            os.mkfifo(pipe)

def execute_command(command):
    """Execute a command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "error": None
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Command timed out after 30 seconds",
            "returncode": -1,
            "error": "timeout"
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "error": "exception"
        }

def main():
    ensure_pipes()
    print("Command server started", flush=True)
    
    while True:
        try:
            # Read command from pipe
            with open(COMMAND_PIPE, 'r') as f:
                request = f.readline().strip()
            
            if not request:
                continue
            
            # Parse the request
            try:
                req_data = json.loads(request)
                request_id = req_data.get("id", str(uuid.uuid4()))
                command = req_data.get("command", "")
            except json.JSONDecodeError:
                # Backward compatibility: treat as raw command
                request_id = str(uuid.uuid4())
                command = request
            
            print(f"Executing command: {command}", flush=True)
            
            # Execute the command
            result = execute_command(command)
            
            # Prepare response
            response = {
                "id": request_id,
                "command": command,
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "returncode": result["returncode"],
                "error": result["error"],
                "timestamp": time.time()
            }
            
            # Write response with delimiter
            with open(RESPONSE_PIPE, 'w') as f:
                f.write(json.dumps(response) + "\n###END###\n")
                f.flush()
                
        except KeyboardInterrupt:
            print("Server shutting down", flush=True)
            break
        except Exception as e:
            print(f"Server error: {e}", flush=True)
            # Try to send error response
            try:
                error_response = {
                    "id": "error",
                    "command": "unknown",
                    "stdout": "",
                    "stderr": f"Server error: {str(e)}",
                    "returncode": -1,
                    "error": "server_error",
                    "timestamp": time.time()
                }
                with open(RESPONSE_PIPE, 'w') as f:
                    f.write(json.dumps(error_response) + "\n###END###\n")
                    f.flush()
            except:
                pass

if __name__ == "__main__":
    main()