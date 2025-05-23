#!/usr/bin/env python3
"""
Command client that runs in the controller container.
Sends commands and receives responses with proper synchronization.
"""

import os
import json
import sys
import uuid
import time

COMMAND_PIPE = "/shared/command_pipe"
RESPONSE_PIPE = "/shared/response_pipe"

def send_command(command, timeout=30):
    """Send a command and wait for the response"""
    request_id = str(uuid.uuid4())
    
    # Prepare request
    request = {
        "id": request_id,
        "command": command
    }
    
    # Send command
    with open(COMMAND_PIPE, 'w') as f:
        f.write(json.dumps(request) + "\n")
        f.flush()
    
    # Read response with delimiter
    response_text = ""
    start_time = time.time()
    
    with open(RESPONSE_PIPE, 'r') as f:
        while True:
            if time.time() - start_time > timeout:
                return {
                    "error": "Client timeout waiting for response",
                    "stdout": "",
                    "stderr": "Response timeout",
                    "returncode": -1
                }
            
            line = f.readline()
            if not line:
                time.sleep(0.01)
                continue
                
            response_text += line
            
            # Check for end delimiter
            if "###END###" in response_text:
                response_text = response_text.replace("###END###\n", "")
                break
    
    # Parse response
    try:
        response = json.loads(response_text.strip())
        
        # Verify this is our response
        if response.get("id") != request_id:
            return {
                "error": "Response ID mismatch",
                "stdout": "",
                "stderr": "Got response for different request",
                "returncode": -1
            }
        
        return response
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse response: {e}",
            "stdout": response_text,
            "stderr": "",
            "returncode": -1
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: command_client.py <command>")
        print("Example: command_client.py 'ls -la'")
        sys.exit(1)
    
    command = ' '.join(sys.argv[1:])
    
    # Send command and get response
    response = send_command(command)
    
    # Display results
    if response.get("stdout"):
        print(response["stdout"], end='')
    
    if response.get("stderr"):
        print(response["stderr"], file=sys.stderr, end='')
    
    if response.get("error"):
        print(f"\nError: {response['error']}", file=sys.stderr)
    
    # Exit with the same code as the command
    sys.exit(response.get("returncode", 0))

if __name__ == "__main__":
    main()