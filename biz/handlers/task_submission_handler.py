#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2019/3/20
Desc    : 
"""

import base64
import datetime
import json
from .task_accept import create_task as acc_create_task
from libs.base_handler import BaseHandler
from models.task_other import DB, DBTag, Tag, ServerTag, Server, ProxyInfo, TaskPublishConfig, model_to_dict
from models.git_model import GitRepo
from models.scheduler import TempList, TempDetails
from websdk.db_context import DBContext


class PublishAppHandler(BaseHandler):
    async def get(self, *args, **kwargs):
        publish_name = self.get_argument('publish_name', default=None, strip=True)
        username = self.get_current_user()
        publish_app_list = []
        host_list = []

        if publish_name:
            ### 选中发布
            all_host_info = {}
            with DBContext('r') as session:
                app_info = session.query(TaskPublishConfig).filter(TaskPublishConfig.publish_name == publish_name).all()

            for msg in app_info:
                data_dict = model_to_dict(msg)
                need_data = dict(repository=data_dict.get('repository'), build_host=data_dict.get('build_host'),
                                 temp_name=data_dict.get('temp_name'))

                tag_name = data_dict.get('tag_name')
                if tag_name:
                    server_info = session.query(Server).outerjoin(ServerTag, Server.id == ServerTag.server_id
                                                                  ).outerjoin(Tag, Tag.id == ServerTag.tag_id).filter(
                        Tag.tag_name == tag_name).all()

                    for s in server_info:
                        server_dict = model_to_dict(s)
                        all_host_info[str(server_dict['hostname'])] = server_dict['ip']
                        host_list.append(server_dict['hostname'])

                    need_data['all_host_info'] = all_host_info
                    need_data['host_list'] = host_list

                else:
                    if data_dict.get('publish_type') == 'server':
                        return self.write(dict(code=-1, msg='请注意，当前应用没有配置标签'))

                return self.write(dict(code=0, msg='获取详细成功', data=need_data))

        else:
            with DBContext('r') as session:
                publish_info = session.query(TaskPublishConfig.publish_name, GitRepo.user_info).outerjoin(
                    GitRepo, TaskPublishConfig.repository == GitRepo.ssh_url_to_repo).order_by(
                    TaskPublishConfig.id).all()
            for msg in publish_info:
                if self.is_superuser:
                    publish_app_list.append(msg[0])
                elif msg[1] and username in msg[1].split(','):
                    for u in msg[1].split(','):
                        if username == u.split("@")[0]:
                            publish_app_list.append(msg[0])
            return self.write(dict(code=0, msg='获取成功', data=publish_app_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        custom = data.get('custom')

        publish_name = data.get('publish_name', None)
        publish_tag = data.get('publish_tag', None)
        host_list = data.get('host_list', None)
        start_time = data.get('start_time', None)
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=8)

        args_dict = {}

        if custom:
            if custom.get('custom_key') and custom.get('custom_value'):
                args_dict[custom.get('custom_key')] = custom.get('custom_value')

        if not publish_name or not publish_tag or not start_time:
            return self.write(dict(code=-1, msg='必填项不能为空'))

        with DBContext('r') as session:
            conf_info = session.query(TaskPublishConfig).filter(TaskPublishConfig.publish_name == publish_name).first()
            temp_id = session.query(TempList.temp_id).filter(TempList.temp_name == conf_info.temp_name).first()

            if not temp_id:
                return self.write(dict(code=-1, msg='关联的任务模板有误，快去检查！'))
            else:
                temp_id = temp_id[0]

            first_group = session.query(TempDetails.group).filter(TempDetails.temp_id == temp_id).order_by(
                TempDetails.group).first()

            if not first_group:
                return self.write(dict(code=-1, msg='关联的任务模板任务组有误，快去检查！'))

            else:
                first_group = first_group[0]

            if host_list:
                server_info = session.query(Server).filter(Server.hostname.in_(host_list)).all()
                server_dict = {}
                for msg in server_info:
                    data_dict = model_to_dict(msg)
                    if data_dict['hostname']:
                        server_dict[data_dict['hostname']] = data_dict['ip']
                args_dict['SERVER_DICT'] = json.dumps(server_dict)

        conf_dict = model_to_dict(conf_info)
        conf_dict.pop('id')
        conf_dict.pop('create_time')
        args_dict['PUBLISH_NAME'] = publish_name
        args_dict['PUBLISH_TAG'] = publish_tag

        for i, j in conf_dict.items():
            if j and not i.startswith('Secret') and not i.startswith('secret'):
                args_dict[i.upper()] = j

        hosts_dict = {first_group: conf_info.build_host}
        data_info = dict(exec_time=start_time, temp_id=temp_id, task_name=publish_name,
                         task_type=conf_info.temp_name,
                         submitter=self.get_current_nickname(), associated_user="", args=str(args_dict),
                         hosts=str(hosts_dict), schedule='new', details='', )

        return_data = acc_create_task(**data_info)
        return self.write(return_data)


### 数据库审核
class MySqlAudit(BaseHandler):
    def get(self, *args, **kwargs):
        value = self.get_argument('value', default=None, strip=True)
        db_list = []
        with DBContext('r') as session:
            db_info = session.query(DB).outerjoin(DBTag, DB.id == DBTag.db_id).outerjoin(Tag, Tag.id == DBTag.tag_id
                                                                                         ).filter(
                Tag.tag_name == str(value), DB.db_type == 'mysql', DB.db_mark == '写')
            proxy_host = session.query(Tag.proxy_host).filter(Tag.tag_name == value).first()[0]

            if not proxy_host:
                return self.write(dict(code=-1, msg='请给选择标签添加代理主机'))

            for msg in db_info:
                data_dict = model_to_dict(msg)
                db_list.append(data_dict['db_code'])

            if len(db_list) == 0:
                return self.write(dict(code=-2, msg='当前标签没有MySQL写库'))

        self.write(dict(code=0, msg='获取成功', data=db_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        tag = data.get('tag', None)
        sql_data = data.get('sql_data', None)
        approver = data.get('approver', None)
        if not tag or not sql_data or not approver:
            return self.write(dict(code=-1, msg='必填项不能为空'))

        db_str = ""
        with DBContext('r') as session:
            temp_info = session.query(TempList).filter(TempList.temp_id == 330).first()
            if not temp_info:
                return self.write(dict(code=-2, msg='关联的任务模板有误，快去检查！'))

            db_info = session.query(DB).outerjoin(DBTag, DB.id == DBTag.db_id).outerjoin(Tag, Tag.id == DBTag.tag_id
                                                                                         ).filter(
                Tag.tag_name == str(tag), DB.db_type == 'mysql', DB.db_mark == '写')
            proxy_host = session.query(Tag.proxy_host).filter(Tag.tag_name == tag).first()[0]
            inception_info = session.query(ProxyInfo.inception).filter(ProxyInfo.proxy_host == proxy_host).first()[0]

        for msg in db_info:
            data_dict = model_to_dict(msg)
            data_dict.pop('create_time')
            data_dict.pop('db_detail')
            base64.b64encode(str(data_dict).encode('utf-8'))
            if db_str:
                db_str = db_str + ",,," + json.dumps(data_dict)
            else:
                db_str = json.dumps(data_dict)
        db_str = str(base64.b64encode(db_str.encode('utf-8')), encoding="utf8")
        inception_info = str(base64.b64encode(str(inception_info).encode('utf-8')), encoding="utf8")
        sql_data = str(base64.b64encode(sql_data.encode('utf-8')), encoding="utf8")

        args_dict = dict(MYSQLINFO=db_str, SQL_DATA=sql_data, INCEPTION=inception_info)
        hosts_dict = {1: proxy_host}
        data_info = dict(exec_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), temp_id=330,
                         task_name='MySQL', task_type='数据库审核', submitter=self.get_current_nickname(), executor=approver,
                         associated_user="", args=str(args_dict), hosts=str(hosts_dict), schedule='new', details='')

        return_data = acc_create_task(**data_info)
        return self.write(return_data)


class MySQLOptimization(BaseHandler):
    def get(self, *args, **kwargs):
        value = self.get_argument('value', default=None, strip=True)
        db_list = []
        with DBContext('r') as session:
            db_info = session.query(DB).outerjoin(DBTag, DB.id == DBTag.db_id).outerjoin(Tag, Tag.id == DBTag.tag_id
                                                                                         ).filter(
                Tag.tag_name == str(value), DB.db_type == 'mysql').all()
            proxy_host = session.query(Tag.proxy_host).filter(Tag.tag_name == value).first()[0]

            if not proxy_host:
                return self.write(dict(code=-1, msg='请给选择标签添加代理主机'))

            for msg in db_info:
                data_dict = model_to_dict(msg)
                db_list.append(data_dict['db_code'])
            ### 这里需要获取库 未完成

            if len(db_list) == 0:
                return self.write(dict(code=-2, msg='当前标签下没有MySQL库'))

        self.write(dict(code=0, msg='获取成功', data=db_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        tag = data.get('tag', None)
        sql_data = data.get('sql_data', None)
        db_name = data.get('db_name', None)
        db_code = data.get('db_code', None)
        the_way = data.get('the_way', None)
        db_str = ''

        if not tag or not sql_data or not db_name or not db_code:
            return self.write(dict(code=-1, msg='必填项不能为空'))

        with DBContext('r') as session:
            db_info = session.query(DB).filter(DB.db_code == db_code).all()
            proxy_host = session.query(Tag.proxy_host).filter(Tag.tag_name == tag).first()[0]

            temp_info = session.query(TempList).filter(TempList.temp_id == 331).first()

        if not temp_info:
            return self.write(dict(code=-2, msg='关联的任务模板有误，快去检查！'))

        for msg in db_info:
            data_dict = model_to_dict(msg)
            data_dict.pop('create_time')
            data_dict.pop('db_detail')
            db_str = str(base64.b64encode(json.dumps(data_dict).encode('utf-8')), encoding="utf8")

        sql_data = str(base64.b64encode(sql_data.encode('utf-8')), encoding="utf8")

        args_dict = dict(MYSQLINFO=db_str, DB_NAME=db_name, SQL_DATA=sql_data, THE_WAY=the_way)
        hosts_dict = {1: proxy_host}
        data_info = dict(exec_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), temp_id=331,
                         task_name='MySQL', task_type='数据库优化', submitter=self.get_current_nickname(),
                         associated_user="", args=str(args_dict), hosts=str(hosts_dict), schedule='ready', details='')
        return_data = acc_create_task(**data_info)

        data = dict(list_id=return_data['list_id'], task_group=1, task_level=1, exec_ip=proxy_host)
        return_data['data'] = data
        return self.write(return_data)


class CustomTask(BaseHandler):
    def get(self, *args, **kwargs):
        value = self.get_argument('value', default=None, strip=True)
        server_list = []
        with DBContext('r') as session:
            server_info = session.query(Server).outerjoin(ServerTag, Server.id == ServerTag.server_id).outerjoin(
                Tag, Tag.id == ServerTag.tag_id).filter(Tag.tag_name == str(value))

        for msg in server_info:
            data_dict = model_to_dict(msg)
            data_dict.pop('create_time')
            server_list.append(data_dict['hostname'])

        self.write(dict(code=0, msg='获取成功', data=server_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        tag = data.get('tag', None)
        temp_id = data.get('temp_id', None)
        hostnames = data.get('hostnames', None)
        args_items = data.get('args_items', None)
        start_time = data.get('start_time', None)
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=8)
        if not tag or not start_time or not temp_id:
            return self.write(dict(code=-1, msg='必填项不能为空'))

        if len(hostnames) == 0:
            return self.write(dict(code=-2, msg='必须有主机才行啊'))

        if len(hostnames) > 100:
            return self.write(dict(code=-3, msg='并发主机不能超过100'))

        args_dict = {}
        if args_items:
            for i in args_items:
                if i['status'] == 1:
                    args_dict[str(i['key'])] = i['value']

        server_ip_list = []
        with DBContext('r') as session:
            server_info = session.query(Server.ip).filter(Server.hostname.in_(hostnames))
            first_group = session.query(TempDetails.group).filter(TempDetails.temp_id == temp_id).order_by(
                TempDetails.group).first()[0]

        if not first_group:
            return self.write(dict(code=-4, msg='当前模板配置有误-{}'.format(temp_id)))

        for msg in server_info:
            server_ip_list.append(msg[0])

        hosts_dict = {first_group: ','.join(server_ip_list)}
        data_info = dict(exec_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), temp_id=temp_id,
                         task_name='自定义任务', submitter=self.get_current_nickname(),
                         associated_user="", args=str(args_dict), hosts=str(hosts_dict), schedule='new', details='')

        return_data = acc_create_task(**data_info)
        return self.write(return_data)


class CustomTaskProxy(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        tag_list = json.loads(key)['tag_list']
        if len(tag_list) == 0:
            return self.write(dict(code=-1, msg='请至少选中一个标签'))

        server_list = []
        proxy_list = []
        with DBContext('r') as session:
            server_info = session.query(Server).outerjoin(ServerTag, Server.id == ServerTag.server_id).outerjoin(
                Tag, Tag.id == ServerTag.tag_id).filter(Tag.tag_name.in_(tag_list))

            proxy_host = session.query(Tag.proxy_host).filter(Tag.tag_name.in_(tag_list)).all()

        for p in proxy_host:
            proxy_list.append(p[0])
        if not proxy_host:
            return self.write(dict(code=-1, msg='请给选择标签添加代理主机'))

        for msg in server_info:
            data_dict = model_to_dict(msg)
            data_dict.pop('create_time')
            server_list.append(data_dict['hostname'])

        self.write(dict(code=0, msg='获取成功', data=dict(server_list=server_list, proxy_list=list(set(proxy_list)))))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        tag = data.get('tag', None)
        temp_id = data.get('temp_id', None)
        hostnames = data.get('hostnames', None)
        proxy_list = data.get('proxy_list', None)
        args_items = data.get('args_items', None)
        start_time = data.get('start_time', None)
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=8)
        if not tag or not start_time or not temp_id:
            return self.write(dict(code=-1, msg='必填项不能为空'))

        if len(hostnames) == 0:
            return self.write(dict(code=-2, msg='必须有主机才行啊'))

        if len(proxy_list) != 1:
            return self.write(dict(code=-2, msg='代理主机选择错误，有且只能有一个'))

        proxy_host = proxy_list[0]
        if len(hostnames) > 100:
            return self.write(dict(code=-3, msg='并发主机不能超过100'))

        args_dict = {}
        if args_items:
            for i in args_items:
                if i['status'] == 1:
                    args_dict[str(i['key'])] = i['value']

        server_ip_list = []
        with DBContext('r') as session:
            server_info = session.query(Server.ip).filter(Server.hostname.in_(hostnames))
            first_group = session.query(TempDetails.group).filter(TempDetails.temp_id == temp_id).order_by(
                TempDetails.group).first()[0]

        if not first_group:
            return self.write(dict(code=-4, msg='当前模板配置有误-{}'.format(temp_id)))

        for msg in server_info:
            server_ip_list.append(msg[0])

        args_dict['SERVER_IP'] = ','.join(server_ip_list)
        args_dict['SERVER_HOST'] = ','.join(hostnames)

        hosts_dict = {first_group: proxy_host}
        data_info = dict(exec_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), temp_id=temp_id,
                         task_name='自定义任务-代理', submitter=self.get_current_nickname(),
                         associated_user="", args=str(args_dict), hosts=str(hosts_dict), schedule='new', details='')

        return_data = acc_create_task(**data_info)
        return self.write(return_data)


class PostTaskHandler(BaseHandler):
    def get(self, *args, **kwargs):
        value = self.get_argument('value', default=None, strip=True)
        server_list = []
        with DBContext('r') as session:
            server_info = session.query(Server).outerjoin(ServerTag, Server.id == ServerTag.server_id).outerjoin(
                Tag, Tag.id == ServerTag.tag_id).filter(Tag.tag_name == str(value))

            for msg in server_info:
                data_dict = model_to_dict(msg)
                data_dict.pop('create_time')
                server_list.append(data_dict)

        self.write(dict(code=0, msg='获取成功', data=server_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        post_data = data.get('post_data', None)
        start_time = data.get('start_time', None)
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=8)

        if not post_data or not start_time:
            return self.write(dict(code=-1, msg='必填项不能为空'))

        try:
            post_data = json.loads(post_data)
            post_data['exec_time'] = start_time
            temp_id = post_data['temp_id']

        except Exception as e:
            return self.write(dict(code=-2, msg=str(e)))

        with DBContext('r') as session:
            temp_info = session.query(TempList).filter(TempList.temp_id == temp_id).first()

            first_group = session.query(TempDetails.group).filter(TempDetails.temp_id == temp_id).order_by(
                TempDetails.group).first()[0]

        if not temp_info:
            return self.write(dict(code=-3, msg='关联的任务模板有误，快去检查！'))

        if not first_group:
            return self.write(dict(code=-4, msg='要确保当前模板已经配置完成'))

        return_data = acc_create_task(**post_data)
        return self.write(return_data)


class AssetPurchase(BaseHandler):

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        temp_name = data.get('temp_name')
        host_env = data.get('host_env')
        tag_list = data.get('tag_list')

        with DBContext('r') as session:
            temp_id = session.query(TempList.temp_id).filter(TempList.temp_name == temp_name).first()
            if not temp_id:
                return self.write(dict(code=-1, msg='关联的任务模板不存在，快去检查！'))
            else:
                temp_id = temp_id[0]

            first_group = session.query(TempDetails.group).filter(TempDetails.temp_id == temp_id).order_by(
                TempDetails.group).first()

            if not first_group:
                return self.write(dict(code=-4, msg='当前模板配置有误-{}'.format(temp_id)))
            else:
                first_group = first_group[0]

        args_dict = data
        if host_env:
            host_env = ','.join(host_env)
            args_dict['host_env'] = host_env
        else:
            args_dict.pop('host_env')

        if tag_list:
            if isinstance(tag_list, list):
                tag_list = ','.join(tag_list)
            args_dict['tag_list'] = tag_list
        else:
            args_dict.pop('tag_list')

        args_dict.pop('temp_name')

        exec_host = args_dict.pop('exec_host')

        hosts_dict = {first_group: exec_host}

        new_dict = {}
        for i, j in args_dict.items():
            new_dict[i.upper()] = j

        data_info = dict(exec_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), temp_id=temp_id,
                         task_name='资源', submitter=self.get_current_nickname(),
                         associated_user="", args=str(new_dict), hosts=str(hosts_dict), schedule='new', details='')
        return_data = acc_create_task(**data_info)
        return self.write(return_data)


class AssetPurchaseAWS(BaseHandler):
    def post(self, *args, **kwargs):
        return self.write(dict(code=-1, msg='此方法暂无'))


class AssetPurchaseALY(BaseHandler):

    def post(self, *args, **kwargs):
        return self.write(dict(code=-1, msg='此方法暂无'))


class AssetPurchaseQCloud(BaseHandler):

    def post(self, *args, **kwargs):
        return self.write(dict(code=-1, msg='此方法暂无'))


opt_info_urls = [
    (r"/other/v1/submission/publish/", PublishAppHandler),
    (r"/other/v1/submission/mysql_audit/", MySqlAudit),
    (r"/other/v1/submission/mysql_opt/", MySQLOptimization),
    (r"/other/v1/submission/custom_task/", CustomTask),
    (r"/other/v1/submission/custom_task_proxy/", CustomTaskProxy),
    (r"/other/v1/submission/post_task/", PostTaskHandler),
    (r"/other/v1/submission/purchase_aws/", AssetPurchase),
    (r"/other/v1/submission/purchase_aly/", AssetPurchase),
    (r"/other/v1/submission/purchase_qcloud/", AssetPurchase),
]
if __name__ == "__main__":
    pass
