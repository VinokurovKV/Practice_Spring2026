"""Shared monster helpers."""

import io

import cowsay

CUSTOM_MONSTERS = ("jgsbat",)
JGSBAT = cowsay.read_dot_cow(io.StringIO(r"""
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\/o\/o\/'.   `(
      ) .' . \====/ . '. (
       )  / <<    >> \  (
        '-._/``  ``\_.-'
  jgs     \\'--'//
         (((""  "")))
"""))


def available_monsters():
    """List supported monsters."""
    return cowsay.list_cows() + list(CUSTOM_MONSTERS)


def make_monster_message(name, hello):
    """Build a monster greeting."""
    if name == "jgsbat":
        return cowsay.cowsay(hello, cowfile=JGSBAT)
    return cowsay.cowsay(hello, cow=name)
