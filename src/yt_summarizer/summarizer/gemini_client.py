import logging
import time
from google import genai

log = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.8-flash"
MAX_RETRIES = 3


class GeminiSummarizer:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(
        self, title: str, intent: str, transcript: str, detail_level: str
    ) -> str | None:
        from yt_summarizer.summarizer.prompts import build_prompt

        prompt = build_prompt(title, intent, transcript, detail_level)

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.models.generate_content(
                    model=self.model, contents=prompt
                )
                return response.text
            except Exception as e:
                log.warning(
                    "Gemini API attempt %d/%d failed for '%s': %s",
                    attempt + 1,
                    MAX_RETRIES,
                    title,
                    e,
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** (attempt + 1))

        log.error("All %d attempts failed for '%s'", MAX_RETRIES, title)
        return None
