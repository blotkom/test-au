#!/usr/bin/env python
"""
Direct script to run the VisoLearn local interface with the --no-gradio-queue option.
This bypasses the Gradio queue system which might be causing the "Expecting value" error.
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Hugging Face token
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Get port from environment or use default
PORT = os.environ.get("PORT", "5050")

# Check if token is provided
if not HF_TOKEN:
    print("Warning: No Hugging Face token found in environment variables.")
    print("You'll need to provide your token in the application UI.")

# Set the NO_GRADIO_QUEUE environment variable
os.environ["NO_GRADIO_QUEUE"] = "1"

# Run the gradio client with --no-gradio-queue
# This command directly uses the gradio_client with the option
cmd = [
    sys.executable, "-c",
    """
from gradio_client import Client
print("Initializing with --no-gradio-queue option...")
try:
    # Test connection to verify the flag works
    client = Client(
        "Compumacy/VisoLearn", 
        hf_token="%s",
        no_queue=True
    )
    print("Successfully initialized client with --no-gradio-queue")
except Exception as e:
    print(f"Error initializing client: {str(e)}")
    """ % HF_TOKEN
]

try:
    # Test the gradio_client first
    print("Testing gradio_client connection...")
    subprocess.run(cmd, check=False)
    
    print(f"\nStarting the VisoLearn interface on port {PORT}...")
    # Start the Streamlit app
    streamlit_cmd = [
        "streamlit", "run", "app.py",
        "--server.port", PORT,
        "--server.address", "0.0.0.0"
    ]
    subprocess.run(streamlit_cmd)
    
except KeyboardInterrupt:
    print("\nShutting down...")
    sys.exit(0)
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1) 