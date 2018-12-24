#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
Author : shenshuo
date   : 2017-10-11
role   : Application
"""

import tornado
from websdk.application import Application as myApplication
from biz.handlers.templet_handler import temp_urls
from biz.handlers.task_handler import task_list_urls
from biz.handlers.accept_task import accept_task_urls
from biz.handlers.job_log_handler import task_log_urls
from biz.handlers.job_log_handler import tail_data
from biz.handlers.other_handler import other_urls


class Application(myApplication):
    def __init__(self, **settings):
        urls = []
        urls.extend(temp_urls)
        urls.extend(task_list_urls)
        urls.extend(accept_task_urls)
        urls.extend(task_log_urls)
        urls.extend(other_urls)
        tailed_callback = tornado.ioloop.PeriodicCallback(tail_data, 500)
        tailed_callback.start()
        super(Application, self).__init__(urls, **settings)


if __name__ == '__main__':
    pass
