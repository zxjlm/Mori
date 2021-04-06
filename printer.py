"""
@project : Mori
@author  : harumonia
@mail   : zxjlm233@gmail.com
@ide    : PyCharm
@time   : 2020-11-17 19:23:27
@description: None
"""

import string
from dataclasses import dataclass
from rich.segment import Segment
from rich.style import Style
from rich.console import Console, ConsoleOptions, RenderResult


def str_count(s: str) -> int:
    """
    for prettier output, i use this function to calculate the space of right.
    Args:
        s: string

    Returns:
        how many space should put on the right.

    """
    count_en, count_zh, count_pu = 0, 0, 0
    s_len = len(s)
    for c in s:
        if c in string.ascii_letters or c.isdigit() or c.isspace():
            count_en += 1
        elif c.isalpha():
            count_zh += 1
        else:
            count_pu += 1
    total_chars = count_en + count_pu + count_zh
    if total_chars == s_len:
        return (count_pu + count_en) + count_zh * 2
    else:
        return len(s) * 2


@dataclass
class SimpleResult:
    """
    diy output of each dict.
    """

    name: str
    url: str
    result: str
    error_text: str
    time: float

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        if not isinstance(self.time, float):
            self.time = -0.1
        yield Segment(self.name, Style(color="magenta"))
        yield Segment(":    ")
        yield Segment(self.url, Style(color="green"))
        if len(self.url) > 140:
            yield Segment("\n" + " " * str_count(self.name))
        else:
            yield Segment(" ,   ")
        yield Segment(self.result, Style(color="cyan"))
        yield Segment(" ,   ")
        yield Segment(
            str(round(self.time, 4)) + " s",
            Style(color="blue" if self.time < 5 else "red"),
        )
        yield Segment("\n")
        if self.error_text and self.error_text != "status_code is 200":
            yield Segment(
                " " * str_count(self.name) + f"Error: {self.error_text}\n",
                Style(color="red"),
            )


class ResultPrinter:
    """
    without the arg --verbose.
    """

    def __init__(self, verbose, invalid, console):
        self.verbose = verbose
        self.invalid = invalid
        self.console = console

    def printer(self, result: dict) -> None:
        """
        Result dictionary can be found in function processor() in mori.py.
        Args:
            result:

        Returns:

        """

        def map_simple_results(sub_result):
            """

            Args:
                sub_result:

            Returns:

            """
            sr = SimpleResult(
                sub_result["name"],
                sub_result["url"],
                sub_result["check_result"],
                sub_result["error_text"],
                sub_result["time(s)"],
            )
            return sr

        if self.invalid and result["check_result"] != "OK":
            return

        if self.verbose:
            traceback = result.pop("traceback")
            # result.pop('check_result')

            if result["check_result"] != "OK":
                self.console.print(result, style=Style(color="red", underline=True))
                self.console.print(traceback)
            else:
                self.console.print(result)

        else:
            simple_result = map_simple_results(result)
            self.console.print(simple_result)
