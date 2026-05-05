import multiprocessing
import time
import unittest

from mood.client.client import Client
from mood.server.server import start_server
from mood.common import DEFAULT_HOST, DEFAULT_PORT
from mood.common import make_monster_message


HOST = DEFAULT_HOST
PORT = DEFAULT_PORT


class TestServerCommands(unittest.TestCase):
    def setUp(self):
        self.proc = multiprocessing.Process(
            target=start_server,
            args=(HOST, PORT),
        )
        self.proc.start()

        time.sleep(1)

        self.client = Client(HOST, PORT, "tester")

        login_reply = self.client.read_block()
        self.assertEqual(login_reply, "Successfully logged in as tester")

        entered_reply = self.client.read_block()
        self.assertEqual(entered_reply, "tester entered the MUD")

        self.client.send("movemonsters off")
        reply = self.client.read_block()
        self.assertEqual(reply, "Moving monsters: off")

    def tearDown(self):
        self.client.close()
        self.proc.terminate()

    def test_addmon(self):
        self.client.send("addmon dragon hi 10 1 0")
        reply = self.client.read_block()

        self.assertEqual(
            reply,
            'tester added monster dragon to (1, 0) saying "hi" with 10 hit points',
        )


    def test_move_to_monster(self):
        hello = "hello_from_dragon"

        self.client.send(f"addmon dragon {hello} 10 1 0")
        addmon_reply = self.client.read_block()
        self.assertEqual(
            addmon_reply,
            'tester added monster dragon to (1, 0) saying "hello_from_dragon" with 10 hit points',
        )

        self.client.send("move 1 0")
        reply = self.client.read_block()

        expected = "Moved to (1, 0)\n" + make_monster_message("dragon", hello)
        self.assertEqual(reply, expected)


    def test_attack_monster(self):
        self.client.send("addmon dragon hi 10 1 0")
        addmon_reply = self.client.read_block()
        self.assertEqual(
            addmon_reply,
            'tester added monster dragon to (1, 0) saying "hi" with 10 hit points',
        )

        self.client.send("move 1 0")
        move_reply = self.client.read_block()
        self.assertIn("Moved to (1, 0)", move_reply)
        self.assertIn("hi", move_reply)

        self.client.send("attack dragon 10 sword")
        reply = self.client.read_block()

        self.assertIn("tester attacked dragon with sword, damage 10 hit points", reply)
        self.assertIn("dragon died", reply)
