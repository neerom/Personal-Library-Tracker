"""Entry point for the Personal Library & Reading Tracker.

Run it from the project folder:

    python main.py                 # open the interactive menu
    python main.py --help          # list the command-line commands
    python main.py add "Alchemist" "Paul Coellho" Sci-Fi 412
"""

import sys
from pathlib import Path

from src.cli import LibraryCLI, build_parser, run_command
from src.library import Library
from src.models import StorageError
from src.storage import JsonStorage

# The data file lives in the data/ folder next to this file, whatever
# folder you run the app from.
DATA_FILE = Path(__file__).resolve().parent / "data" / "data.json"


def main(argv: list[str] | None = None) -> int:
    """Read the command-line arguments, then run a command or the menu.

    Args:
        argv: The arguments to read. ``None`` means the real command
            

    Returns:
        The exit code: 0 for success, 1 for an error.
    """
    args = build_parser().parse_args(argv)
    data_file = Path(args.data) if args.data else DATA_FILE
    try:
        library = Library(JsonStorage(data_file))
    except StorageError as err:
        print(f"Error: {err}", file=sys.stderr)
        print("Fix or delete the data file, then run the program again.",
              file=sys.stderr)
        return 1

    if args.command is None:
        LibraryCLI(library).run()
        return 0
    return run_command(library, args)


if __name__ == "__main__":
    sys.exit(main())
