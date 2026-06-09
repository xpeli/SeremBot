"""Tests for ChatGPTCommunicator — chat, images, conversation management."""

from unittest.mock import MagicMock

import pytest
from openai import APIError, APITimeoutError, RateLimitError

from ChatGPTCommunicator import (
    MAX_CONVERSATION_TURNS,
    ChatGPTCommunicator,
)

# ── Helpers for constructing OpenAI exceptions in tests ──────────────────────

_FAKE_REQUEST = MagicMock()  # httpx.Request mock


def _rate_limit():
    return RateLimitError(
        "rate limited", response=MagicMock(status_code=429), body=None
    )


def _timeout():
    return APITimeoutError(request=_FAKE_REQUEST)


def _api_error(status=500):
    return APIError(f"error {status}", MagicMock(), body=None)


class TestInit:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("CHATGPT_TOKEN", raising=False)
        with pytest.raises(ValueError, match="CHATGPT_TOKEN"):
            ChatGPTCommunicator(api_key=None)

    def test_uses_explicit_api_key(self):
        c = ChatGPTCommunicator(api_key="explicit")
        assert c._api_key == "explicit"

    def test_uses_env_var(self, fake_api_key):
        c = ChatGPTCommunicator()
        assert c._api_key == "***"


class TestChatCompletion:
    def test_first_message_creates_new_response(self, communicator, mock_openai):
        result = communicator.send_chat_completion("Hello", "Be helpful")
        assert result == "Mock response text"
        call_kwargs = mock_openai.responses.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["input"] == "Hello"

    def test_second_message_uses_previous_id(self, communicator, mock_openai):
        communicator.send_chat_completion("First", "Be helpful")
        communicator.send_chat_completion("Second", "Be helpful")
        second = mock_openai.responses.create.call_args_list[1].kwargs
        assert second["previous_response_id"] == "resp_mock_123"
        assert second["input"] == [{"role": "user", "content": "Second"}]

    def test_turns_increment(self, communicator):
        assert communicator.turn_count == 0
        communicator.send_chat_completion("A", "X")
        assert communicator.turn_count == 1
        communicator.send_chat_completion("B", "X")
        assert communicator.turn_count == 2

    def test_rate_limit_retries_once(self, communicator):
        call_count = 0

        def flaky(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise _rate_limit()
            return MagicMock(output_text="Recovered!")

        communicator.client.responses.create = flaky
        result = communicator.send_chat_completion("Test", "X")
        assert result == "Recovered!"
        assert call_count == 2

    def test_rate_limit_exhausted_graceful(self, communicator):
        def always(*args, **kwargs):
            raise _rate_limit()

        communicator.client.responses.create = always
        result = communicator.send_chat_completion("Test", "X")
        assert "Rate limited" in result

    def test_timeout_graceful(self, communicator):
        communicator.client.responses.create.side_effect = _timeout()
        result = communicator.send_chat_completion("Test", "X")
        assert "taking too long" in result

    def test_api_error_graceful(self, communicator):
        communicator.client.responses.create.side_effect = _api_error(500)
        result = communicator.send_chat_completion("Test", "X")
        assert "error" in result.lower()

    def test_unexpected_exception_graceful(self, communicator):
        communicator.client.responses.create.side_effect = Exception("boom")
        result = communicator.send_chat_completion("Test", "X")
        assert "went wrong" in result


class TestConversationReset:
    def test_reset_clears_state(self, communicator):
        communicator.send_chat_completion("Hello", "X")
        assert communicator.turn_count == 1
        assert communicator._response is not None

        communicator.reset_conversation()
        assert communicator.turn_count == 0
        assert communicator._response is None

    def test_auto_reset_at_limit(self, communicator):
        for i in range(MAX_CONVERSATION_TURNS):
            communicator.send_chat_completion(f"Msg {i}", "X")
        assert communicator.turn_count == MAX_CONVERSATION_TURNS

        communicator.send_chat_completion("Over limit", "X")
        assert communicator.turn_count == 1


class TestImageGeneration:
    def test_success(self, communicator, mock_openai, tmp_path, mocker):
        mocker.patch("ChatGPTCommunicator.requests.get",
                      return_value=MagicMock(content=b"fakeimage", status_code=200,
                                            raise_for_status=MagicMock()))
        path = str(tmp_path / "img.png")
        result = communicator.generate_image("a cat", path, size="256x256")
        assert result == path
        mock_openai.images.generate.assert_called_once()

    def test_timeout_raises(self, communicator):
        communicator.client.images.generate.side_effect = _timeout()
        with pytest.raises(RuntimeError, match="timed out"):
            communicator.generate_image("test", "/tmp/nope.png")

    def test_rate_limit_raises(self, communicator):
        communicator.client.images.generate.side_effect = _rate_limit()
        with pytest.raises(RuntimeError, match="Rate limited"):
            communicator.generate_image("test", "/tmp/nope.png")

    def test_no_url_raises(self, communicator, mock_openai):
        mock_openai.images.generate.return_value = MagicMock(
            data=[MagicMock(url=None)]
        )
        with pytest.raises(RuntimeError, match="no image URL"):
            communicator.generate_image("test", "/tmp/nope.png")


class TestPersonalitySwitching:
    def test_all_personalities_have_entries(self):
        from BotPersonalities import PersonalityName, personalities
        for name in PersonalityName:
            assert name in personalities, f"Missing personality: {name}"
            assert personalities[name], f"Empty personality: {name}"


class TestTurnLimitConstant:
    def test_max_turns_is_reasonable(self):
        assert 5 <= MAX_CONVERSATION_TURNS <= 50
