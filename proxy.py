"""
@project : Mori
@author  : harumonia
@mail   : zxjlm233@gmail.com
@ide    : PyCharm
@time   : 2020-11-17 19:23:27
@description: None
"""
import requests
import logging


class Proxy:
    """
    handle proxy
    """

    proxy_url = ""
    proxies = None
    strict_proxy = None
    use_proxy = False
    headers = {}

    @staticmethod
    def test_api(proxies):
        headers = (
            Proxy.headers
            if Proxy.strict_proxy
            else {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; "
                "rv:55.0) Gecko/20100101 Firefox/55.0",
            }
        )

        url = Proxy.strict_proxy if Proxy.strict_proxy else "https://www.baidu.com/"
        if url == "skip":
            return True
        resp = requests.get(url, proxies=proxies, timeout=15, headers=headers)
        return resp and resp.status_code == 200

    @staticmethod
    def get_api(api_addr: str) -> dict:
        """
        get proxy from api.
        api return format -- "http://*.*.*.*:*"
        Args:s
            api_addr: it should be define in json file.use "proxy" key,
            more info can be found in README.md.

        Returns:
            dictionary -- {"http":"http://*.*.*.*:*",
                            "https":"https://*.*.*.*:*"}
        """
        for _ in range(0, 5):
            try:
                response = requests.get(api_addr, timeout=10)
                status = response.status_code
                if str(status) == "200" and response.text.strip():
                    ip_addr = response.text.strip()
                    result = {
                        "https": ip_addr.replace("http", "https"),
                        "http": ip_addr,
                    }
                    if Proxy.test_api(result):
                        return result
                if str(status) == "400" or str(status) == "503":
                    logging.warning(response.text)
                    continue
                if not response.text.strip():
                    # logging.warning("返回代理为空")
                    ...
            except Exception as _e:
                logging.info(_e)
                continue

    @staticmethod
    def get_proxy():
        """s
        get_proxy. pay attention to the static members of this class.
        Returns:

        """
        proxies = None
        if Proxy.proxy_url and Proxy.use_proxy:
            # if re.search(r'(\d+\.\d+\.\d+\.\d+:\d+)', site_data['proxy']):
            #     proxy = 'http://' + \
            #         re.search(r'(\d+\.\d+\.\d+\.\d+:\d+)',
            #                   site_data['proxy']).group(1)
            #     proxies = {"http": proxy, "https": proxy}
            # else:
            proxies = Proxy.get_api(Proxy.proxy_url)
            if not proxies:
                raise Exception("failed to get proxies")
            Proxy.proxies = proxies

        return proxies

    @staticmethod
    def set_proxy_url(proxy_url, strict_proxy, use_proxy, headers):
        """
        like __init__()
        Args:
            proxy_url:
            strict_proxy:
            use_proxy:
            headers:

        Returns:

        """
        Proxy.proxy_url = proxy_url
        Proxy.strict_proxy = strict_proxy
        Proxy.use_proxy = use_proxy
        Proxy.headers = headers
