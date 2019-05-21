#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
author : shenshuo
date   : 2017年11月30日15:55:48
desc   : 任务管理API
任务状态标记   0:新建,1:等待,2:运行中,3:完成,4:错误,5:手动
"""

import json
import time, datetime
from ast import literal_eval
from libs.base_handler import BaseHandler
from websdk.db_context import DBContext
from sqlalchemy import or_, func
from models.scheduler import TaskList, TaskSched, TempDetails, ArgsList, model_to_dict
from websdk.cache_context import cache_conn


class TaskListHandler(BaseHandler):
    def get(self, *args, **kwargs):
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default=100, strip=True)
        limit_start = (int(page_size) - 1) * int(limit)
        task_list = []
        this_list = []
        username = self.get_current_user()
        nickname = self.get_current_nickname()
        ### 超级管理员 和模板关联过的用户可以查看

        with DBContext('r') as session:
            count = session.query(TaskList).filter(TaskList.schedule != 'OK').count()
            task_info = session.query(TaskList).filter(TaskList.schedule != 'OK').order_by(
                -TaskList.start_time, -TaskList.list_id).offset(limit_start).limit(int(limit))

        for msg in task_info:
            data_dict = model_to_dict(msg)
            user_list = []
            for i in list(literal_eval(data_dict.get("associated_user")).values()):
                user_list.extend(i)
            if username in user_list or nickname in user_list or self.is_superuser:
                data_dict['create_time'] = str(data_dict['create_time'])
                data_dict['start_time'] = str(data_dict['start_time'])
                this_list.append(data_dict.get("list_id"))
                task_list.append(data_dict)

        list_id = "" if len(this_list) < 1 else this_list[0]

        return self.write(dict(code=0, msg="获取成功", data=task_list, count=count, list_id=list_id))

    def patch(self, *args, **kwargs):
        ### 审批
        data = json.loads(self.request.body.decode("utf-8"))
        list_id = data.get('list_id', None)
        start_time = data.get('start_time', None)
        nickname = self.get_current_nickname()

        if not list_id or not start_time:
            return self.write(dict(code=-1, msg='订单ID和开始时间不能为空'))

        with DBContext('r') as session:
            task_info = session.query(TaskList).filter(TaskList.list_id == list_id).first()

        admin_user = literal_eval(task_info.associated_user).get("admin")
        if nickname in admin_user or self.is_superuser:
            with DBContext('w', None, True) as session:
                session.query(TaskList).filter(TaskList.list_id == list_id).update(
                    {TaskList.schedule: 'ready', TaskList.start_time: start_time, TaskList.status: '1',
                     TaskList.executor: nickname})

                session.query(TaskSched).filter(TaskSched.list_id == list_id, TaskSched.task_status == '0').update(
                    {TaskSched.task_status: '1'})
            redis_conn = cache_conn()
            try:
                time_array = time.strptime(start_time, '%Y-%m-%d %H:%M')
            except:
                time_array = time.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            start_time = time.mktime(time_array)
            redis_conn.set('task_id_{}_start_time'.format(list_id), start_time)
            redis_conn.expire('task_id_{}_start_time'.format(list_id), 2592000)
            return self.write(dict(code=0, msg='任务开始成功'))
        else:
            return self.write(dict(code=-2, msg="你没有审批权限"))

    def put(self, *args, **kwargs):
        ### 终止任务
        data = json.loads(self.request.body.decode("utf-8"))
        list_id = data.get('list_id', None)
        nickname = self.get_current_nickname()

        if not list_id:
            return self.write(dict(code=-1, msg='订单ID不能为空'))

        with DBContext('r') as session:
            task_info = session.query(TaskList).filter(TaskList.list_id == list_id).first()

        admin_user = literal_eval(task_info.associated_user).get("admin")
        if nickname in admin_user or self.is_superuser:
            with DBContext('w', None, True) as session:
                session.query(TaskList).filter(TaskList.list_id == list_id).update({TaskList.schedule: 'OK'})
                session.query(TaskSched).filter(TaskSched.list_id == list_id).update({TaskSched.task_status: '3'})

            return self.write(dict(code=0, msg='订单终止成功'))
        else:
            return self.write(dict(code=-2, msg="你没有终止权限"))


class TaskCheckHandler(BaseHandler):
    def get(self, *args, **kwargs):
        list_id = self.get_argument('list_id', default=None, strip=True)
        get_run_group = self.get_argument('get_run_group', default=None, strip=True)
        get_run_host = self.get_argument('get_run_host', default=None, strip=True)
        nickname = self.get_current_nickname()
        hand_list = []
        if not list_id:
            return self.write(dict(code=-1, msg='订单ID不能为空'))

        with DBContext('r') as session:
            task_info = session.query(TaskList).filter(TaskList.list_id == list_id).first()
            args_info = session.query(ArgsList.args_name, ArgsList.args_self).all()
            hand_task = session.query(TempDetails.command_name).filter(TempDetails.temp_id == task_info.temp_id,
                                                                       TempDetails.trigger == 'hand').all()

        args_record = []
        new_args_dict = {}
        new_args_list = []
        try:
            args_dict = literal_eval(task_info.args)
        except Exception as e :
            print(str(e))
            args_dict = {}

        for h in hand_task:
            hand_list.append(h[0])

        if args_dict:
            for k, v in args_dict.items():
                # if len(v) < 100:  ### 只展示比较短的参数
                for i in args_info:
                    args_record.append(i[1])
                    if i[1] == k:
                        new_args_dict[i[0]] = v
                        new_args_list.append({'args_key': i[0],'args_value': v})
                if k not in args_record:
                    new_args_dict[k] = v
                    new_args_list.append({'args_key': k, 'args_value': v})

        ### 组
        all_hosts = literal_eval(task_info.hosts)
        group_list = list(all_hosts.keys())
        ### 已经获取到组
        if get_run_group:
            run_group = get_run_group
        else:
            if len(group_list) < 1:
                return self.write(dict(code=-1, msg='没有可运行组'))
            elif len(group_list) == 1:
                run_group = group_list[0]
            else:
                with DBContext('r') as session:
                    scheduler_info = session.query(TaskSched.task_group).filter(TaskSched.list_id == list_id).filter(
                        or_(TaskSched.task_status == "2", TaskSched.task_status == "4")).first()
                if scheduler_info:
                    run_group = scheduler_info[0]
                else:
                    run_group = group_list[0]

        this_hosts = all_hosts.get(int(run_group))
        if not this_hosts or len(this_hosts.split(',')) < 1:
            return self.write(dict(code=-2, msg='运行组中没有可执行主机'))

        this_host_list = this_hosts.split(',')
        if get_run_host:
            this_host = get_run_host
        else:
            this_host = this_host_list[0]

        scheduler_list, hosts_status = get_task_info(list_id, run_group, this_host, this_host_list)

        ### 编组别名暂无
        admin_user = literal_eval(task_info.associated_user).get("admin")
        associated_user = "管理员：{}".format(" ".join(admin_user))
        if nickname in admin_user or self.is_superuser:
            approval_button = True
        else:
            approval_button = False

        # 审批按钮
        # 干预按钮

        data_dict = dict(create_time=str(task_info.create_time), start_time=str(task_info.start_time),
                         username=self.get_current_user(), creator=task_info.creator,
                         executor=task_info.executor, new_args=new_args_dict, new_args_list=new_args_list,
                         schedule=task_info.schedule,
                         associated_user=associated_user, approval_button=approval_button,
                         args_keys=list(new_args_dict.keys()), hand_list=hand_list, group_list=group_list,
                         run_group=str(run_group), this_host_list=list(this_host_list), this_host=this_host,
                         scheduler_list=scheduler_list, hosts_status=hosts_status, list_id=str(list_id))

        return self.write(dict(code=0, msg='获取订单信息成功', data=data_dict))

    def put(self, *args, **kwargs):
        ### 处理全部需要手动干预的任务
        data = json.loads(self.request.body.decode("utf-8"))
        list_id = data.get('list_id', None)
        hand_task = data.get('hand_task', None)

        if not list_id:
            return self.write(dict(code=-1, msg='订单ID 不能为空'))
        if not hand_task:
            return self.write(dict(code=-2, msg='任务名称不正确'))

        with DBContext('w', None, True) as session:
            session.query(TaskSched).filter(TaskSched.list_id == list_id, TaskSched.task_name == hand_task).update(
                {TaskSched.task_status: '1'})
            data_info = session.query(TaskSched).filter(TaskSched.list_id == list_id,
                                                        TaskSched.task_name == hand_task).all()

            redis_conn = cache_conn()
            redis_pipe = redis_conn.pipeline()
            for msg in data_info:
                data_dict = model_to_dict(msg)
                hash_key = "task_{}_{}_{}".format(list_id, data_dict["task_group"], data_dict["exec_ip"])
                redis_pipe.hset(hash_key, data_dict["task_level"], '1')
                redis_pipe.expire(hash_key, 2592000)
            redis_pipe.execute()

        return self.write(dict(code=0, msg='审核干预成功'))

    def patch(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        list_id = data.get('list_id', None)
        task_group = data.get('task_group', None)
        task_level = data.get('task_level', None)
        exec_ip = data.get('exec_ip', None)
        hand_type = data.get('hand_type', None)
        if not list_id or not task_group or not task_level or not exec_ip:
            return self.write(dict(code=-1, msg='缺少必要参数'))

        if not hand_type:
            return self.write(dict(code=-1, msg='执行类型不能为空'))
        hash_key = "task_{}_{}_{}".format(list_id, task_group, exec_ip)
        redis_conn = cache_conn()

        if hand_type == "execute":
            s_id = data.get('scheduler_id', None)
            if s_id:
                with DBContext('w', None, True) as session:
                    session.query(TaskSched).filter(TaskSched.sched_id == s_id).update({TaskSched.task_status: '1'})
                redis_conn.hset(hash_key, task_level, '1')
                redis_conn.expire(hash_key, 2592000)
                return self.write(dict(code=0, msg='审核执行成功'))
            else:
                return self.write(dict(code=-2, msg='审批执行任务参数缺失'))

        elif hand_type == "restart":
            with DBContext('w', None, True) as session:
                session.query(TaskSched).filter(TaskSched.list_id == list_id, TaskSched.task_group == task_group,
                                                TaskSched.exec_ip == exec_ip, TaskSched.task_status != '5',
                                                TaskSched.task_status != '7',
                                                TaskSched.task_level >= task_level).update({TaskSched.task_status: '1'})
                session.query(TaskSched).filter(TaskSched.list_id == list_id, TaskSched.task_group == task_group,
                                                TaskSched.exec_ip == exec_ip, TaskSched.task_status != '5',
                                                TaskSched.task_status != '7',
                                                TaskSched.task_level < task_level).update({TaskSched.task_status: '3'})

                data_info = session.query(TaskSched.task_level, TaskSched.task_status).filter(
                    TaskSched.list_id == list_id,
                    TaskSched.task_group == task_group,
                    TaskSched.exec_ip == exec_ip).all()
            level_status = {}
            for s in data_info:
                if s[1] not in ['5', '7']:
                    if s[0] >= task_level:
                        level_status[s[0]] = s[1]
                    else:
                        level_status[s[0]] = '3'
            print(level_status)
            redis_conn.hmset(hash_key, level_status)
            redis_conn.expire(hash_key, 2592000)

            return self.write(dict(code=0, msg='重新执行成功'))
        elif hand_type == "stop_one":
            with DBContext('w', None, True) as session:
                session.query(TaskSched).filter(TaskSched.list_id == list_id, TaskSched.task_group == task_group,
                                                TaskSched.exec_ip == exec_ip).update({TaskSched.task_status: '3'})

                data_info = session.query(TaskSched.task_level).filter(TaskSched.list_id == list_id,
                                                                       TaskSched.task_group == task_group,
                                                                       TaskSched.exec_ip == exec_ip).all()
            level_status = {}
            for s in data_info:
                level_status[s[0]] = '3'
            redis_conn.hmset(hash_key, level_status)
            redis_conn.expire(hash_key, 2592000)
            return self.write(dict(code=0, msg='终止此组任务成功'))
        else:
            return self.write(dict(code=-5, msg='错误任务类型'))


def get_task_info(list_id, task_group, exec_ip, this_host_list):
    scheduler_list = []
    hosts_status = {}
    with DBContext('r') as session:
        for h in this_host_list:
            scheduler_info = session.query(TaskSched).filter(TaskSched.list_id == list_id,
                                                             TaskSched.task_group == task_group,
                                                             TaskSched.exec_ip == h).order_by(
                TaskSched.task_level).all()

            status_list = []
            for msg in scheduler_info:
                data_dict = model_to_dict(msg)
                status_list.append(data_dict.get("task_status"))
                if exec_ip == data_dict.get("exec_ip"):
                    scheduler_list.append(data_dict)

            status = '4'
            if '0' in status_list:
                status = '0'
            if '1' in status_list:
                status = '1'
            if '2' in status_list:
                status = '2'
            if '5' in status_list and '1' not in status_list and '2' not in status_list:
                status = '5'
            if '6' in status_list:
                status = '6'
            if '7' in status_list:
                status = '7'
            if '4' in status_list:
                status = '4'
            if '3' in status_list and len(list(set(status_list))) == 1:
                status = '3'

            hosts_status[str(h)] = status

    return scheduler_list, hosts_status


class HistoryListHandler(BaseHandler):
    def get(self, *args, **kwargs):
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default=500, strip=True)
        limit_start = (int(page_size) - 1) * int(limit)
        task_list = []
        this_list = []
        username = self.get_current_user()
        nickname = self.get_current_nickname()

        with DBContext('r') as session:
            count = session.query(TaskList).filter(TaskList.schedule == 'OK').count()
            task_info = session.query(TaskList).filter(TaskList.schedule == 'OK').order_by(
                -TaskList.list_id).offset(limit_start).limit(int(limit))

        for msg in task_info:
            data_dict = model_to_dict(msg)
            user_list = []
            for i in list(literal_eval(data_dict.get("associated_user")).values()):
                user_list.extend(i)
            if username in user_list or nickname in user_list or self.is_superuser:
                data_dict['create_time'] = str(data_dict['create_time'])
                data_dict['start_time'] = str(data_dict['start_time'])
                this_list.append(data_dict.get("list_id"))
                task_list.append(data_dict)

        return self.write(dict(code=0, msg="获取成功", data=task_list, count=count, history=True))


class TaskStatementHandler(BaseHandler):
    def get(self, *args, **kwargs):
        statement_list = []

        with DBContext('r') as session:
            count = session.query(TaskList).count()
            task_info = session.query(TaskList.task_type, func.count(TaskList.task_type)).group_by(TaskList.task_type)
        for msg in task_info:
            statement_list.append(dict(task_type=msg[0],task_len=msg[1]))

        return self.write(dict(code=0, msg="获取成功", data=statement_list, count=count))


# class TaskLogHandler(BaseHandler):
#     def get(self, *args, **kwargs):
#         list_id = self.get_argument('list_id', default=1, strip=True)
#         group = self.get_argument('task_group', default=None, strip=True)
#         level = self.get_argument('task_level', default=None, strip=True)
#         hosts = self.get_argument('exec_ip', default=None, strip=True)
#         if not list_id or not group or not level or not hosts:
#             return self.write(dict(status=-1, msg='参数不能为空'))
#
#         log_list = []
#         with DBContext('readonly') as session:
#             log_info = session.query(TaskLog.log_time, TaskLog.task_log).filter(TaskLog.list_id == list_id,
#                                                                                 TaskLog.exec_ip == hosts,
#                                                                                 TaskLog.task_group == group,
#                                                                                 TaskLog.task_level == level).all()
#         for i in log_info:
#             log_list.append(dict(log_time=str(i[0]), task_log=str(i[1])))
#
#         self.write(dict(code=0, msg='获取日志成功', data=log_list))
#
#
# class ListLogHandler(BaseHandler):
#     def get(self, list_id):
#         if not list_id:
#             return self.write(dict(status=-1, msg='参数不能为空'))
#
#         log_list = []
#         with DBContext('readonly') as session:
#             log_info = session.query(TaskLog.log_time, TaskLog.task_log).filter(TaskLog.list_id == list_id).all()
#         for i in log_info:
#             log_list.append(dict(log_time=str(i[0]), task_log=str(i[1])))
#
#         self.write(dict(status=0, msg='获取日志成功', data=log_list))


task_list_urls = [
    (r"/v2/task/list/", TaskListHandler),
    (r"/v2/task/check/", TaskCheckHandler),
    (r"/v2/task/check_history/", HistoryListHandler),
    (r"/v2/task/statement/", TaskStatementHandler),
    # (r"/v1/task/log/", TaskLogHandler),
    # (r"/v1/task/log/(\d*)/", ListLogHandler),
]

if __name__ == "__main__":
    pass
