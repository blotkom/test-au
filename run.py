import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get port from environment or use default
port = os.environ.get("PORT", "5050")

def main():
    """
    Run the Streamlit application with the specified port
    """
    print(f"Starting VisoLearn Local Interface on port {port}...")
    
    # Set the NO_GRADIO_QUEUE environment variable to bypass Gradio's queue
    os.environ["NO_GRADIO_QUEUE"] = "1"
    
    # Command to run Streamlit app
    command = [
        "streamlit", "run", "app.py",
        "--server.port", port,
        "--server.address", "0.0.0.0"  # Listen on all interfaces
    ]
    
    try:
        # Run the command
        process = subprocess.run(command)
        return process.returncode
    except KeyboardInterrupt:
        print("\nShutting down...")
        return 0
    except Exception as e:
        print(f"Error running Streamlit app: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 