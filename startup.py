#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
author : shenshuo
date   : 2018年11月7日
role   : 启动程序
"""

import fire
from tornado.options import define
from websdk.program import MainProgram
from settings import settings as app_settings
from biz.applications import Application as TaskApp
from biz.program import Application as DealApp
from biz.subscribe import RedisSubscriber as SubApp

define("service", default='api', help="start service flag", type=str)


class MyProgram(MainProgram):
    def __init__(self, service='task_api', progress_id=''):
        self.__app = None
        settings = app_settings
        if service == 'task_api':
            self.__app = TaskApp(**settings)
        elif service == 'exec_task':
            self.__app = DealApp(**settings)
        elif service == 'daily_record':
            self.__app = SubApp(**settings)
        super(MyProgram, self).__init__(progress_id)
        self.__app.start_server()


if __name__ == '__main__':
    fire.Fire(MyProgram)
