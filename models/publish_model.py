#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2019/7/19
Desc    : 项目发布
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper

Base = declarative_base()


def model_to_dict(model):
    model_dict = {}
    for key, column in class_mapper(model.__class__).c.items():
        model_dict[column.name] = getattr(model, key, None)
    return model_dict


class PublishList(Base):
    __tablename__ = 'task_publish_list'

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    project_name = Column('project_name', String(255), nullable=False)  ###
    pm = Column('pm', String(200))  ###
    developers = Column('developers', String(255))  ###
    tester = Column('tester', String(255))  ###
    dba = Column('dba', String(200))  ###
    other_user = Column('other_user', String(255))  ###
    # user_data = Column('user_data', Text())  ###
    run_env = Column('run_env', String(25))  ###当前环境
    step_info = Column('step_info', Text())  ### 项目进度详情
    task_info = Column('task_info', Text())  ###  关联代码仓库以及其他信息
    repo_info = Column('repo_info', Text())  ###  关联代码仓库以及其他信息
    # sql_info =  Column('sql_info', Text())  ###  数据库语句
    real_publish = Column('real_publish', Text())  ###  发布使用的信息，包含仓库 标签，数据库语句
    description = Column('description', String(255))  ### 描述、备注
    create_time = Column('create_time', DateTime(), default=datetime.now)  ### 创建时间
    start_time = Column('start_time', DateTime())  ### 上线时间


class PublishLog(Base):
    __tablename__ = 'task_publish_log'

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    project_id = Column('project_id', Integer, nullable=False, index=True)  ###
    log_info = Column('log_info', String(255))  ###
