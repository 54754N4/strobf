from __future__ import annotations

from io import StringIO


class StringBuilder:
    _file_str = None

    def __init__(self):
        self._file_str = StringIO()

    def append(self, fmt: str) -> StringBuilder:
        self._file_str.write(fmt)
        return self

    def to_string(self) -> str:
        return self._file_str.getvalue()

    def __str__(self) -> str:
        return self.to_string()

    def close(self) -> None:
        self._file_str.close()

    # with statement methods

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
