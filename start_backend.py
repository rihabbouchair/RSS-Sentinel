#!/usr/bin/env python3
"""
Start the backend server from the correct directory
"""
import os
import sys
import subprocess

# Change to backend directory
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

# Run uvicorn
subprocess.run(
	[sys.executable, '-m', 'uvicorn', 'main:app', '--reload', '--no-access-log'],
	cwd=os.getcwd(),
)
