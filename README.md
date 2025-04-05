# VisoLearn Local Interface

A local Python web interface that mirrors the functionality of the private VisoLearn Gradio application hosted on Hugging Face Spaces. This interface allows you to interact with the hosted Gradio app's API using the `gradio_client` library, providing a local experience while leveraging the remote AI capabilities.

## Features

- Generate educational images for children with autism
- Multiple image styles (Realistic, Illustration, Cartoon, Watercolor, 3D Rendering)
- Interactive chat interface for describing images
- Progress tracking for identified details
- Customizable difficulty levels
- Session logging and image saving

## Requirements

- Python 3.8 or higher
- A Hugging Face account with access to the VisoLearn Space
- A Hugging Face API token with access permissions

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/autism-education.git
   cd autism-education
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   - Copy the `.env.example` file to `.env`
   - Add your Hugging Face token to the `.env` file
   ```bash
   cp .env.example .env
   # Edit the .env file with your text editor
   ```

## Usage

There are multiple ways to run the application:

1. Using the provided run script (recommended):
   ```bash
   python run.py
   ```

2. Using the direct run script with `--no-gradio-queue` option:
   ```bash
   python run_direct.py
   ```

3. Using Streamlit directly:
   ```bash
   streamlit run app.py --server.port 5050
   ```

4. For connection issues, you can explicitly disable the Gradio queue:
   ```bash
   # Set environment variable
   export NO_GRADIO_QUEUE=1  # On Linux/macOS
   set NO_GRADIO_QUEUE=1     # On Windows cmd
   $env:NO_GRADIO_QUEUE=1    # On Windows PowerShell
   
   # Then run streamlit
   streamlit run app.py --server.port 5050
   ```

5. Open your web browser and navigate to:
   ```
   http://localhost:5050
   ```

6. Enter your Hugging Face token in the sidebar (if not already provided in the .env file)

7. Configure the child's information and education settings:
   - Child's Age
   - Autism Level (Level 1, 2, or 3)
   - Topic Focus
   - Treatment Plan
   - Allowed Attempts
   - Details Threshold
   - Image Style

8. Click "Generate Image" to create an educational image

9. Have the child describe what they see in the image, type their description in the text area, and click "Submit Description"

10. Continue the conversation to help them identify more details in the image

11. Save session logs and images as needed

## Troubleshooting

### Connection Issues

If you see an error like `Failed to initialize client: Failed to initialize VisoLearn client: Expecting value: line 1 column 1 (char 0)`, this typically indicates one of the following issues:

1. **Gradio Queue Issue (Most Common)**
   - This error often occurs due to Gradio's queuing system
   - Use one of the following solutions:
     - Run the application using `python run_direct.py`
     - Set the environment variable `NO_GRADIO_QUEUE=1` before running
     - Use the fallback mode in the UI if connection fails

2. **Missing or Invalid Hugging Face Token**:
   - Ensure you have provided a valid Hugging Face token
   - The token must have permission to access the private VisoLearn space
   - You can create or manage tokens at https://huggingface.co/settings/tokens

3. **Permission Issues**:
   - Make sure your token has read and execute permissions for the VisoLearn Space
   - If you see a 403 error, you don't have permission to access the space
   - Contact the space owner to request access

4. **Space Status**:
   - The Hugging Face Space might be sleeping or starting up
   - Click the "Validate" button to wake up the space
   - It may take up to 1-2 minutes for a sleeping space to become available

5. **Network Issues**:
   - Ensure you have a stable internet connection
   - Check if your firewall might be blocking the connection

### Fallback Mode

If you continue to have connection issues, you can enable the "Fallback Mode" in the sidebar, which provides a limited version of the application that works without API access.

### Debugging

1. Enable Debug Mode in the sidebar to see detailed error messages
2. Check your browser's developer console for additional errors
3. Try validating your token using the "Validate" button in the sidebar

## API Endpoints

The application connects to the following Gradio API endpoints:

- `/generate_image_and_reset_chat`: Generate a new image and reset the conversation
- `/chat_respond`: Process a user message and get AI feedback
- `/save_session_log`: Save the current session log
- `/save_all_session_images`: Save all images from the current session
- `/update_checklist_html`: Get the HTML for the checklist of details to identify
- `/update_progress_html`: Get the HTML for the progress display
- `/update_attempt_counter`: Get the HTML for the attempt counter
- `/update_sessions`: Get the current sessions data
- `/update_difficulty_label`: Get the current difficulty label

## Customization

You can modify the following aspects of the application:

- Port number (in .env file or command line)
- UI appearance (in app.py)
- Default settings (in app.py)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- VisoLearn Gradio application by Compumacy
- Gradio for the client library
- Streamlit for the web interface framework 