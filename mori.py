"""
@project : Mori
@author  : harumonia
@mail   : zxjlm233@gmail.com
@ide    : PyCharm
@time   : 2020-11-17 19:23:27
@description: None
"""
from concurrent.futures.thread import ThreadPoolExecutor

import requests
import json
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.traceback import Traceback
import platform
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from printer import ResultPrinter
from reporter import Reporter
from proxy import Proxy

__version__ = "v1.1"

from utils.data_processor import data_render, regex_checker
from utils.http_tools import get_response, timeout_check
from utils.rich_tools import diy_rich_progress
from utils.send_mail import send_mail

module_name = "Mori Kokoro"
console = Console()


def processor(
        site_data: dict,
        timeout: int,
        use_proxy: bool,
        result_printer: ResultPrinter,
        task_id: TaskID,
        progress: Progress,
) -> dict:
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
        monitor_id = progress.add_task(
            f'{site_data["name"]} (retry)', visible=False, total=max_retries
        )
    # progress.update(monitor_id, advance=-max_retries)
    check_result, check_results = "Damage", []
    r, resp_text = None, ""
    try:
        for retries in range(max_retries):
            check_result = "Damage"
            traceback, r, resp_text = None, None, ""
            error_text, exception_text, check_results = "", "", {}
            check_result = "Unknown"

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; "
                              "rv:55.0) Gecko/20100101 Firefox/55.0",
            }

            if site_data.get("headers"):
                if isinstance(site_data.get("headers"), dict):
                    headers.update(site_data.get("headers"))

            Proxy.set_proxy_url(
                site_data.get("proxy"),
                site_data.get("strict_proxy"),
                use_proxy,
                headers,
            )

            if site_data.get("antispider") and site_data.get("data"):
                try:
                    import importlib

                    package = importlib.import_module(
                        "antispider." + site_data["antispider"]
                    )
                    Antispider = getattr(package, "Antispider")
                    site_data["data"], headers = Antispider(
                        site_data["data"], headers
                    ).processor()
                except Exception as _e:
                    site_data["single"] = True
                    site_data["exception_text"] = _e
                    site_data["traceback"] = Traceback()
                    raise Exception("antispider failed")

            try:
                proxies = Proxy.get_proxy()
            except Exception as _e:
                site_data["single"] = True
                site_data["exception_text"] = _e
                site_data["traceback"] = Traceback()
                raise Exception("all of six proxies can`t be used")

            if site_data.get("single"):
                error_text = site_data["error_text"]
                exception_text = site_data["exception_text"]
                traceback = site_data["traceback"]
            else:
                (
                    r,
                    error_text,
                    exception_text,
                    check_results,
                    check_result,
                    traceback,
                    resp_text,
                ) = get_response(session, site_data, headers, timeout, proxies)
                if error_text and retries + 1 < max_retries:
                    if progress:
                        progress.update(
                            monitor_id, advance=1, visible=True, refresh=True
                        )
                    continue

            result = {
                "name": site_data["name"],
                "url": site_data["url"],
                "base_url": site_data.get("base_url", ""),
                "resp_text": resp_text
                if len(resp_text) < 500
                else "too long, and you can add --xls " "to see detail in *.xls file",
                "status_code": getattr(r, "status_code", "failed"),
                "time(s)": float(r.elapsed.total_seconds()) if r else -1.0,
                "error_text": str(error_text),
                "exception_text": exception_text,
                "check_result": check_result,
                "traceback": traceback,
                "check_results": check_results,
                "remark": site_data.get("remark", ""),
            }

            rel_result = dict(result.copy())
            rel_result["resp_text"] = resp_text
            break
    except Exception as error:
        result = {
            "name": site_data["name"],
            "url": site_data["url"],
            "base_url": site_data.get("base_url", ""),
            "resp_text": resp_text
            if len(resp_text) < 500
            else "too long, and you can add --xls " "to see detail in *.xls file",
            "status_code": getattr(r, "status_code",
                                   "failed") if r else "none",
            "time(s)": float(r.elapsed.total_seconds()) if r else -1.0,
            "error_text": str(error) or "site handler error",
            "check_result": check_result,
            "traceback": Traceback(),
            "check_results": check_results,
            "remark": site_data.get("remark", ""),
        }
        rel_result = dict(result.copy())

    if result_printer:
        progress.update(task_id, advance=1, refresh=True)
        result_printer.printer(result)
        progress.remove_task(monitor_id)

    return rel_result


@diy_rich_progress
def mori(
        progress: Progress,
        site_data_l: list,
        timeout: int,
        use_proxy: bool,
        verbose: bool,
        print_invalid: bool
) -> list:
    """
    Run mori.
    Args:
        print_invalid:
        verbose:
        progress: Instance of rich.Progress() defined in decorator.
        site_data_l: Read from json file.
        timeout: Defined in cmd arguments, default is 35s.
        use_proxy: Defined in cmd arguments ( --no--proxy ).

    Returns:
        list-dict
        content of the dictionary can be found in function processor().

    """
    result_printer = ResultPrinter(verbose, print_invalid, console)

    tasks = []
    with ThreadPoolExecutor(
            max_workers=len(site_data_l) if len(site_data_l) <= 20 else 20
    ) as pool:
        task_id = progress.add_task("Processing ...", total=len(site_data_l))
        for site_data in site_data_l:
            task = pool.submit(
                processor,
                site_data,
                timeout,
                use_proxy,
                result_printer,
                task_id,
                progress,
            )
            tasks.append(task)
    # wait(tasks, return_when=ALL_COMPLETED)

    results_total = [getattr(foo, "_result") for foo in tasks]

    return results_total


def main():
    """
    Just main
    Returns:

    """

    version_string = (
        f"%(prog)s {__version__} \n "
        f"requests:  {requests.__version__} \n"
        f"Python:  {platform.python_version()} \n"
    )

    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description=f"{module_name} " f"(Version {__version__})",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=version_string,
        help="Display version information and dependencies.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        "-d",
        "--debug",
        action="store_true",
        dest="verbose",
        default=False,
        help="Display extra debugging information and metrics.",
    )
    parser.add_argument(
        "--xls",
        action="store_true",
        dest="xls",
        default=False,
        help="Create .xls File.(Microsoft Excel file format)",
    )
    parser.add_argument(
        "--show-all-site",
        action="store_true",
        dest="show_site_list",
        default=False,
        help="Show all information of the apis in files.",
    )
    parser.add_argument(
        "--json",
        "-j",
        metavar="JSON_FILES",
        dest="json_files",
        type=str,
        nargs="+",
        default=None,
        help="Load data from a local JSON file.Accept plural " "files.",
    )
    parser.add_argument(
        "--email",
        "-e",
        metavar="EMAIL_ADDRESS_LIST",
        dest="emails",
        type=str,
        nargs="*",
        default="not send",
        help="Send email to mailboxes. You can order the "
             "addresses in cmd argument, default is "
             "in the file 'config.py'.",
    )
    parser.add_argument(
        "--print-invalid",
        action="store_false",
        dest="print_invalid",
        default=False,
        help="Output api(s) that was invalid.",
    )
    parser.add_argument(
        "--no-proxy",
        default=True,
        action="store_false",
        dest="use_proxy",
        help="Use proxy.Proxy should define in config.py",
    )
    parser.add_argument(
        "--timeout",
        action="store",
        metavar="TIMEOUT",
        dest="timeout",
        type=timeout_check,
        default=None,
        help="Time (in seconds) to wait for response to "
             "requests. "
             "Default timeout is 35s. "
             "A longer timeout will be more likely to "
             "get results from slow sites. "
             "On the other hand, this may cause a long "
             "delay to gather all results.",
    )

    args = parser.parse_args()

    file_path_l = args.json_files or ["./apis.json"]
    apis = []

    for file_path in file_path_l:
        with open(file_path, "r", encoding="utf-8") as f:
            apis_sub = json.load(f)
        console.print(f"[green] read file {file_path} success~")
        data_render(apis_sub)
        apis += apis_sub

    if args.show_site_list:
        keys_to_show = ["name", "url", "data"]
        apis_to_show = list(
            map(
                lambda api: {
                    key: value for key, value in api.items() if
                    key in keys_to_show
                },
                apis,
            )
        )
        console.print(apis_to_show)

    else:
        r = r"""
             __  __               _   _  __        _
            |  \/  |  ___   _ __ (_) | |/ /  ___  | | __  ___   _ __   ___
            | |\/| | / _ \ | '__|| | | ' /  / _ \ | |/ / / _ \ | '__| / _ \
            | |  | || (_) || |   | | | . \ | (_) ||   < | (_) || |   | (_) |
            |_|  |_| \___/ |_|   |_| |_|\_\ \___/ |_|\_\ \___/ |_|    \___/
            """
        print(r)

        # start = time.perf_counter()
        # for _ in range(20):
        results = mori(
            site_data_l=apis,
            timeout=args.timeout or 35,
            use_proxy=args.use_proxy,
            verbose=args.verbose,
            print_invalid=args.print_invalid
        )
        # use_time = time.perf_counter() - start
        # print('total_use_time:{}'.format(use_time))

        if args.xls or isinstance(args.emails, list):
            for i, result in enumerate(results):
                results[i]["check_results"] = "\n".join(
                    [
                        f"{key} : {value}"
                        for key, value in result["check_results"].items()
                    ]
                )

            repo = Reporter(
                [
                    "name",
                    "url",
                    "base_url",
                    "status_code",
                    "time(s)",
                    "check_result",
                    "check_results",
                    "error_text",
                    "remark",
                    "resp_text",
                ],
                results,
            )

            if args.xls:
                console.print("[cyan]now generating report...")

                repo.processor()

                console.print("[green]mission completed")

            if isinstance(args.emails, list):
                try:
                    import config
                except Exception as _e:
                    console.print(
                        "can`t get config.py file, please read README.md, "
                        "search keyword [red]config.py",
                        _e,
                    )
                    return

                console.print("[cyan]now sending email...")

                if args.emails:
                    receivers = args.emails
                else:
                    receivers = config.RECEIVERS

                fs = repo.processor(is_stream=True)
                html = repo.generate_table()
                try:
                    send_mail(
                        receivers,
                        fs,
                        html,
                        config.MAIL_SUBJECT,
                        config.MAIL_HOST,
                        config.MAIL_USER,
                        config.MAIL_PASS,
                        getattr(config, "MAIL_PORT", 0),
                    )

                    console.print("[green]mission completed")
                except Exception as _e:
                    console.print(f"[red]mission failed,{_e}")


if __name__ == "__main__":
    main()
