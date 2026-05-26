"""
Cloudflare Stream utility functions for Edufix LMS.
Uses the Cloudflare Stream REST API (no extra pip packages needed — only `requests`).

All settings are read lazily inside each function so they are guaranteed to
be available at call time (avoids module-level import-time issues).
"""
import requests
from django.conf import settings


def _base_url():
    account_id = getattr(settings, 'CLOUDFLARE_ACCOUNT_ID', '').strip()
    if not account_id:
        raise ValueError(
            "CLOUDFLARE_ACCOUNT_ID is not set. "
            "Add it to your .env file and restart the server."
        )
    return f"https://api.cloudflare.com/client/v4/accounts/{account_id}/stream"


def _headers():
    token = getattr(settings, 'CLOUDFLARE_API_TOKEN', '').strip()
    if not token:
        raise ValueError(
            "CLOUDFLARE_API_TOKEN is not set. "
            "Add it to your .env file and restart the server."
        )
    return {"Authorization": f"Bearer {token}"}


def upload_video_from_file(file_obj, filename):
    """
    Upload an InMemoryUploadedFile / TemporaryUploadedFile to Cloudflare Stream.

    Args:
        file_obj: Django file-like object (request.FILES['video_file'])
        filename: original filename string

    Returns:
        str: Cloudflare Stream video UID (cf_stream_video_id)

    Raises:
        ValueError if credentials are missing
        requests.HTTPError on API failure
    """
    response = requests.post(
        _base_url(),
        headers=_headers(),
        files={"file": (filename, file_obj, "video/mp4")},
        data={"name": filename},
        timeout=300,  # large files need extra time
    )
    response.raise_for_status()
    data = response.json()
    return data["result"]["uid"]


def get_video_status(video_id):
    """
    Poll processing status for a Cloudflare Stream video.

    Returns a dict:
        {
            "ready":     bool,
            "state":     str,   # "pendingupload" | "downloading" | "queued" | "inprogress" | "ready" | "error"
            "thumbnail": str,
            "duration":  float,
        }
    """
    response = requests.get(
        f"{_base_url()}/{video_id}",
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    result = response.json().get("result", {})
    status = result.get("status", {})
    return {
        "ready":     result.get("readyToStream", False),
        "state":     status.get("state", "processing"),
        "thumbnail": result.get("thumbnail", ""),
        "duration":  result.get("duration", 0),
    }


def delete_video(video_id):
    """
    Delete a video from Cloudflare Stream.
    Silently ignores errors (e.g. already deleted).
    """
    try:
        requests.delete(
            f"{_base_url()}/{video_id}",
            headers=_headers(),
            timeout=30,
        )
    except Exception:
        pass
