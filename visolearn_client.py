import os
import io
import base64
import json
import requests
import time
from PIL import Image
from gradio_client import Client

class VisoLearnClient:
    """
    Client for interacting with the VisoLearn Gradio API hosted on Hugging Face Spaces.
    Provides methods for all API endpoints available in the VisoLearn application.
    """
    
    def __init__(self, hf_token=None):
        """
        Initialize the client with authentication
        
        Args:
            hf_token (str): Hugging Face API token for authentication
        """
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        self.space_name = "Compumacy/VisoLearn"
        self.client = None
        self.initialized = self.initialize()
    
    def initialize(self):
        """Initialize the Gradio client with authentication"""
        if not self.hf_token:
            raise ValueError("Hugging Face token is required to access the VisoLearn API. Please add your token to the .env file or enter it in the application.")
        
        try:
            # First check if the Space is available
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            response = requests.get(
                f"https://huggingface.co/api/spaces/{self.space_name}/runtime",
                headers=headers
            )
            
            if response.status_code != 200:
                error_msg = f"Failed to connect to {self.space_name}. Status code: {response.status_code}"
                if response.status_code == 401:
                    error_msg += ". Invalid or unauthorized token. Please check your Hugging Face token."
                elif response.status_code == 404:
                    error_msg += ". Space not found. Check if the space name is correct."
                elif response.status_code == 403:
                    error_msg += ". You don't have permission to access this private space."
                raise ConnectionError(error_msg)
            
            # Check if the space is running
            status = response.json().get("stage")
            if status not in ["RUNNING", "RUNNING_BUILDING"]:
                # If space is sleeping, wake it up
                if status == "SLEEPING":
                    print(f"Space {self.space_name} is sleeping. Waking it up...")
                    wake_response = requests.post(
                        f"https://huggingface.co/api/spaces/{self.space_name}/wake",
                        headers=headers
                    )
                    if wake_response.status_code == 200:
                        # Wait for the space to wake up (max 60 seconds)
                        for _ in range(12):  # 12 * 5 seconds = 60 seconds
                            time.sleep(5)
                            status_response = requests.get(
                                f"https://huggingface.co/api/spaces/{self.space_name}/runtime",
                                headers=headers
                            )
                            if status_response.status_code == 200:
                                current_status = status_response.json().get("stage")
                                if current_status == "RUNNING":
                                    break
                    else:
                        raise ConnectionError(f"Failed to wake up the space {self.space_name}")
                else:
                    raise ConnectionError(f"Space {self.space_name} is not running. Current status: {status}")
            
            # Initialize the client
            try:
                self.client = Client(
                    self.space_name, 
                    hf_token=self.hf_token,
                    verbose=False
                )
                return True
            except Exception as e:
                raise ConnectionError(f"Failed to initialize Gradio client: {str(e)}")
                
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Network error when connecting to Hugging Face: {str(e)}")
        except json.JSONDecodeError as e:
            raise ConnectionError(f"Invalid response from Hugging Face API: {str(e)}")
        except Exception as e:
            raise ConnectionError(f"Failed to initialize VisoLearn client: {str(e)}")
    
    def _ensure_initialized(self):
        """Ensure client is initialized before making API calls"""
        if not self.client:
            self.initialized = self.initialize()
            if not self.initialized:
                raise ConnectionError("Client not initialized. Please check your Hugging Face token and connection.")
    
    def generate_image(self, age="3", autism_level="Level 1", topic_focus="", 
                      treatment_plan="", attempt_limit=3, details_threshold=70, 
                      image_style="Realistic"):
        """
        Generate an image based on the provided parameters
        
        Args:
            age (str): The child's age
            autism_level (str): Autism level (Level 1, 2, or 3)
            topic_focus (str): The topic to focus on
            treatment_plan (str): Treatment plan
            attempt_limit (int): Number of allowed attempts
            details_threshold (float): Threshold percentage for detail identification
            image_style (str): Style of image to generate
        
        Returns:
            dict: Image data and related information
        """
        self._ensure_initialized()
        
        try:
            result = self.client.predict(
                age,
                autism_level,
                topic_focus,
                treatment_plan,
                attempt_limit,
                details_threshold,
                image_style,
                api_name="/generate_image_and_reset_chat"
            )
            
            return result
        except Exception as e:
            raise RuntimeError(f"Error generating image: {str(e)}")
    
    def chat_respond(self, user_message):
        """
        Process a user message and get a response
        
        Args:
            user_message (str): The child's description of the image
        
        Returns:
            tuple: (text response, conversation history, image data)
        """
        self._ensure_initialized()
        
        try:
            result = self.client.predict(
                user_message,
                api_name="/chat_respond"
            )
            
            return result
        except Exception as e:
            raise RuntimeError(f"Error processing chat message: {str(e)}")
    
    def save_session_log(self):
        """
        Save the current session log
        
        Returns:
            str: Result message
        """
        self._ensure_initialized()
        
        try:
            result = self.client.predict(
                api_name="/save_session_log"
            )
            
            return result
        except Exception as e:
            raise RuntimeError(f"Error saving session log: {str(e)}")
    
    def save_all_session_images(self):
        """
        Save all images from the current session
        
        Returns:
            str: Result message
        """
        self._ensure_initialized()
        
        try:
            result = self.client.predict(
                api_name="/save_all_session_images"
            )
            
            return result
        except Exception as e:
            raise RuntimeError(f"Error saving session images: {str(e)}")
    
    def update_checklist(self):
        """
        Get the current checklist HTML
        
        Returns:
            str: HTML representation of the checklist
        """
        self._ensure_initialized()
        
        try:
            result = self.client.predict(
                api_name="/update_checklist_html"
            )
            
            return result
        except Exception as e:
            raise RuntimeError(f"Error updating checklist: {str(e)}")
    
    def update_progress(self):
        """
        Get the current progress HTML
        
        Returns:
            str: HTML representation of the progress
        """
        self._ensure_initialized()
        
        try:
            result = self.client.predict(
                api_name="/update_progress_html"
            )
            
            return result
        except Exception as e:
            raise RuntimeError(f"Error updating progress: {str(e)}")
    
    def update_attempt_counter(self):
        """
        Get the current attempt counter HTML
        
        Returns:
            str: HTML representation of the attempt counter
        """
        self._ensure_initialized()
        
        try:
            result = self.client.predict(
                api_name="/update_attempt_counter"
            )
            
            return result
        except Exception as e:
            raise RuntimeError(f"Error updating attempt counter: {str(e)}")
    
    def update_sessions(self):
        """
        Get the current sessions data
        
        Returns:
            dict: Session data
        """
        self._ensure_initialized()
        
        try:
            result = self.client.predict(
                api_name="/update_sessions"
            )
            
            return result
        except Exception as e:
            raise RuntimeError(f"Error updating sessions: {str(e)}")
    
    def update_difficulty_label(self):
        """
        Get the current difficulty label
        
        Returns:
            str: Difficulty label
        """
        self._ensure_initialized()
        
        try:
            result = self.client.predict(
                api_name="/update_difficulty_label"
            )
            
            return result
        except Exception as e:
            raise RuntimeError(f"Error updating difficulty label: {str(e)}")
    
    @staticmethod
    def process_data_url(data_url):
        """
        Process an image data URL and convert it to a PIL Image
        
        Args:
            data_url (str): The data URL containing the image data
        
        Returns:
            PIL.Image: The processed image
        """
        try:
            if data_url and data_url.startswith("data:image"):
                # Extract the base64 encoded image data
                base64_data = data_url.split(",")[1]
                # Decode the base64 data
                image_data = base64.b64decode(base64_data)
                # Create a PIL Image
                image = Image.open(io.BytesIO(image_data))
                return image
            return None
        except Exception as e:
            print(f"Error processing image data URL: {str(e)}")
            return None 