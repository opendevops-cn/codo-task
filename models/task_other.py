#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2018/11/30
Desc    : 其他
"""

from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper
from datetime import datetime

Base = declarative_base()


def model_to_dict(model):
    model_dict = {}
    for key, column in class_mapper(model.__class__).c.items():
        model_dict[column.name] = getattr(model, key, None)
    return model_dict


class TaskCodeRepository(Base):
    __tablename__ = 'task_code_repository'

    ### 代码仓库，可以录入和通过git api 获取
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    app_name = Column('app_name', String(50), unique=True)  ###  名称
    repository = Column('repository', String(300))  ### 仓库地址
    user_info = Column('user_info', String(300))  ### 用户相关
    description = Column('description', String(100))  ### 描述、备注
    create_time = Column('create_time', DateTime(), default=datetime.now)  ### 创建时间


class DockerRegistry(Base):
    __tablename__ = 'task_docker_registry'

    ### 镜像仓库，手动录入相关的项目
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    project_name = Column('project_name',  String(20),unique=True)   ###  docker 仓库项目地址
    registry_url = Column('registry_url', String(100), unique=True)  ### 仓库地址
    user_name = Column('user_name', String(20))         ### 用户账户
    password = Column('password', String(80))           ### 用户密码
    create_time = Column('create_time', DateTime(), default=datetime.now)  ### 创建时间


class TaskPublishConfig(Base):
    __tablename__ = 'task_publish_config'

    ### 普通发布配置
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    publish_name = Column('publish_name', String(50), unique=True)  ###  发布项目的名称
    publish_type = Column('publish_type', String(20))  ### 服务器 存储桶  容器
    repository = Column('repository', String(300))  ### 仓库地址
    build_host = Column('build_host', String(20))  ### 构建主机
    exclude_file = Column('exclude_file', String(200))  ### 排除文件
    temp_name  = Column('temp_name', String(30))  ### 任务模板
    publish_type1 = Column('publish_type1', String(20))  ### 简单  灰度  蓝绿
    publish_path = Column('publish_path', String(35))   ### 发布路径
    publish_hosts = Column('publish_hosts', String(400))  ### 发布主机
    publish_hosts_api = Column('publish_hosts_api', String(120))  ### 发布主机
    bucket_type = Column('bucket_type', String(20))  ### 存储桶信息
    region =  Column('region', String(50))  ### 存储桶信息
    bucket_name =  Column('bucket_name', String(50))  ### 存储桶信息
    bucket_path =  Column('bucket_path', String(60))  ### 存储的路径
    SecretID =  Column('SecretID', String(60))  ###
    SecretKey =  Column('SecretKey', String(120))  ###
    docker_registry  = Column('docker_registry', String(200))         ### docker 镜像仓库地址
    k8s_api   = Column('k8s_api', String(200))            ### K8S API地址
    namespace = Column('namespace', String(80))           ### 命名空间
    mail_to = Column('mail_to', String(500))              ### 任务中邮件发送人
    create_time = Column('create_time', DateTime(), default=datetime.now)  ### 创建时间