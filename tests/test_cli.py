"""Tests for src/cli.py: the menu and the command-line arguments."""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from main import main
from src.cli import LibraryCLI, build_parser, run_command
from src.library import Library


def run_cli(library: Library, inputs: list[str]) -> str:
    """Run the menu with the given answers and return what it printed."""
    output = io.StringIO()
    with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
        LibraryCLI(library).run()
    return output.getvalue()


def run_args(library: Library, argv: list[str]) -> tuple[int, str, str]:
    """Run one command-line command; return (exit code, stdout, stderr)."""
    args = build_parser().parse_args(argv)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = run_command(library, args)
    return code, out.getvalue(), err.getvalue()


class TestLibraryCLI(unittest.TestCase):
    """End-to-end menu sessions."""

    def test_add_book_through_menu(self) -> None:
        """Option 1 adds a book with the default to-read status."""
        library = Library()
        run_cli(library, ["1", "Dune", "Frank Herbert", "Sci-Fi", "412",
                          "", "0"])
        book = library.get_book(1)
        self.assertEqual(book.title, "Dune")
        self.assertEqual(book.status, "to-read")

    def test_bad_input_does_not_crash(self) -> None:
        """Unknown options and non-numbers are re-asked, not fatal."""
        library = Library()
        output = run_cli(library, ["9", "1", "Dune", "Frank Herbert",
                                   "Sci-Fi", "abc", "412", "", "0"])
        self.assertIn("Invalid choice", output)
        self.assertIn("Please enter a whole number", output)
        self.assertEqual(len(library), 1)

    def test_unknown_book_id_shows_error(self) -> None:
        """A missing ID prints an error and the menu keeps running."""
        library = Library()
        library.add_book("Dune", "Frank Herbert", "Sci-Fi", 412)
        output = run_cli(library, ["4", "99", "0"])
        self.assertIn("Error: No book with ID 99.", output)
        self.assertIn("Goodbye", output)

    def test_every_menu_option(self) -> None:
        """Walk through options 2-7 in one session."""
        library = Library()
        library.add_book("Dune", "Frank Herbert", "Sci-Fi", 412)
        library.add_book("Emma", "Jane Austen", "Classic", 474)
        output = run_cli(library, [
            "2", "", "",                 # view all, no filters
            "2", "to-read", "sci-fi",    # view with both filters
            "3", "1", "100",             # progress: Dune -> page 100
            "4", "2",                    # finish Emma
            "6", "austen",               # search by author
            "7",                         # statistics
            "5", "1", "n",               # remove Dune, then cancel
            "5", "1", "y",               # remove Dune, confirm
            "0",
        ])
        self.assertIn("Updated: [1] Dune", output)
        self.assertIn("Well done! [2] Emma", output)
        self.assertRegex(output, r"Favorite genre:\s+Classic")
        self.assertIn("Cancelled.", output)
        self.assertIn("Removed 'Dune'.", output)
        self.assertEqual(len(library), 1)

    def test_actions_with_no_books(self) -> None:
        """Options on an empty library explain there is nothing to do."""
        output = run_cli(Library(), ["2", "", "", "3", "0"])
        self.assertIn("No books found.", output)
        self.assertIn("No books available for this action.", output)

    def test_end_of_input_exits_cleanly(self) -> None:
        """Ctrl+D / Ctrl+Z (end of input) closes the app politely."""
        output = io.StringIO()
        with patch("builtins.input", side_effect=EOFError), \
                redirect_stdout(output):
            LibraryCLI(Library()).run()
        self.assertIn("Goodbye", output.getvalue())


class TestCommandLineArguments(unittest.TestCase):
    """One-off commands such as ``python main.py add ...``."""

    def setUp(self) -> None:
        """Create an in-memory library with one book being read."""
        self.library = Library()
        self.library.add_book(
            "The Hobbit", "J.R.R. Tolkien", "Fantasy", 310, "reading"
        )

    def test_no_command_means_menu(self) -> None:
        """With no command, main.py opens the interactive menu."""
        self.assertIsNone(build_parser().parse_args([]).command)

    def test_add(self) -> None:
        """``add`` creates a book, with an optional --status."""
        code, out, _ = run_args(self.library, [
            "add", "Dune", "Frank Herbert", "Sci-Fi", "412",
            "--status", "reading",
        ])
        self.assertEqual(code, 0)
        self.assertIn("Added: [2] Dune", out)
        self.assertEqual(self.library.get_book(2).status, "reading")

    def test_list_with_filters(self) -> None:
        """``list --status --genre`` filters the books shown."""
        self.library.add_book("Dune", "Frank Herbert", "Sci-Fi", 412)
        _, out, _ = run_args(
            self.library, ["list", "--status", "reading", "--genre", "fantasy"]
        )
        self.assertIn("The Hobbit", out)
        self.assertNotIn("Dune", out)

    def test_progress_then_finish(self) -> None:
        """``progress`` and ``finish`` update the book."""
        run_args(self.library, ["progress", "1", "200"])
        self.assertEqual(self.library.get_book(1).current_page, 200)
        _, out, _ = run_args(self.library, ["finish", "1"])
        self.assertIn("Well done!", out)
        self.assertEqual(self.library.get_book(1).status, "finished")

    def test_search_stats_and_remove(self) -> None:
        """``search``, ``stats`` and ``remove`` all work."""
        _, out, _ = run_args(self.library, ["search", "TOLK"])
        self.assertIn("The Hobbit", out)
        _, out, _ = run_args(self.library, ["stats"])
        self.assertRegex(out, r"Total books:\s+1")
        _, out, _ = run_args(self.library, ["remove", "1"])
        self.assertIn("Removed 'The Hobbit'.", out)
        self.assertEqual(len(self.library), 0)

    def test_unknown_id_returns_error_code(self) -> None:
        """A failed action prints an error and returns exit code 1."""
        code, _, err = run_args(self.library, ["finish", "99"])
        self.assertEqual(code, 1)
        self.assertIn("Error: No book with ID 99.", err)

    def test_bad_number_is_a_usage_error(self) -> None:
        """argparse rejects a non-number page with exit code 2."""
        with redirect_stderr(io.StringIO()) as err, \
                self.assertRaises(SystemExit) as caught:
            build_parser().parse_args(["progress", "1", "abc"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("invalid int value", err.getvalue())


class TestMainEntryPoint(unittest.TestCase):
    """main() with real arguments and a temporary data file."""

    def setUp(self) -> None:
        """Create a temporary data file path."""
        temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=R1732
        self.addCleanup(temp_dir.cleanup)
        self.data_file = str(Path(temp_dir.name) / "data.json")

    def test_commands_are_saved_between_runs(self) -> None:
        """A book added by one command is listed by the next one."""
        with redirect_stdout(io.StringIO()):
            code = main(["--data", self.data_file,
                         "add", "Emma", "Jane Austen", "Classic", "474"])
        self.assertEqual(code, 0)
        out = io.StringIO()
        with redirect_stdout(out):
            main(["--data", self.data_file, "list"])
        self.assertIn("[1] Emma by Jane Austen", out.getvalue())

    def test_damaged_data_file_returns_error(self) -> None:
        """A broken data file gives exit code 1, not a crash."""
        Path(self.data_file).write_text("{oops", encoding="utf-8")
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["--data", self.data_file, "list"])
        self.assertEqual(code, 1)
        self.assertIn("not valid JSON", err.getvalue())


if __name__ == "__main__":
    unittest.main()
