"""Tests for the Library class in src/library.py."""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.library import Library
from src.models import BookNotFoundError, InvalidBookError
from src.storage import JsonStorage


class TestLibraryBasics(unittest.TestCase):
    """Adding, finding, filtering, searching and removing books."""

    def setUp(self) -> None:
        """Create an in-memory library with three books."""
        self.library = Library()
        self.library.add_book("Dune", "Frank Herbert", "Sci-Fi", 412)
        self.library.add_book(
            "The Hobbit", "J.R.R. Tolkien", "Fantasy", 310, "reading"
        )
        self.library.add_book(
            "The Silmarillion", "J.R.R. Tolkien", "Fantasy", 365
        )

    def test_ids_are_assigned_in_order(self) -> None:
        """Each new book gets the next ID."""
        ids = [book.book_id for book in self.library.list_books()]
        self.assertEqual(ids, [1, 2, 3])

    def test_ids_are_not_reused_after_middle_removal(self) -> None:
        """New IDs continue from the highest existing ID."""
        self.library.remove_book(2)
        book = self.library.add_book("Emma", "Jane Austen", "Classic", 474)
        self.assertEqual(book.book_id, 4)

    def test_invalid_book_is_not_added(self) -> None:
        """Invalid data raises an error and nothing is added."""
        with self.assertRaises(InvalidBookError):
            self.library.add_book("", "Someone", "Drama", 100)
        self.assertEqual(len(self.library), 3)

    def test_get_missing_book_raises(self) -> None:
        """Asking for an unknown ID raises BookNotFoundError."""
        with self.assertRaises(BookNotFoundError):
            self.library.get_book(99)

    def test_filter_by_status(self) -> None:
        """Only books with the chosen status are returned."""
        books = self.library.list_books(status="reading")
        self.assertEqual([book.title for book in books], ["The Hobbit"])

    def test_filter_by_genre_is_case_insensitive(self) -> None:
        """'fantasy' matches books saved as 'Fantasy'."""
        self.assertEqual(len(self.library.list_books(genre="fantasy")), 2)

    def test_filter_by_invalid_status_raises(self) -> None:
        """An unknown status filter raises InvalidBookError."""
        with self.assertRaises(InvalidBookError):
            self.library.list_books(status="paused")

    def test_search_title_partial_case_insensitive(self) -> None:
        """'HOB' finds 'The Hobbit'."""
        books = self.library.search("HOB")
        self.assertEqual([book.title for book in books], ["The Hobbit"])

    def test_search_author(self) -> None:
        """'tolkien' finds both Tolkien books."""
        self.assertEqual(len(self.library.search("tolkien")), 2)

    def test_search_empty_query_returns_nothing(self) -> None:
        """A blank search returns an empty list."""
        self.assertEqual(self.library.search("   "), [])

    def test_remove_book(self) -> None:
        """Removing a book takes it out of the collection."""
        removed = self.library.remove_book(1)
        self.assertEqual(removed.title, "Dune")
        self.assertEqual(len(self.library), 2)

    def test_remove_missing_book_raises(self) -> None:
        """Removing an unknown ID raises BookNotFoundError."""
        with self.assertRaises(BookNotFoundError):
            self.library.remove_book(42)


class TestLibraryStatistics(unittest.TestCase):
    """The statistics summary."""

    def test_empty_library(self) -> None:
        """An empty library reports zeros and no favourite genre."""
        stats = Library().statistics()
        self.assertEqual(stats.total_books, 0)
        self.assertEqual(stats.average_pages, 0.0)
        self.assertIsNone(stats.favorite_genre)

    def test_statistics_values(self) -> None:
        """Counts, this-year total, average and favourite genre."""
        library = Library()
        library.add_book("A", "Author A", "Fantasy", 300)
        library.add_book("B", "Author B", "Fantasy", 500)
        library.add_book("C", "Author C", "Sci-Fi", 200)
        library.add_book("D", "Author D", "Sci-Fi", 999)  # never finished
        library.mark_finished(1, date(2026, 2, 1))
        library.mark_finished(2, date(2026, 6, 1))
        library.mark_finished(3, date(2025, 12, 31))

        stats = library.statistics(today=date(2026, 10, 24))

        self.assertEqual(stats.total_books, 4)
        self.assertEqual(stats.finished_books, 3)
        self.assertEqual(stats.finished_this_year, 2)
        self.assertEqual(stats.average_pages, 333.3)
        self.assertEqual(stats.favorite_genre, "Fantasy")


class TestLibraryPersistence(unittest.TestCase):
    """Changes are saved to disk and loaded again on the next run."""

    def setUp(self) -> None:
        """Create a temporary folder for the data file."""
        temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=R1732
        self.addCleanup(temp_dir.cleanup)
        self.data_file = Path(temp_dir.name) / "data.json"

    def test_changes_survive_restart(self) -> None:
        """A second Library on the same file sees the saved changes."""
        first_run = Library(JsonStorage(self.data_file))
        first_run.add_book("Dune", "Frank Herbert", "Sci-Fi", 412)
        first_run.update_progress(1, 100)

        second_run = Library(JsonStorage(self.data_file))
        book = second_run.get_book(1)
        self.assertEqual(book.title, "Dune")
        self.assertEqual(book.current_page, 100)
        self.assertEqual(book.status, "reading")


if __name__ == "__main__":
    unittest.main()
