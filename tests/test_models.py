"""Tests for the Book class in src/models.py."""

import unittest
from datetime import date
from typing import Any

from src.models import Book, InvalidBookError


def make_book(**overrides: Any) -> Book:
    """Return a valid Book, with any fields replaced by ``overrides``."""
    data: dict[str, Any] = {
        "book_id": 1,
        "title": "Dune",
        "author": "Frank Herbert",
        "genre": "Sci-Fi",
        "total_pages": 400,
    }
    data.update(overrides)
    return Book(**data)


class TestBookCreation(unittest.TestCase):
    """Creating books with valid and invalid data."""

    def test_valid_book_has_defaults(self) -> None:
        """A new book starts as to-read on page 0."""
        book = make_book()
        self.assertEqual(book.status, "to-read")
        self.assertEqual(book.current_page, 0)
        self.assertIsNone(book.finish_date)

    def test_whitespace_is_trimmed(self) -> None:
        """Leading and trailing spaces are removed from text fields."""
        book = make_book(title="  Dune  ", status=" Reading ")
        self.assertEqual(book.title, "Dune")
        self.assertEqual(book.status, "reading")

    def test_empty_title_is_rejected(self) -> None:
        """A blank title raises InvalidBookError."""
        with self.assertRaises(InvalidBookError):
            make_book(title="   ")

    def test_zero_pages_is_rejected(self) -> None:
        """Total pages must be above zero."""
        with self.assertRaises(InvalidBookError):
            make_book(total_pages=0)

    def test_unknown_status_is_rejected(self) -> None:
        """Only the three known statuses are allowed."""
        with self.assertRaises(InvalidBookError):
            make_book(status="abandoned")

    def test_bad_finish_date_is_rejected(self) -> None:
        """Finish dates must be in YYYY-MM-DD format."""
        with self.assertRaises(InvalidBookError):
            make_book(finish_date="24/10/2026")

    def test_added_as_finished_gets_date_and_full_pages(self) -> None:
        """A book created as finished is fully read and dated."""
        book = make_book(status="finished")
        self.assertEqual(book.current_page, 400)
        self.assertEqual(book.finish_date, date.today().isoformat())


class TestBookProgress(unittest.TestCase):
    """Updating progress and finishing a book."""

    def test_progress_moves_to_read_into_reading(self) -> None:
        """Updating progress on a to-read book starts reading it."""
        book = make_book()
        book.update_progress(120)
        self.assertEqual(book.status, "reading")
        self.assertEqual(book.current_page, 120)
        self.assertEqual(book.progress_percent, 30)

    def test_page_out_of_range_is_rejected(self) -> None:
        """Pages above the total (or negative) are not allowed."""
        book = make_book(status="reading")
        with self.assertRaises(InvalidBookError):
            book.update_progress(401)
        with self.assertRaises(InvalidBookError):
            book.update_progress(-1)

    def test_reaching_last_page_finishes_book(self) -> None:
        """Reading the last page marks the book as finished."""
        book = make_book(status="reading")
        book.update_progress(400)
        self.assertEqual(book.status, "finished")
        self.assertIsNotNone(book.finish_date)

    def test_progress_on_finished_book_is_rejected(self) -> None:
        """A finished book's progress cannot be changed."""
        book = make_book(status="finished")
        with self.assertRaises(InvalidBookError):
            book.update_progress(10)

    def test_mark_finished_records_date(self) -> None:
        """Marking finished sets status, pages and the given date."""
        book = make_book(status="reading", current_page=50)
        book.mark_finished(date(2026, 3, 15))
        self.assertEqual(book.status, "finished")
        self.assertEqual(book.current_page, 400)
        self.assertEqual(book.finish_date, "2026-03-15")

    def test_mark_finished_twice_is_rejected(self) -> None:
        """A book cannot be finished twice."""
        book = make_book(status="finished")
        with self.assertRaises(InvalidBookError):
            book.mark_finished()


class TestBookSerialisation(unittest.TestCase):
    """Converting books to and from dictionaries."""

    def test_round_trip(self) -> None:
        """to_dict followed by from_dict gives an equal book."""
        book = make_book(status="reading", current_page=42)
        self.assertEqual(Book.from_dict(book.to_dict()), book)

    def test_missing_key_is_rejected(self) -> None:
        """A record without a title raises InvalidBookError."""
        data = make_book().to_dict()
        del data["title"]
        with self.assertRaises(InvalidBookError):
            Book.from_dict(data)

    def test_non_numeric_pages_are_rejected(self) -> None:
        """A record with text in total_pages raises InvalidBookError."""
        data = make_book().to_dict()
        data["total_pages"] = "lots"
        with self.assertRaises(InvalidBookError):
            Book.from_dict(data)


if __name__ == "__main__":
    unittest.main()
