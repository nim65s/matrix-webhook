"""Test module for grafana formatter."""

import unittest

import httpx
import nio

from .start import BOT_URL, FULL_ID, MATRIX_ID, MATRIX_PW, MATRIX_URL

SHA256 = "fd7522672889385736be8ffc86d1f8de2e15668864f49af729b5c63e5e0698c4"


def headers(sha256=SHA256, event="push"):
    """Mock headers from github webhooks."""
    return {
        # 'Request URL': 'https://bot.saurel.me/room?formatter=github',
        # 'Request method': 'POST',
        "Accept": "*/*",
        "content-type": "application/json",
        "User-Agent": "GitHub-Hookshot/8d33975",
        "X-GitHub-Delivery": "636b9b1c-0761-11ec-8a8a-5e435c5ac4f4",
        "X-GitHub-Event": event,
        "X-GitHub-Hook-ID": "311845633",
        "X-GitHub-Hook-Installation-Target-ID": "171114171",
        "X-GitHub-Hook-Installation-Target-Type": "repository",
        "X-Hub-Signature": "sha1=ea68fdfcb2f328aaa8f50d176f355e5d4fc95d94",
        "X-Hub-Signature-256": f"sha256={sha256}",
    }


class GithubFormatterTest(unittest.IsolatedAsyncioTestCase):
    """Github formatter test class."""

    async def test_github_notification(self):
        """Send a mock github webhook, and check the result."""
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        with open("tests/example_github_push.json", "rb") as f:
            example_github_push = f.read().strip()
        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                params={
                    "formatter": "github",
                },
                content=example_github_push,
                headers=headers(event="something else"),
            ).json(),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(
            message.formatted_body,
            "<p>notification from github</p>",
        )

    async def test_github_push(self):
        """Send a mock github push webhook, and check the result."""
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        with open("tests/example_github_push.json", "rb") as f:
            example_github_push = f.read().strip()
        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                params={
                    "formatter": "github",
                },
                content=example_github_push,
                headers=headers(),
            ).json(),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        before = "ac7d1d9647008145e9d0cf65d24744d0db4862b8"
        after = "4bcdb25c809391baaabc264d9309059f9f48ead2"
        GH = "https://github.com"
        expected = f'<p>@<a href="{GH}/nim65s">nim65s</a> pushed on refs/heads/devel: '
        expected += f'<a href="{GH}/nim65s/matrix-webhook/compare/ac7d1d964700...'
        expected += f'4bcdb25c8093">{before} → {after}</a>:</p>\n<ul>\n<li>'
        expected += f'<a href="{GH}/nim65s/matrix-webhook/commit/{after}">'
        expected += "formatters: also get headers</a></li>\n</ul>"

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(
            message.formatted_body,
            expected,
        )

    async def test_github_wrong_digest(self):
        """Send a mock github push webhook with a wrong digest."""
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        with open("tests/example_github_push.json", "rb") as f:
            example_github_push = f.read().strip()

        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                params={
                    "formatter": "github",
                },
                content=example_github_push,
                headers=headers("wrong digest"),
            ).json(),
            {"status": 401, "ret": "Invalid SHA-256 HMAC digest"},
        )
