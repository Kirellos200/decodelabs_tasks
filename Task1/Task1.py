import os
import google.generativeai as genai


genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

class StatefulChatbot:
    def __init__(self, model_name="gemini-3-flash-preview", window_size=10):
        # 1. Connect to a frontier LLM
        self.model = genai.GenerativeModel(model_name)
        
        # 2. Maintain an active in-memory list array to store the conversation history
        self.history = []
        
        # Limit for the Sliding Window Algorithm (FIFO)
        self.window_size = window_size 

    def structural_validation_gate(self, user_input):
        if not user_input or not user_input.strip():
            print("\n[System] Error: 400 Bad Request - Input cannot be empty or just whitespace.")
            return False
        return True

    def enforce_sliding_window(self):
        # We check if the history exceeds our set window size
        if len(self.history) > self.window_size:
            # Drop the oldest user/model interaction pair (the first two items)
            self.history = self.history[2:]
            print("\n[System] Context limit reached. Truncated oldest messages (FIFO).")

    def chat_loop(self):
        print("-------------------------------------------------\n")
        print(" AGENT INITIALIZED ")
        print(" Type 'exit' to end the session.")
        print("-------------------------------------------------\n")

        while True:
            user_input = input("User: ")

            if user_input.lower() == 'exit':
                print("\n[System] Terminating session. Local RAM cleared.")
                break

            # Pass through the Structural Validation Gate
            if not self.structural_validation_gate(user_input):
                continue

            # Append validated input to local history as a structured user content object
            self.history.append({
                "role": "user",
                "parts": [user_input]
            })

            self.enforce_sliding_window()

            try:
                # Process: GenAI SDK Cloud Transmission
                response = self.model.generate_content(self.history)
                
                model_text = response.text
                print(f"\nModel: {model_text}\n")

                # Append the model's generated response to the history list
                self.history.append({
                    "role": "model",
                    "parts": [model_text]
                })

            except Exception as e:
                print(f"\n[System] API Communication Error: {e}")
                # Rollback the last user input so the array isn't corrupted by a failed call
                self.history.pop()

if __name__ == "__main__":
    bot = StatefulChatbot()
    bot.chat_loop()