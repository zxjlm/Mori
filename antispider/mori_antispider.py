from antispider.base_antispider import BaseAntiSpiderSolution
import requests


class Antispider(BaseAntiSpiderSolution):
    """
    这里写了一个用来测试的反爬虫样例，反爬虫运作思路如下：
    1. 向'http://173.82.155.186/gettoken'申请一个与ip绑定的token
    2. 将该token写入data,后续的访问需要验证token

    Attention: 某些token与cookie有相互映照，这里将cookie以字典的形式存储到self.headers
            中即可
    """

    def processor(self):
        url = 'http://173.82.155.186/gettoken'
        resp = self.my_http_get(url)
        if resp:
            self.data['token'] = resp.text.replace('"', '')
            # 如果需要存储cookie ↓
            # self.headers['Cookie'] = resp.cookies.get_dict()
        else:
            raise Exception('return None')
        return self.data, self.headers
