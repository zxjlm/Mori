"""
@project : Mori
@author  : harumonia
@mail   : zxjlm233@gmail.com
@ide    : PyCharm
@time   : 2020-11-17 19:23:27
@description: None
"""
from concurrent.futures.thread import ThreadPoolExecutor
from functools import wraps
from io import BytesIO
from typing import Union

import requests
import json
import re
import time
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.traceback import Traceback
import platform
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from printer import ResultPrinter
from reporter import Reporter
from proxy import Proxy

__version__ = 'v0.7'
module_name = "Mori Kokoro"


def regex_checker(regex: str, resp_json: dict, exception=None) -> str:
    """
    ergodic the response tree,and try match the regex

    Args:
        regex:
        resp_json:
        exception:

    Returns:
        if match successfully,return 'OK'
        else return 'Damage' or error text

    """
    try:
        error = None
        res = regex_checker_recur(regex.split('->'), resp_json)
    except TypeError as ty_e:
        error = f'can`t match , {ty_e}'
        res = None
    except Exception as _e:
        res = None
        error = _e
    if exception:
        return 'OK' if res == exception else error
    else:
        return 'OK' if res else error


def regex_checker_recur(regex_s: list, resp_json: Union[list, dict]):
    """
    get the leaf value of this regex path
    Args:
        regex_s:regex path
        resp_json:

    Returns:
        if it can get string type value via regex path,return this string result
        else raise Exception

    """
    is_index = re.search(r'\$(\d+)\$', regex_s[0])
    if len(regex_s) == 1:
        return resp_json[regex_s[0]]
    elif is_index:
        return regex_checker_recur(regex_s[1:],
                                   resp_json[int(is_index.group(1))])
    else:
        return regex_checker_recur(regex_s[1:], resp_json[regex_s[0]])


def data_render(apis: list) -> None:
    """
    Render api data in apis,while find string warp by '{{ }}',it means there is a dynamic data, which need to be replace.

    such as {{time}} means str(int(time.time() * 1000)),edit this function can diy your render way.
    Args:
        apis:

    Returns:

    """

    def coloring(api_sub):
        """
        render api recursively
        Args:
            api_sub: member of apis

        Returns:

        """
        for key, value in api_sub.items():
            if isinstance(value, list):
                for val in value:
                    coloring(val)
            if isinstance(value, dict):
                coloring(value)
            if value == "{{time}}":
                api_sub[key] = str(int(time.time() * 1000))

    for idx, api in enumerate(apis):
        if "data" in api.keys():
            coloring(apis[idx]['data'])


def get_response(session: requests.Session, site_data: dict, headers: dict,
                 timeout: int,
                 proxies: Union[dict, None]) -> tuple:
    """
    request url and process response data,including decrypt(optional),check regex and so on.

    also, it will handle with possible errors in the process
    Args:
        session: a instance of requests.Session()
        site_data: a dictionary in site_data_list which read from json file
        headers: header for requests
        timeout: Time in seconds to wait before timing out request
        proxies: a {'http':'http://*','https':'https://*'} like dict or None

    Returns:

    """
    check_result = 'Unknown'
    check_results = {}
    traceback = None
    resp_text = ''
    exception_text = ''
    error_context = ''
    response = None

    try:
        if site_data.get('data'):
            if 'Cookie' in headers.keys():
                cookies = headers.pop('Cookie')
                for k, v in cookies.items():
                    session.cookies.set(k, v)
            if re.search(r'application.json', headers.get('Content-Type', '')):
                response = session.post(
                    site_data['url'], json=site_data['data'], headers=headers,
                    timeout=timeout, proxies=proxies,
                    allow_redirects=True)
            else:
                response = session.post(
                    site_data['url'], data=site_data['data'], headers=headers,
                    timeout=timeout, proxies=proxies,
                    allow_redirects=True)
        else:
            response = session.get(
                site_data['url'], headers=headers, timeout=timeout,
                proxies=proxies)

        if response and response.text:
            resp_text = response.text
        else:
            return response, 'request failed or get empty response', \
                   exception_text, check_results, 'Damage', traceback, \
                   resp_text

        resp_json = {}

        if site_data.get('decrypt') and resp_text:
            try:
                import importlib
                package = importlib.import_module(
                    'decrypt.' + site_data['decrypt'])
                Decrypt = getattr(package, 'Decrypt')
                resp_text = Decrypt().decrypt(resp_text)
            except Exception as _e:
                traceback = Traceback()
                error_context = 'json decrypt error'
                exception_text = _e

        if resp_text:
            try:
                # 有些键可能值是null,这种实际上是可以通过判断逻辑的,
                # 所以使用占位符(placeholder)来解除null
                # 不排除这种提取方法会引发新一轮的错误，再找到更好的提取方法之前，暂且先这样
                resp_text = re.sub(r'[\s\n]', '', resp_text). \
                    replace('null', '"placeholder"')
                resp_json = json.loads(
                    re.search(r'(")?({.*})(?(1)")', resp_text).group(0))
                if isinstance(resp_json, str):
                    # 针对 "/"../"" 类做出特殊优化
                    resp_json = json.loads(resp_json)
            except Exception as _e:
                traceback = Traceback()
                error_context = 'response data not json format'
                exception_text = _e
            try:
                check_results = {regex: regex_checker(
                    regex, resp_json, site_data.get('exception'))
                    for regex in site_data['regex']}

                if list(check_results.values()) != ['OK'] * len(check_results):
                    error_context = 'regex failed'
                    check_result = 'Damage'
                else:
                    check_result = 'OK'

            except Exception as _e:
                traceback = Traceback()
                error_context = 'json decrypt error'
                exception_text = _e
    except requests.exceptions.HTTPError as errh:
        error_context = "HTTP Error"
        exception_text = str(errh)
    except requests.exceptions.ProxyError as errp:
        error_context = "Proxy Error"
        exception_text = str(errp)
    except requests.exceptions.ConnectionError as errc:
        error_context = "Error Connecting"
        exception_text = str(errc)
    except requests.exceptions.Timeout as errt:
        error_context = "Timeout Error"
        exception_text = str(errt)
    except requests.exceptions.RequestException as err:
        error_context = "Unknown Error"
        exception_text = str(err)

    return response, error_context, exception_text, check_results, check_result, traceback, resp_text


def processor(site_data: dict, timeout: int, use_proxy: bool,
              result_printer: ResultPrinter, task_id: TaskID,
              progress: Progress) -> dict:
    """
    the main processor for mori.
    Args:
        result_printer:
        site_data: a dictionary in site_data_list which read from json file
        timeout: Time in seconds to wait before timing out request
        use_proxy: not use proxy while this value is False. Of course, proxy
            field in the config file should have a value.
            result_printer: when processor finish , result_printer will be
            invoked to output result.
        task_id: it is id of main_progress, when processor finish,
            main_progress while step 1.
        progress: main progress.

    Returns:
        Dictionary containing results from report.
        'name': api name in configuration,
        'url': api url in configuration,
        'base_url': api base_url in configuration,
        'resp_text': raw response.text from url, if length of resp_text > 500,
            it wont`t display on console, and you can add --xls to see detail
            in *.xls file.
        'status_code': response status_code,
        'time(s)': time in seconds spend on request,
        'error_text': error_text,
        'exception_text': exception_text,
        'check_result': 'OK' , 'Damage' or 'Unknown'. Default is 'Unknown'.
        'traceback': Instance of Traceback.
        'check_results': check_results, each result of all regexes.
        'remark': field hold on
    """
    rel_result, result, monitor_id = {}, {}, None
    session = requests.Session()
    max_retries = 5
    if progress:
        monitor_id = progress.add_task(f'{site_data["name"]} (retry)',
                                       visible=False, total=max_retries)
    # progress.update(monitor_id, advance=-max_retries)
    for retries in range(max_retries):

        traceback, r, resp_text = None, None, ''
        error_text, exception_text, check_result, check_results = '', '', \
                                                                  'Unknown', {}

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; '
                          'rv:55.0) Gecko/20100101 Firefox/55.0',
        }

        if site_data.get('headers'):
            if isinstance(site_data.get('headers'), dict):
                headers.update(site_data.get('headers'))

        Proxy.set_proxy_url(site_data.get('proxy'),
                            site_data.get('strict_proxy'), use_proxy, headers)

        if site_data.get('antispider') and site_data.get('data'):
            try:
                import importlib
                package = importlib.import_module(
                    'antispider.' + site_data['antispider'])
                Antispider = getattr(package, 'Antispider')
                site_data['data'], headers = Antispider(
                    site_data['data'], headers).processor()
            except Exception as _e:
                site_data['single'] = True
                site_data['exception_text'] = _e
                site_data['traceback'] = Traceback()
                raise Exception('antispider failed')

        try:
            proxies = Proxy.get_proxy()
        except Exception as _e:
            site_data['single'] = True
            site_data['exception_text'] = _e
            site_data['traceback'] = Traceback()
            raise Exception('all of six proxies can`t be used')

        try:
            if site_data.get('single'):
                check_result = 'Damage'
                error_text = site_data['error_text']
                exception_text = site_data['exception_text']
                traceback = site_data['traceback']
            else:
                r, error_text, exception_text, check_results, check_result, \
                traceback, resp_text = get_response(
                    session,
                    site_data,
                    headers,
                    timeout,
                    proxies)
                if error_text and retries + 1 < max_retries:
                    if progress:
                        progress.update(monitor_id, advance=1, visible=True,
                                        refresh=True)
                    continue

            result = {
                'name': site_data['name'],
                'url': site_data['url'],
                'base_url': site_data.get('base_url', ''),
                'resp_text': resp_text if len(
                    resp_text) < 500 else 'too long, and you can add --xls '
                                          'to see detail in *.xls file',
                'status_code': getattr(r, 'status_code', 'failed'),
                'time(s)': float(r.elapsed.total_seconds()) if r else -1.,
                'error_text': error_text,
                'exception_text': exception_text,
                'check_result': check_result,
                'traceback': traceback,
                'check_results': check_results,
                'remark': site_data.get('remark', '')
            }

            rel_result = dict(result.copy())
            rel_result['resp_text'] = resp_text
            break
        except Exception as error:
            result = {
                'name': site_data['name'],
                'url': site_data['url'],
                'base_url': site_data.get('base_url', ''),
                'resp_text': resp_text if len(
                    resp_text) < 500 else 'too long, and you can add --xls '
                                          'to see detail in *.xls file',
                'status_code': getattr(r, 'status_code', 'failed'),
                'time(s)': float(r.elapsed.total_seconds()) if r else -1.,
                'error_text': error or 'site handler error',
                'check_result': check_result,
                'traceback': Traceback(),
                'check_results': check_results,
                'remark': site_data.get('remark', '')
            }
            rel_result = dict(result.copy())

    if result_printer:
        progress.update(task_id, advance=1, refresh=True)
        result_printer.printer(result)
        progress.remove_task(monitor_id)

    return rel_result


def diy_rich_progress(func):
    """
    Decorator of rich`s progress.

    It`s aim to decouple, but the effect is not ideal.
    Args:
        func:

    Returns:

    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        wrapper
        Args:
            *args: like mori
            **kwargs:

        Returns:

        """
        console = kwargs.pop('console')
        if console:
            with Progress(console=console, auto_refresh=False) as progress:
                results = func(progress, *args, **kwargs)
        else:
            results = func(None, *args, **kwargs)
        return results

    return wrapper


@diy_rich_progress
def mori(progress: Progress, site_data_l: list, result_printer: ResultPrinter,
         timeout: int, use_proxy: bool) -> list:
    """
    Run mori.
    Args:
        progress: Instance of rich.Progress() defined in decorator.
        site_data_l: Read from json file.
        result_printer: to print the result.
        timeout: Defined in cmd arguments, default is 35s.
        use_proxy: Defined in cmd arguments ( --no--proxy ).

    Returns:
        list-dict
        content of the dictionary can be found in function processor().

    """
    tasks = []
    with ThreadPoolExecutor(max_workers=len(site_data_l) if len(
            site_data_l) <= 20 else 20) as pool:
        task_id = progress.add_task('Processing ...', total=len(site_data_l))
        for site_data in site_data_l:
            task = pool.submit(processor, site_data, timeout, use_proxy,
                               result_printer, task_id, progress)
            tasks.append(task)
    # wait(tasks, return_when=ALL_COMPLETED)

    results_total = [getattr(foo, '_result') for foo in tasks]

    return results_total


def timeout_check(value):
    """
    Checks timeout for validity.
    Args:
        value:

    Returns:
        Floating point number representing the time (in seconds) that should be
    used for the timeout.

    NOTE:  Will raise an exception if the timeout in invalid.
    """
    from argparse import ArgumentTypeError

    try:
        timeout = float(value)
    except Exception as _:
        raise ArgumentTypeError(f"Timeout '{value}' must be a number.")
    if timeout <= 0:
        raise ArgumentTypeError(
            f"Timeout '{value}' must be greater than 0.0s.")
    return timeout


def send_mail(receivers: list, file_content: BytesIO, html: str, subject: str,
              mail_host: str, mail_user: str,
              mail_pass: str, mail_port: int = 0):
    """
    Send mail.
    Read necessary configuration from config.py.
    The mean of each argument can be found in README.md.
    Args:
        receivers: a list in which store receivers` email address. such as [zxjlm233@gamil.com].
        file_content: a BytesIO type. Because when send email, mori also send a CSV file of detail result.
                    The content is not absolutely generated but read from the workbook of xlwt.
        html: it`s a html5 table of CSV, for more intuitive display.
        subject: literal meaning
        mail_host: literal meaning
        mail_user: username of mail sender.
        mail_pass: password of mail senders.
        mail_port: depend on your service.

    Returns:
        None

    Notes: It`s a universal function can use in other scene by a little modification.
    """
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
    """
    Just main
    Returns:

    """

    version_string = f"%(prog)s {__version__}\n" + \
                     f"requests:  {requests.__version__}\n" + \
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
                        help="Show all information of the apis in files."
                        )
    parser.add_argument("--json", "-j", metavar="JSON_FILES",
                        dest="json_files", type=str, nargs='+', default=None,
                        help="Load data from a local JSON file.Accept plural files.")
    parser.add_argument("--email", "-e",
                        metavar="EMAIL_ADDRESS_LIST",
                        dest="emails", type=str, nargs='*', default='not send',
                        help="Send email to mailboxes. You can order the addresses in cmd argument, default is in the file 'config.py'.")
    parser.add_argument("--print-invalid",
                        action="store_false", dest="print_invalid",
                        default=False,
                        help="Output api(s) that was invalid."
                        )
    parser.add_argument("--no-proxy", default=True,
                        action="store_false", dest="use_proxy",
                        help="Use proxy.Proxy should define in config.py"
                        )
    parser.add_argument("--timeout",
                        action="store", metavar='TIMEOUT',
                        dest="timeout", type=timeout_check, default=None,
                        help="Time (in seconds) to wait for response to requests. "
                             "Default timeout is 35s. "
                             "A longer timeout will be more likely to get results from slow sites. "
                             "On the other hand, this may cause a long delay to gather all results."
                        )

    args = parser.parse_args()

    console = Console()

    file_path_l = args.json_files or ['./apis.json']
    apis = []

    for file_path in file_path_l:
        with open(file_path, 'r', encoding='utf-8') as f:
            apis_sub = json.load(f)
        console.print(f'[green] read file {file_path} success~')
        data_render(apis_sub)
        apis += apis_sub

    if args.show_site_list:

        keys_to_show = ['name', 'url', 'data']
        apis_to_show = list(map(
            lambda api: {key: value for key, value in api.items() if
                         key in keys_to_show}, apis))
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

        # start = time.perf_counter()
        # for _ in range(20):
        results = mori(site_data_l=apis, console=console,
                       result_printer=result_printer,
                       timeout=args.timeout or 35,
                       use_proxy=args.use_proxy)
        # use_time = time.perf_counter() - start
        # print('total_use_time:{}'.format(use_time))

        if args.xls or isinstance(args.emails, list):
            for i, result in enumerate(results):
                results[i]['check_results'] = '\n'.join(
                    [f'{key} : {value}' for key, value in
                     result['check_results'].items()])

            repo = Reporter(
                ['name', 'url', 'base_url', 'status_code', 'time(s)',
                 'check_result', 'check_results', 'error_text', 'remark',
                 'resp_text'], results)

            if args.xls:
                console.print('[cyan]now generating report...')

                repo.processor()

                console.print('[green]mission completed')

            if isinstance(args.emails, list):
                try:
                    import config
                except Exception as _e:
                    console.print(
                        'can`t get config.py file, please read README.md, search keyword [red]config.py',
                        _e)
                    return

                console.print('[cyan]now sending email...')

                if args.emails:
                    receivers = args.emails
                else:
                    receivers = config.RECEIVERS

                fs = repo.processor(is_stream=True)
                html = repo.generate_table()
                try:
                    send_mail(receivers, fs, html, config.MAIL_SUBJECT,
                              config.MAIL_HOST,
                              config.MAIL_USER, config.MAIL_PASS,
                              getattr(config, 'MAIL_PORT', 0))

                    console.print('[green]mission completed')
                except Exception as _e:
                    console.print(f'[red]mission failed,{_e}')


if __name__ == "__main__":
    main()
