#!/usr/bin/env python3
"""
Test script that calls the command client 5 times with different commands
and prints out the outputs with clear separation.
"""

import subprocess
import sys
import os

def run_command_client(command):
    """Run the command client with a given command"""
    print(f"\n{'='*60}")
    print(f"RUNNING COMMAND: {command}")
    print(f"{'='*60}")
    
    try:
        # Run the command client
        result = subprocess.run(
            [sys.executable, "agent/command_client.py", command],
            capture_output=True,
            text=True
        )
        
        print(f"Return Code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Error running command client: {e}")
    
    print(f"{'='*60}")

def main():
    """Main function to test the command client with 5 different commands"""
    
    print("Testing Command Client with 5 Different Commands")
    print("=" * 60)
    
    # List of 5 different commands to test
    commands = [
        "ls -la",                    # List files with details
        "pwd",                       # Print working directory
        "echo 'Hello from command client!'",  # Simple echo command
        "whoami",                    # Current user
        "date",                      # Current date and time
    ]
    
    for i, command in enumerate(commands, 1):
        print(f"\n[TEST {i}/5]")
        run_command_client(command)
        
        # Add a small delay between commands
        import time
        time.sleep(0.5)
    
    print(f"\n{'='*60}")
    print("All command client tests completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()