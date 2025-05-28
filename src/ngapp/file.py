"""File handling for the client."""

import json
import os
import zipfile

from .utils import read_file, set_directory, write_file, zip_directory


class SpecialFile:
    """A file with special handling.
    Stored as directory on backend"""

    path_: str = ""

    def __init__(self, path):
        self.path_ = path

    def path(self, *args):
        """Return the path to this file, optionally appending the given path elements."""
        return os.path.join(self.path_, *args) if args else self.path_

    def get_metadata(self):
        """Return the metadata of the file."""
        return json.loads(read_file(self.path("metadata")))

    async def upload(self):
        """Upload the file to the backend as zip."""
        with set_directory(self.path()):
            data = zip_directory(".")
            await file_api.upload(self.get_metadata(), data)

    def load(self):
        """Load the data."""
        return json.loads(read_file(self.path("data")))

    def save(self, data: dict):
        """Save the data."""
        write_file(self.path("data"), json.dumps(data, indent=4))

    def extract(self, zipped_data):
        """Extracted the zipped data."""
        with set_directory(os.path.dirname(self.path())):
            with zipfile.ZipFile(zipped_data, "r") as archive:
                archive.extractall()

    @staticmethod
    def get_file(path):
        """Return the file with the given id and type."""
        file_type = SpecialFile(path).get_metadata()["file_type"]
        return _file_types[file_type](path)


_file_types = {}


def register_filetype(typ):
    """Decorator to register a file custom SpecialFile type."""
    _file_types[typ._type] = typ
    return typ


@register_filetype
class SimulationFile(SpecialFile):
    """A simulation file (representing a job on the backend)."""

    _type = "simulation"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_type = SimulationFile._type
        os.makedirs(self.path(), exist_ok=True)
        if not os.path.exists(self.path("data")):
            self.save({})
