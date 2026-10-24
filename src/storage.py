"""Saving and loading the book collection as a JSON file."""

import json
from pathlib import Path

from .models import Book, InvalidBookError, StorageError


class JsonStorage:
    """Reads and writes a list of books to a single JSON file.

    Attributes:
        file_path: Location of the JSON data file.
    """

    def __init__(self, file_path: str | Path = "data/data.json") -> None:
        """Remember where the data file lives.

        Args:
            file_path: Path to the JSON file. Neither the file nor its
                folder needs to exist yet; both are created on the
                first save.
        """
        self.file_path = Path(file_path)

    def load(self) -> list[Book]:
        """Load all books from the data file.

        Returns:
            The saved books, or an empty list if the file does not
            exist yet (for example on the very first run).

        Raises:
            StorageError: If the file cannot be read or is not valid.
        """
        if not self.file_path.exists():
            return []
        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                raw_books = json.load(file)
        except json.JSONDecodeError as err:
            raise StorageError(
                f"'{self.file_path}' is not valid JSON."
            ) from err
        except OSError as err:
            raise StorageError(
                f"Could not read '{self.file_path}': {err}"
            ) from err

        if not isinstance(raw_books, list):
            raise StorageError(
                f"'{self.file_path}' should contain a list of books."
            )
        try:
            return [Book.from_dict(item) for item in raw_books]
        except InvalidBookError as err:
            raise StorageError(
                f"'{self.file_path}' contains a bad record: {err}"
            ) from err

    def save(self, books: list[Book]) -> None:
        """Write all books to the data file, replacing its contents.

        Args:
            books: The full collection to save.

        Raises:
            StorageError: If the file cannot be written.
        """
        data = [book.to_dict() for book in books]
        try:
            # Create the data/ folder if it is missing (e.g. fresh clone).
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.file_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
        except OSError as err:
            raise StorageError(
                f"Could not save to '{self.file_path}': {err}"
            ) from err
