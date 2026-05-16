"""Matrix Webhook media upload helpers."""

import logging
from http import HTTPStatus
from pathlib import PurePosixPath
from urllib.parse import urlparse

import aiohttp
from markdown import markdown
from nio.responses import UploadError

from . import utils

LOGGER = logging.getLogger("matrix_webhook.media")


async def upload_from_url(url):
    """Fetch ``url`` and upload it to the homeserver media repo.

    Returns ``(mxc_uri, mimetype, size, filename)``. Raises ``ValueError``
    if either the fetch or the upload fails.
    """
    msg = f"Fetching image from {url=}"
    LOGGER.debug(msg)

    try:
        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            if resp.status != HTTPStatus.OK:
                msg = f"Failed to fetch {url}: HTTP {resp.status}"
                raise ValueError(msg)
            content_type = resp.headers.get(
                "Content-Type",
                "application/octet-stream",
            )
            image_bytes = await resp.read()
    except aiohttp.ClientError as e:
        msg = f"Failed to fetch {url}: {e!r}"
        raise ValueError(msg) from e

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


async def captioned_image(image_url, body, formatted_body=None):
    """Build an ``m.image`` event content from an explicit URL + caption.

    Fetches and uploads ``image_url`` to the homeserver media repo and
    returns an ``m.image`` content dict with the resulting ``mxc://`` URI.
    ``body`` is used as the caption (plain text) and rendered as HTML for
    ``formatted_body``, unless an explicit ``formatted_body`` is supplied.

    Returns ``None`` if the upload fails; the caller falls back to ``m.text``.
    """
    try:
        mxc, mimetype, size, filename = await upload_from_url(image_url)
    except ValueError as e:
        msg = f"Image upload skipped, falling back to text: {e}"
        LOGGER.warning(msg)
        return None

    return {
        "msgtype": "m.image",
        "url": mxc,
        "filename": filename,
        "info": {"mimetype": mimetype, "size": size},
        "body": body,
        "format": "org.matrix.custom.html",
        "formatted_body": formatted_body or markdown(body, extensions=["extra"]),
    }