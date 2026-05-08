"""Shared monster helpers."""

import io
from importlib.resources import files

import cowsay


CUSTOM_MONSTERS = ("jgsbat",)


def load_custom_cow(name):
    """Load custom cow from package data."""
    cow_text = files("mood.common").joinpath("cows", f"{name}.txt").read_text(
        encoding="utf-8"
    )
    return cowsay.read_dot_cow(io.StringIO(cow_text))


def available_monsters():
    """List supported monsters."""
    return cowsay.list_cows() + list(CUSTOM_MONSTERS)


def make_monster_message(name, hello):
    """Build a monster greeting."""
    if name in CUSTOM_MONSTERS:
        return cowsay.cowsay(hello, cowfile=load_custom_cow(name))
    return cowsay.cowsay(hello, cow=name)