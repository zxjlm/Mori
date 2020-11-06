import xlwt
from io import BytesIO, StringIO


class Reporter:

    def __init__(self, headers: list, results: list):
        self.headers = headers
        self.results = results
        self.workbook = xlwt.Workbook(encoding='utf-8')
        self.worksheet = self.workbook.add_sheet('Reports')
        self.table = ''

    def generate_headers(self):
        style = xlwt.XFStyle()
        font = xlwt.Font()
        font.name = 'Times New Roman'
        font.bold = True
        style.font = font
        for col, value in enumerate(self.headers):
            self.worksheet.write(0, col, value, style)

    def row_writer(self, inx: int, result: dict):
        style = xlwt.XFStyle()
        for col, header in enumerate(self.headers):
            if result['check_result'] != 'OK':
                style = xlwt.XFStyle()
                font = xlwt.Font()
                font.colour_index = 2
                style.font = font
            if header == 'resp_text' and len(result[header]) >= 32767:
                result[header] = 'too long'
            if header == 'time(s)':
                result[header] = round(result[header], 4)
            self.worksheet.write(inx, col, result[header], style)

    def generate_excel(self, file_name):
        self.generate_headers()

        for inx, foo in enumerate(self.results):
            self.row_writer(inx+1, foo)

        self.workbook.save(file_name)
        ...

    def generate_table(self):
        th = ''
        for value in self.headers:
            th += f'<th style="border:1px solid">{value}</th>'
        thead = f'<thead style="background-color:gray;">{th}</thead>'
        tbody = ''
        for result in self.results:
            tr = ''
            for header in self.headers:
                if header == 'resp_text':
                    continue
                tr += f'<td style="border:1px solid">{result[header]}</td>'
            if result['check_result'] != "OK":
                tbody += f'<tr style="color:red">{tr}</tr>'
            else:
                tbody += f'<tr>{tr}</tr>'
        return f'<p>Mori Result</p><table style="border:1px solid">{thead}{tbody}</table>'

    def processor(self, is_stream: bool = False, file_name: str = 'report.xls'):
        if is_stream:
            fs = BytesIO()
            self.generate_excel(fs)
            return fs
        else:
            self.generate_excel(file_name)
