import streamlit as st
import os
import io
import base64
import json
import datetime
import re
import traceback
from PIL import Image
from dotenv import load_dotenv
from visolearn_client import VisoLearnClient
from fallback_mode import FallbackMode

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="VisoLearn Local Interface",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get HF token from environment variables or let user input it
HF_TOKEN = os.environ.get("HF_TOKEN", "")
PORT = int(os.environ.get("PORT", 5050))

# Initialize session state variables if they don't exist
if "active_session" not in st.session_state:
    st.session_state.active_session = {
        "prompt": None,
        "image": None,
        "chat": [],
        "topic_focus": "",
        "treatment_plan": "",
        "key_details": [],
        "identified_details": [],
        "used_hints": [],
        "difficulty": "Very Simple",
        "autism_level": "Level 1",
        "age": "3",
        "attempt_count": 0,
        "attempt_limit": 3,
        "details_threshold": 70,
        "image_style": "Realistic"
    }

if "saved_sessions" not in st.session_state:
    st.session_state.saved_sessions = []

if "checklist" not in st.session_state:
    st.session_state.checklist = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "generated_image" not in st.session_state:
    st.session_state.generated_image = None

if "client" not in st.session_state:
    st.session_state.client = None

if "is_connected" not in st.session_state:
    st.session_state.is_connected = False

if "connection_error" not in st.session_state:
    st.session_state.connection_error = None

if "hf_token" not in st.session_state:
    st.session_state.hf_token = HF_TOKEN
    
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

if "fallback_mode" not in st.session_state:
    st.session_state.fallback_mode = False

# Function to extract details from HTML content
def extract_checklist_from_html(html_content):
    """
    Extract checklist items from HTML content returned by the API
    """
    checklist = []
    if not html_content:
        return checklist
    
    # Use regex to find checklist items
    pattern = r'<div class="checklist-item ([^"]+)">\s*<span class="checkmark">([^<]+)</span>\s*<span>([^<]+)</span>\s*</div>'
    matches = re.findall(pattern, html_content)
    
    for i, match in enumerate(matches):
        css_class, checkmark, detail = match
        identified = "identified" in css_class
        checklist.append({"detail": detail, "identified": identified, "id": i})
    
    return checklist

# Function to initialize Gradio client
def initialize_client():
    if not st.session_state.hf_token:
        st.error("⚠️ Hugging Face token is required. Please enter your token in the sidebar.")
        st.session_state.connection_error = "Missing Hugging Face token"
        st.session_state.is_connected = False
        return False
    
    try:
        st.session_state.client = VisoLearnClient(hf_token=st.session_state.hf_token)
        st.session_state.is_connected = True
        st.session_state.connection_error = None
        st.session_state.fallback_mode = False
        return True
    except Exception as e:
        detailed_error = str(e)
        st.session_state.connection_error = detailed_error
        st.session_state.is_connected = False
        
        error_message = "⚠️ Failed to connect to VisoLearn API"
        if "403" in detailed_error:
            error_message += ": You don't have permission to access this private space. Please check that your token has the correct permissions."
        elif "401" in detailed_error:
            error_message += ": Invalid or unauthorized token. Please check your Hugging Face token."
        elif "404" in detailed_error:
            error_message += ": Space not found. The VisoLearn space may have been moved or renamed."
        elif "sleeping" in detailed_error.lower():
            error_message += ": The space is sleeping. Trying to wake it up, please wait a moment and try again."
        elif "not running" in detailed_error.lower():
            error_message += ": The space is not running. Please wait a moment and try again."
        else:
            error_message += f": {detailed_error}"
            
        st.error(error_message)
        
        if st.session_state.debug_mode:
            st.expander("Detailed Error").code(traceback.format_exc())
            
        return False

# Function to toggle fallback mode
def toggle_fallback_mode():
    st.session_state.fallback_mode = not st.session_state.fallback_mode
    
    if st.session_state.fallback_mode:
        st.session_state.is_connected = False
        st.info("Fallback mode enabled. Using local functionality without API connection.")
    else:
        # Try to reconnect
        initialize_client()

# Function to generate image
def generate_image():
    if st.session_state.fallback_mode:
        # Use fallback mode to generate a placeholder image
        image_text = f"Sample Image: {st.session_state.topic_focus}" if st.session_state.topic_focus else "Sample Image"
        result = FallbackMode.generate_placeholder_image(text=image_text)
        
        if result:
            st.session_state.generated_image = result
            
            # Update active session
            st.session_state.active_session = {
                "prompt": "Generated placeholder image (fallback mode)",
                "image": result.get('url', None),
                "chat": [],
                "topic_focus": st.session_state.topic_focus,
                "treatment_plan": st.session_state.treatment_plan,
                "key_details": [],
                "identified_details": [],
                "used_hints": [],
                "difficulty": "Very Simple",
                "autism_level": st.session_state.autism_level,
                "age": st.session_state.age,
                "attempt_count": 0,
                "attempt_limit": int(st.session_state.attempt_limit),
                "details_threshold": float(st.session_state.details_threshold),
                "image_style": st.session_state.image_style
            }
            
            # Create a placeholder checklist
            st.session_state.checklist = FallbackMode.generate_placeholder_checklist(st.session_state.topic_focus)
            
            # Clear conversation history
            st.session_state.conversation_history = []
            
            return True
    else:
        # Try to use the API
        if not initialize_client():
            # If API connection fails, ask if user wants to use fallback mode
            if st.sidebar.button("Use Fallback Mode Instead"):
                st.session_state.fallback_mode = True
                generate_image()  # Call this function again with fallback mode enabled
            return False
        
        with st.spinner("Generating image... This may take a minute."):
            try:
                result = st.session_state.client.generate_image(
                    age=st.session_state.age,
                    autism_level=st.session_state.autism_level,
                    topic_focus=st.session_state.topic_focus,
                    treatment_plan=st.session_state.treatment_plan,
                    attempt_limit=st.session_state.attempt_limit,
                    details_threshold=st.session_state.details_threshold,
                    image_style=st.session_state.image_style
                )
                
                if result and isinstance(result, dict):
                    st.session_state.generated_image = result
                    
                    # Update active session
                    st.session_state.active_session = {
                        "prompt": "Generated image",
                        "image": result.get('url', None),
                        "chat": [],
                        "topic_focus": st.session_state.topic_focus,
                        "treatment_plan": st.session_state.treatment_plan,
                        "key_details": [],
                        "identified_details": [],
                        "used_hints": [],
                        "difficulty": "Very Simple",
                        "autism_level": st.session_state.autism_level,
                        "age": st.session_state.age,
                        "attempt_count": 0,
                        "attempt_limit": int(st.session_state.attempt_limit),
                        "details_threshold": float(st.session_state.details_threshold),
                        "image_style": st.session_state.image_style
                    }
                    
                    # Update checklist
                    update_checklist()
                    
                    # Clear conversation history
                    st.session_state.conversation_history = []
                    
                    return True
                else:
                    st.error("Failed to generate image. The API returned an invalid response.")
                    if st.session_state.debug_mode:
                        st.write("API Response:", result)
                    return False
            except Exception as e:
                st.error(f"Error generating image: {str(e)}")
                if st.session_state.debug_mode:
                    st.expander("Detailed Error").code(traceback.format_exc())
                
                # Offer fallback mode
                if st.sidebar.button("Use Fallback Mode Instead"):
                    st.session_state.fallback_mode = True
                    generate_image()  # Call this function again with fallback mode enabled
                
                return False

# Function to update checklist
def update_checklist():
    if st.session_state.fallback_mode:
        # In fallback mode, we've already created the checklist when generating the image
        return
    
    if not initialize_client():
        return
    
    try:
        # Get checklist data from the API
        html_content = st.session_state.client.update_checklist()
        
        # Extract checklist items from HTML
        st.session_state.checklist = extract_checklist_from_html(html_content)
        
        # If no items extracted, create placeholder items
        if not st.session_state.checklist and st.session_state.active_session and st.session_state.active_session["image"]:
            # Placeholder items
            st.session_state.checklist = [
                {"detail": "Object in image", "identified": False, "id": 0},
                {"detail": "Color", "identified": False, "id": 1},
                {"detail": "Shape", "identified": False, "id": 2},
                {"detail": "Background", "identified": False, "id": 3}
            ]
    except Exception as e:
        st.error(f"Error updating checklist: {str(e)}")
        if st.session_state.debug_mode:
            st.expander("Detailed Error").code(traceback.format_exc())

# Function to update progress
def update_progress():
    if not st.session_state.checklist:
        return "No active session or no details to identify."
    
    try:
        # Try to get progress HTML from API if connected
        if st.session_state.is_connected and not st.session_state.fallback_mode:
            try:
                progress_html = st.session_state.client.update_progress()
            except:
                progress_html = None
        else:
            progress_html = None
            
        # Fall back to local calculation if API call fails or not connected
        total_items = len(st.session_state.checklist)
        identified_items = sum(1 for item in st.session_state.checklist if item["identified"])
        percentage = (identified_items / total_items) * 100 if total_items > 0 else 0
        
        return f"Progress: {identified_items}/{total_items} details ({percentage:.1f}%)"
    except Exception as e:
        if st.session_state.debug_mode:
            st.warning(f"Error updating progress: {str(e)}")
        # Fallback if everything fails
        return "Progress tracking unavailable"

# Function to process chat message
def process_chat_message():
    if st.session_state.fallback_mode:
        # Process message using fallback mode
        if not st.session_state.message or not st.session_state.message.strip():
            st.warning("Please enter a description first")
            return
        
        user_message = st.session_state.message.strip()
        
        # Process the message using the fallback logic
        response, updated_checklist = FallbackMode.process_chat_message(
            user_message, 
            st.session_state.checklist,
            st.session_state.active_session  # Pass the active session
        )
        
        # Update the checklist
        st.session_state.checklist = updated_checklist
        
        # Add messages to conversation history
        st.session_state.conversation_history.append(("Child", user_message))
        st.session_state.conversation_history.append(("Teacher", response))
        
        # Update active session - handle attempt count
        attempt_count = st.session_state.active_session.get("attempt_count", 0)
        attempt_limit = st.session_state.active_session.get("attempt_limit", 3)
        
        # Increment attempt count but don't exceed limit
        if attempt_count < attempt_limit:
            st.session_state.active_session["attempt_count"] = attempt_count + 1
        
        # Clear the message input
        st.session_state.message = ""
        
        return
    
    # Normal API-based processing
    if not initialize_client():
        return
    
    if not st.session_state.message or not st.session_state.message.strip():
        st.warning("Please enter a description first")
        return
    
    user_message = st.session_state.message.strip()
    
    with st.spinner("Processing response... This may take a moment."):
        try:
            result = st.session_state.client.chat_respond(user_message)
            
            if result and isinstance(result, tuple) and len(result) >= 2:
                # Extract data from result
                ai_response = result[0]
                conversation = result[1] if len(result) > 1 else None
                image_data = result[2] if len(result) > 2 else None
                
                # Add messages to conversation history
                st.session_state.conversation_history.append(("Child", user_message))
                st.session_state.conversation_history.append(("Teacher", ai_response))
                
                # Update active session - handle attempt count
                attempt_count = st.session_state.active_session.get("attempt_count", 0)
                attempt_limit = st.session_state.active_session.get("attempt_limit", 3)
                
                # Increment attempt count but don't exceed limit
                if attempt_count < attempt_limit:
                    st.session_state.active_session["attempt_count"] = attempt_count + 1
                
                # Clear the message input
                st.session_state.message = ""
                
                # Update checklist based on response
                update_checklist()
                
                # Update image if a new one is returned
                if image_data and 'url' in image_data:
                    st.session_state.generated_image = image_data
                    st.session_state.active_session["image"] = image_data.get('url')
            else:
                st.error("Failed to process chat. The API returned an invalid response.")
                if st.session_state.debug_mode:
                    st.write("API Response:", result)
        except Exception as e:
            st.error(f"Error processing chat: {str(e)}")
            if st.session_state.debug_mode:
                st.expander("Detailed Error").code(traceback.format_exc())
            
            # Offer fallback mode
            if st.sidebar.button("Switch to Fallback Mode"):
                st.session_state.fallback_mode = True
                # Re-process the message in fallback mode
                st.session_state.message = user_message
                process_chat_message()

# Function to save session log
def save_session_log():
    if st.session_state.fallback_mode:
        st.warning("Session log saving is not available in fallback mode.")
        return
    
    if not initialize_client():
        return
    
    with st.spinner("Saving session log..."):
        try:
            result = st.session_state.client.save_session_log()
            st.success("✅ Session log saved successfully")
        except Exception as e:
            st.error(f"Error saving session log: {str(e)}")
            if st.session_state.debug_mode:
                st.expander("Detailed Error").code(traceback.format_exc())

# Function to save images
def save_session_images():
    if st.session_state.fallback_mode:
        st.warning("Session image saving is not available in fallback mode.")
        return
    
    if not initialize_client():
        return
    
    with st.spinner("Saving session images..."):
        try:
            result = st.session_state.client.save_all_session_images()
            st.success("✅ Session images saved successfully")
        except Exception as e:
            st.error(f"Error saving session images: {str(e)}")
            if st.session_state.debug_mode:
                st.expander("Detailed Error").code(traceback.format_exc())

# Toggle debug mode
def toggle_debug_mode():
    st.session_state.debug_mode = not st.session_state.debug_mode

# Function to validate token
def validate_token():
    initialize_client()

# Sidebar for configuration
with st.sidebar:
    st.title("VisoLearn Local Interface")
    
    # Token input with validation (only show if not in fallback mode)
    if not st.session_state.fallback_mode:
        token_col1, token_col2 = st.columns([3, 1])
        with token_col1:
            st.session_state.hf_token = st.text_input("Hugging Face Token", 
                                                    value=st.session_state.hf_token, 
                                                    type="password",
                                                    placeholder="Enter your token here")
        with token_col2:
            st.button("Validate", on_click=validate_token)
        
        # Connection status indicator
        if st.session_state.is_connected:
            st.success("✅ Connected to VisoLearn API")
        elif st.session_state.connection_error:
            st.error(f"❌ Connection Error: {st.session_state.connection_error}")
            
            # Provide specific help based on the error
            if "403" in str(st.session_state.connection_error):
                st.info("💡 This is likely a permissions issue. Make sure your token has access to the VisoLearn space.")
            elif "401" in str(st.session_state.connection_error):
                st.info("💡 Your token appears to be invalid. Please check it and try again.")
            elif "sleeping" in str(st.session_state.connection_error).lower():
                st.info("💡 The space is sleeping. Try clicking the Validate button again to wake it up.")
        
        if not st.session_state.hf_token:
            st.warning("⚠️ Please enter your Hugging Face token")
    else:
        st.warning("⚠️ FALLBACK MODE: Running without API connection")
        
    # Fallback mode toggle
    st.checkbox("Use Fallback Mode", value=st.session_state.fallback_mode, on_change=toggle_fallback_mode)
    
    # Child's information section
    st.header("Child's Information")
    st.session_state.age = st.text_input("Child's Age", value="3")
    st.session_state.autism_level = st.selectbox(
        "Autism Level",
        options=["Level 1", "Level 2", "Level 3"],
        index=0
    )
    
    # Education settings section
    st.header("Education Settings")
    st.session_state.topic_focus = st.text_input("Topic Focus", placeholder="Enter a specific topic...")
    st.session_state.treatment_plan = st.text_area("Treatment Plan", placeholder="Enter the treatment plan...")
    st.session_state.attempt_limit = st.number_input("Allowed Attempts", min_value=1, max_value=10, value=3, step=1)
    st.session_state.details_threshold = st.slider("Details Threshold (%)", min_value=10, max_value=100, value=70, step=5)
    st.session_state.image_style = st.selectbox(
        "Image Style",
        options=["Realistic", "Illustration", "Cartoon", "Watercolor", "3D Rendering"],
        index=0
    )
    
    # Generate image button
    if st.session_state.fallback_mode:
        st.button("Generate Placeholder Image", on_click=generate_image)
    else:
        st.button("Generate Image", on_click=generate_image, disabled=not st.session_state.hf_token)
    
    st.divider()
    
    # Save buttons (disabled in fallback mode)
    col1, col2 = st.columns(2)
    with col1:
        st.button("Save Log", on_click=save_session_log, disabled=not st.session_state.is_connected or st.session_state.fallback_mode)
    with col2:
        st.button("Save Images", on_click=save_session_images, disabled=not st.session_state.is_connected or st.session_state.fallback_mode)
    
    # Debug mode toggle at the bottom of sidebar
    st.divider()
    st.checkbox("Debug Mode", value=st.session_state.debug_mode, on_change=toggle_debug_mode)

# Main content
st.title("VisoLearn Educational Tool")

# Display fallback mode banner if enabled
if st.session_state.fallback_mode:
    st.warning("📢 **FALLBACK MODE ENABLED**: Running with limited functionality without API connection. Some features are simulated locally.")

# Display connection warning if needed
elif not st.session_state.is_connected and st.session_state.hf_token:
    st.warning("⚠️ Not connected to the VisoLearn API. Some features will be unavailable. Check your token and connection or enable fallback mode in the sidebar.")

# Display active image
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Generated Image")
    if st.session_state.generated_image:
        if 'url' in st.session_state.generated_image and st.session_state.generated_image['url']:
            url = st.session_state.generated_image['url']
            if url.startswith('data:image'):
                image = VisoLearnClient.process_data_url(url)
                if image:
                    st.image(image, use_container_width=True)
                else:
                    st.error("Could not display the image. The image data may be corrupted.")
            else:
                try:
                    st.image(url, use_container_width=True)
                except Exception as e:
                    st.error(f"Could not load image from URL: {str(e)}")
    else:
        st.info("Generate an image to start the session")
    
    # Chat interface
    st.header("Child's Description")
    message_input = st.text_area("Type what the child says about the image...", key="message")
    st.button("Submit Description", on_click=process_chat_message, disabled=not (st.session_state.is_connected or st.session_state.fallback_mode) or not st.session_state.generated_image)
    
    # Display connection message if not connected and not in fallback mode
    if not st.session_state.is_connected and not st.session_state.fallback_mode:
        st.warning("⚠️ Please connect to the VisoLearn API or enable fallback mode to submit descriptions")
    
    # Display conversation history
    st.header("Conversation History")
    if st.session_state.conversation_history:
        for i, (speaker, message) in enumerate(st.session_state.conversation_history):
            if speaker == "Child":
                with st.container(border=True):
                    st.write(f"👧 **Child:** {message}")
            else:
                with st.container(border=True):
                    st.write(f"👩‍🏫 **Teacher:** {message}")
    else:
        st.info("No conversation yet. Generate an image and describe what you see.")

with col2:
    # Display details to identify
    st.header("Details to Identify")
    if st.session_state.checklist:
        for item in st.session_state.checklist:
            if item["identified"]:
                st.success(f"✅ {item['detail']}")
            else:
                st.warning(f"❌ {item['detail']}")
    else:
        st.info("Generate an image to see details to identify")
    
    # Progress tracking
    st.header("Progress")
    progress_container = st.container(border=True)
    with progress_container:
        progress_text = update_progress()
        st.write(progress_text)
        
        # Create a visual progress bar
        if st.session_state.checklist:
            total_items = len(st.session_state.checklist)
            identified_items = sum(1 for item in st.session_state.checklist if item["identified"])
            percentage = (identified_items / total_items) * 100 if total_items > 0 else 0
            # Cap the progress value at 100% (1.0) to avoid StreamlitAPIException
            progress_value = min(1.0, percentage / 100)
            st.progress(progress_value)
    
    # Attempt counter
    st.subheader("Attempts")
    attempt_container = st.container(border=True)
    with attempt_container:
        if "active_session" in st.session_state:
            attempt_count = st.session_state.active_session.get("attempt_count", 0)
            attempt_limit = st.session_state.active_session.get("attempt_limit", 3)
            
            # Cap the displayed attempt count to never exceed the limit
            display_count = min(attempt_count, attempt_limit)
            
            st.write(f"Attempts: {display_count}/{attempt_limit}")
            
            # Visual indicator for attempts - cap at 100%
            attempts_percentage = (display_count / attempt_limit) * 100 if attempt_limit > 0 else 0
            # Cap the progress value at 100% (1.0) to avoid StreamlitAPIException
            progress_value = min(1.0, attempts_percentage / 100)
            st.progress(progress_value, "Attempts used")
            
            # Show warning if limit is reached
            if attempt_count >= attempt_limit:
                # Check if not all items are identified
                if not all(item["identified"] for item in st.session_state.checklist):
                    st.warning("⚠️ Maximum attempts reached. The next interaction will move to a new image.")
        else:
            st.write("Attempts: 0/0")

# Session details section
st.header("Session Details")
if st.session_state.active_session:
    # Simplify the session data for display
    display_session = {
        "Difficulty": st.session_state.active_session.get("difficulty", "Very Simple"),
        "Topic Focus": st.session_state.active_session.get("topic_focus", ""),
        "Image Style": st.session_state.active_session.get("image_style", "Realistic"),
        "Autism Level": st.session_state.active_session.get("autism_level", "Level 1"),
        "Age": st.session_state.active_session.get("age", "3"),
        "Identified Details": len([item for item in st.session_state.checklist if item["identified"]]),
        "Total Details": len(st.session_state.checklist),
        "Fallback Mode": st.session_state.fallback_mode
    }
    st.json(display_session)
else:
    st.info("No active session")

# Add information about the app
with st.expander("About VisoLearn Local Interface"):
    st.markdown("""
    ## VisoLearn Local Interface
    
    This is a local interface for the VisoLearn educational tool hosted on Hugging Face Spaces. The application 
    helps children with autism practice describing images, with the system providing supportive feedback and 
    tracking their progress in identifying details.
    
    ### How to Use
    
    1. Enter your Hugging Face token in the sidebar for authentication
    2. Configure the child's information and education settings
    3. Click "Generate Image" to create an educational image
    4. Have the child describe what they see in the image
    5. Enter their description and click "Submit" for AI-powered feedback
    6. Continue the conversation to help them identify more details
    
    ### Fallback Mode
    
    If you cannot connect to the VisoLearn API, you can enable fallback mode to use a limited version 
    of the application with local functionality. In fallback mode:
    
    - Images are generated locally as placeholders
    - Checklist items are simplified
    - Chat responses are handled locally with basic logic
    - Session saving is disabled
    
    Fallback mode allows you to test the interface and demonstrate the concept without API access.
    
    ### Features
    
    - Customizable difficulty levels
    - Various image styles (Realistic, Cartoon, Illustration, etc.)
    - Progress tracking
    - Session logging
    
    Made with ❤️ for children with autism
    """)

# Add troubleshooting section
with st.expander("Troubleshooting"):
    st.markdown("""
    ## Troubleshooting Connection Issues
    
    If you're having trouble connecting to the VisoLearn API, try these steps:
    
    1. **Check your Hugging Face token:**
       - Make sure you have entered a valid Hugging Face token
       - Verify that your token has access to the private "Compumacy/VisoLearn" space
       - You can create or view your tokens at https://huggingface.co/settings/tokens
    
    2. **Network Issues:**
       - Ensure you have a stable internet connection
       - Check if your firewall might be blocking the connection
    
    3. **Space Status:**
       - The Hugging Face Space might be sleeping or starting up
       - Click the "Validate" button to try to wake up the space
       - It may take up to 1-2 minutes for a sleeping space to become available
    
    4. **Permission Issues:**
       - If you see a 403 error, you don't have permission to access the space
       - Contact the space owner to request access
    
    5. **Use Fallback Mode:**
       - If you can't resolve connection issues, enable "Fallback Mode" in the sidebar
       - This allows you to use a limited version of the application without API access
    
    6. **Still Having Issues?**
       - Enable Debug Mode in the sidebar to see detailed error messages
       - Take a screenshot of the error and contact support
    """)

# Run the Streamlit app on specified port
# Note: This will be handled by the streamlit command with the --server.port parameter 