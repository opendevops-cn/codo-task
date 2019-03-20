#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
Author : shenshuo
date   : 2019-03-19
role   : Application 放一些定时任务 ，可能会导致阻塞
"""

import tornado
from websdk.application import Application as myApplication
from biz.handlers.job_log_handler import tail_data
from .alert_tasks import send_alarm


class Application(myApplication):
    def __init__(self, **settings):
        urls = []
        alert_callback = tornado.ioloop.PeriodicCallback(send_alarm, 60000)
        alert_callback.start()
        tailed_callback = tornado.ioloop.PeriodicCallback(tail_data, 500)
        tailed_callback.start()
        super(Application, self).__init__(urls, **settings)


if __name__ == '__main__':
    pass