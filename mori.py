import requests
import json
import re
from requests_futures.sessions import FuturesSession
import time
from rich.console import Console
from rich.traceback import Traceback
import platform
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from printer import SimpleResult, ResultPrinter
import xlwt
from reporter import Reporter
from proxy import Proxy

__version__ = 'v0.5'
module_name = "Mori Kokoro"


class MoriFuturesSession(FuturesSession):
    def request(self, method, url, hooks={}, *args, **kwargs):
        start = time.monotonic()

        def response_time(resp, *args, **kwargs):
            resp.elapsed = time.monotonic() - start
            return

        hooks['response'] = [response_time]

        return super(MoriFuturesSession, self).request(method,
                                                       url,
                                                       hooks=hooks,
                                                       *args, **kwargs)


def regex_checker(regex, resp_json, exception=None):
    res = regex_checker_recur(regex.split('->'), resp_json)
    if exception:
        return 'OK' if res == exception else 'Damage'
    else:
        return 'OK' if len(res) > 0 else 'Damage'


def regex_checker_recur(regexs, resp_json):
    is_index = re.search(r'\$(\d+)\$', regexs[0])
    if len(regexs) == 1:
        return resp_json[regexs[0]]
    elif is_index:
        return regex_checker_recur(regexs[1:], resp_json[int(is_index.group(1))])
    else:
        return regex_checker_recur(regexs[1:], resp_json[regexs[0]])


def data_render(apis):
    def coloring(api):
        for key, value in api.items():
            if isinstance(value, list):
                for val in value:
                    coloring(val)
            if isinstance(value, dict):
                coloring(value)
            if value == "{{time}}":
                api[key] = str(int(time.time() * 1000))

    for idx, api in enumerate(apis):
        if "data" in api.keys():
            coloring(apis[idx]['data'])


def get_response(request_future, social_network):
    response = None

    error_context = "General Unknown Error"
    expection_text = None
    try:
        response = request_future.result()
        if response.status_code:
            error_context = None
    except requests.exceptions.HTTPError as errh:
        error_context = "HTTP Error"
        expection_text = str(errh)
    except requests.exceptions.ProxyError as errp:
        error_context = "Proxy Error"
        expection_text = str(errp)
    except requests.exceptions.ConnectionError as errc:
        error_context = "Error Connecting"
        expection_text = str(errc)
    except requests.exceptions.Timeout as errt:
        error_context = "Timeout Error"
        expection_text = str(errt)
    except requests.exceptions.RequestException as err:
        error_context = "Unknown Error"
        expection_text = str(err)

    return response, error_context, expection_text


def mori(site_datas, result_printer, timeout):
    if len(site_datas) >= 20:
        max_workers = 20
    else:
        max_workers = len(site_datas)

    session = MoriFuturesSession(
        max_workers=max_workers, session=requests.Session())

    results_total = []

    for site_data in site_datas:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
        }
        check_result = 'Damage'
        traceback, r, resp_text = None, None, ''

        if site_data.get('proxy'):
            Proxy.set_proxy_url(site_data['proxy'])

        try:
            if site_data.get('headers'):
                if isinstance(site_data.get('headers'), dict):
                    headers.update(site_data.get('headers'))

            if site_data.get('antispider') and site_data.get('data'):
                try:
                    import importlib
                    package = importlib.import_module('antispider.' + site_data['antispider'])
                    Antispider = package.Antispider
                    site_data['data'], headers = Antispider(
                        site_data['data'], headers).processor()
                except Exception as _e:
                    raise Exception('antispider error')

            for _ in range(4):
                proxies = Proxy.get_proxy()
                if site_data.get('data'):
                    if re.search(r'application.json', headers.get('Content-Type', '')):
                        site_data["request_future"] = session.post(
                            site_data['url'], json=site_data['data'], headers=headers, timeout=timeout, proxies=proxies,
                            allow_redirects=True)
                    else:
                        # data = json.dumps(site_data['data'])
                        site_data["request_future"] = session.post(
                            site_data['url'], data=site_data['data'], headers=headers, timeout=timeout, proxies=proxies,
                            allow_redirects=True)
                else:
                    site_data["request_future"] = session.get(
                        site_data['url'], headers=headers, timeout=timeout, proxies=proxies)
                future = site_data["request_future"]
                r, error_text, expection_text = get_response(request_future=future,
                                                             social_network=site_data['name'])

                if not error_text:
                    break

            if r:
                resp_text = r.text

            if site_data.get('decrypt') and resp_text:
                try:
                    import importlib
                    package = importlib.import_module(
                        'decrypt.' + site_data['decrypt'])
                    Decrypt = package.Decrypt
                    resp_text = Decrypt().decrypt(resp_text)
                except Exception as _e:
                    raise Exception('json decrypt error')

            if resp_text:
                try:
                    resp_json = json.loads(
                        re.search('({.*})', resp_text.replace('\\', '')).group(1))
                except Exception as _e:
                    raise Exception('response data not json format')
                try:
                    for regex in site_data['regex']:
                        check_result = regex_checker(
                            regex, resp_json, site_data.get('exception'))
                        if check_result != 'OK':
                            error_text = 'regex failed'
                            break
                except Exception as _e:
                    raise Exception('regex failed.')

            result = {
                'name': site_data['name'],
                'url': site_data['url'],
                'resp_text': resp_text if len(
                    resp_text) < 500 else 'too long, and you can add --xls to see detail in *.xls file',
                'status_code': r.status_code,
                'time(s)': r.elapsed,
                'error_text': error_text,
                'expection_text': expection_text,
                'check_result': check_result,
                'traceback': traceback
            }

            rel_result = result.copy()
            rel_result['resp_text'] = resp_text

        except Exception as error:
            result = {
                'name': site_data['name'],
                'url': site_data['url'],
                'resp_text': resp_text if len(
                    resp_text) < 500 else 'too long, and you can add --xls to see detail in *.xls file',
                'status_code': r and r.status_code,
                'time(s)': r and r.elapsed,
                'error_text': error or 'site handler error',
                'check_result': check_result,
                'traceback': Traceback()
            }
            rel_result = result.copy()

        results_total.append(rel_result)
        result_printer.printer(result)

    return results_total


def timeout_check(value):
    from argparse import ArgumentTypeError

    try:
        timeout = float(value)
    except:
        raise ArgumentTypeError(f"Timeout '{value}' must be a number.")
    if timeout <= 0:
        raise ArgumentTypeError(
            f"Timeout '{value}' must be greater than 0.0s.")
    return timeout


def send_mail(receivers: list, file_content, html, subject, mail_host, mail_user, mail_pass, mail_port=0):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sender = mail_user
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = ';'.join(receivers)
    message['Subject'] = subject

    if html:
        message.attach(MIMEText(html, 'html', 'utf-8'))

    part = MIMEText(file_content.getvalue(), "vnd.ms-excel", 'utf-8')
    part.add_header('Content-Disposition', 'attachment',
                    filename=f'{subject}.xls')
    message.attach(part)

    for count in range(4):
        try:
            if mail_port == 0:
                smtp = smtplib.SMTP()
                smtp.connect(mail_host)
            else:
                smtp = smtplib.SMTP_SSL(mail_host, mail_port)
            smtp.ehlo()
            smtp.login(mail_user, mail_pass)
            smtp.sendmail(sender, receivers, message.as_string())
            smtp.close()
            break
        except Exception as _e:
            print(_e)
            if count == 3:
                raise Exception('failed to send email')


def main():
    version_string = f"%(prog)s {__version__}\n" + \
                     f"{requests.__description__}:  {requests.__version__}\n" + \
                     f"Python:  {platform.python_version()}"

    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                            description=f"{module_name} (Version {__version__})"
                            )
    parser.add_argument("--version",
                        action="version", version=version_string,
                        help="Display version information and dependencies."
                        )
    parser.add_argument("--verbose", "-v", "-d", "--debug",
                        action="store_true", dest="verbose", default=False,
                        help="Display extra debugging information and metrics."
                        )
    parser.add_argument("--xls",
                        action="store_true", dest="xls", default=False,
                        help="Create .xls File.(Microsoft Excel file format)"
                        )
    parser.add_argument("--show-all-site",
                        action="store_true",
                        dest="show_site_list", default=False,
                        help="Show all infomations of the apis in files."
                        )
    parser.add_argument("--json", "-j", metavar="JSON_FILE",
                        dest="json_file", default=None,
                        help="Load data from a local JSON file.")
    parser.add_argument("--email", "-e",
                        # metavar="EMAIL",
                        action="store_true",
                        dest="email", default=False,
                        help="Send email to mailboxes in the file 'config.py'.")
    parser.add_argument("--print-invalid",
                        action="store_false", dest="print_invalid", default=False,
                        help="Output api(s) that was invalid."
                        )
    parser.add_argument("--timeout",
                        action="store", metavar='TIMEOUT',
                        dest="timeout", type=timeout_check, default=None,
                        help="Time (in seconds) to wait for response to requests. "
                             "Default timeout is infinity. "
                             "A longer timeout will be more likely to get results from slow sites. "
                             "On the other hand, this may cause a long delay to gather all results."
                        )

    args = parser.parse_args()

    console = Console()

    file_path = args.json_file or './apis.json'

    with open(file_path, 'r', encoding='utf-8') as f:
        apis = json.load(f)
    data_render(apis)

    if args.show_site_list:

        keys_to_show = ['name', 'url', 'data']
        apis_to_show = list(map(lambda api: {key: value for key,
                                                            value in api.items() if key in keys_to_show}, apis))
        console.print(apis_to_show)

    else:
        r = r'''
             __  __               _   _  __        _
            |  \/  |  ___   _ __ (_) | |/ /  ___  | | __  ___   _ __   ___
            | |\/| | / _ \ | '__|| | | ' /  / _ \ | |/ / / _ \ | '__| / _ \
            | |  | || (_) || |   | | | . \ | (_) ||   < | (_) || |   | (_) |
            |_|  |_| \___/ |_|   |_| |_|\_\ \___/ |_|\_\ \___/ |_|    \___/
            '''
        print(r)

        result_printer = ResultPrinter(
            args.verbose, args.print_invalid, console)

        results = mori(apis, result_printer, timeout=args.timeout or 15)

        if args.xls:
            console.print('[cyan]now generating report...')

            repo = Reporter(['name', 'url', 'status_code', 'time(s)',
                             'check_result', 'error_text', 'resp_text'], results)
            repo.processor()

            console.print('[green]mission completed')

        if args.email:
            try:
                import config
            except:
                console.print(
                    'can`t get config.py file, please read README.md, search keyword [red]config.py')
            console.print('[cyan]now sending email...')
            repo = Reporter(['name', 'url', 'status_code', 'time(s)',
                             'check_result', 'error_text', 'resp_text'], results)
            fs = repo.processor(is_stream=True)
            html = repo.generate_table()
            try:
                send_mail(config.RECEIVERS, fs, html, config.MAIL_SUBJECT, config.MAIL_HOST,
                          config.MAIL_USER, config.MAIL_PASS, getattr(config, 'MAIL_PORT', 0))

                console.print('[green]mission completed')
            except Exception as _e:
                console.print(f'[red]mission failed,{_e}')


if __name__ == "__main__":
    main()
