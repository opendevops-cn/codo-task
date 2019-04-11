#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
Author : shenshuo
date   : 2017-10-11
role   : Application
"""

from websdk.application import Application as myApplication
from biz.handlers.templet_handler import temp_urls
from biz.handlers.task_handler import task_list_urls
from biz.handlers.task_accept import accept_task_urls


class Application(myApplication):
    def __init__(self, **settings):
        urls = []
        urls.extend(temp_urls)
        urls.extend(task_list_urls)
        urls.extend(accept_task_urls)
        super(Application, self).__init__(urls, **settings)


if __name__ == '__main__':
    pass
