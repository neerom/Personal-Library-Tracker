# Personal Library & Reading Tracker

A simple command-line app to manage your book collection and track your
reading progress. Books are saved to a JSON file, so your library is still
there the next time you run the program.

## Features

1. Add a book (title, author, genre, total pages, status)
2. View all books, optionally filtered by status and/or genre
3. Update reading progress (current page)
4. Mark a book as finished (the finish date is recorded automatically)
5. Remove a book
6. Search by title or author (case-insensitive, partial match)
7. View statistics (total books, finished this year, average pages per
   finished book, favourite genre)
8. Automatic saving to `data/data.json` and loading on the next run

Every action works in two ways: from an **interactive menu**, or as a
one-line **command-line argument** (for example `python main.py stats`).

## Requirements


The app itself uses only the Python standard library. `requirements.txt`
lists optional tools for checking code style and test coverage.

## Project structure

```
personal-library/
├── src/
│   ├── __init__.py      # marks src as a Python package
│   ├── models.py        # Book class and custom exceptions
│   ├── library.py       # Library class (business logic)
│   ├── storage.py       # save/load books to JSON
│   └── cli.py           # command-line arguments and text menu
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_library.py
│   ├── test_storage.py
│   └── test_cli.py
├── data/
│   ├── data.json        # your saved books (ignored by Git)
│   └── .gitkeep         # keeps the empty data/ folder in Git
├── main.py              # entry point: python main.py
├── requirements.txt
├── README.md
└── .gitignore
```

### The data file

- Your books are saved in `data/data.json`. It starts as an empty list
  (`[]`) and is updated every time you add or change a book.
- `.gitignore` contains the line `data/data.json`, so your personal data
  is never committed or pushed to GitHub.
- Because Git does not store empty folders, `data/.gitkeep` is committed
  so the `data/` folder still exists in a fresh clone.
- If `data/data.json` (or even the whole `data/` folder) is missing, the
  app creates it automatically the first time it saves.

## Setup 

```bash
cd path/to/personal-library
```

###  Create a virtual environment

Windows:

```bash
python -m venv venv
```

macOS / Linux:

```bash
python3 -m venv venv
```

### 3. Activate the virtual environment

Windows (Command Prompt):


```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\activate
```


### 4. Install the optional tools

```bash
pip install -r requirements.txt
```

This installs `flake8`, `pylint` and `coverage`. You can skip this step if
you only want to run the app.

## Run the app

There are two ways to use the app. Both save to the same
`data/data.json`, so you can mix them freely.

### Option A: command-line arguments

Give a command after `main.py` to do one action and exit:

```bash
python main.py --help                         # list all commands
python main.py add "The Hobbit" "J.R.R. Tolkien" Fantasy 310
python main.py add Alchemist "Paul Coelho" Philosophy 197 --status reading
python main.py list                           # all books
python main.py list --status reading          # filter by status
python main.py list --genre fantasy           # filter by genre
python main.py progress 2 150                 # book 2 is on page 150
python main.py finish 1                       # mark book 1 as finished
python main.py search tolkien                 # title or author
python main.py stats
python main.py remove 2
```

| Command | Arguments | What it does |
|---|---|---|
| `add` | `TITLE AUTHOR GENRE PAGES [--status STATUS]` | Add a book (status defaults to `to-read`) |
| `list` | `[--status STATUS] [--genre GENRE]` | Show books, optionally filtered |
| `progress` | `BOOK_ID PAGE` | Update reading progress |
| `finish` | `BOOK_ID` | Mark a book as finished (records today's date) |
| `remove` | `BOOK_ID` | Remove a book |
| `search` | `TEXT` | Search titles and authors (partial, any case) |
| `stats` | — | Show reading statistics |

Notes:

- Put quotes around values that contain spaces, like `"The Hobbit"`.
- `STATUS` is one of `to-read`, `reading` or `finished`.
- Run `python main.py COMMAND --help` for help on one command, for example
  `python main.py add --help`.
- `--data FILE` (before the command) uses a different data file, for
  example `python main.py --data test.json list`.
- Exit codes: `0` success, `1` the action failed (for example an unknown
  book ID), `2` the arguments were wrong (for example letters for a page).

### Option B: interactive menu

Run `main.py` with no command:

```bash
python main.py
```

You will see this menu. Type a number and press Enter:

```
========== Personal Library ==========
1. Add a book
2. View all books
3. Update reading progress
4. Mark a book as finished
5. Remove a book
6. Search books
7. View statistics
0. Exit
======================================
```

Tips:

- Each book gets an ID number (shown as `[1]`, `[2]` ...). Options 3, 4 and
  5 list the books and ask for the ID.
- Updating progress on a `to-read` book moves it to `reading`; reaching the
  last page marks it as `finished`.
- To start with an empty library, close the app and either delete
  `data/data.json` or replace its contents with `[]`.

## Run the tests

From the `personal-library` folder:

```bash
python -m unittest -v
```

All 53 tests should finish with `OK`. The tests use temporary files, so
they never change your `data/data.json`.

To see test coverage (after step 4):

```bash
coverage run -m unittest
coverage report
```

## Check code style

```bash
flake8 src tests main.py
pylint src tests main.py
```

flake8 should print nothing, and pylint should rate the code

data/data.json` once. |
