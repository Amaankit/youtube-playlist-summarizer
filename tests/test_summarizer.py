from unittest.mock import patch, MagicMock
from yt_summarizer.summarizer.prompts import build_prompt
from yt_summarizer.summarizer.gemini_client import GeminiSummarizer


def test_build_prompt_brief():
    prompt = build_prompt(
        title="Binary Search",
        intent="DSA",
        transcript="This video explains binary search...",
        detail_level="brief",
    )
    assert "Binary Search" in prompt
    assert "DSA" in prompt
    assert "This video explains binary search..." in prompt
    assert "300-500 words" in prompt


def test_build_prompt_detailed():
    prompt = build_prompt(
        title="Binary Search",
        intent="DSA",
        transcript="This video explains binary search...",
        detail_level="detailed",
    )
    assert "Binary Search" in prompt
    assert "DSA" in prompt
    assert "800-1500 words" in prompt
    assert "Key Takeaways" in prompt


@patch("yt_summarizer.summarizer.gemini_client.genai")
def test_gemini_summarizer_generate(mock_genai):
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = "# Binary Search\n\nThis is a summary..."
    mock_client.models.generate_content.return_value = mock_response

    summarizer = GeminiSummarizer(api_key="fake-key")
    result = summarizer.generate(
        title="Binary Search",
        intent="DSA",
        transcript="This video explains binary search...",
        detail_level="detailed",
    )
    assert result == "# Binary Search\n\nThis is a summary..."
    mock_client.models.generate_content.assert_called_once()


@patch("yt_summarizer.summarizer.gemini_client.genai")
def test_gemini_summarizer_returns_none_on_failure(mock_genai):
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.models.generate_content.side_effect = Exception("API error")

    summarizer = GeminiSummarizer(api_key="fake-key")
    result = summarizer.generate(
        title="Binary Search",
        intent="DSA",
        transcript="text",
        detail_level="brief",
    )
    assert result is None
