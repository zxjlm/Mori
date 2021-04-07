# -*- coding: utf-8 -*-
"""
    :time: 2021/4/7 9:26
    :author: Harumonia
    :url: http://harumonia.moe
    :project: Mori
    :file: data_processor.py
    :copyright: © 2021 harumonia<zxjlm233@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
import re
import time
from typing import Union


def data_render(apis: list) -> None:
    """
    Render api data in apis,while find string warp by '{{ }}',
    it means there is a dynamic data, which need to be replace.

    such as {{time}} means str(int(time.time() * 1000)),
    edit this function can diy your render way.

    Args:
        apis:

    Returns:

    """

    def rendering_data(api_sub):
        """
        render api recursively
        Args:
            api_sub: member of apis

        Returns:

        """
        if isinstance(api_sub, dict):
            for key, value in api_sub.items():
                if isinstance(value, list):
                    for val in value:
                        rendering_data(val)
                elif isinstance(value, dict):
                    rendering_data(value)
                else:
                    if value == "{{time}}":
                        api_sub[key] = str(int(time.time() * 1000))
        elif isinstance(api_sub, list):
            for key, val in enumerate(api_sub):
                if isinstance(val, str):
                    if val == "{{time}}":
                        api_sub[key] = str(int(time.time() * 1000))
                else:
                    rendering_data(val)

        # for key, value in api_sub.items():
        #     if isinstance(value, list):
        #         for val in value:
        #             rendering_data(val)
        #     if isinstance(value, dict):
        #         rendering_data(value)
        #     if value == "{{time}}":
        #         api_sub[key] = str(int(time.time() * 1000))

    for idx, api in enumerate(apis):
        if "data" in api.keys():
            rendering_data(apis[idx]["data"])


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
        res = regex_checker_recur(regex.split("->"), resp_json)
    except TypeError as ty_e:
        error = f"can`t match , {ty_e}"
        res = None
    except Exception as _e:
        res = None
        error = _e
    if exception:
        return "OK" if res == exception else error
    else:
        return "OK" if res else error


def regex_checker_recur(regex_s: list, resp_json: Union[list, dict]):
    """
    get the leaf value of this regex path
    Args:
        regex_s:regex path
        resp_json:

    Returns:
        if it can get string type value via regex path
        ,return this string result, else raise Exception

    """
    is_index = re.search(r"\$(\d+)\$", regex_s[0])
    if len(regex_s) == 1:
        return resp_json[regex_s[0]]
    elif is_index:
        return regex_checker_recur(regex_s[1:], resp_json[int(is_index.group(1))])
    else:
        return regex_checker_recur(regex_s[1:], resp_json[regex_s[0]])
