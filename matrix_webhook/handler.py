"""Matrix Webhook main request handler."""

import json
import logging
from http import HTTPStatus
from hmac import HMAC

from markdown import markdown

from . import conf, formatters, utils

LOGGER = logging.getLogger("matrix_webhook.handler")


async def matrix_webhook(request):
    """
    Coroutine given to the server, st. it knows what to do with an HTTP request.

    This one handles a POST, checks its content, and forwards it to the matrix room.
    """
    LOGGER.debug(f"Handling {request=}")
    data_b = await request.read()

    try:
        data = json.loads(data_b.decode())
    except json.decoder.JSONDecodeError:
        return utils.create_json_response(HTTPStatus.BAD_REQUEST, "Invalid JSON")

    # legacy naming
    if "text" in data and "body" not in data:
        data["body"] = data["text"]

    # allow key to be passed as a parameter
    if "key" in request.rel_url.query and "key" not in data:
        data["key"] = request.rel_url.query["key"]

    if "formatter" in request.rel_url.query:
        try:
            data = getattr(formatters, request.rel_url.query["formatter"])(
                data, request.headers
            )
        except AttributeError:
            return utils.create_json_response(
                HTTPStatus.BAD_REQUEST, "Unknown formatter"
            )

    if "room_id" in request.rel_url.query and "room_id" not in data:
        data["room_id"] = request.rel_url.query["room_id"]
    if "room_id" not in data:
        data["room_id"] = request.path.lstrip("/")

    # If we get a good SHA-256 HMAC digest,
    # we can consider that the sender has the right API key
    if "digest" in data:
        if data["digest"] == HMAC(conf.API_KEY.encode(), data_b, "sha256").hexdigest():
            data["key"] = conf.API_KEY
        else:  # but if there is a wrong digest, an informative error should be provided
            return utils.create_json_response(
                HTTPStatus.UNAUTHORIZED, "Invalid SHA-256 HMAC digest"
            )

    missing = []
    for key in ["body", "key", "room_id"]:
        if key not in data or not data[key]:
            missing.append(key)
    if missing:
        return utils.create_json_response(
            HTTPStatus.BAD_REQUEST, f"Missing {', '.join(missing)}"
        )

    if data["key"] != conf.API_KEY:
        return utils.create_json_response(HTTPStatus.UNAUTHORIZED, "Invalid API key")

    if "formatted_body" in data:
        formatted_body = data["formatted_body"]
    else:
        formatted_body = markdown(str(data["body"]), extensions=["extra"])

    # try to join room first -> non none response means error
    resp = await utils.join_room(data["room_id"])
    if resp is not None:
        return resp

    content = {
        "msgtype": "m.text",
        "body": data["body"],
        "format": "org.matrix.custom.html",
        "formatted_body": formatted_body,
    }
    return await utils.send_room_message(data["room_id"], content)
