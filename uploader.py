"""
uploader.py — raw multipart implementations for each host.

Catbox raw source ref: https://gist.github.com/nate-moo/421ffe01575f8abd1d9792b50dcd0a16
Key fix: reqtype + userhash are separate form fields BEFORE fileToUpload.
Old code used aiohttp.FormData with content_type on the file field which
corrupted the multipart body catbox expects.
"""

import uuid
import asyncio
import mimetypes
import aiohttp
import aiofiles
import logging

logger = logging.getLogger(__name__)

CATBOX_URL    = "https://catbox.moe/user/api.php"
LITTERBOX_URL = "https://litterbox.catbox.moe/resources/internals/api.php"
ZEROX0_URL    = "https://0x0.st"
TMPFILES_URL  = "https://tmpfiles.org/api/v1/upload"


def _guess_mime(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def _build_multipart(fields: list[tuple], file_bytes: bytes, filename: str, mime: str, boundary: str) -> bytes:
    """
    Build raw multipart/form-data body.
    fields: list of (name, value) text field tuples added BEFORE the file field.
    """
    body = b""
    sep = f"--{boundary}\r\n".encode()

    for name, value in fields:
        body += sep
        body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += f"{value}\r\n".encode()

    # file field
    body += sep
    body += f'Content-Disposition: form-data; name="fileToUpload"; filename="{filename}"\r\n'.encode()
    body += f"Content-Type: {mime}\r\n\r\n".encode()
    body += file_bytes
    body += f"\r\n--{boundary}--\r\n".encode()
    return body


async def upload_to_catbox(file_path: str, filename: str) -> str | None:
    """
    catbox.moe — permanent, anonymous, up to 200MB.

    Exact form fields (from catbox source):
      reqtype   = fileupload
      userhash  = (empty string for anonymous)
      fileToUpload = <file binary>
    """
    try:
        async with aiofiles.open(file_path, "rb") as f:
            file_bytes = await f.read()

        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        mime = _guess_mime(filename)

        body = _build_multipart(
            fields=[("reqtype", "fileupload"), ("userhash", "")],
            file_bytes=file_bytes,
            filename=filename,
            mime=mime,
            boundary=boundary,
        )

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
        }

        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession() as session:
            async with session.post(CATBOX_URL, data=body, headers=headers, timeout=timeout) as resp:
                text = (await resp.text()).strip()
                logger.info(f"Catbox [{resp.status}]: {text[:200]}")
                if resp.status == 200 and text.startswith("https://files.catbox.moe/"):
                    return text

    except Exception as e:
        logger.error(f"Catbox error: {e}")
    return None


async def upload_to_litterbox(file_path: str, filename: str, time: str = "72h") -> str | None:
    """
    litterbox.catbox.moe — temporary (1h/12h/24h/72h), anonymous, up to 1GB.
    Litterbox uses 'fileToUpload' field name same as catbox, but 'time' instead of 'userhash'.
    """
    try:
        async with aiofiles.open(file_path, "rb") as f:
            file_bytes = await f.read()

        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        mime = _guess_mime(filename)

        # Litterbox: reqtype + time fields, then fileToUpload
        sep = f"--{boundary}\r\n".encode()
        body = b""
        for name, val in [("reqtype", "fileupload"), ("time", time)]:
            body += sep
            body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            body += f"{val}\r\n".encode()
        body += sep
        body += f'Content-Disposition: form-data; name="fileToUpload"; filename="{filename}"\r\n'.encode()
        body += f"Content-Type: {mime}\r\n\r\n".encode()
        body += file_bytes
        body += f"\r\n--{boundary}--\r\n".encode()

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
        }

        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession() as session:
            async with session.post(LITTERBOX_URL, data=body, headers=headers, timeout=timeout) as resp:
                text = (await resp.text()).strip()
                logger.info(f"Litterbox [{resp.status}]: {text[:200]}")
                if resp.status == 200 and text.startswith("https://"):
                    return text

    except Exception as e:
        logger.error(f"Litterbox error: {e}")
    return None


async def upload_to_0x0(file_path: str, filename: str) -> str | None:
    """
    0x0.st — permanent (retention: 365 - (size_mb/1024)*365 days min 30d).
    Field name is 'file' (not 'fileToUpload').
    """
    try:
        async with aiofiles.open(file_path, "rb") as f:
            file_bytes = await f.read()

        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        mime = _guess_mime(filename)

        sep = f"--{boundary}\r\n".encode()
        body = sep
        body += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
        body += f"Content-Type: {mime}\r\n\r\n".encode()
        body += file_bytes
        body += f"\r\n--{boundary}--\r\n".encode()

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
        }

        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession() as session:
            async with session.post(ZEROX0_URL, data=body, headers=headers, timeout=timeout) as resp:
                text = (await resp.text()).strip()
                logger.info(f"0x0.st [{resp.status}]: {text[:200]}")
                if resp.status == 200 and text.startswith("https://"):
                    return text

    except Exception as e:
        logger.error(f"0x0.st error: {e}")
    return None


async def upload_to_tmpfiles(file_path: str, filename: str) -> str | None:
    """
    tmpfiles.org — permanent, no account.
    Returns JSON {status, data:{url}} — convert to direct /dl/ link.
    """
    try:
        async with aiofiles.open(file_path, "rb") as f:
            file_bytes = await f.read()

        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        mime = _guess_mime(filename)

        sep = f"--{boundary}\r\n".encode()
        body = sep
        body += f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
        body += f"Content-Type: {mime}\r\n\r\n".encode()
        body += file_bytes
        body += f"\r\n--{boundary}--\r\n".encode()

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }

        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession() as session:
            async with session.post(TMPFILES_URL, data=body, headers=headers, timeout=timeout) as resp:
                logger.info(f"tmpfiles [{resp.status}]")
                if resp.status == 200:
                    j = await resp.json(content_type=None)
                    url = j.get("data", {}).get("url", "")
                    if url:
                        return url.replace("tmpfiles.org/", "tmpfiles.org/dl/", 1)

    except Exception as e:
        logger.error(f"tmpfiles error: {e}")
    return None


async def upload_file(file_path: str, filename: str) -> dict:
    """
    Upload to all permanent hosts concurrently.
    Falls back to litterbox (72h) only if ALL permanent hosts fail.
    Returns dict: { label: url }
    """
    catbox_t   = asyncio.create_task(upload_to_catbox(file_path, filename))
    zerox0_t   = asyncio.create_task(upload_to_0x0(file_path, filename))
    tmpfiles_t = asyncio.create_task(upload_to_tmpfiles(file_path, filename))

    catbox_url, zerox0_url, tmpfiles_url = await asyncio.gather(
        catbox_t, zerox0_t, tmpfiles_t
    )

    results = {}
    if catbox_url:
        results["catbox.moe"] = catbox_url
    if zerox0_url:
        results["0x0.st"] = zerox0_url
    if tmpfiles_url:
        results["tmpfiles.org"] = tmpfiles_url

    if not results:
        logger.warning("All permanent hosts failed — trying litterbox fallback (72h)")
        litter_url = await upload_to_litterbox(file_path, filename, "72h")
        if litter_url:
            results["litterbox (72h)"] = litter_url

    return results


async def upload_catbox_only(file_path: str, filename: str) -> dict:
    """Used by /cat command. Falls back to litterbox if catbox fails."""
    url = await upload_to_catbox(file_path, filename)
    if url:
        return {"catbox.moe": url}

    logger.warning("Catbox failed — falling back to litterbox 72h")
    url = await upload_to_litterbox(file_path, filename, "72h")
    if url:
        return {"litterbox (72h)": url}

    return {}
