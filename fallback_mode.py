import os
import base64
import json
import io
import random
from PIL import Image, ImageDraw, ImageFont

class FallbackMode:
    """
    Provides fallback functionality when the VisoLearn API is unavailable.
    This allows basic testing and UI interaction without the actual API.
    """
    
    @staticmethod
    def generate_placeholder_image(text="Placeholder Image", width=512, height=512, color=(240, 240, 240)):
        """
        Generate a simple placeholder image with text
        """
        try:
            # Create a blank image
            img = Image.new('RGB', (width, height), color=color)
            draw = ImageDraw.Draw(img)
            
            # Try to use a system font, fall back to default if not available
            try:
                # Different font paths for different operating systems
                if os.name == 'nt':  # Windows
                    font_path = "C:\\Windows\\Fonts\\Arial.ttf"
                elif os.name == 'posix':  # macOS or Linux
                    if os.path.exists("/System/Library/Fonts/Helvetica.ttc"):  # macOS
                        font_path = "/System/Library/Fonts/Helvetica.ttc"
                    else:  # Linux
                        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                else:
                    font_path = None
                
                if font_path and os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 30)
                else:
                    font = ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()
            
            # Draw border
            border_width = 10
            draw.rectangle([(border_width, border_width), 
                            (width - border_width, height - border_width)], 
                          outline=(180, 180, 180), width=border_width)
            
            # Add text
            text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (200, 30)
            position = ((width - text_width) // 2, (height - text_height) // 2)
            draw.text(position, text, fill=(100, 100, 100), font=font)
            
            # Add topic and style info if available
            if ":" in text:
                parts = text.split(":", 1)
                if len(parts) > 1:
                    topic = parts[1].strip()
                    draw.text((20, height - 60), f"Topic: {topic}", fill=(100, 100, 100), font=font)
            
            # Add disclaimer
            small_font = ImageFont.load_default()
            draw.text((20, height - 30), "FALLBACK MODE - API Unavailable", fill=(255, 0, 0), font=small_font)
            
            # Convert to data URL
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            data_url = f"data:image/png;base64,{img_str}"
            
            # Create a dict similar to what the API would return
            result = {
                'url': data_url,
                'path': None,
                'size': len(buffered.getvalue()),
                'mime_type': 'image/png',
                'is_stream': False
            }
            
            return result
        except Exception as e:
            print(f"Error generating placeholder image: {str(e)}")
            return None
    
    @staticmethod
    def generate_placeholder_checklist(topic="Unknown"):
        """
        Generate a placeholder checklist based on the topic
        """
        # Generic details that could apply to many images
        generic_details = [
            "Background color",
            "Main subject",
            "Foreground elements",
            "Lighting effects",
            "Shadows and highlights",
            "Texture patterns",
            "Color scheme"
        ]
        
        # Add topic-specific details if a topic is provided
        topic_details = []
        if topic and topic != "Unknown":
            topic_words = topic.lower().split()
            
            # Animals
            if any(word in topic_words for word in ["animal", "animals", "pet", "pets", "wildlife"]):
                topic_details = ["Animal type", "Animal posture", "Animal coloring", "Habitat elements", "Animal features"]
            
            # People
            elif any(word in topic_words for word in ["person", "people", "child", "children", "family"]):
                topic_details = ["Person's expression", "Clothing items", "Posture or pose", "Hair style", "Action being performed"]
            
            # Nature
            elif any(word in topic_words for word in ["nature", "landscape", "tree", "forest", "mountain", "ocean"]):
                topic_details = ["Type of landscape", "Plant life", "Weather conditions", "Time of day", "Natural features"]
            
            # Objects
            elif any(word in topic_words for word in ["object", "toy", "item", "tool"]):
                topic_details = ["Object shape", "Object purpose", "Object material", "Object size", "Object color"]
        
        # Combine generic and topic-specific details
        all_details = topic_details + generic_details
        
        # Select a random subset (between 5 and 8 items)
        num_details = min(len(all_details), random.randint(5, 8))
        selected_details = random.sample(all_details, num_details)
        
        # Create checklist items
        checklist = []
        for i, detail in enumerate(selected_details):
            checklist.append({
                "detail": detail,
                "identified": False,
                "id": i
            })
        
        return checklist
    
    @staticmethod
    def process_chat_message(message, checklist, active_session=None):
        """
        Process a chat message and update the checklist
        
        Args:
            message (str): The user's message
            checklist (list): The current checklist of items to identify
            active_session (dict, optional): The active session containing attempt limits
        
        Returns:
            tuple: (response message, updated checklist)
        """
        # Simple logic to update checklist based on message content
        updated_checklist = checklist.copy()
        
        # Check each detail against the message
        for i, item in enumerate(updated_checklist):
            # Don't process already identified items
            if item["identified"]:
                continue
                
            # Simple word matching (in a real system, this would be more sophisticated)
            detail_words = item["detail"].lower().split()
            message_lower = message.lower()
            
            # If any word from the detail is in the message, mark it as identified
            for word in detail_words:
                if len(word) > 3 and word in message_lower:  # Only check words longer than 3 chars
                    updated_checklist[i]["identified"] = True
                    break
        
        # Generate a simple response based on how many items were identified
        newly_identified = sum(1 for i, item in enumerate(updated_checklist) 
                              if item["identified"] and not checklist[i]["identified"])
        
        if newly_identified > 0:
            response = f"Great job! You identified {newly_identified} new detail{'s' if newly_identified > 1 else ''}."
            if newly_identified > 1:
                response += " Your observation skills are excellent!"
        else:
            # Hint about unidentified details
            unidentified = [item["detail"] for item in updated_checklist if not item["identified"]]
            if unidentified:
                hint_item = random.choice(unidentified)
                response = f"Good try! Can you tell me more about the {hint_item.lower()}?"
            else:
                response = "Wonderful! You've identified all the details in this image."
                
        # Add extra message if attempts are getting high but attempt_limit is specified
        if active_session and active_session.get("attempt_limit"):
            attempt_count = active_session.get("attempt_count", 0)
            attempt_limit = active_session.get("attempt_limit")
            
            # If this would be the last attempt before reaching the limit
            if attempt_count + 1 >= attempt_limit and not all(item["identified"] for item in updated_checklist):
                response += "\n\nThis is your last attempt. After this, we'll move to a new image."
        
        return response, updated_checklist
    
    @staticmethod
    def create_html_checklist(checklist):
        """
        Create HTML representation of the checklist
        """
        html = '<div id="checklist-container" style="background-color: #000000; color: #ffffff; padding: 15px; border-radius: 8px;">'
        html += '<style>.checklist-item {display: flex; align-items: center; margin-bottom: 10px; padding: 8px; border-radius: 5px; transition: background-color 0.3s;} '
        html += '.identified {background-color: #1e4620; text-decoration: line-through; color: #7fff7f;} '
        html += '.not-identified {background-color: #222222; color: #ffffff;} '
        html += '.checkmark {margin-right: 10px; font-size: 1.2em;}</style>'
        
        for item in checklist:
            detail = item["detail"]
            identified = item["identified"]
            css_class = "identified" if identified else "not-identified"
            checkmark = "✅" if identified else "❌"
            
            html += f'<div class="checklist-item {css_class}">'
            html += f'<span class="checkmark">{checkmark}</span>'
            html += f'<span>{detail}</span>'
            html += '</div>'
        
        html += '</div>'
        return html 