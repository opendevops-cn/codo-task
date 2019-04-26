#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
author : SS
date   : 2017-10-11 12:48:43
role   : exec tasks
### 任务状态标记 0:新建,1:等待,2:运行中,3:完成,4:错误,5:手动,6：中断，7，定时
### 任务组按顺序触发，任务按预设触发，默认顺序执行
### 2018年4月16日  更改多进程为多线程
### 2018年11月20日 删除salt支持
### 2019年4月25日  日志优化
"""

import subprocess
import multiprocessing
import json
import time
import datetime
from models.scheduler import TaskList, TaskSched
from libs.db_context import DBContext

exec_timeout = 600


def exec_shell(log_key, real_cmd, cmd, redis_conn):
    redis_conn.publish("task_log", json.dumps(
        {"log_key": log_key, "exec_time": int(round(time.time() * 1000)), "result": "[CMD]: {}".format(cmd)}))
    start_time = time.time()
    sub = subprocess.Popen(real_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        time.sleep(2)
        ret = subprocess.Popen.poll(sub)
        current_time = time.time()
        duration = current_time - start_time
        ### 处理输出
        try:
            for i in sub.stdout.readlines():
                result = i.decode('utf-8')
                if result.replace('\n', ''):
                    redis_conn.publish("task_log", json.dumps(
                        {"log_key": log_key, "exec_time": int(round(time.time() * 1000)), "result": result}))
        except Exception as e:
            redis_conn.publish("task_log", json.dumps(
                {"log_key": log_key, "exec_time": int(round(time.time() * 1000)), "result": str(e)}))

        ### 判断状态进行处理
        if ret == 0:
            try:
                for i in sub.stdout.readlines():
                    result = i.decode('utf-8')
                    if result.replace('\n', ''):
                        redis_conn.publish("task_log", json.dumps(
                            {"log_key": log_key, "exec_time": int(round(time.time() * 1000)), "result": result}))
            except Exception as e:
                redis_conn.publish("task_log", json.dumps(
                    {"log_key": log_key, "exec_time": int(round(time.time() * 1000)), "result": str(e)}))
            sub.communicate()
            break
        elif ret is None:
            if duration >= exec_timeout:
                sub.terminate()
                sub.wait()
                sub.communicate()
                redis_conn.publish("task_log", json.dumps(
                    {"log_key": log_key, "exec_time": int(round(time.time() * 1000)),
                     "result": "execute timeout, execute time {}, it's killed.".format(duration)}))

                break
        else:
            out, err = sub.communicate()
            try:
                result = err.decode('utf-8').replace('\n', '')
            except Exception as e:
                result = str(e)

            redis_conn.publish("task_log", json.dumps(
                {"log_key": log_key, "exec_time": int(round(time.time() * 1000)), "result": result}))
            break
    return ret


def convert(data):
    if isinstance(data, bytes):  return data.decode('utf8')
    if isinstance(data, dict):   return dict(map(convert, data.items()))
    if isinstance(data, tuple):  return map(convert, data)
    return data


class MyExecute:
    def __init__(self, flow_id, group_id, all_exec_ip, all_args_info, exec_user_dict, level_list, redis_conn):
        self.flow_id = str(flow_id)
        self.group_id = group_id
        self.all_exec_ip = all_exec_ip
        self.all_args_info = all_args_info
        self.exec_user_dict = exec_user_dict
        self.redis_conn = redis_conn
        self.level_list = level_list

    ### 检查之前的执行组状态
    def check_group(self, gid='before'):
        if gid == 'before':
            ### 检查之前组
            with DBContext('r') as session:
                status_list = session.query(TaskSched.task_status).filter(TaskSched.list_id == self.flow_id,
                                                                          TaskSched.task_group < self.group_id).all()
        else:
            ### 检查之前组
            with DBContext('r') as session:
                status_list = session.query(TaskSched.task_status).filter(TaskSched.list_id == self.flow_id).all()

        for i in status_list:
            if i[0] != '3':
                return '4'
        return '3'

    ### 变更订单状态
    def change_list(self):
        status_list = []
        with DBContext('r') as session:
            status = session.query(TaskSched.task_status).filter(TaskSched.list_id == self.flow_id).all()
        for s in status:
            status_list.append(s[0])
        if '0' in status_list:
            status = '0'
        if '1' in status_list:
            status = '1'
        if '2' in status_list:
            status = '2'
        if '7' in status_list:
            status = '7'
        if '5' in status_list and '1' not in status_list and '2' not in status_list:
            status = '5'
        if '6' in status_list:
            status = '6'
        if '4' in status_list:
            status = '4'
        if '3' in status_list and len(list(set(status_list))) == 1:
            status = '3'
        with DBContext('w') as session:
            session.query(TaskList).filter(TaskList.list_id == self.flow_id).update({TaskList.status: status})
            session.commit()

    ### 解析参数
    def resolve_args(self, args, log_key):
        args_list = []
        all_args = ''

        if args:
            param_list = args.split(' ')
            for p in param_list:
                try:
                    par_l = str(self.all_args_info.get(p, p)).strip()
                except Exception as e:
                    self.redis_conn.publish("task_log", json.dumps(
                        {"log_key": log_key, "exec_time": int(round(time.time() * 1000)), "result": str(e)}))
                    return args
                if type(par_l) == "unicode":
                    par_l = par_l.encode('utf-8')
                args_list.append(par_l)
            all_args = ' '.join(args_list)
            ###解析FLOW_ID
            all_args = all_args.replace('FLOW_ID', self.flow_id)
            return all_args
        else:
            return all_args

    ### 执行任务函数
    def exec_task(self, **info):
        if info.get('force_host'):
            real_host = info.get('force_host', '')
        else:
            real_host = info.get('exec_ip', '')

        my_cmd = info.get('task_cmd', '') + ' ' + info.get('task_args', '')
        log_key = info.get("log_key", '111')

        ### 判断是否是要在本地操作
        if real_host == "127.0.0.1":
            real_cmd = my_cmd
        else:
            ### 别名具有唯一性
            alias_user = info.get("exec_user")
            exec_user = self.exec_user_dict.get(alias_user)
            ssh_port = self.exec_user_dict.get(alias_user + "port")
            key_file = "/home/.ssh_key/{}_key".format(alias_user)
            real_cmd = "ssh -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o ServerAliveInterval=60 -o ConnectTimeout=5" \
                       " -i {} -p {} {}@{} '{}'".format(key_file, ssh_port, exec_user, real_host, my_cmd)

        try:
            status = exec_shell(log_key, real_cmd, my_cmd, self.redis_conn)
            if status is not 0:
                status = 4
        except Exception as e:
            self.redis_conn.publish("task_log", json.dumps(
                {"log_key": log_key, "exec_time": int(round(time.time() * 1000)), "result": str(e)}))
            status = -1

        if status == 0:
            real_status = '3'
        else:
            real_status = '4'
        return real_status

    ### 任务调度函数
    ### 任务组按顺序触发，任务按预设触发，默认顺序执行
    def exec_main(self, ip):
        level_status = {}
        int_sleep = 0
        hash_key = "task_{}_{}_{}".format(self.flow_id, self.group_id, ip)
        while True:
            ### 挂起的任务设置休眠时间
            print('list-{0} group-{1} {2} sleep after {3}s {4}'.format(self.flow_id, self.group_id, ip, int_sleep,
                                                                       datetime.datetime.now()))

            time.sleep(int_sleep)
            int_sleep += 5
            if int_sleep > 20:
                int_sleep = 20

            ### 检查订单状态 如果全部都完成就退出
            if self.check_group('all') == '3':
                with DBContext('w') as session:
                    session.query(TaskList).filter(TaskList.list_id == self.flow_id).update({TaskList.schedule: 'OK'})
                    session.commit()
                break

            ### 如果之前执行组都成功，任务正式开始
            if self.check_group() == '3':
                if not level_status:
                    for i in self.level_list:
                        log_key = "{}_{}_{}_{}".format(self.flow_id, self.group_id, i, ip)
                        level_status_key = "level_status_{}".format(log_key)
                        level_status[i] = self.redis_conn.get(level_status_key)
                    self.redis_conn.hmset(hash_key, level_status)
                    self.redis_conn.expire(hash_key, 2592000)

                for i in self.level_list:
                    log_key = "{}_{}_{}_{}".format(self.flow_id, self.group_id, i, ip)
                    task_info_key = "task_info_{}".format(log_key)
                    task_cmd_info = convert(self.redis_conn.hgetall(task_info_key))

                    exec_info = dict(task_level=i, task_name=task_cmd_info.get('task_name'), log_key=log_key,
                                     task_cmd=task_cmd_info.get('task_cmd'), exec_user=task_cmd_info.get('exec_user'),
                                     task_args=self.resolve_args(task_cmd_info.get('task_args'), log_key),
                                     force_host=task_cmd_info.get('force_host'), exec_ip=task_cmd_info.get('exec_ip'))

                    status_list = self.redis_conn.hvals(hash_key)

                    this_status = self.redis_conn.hget(hash_key, i)
                    print('组：', self.group_id, '优先级', i, status_list, this_status)
                    ### 当前的状态如是为手动干预，中断,或 包含错误状态 则跳出循环
                    if b'5' == this_status or b'6' == this_status or b'4' in status_list:
                        break

                    ### 定时任务则判断是否可以开始,如果可以开始则修改缓存数据
                    if b'7' == this_status:
                        start_time = self.redis_conn.get('task_id_{}_start_time'.format(self.flow_id))
                        if time.mktime(datetime.datetime.now().timetuple()) > float(start_time.decode('utf8')):
                            self.redis_conn.hset(hash_key, i, '1')
                            this_status = b'1'
                        else:
                            break

                    ### 当前状态为等待执行和当前执行队列没有失败
                    if this_status == b'1' and b'4' not in status_list:
                        ### 修改状态为运行中
                        with DBContext('w') as session:
                            session.query(TaskSched).filter(TaskSched.list_id == self.flow_id,
                                                            TaskSched.task_group == self.group_id,
                                                            TaskSched.task_level == exec_info['task_level'],
                                                            TaskSched.exec_ip == exec_info['exec_ip']).update(
                                {TaskSched.task_status: '2'})
                            session.commit()
                        self.redis_conn.hset(hash_key, i, '2')

                        ### 执行任务
                        recode = self.exec_task(**exec_info)
                        ### 修改运行后的状态
                        with DBContext('w') as session:
                            session.query(TaskSched).filter(TaskSched.list_id == self.flow_id,
                                                            TaskSched.task_group == self.group_id,
                                                            TaskSched.task_level == exec_info['task_level'],
                                                            TaskSched.exec_ip == exec_info['exec_ip']).update(
                                {TaskSched.task_status: recode})
                            session.commit()
                        self.redis_conn.hset(hash_key, i, recode)
                        self.change_list()
                        int_sleep = 0
                        break

    def exec_thread(self):
        threads = []
        for ip in self.all_exec_ip.split(','):
            if ip:
                threads.append(multiprocessing.Process(target=self.exec_main, args=(ip,)))
        print("current has {0} threads task list-{1} group-{2}".format(len(threads), self.flow_id, self.group_id))
        ###开始多进程程
        for start_t in threads:
            try:
                start_t.start()
            except UnboundLocalError:
                print('error')
        ###阻塞
        for join_t in threads:
            join_t.join()

    # def exec_thread_new(self):
    #     ### 取所有主机 最多启动100个进程
    #     pool_num = len(self.all_exec_ip.split(','))
    #     if pool_num > 100:
    #         pool_num = 100
    #     with Pool(max_workers=pool_num) as executor:
    #         future_tasks = [executor.submit(self.exec_main, the_ip) for the_ip in self.all_exec_ip.split(',')]
    #
    #     results = wait(future_tasks)
    #     print(results)
    #     print('主线程')
    #
    #     print('pool_num: {0} {1} task list-{2} group-{3}'.format(pool_num, 'xx', self.flow_id, self.group_id))


if __name__ == "__main__":
    pass
