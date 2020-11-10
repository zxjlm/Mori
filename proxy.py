import time
import requests
from config import CONFIG_PROXY_SERVICE
import logging


class Proxy:

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
                    break
                if str(status) == "400" or str(status) == "503":
                    logging.warning(response.text)
                    continue
                if not response.text.strip():
                    logging.warning("返回代理为空")
            except:
                continue
            finally:
                if response is not None:
                    response.close()
        return result

    @staticmethod
    def get_proxy(site_data):
        proxies = None
        if site_data.get('proxy'):
            # if re.search(r'(\d+\.\d+\.\d+\.\d+:\d+)', site_data['proxy']):
            #     proxy = 'http://' + \
            #         re.search(r'(\d+\.\d+\.\d+\.\d+:\d+)',
            #                   site_data['proxy']).group(1)
            #     proxies = {"http": proxy, "https": proxy}
            # else:
            proxies = Proxy.get_api(site_data['proxy'])
            if not proxies:
                raise Exception('failed to get proxies')

        return proxies
