import logging
import sys

from nio import AsyncClientConfig, AsyncClient, LoginResponse, JoinError, RoomSendError

from matrix_webhook.storage import DataStorage, MatrixData
import conf

LOGGER = logging.getLogger("matrix_webhook.matrix")

class MatrixClient:

    def __init__(self, storage: DataStorage):
        """Constructor"""
        self._storage = storage
        self._data = self._storage.read_account_data()

        self._client_config = AsyncClientConfig(
            max_limit_exceeded=0,
            max_timeouts=0,
            store_sync_tokens=True,
            encryption_enabled=conf.E2E)

        if not self._is_encryption_valid():
            print("Encryption config invalid.")
            sys.exit(1)

        storage_path = None
        if conf.E2E:
            print("Enable encryption")
            storage_path = self._storage.get_session_storage_location()

        self._client = AsyncClient(
            conf.MATRIX_URL,
            conf.MATRIX_ID,
            store_path=storage_path,
            config=self._client_config)

    def _is_encryption_valid(self):
        """Check if the encryption config is valid."""
        if not self._data._file_exists:
            return True
        return conf.E2E == self._data.encryption

    async def _load_key(self):
        await self._client.import_keys(self._storage.get_session_storage_location() + "/element-keys.txt",
                                       conf.KEY_PASSWORD)

        if self._client.should_upload_keys:
            await self._client.keys_upload()

    async def _first_login(self):
        """First time login."""
        resp = await self._client.login(conf.MATRIX_PW, device_name="matrix-webhook")

        if not isinstance(resp, LoginResponse):
            raise MatrixException(resp.message, resp)

        self._data = MatrixData(device_id=self._client.device_id, access_token=self._client.access_token, encryption=conf.E2E)
        self._storage.write_account_data(self._data)

        if conf.E2E:
            await self._load_key()

        await self._client.sync(timeout=30000, full_state=True)

    async def _restore_login(self):
        """Restore login from file."""
        self._data = self._storage.read_account_data()

        self._client.restore_login(
            user_id=conf.MATRIX_ID,
            device_id=self._data.device_id,
            access_token=self._data.access_token
        )

        if conf.E2E:
            self._client.load_store()

        if self._client.should_upload_keys:
            await self._client.keys_upload()

        await self._client.sync(timeout=30000, full_state=True)


    async def login(self):
        """Log the user in."""
        if not self._storage.exists():
            await self._first_login()
        else:
            await self._restore_login()

    async def close(self):
        """Close connection."""
        await self._client.close()

    async def join_room(self, room_id):
        """Join a room."""
        resp = await self._client.join(room_id)

        if isinstance(resp, JoinError):
            raise MatrixException(resp.message, resp)

    async def send_message(self, room_id, content):
        """Send a message into a room."""
        resp = await self._client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content=content,
            ignore_unverified_devices=True
        )
        if isinstance(resp, RoomSendError):
            raise MatrixException(resp.message, resp)

class MatrixException(Exception):
    def __init__(self, message: str, response) -> None:
        """Initialize."""
        super().__init__(message)
        self.response = response