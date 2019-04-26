#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2018/10/26
Desc    : 订阅redis的消息，写入数据库
"""
import json
from websdk.configs import configs
from websdk.db_context import DBContext
from websdk.cache_context import cache_conn
from models.scheduler import TaskLog


class RedisSubscriber:
    """
    Redis频道订阅类
    """

    def __init__(self, channel='task_log', **settings):
        if configs.can_import:
            configs.import_dict(**settings)
        self.redis_conn = cache_conn()
        self.channel = channel  # 定义频道名称
        self.__settings = settings

    def start_server(self):
        pub = self.redis_conn.pubsub()
        pub.subscribe(self.channel)
        try:
            with DBContext('w', None, True, **self.__settings) as session:
                for item in pub.listen():
                    if item['type'] == 'message':
                        result = item['data'].decode('utf8')
                        data = json.loads(result)
                        print(data.get('log_key'), data.get('exec_time'), data.get('result'))
                        # log_info = data.get('result')[0:480]
                        log_info = data.get('result')
                        task_level = data.get('log_key').split('_')[2]
                        session.add(TaskLog(log_key=data.get('log_key'), task_level=task_level, log_info=log_info,
                                            exec_time=data.get('exec_time')))
                        session.commit()
                    if item['data'] == 'over':
                        break
            pub.unsubscribe('spub')

        except KeyboardInterrupt:
            pub.unsubscribe('spub')
