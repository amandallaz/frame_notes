import os
from urllib.parse import unquote, urlparse


def cloudinary_credentials():
    """
    Return CLOUDINARY_STORAGE dict when credentials are set, else None.

    Supports CLOUDINARY_URL (cloudinary://key:secret@cloud_name) or
    CLOUDINARY_CLOUD_NAME + CLOUDINARY_API_KEY + CLOUDINARY_API_SECRET.
    """
    url = os.environ.get("CLOUDINARY_URL", "").strip()
    if url:
        if url.startswith("cloudinary://"):
            url = "https://" + url[len("cloudinary://") :]
        parsed = urlparse(url)
        if parsed.hostname and parsed.username and parsed.password:
            return {
                "CLOUD_NAME": parsed.hostname,
                "API_KEY": unquote(parsed.username),
                "API_SECRET": unquote(parsed.password),
            }
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key = os.environ.get("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", "").strip()
    if cloud_name and api_key and api_secret:
        return {
            "CLOUD_NAME": cloud_name,
            "API_KEY": api_key,
            "API_SECRET": api_secret,
        }
    return None
