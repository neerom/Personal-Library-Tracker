"""Business logic for managing the book collection.

The ``Library`` class keeps a list of ``Book`` objects in memory and,
when it is given a storage object, saves the list after every change.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import date

from .models import VALID_STATUSES, Book, BookNotFoundError, InvalidBookError
from .storage import JsonStorage


@dataclass
class LibraryStats:
    """Summary numbers shown on the statistics screen.

    Attributes:
        total_books: Number of books in the collection.
        finished_books: Number of books marked "finished".
        finished_this_year: Books finished in the current calendar year.
        average_pages: Average page count of finished books.
        favorite_genre: Genre with the most finished books, or None.
    """

    total_books: int
    finished_books: int
    finished_this_year: int
    average_pages: float
    favorite_genre: str | None


class Library:
    """A collection of books with add, search, update and stats actions.

    The Library *has a* list of Book objects and *has a* storage object
    (composition). Every method that changes the collection saves it.
    """

    def __init__(self, storage: JsonStorage | None = None) -> None:
        """Create the library and load any previously saved books.

        Args:
            storage: Where to save books. ``None`` keeps the books in
                memory only, which is useful in tests.

        Raises:
            StorageError: If the saved data cannot be loaded.
        """
        self._storage = storage
        self._books: list[Book] = storage.load() if storage else []

    def __len__(self) -> int:
        """Return the number of books in the library."""
        return len(self._books)

    def add_book(
        self, title: str, author: str, genre: str, total_pages: int,
        status: str = "to-read",
    ) -> Book:
        """Create a new book, add it to the collection and save.

        Args:
            title: Book title.
            author: Author name.
            genre: Book genre.
            total_pages: Number of pages (must be above 0).
            status: "to-read", "reading" or "finished".

        Returns:
            The newly added Book (with its ID filled in).

        Raises:
            InvalidBookError: If any of the values are invalid.
        """
        book = Book(
            book_id=self._next_id(),
            title=title,
            author=author,
            genre=genre,
            total_pages=total_pages,
            status=status,
        )
        self._books.append(book)
        self._save()
        return book

    def get_book(self, book_id: int) -> Book:
        """Return the book with the given ID.

        Raises:
            BookNotFoundError: If no book has that ID.
        """
        for book in self._books:
            if book.book_id == book_id:
                return book
        raise BookNotFoundError(f"No book with ID {book_id}.")

    def list_books(
        self, status: str | None = None, genre: str | None = None
    ) -> list[Book]:
        """Return all books, optionally filtered by status and/or genre.

        Args:
            status: Only include books with this status.
            genre: Only include books of this genre (case-insensitive).

        Raises:
            InvalidBookError: If ``status`` is not a valid status.
        """
        if status is not None and status not in VALID_STATUSES:
            raise InvalidBookError(
                f"Status must be one of: {', '.join(VALID_STATUSES)}."
            )
        books = list(self._books)
        if status:
            books = [book for book in books if book.status == status]
        if genre:
            wanted = genre.strip().lower()
            books = [book for book in books if book.genre.lower() == wanted]
        return books

    def search(self, query: str) -> list[Book]:
        """Find books whose title or author contains ``query``.

        The match is case-insensitive and partial, so "tolk" finds
        "J.R.R. Tolkien". An empty query returns no books.
        """
        text = query.strip().lower()
        if not text:
            return []
        return [
            book for book in self._books
            if text in book.title.lower() or text in book.author.lower()
        ]

    def update_progress(self, book_id: int, page: int) -> Book:
        """Set the current page of a book and save.

        Raises:
            BookNotFoundError: If no book has that ID.
            InvalidBookError: If the page is out of range or the book
                is already finished.
        """
        book = self.get_book(book_id)
        book.update_progress(page)
        self._save()
        return book

    def mark_finished(
        self, book_id: int, finish_date: date | None = None
    ) -> Book:
        """Mark a book as finished (recording the date) and save.

        Args:
            book_id: ID of the book to finish.
            finish_date: Date to record. Defaults to today.

        Raises:
            BookNotFoundError: If no book has that ID.
            InvalidBookError: If the book is already finished.
        """
        book = self.get_book(book_id)
        book.mark_finished(finish_date)
        self._save()
        return book

    def remove_book(self, book_id: int) -> Book:
        """Remove a book from the collection and save.

        Returns:
            The book that was removed.

        Raises:
            BookNotFoundError: If no book has that ID.
        """
        book = self.get_book(book_id)
        self._books.remove(book)
        self._save()
        return book

    def statistics(self, today: date | None = None) -> LibraryStats:
        """Calculate summary statistics for the collection.

        Args:
            today: The date used to decide the "current year".
                Defaults to the real date (tests pass a fixed one).
        """
        year = (today or date.today()).year
        finished = [book for book in self._books if book.status == "finished"]
        finished_this_year = [
            book for book in finished
            if book.finish_date
            and date.fromisoformat(book.finish_date).year == year
        ]
        average_pages = (
            sum(book.total_pages for book in finished) / len(finished)
            if finished else 0.0
        )
        genre_counts = Counter(book.genre for book in finished)
        favorite_genre = (
            genre_counts.most_common(1)[0][0] if genre_counts else None
        )
        return LibraryStats(
            total_books=len(self._books),
            finished_books=len(finished),
            finished_this_year=len(finished_this_year),
            average_pages=round(average_pages, 1),
            favorite_genre=favorite_genre,
        )

    def _next_id(self) -> int:
        """Return the next unused book ID (highest ID + 1)."""
        return max((book.book_id for book in self._books), default=0) + 1

    def _save(self) -> None:
        """Save the collection if a storage object was provided."""
        if self._storage is not None:
            self._storage.save(self._books)
