import cmd
from shlex import split
from pathlib import Path
from calendar import TextCalendar

Month = { \
'JANUARY': 1, \
'FEBRUARY': 2, \
'MARCH': 3, \
'APRIL': 4, \
'MAY': 5, \
'JUNE': 6, \
'JULY': 7, \
'AUGUST': 8, \
'SEPTEMBER': 9, \
'OCTOBER': 10, \
'NOVEMBER': 11, \
'DECEMBER': 12 \
}

class SizeCmdl(cmd.Cmd):
    prompt = "==> "

    def do_size(self, arg):
        """Print file sizes"""
        args = split(arg)
        for name in args:
            print(f"{name}: {Path(name).stat().st_size}")

    def do_month(self, arg):
        """Print a month’s calendar"""
        args = split(arg)
        if len(args) == 2:
            TextCalendar().prmonth(int(args[0]), Month[args[1]])
        else:
            print("no args")

    def do_year(self, arg):
        """Print the calendar for an entire year"""
        TextCalendar().pryear(int(arg))
              

    def do_EOF(self, arg):
        print("\nBye\n")
        return 1


if __name__ == "__main__":
    SizeCmdl().cmdloop()
