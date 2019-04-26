#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2018/11/26
Desc    : 
"""

import time
import tornado.websocket
from websdk.db_context import DBContext
from models.scheduler import TaskLog, model_to_dict

LISTENERS = {}
LISTENERS_v1 = {}


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        pass

    def on_message(self, message):
        msg_id = message
        try:
            if msg_id in LISTENERS:
                LISTENERS[msg_id]['ele'].append(self)
            else:
                LISTENERS[msg_id] = {'ele': [self]}
        except Exception as e:
            self.write_message(str(e))
        self.msg_id = msg_id

    def on_close(self):
        print("WebSocket closed")
        try:
            LISTENERS[self.msg_id]['ele'].remove(self)
            if not LISTENERS[self.msg_id]['ele']:
                LISTENERS.pop(self.msg_id)
        except Exception as e:
            self.write_message(str(e))

    def check_origin(self, origin):
        return True


def tail_data():
    log_list = []
    with DBContext('r') as session:
        for key in LISTENERS:
            ele_list = LISTENERS[key]['ele']
            if ele_list:
                log_info = session.query(TaskLog).filter(TaskLog.log_key == key).order_by(TaskLog.exec_time).all()
                for msg in log_info:
                    data_dict = model_to_dict(msg)
                    exec_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data_dict.get('exec_time') / 1000))
                    log_list.append("{}： {}".format(str(exec_time), data_dict.get('log_info')))

                for el in ele_list:
                    el.write_message('----'.join(log_list))

            else:
                LISTENERS.pop(key)


class GetLogDataHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        pass

    def on_message(self, message):
        msg_id = message
        try:
            if msg_id in LISTENERS_v1:
                LISTENERS_v1[msg_id]['ele'].append(self)
            else:
                LISTENERS_v1[msg_id] = {'ele': [self]}
        except Exception as e:
            self.write_message(str(e))
        self.msg_id = msg_id

    def on_close(self):
        print("WebSocket closed")
        try:
            LISTENERS_v1[self.msg_id]['ele'].remove(self)
            if not LISTENERS_v1[self.msg_id]['ele']:
                LISTENERS_v1.pop(self.msg_id)
        except Exception as e:
            self.write_message(str(e))

    def check_origin(self, origin):
        return True


def get_log_data():
    log_list1 = []
    with DBContext('r') as session:
        for key in LISTENERS_v1:
            ele_list = LISTENERS_v1[key]['ele']
            if ele_list:
                log_info = session.query(TaskLog).filter(TaskLog.log_key == key).order_by(TaskLog.exec_time).all()
                for msg in log_info:
                    data_dict = model_to_dict(msg)
                    log_list1.append(data_dict.get('log_info'))

                if log_list1:
                    del log_list1[0]
                for el in ele_list:
                    el.write_message('----'.join(log_list1))

            else:
                LISTENERS_v1.pop(key)


task_log_urls = [
    (r"/ws/v1/task/log/", WebSocketHandler),
    (r"/ws/v1/task/log_data/", GetLogDataHandler),
]

if __name__ == "__main__":
    pass
