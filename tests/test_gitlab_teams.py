"""
Test module for gitlab "teams" formatter.

"""

import unittest

import httpx
import nio

from .start import BOT_URL, FULL_ID, KEY, MATRIX_ID, MATRIX_PW, MATRIX_URL


class GitlabTeamsFormatterTest(unittest.IsolatedAsyncioTestCase):
    """Gitlab "teams" formatter test class."""

    async def test_gitlab_teams_body(self):
        """Send a markdown message, and check the result."""
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        with open("tests/example_gitlab_teams.json") as f:
            example_gitlab_teams_request = f.read()
        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                params={"formatter": "gitlab_teams", "key": KEY},
                content=example_gitlab_teams_request,
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
            "John Doe pushed to branch [master](https://gitlab.com/jdoe/test/commits"
            + "/master) in [John Doe / test](https://gitlab.com/jdoe/test) \u2192 [Com"
            + "pare changes](https://gitlab.com/jdoe/test/compare/b76004b20503d4d506e5"
            + "1a670de095cc063e4707...3517b06c64c9d349e2213650d6c009db0471361e)  \n\n*"
            + " [3517b06c](https://gitlab.com/jdoe/test/-/commit/3517b06c64c9d349e2213"
            + "650d6c009db0471361e): Merge branch 'prod' into 'master' - John Doe  \n*"
            + " [1f661795](https://gitlab.com/jdoe/test/-/commit/1f661795b220c5fe352f3"
            + "91eb8de3ac4fcc6fc1d): Merge branch 'revert-a827b196' into 'prod' - John"
            + " Doe  \n* [b76004b2](https://gitlab.com/jdoe/test/-/commit/b76004b20503"
            + "d4d506e51a670de095cc063e4707): Merge branch 'revert-a827b196' into 'mas"
            + "ter' - John Doe",
        )
