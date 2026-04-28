"""Matrix Webhook media upload helpers."""

import logging
import re
from http import HTTPStatus
from pathlib import PurePosixPath
from urllib.parse import urlparse

import aiohttp
from markdown import markdown
from nio.responses import UploadError

from . import utils

LOGGER = logging.getLogger("matrix_webhook.media")

# Markdown image syntax with an http(s) URL: ``![alt](url)``.
_MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\((https?://[^)\s]+)\)")
# Permissive markdown image regex (any URL contents, including empty).
_MD_ANY_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")


def strip_orphan_image_links(body):
    """Drop markdown image refs whose URL is empty or not http(s).

    Templating engines on the sender side (e.g. Jellyseerr's
    ``{{image}}``) can produce ``![alt]()`` for events with no
    associated media, which the markdown renderer would emit as a
    broken ``<img>`` tag. http(s) refs are preserved so the
    upload-failure fallback path still shows the user the URL.
    """

    def _decide(match):
        url = (match.group(2) or "").strip()
        if url.startswith(("http://", "https://")):
            return match.group(0)
        return ""

    out = _MD_ANY_IMG_RE.sub(_decide, body)
    if out == body:
        # Nothing stripped; return as-is to preserve whitespace that
        # other paths (e.g. formatter outputs) may rely on.
        return body
    return re.sub(r"\n{3,}", "\n\n", out).strip()


async def upload_from_url(url):
    """Fetch ``url`` and upload it to the homeserver media repo.

    Returns ``(mxc_uri, mimetype, size, filename)``. Raises ``ValueError``
    if either the fetch or the upload fails.
    """
    msg = f"Fetching image from {url=}"
    LOGGER.debug(msg)

    async with aiohttp.ClientSession() as session, session.get(url) as resp:
        if resp.status != HTTPStatus.OK:
            msg = f"Failed to fetch {url}: HTTP {resp.status}"
            raise ValueError(msg)
        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        image_bytes = await resp.read()

    filename = PurePosixPath(urlparse(url).path).name or "image"

    msg = f"Uploading {len(image_bytes)} bytes as {filename=} ({content_type=})"
    LOGGER.debug(msg)

    upload_resp, _ = await utils.CLIENT.upload(
        lambda got_429, got_timeouts: image_bytes,
        content_type=content_type,
        filename=filename,
        filesize=len(image_bytes),
    )

    if isinstance(upload_resp, UploadError):
        msg = f"Failed to upload {url}: {upload_resp.message}"
        raise ValueError(msg)

    return upload_resp.content_uri, content_type, len(image_bytes), filename


async def captioned_image_or_text(body):
    """Build an ``m.image`` event content from markdown image links in ``body``.

    If ``body`` contains at least one ``![alt](http(s)://...)`` reference,
    fetches and uploads the FIRST one to the homeserver media repo and
    returns an ``m.image`` event content dict with the URL set to the
    resulting ``mxc://`` URI. The caption is the rest of ``body`` with all
    markdown image links stripped, rendered as both plain text (``body``)
    and HTML (``formatted_body``). The ``filename`` field is set to the
    original URL's basename so MSC4193-aware clients render the image with
    a caption rather than treating ``body`` as the filename.

    Returns ``None`` if ``body`` has no image references, or if the upload
    fails. The caller is responsible for falling back to an ``m.text``
    event in either case.
    """
    matches = list(_MD_IMG_RE.finditer(body))
    if not matches:
        return None

    first = matches[0]
    try:
        mxc, mimetype, size, filename = await upload_from_url(first.group(2))
    except ValueError as e:
        msg = f"Image upload skipped, falling back to text: {e}"
        LOGGER.warning(msg)
        return None

    # Strip ALL image refs from the body — the first becomes the m.image
    # url, additional ones (rare) would require multiple events which we do
    # not emit; leaving them in the caption as raw markdown would render as
    # plain-text URLs in Element X anyway. Collapse the blank-line gap that
    # the strip leaves around the image link.
    caption = _MD_IMG_RE.sub("", body)
    caption = re.sub(r"\n{3,}", "\n\n", caption).strip()

    content = {
        "msgtype": "m.image",
        "url": mxc,
        "filename": filename,
        "info": {"mimetype": mimetype, "size": size},
    }
    if caption:
        content["body"] = caption
        content["format"] = "org.matrix.custom.html"
        content["formatted_body"] = markdown(caption, extensions=["extra"])
    else:
        content["body"] = filename

    return content
