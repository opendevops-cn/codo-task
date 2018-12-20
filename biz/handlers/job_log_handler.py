#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2018/11/26
Desc    : 
"""

import tornado.websocket
from websdk.db_context import DBContext
from models.scheduler import TaskLog, model_to_dict

LISTENERS = {}


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
                log_info = session.query(TaskLog).filter(TaskLog.log_key == key).order_by(
                    TaskLog.log_time).all()
                for msg in log_info:
                    data_dict = model_to_dict(msg)
                    log_list.append("{}： {}".format(str(data_dict.get('log_time')), data_dict.get('log_info')))

                for el in ele_list:
                    el.write_message('----'.join(log_list))

            else:
                LISTENERS.pop(key)


task_log_urls = [
    (r"/v2/task/ws_log/", WebSocketHandler),
]

if __name__ == "__main__":
    pass
