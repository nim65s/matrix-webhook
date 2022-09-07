"""
Test version 9 compatibility of grafana formatter.

ref https://grafana.com/docs/grafana/latest/alerting/old-alerting/notifications/#webhook
"""

import unittest

import httpx
import nio

from .start import BOT_URL, FULL_ID, MATRIX_ID, MATRIX_PW, MATRIX_URL


class GrafanaForwardFormatterTest(unittest.IsolatedAsyncioTestCase):
    """Grafana formatter test class."""

    async def test_grafana_body(self):
        """Send a markdown message, and check the result."""
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        with open("tests/example_grafana_9x.json") as f:
            example_grafana_request = f.read()
        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                params={"formatter": "grafana"},
                content=example_grafana_request,
            ).json(),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        expected_body = (
            "#### [FIRING:1]  (TestAlert Grafana)\n**Firing**\n\n\n\nValue: [ metr"
            "ic='foo' labels={instance=bar} value=10 ]\n\nLabels:\n\n - alertname "
            "= TestAlert\n\n - instance = Grafana\n\nAnnotations:\n\n - summary = "
            "Notification test\n\nSilence: https://grafana.example.com/alerting/si"
            "lence/new?alertmanager=grafana&matcher=alertname%3DTestAlert&matcher="
            "instance%3DGrafana\n\n\n\n"
        )
        self.assertEqual(message.body, expected_body)
