# extractor.py
import re
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

def extract_video_id(url: str) -> str:
    """
    Extracts the YouTube video ID from various URL formats.
    """
    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})"
    ]
    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")

def fetch_transcript(youtube_url: str,
                     languages: list[str] | None = None,
                     preserve_formatting: bool = False) -> str:
    """
    Fetches and returns the transcript text for a YouTube video URL.
    Uses youtube-transcript-api v1.2.3 API.
    
    Parameters:
        youtube_url: Full YouTube video URL.
        languages: optional list of language codes in descending preference.
        preserve_formatting: whether to keep HTML tags (italic/bold) in transcript.
    
    Returns:
        A single‐string cleaned transcript (text only).
    """
    video_id = extract_video_id(youtube_url)
    ytt_api = YouTubeTranscriptApi()

    try:
        transcript = ytt_api.fetch(video_id,
                                   languages=languages or ["en"],
                                   preserve_formatting=preserve_formatting)
    except NoTranscriptFound:
        raise RuntimeError("Transcript not found for this video.")
    except TranscriptsDisabled:
        raise RuntimeError("Transcripts are disabled for this video.")
    except Exception as e:
        raise RuntimeError(f"Transcript could not be fetched: {str(e)}")

    # transcript is a FetchedTranscript (iterable of snippets)
    # extract text from each snippet
    texts = [snippet.text for snippet in transcript]
    cleaned = " ".join(texts)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        raise RuntimeError("Transcript is empty after fetch/clean.")
    return cleaned

if __name__ == "__main__":
    test_url = input("Enter YouTube URL: ")
    try:
        print(fetch_transcript(test_url))
    except Exception as err:
        print("Error:", err)
