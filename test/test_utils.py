# -*- coding: utf-8 -*-
"""
    :time: 2021/4/7 10:16
    :author: Harumonia
    :url: http://harumonia.moe
    :project: Mori
    :file: test_utils.py
    :copyright: © 2021 harumonia<zxjlm233@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from utils.data_processor import data_render


def test_render_data():
    apis = [
        {
            "name": "Mori get api without params",
            "url": "http://mori.harumonia.moe/",
            "regex": ["Hello"],
            "data": {"t": "{{time}}"},
        }
    ]
    data_render(apis)
    assert apis[0]["data"]["t"] != "{{time}}"
