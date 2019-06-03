#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2018/11/30
Desc    : 其他扩展功能
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
    registry_url = Column('registry_url', String(150), unique=True)  ### 仓库地址
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
    config_file = Column('config_file', String(500))    ### 配置文件
    publish_hosts = Column('publish_hosts', String(400))  ### 发布主机
    publish_hosts_api = Column('publish_hosts_api', String(120))  ### 发布主机
    tag_name = Column('tag_name', String(35))  ###  关联标签
    bucket_type = Column('bucket_type', String(20))  ### 存储桶信息
    region =  Column('region', String(50))  ### 存储桶信息
    bucket_name =  Column('bucket_name', String(50))  ### 存储桶信息
    bucket_path =  Column('bucket_path', String(60))  ### 存储的路径
    SecretID =  Column('SecretID', String(60))  ###
    SecretKey =  Column('SecretKey', String(120))  ###
    docker_registry  = Column('docker_registry', String(200))         ### docker 镜像仓库地址
    k8s_api   = Column('k8s_api', String(200))                ### K8S API地址
    k8s_host = Column('k8s_host', String(30))                 ### K8S master地址
    namespace = Column('namespace', String(80))               ### 命名空间
    mail_to = Column('mail_to', String(500))                  ### 任务中邮件发送人
    create_time = Column('create_time', DateTime(), default=datetime.now)  ### 创建时间


class Tag(Base):
    __tablename__ = 'asset_tag'

    ### 标签  通过标签来定义主机组 和DB集群
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column('tag_name', String(35), unique=True, nullable=False)
    users = Column('users', String(1000))  ### 用户
    proxy_host = Column('proxy_host', String(35))  ### 代理主机 适配多云
    create_time = Column('create_time', DateTime(), default=datetime.now, onupdate=datetime.now)

class DBTag(Base):
    __tablename__ = 'asset_db_tag'

    id = Column(Integer, primary_key=True, autoincrement=True)
    db_id = Column('db_id', Integer)
    tag_id = Column('tag_id', Integer)


class ServerTag(Base):
    __tablename__ = 'asset_server_tag'

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column('server_id', Integer)
    tag_id = Column('tag_id', Integer)

class DB(Base):
    __tablename__ = 'asset_db'
    ### 数据库集群
    id = Column(Integer, primary_key=True, autoincrement=True)
    db_code = Column('db_code', String(50))  ### 名称 代号 编码
    db_host = Column('db_host', String(80), nullable=False)
    db_port = Column('db_port', String(5), nullable=False, default=3306)
    db_user = Column('db_user', String(20), nullable=False,default='root')
    db_pwd = Column('db_pwd', String(30),nullable=False)
    db_env = Column('db_env', String(10), nullable=False,default='写')
    proxy_host = Column('proxy_host', String(35))  ### 代理主机 适配多云
    db_type = Column('db_type', String(10))  ### 标记类型
    db_mark = Column('db_mark', String(10))  ### 标记读写备
    db_detail = Column('db_detail', String(30))
    all_dbs = Column('all_dbs', String(300))  ### 所有的数据库
    state = Column('state', String(15))
    create_time = Column('create_time', DateTime(), default=datetime.now, onupdate=datetime.now)


class Server(Base):
    __tablename__ = 'asset_server'

    ### 服务器
    id = Column(Integer, primary_key=True, autoincrement=True)
    hostname = Column('hostname', String(100), unique=True,nullable=False)
    ip = Column('ip', String(20))
    idc = Column('idc', String(25))
    region = Column('region', String(25))
    state = Column('state', String(15))
    detail = Column('detail', String(20))
    create_time = Column('create_time', DateTime(), default=datetime.now, onupdate=datetime.now)


class ProxyInfo(Base):
    __tablename__ = 'asset_proxy_info'

    ### 代理主机  通过此主机来连接数据库
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    proxy_host = Column('proxy_host', String(100),unique=True, nullable=False)
    inception = Column('inception', String(300))
    salt = Column('salt', String(300))
    detail = Column('detail', String(20))