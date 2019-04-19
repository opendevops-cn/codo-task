#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
Author : shenshuo
date   : 2019-03-19
role   : Application 报警
"""

import tornado
from websdk.application import Application as myApplication
from .alert_tasks import send_alarm


class Application(myApplication):
    def __init__(self, **settings):
        urls = []
        alert_callback = tornado.ioloop.PeriodicCallback(send_alarm, 120000)
        alert_callback.start()
        super(Application, self).__init__(urls, **settings)


if __name__ == '__main__':
    pass
