import os

import openai
import requests
from typing import List, Dict

class ChatGPTCommunicator:
    _API_KEY = os.environ.get("CHATGPT_TOKEN")
    MESSAGE_APPEND = {"role": "user", "content":
                "Above I sent you some code. Each code is in a separate message. "
                "Can you explain what this code does and how it functions together?"
                "In the end, please also explain the entire project."}

    def __init__(self, api_key: str = _API_KEY):
        self.api_key = api_key

    def send_single_prompt(self, prompt: str) -> str:
        openai.api_key = self.api_key

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"{prompt}\nAI:",
            max_tokens=350,
            temperature=0.8,
            top_p=1,
            n=1,
            stop=None,
            echo=False
        )

        response_text = response.choices[0].text.strip()
        return response_text

    def send_chat_prompt(self, messages: List[Dict[str, str]]):
        openai.api_key = self.api_key
        messages.append(self.MESSAGE_APPEND)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.8,
            top_p=1,
            n=1,
            stop=None
        )

        return response.get("choices")[0].get("message").get("content")

    def generate_image(self, prompt: str, image_savefile: str, size: str = "256x256"):
        openai.api_key = self.api_key

        image = openai.Image.create(prompt=prompt, n=1, size=size)

        # Download image from URL
        image_url = image['data'][0]['url']
        response = requests.get(image_url)
        with open(image_savefile, 'wb') as f:
            f.write(response.content)

if __name__ == "__main__":
    c = ChatGPTCommunicator()
    openai.api_key = os.environ.get("CHATGPT_TOKEN")

    m: List[Dict[str, str]] = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "First secret codeword is Blue"},
        {"role": "user", "content": "Second secret codeword is Red"},
        {"role": "user", "content": "This secret codeword is Purple"},
        {"role": "user", "content": "Can you tell me the secret codewords?"},
    ]
