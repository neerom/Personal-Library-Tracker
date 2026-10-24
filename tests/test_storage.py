"""Tests for JsonStorage in src/storage.py."""

import tempfile
import unittest
from pathlib import Path

from src.models import Book, StorageError
from src.storage import JsonStorage


class TestJsonStorage(unittest.TestCase):
    """Saving and loading the JSON data file."""

    def setUp(self) -> None:
        """Create a temporary folder and a storage object inside it."""
        temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=R1732
        self.addCleanup(temp_dir.cleanup)
        self.data_file = Path(temp_dir.name) / "data.json"
        self.storage = JsonStorage(self.data_file)

    def test_missing_file_loads_empty_list(self) -> None:
        """On the first run there is no file, so no books."""
        self.assertEqual(self.storage.load(), [])

    def test_save_then_load(self) -> None:
        """Saved books are loaded back unchanged."""
        books = [
            Book(1, "Dune", "Frank Herbert", "Sci-Fi", 412),
            Book(2, "Emma", "Jane Austen", "Classic", 474, "finished"),
        ]
        self.storage.save(books)
        self.assertEqual(self.storage.load(), books)

    def test_save_creates_missing_data_folder(self) -> None:
        """Saving into a data/ folder that does not exist creates it."""
        nested = JsonStorage(self.data_file.parent / "data" / "data.json")
        nested.save([Book(1, "Dune", "Frank Herbert", "Sci-Fi", 412)])
        self.assertTrue(nested.file_path.exists())
        self.assertEqual(len(nested.load()), 1)

    def test_empty_list_file_loads_no_books(self) -> None:
        """A data file containing [] (the shipped file) loads cleanly."""
        self.data_file.write_text("[]\n", encoding="utf-8")
        self.assertEqual(self.storage.load(), [])

    def test_corrupt_json_raises_storage_error(self) -> None:
        """A file that is not valid JSON raises StorageError."""
        self.data_file.write_text("{ not json", encoding="utf-8")
        with self.assertRaises(StorageError):
            self.storage.load()

    def test_wrong_shape_raises_storage_error(self) -> None:
        """A JSON object instead of a list raises StorageError."""
        self.data_file.write_text('{"title": "Dune"}', encoding="utf-8")
        with self.assertRaises(StorageError):
            self.storage.load()

    def test_bad_record_raises_storage_error(self) -> None:
        """A record with missing fields raises StorageError."""
        self.data_file.write_text('[{"title": "Dune"}]', encoding="utf-8")
        with self.assertRaises(StorageError):
            self.storage.load()


if __name__ == "__main__":
    unittest.main()
