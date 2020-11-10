from dataclasses import dataclass
from rich.segment import Segment
from rich.style import Style
from rich.console import Console, ConsoleOptions, RenderResult


@dataclass
class SimpleResult:
    name: str
    url: str
    result: str
    error_text: str
    time: float

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment(self.name, Style(color="magenta"))
        yield Segment(':    ')
        yield Segment(self.url, Style(color="green"))
        yield Segment(' ,   ')
        yield Segment(self.result, Style(color="cyan"))
        yield Segment(' ,   ')
        yield Segment(str(round(self.time, 4))+' s', Style(color="blue" if self.time < 5 else 'red'))
        yield Segment('\n')
        if self.error_text:
            yield Segment(f'\t\t error: {self.error_text}\n', Style(color="red"))


class ResultPrinter:

    def __init__(self, verbose, invalid, console):
        self.verbose = verbose
        self.invalid = invalid
        self.console = console

    def printer(self, result):

        def map_simple_results(result):
            sr = SimpleResult(result['name'], result['url'],
                              result['check_result'], result['error_text'], result['time(s)'])
            return sr

        if self.invalid and result['check_result'] != 'OK':
            return

        if self.verbose:
            traceback = result.pop('traceback')
            self.console.print(result)
            if result['check_result'] != 'OK':
                self.console.print(traceback)

        else:
            simple_result = map_simple_results(result)
            self.console.print(simple_result)
