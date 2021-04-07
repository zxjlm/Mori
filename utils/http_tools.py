# -*- coding: utf-8 -*-
"""
    :time: 2021/4/7 9:28
    :author: Harumonia
    :url: http://harumonia.moe
    :project: Mori
    :file: http_tools.py
    :copyright: © 2021 harumonia<zxjlm233@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
import json
import re
from typing import Union

import requests
from rich.traceback import Traceback

from utils.data_processor import regex_checker


def get_response(
    session: requests.Session,
    site_data: dict,
    headers: dict,
    timeout: int,
    proxies: Union[dict, None],
) -> tuple:
    """
    request url and process response data,including decrypt(optional),
    check regex and so on.

    also, it will handle with possible errors in the process
    Args:
        session: a instance of requests.Session()
        site_data: a dictionary in site_data_list which read from json file
        headers: header for requests
        timeout: Time in seconds to wait before timing out request
        proxies: a {'http':'http://*','https':'https://*'} like dict or None

    Returns:

    """
    check_result = "Unknown"
    check_results = {}
    traceback = None
    resp_text = ""
    exception_text = ""
    error_context = ""
    response = None

    try:
        if site_data.get("data"):
            if "Cookie" in headers.keys():
                cookies = headers.pop("Cookie")
                for k, v in cookies.items():
                    session.cookies.set(k, v)
            if re.search(r"application.json", headers.get("Content-Type", "")):
                response = session.post(
                    site_data["url"],
                    json=site_data["data"],
                    headers=headers,
                    timeout=timeout,
                    proxies=proxies,
                    allow_redirects=True,
                    verify=False,
                )
            else:
                response = session.post(
                    site_data["url"],
                    data=site_data["data"],
                    headers=headers,
                    timeout=timeout,
                    proxies=proxies,
                    allow_redirects=True,
                    verify=False,
                )
        else:
            response = session.get(
                site_data["url"],
                headers=headers,
                timeout=timeout,
                proxies=proxies,
                verify=False,
            )

        if response and response.text:
            resp_text = response.text
        else:
            return (
                response,
                "request failed or get empty response",
                exception_text,
                check_results,
                "Damage",
                traceback,
                resp_text,
            )

        resp_json = {}

        if site_data.get("decrypt") and resp_text:
            try:
                import importlib

                package = importlib.import_module("decrypt." + site_data["decrypt"])
                Decrypt = getattr(package, "Decrypt")
                resp_text = Decrypt().decrypt(resp_text)
            except Exception as _e:
                traceback = Traceback()
                error_context = "json decrypt error"
                exception_text = _e

        if resp_text:
            try:
                # 有些键可能值是null,这种实际上是可以通过判断逻辑的,
                # 所以使用占位符(placeholder)来解除null
                # 不排除这种提取方法会引发新一轮的错误，再找到更好的提取方法之前,
                # 暂且先这样
                resp_text = re.sub(r"[\s\n]", "", resp_text).replace("null", "9527")
                if site_data["regex"][0].startswith("$"):
                    # 直接返回了一个列表的json格式
                    resp_json = json.loads(
                        re.search(r'(")?(\[.*])(?(1)")', resp_text).group(0)
                    )
                else:
                    resp_json = json.loads(
                        re.search(r'(")?({.*})(?(1)")', resp_text).group(0)
                    )
                if isinstance(resp_json, str):
                    # 针对 "/"../"" 类做出特殊优化
                    resp_json = json.loads(resp_json)
            except Exception as _e:
                traceback = Traceback()
                error_context = "response data not json format"
                exception_text = _e
            try:
                check_results = {
                    regex: regex_checker(regex, resp_json, site_data.get("exception"))
                    for regex in site_data["regex"]
                }

                if list(check_results.values()) != ["OK"] * len(check_results):
                    error_context = "regex failed"
                    check_result = "Damage"
                else:
                    check_result = "OK"

            except Exception as _e:
                traceback = Traceback()
                error_context = "json decrypt error"
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

    return (
        response,
        error_context,
        exception_text,
        check_results,
        check_result,
        traceback,
        resp_text,
    )


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
    except Exception as _e:
        raise ArgumentTypeError(f"Timeout '{value}' must be a number. {_e}")
    if timeout <= 0:
        raise ArgumentTypeError(f"Timeout '{value}' must be greater than 0.0s.")
    return timeout
