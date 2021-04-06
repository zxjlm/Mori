from abc import ABCMeta

import requests

from proxy import Proxy


class BaseAntiSpiderSolution(metaclass=ABCMeta):
    """
    反爬虫解决方法
    目前遭遇的反爬虫手段，按处理结果分，大致为两类:
    1. token放在headers中，更新headers
    2. 在post的data中添加签名验证
    反反爬虫类基于这两类构建
    """

    def __init__(self, data, headers):
        self.headers = headers
        self.data = data

    def processor(self):
        """
        具体的处理函数
        """
        ...

    def my_http_get(
        self,
        url,
        timeout=5,
        verify=True,
        allow_redirects=False,
        retry_times=5,
        success_status=200,
    ):
        """
        自定义get request
        """
        count, e_ = 0, ""
        while count < retry_times:
            try:
                proxies = Proxy.get_proxy()
                resp = requests.get(
                    url,
                    headers=self.headers,
                    proxies=proxies,
                    timeout=timeout,
                    verify=verify,
                    allow_redirects=allow_redirects,
                )
                if resp.status_code == success_status:
                    return resp
                else:
                    continue
            except Exception as _e:
                e_ = _e
                continue
        raise Exception(e_)
