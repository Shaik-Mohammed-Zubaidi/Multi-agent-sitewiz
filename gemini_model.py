import google.generativeai as genai
import os

class GeminiChatClient:
    def __init__(self, model="models/gemini-1.5-flash-latest", temperature=0.2):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.chat = self.model.start_chat()
        self.temperature = temperature

    def chat_completion(self, messages):
        full_prompt = ""
        for m in messages:
            if m["role"] == "user":
                full_prompt += f"User: {m['content']}\n"
            elif m["role"] == "assistant":
                full_prompt += f"Assistant: {m['content']}\n"

        response = self.chat.send_message(full_prompt)
        return {"content": response.text}
