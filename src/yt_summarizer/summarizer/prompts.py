BRIEF_TEMPLATE = """You are summarizing a YouTube video transcript.

Context: This video is part of a {intent} series.
Video Title: {title}

Instructions:
- Summarize the key points in 300-500 words
- If the video contains code, include it inline as markdown code blocks with the language specified
- Pair each code block with a brief explanation of what it does
- Use markdown formatting with headers for sections

Transcript:
{transcript}"""

DETAILED_TEMPLATE = """You are creating a detailed study note from a YouTube video transcript.

Context: This video is part of a {intent} series.
Video Title: {title}

Instructions:
- Follow the video's teaching structure and flow
- Cover all concepts explained in the video thoroughly (800-1500 words)
- If the video contains code, include ALL code inline as markdown code blocks with the language specified, placed exactly where the concept is explained — just like the video teaches it
- For each code block, explain the logic, approach, and complexity (time/space) if applicable
- Use markdown headers, bullet points, and bold for key terms
- End with a "Key Takeaways" section

Transcript:
{transcript}"""


def build_prompt(title: str, intent: str, transcript: str, detail_level: str) -> str:
    template = DETAILED_TEMPLATE if detail_level == "detailed" else BRIEF_TEMPLATE
    return template.format(title=title, intent=intent, transcript=transcript)
