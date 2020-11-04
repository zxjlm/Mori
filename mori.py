import requests
import json
import re
from requests_futures.sessions import FuturesSession
import time
from rich.console import Console
import platform
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from art import tprint
from printer import SimpleResult, ResultPrinter
import csv

__version__ = 'v0.2'
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
                api[key] = str(int(time.time()*1000))

    for idx, api in enumerate(apis):
        if "data" in api.keys():
            coloring(apis[idx])


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

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }

    results_total = []

    for site_data in site_datas:
        check_result = 'Damage'
        try:
            if site_data.get('headers'):
                if isinstance(site_data.get('headers'), dict):
                    headers.update(site_data.get('headers'))

            for _ in range(4):
                proxies = None
                if site_data.get('proxy'):
                    proxy = requests.get(site_data['proxy']).text
                    proxies = {"http": proxy, "https": proxy}

                if site_data.get('data'):
                    if headers.get('Content-Type') == 'application/json':
                        site_data["request_future"] = session.post(
                            site_data['url'], json=site_data['data'], headers=headers, timeout=timeout, proxies=proxies)
                    else:
                        # data = json.dumps(site_data['data'])
                        site_data["request_future"] = session.post(
                            site_data['url'], data=site_data['data'], headers=headers, timeout=timeout, proxies=proxies)
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

            if site_data.get('decrypt'):
                try:
                    import importlib
                    package = importlib.import_module(site_data['decrypt'])
                    Decrypt = package.Decrypt
                    resp_text = Decrypt().decrypt(resp_text)
                except Exception as _e:
                    error_text = 'json decrypt error'
                    expection_text = _e

            if resp_text:
                try:
                    resp_json = json.loads(
                        re.search('({.*})', resp_text).group(1))
                    check_result = regex_checker(
                        site_data['regex'], resp_json, site_data.get('exception'))
                    if check_result != 'OK':
                        error_text = 'regex failed'
                except Exception as _e:
                    error_text = 'data responsed is not json format.'
                    expection_text = _e

            result = {
                'name': site_data['name'],
                'url': site_data['url'],
                'resp_text': resp_text if len(resp_text) < 1000 else 'too long',
                'resp_status_code': r.status_code,
                'time': r.elapsed,
                'error_text': error_text,
                'expection_text': expection_text,
                'check_result': check_result
            }

        except Exception as error:
            result = {
                'name': site_data['name'],
                'url': site_data['url'],
                'resp_text': None,
                'resp_status_code': -1,
                'time': -1,
                'error_text': 'site handler error',
                'expection_text': error,
                'check_result': check_result
            }

        results_total.append(result)
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


def main():
    version_string = f"%(prog)s {__version__}\n" +  \
                     f"{requests.__description__}:  {requests.__version__}\n" + \
                     f"Python:  {platform.python_version()}"

    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                            description=f"{module_name} (Version {__version__})"
                            )
    parser.add_argument("--version",
                        action="version",  version=version_string,
                        help="Display version information and dependencies."
                        )
    parser.add_argument("--verbose", "-v", "-d", "--debug",
                        action="store_true",  dest="verbose", default=False,
                        help="Display extra debugging information and metrics."
                        )
    parser.add_argument("--csv",
                        action="store_true",  dest="csv", default=False,
                        help="Create Comma-Separated Values (CSV) File."
                        )
    parser.add_argument("--show-all-site",
                        action="store_true",
                        dest="show_site_list", default=False,
                        help="Show all infomations of the apis in files."
                        )
    parser.add_argument("--json", "-j", metavar="JSON_FILE",
                        dest="json_file", default=None,
                        help="Load data from a local JSON file.")
    parser.add_argument("--print-invaild",
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

    with open(file_path, 'r') as f:
        apis = json.load(f)
    data_render(apis)

    if args.show_site_list:

        keys_to_show = ['name', 'url', 'data']
        apis_to_show = list(map(lambda api: {key: value for key,
                                             value in api.items() if key in keys_to_show}, apis))
        console.print(apis_to_show)

    else:
        tprint('Mori Kokoro')

        result_printer = ResultPrinter(
            args.verbose, args.print_invalid, console)

        results = mori(apis, result_printer, timeout=args.timeout or 15)

        if args.csv:
            console.print('[cyan]now generate report...')
            with open("report.csv", "w", newline='', encoding="utf-8") as csv_report:
                writer = csv.writer(csv_report)
                writer.writerow(['name',
                                 'url',
                                 'status_code',
                                 'time',
                                 'check_result',
                                 'error_text',
                                 ]
                                )
                for site in results:
                    writer.writerow([site['name'],
                                     site['url'],
                                     site['resp_status_code'],
                                     site['time'],
                                     site['check_result'],
                                     site['error_text'],
                                     ]
                                    )


if __name__ == "__main__":
    main()
