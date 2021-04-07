# -*- coding: utf-8 -*-
"""
    :time: 2021/4/7 9:32
    :author: Harumonia
    :url: http://harumonia.moe
    :project: Mori
    :file: rich_tools.py
    :copyright: © 2021 harumonia<zxjlm233@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from functools import wraps

from rich.progress import Progress


def diy_rich_progress(func):
    """
    Decorator of rich`s progress.

    It`s aim to decouple, but the effect is not ideal.
    Args:
        func:

    Returns:

    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        wrapper
        Args:
            *args: like mori
            **kwargs:

        Returns:

        """
        console = kwargs.pop("console")
        if console:
            with Progress(console=console, auto_refresh=False) as progress:
                results = func(progress, *args, **kwargs)
        else:
            results = func(None, *args, **kwargs)
        return results

    return wrapper
