#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2018/11/20
Desc    : 
"""
import redis

redis_pool = redis.ConnectionPool(host= '127.0.0.1',
                                  port= 6379,
                                  db=8,
                                  password='123456')
# self.redis_con = redis.Redis(connection_pool=redis_pool)
r = redis.StrictRedis(connection_pool=redis_pool)
r.hmset('hash1',{'k2':'v2', 'k3':'v3'})
print(r.hmget('hash1', ['k2', 'k3', 'test1']))

# redis_pool = redis.ConnectionPool(host=redis_conf.get(const.RD_HOST_KEY, '127.0.0.1'),
#                                   port=int(redis_conf.get(const.RD_PORT_KEY, 6379)),
#                                   db=int(redis_conf.get(const.RD_DB_KEY, 0)),
#                                   password=redis_conf.get(const.RD_PASSWORD_KEY))
# self.redis_conn = redis.StrictRedis(connection_pool=redis_pool)