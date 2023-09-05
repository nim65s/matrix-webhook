import json
from dataclasses import dataclass
from os import path, makedirs


@dataclass
class MatrixData:
    access_token: str
    device_id: str
    encryption: bool
    _file_exists: bool = False


class DataStorage:

    def __init__(self, location):
        """Constructor"""
        self.session_folder = location

        self.filename = self.session_folder + "/data.json"

        if not path.exists(self.session_folder):
            makedirs(self.session_folder)

    def exists(self):
        """Check if the data exists."""
        return path.exists(self.filename)

    def get_session_storage_location(self):
        """Get the path for the session storage."""
        return self.session_folder

    def write_account_data(self, data: MatrixData):
        """Save the matrix data """
        data._file_exists = True
        data_text = json.dumps(data.__dict__)

        with open(self.filename, "w") as file:
            file.seek(0)
            file.write(data_text)
            file.truncate()

    def read_account_data(self):
        """Read the matrix data."""
        if not self.exists():
            return MatrixData("", "", False)

        with open(self.filename, "r") as file:
            parsed_json = json.load(file)

            return MatrixData(access_token=parsed_json["access_token"], device_id=parsed_json["device_id"], encryption=parsed_json["encryption"], _file_exists=True)