import sys
import socket
import cmd

class NC(Cmd.cmd):
    prompt = "> "

    def do_connect(self, arg):
        """Connect host port"""
        args = arg.split()
        match args:
            case [host, port]:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((nost, int(port)))

    def do_print(self, arg):
        if arg:
            self.s.sendall(b"print " + arg.encode())
            print(self.s.recv(1024).rstrip().decode())

    def do_info(self, arg):
        match arg:
            case "host" | "port":
                self.s.sendall(b"info " + arg.encode())
                print(self.s.recv(1024).rstrip().decode())

    def complete_info(text, line, begidx, endidx):
        return [s for s in ["host", "port"] if s.startswith(text)]
