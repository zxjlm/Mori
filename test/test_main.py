"""
@project : Mori
@author  : harumonia
@mail   : zxjlm233@163.com
@ide    : PyCharm
@time   : 2020-11-28 09:48:53
@description: TODO
"""
import json

import pytest
import requests
from rich.console import Console
from rich.progress import Progress

from antispider.mori_antispider import Antispider
from decrypt.mori_decrypt import Decrypt
from mori import mori, processor
from printer import ResultPrinter


@pytest.fixture
def init_console():
    return Console()


@pytest.fixture
def init_result_printer(init_console):
    return ResultPrinter(False, False, init_console)


def test_anti_spider():
    headers = {"Content-Type": "application/json", "accept": "application/json"}
    data = {"token": 0}
    anti = Antispider(data, headers)
    data_, headers_ = anti.processor()
    response = requests.post(
        "http://mori.harumonia.moe/token/", json=data_, headers=headers_
    )
    assert response.status_code == 200


def test_anti_spider_failed():
    headers = {"Content-Type": "application/json", "accept": "application/json"}
    response = requests.post(
        "http://mori.harumonia.moe/token/", json={}, headers=headers
    )
    assert response.status_code == 422


def test_encryption():
    url = "http://mori.harumonia.moe/base64/"
    response = requests.get(url)
    assert (
        response.text != '{"class": [{"name": "A", "total": 64, '
        '"mid-term-examination": 2, "students": '
        '[{"number": "1", "name": "Ren", "sex": "F"}, '
        '{"number": "2", "name": "Tio", "sex": "F"}]}]}'
    )
    dec_res = Decrypt().decrypt(response.text)
    json_res = json.loads(dec_res)
    assert json_res["class"][0]["name"] == "A"


def test_single_mori(init_result_printer, init_console):
    site_data = {
        "name": "Mori get api without params",
        "url": "http://mori.harumonia.moe/",
        "regex": ["Hello"],
    }
    with Progress(console=init_console, auto_refresh=False) as progress:
        task_id = progress.add_task("Processing ...", total=1)
        result = processor(
            site_data,
            35,
            False,
            init_result_printer,
            task_id,
            progress,
        )
    assert result["status_code"] == 200
    assert result["check_result"] == "OK"
    assert result["check_results"]["Hello"] == "OK"


def test_multi_mori(init_console):
    apis = [
        {
            "name": "Mori get api without params | error case | key-error",
            "url": "http://mori.harumonia.moe/",
            "regex": ["hello->error"],
        },
        {
            "name": "Mori get api without params | error case | type-error",
            "url": "http://mori.harumonia.moe/",
            "regex": ["Hello->error"],
        },
        {
            "name": "Mori get api encrypt",
            "url": "http://mori.harumonia.moe/base64/",
            "regex": ["class->$0$->students"],
            "decrypt": "mori_decrypt",
        },
        {
            "name": "Mori post api antispider",
            "url": "http://mori.harumonia.moe/token/",
            "regex": ["result"],
            "antispider": "mori_antispider",
            "headers": {
                "Content-Type": "application/json",
                "accept": "application/json",
            },
            "data": {"token": 0},
        },
    ]
    results = mori(apis, 35, False, False, False)
    assert results[0]["error_text"] == "regex failed"
    assert results[1]["check_result"] == "Damage"
    assert results[2]["error_text"] == ""
    assert results[2]["check_result"] == "OK"
    assert results[3]["check_result"] == "OK"
