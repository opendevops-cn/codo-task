#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
Author : shenshuo
date   : 2017年10月17日17:23:19
desc   : task control models
"""

from sqlalchemy import Column, String, Integer, Text, DateTime,BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper
from datetime import datetime

Base = declarative_base()


def model_to_dict(model):
    model_dict = {}
    for key, column in class_mapper(model.__class__).c.items():
        model_dict[column.name] = getattr(model, key, None)
    return model_dict


class TaskList(Base):
    __tablename__ = 'scheduler_task_list'

    ### 任务详情表
    list_id = Column('list_id', Integer, primary_key=True, autoincrement=True)
    task_name = Column('task_name', String(50))  ### 任务名称
    task_type = Column('task_type', String(50))  ### 任务类型
    hosts = Column('hosts', Text())  ### 主机地址
    args = Column('args', Text())  ### 参数
    details = Column('details', Text())  ### 详情
    description = Column('description', Text())  ### 描述、备注
    associated_user = Column('associated_user', String(250), default= "{}")  ### 存放关联用户的信息，可能会比较大
    creator = Column('creator', String(50))  ### 创建者
    executor = Column('executor', String(50))  ### 执行者
    status = Column('status', String(5))  ### 任务状态
    schedule = Column('schedule', String(50))  ### 进度
    temp_id = Column('temp_id', String(12))  ### 模板ID
    create_time = Column('create_time', DateTime(), default=datetime.now)  ### 创建时间
    start_time = Column('start_time', DateTime())  ### 执行时间


class TaskSched(Base):
    __tablename__ = 'scheduler_task_info'

    ### 根据任务表和任务模板表生成此表
    ### 任务根据此表执行
    sched_id = Column('sched_id', Integer, primary_key=True, autoincrement=True)
    list_id = Column('list_id', String(11))
    task_group = Column('task_group', Integer)
    task_level = Column('task_level', Integer)
    task_name = Column('task_name', String(30))
    task_cmd = Column('task_cmd', String(250))
    task_args = Column('task_args', String(250))
    trigger = Column('trigger', String(10))
    exec_user = Column('exec_user', String(30))
    force_host = Column('force_host', String(50))
    exec_ip = Column('exec_ip', String(50))
    task_status = Column('task_status', String(5))


class TaskLog(Base):
    __tablename__ = 'scheduler_task_log'

    ### 任务日志表
    log_id = Column('log_id', Integer, primary_key=True, autoincrement=True)
    log_key =Column('log_key', String(35))
    task_level = Column('task_level', Integer)
    log_info = Column('log_info', Text())
    exec_time = Column('exec_time', BigInteger)
    log_time = Column('log_time', DateTime(), default=datetime.now)


class TaskMonitor(Base):
    __tablename__ = 'task_monitor'

    ### 任务监控
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    list_id = Column('list_id', Integer)
    call_level = Column('call_level', Integer)
    call_info = Column('call_info', String(300))
    call_status = Column('call_status', Integer)
    call_users = Column('call_users', String(500))
    ctime = Column('ctime', DateTime(), default=datetime.now)


class CommandList(Base):
    __tablename__ = 'scheduler_cmd_list'

    ### 命令表
    command_id = Column('command_id', Integer, primary_key=True, autoincrement=True)
    command_name = Column('command_name', String(25), unique=True)
    command = Column('command', String(250))
    args = Column('args', String(250))
    force_host = Column('force_host', String(50))
    creator = Column('creator', String(35))
    create_time = Column('create_time', DateTime(), default=datetime.now)
    update_time = Column('update_time', DateTime(), default=datetime.now, onupdate=datetime.now)

class ArgsList(Base):
    __tablename__ = 'scheduler_args_list'

    ### 参数对照表
    args_id = Column('args_id', Integer, primary_key=True, autoincrement=True)
    args_name = Column('args_name', String(35))
    args_self = Column('args_self', String(50))
    creator = Column('creator', String(40))
    update_time = Column('update_time', DateTime(), default=datetime.now, onupdate=datetime.now)

class TempList(Base):
    __tablename__ = 'scheduler_temp_list'

    ### 命令模板列表
    temp_id = Column('temp_id', Integer, primary_key=True, autoincrement=True)
    temp_name = Column('temp_name', String(30), unique=True)
    creator = Column('creator', String(35))
    create_time = Column('create_time', DateTime(), default=datetime.now)
    update_time = Column('update_time', DateTime(), default=datetime.now, onupdate=datetime.now)


class TempDetails(Base):
    __tablename__ = 'scheduler_temp_details'

    ### 执行模板详情
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    temp_id = Column('temp_id', String(11))
    group = Column('group', Integer)
    level = Column('level', Integer)
    command_name = Column('command_name', String(25))
    command = Column('command', String(250))
    args = Column('args', String(250))
    trigger = Column('trigger', String(10))
    exec_user = Column('exec_user', String(20))
    force_host = Column('force_host', String(50))
    creator = Column('creator', String(35))
    update_time = Column('update_time', DateTime(), default=datetime.now, onupdate=datetime.now)

class TempToUser(Base):
    __tablename__ = 'scheduler_temp_user'

    ### 模板关联用户
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    temp_id = Column('temp_id', Integer)
    user_id = Column('user_id', Integer)
    nickname = Column('nickname',  String(35))

class ExecuteUser(Base):
    __tablename__ = 'scheduler_execute_user'

    ### 执行用户
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    alias_user = Column('alias_user', String(80), unique=True,nullable=False)
    exec_user = Column('exec_user', String(35), default='root')
    ssh_port = Column('ssh_port', Integer, default=22)
    password = Column('password', String(100))
    user_key = Column('user_key',  Text())
    remarks = Column('remarks', String(150))
    update_time = Column('update_time', DateTime(), default=datetime.now, onupdate=datetime.now)

if __name__ == '__main__':
    pass
