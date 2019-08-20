#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2019/7/19
Desc    : 项目发布API
"""

import json
import datetime
from sqlalchemy import or_
from libs.base_handler import BaseHandler
from models.git_model import GitRepo
from models.publish_model import PublishList, model_to_dict
from websdk.db_context import DBContext
from .task_accept import create_task as acc_create_task
###
# from .configs_init import configs_init
from websdk.consts import const
from websdk.tools import convert
from websdk.cache_context import cache_conn


class ProjectHandler(BaseHandler):
    def get(self, *args, **kwargs):
        project_id = self.get_argument('project_id', default=None, strip=True)
        nickname = self.get_current_nickname()
        if not project_id:
            return self.write(dict(code=-1, msg='项目不能为空'))

        with DBContext('r') as session:
            project_info = session.query(PublishList).filter(PublishList.id == project_id).first()

        project_info = model_to_dict(project_info)
        project_info['start_time'] = str(project_info['start_time'])
        project_info['create_time'] = str(project_info['create_time'])
        project_info['pm'] = project_info['pm'].split(',') if project_info['pm'] else []
        project_info['developers'] = project_info['developers'].split(',')
        project_info['tester'] = project_info['tester'].split(',') if project_info['tester'] else []
        project_info['dba'] = project_info['dba'].split(',') if project_info['dba'] else []
        project_info['other_user'] = project_info['other_user'].split(',') if project_info['other_user'] else []

        project_info['pm_admin'] = True if nickname in project_info['pm'] else False
        project_info['developers_admin'] = True if nickname in project_info['developers'] else False
        project_info['tester_admin'] = True if nickname in project_info['tester'] else False
        project_info['dba_admin'] = True if nickname in project_info['dba'] else False

        self.write(dict(code=0, msg='获取项目详情成功', data=project_info))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        project_name = data.get('project_name')
        pm = data.get('pm')
        developers = data.get('developers')
        tester = data.get('tester')
        dba = data.get('dba')
        other_user = data.get('other_user')
        env_list = data.get('env_list')
        description = data.get('description')
        start_time = data.get('start_time', None)
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ") + datetime.timedelta(hours=8)

        print(data)
        if self.get_current_nickname() not in pm:
            pm.append(self.get_current_nickname())
        if not project_name or not developers or not env_list:
            return self.write(dict(code=-1, msg='参数不能为空'))

        ### 列表转为字符串
        pm, developers, tester = ','.join(pm), ','.join(developers), ','.join(tester)
        dba, other_user = ','.join(dba), ','.join(other_user)

        step_info_list = []
        serial = 0
        for env in env_list.split('-'):
            serial += 1
            if env == '项目信息':
                step_info_list.append({'name': env, "state": '2', "serial": serial})
            else:
                step_info_list.append({'name': env, "state": '1', "serial": serial})

        print("此处应该发送邮件到各个人员，提醒项目创建成功")
        # return
        # redis_conn = cache_conn()
        # # config_info = redis_conn.hgetall(const.APP_SETTINGS)
        # # config_info = convert(config_info)
        # # print(config_info)
        # nickname_key = bytes(self.get_current_nickname()+ '__contact', encoding='utf-8')
        # print( redis_conn.hmget(nickname_key, 'tel', 'email'))

        # with DBContext('r') as session:
        #     is_exist = session.query(TaskCodeRepository.id).filter(TaskCodeRepository.repository == repository).first()
        # if is_exist:
        #     return self.write(dict(code=-2, msg='不能重复'))

        # PublishList.repo_info: json.dumps(repo_info)
        repo_info = {"repo_info_list": []}
        with DBContext('w', None, True) as session:
            session.add(PublishList(project_name=project_name, pm=pm, developers=developers, tester=tester,
                                    dba=dba, other_user=other_user, step_info=json.dumps(step_info_list), run_env='dev',
                                    repo_info=json.dumps(repo_info), description=description, start_time=start_time))

        return self.write(dict(code=0, msg='创建项目上线流程成功'))

    def patch(self, *args, **kwargs):
        ### 对发布做干预和内容修改
        temp_id = '9039'
        ## 每个环境发布到那个k8s，发布到那个命名空间
        data = json.loads(self.request.body.decode("utf-8"))
        project_id = data.get('project_id')

        if not project_id:
            return self.write(dict(code=-1, msg='项目ID不能为空'))

        user_type = data.get('user_type')
        ### 更改用户
        if user_type:
            user_value = data.get('user_value')
            user_value = ','.join(user_value)
            with DBContext('w', None, True) as session:
                session.query(PublishList).filter(PublishList.id == project_id).update({user_type: user_value})
            return self.write(dict(code=0, msg='更新{}成功'.format(user_type)))

        repo_id_list = data.get('repo_id_list')
        repo_info = {"repo_info_list": []}
        repo_list = []
        ### 更改应用
        if repo_id_list:
            with DBContext('w', None, True) as session:
                git_repo_info = session.query(GitRepo).filter(GitRepo.id.in_(repo_id_list)).all()
                for msg in git_repo_info:
                    new_dict = {}
                    data_dict = model_to_dict(msg)
                    ### 取钩子 ssh  路径 项目ID
                    hook_list = []
                    if data_dict['git_hooks']:
                        git_hooks = json.loads(data_dict['git_hooks'])
                        for k, v in git_hooks.items():
                            hook_list.append(k)

                    new_dict['hook_list'] = hook_list
                    new_dict['id'] = data_dict['id']
                    new_dict['git_url'] = data_dict['git_url']
                    new_dict['project_id'] = data_dict['project_id']
                    new_dict['relative_path'] = data_dict['relative_path']
                    new_dict['ssh_url_to_repo'] = data_dict['ssh_url_to_repo']
                    new_dict['project_tag'] = ""
                    new_dict['sql_true'] = False
                    new_dict['project_sql'] = ""
                    new_dict['tag_list'] = []
                    new_dict['project_level'] = 1
                    repo_list.append(new_dict)

                repo_info['repo_info_list'] = repo_list
                ### 选择仓库后修改进度
                step_info_list = state_handle(project_id, '项目开发')

                session.query(PublishList).filter(PublishList.id == project_id).update(
                    {PublishList.repo_info: json.dumps(repo_info), PublishList.step_info: str(step_info_list)})
            return self.write(dict(code=0, msg='更新成功', data=repo_info))

        ### 发起测试
        to_test = data.get('project_test')
        if to_test:
            new_publish_list = []
            for app in to_test:
                new_dict = dict(relative_path=app.get('relative_path'), ssh_url_to_repo=app.get('ssh_url_to_repo'),
                                project_tag=app.get('project_tag'), project_sql=app.get('project_sql'),
                                project_level=app.get('project_level'))
                new_publish_list.append(new_dict)

            ### 发布使用的参数
            publish_info = dict(publish_list=new_publish_list)
            ### 记录的数据
            repo_info = {"repo_info_list": to_test}

            publish_info['ENV'] = 'qa'
            ###### 触发任务。

            hosts_dict = {1: '127.0.0.1'}
            data_info = dict(temp_id=temp_id, task_name="微服务发布", submitter=self.get_current_nickname(),
                             associated_user="", args=str(publish_info), hosts=str(hosts_dict), schedule='ready')

            ### 提交任务
            return_data = acc_create_task(**data_info)

            ### 更新触发的任务id，方便查询
            task_dict = dict(测试环境=return_data.get('list_id'))
            ### 更新步骤
            step_info_list = state_handle(project_id, '测试环境')
            with DBContext('w', None, True) as session:
                session.query(PublishList).filter(PublishList.id == project_id).update(
                    {PublishList.step_info: str(step_info_list), PublishList.run_env: 'qa',
                     PublishList.task_info:json.dumps(task_dict),
                     PublishList.real_publish: json.dumps(publish_info), PublishList.repo_info: json.dumps(repo_info)})

            return self.write(return_data)
            # return self.write(dict(code=0, msg='提测成功'))

        self.write(dict(code=0, msg='不在计划内的状态'))

    def put(self, *args, **kwargs):
        ### 审批流
        pass


class PublishListHandler(BaseHandler):
    def get(self, *args, **kwargs):
        publish_dev_list = []
        publish_qa_list = []
        publish_online_list = []
        with DBContext('r') as session:
            publish_info = session.query(PublishList).filter(PublishList.run_env != 'end').all()

        for msg in publish_info:
            data_dict = model_to_dict(msg)
            data_dict['create_time'] = str(data_dict['create_time'])
            data_dict['start_time'] = str(data_dict['start_time'])
            if data_dict['run_env'] == 'dev':
                publish_dev_list.append(data_dict)
            elif data_dict['run_env'] == 'qa':
                publish_qa_list.append(data_dict)
            else:
                publish_online_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', publish_dev_list=publish_dev_list,
                               publish_qa_list=publish_qa_list, publish_online_list=publish_online_list))


class PublishDetailHandler(BaseHandler):
    def get(self, *args, **kwargs):
        publish_dev_list = []
        publish_qa_list = []
        publish_online_list = []
        with DBContext('r') as session:
            publish_info = session.query(PublishList).filter(PublishList.run_env != 'end').all()

        for msg in publish_info:
            data_dict = model_to_dict(msg)
            data_dict['create_time'] = str(data_dict['create_time'])
            data_dict['start_time'] = str(data_dict['start_time'])
            if data_dict['run_env'] == 'dev':
                publish_dev_list.append(data_dict)
            elif data_dict['run_env'] == 'qa':
                publish_qa_list.append(data_dict)
            else:
                publish_online_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', publish_dev_list=publish_dev_list,
                               publish_qa_list=publish_qa_list, publish_online_list=publish_online_list))


def state_handle(project_id, the_step_name):
    new_step_info_list = []
    with DBContext('r') as session:
        step_info_list = session.query(PublishList.step_info).filter(PublishList.id == project_id).first()
    step_info_list = eval(step_info_list[0])

    step_serial = 1
    for step_info in step_info_list:
        if step_info['name'] == the_step_name:
            step_serial = step_info['serial']

    for step_info in step_info_list:
        if step_info['serial'] < step_serial:
            step_info['state'] = '3'
        elif step_info['serial'] == step_serial:
            step_info['state'] = '2'
        else:
            step_info['state'] = '1'
        new_step_info_list.append(step_info)

    return new_step_info_list


project_publish_urls = [
    (r"/other/v1/publish/project/", ProjectHandler),
    (r"/other/v1/publish/list/", PublishListHandler),
    (r"/other/v1/publish/detail/", PublishDetailHandler),

]
if __name__ == "__main__":
    pass
