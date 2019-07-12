#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
Author : SS
date   : 2017-10-11 12:48:43
desc   : exec scheduler
### 任务状态标记 0:新建,1:等待,2:运行中,3:完成,4:错误,5:手动
### 任务组按顺序触发，任务按预设触发，默认顺序执行
### 2018-3-29 更改消息为不确认
"""

import time
import datetime
import os
import multiprocessing
from ast import literal_eval
from websdk.web_logs import ins_log
from biz.exec_tasks import MyExecute
from models.scheduler import TaskList, TaskSched, ExecuteUser, model_to_dict
# from websdk.db_context import DBContext
from libs.db_context import DBContext
from websdk.configs import configs
from websdk.mqhelper import MessageQueueBase
from websdk.cache_context import cache_conn


class DealMQ(MessageQueueBase):
    """接受MQ消息 根据订单ID和分组 多线程执行任务"""

    def __init__(self, **settings):
        if configs.can_import:
            configs.import_dict(**settings)
        self.redis_conn = cache_conn()

        super(DealMQ, self).__init__(exchange='task_scheduler', exchange_type='direct', routing_key='the_task_id',
                                     queue_name='deal_task_scheduler', no_ack=False)

    def run(self, flow_id, group_id, all_hosts, all_args, exec_user_dict, level_list):
        MyExecute(flow_id, group_id, all_hosts, all_args, exec_user_dict, level_list, self.redis_conn).exec_thread()

    def exec_list_thread(self, lid, *all_gid):
        ### 如果任务没有审批，则进入休眠,初始休眠时间为0秒
        int_sleep, end_sleep = 1, 1
        while True:
            ### 挂起的任务设置休眠时间
            ins_log.read_log('info', 'The task-{0} is not ready, retry after {1} s of sleep'.format(lid, int_sleep))
            time.sleep(int_sleep)
            int_sleep += 2
            end_sleep += int_sleep
            if int_sleep > 15:
                int_sleep = 15

            with DBContext('r') as session:
                job_code = session.query(TaskList).filter(TaskList.list_id == lid, TaskList.schedule == 'new').first()
            if not job_code:
                break

            if end_sleep > 150:
                raise SystemExit('message timeout')

        ### 标记为任务开始，判断任务是否审批(schedule等于ready)
        with DBContext('w') as session:
            session.query(TaskList.list_id).filter(TaskList.list_id == lid, TaskList.schedule == 'ready').update(
                {TaskList.schedule: 'start'})
            session.commit()

        exec_user_dict = dict()
        with DBContext('r') as session:
            exec_user_info = session.query(ExecuteUser).all()
            task_info = session.query(TaskList).filter(TaskList.list_id == lid).first()
            sched_task_info = session.query(TaskSched).filter(TaskSched.list_id == lid).all()
            ### 参数信息 主机信息
            all_args_info = literal_eval(task_info.args)
            all_host_info = literal_eval(task_info.hosts)
            self.redis_conn.set('task_id_{}_start_time'.format(lid), time.mktime(task_info.start_time.timetuple()))
            self.redis_conn.expire('task_id_{}_start_time'.format(lid), 2592000)

            ### 管理用户信息
            for msg in exec_user_info:
                data_dict = model_to_dict(msg)
                exec_user_dict[data_dict.get("alias_user")] = data_dict.get("exec_user")
                exec_user_dict[data_dict.get("alias_user") + "port"] = data_dict.get("ssh_port", "22")
                exec_user_dict[data_dict.get("alias_user") + "password"] = data_dict.get("password", "")
                key_file = "/home/.ssh_key/{}_key".format(data_dict.get("alias_user"))
                if not os.path.exists('/home/.ssh_key/'):
                    os.makedirs('/home/.ssh_key/')
                with open(key_file, 'w') as k_file:
                    k_file.write(data_dict.get("user_key"))
                os.system("chmod 600 {}".format(key_file))

            ### 取出必要信息写入缓存
            level_list_info = dict()
            for i in all_gid:
                level_list_info[i[0]] = []
            with self.redis_conn.pipeline() as redis_pipe:
                for msg in sched_task_info:
                    data_dict = model_to_dict(msg)
                    log_key = "{}_{}_{}_{}".format(lid, data_dict["task_group"], data_dict["task_level"],
                                                   data_dict["exec_ip"])
                    task_info_key = "task_info_{}".format(log_key)
                    level_status_key = "level_status_{}".format(log_key)

                    data_dict["log_key"] = log_key
                    redis_pipe.hmset(task_info_key, data_dict)
                    redis_pipe.set(level_status_key, data_dict["task_status"])
                    redis_pipe.expire(task_info_key, 2592000)
                    redis_pipe.expire(level_status_key, 2592000)

                    for i in all_gid:
                        if i[0] == data_dict["task_group"]:
                            level_list_info[i[0]].append(int(data_dict["task_level"]))
                redis_pipe.execute()
        threads = []
        #####取所有主机###
        for i in all_gid:
            i = i[0]
            if i:
                all_exec_ip = all_host_info.get(i)
                level_list = list(set(level_list_info[i]))
                level_list.sort()
                print('level_list', level_list)
                threads.append(multiprocessing.Process(target=self.run, args=(
                    lid, i, all_exec_ip, all_args_info, exec_user_dict, level_list)))
        ins_log.read_log('info', "current has %d threads group execution " % len(threads))

        ###开始多进程
        for start_t in threads:
            try:
                start_t.start()
            except UnboundLocalError:
                ins_log.read_log('error', "UnboundLocalError")
        ###阻塞
        for join_t in threads:
            join_t.join()

    def on_message(self, body):
        ins_log.read_log('info', 'flow_id is {}'.format(body))
        time.sleep(2)
        try:
            args = int(body)
        except ValueError:
            ins_log.read_log('error', '[*]body type error01, must be int,body:(%s)' % str(body, encoding='utf-8'))
            args = 0
        except UnboundLocalError:
            ins_log.read_log('error', '[*]body type error02, must be int,body:(%s)' % str(body, encoding='utf-8'))
            args = 0

        if type(args) == int:
            flow_id = args
            with DBContext('r') as session:
                is_exist = session.query(TaskList.list_id).filter(TaskList.list_id == flow_id,
                                                                  TaskList.schedule.in_(('new', 'ready'))).first()
            ###查询ID是否存在并且未执行
            if is_exist:
                with DBContext('r') as session:
                    all_group = session.query(TaskSched.task_group).filter(TaskSched.list_id == flow_id).group_by(
                        TaskSched.task_group).all()

                ### 多进程分组执行任务
                self.exec_list_thread(flow_id, *all_group)
                ### 记录并修改状态
                with DBContext('w') as session:
                    session.query(TaskList.list_id).filter(TaskList.list_id == flow_id).update(
                        {TaskList.schedule: 'OK'})
                    session.commit()

                ins_log.read_log('info', 'list {0} end of task'.format(flow_id))

            else:
                ins_log.read_log('error', 'The task id-{0} has been executed !!!'.format(body))
                return

        else:
            ins_log.read_log('error', '[*]body type error03, must be int,body:(%s)' % str(body, encoding='utf-8'))


if __name__ == "__main__":
    pass
