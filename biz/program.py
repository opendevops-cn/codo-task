#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
Author : shenshuo
date   : 2017/7/11 下午1:21
role   : 执行任务
"""


from biz.exec_sched import DealMQ


class Application(DealMQ):
    def __init__(self, **settings):
        super(Application, self).__init__(**settings)

    def start_server(self):
        self.start_consuming()

if __name__ == '__main__':
    app = Application()
    app.start_server()