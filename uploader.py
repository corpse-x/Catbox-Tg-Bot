import aiohttp
import aiofiles
import os
import logging
from config import CATBOX_API, LITTERBOX_API, ZEROX0_API, TMPFILES_API

logger = logging.getLogger(__name__)


async def upload_to_catbox(file_path: str, filename: str) -> str | None:
    """Upload to catbox.moe - permanent, no account needed."""
    try:
        async with aiohttp.ClientSession() as session:
            async with aiofiles.open(file_path, "rb") as f:
                file_data = await f.read()
            data = aiohttp.FormData()
            data.add_field("reqtype", "fileupload")
            data.add_field(
                "fileToUpload",
                file_data,
                filename=filename,
                content_type="application/octet-stream"
            )
            async with session.post(CATBOX_API, data=data, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    url = await resp.text()
                    url = url.strip()
                    if url.startswith("https://"):
                        return url
    except Exception as e:
        logger.error(f"Catbox upload failed: {e}")
    return None


async def upload_to_0x0(file_path: str, filename: str) -> str | None:
    """Upload to 0x0.st - permanent (retention based on size), no login."""
    try:
        async with aiohttp.ClientSession() as session:
            async with aiofiles.open(file_path, "rb") as f:
                file_data = await f.read()
            data = aiohttp.FormData()
            data.add_field(
                "file",
                file_data,
                filename=filename,
                content_type="application/octet-stream"
            )
            async with session.post(ZEROX0_API, data=data, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    url = await resp.text()
                    url = url.strip()
                    if url.startswith("https://"):
                        return url
    except Exception as e:
        logger.error(f"0x0.st upload failed: {e}")
    return None


async def upload_to_tmpfiles(file_path: str, filename: str) -> str | None:
    """Upload to tmpfiles.org - permanent, no login."""
    try:
        async with aiohttp.ClientSession() as session:
            async with aiofiles.open(file_path, "rb") as f:
                file_data = await f.read()
            data = aiohttp.FormData()
            data.add_field(
                "file",
                file_data,
                filename=filename,
                content_type="application/octet-stream"
            )
            async with session.post(TMPFILES_API, data=data, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    json_resp = await resp.json()
                    url = json_resp.get("data", {}).get("url")
                    if url:
                        # Convert to direct URL
                        return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception as e:
        logger.error(f"tmpfiles upload failed: {e}")
    return None


async def upload_file(file_path: str, filename: str) -> dict:
    """
    Try multiple upload services. Returns dict with results from each.
    Primary: catbox.moe (permanent)
    Fallback: 0x0.st, tmpfiles.org
    """
    results = {}

    # Try catbox first (primary)
    url = await upload_to_catbox(file_path, filename)
    if url:
        results["catbox"] = url

    # Try 0x0.st
    url = await upload_to_0x0(file_path, filename)
    if url:
        results["0x0.st"] = url

    # Try tmpfiles as third option
    url = await upload_to_tmpfiles(file_path, filename)
    if url:
        results["tmpfiles"] = url

    return results
