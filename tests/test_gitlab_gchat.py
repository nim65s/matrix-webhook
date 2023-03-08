"""Test module for gitlab "google chat" formatter."""

import unittest
from pathlib import Path

import httpx
import nio

from .start import BOT_URL, FULL_ID, KEY, MATRIX_ID, MATRIX_PW, MATRIX_URL


class GitlabGchatFormatterTest(unittest.IsolatedAsyncioTestCase):
    """Gitlab "google chat" formatter test class."""

    async def test_gitlab_gchat_body(self):
        """Send a markdown message, and check the result."""
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        with Path("tests/example_gitlab_gchat.json").open() as f:
            example_gitlab_gchat_request = f.read()
        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                params={"formatter": "gitlab_gchat", "key": KEY},
                content=example_gitlab_gchat_request,
            ).json(),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(
            message.body,
            "John Doe pushed to branch [master](https://gitlab.com/jdoe/test/commits/m"
            + "aster) of [John Doe / test](https://gitlab.com/jdoe/test) ([Compare chan"
            + "ges](https://gitlab.com/jdoe/test/compare/b76004b20503d4d506e51a670de095"
            + "cc063e4707...3517b06c64c9d349e2213650d6c009db0471361e))\n[3517b06c](http"
            + "s://gitlab.com/jdoe/test/-/commit/3517b06c64c9d349e2213650d6c009db047136"
            + "1e): Merge branch 'prod' into 'master' - John Doe\n\n[1f661795](https://"
            + "gitlab.com/jdoe/test/-/commit/1f661795b220c5fe352f391eb8de3ac4fcc6fc1d):"
            + " Merge branch 'revert-a827b196' into 'prod' - John Doe\n\n[b76004b2](htt"
            + "ps://gitlab.com/jdoe/test/-/commit/b76004b20503d4d506e51a670de095cc063e4"
            + "707): Merge branch 'revert-a827b196' into 'master' - John Doe",
        )
