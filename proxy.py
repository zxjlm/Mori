import time
import requests
import logging


class Proxy:
    """
    获取代理
    """
    proxy_url = ''
    proxies = None

    @staticmethod
    def test_api(proxies):
        url = 'https://www.baidu.com/'
        resp = requests.get(url, proxies=proxies, timeout=15)
        return resp and resp.status_code == 200

    @staticmethod
    def get_api(api_addr: str) -> dict:
        """
        请求接口，获取代理。 
        return 代理格式 "http://*.*.*.*:*"
        """
        result = {}
        response = None
        for _ in range(0, 5):
            try:
                response = requests.get(
                    api_addr,
                    timeout=10
                )
                status = response.status_code
                if str(status) == "200" and response.text.strip():
                    ip_addr = response.text.strip()
                    result = {
                        'https': ip_addr,
                        'http': ip_addr
                    }
                    if Proxy.test_api(result):
                        break
                if str(status) == "400" or str(status) == "503":
                    logging.warning(response.text)
                    continue
                if not response.text.strip():
                    logging.warning("返回代理为空")
            except Exception as _:
                continue
            finally:
                if response is not None:
                    response.close()
        return result

    @staticmethod
    def get_proxy():
        """
        从接口获取代理
        """
        proxies = None
        if Proxy.proxy_url:
            # if re.search(r'(\d+\.\d+\.\d+\.\d+:\d+)', site_data['proxy']):
            #     proxy = 'http://' + \
            #         re.search(r'(\d+\.\d+\.\d+\.\d+:\d+)',
            #                   site_data['proxy']).group(1)
            #     proxies = {"http": proxy, "https": proxy}
            # else:
            proxies = Proxy.get_api(Proxy.proxy_url)
            if not proxies:
                raise Exception('failed to get proxies')
            Proxy.proxies = proxies

        return proxies

    @staticmethod
    def set_proxy_url(proxy_url):
        """
        固定代理链接
        """
        Proxy.proxy_url = proxy_url
