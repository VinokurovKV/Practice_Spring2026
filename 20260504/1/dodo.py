import shutil
import subprocess
from pathlib import Path


DOMAIN = "mud"
LOCALE = "ru_RU.UTF-8"

PO_DIR = Path("mood/server/po")
POT_FILE = PO_DIR / f"{DOMAIN}.pot"
PO_FILE = PO_DIR / LOCALE / "LC_MESSAGES" / f"{DOMAIN}.po"

LOCALE_DIR = Path("mood/server/locale")
MO_FILE = LOCALE_DIR / LOCALE / "LC_MESSAGES" / f"{DOMAIN}.mo"

DOC_DIR = Path("html")

PY_FILES = [
    "mood/client/client.py",
    "mood/server/server.py",
]

PY_MODULES = [
    "mood.client.client",
    "mood.server.server",
]


def remove_all_generated_files():
    if DOC_DIR.exists():
        shutil.rmtree(DOC_DIR)

    if POT_FILE.exists():
        POT_FILE.unlink()

    if LOCALE_DIR.exists():
        shutil.rmtree(LOCALE_DIR)


def task_pot():
    """Make .pot file."""
    return {
        "actions": [
            f"mkdir -p {PO_DIR}",
            f"xgettext --force-po -L Python -o {POT_FILE} {' '.join(PY_FILES)}",
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
    def make_mo_dir():
        MO_FILE.parent.mkdir(parents=True, exist_ok=True)

    return {
        "actions": [
            make_mo_dir,
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
            f"mkdir -p {DOC_DIR}",
            f"PYTHONPATH=. python3 -m pydoc -w {' '.join(PY_MODULES)}",
            "mv *.html html/ || true",
        ],
        "file_dep": PY_FILES,
        "targets": [DOC_DIR],
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