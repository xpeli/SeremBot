"""OpenAI API communicator — responses, image generation, conversation management."""

import logging
import os
import time
from pathlib import Path
from typing import Literal

import requests
from openai import APIError, APITimeoutError, OpenAI, RateLimitError

log = logging.getLogger("serembot.communicator")

# ── Conversation limits ──────────────────────────────────────────────────────
MAX_CONVERSATION_TURNS = 20  # auto-reset after this many exchanges
# OpenAI responses API doesn't expose token count directly, so we track turns
# as a reasonable proxy.  20 turns ≈ roughly 8K–16K tokens depending on length.

IMAGE_DIR = Path.home() / ".serembot" / "images"
MAX_IMAGE_DIR_MB = 100  # clean up oldest images if folder exceeds this


class ChatGPTCommunicator:
    """Talks to OpenAI's Responses API with conversation memory and auto-reset."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("CHATGPT_TOKEN")
        if not self._api_key:
            raise ValueError(
                "CHATGPT_TOKEN not found. Set it in your environment "
                "or pass api_key= to ChatGPTCommunicator()."
            )
        self.client = OpenAI(api_key=self._api_key, timeout=120.0)
        self._response = None  # current conversation state
        self._turn_count = 0

    # ── Chat ─────────────────────────────────────────────────────────────────

    def send_chat_completion(
        self, prompt: str, instructions: str, _retry: bool = True
    ) -> str:
        """Send a prompt in a persistent conversation. Auto-resets after
        MAX_CONVERSATION_TURNS exchanges to avoid context overflow."""
        if self._turn_count >= MAX_CONVERSATION_TURNS:
            log.info("Conversation turn limit reached — auto-resetting")
            self.reset_conversation()

        try:
            if self._response is None:
                self._response = self.client.responses.create(
                    model="gpt-4o-mini",
                    input=prompt,
                    instructions=instructions,
                )
            else:
                self._response = self.client.responses.create(
                    model="gpt-4o-mini",
                    previous_response_id=self._response.id,
                    input=[{"role": "user", "content": prompt}],
                    instructions=instructions,
                )

            self._turn_count += 1
            log.debug(
                "Turn %d/%d — %d chars response",
                self._turn_count, MAX_CONVERSATION_TURNS,
                len(self._response.output_text),
            )
            return self._response.output_text

        except RateLimitError:
            if not _retry:
                return "⏳ Rate limited by OpenAI. Try again in a minute."
            log.warning("OpenAI rate limit hit — waiting 10s then retrying once")
            time.sleep(10)
            return self.send_chat_completion(prompt, instructions, _retry=False)

        except APITimeoutError:
            log.error("OpenAI API timeout")
            return "⌛ OpenAI is taking too long. Try again."

        except APIError as e:
            log.error("OpenAI API error: %s", e)
            return f"⚠️ API error — {e.status_code if hasattr(e, 'status_code') else 'unknown'}."

        except Exception as e:
            log.exception("Unexpected error in chat completion")
            return "💥 Something went wrong. Try again later."

    def reset_conversation(self):
        """Start a fresh conversation. Called automatically when turn limit hit."""
        self._response = None
        self._turn_count = 0
        log.info("Conversation reset")

    # ── Image generation ─────────────────────────────────────────────────────

    def generate_image(
        self,
        prompt: str,
        image_savefile: str,
        size: Literal[
            "256x256", "512x512", "1024x1024"
        ] = "1024x1024",
    ) -> str:
        """Generate an image via GPT Image API.  Returns the path to the saved file.

        Raises RuntimeError on failure so the caller can handle it gracefully.
        """
        log.info("Generating image: %s (%s)", prompt[:60], size)

        try:
            result = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size,
                n=1,
            )
        except APITimeoutError:
            raise RuntimeError("Image generation timed out.") from None
        except RateLimitError:
            raise RuntimeError("Rate limited — wait a minute.") from None
        except APIError as e:
            raise RuntimeError(
                f"OpenAI API error (status {getattr(e, 'status_code', '?')})."
            ) from e

        image_data = result.data[0]
        image_url = image_data.url
        image_b64 = image_data.b64_json

        # gpt-image-1 returns base64, DALL-E returns URL
        if image_b64:
            import base64
            os.makedirs(os.path.dirname(image_savefile) or ".", exist_ok=True)
            with open(image_savefile, "wb") as f:
                f.write(base64.b64decode(image_b64))
            log.info("Image saved to %s (%d bytes)", image_savefile, len(base64.b64decode(image_b64)))
        elif image_url:
            try:
                resp = requests.get(image_url, timeout=30)
                resp.raise_for_status()
            except requests.RequestException as e:
                raise RuntimeError(f"Failed to download image: {e}") from e
            os.makedirs(os.path.dirname(image_savefile) or ".", exist_ok=True)
            with open(image_savefile, "wb") as f:
                f.write(resp.content)
            log.info("Image saved to %s (%d bytes)", image_savefile, len(resp.content))
        else:
            raise RuntimeError("OpenAI returned neither image URL nor data.")
        self._cleanup_image_dir()
        return image_savefile

    # ── Helpers ──────────────────────────────────────────────────────────────

    @property
    def turn_count(self) -> int:
        return self._turn_count

    @staticmethod
    def _cleanup_image_dir():
        """Remove oldest images if the image directory exceeds MAX_IMAGE_DIR_MB."""
        if not IMAGE_DIR.exists():
            return

        total_size = sum(
            f.stat().st_size for f in IMAGE_DIR.iterdir() if f.is_file()
        )
        if total_size < MAX_IMAGE_DIR_MB * 1024 * 1024:
            return

        log.info(
            "Image dir is %.1f MB (limit %d MB) — cleaning oldest",
            total_size / (1024 * 1024), MAX_IMAGE_DIR_MB,
        )
        files = sorted(
            IMAGE_DIR.iterdir(), key=lambda f: f.stat().st_mtime
        )
        for f in files:
            if not f.is_file():
                continue
            sz = f.stat().st_size
            f.unlink()
            total_size -= sz
            if total_size < MAX_IMAGE_DIR_MB * 1024 * 1024 * 0.7:
                break
