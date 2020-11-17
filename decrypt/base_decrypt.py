from abc import ABCMeta, abstractmethod


class BaseDecrypt(metaclass=ABCMeta):

    @abstractmethod
    def decrypt(self, resp: str) -> str:
        """
        接受一个带解密的字符串
        返回一个解密完成的json字符串
        """
        pass
