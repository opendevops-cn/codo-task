#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2019年6月28日
Desc    : 扩展GIT功能
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Text,DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper

Base = declarative_base()


def model_to_dict(model):
    model_dict = {}
    for key, column in class_mapper(model.__class__).c.items():
        model_dict[column.name] = getattr(model, key, None)
    return model_dict


class GitGroup(Base):
    __tablename__ = 'task_git_group'

    ### GIT 组
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    git_url = Column('git_url', String(120))  ###
    group_id = Column('group_id', Integer)  ###  id
    group_name = Column('group_name', String(150))  ###  组名称
    user_list = Column('user_list', String(255))  ###  关联用户，不关心用户的权限
    description = Column('description', String(255))  ### 描述、备注


class GitUsers(Base):
    __tablename__ = 'task_git_users'

    ### git 用户
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    git_url = Column('git_url', String(120))  ###
    co_user_id = Column('co_user_id', Integer)
    user_id = Column('user_id', Integer)  ###  id
    name = Column('name', String(120))  ###  名字
    username = Column('username', String(120))  ### 用户名
    email = Column('email', String(120))  # 邮箱
    state = Column('state', String(30))  # 状态


class GitRepo(Base):
    __tablename__ = 'task_git_repo'

    ### GIT 项目地址  关联代码仓库
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    git_url = Column('git_url', String(120))  ###
    group_id = Column('group_id', Integer)  ###  id
    group_name = Column('group_name', String(150))  ###  组名称
    project_id = Column('project_id', Integer)  ###  id
    project_name = Column('project_name', String(150))  ### 名称
    relative_path = Column('relative_path', String(150))  ### 相对路径
    ssh_url_to_repo = Column('ssh_url_to_repo', String(255), unique=True)  ### 仓库地址
    http_url_to_repo = Column('http_url_to_repo', String(255), unique=True)  ### 仓库地址
    git_hooks = Column('git_hooks', Text())  ###  钩子
    user_info = Column('user_info', Text())  ### 用户相关
    # description = Column('description', String(255))  ### 描述、备注


class GitConf(Base):
    __tablename__ = 'task_git_conf'

    ### git 配置信息
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    git_url = Column('git_url', String(120), unique=True)  ###
    private_token = Column('private_token', String(120))  ###  密钥
    api_version = Column('api_version', String(10))  ### API版本
    deploy_key = Column('deploy_key', Text())  ### 部署key


class HooksLog(Base):
    __tablename__ = 'task_git_hooks_log'

    ### 钩子日志
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    git_url = Column('git_url', String(120))  ###
    relative_path = Column('relative_path', String(150))  ###
    logs_info = Column('logs_info', String(255))  ###
    create_time = Column('create_time', DateTime(), default=datetime.now)  ### 创建时间
