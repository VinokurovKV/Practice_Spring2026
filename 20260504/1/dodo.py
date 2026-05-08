import shutil
import subprocess
from pathlib import Path


DOMAIN = "messages"
LOCALE = "ru_RU.UTF-8"

PO_DIR = Path("mood/server/po")
POT_FILE = PO_DIR / f"{DOMAIN}.pot"
PO_FILE = PO_DIR / LOCALE / "LC_MESSAGES" / f"{DOMAIN}.po"
MO_FILE = PO_DIR / LOCALE / "LC_MESSAGES" / f"{DOMAIN}.mo"

SPHINX_SOURCE_DIR = Path("doc/source")
SPHINX_BUILD_DIR = Path("doc/build/html")
CLIENT_DOC_DIR = Path("mood/client/html")

PY_FILES = [
    "mood/client/client.py",
    "mood/server/server.py",
]

SPHINX_FILES = [
    "doc/source/conf.py",
    "doc/source/index.rst",
    "doc/source/client.rst",
    "doc/source/server.rst",
]


def remove_all_generated_files():
    if SPHINX_BUILD_DIR.parent.exists():
        shutil.rmtree(SPHINX_BUILD_DIR.parent)

    if CLIENT_DOC_DIR.exists():
        shutil.rmtree(CLIENT_DOC_DIR)

    if POT_FILE.exists():
        POT_FILE.unlink()

    if MO_FILE.exists():
        MO_FILE.unlink()


def task_pot():
    """Make .pot file."""
    return {
        "actions": [
            f"mkdir -p {PO_DIR}",
            (
                f"xgettext --force-po -L Python "
                f"--keyword=tr:2 "
                f"--keyword=ntr:2,3 "
                f"-o {POT_FILE} {' '.join(PY_FILES)}"
            ),
        ],
        "file_dep": PY_FILES,
        "targets": [POT_FILE],
        "clean": True,
    }


def task_po():
    """Make or update .po file."""
    def make_po():
        PO_FILE.parent.mkdir(parents=True, exist_ok=True)

        if PO_FILE.exists():
            subprocess.run(
                ["msgmerge", "--update", str(PO_FILE), str(POT_FILE)],
                check=True,
            )
        else:
            subprocess.run(
                [
                    "msginit",
                    "--no-translator",
                    f"--locale={LOCALE}",
                    f"--input={POT_FILE}",
                    f"--output-file={PO_FILE}",
                ],
                check=True,
            )

    return {
        "actions": [make_po],
        "file_dep": [POT_FILE],
        "targets": [PO_FILE],
    }


def task_mo():
    """Make .mo file."""
    return {
        "actions": [
            f"msgfmt {PO_FILE} -o {MO_FILE}",
        ],
        "file_dep": [PO_FILE],
        "targets": [MO_FILE],
        "clean": True,
    }


def task_i18n():
    """Make translation."""
    return {
        "actions": None,
        "task_dep": ["pot", "po", "mo"],
        "clean": [remove_all_generated_files],
    }


def task_html():
    """Make html docs."""
    return {
        "actions": [
            (
                f"PYTHONPATH=. sphinx-build -b html "
                f"{SPHINX_SOURCE_DIR} {SPHINX_BUILD_DIR}"
            ),
            f"mkdir -p {CLIENT_DOC_DIR}",
            f"cp -r {SPHINX_BUILD_DIR}/* {CLIENT_DOC_DIR}/",
        ],
        "file_dep": PY_FILES + SPHINX_FILES,
        "targets": [
            SPHINX_BUILD_DIR / "index.html",
            CLIENT_DOC_DIR / "index.html",
        ],
        "clean": [remove_all_generated_files],
    }


def task_test():
    """Run tests."""
    return {
        "actions": [
            "python3 -m unittest discover -v",
        ],
        "task_dep": ["i18n"],
        "clean": True,
    }


DOIT_CONFIG = {
    "default_tasks": ["html"],
}