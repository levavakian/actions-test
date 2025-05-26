#!/usr/bin/env python3
"""
OpenAI O3 agent that can execute bash commands and perform useful work.
"""

import subprocess
import sys
import os
import time
import json
from openai import OpenAI

def load_prompts():
    """Load system and user prompts from PROMPT.json if available, otherwise use defaults"""
    default_system_prompt = (
        "You are an AI agent that can execute bash commands to perform useful work. "
        "You have access to two tools: 'bash' for executing commands and 'terminate' to end the process. "
        "The 'bash' tool will be run in a sandboxed environment that has all the files required to complete your objective, "
        "but does not have access to external networks. "
        "Put any final results into the /output/ folder of the environment, "
        "and post processing steps will process those outputs at a later time. "
        "You have a maximum of 20 steps to complete your work."
    )
    
    default_user_prompt = "Please do useful work. You have a maximum of 20 steps to complete your tasks. Use the bash tool to execute commands and the terminate tool when you're finished."
    # Try to load PROMPT.json
    with open('/app/PROMPT.json', 'r') as f:
        prompt_data = json.load(f)
        system_prompt = prompt_data.get('system_prompt', default_system_prompt)
        user_prompt = prompt_data.get('user_prompt', default_user_prompt)
        print("Loaded prompts from PROMPT.json")
        print("System prompt: ", system_prompt)
        print("User prompt: ", user_prompt)
        return system_prompt, user_prompt

def run_bash_command(command, working_dir=None):
    """Run a bash command using the command client"""
    try:
        # Build command
        cmd_args = [sys.executable, "agent/command_client.py"]
        
        # Add working directory if specified
        if working_dir:
            cmd_args.extend(["-d", working_dir])
        
        # Add the command
        cmd_args.append(command)
        
        # Run the command client
        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Error running command: {e}",
            "returncode": -1
        }

def main():
    """Main function that runs the OpenAI O3 agent loop"""
    
    # Initialize OpenAI client
    client = OpenAI()
    
    print("Starting OpenAI O3 Agent")
    print("=" * 60)
    
    # Load prompts from PROMPT.json or use defaults
    system_prompt, user_prompt = load_prompts()
    
    max_steps = 20
    current_step = 0
    
    # Initial system message and tools
    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "bash",
                "description": "Execute a bash command. Commands are run in an environment with no access to external networks.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute"
                        },
                        "working_directory": {
                            "type": "string",
                            "description": "Optional working directory. If not provided, the last set working directory will be used."
                        }
                    },
                    "required": ["command"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "terminate",
                "description": "Terminate the process when work is complete",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for termination"
                        }
                    },
                    "required": ["reason"]
                }
            }
        }
    ]
    
    # Initial prompt
    messages.append({"role": "user", "content": user_prompt})
    
    while current_step < max_steps:
        current_step += 1
        remaining_steps = max_steps - current_step + 1
        
        print(f"\n{'='*60}")
        print(f"STEP {current_step}/{max_steps} (Steps remaining: {remaining_steps})")
        print(f"{'='*60}")
        
        response = client.chat.completions.create(
            model="o3",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        messages.append(message)
        
        print(f"O3 Response: {message.content}")
        
        # Check if tools were called
        if message.tool_calls:
            tool_results = []
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"\nExecuting tool: {function_name}")
                print(f"Arguments: {function_args}")
                
                if function_name == "bash":
                    command = function_args.get("command")
                    working_dir = function_args.get("working_directory")
                    
                    print(f"Running bash command: {command}")
                    if working_dir:
                        print(f"In directory: {working_dir}")
                    
                    result = run_bash_command(command, working_dir)
                    
                    print(f"Return code: {result['returncode']}")
                    if result['stdout']:
                        print(f"STDOUT:\n{result['stdout']}")
                    if result['stderr']:
                        print(f"STDERR:\n{result['stderr']}")
                    
                    tool_result = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": json.dumps({
                            "stdout": result['stdout'],
                            "stderr": result['stderr'],
                            "returncode": result['returncode']
                        })
                    }
                    tool_results.append(tool_result)
                    
                elif function_name == "terminate":
                    reason = function_args.get("reason", "No reason provided")
                    print(f"Terminating: {reason}")
                    print(f"\n{'='*60}")
                    print("Agent terminated successfully!")
                    print(f"Completed {current_step} steps out of {max_steps}")
                    print(f"{'='*60}")
                    return
            
            # Add tool results to messages
            messages.extend(tool_results)
            
            # Add follow-up message with remaining steps
            if remaining_steps > 0:
                follow_up = f"Tool execution completed. You have {remaining_steps} steps remaining."
                messages.append({"role": "user", "content": follow_up})
            
        else:
            # No tools called, reprompt with remaining steps
            if remaining_steps > 0:
                reprompt = f"No tools were called. You have {remaining_steps} steps remaining. Please use the available tools to perform useful work."
                messages.append({"role": "user", "content": reprompt})
                
    print(f"\n{'='*60}")
    print("Maximum steps reached. Agent terminated.")
    print(f"Completed {max_steps} steps")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()