"""Command-line interface for the Personal Library app.

The app can be used in two ways:

* Command-line arguments (argparse) for one quick action, for example
  ``python main.py add "Dune" "Frank Herbert" Sci-Fi 412``.
* An interactive text menu, shown when no command is given.

All user input is read and checked here, so bad input (letters where a
number is expected, unknown statuses, missing IDs) never crashes the
program.
"""

import argparse
import sys
from collections.abc import Callable

from .library import Library, LibraryStats
from .models import VALID_STATUSES, Book, LibraryError

MENU = """
========== Personal Library ==========
1. Add a book
2. View all books
3. Update reading progress
4. Mark a book as finished
5. Remove a book
6. Search books
7. View statistics
0. Exit
======================================"""


def ask_text(prompt: str, allow_empty: bool = False) -> str:
    """Ask until the user types some text (or just Enter, if allowed)."""
    while True:
        answer = input(prompt).strip()
        if answer or allow_empty:
            return answer
        print("This field cannot be empty.")


def ask_int(prompt: str, minimum: int = 0) -> int:
    """Ask until the user types a whole number of at least ``minimum``."""
    while True:
        answer = input(prompt).strip()
        try:
            number = int(answer)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if number < minimum:
            print(f"Please enter a number of at least {minimum}.")
            continue
        return number


def ask_status(prompt: str, allow_empty: bool = False) -> str:
    """Ask until the user types a valid status (or Enter, if allowed)."""
    options = "/".join(VALID_STATUSES)
    while True:
        answer = input(f"{prompt} [{options}]: ").strip().lower()
        if answer in VALID_STATUSES or (allow_empty and not answer):
            return answer
        print(f"Status must be one of: {', '.join(VALID_STATUSES)}.")


def print_books(books: list[Book]) -> None:
    """Print one line per book, or a message if the list is empty."""
    if not books:
        print("No books found.")
        return
    for book in books:
        print(book)


def print_statistics(stats: LibraryStats) -> None:
    """Print the summary statistics, one labelled line each."""
    rows = [
        ("Total books", stats.total_books),
        ("Books finished", stats.finished_books),
        ("Finished this year", stats.finished_this_year),
        ("Avg pages per finished book", stats.average_pages),
        ("Favorite genre", stats.favorite_genre or "-"),
    ]
    for label, value in rows:
        print(f"{label + ':':<30}{value}")


class LibraryCLI:
    """Interactive menu that connects the user to a Library."""

    def __init__(self, library: Library) -> None:
        """Store the library and map each menu number to an action."""
        self.library = library
        self.actions: dict[str, Callable[[], None]] = {
            "1": self.add_book,
            "2": self.view_books,
            "3": self.update_progress,
            "4": self.mark_finished,
            "5": self.remove_book,
            "6": self.search_books,
            "7": self.show_statistics,
        }

    def run(self) -> None:
        """Show the menu in a loop until the user chooses to exit."""
        print("Welcome to your Personal Library & Reading Tracker!")
        try:
            while True:
                print(MENU)
                choice = input("Choose an option: ").strip()
                if choice == "0":
                    break
                action = self.actions.get(choice)
                if action is None:
                    print("Invalid choice. Enter a number from the menu.")
                    continue
                try:
                    action()
                except LibraryError as err:
                    print(f"Error: {err}")
        except (KeyboardInterrupt, EOFError):
            print()
        print("Goodbye! Your library is saved.")

    def add_book(self) -> None:
        """Ask for the book's details and add it to the library."""
        title = ask_text("Title: ")
        author = ask_text("Author: ")
        genre = ask_text("Genre: ")
        total_pages = ask_int("Total pages: ", minimum=1)
        status = ask_status("Status (Enter = to-read)", allow_empty=True)
        book = self.library.add_book(
            title, author, genre, total_pages, status or "to-read"
        )
        print(f"Added: {book}")

    def view_books(self) -> None:
        """Show all books, with optional status and genre filters."""
        status = ask_status("Filter by status (Enter = all)", allow_empty=True)
        genre = ask_text("Filter by genre (Enter = all): ", allow_empty=True)
        print_books(self.library.list_books(status or None, genre or None))

    def update_progress(self) -> None:
        """Ask for a book and its current page, then save the progress."""
        unfinished = [
            book for book in self.library.list_books()
            if book.status != "finished"
        ]
        book_id = self._pick_book_id(unfinished)
        if book_id is None:
            return
        page = ask_int("Current page: ")
        book = self.library.update_progress(book_id, page)
        print(f"Updated: {book}")

    def mark_finished(self) -> None:
        """Ask for a book and mark it as finished with today's date."""
        unfinished = [
            book for book in self.library.list_books()
            if book.status != "finished"
        ]
        book_id = self._pick_book_id(unfinished)
        if book_id is None:
            return
        book = self.library.mark_finished(book_id)
        print(f"Well done! {book}")

    def remove_book(self) -> None:
        """Ask for a book, confirm, and remove it from the library."""
        book_id = self._pick_book_id(self.library.list_books())
        if book_id is None:
            return
        book = self.library.get_book(book_id)
        confirm = input(f"Remove '{book.title}'? (y/n): ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return
        self.library.remove_book(book_id)
        print(f"Removed '{book.title}'.")

    def search_books(self) -> None:
        """Search by title or author (case-insensitive, partial match)."""
        query = ask_text("Search title or author: ")
        print_books(self.library.search(query))

    def show_statistics(self) -> None:
        """Print the collection's summary statistics."""
        print_statistics(self.library.statistics())

    @staticmethod
    def _pick_book_id(books: list[Book]) -> int | None:
        """Show the given books and ask for an ID (None if list empty)."""
        if not books:
            print("No books available for this action.")
            return None
        print_books(books)
        return ask_int("Book ID: ", minimum=1)


# ---------------------------------------------------------------------
# Command-line arguments (argparse)
# ---------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Create the parser for the app's command-line arguments.

    Running ``python main.py`` with no command opens the menu instead.
    """
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Personal Library & Reading Tracker. "
                    "Run without a command to open the interactive menu.",
    )
    parser.add_argument(
        "--data", metavar="FILE",
        help="JSON data file to use (default: data/data.json)",
    )
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")

    add = commands.add_parser("add", help="add a book")
    add.add_argument("title", help="book title (use quotes if it has spaces)")
    add.add_argument("author", help="author name")
    add.add_argument("genre", help="genre, for example Fantasy")
    add.add_argument("pages", type=int, help="total number of pages")
    add.add_argument(
        "--status", choices=VALID_STATUSES, default="to-read",
        help="starting status (default: to-read)",
    )

    view = commands.add_parser("list", help="list books (optional filters)")
    view.add_argument(
        "--status", choices=VALID_STATUSES, help="only this status"
    )
    view.add_argument("--genre", help="only this genre (any case)")

    progress = commands.add_parser("progress", help="update reading progress")
    progress.add_argument("book_id", type=int, help="ID of the book")
    progress.add_argument("page", type=int, help="current page")

    finish = commands.add_parser("finish", help="mark a book as finished")
    finish.add_argument("book_id", type=int, help="ID of the book")

    remove = commands.add_parser("remove", help="remove a book")
    remove.add_argument("book_id", type=int, help="ID of the book")

    search = commands.add_parser("search", help="search by title or author")
    search.add_argument("query", help="text to look for (partial match)")

    commands.add_parser("stats", help="show reading statistics")
    return parser


def _cmd_add(library: Library, args: argparse.Namespace) -> None:
    """Handle ``add``: add a new book."""
    book = library.add_book(
        args.title, args.author, args.genre, args.pages, args.status
    )
    print(f"Added: {book}")


def _cmd_list(library: Library, args: argparse.Namespace) -> None:
    """Handle ``list``: show books, optionally filtered."""
    print_books(library.list_books(args.status, args.genre))


def _cmd_progress(library: Library, args: argparse.Namespace) -> None:
    """Handle ``progress``: set the current page of a book."""
    book = library.update_progress(args.book_id, args.page)
    print(f"Updated: {book}")


def _cmd_finish(library: Library, args: argparse.Namespace) -> None:
    """Handle ``finish``: mark a book as finished today."""
    book = library.mark_finished(args.book_id)
    print(f"Well done! {book}")


def _cmd_remove(library: Library, args: argparse.Namespace) -> None:
    """Handle ``remove``: delete a book from the collection."""
    book = library.remove_book(args.book_id)
    print(f"Removed '{book.title}'.")


def _cmd_search(library: Library, args: argparse.Namespace) -> None:
    """Handle ``search``: find books by title or author."""
    print_books(library.search(args.query))


def _cmd_stats(library: Library, _args: argparse.Namespace) -> None:
    """Handle ``stats``: print the summary statistics."""
    print_statistics(library.statistics())


COMMANDS: dict[str, Callable[[Library, argparse.Namespace], None]] = {
    "add": _cmd_add,
    "list": _cmd_list,
    "progress": _cmd_progress,
    "finish": _cmd_finish,
    "remove": _cmd_remove,
    "search": _cmd_search,
    "stats": _cmd_stats,
}


def run_command(library: Library, args: argparse.Namespace) -> int:
    """Run the single command given on the command line.

    Args:
        library: The library to act on.
        args: Parsed arguments from ``build_parser().parse_args()``.

    Returns:
        0 on success, or 1 if the action failed (the error is printed).
    """
    try:
        COMMANDS[args.command](library, args)
    except LibraryError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    return 0
