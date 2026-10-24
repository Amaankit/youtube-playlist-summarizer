import logging
import time
from groq import Groq

log = logging.getLogger(__name__)

DEFAULT_MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 5
BASE_DELAY = 2


class GroqSummarizer:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(
        self, title: str, intent: str, transcript: str, detail_level: str
    ) -> str | None:
        from yt_summarizer.summarizer.prompts import build_prompt

        prompt = build_prompt(title, intent, transcript, detail_level)

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content
            except Exception as e:
                wait = BASE_DELAY ** (attempt + 1)
                log.warning(
                    "Groq API attempt %d/%d failed for '%s' (retry in %ds): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    title,
                    wait,
                    e,
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait)

        log.error("All %d attempts failed for '%s'", MAX_RETRIES, title)
        return None
