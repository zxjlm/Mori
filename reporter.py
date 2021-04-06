"""
@project : Mori
@author  : harumonia
@mail   : zxjlm233@gmail.com
@ide    : PyCharm
@time   : 2020-11-17 19:23:27
@description: None
"""
import xlwt
from io import BytesIO


class Reporter:
    """
    Generate excel report and html tale report.

    For better distinction between success and failed, we need use some style,
     such as red and black, bold and normal, and so on.
    """

    def __init__(self, headers: list, results: list):
        """

        Args:
            headers:
            results:
        """
        self.headers = headers
        self.results = results
        self.workbook = xlwt.Workbook(encoding="utf-8")
        self.worksheet = self.workbook.add_sheet("Reports")
        self.table = ""

    def generate_headers(self):
        """
        both excel and html table has the same header.
        the value of header define when Reporter instance.
        Returns:
            None

        """
        style = xlwt.XFStyle()
        font = xlwt.Font()
        font.name = "Times New Roman"
        font.bold = True
        style.font = font
        for col, value in enumerate(self.headers):
            self.worksheet.write(0, col, value, style)

    def row_writer(self, inx: int, result: dict):
        """
        generate each row.
        Args:
            inx: inx of this row.
            result: value of this row.it`s a dictionary, keys can be found
                    in function processor() in mori.py.

        Returns:
            None

        """
        for col, header in enumerate(self.headers):
            style = xlwt.XFStyle()
            if result["check_result"] != "OK":
                style = xlwt.XFStyle()
                font = xlwt.Font()
                font.colour_index = 2
                style.font = font
            if header == "resp_text" and len(result[header]) >= 32767:
                result[header] = "too long"
            if header == "time(s)":
                result[header] = round(result[header], 4)
            if header == "check_results":
                style.alignment.wrap = 1
            self.worksheet.write(inx, col, result[header], style)

    def generate_excel(self, file_name):
        """
        literal meaning.
        Args:
            file_name:

        Returns:

        """
        self.generate_headers()

        for inx, foo in enumerate(self.results):
            self.row_writer(inx + 1, foo)
        check_results_col = self.worksheet.col(self.headers.index("check_results"))
        check_results_col.width = 720 * 20

        self.workbook.save(file_name)
        ...

    def generate_table(self):
        """
        literal meaning
        Returns:

        """
        th = ""
        for value in self.headers:
            if "url" in value:
                th += f'<th style="border:1px solid;width: 10%;">{value}</th>'
                continue
            th += f'<th style="border:1px solid">{value}</th>'
        thead = f'<thead style="background-color:gray;">{th}</thead>'
        tbody = ""
        for result in self.results:
            tr = ""
            for header in self.headers:
                if header == "resp_text":
                    continue
                if "url" in header:
                    tr += (
                        f'<td style="border:1px solid;width: 10%;">'
                        f"{result[header]}</td>"
                    )
                    continue
                if header == "check_results":
                    cell_value = result[header].replace("\n", "<hr>")
                    tr += (
                        f'<td style="border:1px solid;width: 10%;">'
                        f"{cell_value}</td>"
                    )
                    continue
                tr += f'<td style="border:1px solid">{result[header]}</td>'
            if result["check_result"] != "OK":
                tbody += f'<tr style="color:red">{tr}</tr>'
            else:
                tbody += f"<tr>{tr}</tr>"
        return (
            f'<p>Mori Result</p><table style="border:1px solid">'
            f"{thead}{tbody}</table>"
        )

    def processor(self, is_stream: bool = False, file_name: str = "demo.xls"):
        """

        Args:
            is_stream: if this value is True, we will use Bytes Stream to
            store the result.
            file_name:

        Returns:

        """
        if is_stream:
            fs = BytesIO()
            self.generate_excel(fs)
            return fs
        else:
            self.generate_excel(file_name)
