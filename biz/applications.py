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
from models.scheduler import TempList
from websdk.db_context import DBContext


class Application(myApplication):
    def __init__(self, **settings):
        self.temp_init(**settings)
        urls = []
        urls.extend(temp_urls)
        urls.extend(task_list_urls)
        urls.extend(accept_task_urls)
        super(Application, self).__init__(urls, **settings)

    ### 初始化配置
    def temp_init(self, **settings):
        with DBContext('w', None, True, **settings) as session:
            is_exist = session.query(TempList.temp_id).filter(TempList.temp_id == 200).first()
            if is_exist:
                return

            session.add(TempList(temp_id=200, temp_name='内置命令起始', creator='system'))
            session.add(TempList(temp_name='示例模板0', creator='system'))
            session.add(TempList(temp_name='示例模板1', creator='system'))
            session.add(TempList(temp_name='示例模板2', creator='system'))
            session.add(TempList(temp_name='示例模板3', creator='system'))
            session.add(TempList(temp_name='示例模板4', creator='system'))
            session.add(TempList(temp_name='示例模板5', creator='system'))
            session.add(TempList(temp_name='AWS自动部署示例1', creator='system'))
            session.add(TempList(temp_name='OSS发布示例1', creator='system'))
            session.add(TempList(temp_name='S3发布示例1', creator='system'))
            session.add(TempList(temp_name='简单发布示例1', creator='system'))
            session.add(TempList(temp_name='k8s发布示例1', creator='system'))
            session.add(TempList(temp_id=330, temp_name='数据库审核', creator='system'))
            session.add(TempList(temp_id=331, temp_name='数据库优化', creator='system'))
            session.add(TempList(temp_id=332, temp_name='代码检查', creator='system'))
            session.add(TempList(temp_id=500, temp_name='内置命令终止', creator='system'))


if __name__ == '__main__':
    pass
