"""
@project : Mori
@author  : zhang_xinjian
@mail   : zxjlm233@163.com
@ide    : PyCharm
@time   : 2020-11-28 09:48:53
@description: TODO
"""
import json

import requests

from antispider.mori_antispider import Antispider
from decrypt.mori_decrypt import Decrypt


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
