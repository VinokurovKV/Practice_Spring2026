import shlex
import unittest
from unittest.mock import MagicMock, patch

from mood.client.client import MUDClient
from mood.common import WEAPONS


class TestClientProtocolConversion(unittest.TestCase):
    def run_session(self, commands):
        fake_net_client = MagicMock()
        fake_net_client.read_block.return_value = "Successfully logged in as tester"

        fake_thread = MagicMock()
        fake_thread.is_alive.return_value = False

        with (
            patch("mood.client.client.Client", return_value=fake_net_client),
            patch("mood.client.client.threading.Thread", return_value=fake_thread),
            patch("builtins.input", side_effect=[*commands, "EOF"]),
            patch("builtins.print") as mock_print,
        ):
            client = MUDClient("tester")
            client.intro = ""
            client.cmdloop()

        return fake_net_client, mock_print


    def test_addmon_first(self):
        fake_net_client, _ = self.run_session([
            "addmon dragon hello hi hp 10 coords 1 0",
        ])

        expected = "addmon {} {} {} {} {}".format(
            shlex.quote("dragon"),
            shlex.quote("hi"),
            10,
            1,
            0,
        )
        fake_net_client.send.assert_called_once_with(expected)


    def test_addmon_second(self):
        hello = "hello world"

        fake_net_client, _ = self.run_session([
            f'addmon dragon hello "{hello}" hp 25 coords 2 3',
        ])

        expected = "addmon {} {} {} {} {}".format(
            shlex.quote("dragon"),
            shlex.quote(hello),
            25,
            2,
            3,
        )
        fake_net_client.send.assert_called_once_with(expected)


    def test_attack_first(self):
        fake_net_client, _ = self.run_session([
            "attack dragon",
        ])

        expected = "attack {} {} {}".format(
            shlex.quote("dragon"),
            WEAPONS["sword"],
            shlex.quote("sword"),
        )
        fake_net_client.send.assert_called_once_with(expected)


    def test_attack_second(self):
        other_weapon = next(w for w in WEAPONS if w != "sword")

        fake_net_client, _ = self.run_session([
            f"attack dragon with {other_weapon}",
        ])

        expected = "attack {} {} {}".format(
            shlex.quote("dragon"),
            WEAPONS[other_weapon],
            shlex.quote(other_weapon),
        )
        fake_net_client.send.assert_called_once_with(expected)


    def test_attack_wrong_arguments(self):
        fake_net_client, mock_print = self.run_session([
            "attack dragon with",
        ])

        fake_net_client.send.assert_not_called()
        mock_print.assert_any_call("Invalid arguments")