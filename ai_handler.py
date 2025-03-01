import google.generativeai as genai
from datetime import datetime, timedelta
import time
from config import API_KEYS
import random

class AIHandler:
    def __init__(self):
        self.current_key_index = 0
        self.key_status = {key: {"errors": 0, "last_error": None} for key in API_KEYS}
        self.initialize_api()
    
    def initialize_api(self):
        """Initialize the API with the current key"""
        if not API_KEYS:
            raise ValueError("No API keys available in .env file")
        genai.configure(api_key=API_KEYS[self.current_key_index])
        self.model = genai.GenerativeModel('gemini-pro')
    
    def get_next_valid_key(self):
        """Get the next valid API key"""
        original_index = self.current_key_index
        
        while True:
            # Move to next key
            self.current_key_index = (self.current_key_index + 1) % len(API_KEYS)
            
            # Check if we've tried all keys
            if self.current_key_index == original_index:
                # Reset error counts for keys that haven't had errors in the last hour
                current_time = datetime.now()
                for key in API_KEYS:
                    last_error = self.key_status[key]["last_error"]
                    if last_error and (current_time - last_error) > timedelta(hours=1):
                        self.key_status[key]["errors"] = 0
                        self.key_status[key]["last_error"] = None
                
                # Find key with least errors
                min_errors = min(self.key_status[key]["errors"] for key in API_KEYS)
                valid_keys = [
                    i for i, key in enumerate(API_KEYS)
                    if self.key_status[key]["errors"] == min_errors
                ]
                
                if valid_keys:
                    self.current_key_index = random.choice(valid_keys)
                    break
                else:
                    raise Exception("All API keys are experiencing issues. Please try again later.")
            
            # If this key has less than 5 errors in the last hour, use it
            current_key = API_KEYS[self.current_key_index]
            if self.key_status[current_key]["errors"] < 5:
                break
        
        return API_KEYS[self.current_key_index]
    
    def record_error(self, key):
        """Record an error for the given key"""
        self.key_status[key]["errors"] += 1
        self.key_status[key]["last_error"] = datetime.now()
    
    def create_chat(self, persona_prompt, temperature):
        """Create a chat session with error handling and key rotation"""
        max_retries = len(API_KEYS)
        current_retry = 0
        
        while current_retry < max_retries:
            try:
                current_key = API_KEYS[self.current_key_index]
                genai.configure(api_key=current_key)
                self.model = genai.GenerativeModel('gemini-pro')
                
                return self.model.start_chat(
                    context=persona_prompt,
                    generation_config={
                        "temperature": temperature,
                        "top_p": 0.8,
                        "top_k": 40,
                    }
                )
            
            except Exception as e:
                self.record_error(current_key)
                print(f"Error with API key {self.current_key_index + 1}: {str(e)}")
                
                try:
                    next_key = self.get_next_valid_key()
                    print(f"Switching to next API key...")
                    current_retry += 1
                except Exception as e:
                    raise Exception(f"All API keys failed: {str(e)}")
        
        raise Exception("Failed to create chat session with all available API keys")
    
    def generate_response(self, chat, message, history):
        """Generate response with error handling and key rotation"""
        max_retries = len(API_KEYS)
        current_retry = 0
        
        while current_retry < max_retries:
            try:
                current_key = API_KEYS[self.current_key_index]
                context = "\n".join([f"{h['role']}: {h['content']}" for h in history])
                prompt = f"{context}\nUser: {message}"
                
                response = chat.send_message(prompt)
                return response.text
            
            except Exception as e:
                self.record_error(current_key)
                print(f"Error with API key {self.current_key_index + 1}: {str(e)}")
                
                try:
                    next_key = self.get_next_valid_key()
                    print(f"Switching to next API key...")
                    current_retry += 1
                    
                    # Recreate chat session with new key
                    chat = self.create_chat(chat.context, chat.generation_config["temperature"])
                except Exception as e:
                    return f"Error: All API keys failed. Please try again later."
        
        return "Error: Failed to generate response with all available API keys"
