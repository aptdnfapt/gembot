import google.generativeai as genai
from datetime import datetime, timedelta
import time
import random
from config import API_KEYS, DEBUG_MODE
import sys
import traceback

class AIHandler:
    def __init__(self):
        self.current_key_index = 0
        self.key_status = {
            key: {
                "errors": 0,
                "last_error": None,
                "total_requests": 0,
                "last_request": None
            } for key in API_KEYS
        }
        self.startup_time = datetime.utcnow()
        print(f"AI Handler initialized at {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Number of API keys loaded: {len(API_KEYS)}")
        self.initialize_api()

    def log_error(self, message, error=None):
        """Log error messages with timestamp"""
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        error_message = f"[{current_time}] ERROR: {message}"
        if error and DEBUG_MODE:
            error_message += f"\n{traceback.format_exc()}"
        print(error_message, file=sys.stderr)

    def log_info(self, message):
        """Log info messages with timestamp"""
        if DEBUG_MODE:
            current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{current_time}] INFO: {message}")

    def initialize_api(self):
        """Initialize the API with the current key"""
        if not API_KEYS:
            raise ValueError("No API keys available in configuration")
        try:
            genai.configure(api_key=API_KEYS[self.current_key_index])
            self.model = genai.GenerativeModel('gemini-pro')
            self.log_info(f"Initialized with API key index {self.current_key_index}")
        except Exception as e:
            self.log_error("Failed to initialize API", e)
            raise

    def get_next_valid_key(self):
        """Get the next valid API key with improved error handling"""
        original_index = self.current_key_index
        current_time = datetime.utcnow()
        
        # Reset error counts for keys that haven't had errors in the last hour
        for key in API_KEYS:
            last_error = self.key_status[key]["last_error"]
            if last_error and (current_time - last_error) > timedelta(hours=1):
                self.key_status[key]["errors"] = 0
                self.key_status[key]["last_error"] = None
                self.log_info(f"Reset error count for key ending in ...{key[-4:]}")

        tried_keys = set()
        while len(tried_keys) < len(API_KEYS):
            self.current_key_index = (self.current_key_index + 1) % len(API_KEYS)
            current_key = API_KEYS[self.current_key_index]
            
            if self.current_key_index not in tried_keys:
                tried_keys.add(self.current_key_index)
                
                # Check if this key is valid (less than 5 errors in the last hour)
                if self.key_status[current_key]["errors"] < 5:
                    self.log_info(f"Switched to API key index {self.current_key_index}")
                    return current_key

        # If we've tried all keys and none are valid, find the least errored key
        min_errors = min(self.key_status[key]["errors"] for key in API_KEYS)
        valid_keys = [
            i for i, key in enumerate(API_KEYS)
            if self.key_status[key]["errors"] == min_errors
        ]

        if valid_keys:
            self.current_key_index = random.choice(valid_keys)
            self.log_info(f"Falling back to least errored key index {self.current_key_index}")
            return API_KEYS[self.current_key_index]
        
        raise Exception("All API keys are experiencing issues. Please try again later.")

    def record_error(self, key):
        """Record an error for the given key"""
        self.key_status[key]["errors"] += 1
        self.key_status[key]["last_error"] = datetime.utcnow()
        self.log_error(f"Error recorded for key ending in ...{key[-4:]}")

    def record_request(self, key):
        """Record a successful request for the given key"""
        self.key_status[key]["total_requests"] += 1
        self.key_status[key]["last_request"] = datetime.utcnow()
        if DEBUG_MODE:
            self.log_info(f"Request recorded for key ending in ...{key[-4:]}")

    def create_chat(self, persona_prompt, temperature):
        """Create a chat session with error handling and key rotation"""
        max_retries = len(API_KEYS)
        current_retry = 0
        last_error = None
        
        while current_retry < max_retries:
            try:
                current_key = API_KEYS[self.current_key_index]
                genai.configure(api_key=current_key)
                self.model = genai.GenerativeModel('gemini-pro')
                
                chat = self.model.start_chat(
                    context=persona_prompt,
                    generation_config={
                        "temperature": temperature,
                        "top_p": 0.8,
                        "top_k": 40,
                    }
                )
                
                self.record_request(current_key)
                return chat
            
            except Exception as e:
                last_error = str(e)
                self.record_error(current_key)
                self.log_error(f"Error creating chat with key index {self.current_key_index}", e)
                
                try:
                    current_key = self.get_next_valid_key()
                    current_retry += 1
                except Exception as e:
                    raise Exception(f"All API keys failed: {str(e)}")
        
        raise Exception(f"Failed to create chat session after {max_retries} attempts. Last error: {last_error}")

    def generate_response(self, chat, message, history):
        """Generate response with error handling and key rotation"""
        max_retries = len(API_KEYS)
        current_retry = 0
        last_error = None
        
        while current_retry < max_retries:
            try:
                current_key = API_KEYS[self.current_key_index]
                
                # Format the conversation history
                context = "\n".join([f"{h['role']}: {h['content']}" for h in history])
                prompt = f"{context}\nUser: {message}"
                
                # Generate response
                response = chat.send_message(prompt)
                
                # Record successful request
                self.record_request(current_key)
                
                return response.text
            
            except Exception as e:
                last_error = str(e)
                self.record_error(current_key)
                self.log_error(f"Error generating response with key index {self.current_key_index}", e)
                
                try:
                    current_key = self.get_next_valid_key()
                    current_retry += 1
                    
                    # Recreate chat session with new key
                    chat = self.create_chat(chat.context, chat.generation_config["temperature"])
                except Exception as e:
                    return f"Error: All API keys failed. Please try again later. Details: {str(e)}"
        
        return f"Error: Failed to generate response after {max_retries} attempts. Last error: {last_error}"

    def get_status(self):
        """Get the current status of all API keys"""
        current_time = datetime.utcnow()
        status = {
            "uptime": str(current_time - self.startup_time),
            "total_keys": len(API_KEYS),
            "current_key_index": self.current_key_index,
            "keys": {}
        }
        
        for key in API_KEYS:
            key_info = self.key_status[key]
            status["keys"][key[-4:]] = {
                "errors": key_info["errors"],
                "total_requests": key_info["total_requests"],
                "last_error": str(key_info["last_error"]) if key_info["last_error"] else "Never",
                "last_request": str(key_info["last_request"]) if key_info["last_request"] else "Never",
                "status": "healthy" if key_info["errors"] < 5 else "cooling_down"
            }
        
        return status

if __name__ == "__main__":
    # Test the AI handler
    handler = AIHandler()
    print("\nAI Handler Status:")
    status = handler.get_status()
    for key, info in status["keys"].items():
        print(f"\nKey ending in ...{key}:")
        for k, v in info.items():
            print(f"  {k}: {v}")
