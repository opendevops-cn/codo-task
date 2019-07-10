#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2019年6月28日
Desc    : GIT仓库管理API
"""

import datetime
import gitlab
import json
from sqlalchemy import or_
from libs.base_handler import BaseHandler
from .task_accept import create_task as acc_create_task
from models.git_model import GitConf, GitGroup, GitUsers, GitRepo, HooksLog, model_to_dict
from websdk.db_context import DBContext
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from tornado import gen


class GitTreeHandler(BaseHandler):
    def get(self, *args, **kwargs):
        repo_list = []
        with DBContext('r') as session:
            repo_info = session.query(GitRepo).all()

        for msg in repo_info:
            data_dict = model_to_dict(msg)
            repo_list.append(data_dict)

        _tree = [{"expand": True, "title": "GitLab", "children": [], "data_type": 'root'}]

        if repo_list:
            tmp_tree = {
                "git_url": {},
                "group_name": {},
            }

            for t in repo_list:
                git_url, group_name = t["git_url"], t['group_name']

                # 因为是第一层所以没有parent
                tmp_tree["git_url"][git_url] = {
                    "expand": True, "title": git_url, "parent": "GitLab", "children": [], "data_type": 'git_url'
                }

                tmp_tree["group_name"][git_url + "|" + group_name] = {
                    "expand": False, "title": group_name, "parent": git_url, "git_url": git_url,
                    "children": [], "data_type": 'group_name'
                }

            for tmp_group in tmp_tree["group_name"].values():
                tmp_tree["git_url"][tmp_group["parent"]]["children"].append(tmp_group)

            for tmp_git in tmp_tree["git_url"].values():
                _tree[0]["children"].append(tmp_git)

            return self.write(dict(code=0, msg='获取项目Tree成功', data=_tree))
        else:
            return self.write(dict(code=0, msg='获取项目Tree失败', data=_tree))


class GitRepoHandler(BaseHandler):
    def get(self, *args, **kwargs):
        git_url = self.get_argument('git_url', default=None, strip=True)
        group_name = self.get_argument('group_name', default=None, strip=True)
        search_val = self.get_argument('search_val', default=None, strip=True)
        repo_list = []

        if search_val:
            with DBContext('r') as session:
                git_repo_info = session.query(GitRepo).filter(
                    or_(GitRepo.group_name.like('%{}%'.format(search_val)),
                        GitRepo.project_name.like('%{}%'.format(search_val)),
                        GitRepo.relative_path.like('%{}%'.format(search_val)),
                        GitRepo.ssh_url_to_repo.like('%{}%'.format(search_val)),
                        GitRepo.git_url.like('%{}%'.format(search_val)))
                ).order_by(GitRepo.git_url, GitRepo.group_name).all()

        elif git_url and group_name:
            with DBContext('r') as session:
                git_repo_info = session.query(GitRepo).filter(GitRepo.git_url == git_url,
                                                              GitRepo.group_name == group_name).order_by(
                    GitRepo.git_url, GitRepo.group_name).all()
        else:
            with DBContext('r') as session:
                git_repo_info = session.query(GitRepo).order_by(GitRepo.git_url, GitRepo.group_name).all()

        for msg in git_repo_info:
            data_dict = model_to_dict(msg)
            data_dict['user_info'] = data_dict['user_info'].split(',')
            hook_list = []
            if data_dict['git_hooks']:
                git_hooks = json.loads(data_dict['git_hooks'])
                for k, v in git_hooks.items():
                    v['tag'] = k
                    hook_list.append(v)
            data_dict['hook_list'] = hook_list
            repo_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', data=repo_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        git_url = data.get('git_url')
        group_name = data.get('group_name')
        project_name = data.get('project_name')
        relative_path = data.get('relative_path')
        ssh_url_to_repo = data.get('ssh_url_to_repo')
        http_url_to_repo = data.get('http_url_to_repo')
        exist_user = data.get('existUser')
        user_info = ','.join(exist_user) if exist_user else ''

        if not git_url or not group_name or not project_name or not relative_path or not ssh_url_to_repo:
            return self.write(dict(code=-1, msg='关键参数不能为空'))

        with DBContext('r') as session:
            http_exist = session.query(GitRepo.id).filter(GitRepo.http_url_to_repo == http_url_to_repo).first()
            ssh_exist = session.query(GitRepo.id).filter(GitRepo.ssh_url_to_repo == ssh_url_to_repo).first()
        if http_exist:
            return self.write(dict(code=-2, msg='http_url_to_repo 已经存在'))

        if ssh_exist:
            return self.write(dict(code=-3, msg='ssh_url_to_repo 已经存在'))

        with DBContext('w', None, True) as session:
            session.add(GitRepo(git_url=git_url, group_name=group_name, project_name=project_name,
                                relative_path=relative_path, ssh_url_to_repo=ssh_url_to_repo,
                                http_url_to_repo=http_url_to_repo, user_info=user_info))

        return self.write(dict(code=0, msg='保存成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        hook_tag = data.get('hook_tag').strip()
        temp_id = data.get('temp_id')
        schedule = data.get('schedule', 'new')
        hook_args = data.get('hook_args')
        the_id = data.get('the_id')
        if not hook_tag or not temp_id or not the_id:
            return self.write(dict(code=1, msg='关键参数不能为空'))

        if hook_args:
            try:
                hook_args_dict = json.loads(hook_args)
            except Exception as e:
                return self.write(dict(code=2, msg='参数字典格式不正确'))
        else:
            hook_args_dict = dict()

        with DBContext('w', None, True) as session:
            git_hooks_info = session.query(GitRepo.git_hooks).filter(GitRepo.id == the_id).first()
            hook_dict = git_hooks_info[0] if git_hooks_info else {}
            if hook_dict:
                try:
                    hook_dict = json.loads(hook_dict)
                except Exception as e:
                    return self.write(dict(code=2, msg='钩子参数转化为字典的时候出错，请仔细检查相关内容' + str(e)))

            if not hook_dict:
                hook_dict = {hook_tag: dict(temp_id=temp_id, schedule=schedule, hook_args=hook_args_dict)}
            else:
                hook_dict[hook_tag] = dict(temp_id=temp_id, schedule=schedule, hook_args=hook_args_dict)

            hook_dict = json.dumps(hook_dict)

            session.query(GitRepo.git_hooks).filter(GitRepo.id == the_id).update({GitRepo.git_hooks: hook_dict})

        self.write(dict(code=0, msg='更新钩子成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        the_id = data.get('the_id')
        id_list = data.get('id_list')
        with DBContext('w', None, True) as session:
            if the_id:
                session.query(GitRepo).filter(GitRepo.id == the_id).delete(synchronize_session=False)
            elif id_list:
                session.query(GitRepo).filter(GitRepo.id.in_(id_list)).delete(synchronize_session=False)
            else:
                return self.write(dict(code=1, msg='关键参数不能为空'))

        self.write(dict(code=0, msg='删除成功'))


class GitUsersHandler(BaseHandler):
    def get(self, *args, **kwargs):
        git_url = self.get_argument('git_url', default=None, strip=True)
        group_name = self.get_argument('group_name', default=None, strip=True)
        repo_user_list = []

        if not git_url or group_name:
            with DBContext('r') as session:
                git_group_info = session.query(GitUsers).all()
        else:
            with DBContext('r') as session:
                git_user_info = session.query(GitGroup.user_list).filter(GitGroup.git_url == git_url,
                                                                         GitGroup.group_name == group_name).first()
                if git_user_info:
                    git_user_info = git_user_info[0]
                    git_user_list = git_user_info.split(',')
                    git_group_info = session.query(GitUsers).filter(GitUsers.user_id.in_(git_user_list)).all()
                else:
                    return self.write(dict(code=0, msg='没有用户', data=[]))

        for msg in git_group_info:
            data_dict = model_to_dict(msg)
            repo_user_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', data=repo_user_list))


class GitConfHandler(BaseHandler):
    def get(self, *args, **kwargs):
        repo_conf_list = []

        with DBContext('r') as session:
            git_group_info = session.query(GitConf).all()

        for msg in git_group_info:
            data_dict = model_to_dict(msg)
            repo_conf_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', data=repo_conf_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        git_url = data.get('git_url')
        private_token = data.get('private_token')
        api_version = data.get('api_version')
        deploy_key = data.get('deploy_key')

        if not git_url or not private_token or not api_version or not deploy_key:
            return self.write(dict(code=-1, msg='关键参数不能为空'))
        try:
            gl = gitlab.Gitlab(git_url, private_token=private_token, api_version=api_version)
            gl.groups.list(all=True)

        except Exception as e:
            return self.write(dict(code=-2, msg='测试失败' + str(e)))

        with DBContext('w', None, True) as session:
            is_exist = session.query(GitConf.id).filter(GitConf.git_url == git_url).first()
            is_count = session.query(GitConf).count()

            if is_count > 3:
                return self.write(dict(code=-3, msg='超出限制'))

            if is_exist:
                session.query(GitConf).filter(GitConf.git_url == git_url).update(
                    {GitConf.private_token: private_token, GitConf.api_version: api_version,
                     GitConf.deploy_key: deploy_key})
            else:
                session.add(GitConf(git_url=git_url, private_token=private_token, api_version=api_version,
                                    deploy_key=deploy_key))

        self.write(dict(code=0, msg='添加成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        git_url = data.get('git_url')

        with DBContext('w', None, True) as session:
            session.query(GitConf).filter(GitConf.git_url == git_url).delete(synchronize_session=False)
            session.query(GitRepo).filter(GitRepo.git_url == git_url).delete(synchronize_session=False)
            session.query(GitUsers).filter(GitUsers.git_url == git_url).delete(synchronize_session=False)
            session.query(GitGroup).filter(GitGroup.git_url == git_url).delete(synchronize_session=False)
        self.write(dict(code=0, msg='删除成功'))


class HooksLogHandler(BaseHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        log_list = []

        with DBContext('r') as session:
            hooks_log_info = session.query(HooksLog).order_by(-HooksLog.id).limit(200).all()

        for msg in hooks_log_info:
            data_dict = model_to_dict(msg)
            data_dict['create_time'] = str(data_dict['create_time'])
            log_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', data=log_list))


class GitHookHandler(BaseHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        self.write(dict(code=0, msg='获取csrf_key成功', csrf_key=self.new_csrf_key))

    @gen.coroutine
    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        git_url = data.get('git_url')
        tag_name = data.get('tag_name')
        relative_path = data.get('relative_path')

        if not git_url or not tag_name or not relative_path:
            return self.write(dict(code=-1, msg='Key parameters cannot be empty'))

        with DBContext('w', None, True) as session:
            session.add(HooksLog(git_url=git_url, relative_path=relative_path, logs_info='收到请求：{}'.format(tag_name)))

            hook_info = session.query(GitRepo.git_hooks, GitRepo.ssh_url_to_repo, GitRepo.http_url_to_repo
                                  ).filter(GitRepo.git_url == git_url, GitRepo.relative_path == relative_path).first()
            if not hook_info:
                # session.add(HooksLog(git_url=git_url, relative_path=relative_path, logs_info='没有查找到相关项目'))
                return self.write(dict(code=0, msg='No related items were found'))

            if hook_info and not hook_info[0]:
                # session.add(HooksLog(git_url=git_url, relative_path=relative_path, logs_info='没有配置钩子'))
                return self.write(dict(code=0, msg='No hooks, ignore'))
            else:
                try:
                    hook_dict = json.loads(hook_info[0])
                except Exception as e:
                    session.add(HooksLog(git_url=git_url, relative_path=relative_path, logs_info='钩子出错'))
                    return self.write(dict(code=2, msg='There was an error when the hook parameter was converted into '
                                                       'a dictionary. Please check the relevant contents carefully' ))

            tag_name_mate = None  ### 匹配到的标签或者分支
            for t in hook_dict.keys():
                if tag_name.startswith(t):
                    tag_name_mate = t

            if not tag_name_mate:
                session.add(HooksLog(git_url=git_url, relative_path=relative_path, logs_info="没有匹配到钩子"))
                return self.write(dict(code=2, msg='No hook matched'))
            else:
                the_hook = hook_dict[tag_name_mate]

                hook_args = dict(TAG=tag_name,RELATIVE_PATH=relative_path, GIT_SSH_URL=hook_info[1],
                                 GIT_HTTP_URL=hook_info[2])
                old_hook_args = the_hook.get('hook_args')
                ### 参数字典
                hosts_dict = {1: "127.0.0.1", 2: "127.0.0.1"}  ### 主机字典
                if the_hook.get('hook_args'):
                    hosts_dict.update(the_hook.get('hook_args'))
                    if old_hook_args.get('hosts_dict') and isinstance(old_hook_args.get('hosts_dict'), dict):
                        hosts_dict = old_hook_args.pop('hosts_dict')

                msg = '匹配到钩子：{} 模板ID：{} 执行：{}，参数：{}'.format(tag_name_mate, the_hook.get('temp_id'),
                                                            the_hook.get('schedule'), str(the_hook.get('hook_args')))
                if len(msg) > 200:
                    msg = msg[:200]
                session.add(HooksLog(git_url=git_url, relative_path=relative_path, logs_info=msg))

        data_info = dict(exec_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                         temp_id=the_hook.get('temp_id'), task_name=relative_path,
                         schedule=the_hook.get('schedule','new'),
                         submitter=self.get_current_nickname(), args=str(hook_args), hosts=str(hosts_dict))
        return_data = acc_create_task(**data_info)
        return self.write(return_data)

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        the_id = data.get('the_id')
        tag_index = data.get('tag_index')

        with DBContext('w', None, True) as session:
            hook_info = session.query(GitRepo.git_hooks).filter(GitRepo.id == the_id).first()
            if not hook_info:
                return self.write(dict(code=-1, msg='No related items were found'))

            if not hook_info[0]:
                return self.write(dict(code=-2, msg='No hooks, ignore'))
            else:
                try:
                    hook_dict = json.loads(hook_info[0])
                except Exception as e:
                    session.query(GitRepo).filter(GitRepo.id == the_id).update({GitRepo.git_hooks: ""})
                    return self.write(dict(code=2, msg='钩子出错'))

            hook_dict.pop(tag_index)
            hook_dict = json.dumps(hook_dict)

            session.query(GitRepo).filter(GitRepo.id == the_id).update({GitRepo.git_hooks: hook_dict})
        self.write(dict(code=0, msg='删除成功'))


class GitSyncHandler(BaseHandler):
    _thread_pool = ThreadPoolExecutor(3)

    @run_on_executor(executor='_thread_pool')
    def sync_git_info(self, git_list):
        try:
            for conf in git_list:
                git_url = conf.get('git_url')
                gl = gitlab.Gitlab(git_url, private_token=conf.get('private_token'),
                                   api_version=conf.get('api_version'))

                with DBContext('r') as session:
                    git_group_list_info = session.query(GitGroup.group_id).filter(GitGroup.git_url == git_url).all()
                    git_user_list_info = session.query(GitUsers.user_id).filter(GitUsers.git_url == git_url).all()

                git_group_list = []
                for g in git_group_list_info:
                    git_group_list.append(g[0])

                git_user_list = []
                for r in git_user_list_info:
                    git_user_list.append(r[0])
                ###
                exist_group_list = []  ### GIT上存在的组
                all_groups = gl.groups.list(all=True)
                for group in all_groups:
                    with DBContext('w', None, True) as session:
                        exist_group_list.append(group.id)

                        user_id_list = []
                        user_email_list = []
                        for me in group.members.list(all=True):
                            the_user_info = gl.users.get(me.id)
                            user_id_list.append(str(me.id))
                            try:
                                user_email_list.append(the_user_info.email)
                            except Exception as e:
                                print(e)

                        user_list = ','.join(user_id_list) if user_id_list else ''

                        if group.id not in git_group_list:
                            session.add(GitGroup(git_url=git_url, group_id=group.id, group_name=group.name,
                                                 description=group.description, user_list=user_list))
                        else:
                            session.query(GitGroup).filter(GitGroup.git_url == git_url,
                                                           GitGroup.group_id == group.id).update(
                                {GitGroup.group_name: group.name, GitGroup.description: group.description,
                                 GitGroup.user_list: user_list})

                        # print('[组]', git_url, group.name)

                        ####
                        group_list = gl.groups.get(group.id)
                        projects = group_list.projects.list(all=True)

                        git_repo_list_info = session.query(GitRepo.project_id).filter(GitRepo.git_url == git_url,
                                                                                      GitRepo.group_id == group_list.id).all()

                        git_repo_list = []
                        for r in git_repo_list_info:
                            git_repo_list.append(r[0])

                        for project in projects:
                            for me in gl.projects.get(project.id).members.list(all=True):
                                the_user_info = gl.users.get(me.id)
                                try:
                                    user_email_list.append(the_user_info.email)
                                except Exception as e:
                                    print(e)

                            user_email_list = list(set(user_email_list))
                            email_list = ','.join(user_email_list) if user_email_list else ''

                            if project.id not in git_repo_list:
                                session.add(GitRepo(git_url=git_url, group_id=group_list.id, group_name=group_list.name,
                                                    project_id=project.id,
                                                    ssh_url_to_repo=project.ssh_url_to_repo,
                                                    http_url_to_repo=project.http_url_to_repo,
                                                    project_name=project.name,
                                                    relative_path=project.path_with_namespace, user_info=email_list))
                            else:
                                session.query(GitRepo).filter(GitRepo.git_url == git_url,
                                                              GitRepo.group_id == group_list.id,
                                                              GitRepo.project_id == project.id).update(
                                    {GitRepo.ssh_url_to_repo: project.ssh_url_to_repo,
                                     GitRepo.http_url_to_repo: project.http_url_to_repo,
                                     GitRepo.project_name: project.name,
                                     GitRepo.relative_path: project.path_with_namespace, GitRepo.user_info: email_list})

                    session.commit()

                ### 用户
                # users = gl.users.list(all=True)
                # exist_user_list = []
                # with DBContext('w', None, True) as session:
                #     for user in users:
                #         exist_user_list.append(user.id)
                #         if user.id not in git_user_list:
                #             session.add(
                #                 GitUsers(git_url=git_url, user_id=user.id, name=user.name, username=user.username,
                #                          email=user.email, state=user.state))
                #         else:
                #             session.query(GitUsers).filter(GitUsers.git_url == git_url,
                #                                            GitUsers.user_id == user.id).update(
                #                 {GitUsers.name: user.name, GitUsers.username: user.username, GitUsers.email: user.email,
                #                  GitUsers.state: user.state})
                #
                #     for uu in git_user_list:
                #         if uu not in exist_user_list:
                #             session.query(GitUsers).filter(GitUsers.git_url == git_url, GitUsers.user_id == uu).delete(
                #                 synchronize_session=False)
            return "执行完成"
        except Exception as e:
            print(e)
            return '执行失败' + str(e)

    @gen.coroutine
    def post(self, *args, **kwargs):
        git_list = []
        with DBContext('r') as session:
            git_conf = session.query(GitConf).all()

        for msg in git_conf:
            data_dict = model_to_dict(msg)
            git_list.append(data_dict)

        try:
            # 超过60s 返回Timeout
            res = yield gen.with_timeout(datetime.timedelta(seconds=60), self.sync_git_info(git_list),
                                         quiet_exceptions=gen.TimeoutError)

            return self.write(dict(code=0, msg=res))
        except gen.TimeoutError:
            return self.write(dict(code=-1, msg='TimeOut'))


git_repo_urls = [
    (r"/other/v1/git/tree/", GitTreeHandler),
    (r"/other/v1/git/repo/", GitRepoHandler),
    (r"/other/v1/git/user/", GitUsersHandler),
    (r"/other/v1/git/conf/", GitConfHandler),
    (r"/other/v1/git/sync/", GitSyncHandler),
    (r"/other/v1/git/hooks/", GitHookHandler),
    (r"/other/v1/git/logs/", HooksLogHandler),

]

if __name__ == "__main__":
    pass
