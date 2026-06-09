import os
from typing import Literal

import requests
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
                instructions=instructions,
            )
        return self.response.output_text

    def generate_image(
            self,
            prompt: str,
            image_savefile: str,
            size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1792x1024",
            quality: Literal["standard", "hd"] = "hd",
    ):
        image = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )

        image_url = image.data[0].url
        response = requests.get(image_url)
        with open(image_savefile, "wb") as f:
            f.write(response.content)
