import sys
import socket
import cmd

class NC(cmd.Cmd):
    prompt = "> "

    def do_connect(self, arg):
        """Connect host port"""
        args = arg.split()
        match args:
            case [host, port]:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((host, int(port)))
                print("Connected")

    def do_print(self, arg):
        if arg:
            self.s.sendall(b"print " + arg.encode() + b'\n')
            print(self.s.recv(1024).rstrip().decode())

    def do_info(self, arg):
        """Info host | port"""
        match arg:
            case "host" | "port":
                self.s.sendall(b"info " + arg.encode() + b'\n')
                print(self.s.recv(1024).rstrip().decode())

    def complete_info(self, text, line, begidx, endidx):
        return [s for s in ["host", "port"] if s.startswith(text)]

    def do_EOF(self, arg):
        return 1


if __name__ == "__main__":
    NC().cmdloop()