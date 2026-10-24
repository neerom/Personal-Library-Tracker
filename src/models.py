"""Data model and custom exceptions for the Personal Library app.

This module defines the ``Book`` class (one book in the collection)
and the custom exceptions the rest of the app raises when something
goes wrong.
"""

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

VALID_STATUSES: tuple[str, ...] = ("to-read", "reading", "finished")


class LibraryError(Exception):
    """Base class for every error raised by this app."""


class BookNotFoundError(LibraryError):
    """Raised when no book matches the requested ID."""


class InvalidBookError(LibraryError):
    """Raised when book data, or an action on a book, is not valid."""


class StorageError(LibraryError):
    """Raised when the data file cannot be read or written."""


@dataclass
class Book:  # pylint: disable=too-many-instance-attributes
    """One book in the collection, together with its reading progress.

    Attributes:
        book_id: Unique number given to the book by the Library.
        title: Book title.
        author: Author name.
        genre: Genre, for example "Fantasy".
        total_pages: Number of pages in the book (must be above 0).
        status: One of "to-read", "reading" or "finished".
        current_page: Last page the reader reached.
        finish_date: Date the book was finished as "YYYY-MM-DD",
            or None if it is not finished yet.
    """

    book_id: int
    title: str
    author: str
    genre: str
    total_pages: int
    status: str = "to-read"
    current_page: int = 0
    finish_date: str | None = None

    def __post_init__(self) -> None:
        """Clean up and validate the fields after the book is created.

        Raises:
            InvalidBookError: If any field has an invalid value.
        """
        self.title = self.title.strip()
        self.author = self.author.strip()
        self.genre = self.genre.strip()
        self.status = self.status.strip().lower()

        if not (self.title and self.author and self.genre):
            raise InvalidBookError("Title, author and genre cannot be empty.")
        if self.total_pages <= 0:
            raise InvalidBookError("Total pages must be greater than 0.")
        if self.status not in VALID_STATUSES:
            raise InvalidBookError(
                f"Status must be one of: {', '.join(VALID_STATUSES)}."
            )
        if not 0 <= self.current_page <= self.total_pages:
            raise InvalidBookError(
                f"Current page must be between 0 and {self.total_pages}."
            )
        if self.finish_date is not None:
            try:
                date.fromisoformat(self.finish_date)
            except (TypeError, ValueError) as err:
                raise InvalidBookError(
                    f"Finish date '{self.finish_date}' is not YYYY-MM-DD."
                ) from err

        # A book added as "finished" is fully read and needs a date.
        if self.status == "finished":
            self.current_page = self.total_pages
            if self.finish_date is None:
                self.finish_date = date.today().isoformat()

    @property
    def progress_percent(self) -> int:
        """Return how much of the book has been read, from 0 to 100."""
        return round(self.current_page * 100 / self.total_pages)

    def update_progress(self, page: int) -> None:
        """Record the page the reader has reached.

        A "to-read" book moves to "reading" automatically, and reaching
        the last page marks the book as finished.

        Args:
            page: The current page number.

        Raises:
            InvalidBookError: If the book is already finished or the
                page number is out of range.
        """
        if self.status == "finished":
            raise InvalidBookError(f"'{self.title}' is already finished.")
        if not 0 <= page <= self.total_pages:
            raise InvalidBookError(
                f"Page must be between 0 and {self.total_pages}."
            )
        self.status = "reading"
        self.current_page = page
        if page == self.total_pages:
            self.mark_finished()

    def mark_finished(self, finish_date: date | None = None) -> None:
        """Mark the book as finished and record the finish date.

        Args:
            finish_date: The date to record. Defaults to today.

        Raises:
            InvalidBookError: If the book is already finished.
        """
        if self.status == "finished":
            raise InvalidBookError(f"'{self.title}' is already finished.")
        self.status = "finished"
        self.current_page = self.total_pages
        self.finish_date = (finish_date or date.today()).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Return the book as a plain dictionary, ready to save as JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Book":
        """Create a Book from a dictionary that was loaded from JSON.

        Args:
            data: A dictionary with the same keys ``to_dict`` produces.

        Returns:
            The new Book.

        Raises:
            InvalidBookError: If keys are missing or values are invalid.
        """
        try:
            return cls(
                book_id=int(data["book_id"]),
                title=str(data["title"]),
                author=str(data["author"]),
                genre=str(data["genre"]),
                total_pages=int(data["total_pages"]),
                status=str(data.get("status", "to-read")),
                current_page=int(data.get("current_page", 0)),
                finish_date=data.get("finish_date"),
            )
        except (KeyError, TypeError, ValueError) as err:
            raise InvalidBookError(f"Invalid book record ({err}).") from err

    def __str__(self) -> str:
        """Return a one-line, human-friendly description of the book."""
        text = (
            f"[{self.book_id}] {self.title} by {self.author} "
            f"| {self.genre} | {self.status} "
            f"| {self.current_page}/{self.total_pages} pages "
            f"({self.progress_percent}%)"
        )
        if self.finish_date:
            text += f" | finished {self.finish_date}"
        return text
