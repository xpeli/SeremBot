"""Shared fixtures and helpers for SeremBot tests."""

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def fake_api_key(monkeypatch):
    """Ensure CHATGPT_TOKEN is set in test environment so communicator
    doesn't raise ValueError during init."""
    monkeypatch.setenv("CHATGPT_TOKEN", "***")


@pytest.fixture
def mock_openai():
    """Mock the entire openai.OpenAI client so tests don't hit the real API."""
    mock_client = MagicMock()
    mock_client.responses.create.return_value = MagicMock(
        output_text="Mock response text",
        id="resp_mock_123",
    )
    mock_client.images.generate.return_value = MagicMock(
        data=[MagicMock(url="https://example.com/fake_image.png")]
    )
    with patch("ChatGPTCommunicator.OpenAI", return_value=mock_client):
        yield mock_client


@pytest.fixture
def communicator(mock_openai):
    """A ChatGPTCommunicator with mocked OpenAI client."""
    from ChatGPTCommunicator import ChatGPTCommunicator

    return ChatGPTCommunicator(api_key="***")
