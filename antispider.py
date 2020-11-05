from abc import ABCMeta, abstractmethod


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
