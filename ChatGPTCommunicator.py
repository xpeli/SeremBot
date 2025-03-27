import os

import openai
import requests
from typing import List, Dict, Literal

from openai import OpenAI


class ChatGPTCommunicator:
    _API_KEY = os.environ.get("CHATGPT_TOKEN")

    def __init__(self, api_key: str = _API_KEY):
        self.client = OpenAI(api_key=api_key)
        self.response = None

    def send_single_prompt(
            self,
            prompt: str,
            instructions: str,
    ) -> str:
        response = self.client.responses.create(
            model="gpt-4o",
            instructions=instructions,
            input=prompt,
        )

        return response.output_text

    def send_chat_completion(
            self,
            prompt: str,
            instructions: str,
    ):

        if self.response is None:
            # Create new response prompt
            self.response = self.client.responses.create(
                model="gpt-4o-mini",
                input=prompt,
                instructions=instructions,
            )
        else:
            self.response = self.client.responses.create(
                model="gpt-4o-mini",
                previous_response_id=self.response.id,
                input=[{"role": "user", "content": prompt}],
            )

    def generate_image(
            self,
            prompt: str,
            image_savefile: str,
            size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1792x1024",
            quality: Literal["standard", "hd"] = "hd"
    ):
        image = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )

        # Download image from URL
        image_url = image.data[0].url
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
