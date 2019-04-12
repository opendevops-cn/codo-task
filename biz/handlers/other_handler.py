#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2018/11/30
Desc    : 其他
"""

import json
from libs.base_handler import BaseHandler
from websdk.db_context import DBContext
from models.task_other import TaskCodeRepository, DockerRegistry, TaskPublishConfig, model_to_dict


class CodeRepositoryHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        repository_list = []

        with DBContext('r') as session:
            if key and value:
                repository_info = session.query(TaskCodeRepository).filter_by(**{key: value}).all()
            else:
                repository_info = session.query(TaskCodeRepository).order_by(TaskCodeRepository.id).all()

        for msg in repository_info:
            data_dict = model_to_dict(msg)
            data_dict['create_time'] = str(data_dict['create_time'])
            repository_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', data=repository_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        app_name = data.get('app_name', None)
        repository = data.get('repository', None)
        description = data.get('description', None)
        if not app_name or not repository:
            return self.write(dict(code=-1, msg='参数不能为空'))

        with DBContext('r') as session:
            is_exist = session.query(TaskCodeRepository.id).filter(TaskCodeRepository.repository == repository).first()
        if is_exist:
            return self.write(dict(code=-2, msg='不能重复'))

        with DBContext('w', None, True) as session:
            session.add(TaskCodeRepository(app_name=app_name, repository=repository, description=description))

        return self.write(dict(code=0, msg='添加新仓库成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        repository_id = data.get('id')
        repository = data.get('repository')
        description = data.get('description')

        if not repository_id:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(TaskCodeRepository).filter(TaskCodeRepository.id == repository_id).update(
                {TaskCodeRepository.repository: repository, TaskCodeRepository.description: description})
        return self.write(dict(code=0, msg='编辑成功,名称不能修改'))

    def patch(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        repository_id = data.get('repository_id')
        user_info = data.get('new_user_info')

        if not repository_id:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(TaskCodeRepository).filter(TaskCodeRepository.id == repository_id).update(
                {TaskCodeRepository.user_info: user_info})
        return self.write(dict(code=0, msg='关联用户成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        repository_id = data.get('repository_id', None)
        if not repository_id:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(TaskCodeRepository).filter(TaskCodeRepository.id == repository_id).delete(
                synchronize_session=False)

        return self.write(dict(code=0, msg='删除成功'))


class DockerRepositoryHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        repository_list = []

        with DBContext('r') as session:
            if key and value:
                repository_info = session.query(DockerRegistry).filter_by(**{key: value}).all()
            else:
                repository_info = session.query(DockerRegistry).order_by(DockerRegistry.id).all()

        for msg in repository_info:
            data_dict = model_to_dict(msg)
            data_dict['create_time'] = str(data_dict['create_time'])
            repository_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', data=repository_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        project_name = data.get('project_name', None)
        registry_url = data.get('registry_url', None)
        user_name = data.get('user_name', None)
        password = data.get('password', None)
        if not project_name or not registry_url:
            return self.write(dict(code=-1, msg='参数不能为空'))

        with DBContext('r') as session:
            is_exist = session.query(DockerRegistry.id).filter(DockerRegistry.registry_url == registry_url).first()
        if is_exist:
            return self.write(dict(code=-2, msg='不能重复'))

        with DBContext('w', None, True) as session:
            session.add(DockerRegistry(project_name=project_name, registry_url=registry_url, user_name=user_name,
                                       password=password))

        return self.write(dict(code=0, msg='添加新项目成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        repository_id = data.get('repository_id', None)
        if not repository_id:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(DockerRegistry).filter(DockerRegistry.id == repository_id).delete(
                synchronize_session=False)

        return self.write(dict(code=0, msg='删除成功'))


class PublishCDHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        publish_app_list = []

        with DBContext('r') as session:
            if key and value:
                publish_info = session.query(TaskPublishConfig).filter_by(**{key: value}).all()
            else:
                publish_info = session.query(TaskPublishConfig).order_by(TaskPublishConfig.id).all()

        for msg in publish_info:
            data_dict = model_to_dict(msg)
            data_dict['create_time'] = str(data_dict['create_time'])
            publish_app_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', data=publish_app_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        publish_name = data.get('publish_name')
        publish_type = data.get('publish_type')
        build_host = data.get('build_host')
        repository = data.get('repository')
        temp_name = data.get('temp_name')
        exclude_file = data.get('exclude_file', '.git')
        if not publish_name or not publish_type or not build_host or not repository or not temp_name:
            return self.write(dict(code=-1, msg='缺失必要参数'))

        if publish_type not in ["service", "bucket", "container"]:
            return self.write(dict(code=-2, msg='发布类型超出预期'))

        try:
            publish_hosts = data.get('publish_hosts')
            publish_path = data.get('publish_path')
            config_file = data.get('config_file')
            publish_hosts_api = data.get('publish_hosts_api')
            tag_name = data.get('tag_name')
            bucket_type = data.get('bucket_type')
            region = data.get('region')
            bucket_name = data.get('bucket_name')
            bucket_path = data.get('bucket_path')
            SecretID = data.get('SecretID')
            SecretKey = data.get('SecretKey')
            docker_registry = data.get('docker_registry')
            k8s_api = data.get('k8s_api')
            k8s_host = data.get('k8s_host')
            namespace = data.get('namespace')
            mail_to = data.get('mail_to')

            with DBContext('w', None, True) as session:
                session.add(TaskPublishConfig(publish_name=publish_name, publish_type=publish_type,
                                              build_host=build_host, repository=repository, temp_name=temp_name,
                                              exclude_file=exclude_file, publish_hosts=publish_hosts,
                                              publish_path=publish_path, config_file=config_file,
                                              publish_hosts_api=publish_hosts_api, tag_name=tag_name,
                                              bucket_type=bucket_type, region=region, bucket_name=bucket_name,
                                              bucket_path=bucket_path, SecretID=SecretID, SecretKey=SecretKey,
                                              docker_registry=docker_registry, k8s_api=k8s_api, k8s_host=k8s_host,
                                              namespace=namespace, mail_to=mail_to))
            return self.write(dict(code=0, msg='添加新应用成功'))
        except Exception as e:
            print(e)
            return self.write(dict(code=-3, msg="关键信息不能重复，或者格式有误"))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        publish_name = data.get('publish_name')
        publish_type = data.get('publish_type')
        build_host = data.get('build_host')
        repository = data.get('repository')
        temp_name = data.get('temp_name')
        exclude_file = data.get('exclude_file', '.git')
        if not publish_name or not publish_type or not build_host or not repository or not temp_name:
            return self.write(dict(code=-1, msg='缺失必要参数'))

        if publish_type not in ["service", "bucket", "container"]:
            return self.write(dict(code=-2, msg='发布类型超出预期'))

        try:
            publish_hosts = data.get('publish_hosts')
            publish_path = data.get('publish_path')
            config_file = data.get('config_file')
            publish_hosts_api = data.get('publish_hosts_api')
            tag_name = data.get('tag_name')
            bucket_type = data.get('bucket_type')
            region = data.get('region')
            bucket_name = data.get('bucket_name')
            bucket_path = data.get('bucket_path')
            SecretID = data.get('SecretID')
            SecretKey = data.get('SecretKey')
            docker_registry = data.get('docker_registry')
            k8s_api = data.get('k8s_api')
            k8s_host = data.get('k8s_host')
            namespace = data.get('namespace')
            mail_to = data.get('mail_to')

            with DBContext('w', None, True) as session:
                session.query(TaskPublishConfig).filter(TaskPublishConfig.publish_name == publish_name).update(
                    {TaskPublishConfig.publish_type: publish_type, TaskPublishConfig.build_host: build_host,
                     TaskPublishConfig.repository: repository,
                     TaskPublishConfig.temp_name: temp_name,
                     TaskPublishConfig.exclude_file: exclude_file,
                     TaskPublishConfig.publish_hosts: publish_hosts,
                     TaskPublishConfig.publish_path: publish_path,
                     TaskPublishConfig.config_file: config_file,
                     TaskPublishConfig.publish_hosts_api: publish_hosts_api,
                     TaskPublishConfig.tag_name: tag_name,
                     TaskPublishConfig.bucket_type: bucket_type,
                     TaskPublishConfig.region: region,
                     TaskPublishConfig.bucket_name: bucket_name,
                     TaskPublishConfig.bucket_path: bucket_path,
                     TaskPublishConfig.SecretID: SecretID,
                     TaskPublishConfig.SecretKey: SecretKey,
                     TaskPublishConfig.docker_registry: docker_registry,
                     TaskPublishConfig.k8s_api: k8s_api,
                     TaskPublishConfig.k8s_host: k8s_host,
                     TaskPublishConfig.namespace: namespace,
                     TaskPublishConfig.mail_to: mail_to,
                     })
            return self.write(dict(code=0, msg='编辑应用成功'))
        except Exception as e:
            print(e)
            return self.write(dict(code=-3, msg="关键信息不能重复，或者格式有误"))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        publish_app_id = data.get('publish_app_id', None)
        if not publish_app_id:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(TaskPublishConfig).filter(TaskPublishConfig.id == publish_app_id).delete(
                synchronize_session=False)

        return self.write(dict(code=0, msg='删除成功'))


#
# class PublishListHandler(BaseHandler):
#     async def get(self, *args, **kwargs):
#         publish_name = self.get_argument('publish_name', default=None, strip=True)
#         nickname = self.get_current_nickname()
#         publish_app_list = []
#
#         if publish_name:
#             all_host_info = {}
#             with DBContext('r') as session:
#                 app_info = session.query(TaskPublishConfig).filter(TaskPublishConfig.publish_name == publish_name).all()
#
#             for msg in app_info:
#                 data_dict = model_to_dict(msg)
#                 need_data = dict(repository=data_dict.get('repository'), build_host=data_dict.get('build_host'),
#                                  temp_name=data_dict.get('temp_name'))
#
#                 if data_dict.get('publish_hosts'):
#                     hosts_list = data_dict.get('publish_hosts').split('\n')
#                     for host in hosts_list:
#                         all_host_info[host.split(' ')[0]] = host.split(' ')[1:4]
#
#                 need_data['all_host_info'] = all_host_info
#                 publish_hosts_api = data_dict.get('publish_hosts_api')
#                 if publish_hosts_api:
#                     http_client = httpclient.AsyncHTTPClient()
#                     response = await http_client.fetch(publish_hosts_api, raise_error=False,
#                                                        headers=self.request.headers)
#                     if response.code == 200:
#                         response_data = json.loads(response.body.decode('utf-8'))
#                         if response_data:
#                             for res in response_data['data']['server_list']:
#                                 if res.get('ip'):
#                                     all_host_info[res.get('ip')] = [res.get('port', 22), res.get('admin_user', 'root')]
#                         need_data['all_host_info'] = all_host_info
#                     else:
#                         return self.write(dict(code=-3, msg='主机组API获取失败 error code：{}'.format(response.code),
#                                                data=need_data))
#                 return self.write(dict(code=0, msg='获取详细成功', data=need_data))
#
#         else:
#             with DBContext('r') as session:
#                 publish_info = session.query(TaskPublishConfig.publish_name, TaskCodeRepository.user_info).outerjoin(
#                     TaskCodeRepository, TaskPublishConfig.repository == TaskCodeRepository.repository).order_by(
#                     TaskPublishConfig.id).all()
#             for msg in publish_info:
#                 if self.is_superuser:
#                     publish_app_list.append(msg[0])
#                 elif msg[1] and nickname in msg[1].split(','):
#                     publish_app_list.append(msg[0])
#             return self.write(dict(code=0, msg='获取成功', data=publish_app_list))
#
#     def post(self, *args, **kwargs):
#         data = json.loads(self.request.body.decode("utf-8"))
#         publish_name = data.get('publish_name', None)
#         publish_tag = data.get('publish_tag', None)
#         start_time = data.get('start_time', None)
#         start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=8)
#
#         if not publish_name or not publish_tag or not start_time:
#             return self.write(dict(code=-1, msg='必填项不能为空'))
#
#         with DBContext('r') as session:
#             config_info = session.query(TaskPublishConfig).filter(
#                 TaskPublishConfig.publish_name == publish_name).first()
#             temp_id = session.query(TempList.temp_id).filter(TempList.temp_name == config_info.temp_name).first()
#             if not temp_id:
#                 return self.write(dict(code=-1, msg='关联的任务模板有误，快去检查！'))
#         args_dict = dict(PUBLISH_NAME=publish_name, PUBLISH_TAG=publish_tag)
#         hosts_dict = {1: config_info.build_host}
#         data_info = dict(exec_time=start_time, temp_id=temp_id[0], task_name=publish_name,
#                          task_type=config_info.temp_name,
#                          submitter=self.get_current_nickname(), associated_user="", args=str(args_dict),
#                          hosts=str(hosts_dict), schedule='new', details='', )
#
#         return_data = acc_create_task(**data_info)
#         return self.write(return_data)
#
#
# class MySqlOptimize(BaseHandler):
#     def post(self, *args, **kwargs):
#         data = json.loads(self.request.body.decode("utf-8"))
#         publish_name = data.get('publish_name', None)
#         temp_id = data.get('temp_id', None)
#         db_name = data.get('db_name', None)
#         sqls = data.get('sqls', None)
#         start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         if not publish_name or not sqls or not db_name or not start_time:
#             return self.write(dict(code=-1, msg='必填项不能为空'))
#
#         with DBContext('r') as session:
#             config_info = session.query(TaskPublishConfig).filter(
#                 TaskPublishConfig.publish_name == publish_name).first()
#             if not temp_id:
#                 return self.write(dict(code=-1, msg='关联的任务模板有误，快去检查！'))
#
#         args_dict = dict(PUBLISH_NAME=publish_name, DB_NAME=db_name, SQLS='"{}"'.format(sqls))
#         hosts_dict = {1: config_info.build_host}
#         data_info = dict(exec_time=start_time, temp_id=temp_id, task_name=publish_name,
#                          task_type=config_info.temp_name, submitter=self.get_current_nickname(),
#                          associated_user="", args=str(args_dict), hosts=str(hosts_dict), schedule='ready', details='', )
#
#         return_data = acc_create_task(**data_info)
#         return self.write(return_data)
#
#
# class MySqlAudit(BaseHandler):
#     def post(self, *args, **kwargs):
#         data = json.loads(self.request.body.decode("utf-8"))
#         publish_name = data.get('publish_name', None)
#         temp_id = data.get('temp_id', None)
#         db_file = data.get('db_file', None)
#         start_time = data.get('start_time', None)
#         print(data)
#         start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=8)
#         if not publish_name or not db_file or not temp_id or not start_time:
#             return self.write(dict(code=-1, msg='必填项不能为空'))
#
#         with DBContext('r') as session:
#             config_info = session.query(TaskPublishConfig).filter(
#                 TaskPublishConfig.publish_name == publish_name).first()
#             if not temp_id:
#                 return self.write(dict(code=-1, msg='关联的任务模板有误，快去检查！'))
#
#         args_dict = dict(PUBLISH_NAME=publish_name, DB_FILE=db_file)
#         hosts_dict = {1: config_info.build_host}
#         data_info = dict(exec_time=start_time, temp_id=temp_id, task_name=publish_name,
#                          task_type=config_info.temp_name, submitter=self.get_current_nickname(),
#                          associated_user="", args=str(args_dict), hosts=str(hosts_dict), schedule='new', details='', )
#
#         return_data = acc_create_task(**data_info)
#         return self.write(return_data)


other_urls = [
    (r"/other/v2/task_other/repository/", CodeRepositoryHandler),
    (r"/other/v2/task_other/docker_registry/", DockerRepositoryHandler),
    (r"/other/v2/task_other/publish_cd/", PublishCDHandler),
]

if __name__ == "__main__":
    pass
