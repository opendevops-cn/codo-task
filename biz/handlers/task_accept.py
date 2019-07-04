#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
Author : shenshuo
date   : 2017-11-11 12:48:43
role   : 接受任务API
"""

import re
import json
from ast import literal_eval
from websdk.mqhelper import MessageQueueBase
from libs.base_handler import BaseHandler
from websdk.db_context import DBContext
from models.scheduler import TaskList, TaskSched, TempDetails, TempList, TempToUser


def new_task(list_id, temp_id, *group_list):
    """根据订单和模板生成任务"""
    with DBContext('w', None, True) as session:
        ip_info = session.query(TaskList.hosts).filter(TaskList.list_id == list_id).first()

        for g in group_list:
            temp_info = session.query(TempDetails).filter(TempDetails.temp_id == temp_id, TempDetails.group == g).all()
            for ip in ip_info:
                gip = literal_eval(ip)[g].split(',')
                for i in gip:
                    for t in temp_info:
                        if t.trigger == 'timed':
                            task_status = '7'
                        elif t.trigger == 'hand':
                            task_status = '5'
                        else:
                            task_status = '1'
                        session.add(TaskSched(list_id=list_id, task_group=g, task_level=t.level,
                                              task_name=t.command_name, task_cmd=t.command, task_args=t.args,
                                              exec_user=t.exec_user, force_host=t.force_host, exec_ip=i,
                                              task_status=task_status))

    return 0


def create_task(**data_info):
    data = data_info
    ### 首先判断参数是否完整（temp_id，hosts,task_name,submitter）必填
    exec_time = data.get('exec_time', '2038-10-25 14:00:00')
    temp_id = str(data.get('temp_id'))
    task_name = data.get('task_name')
    task_type = data.get('task_type')
    submitter = data.get('submitter')  ### 应根据登录的用户
    associated_user = data.get('associated_user')  ###参与用户示例："associated_user": "{'group-1': ['杨铭威']}"
    executor = data.get('executor', '')  ### 审批人可以为空
    args = data.get('args', '{}')  ### 参数，可以为空
    hosts = data.get('hosts', '{}')  ### 执行主机，不能为空
    schedule = data.get('schedule', 'new')  ### 进度
    details = data.get('details', '')  ### 任务描述
    hosts = literal_eval(hosts)
    group_list = []
    temp_user = []
    hosts_dic = {}

    if not temp_id and not hosts and not task_name and not submitter:
        return dict(code=6, msg="必要参数缺失")

    ### 接受字符串类型的主机组
    for h in hosts.keys():
        hosts[int(h)] = hosts.pop(h)

    with DBContext('r') as session:
        all_group = session.query(TempDetails.group).filter(TempDetails.temp_id == temp_id).group_by(
            TempDetails.group).all()

        for g in all_group:
            g = g[0]
            group_list.append(g)
            host = hosts.get(g)
            if not host:
                return dict(code=-4, msg="The exec host cannot be empty")

            if len(host.split(',')) >100:
                return dict(code=-4, msg="Too many hosts, please execute in groups")

            for ip in host.split(','):
                if not re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', ip):
                    return dict(code=5, msg="ip格式有误")

            hosts_dic[g] = hosts.get(g, '')

        user_info = session.query(TempToUser.nickname).filter(TempToUser.temp_id == temp_id).all()
        for u in user_info:
            temp_user.append(u[0])

    if submitter not in temp_user:
        temp_user.append(submitter)  ### 需要把提交人也加入进去

    temp_user_info = dict(admin=temp_user)
    if associated_user:
        associated_user = literal_eval(associated_user)
        if type(associated_user).__name__ == 'dict':
            temp_user_info = str(dict(temp_user_info, **associated_user))
    else:
        temp_user_info = str(temp_user_info)

    if set(group_list).issubset(set(hosts.keys())):
        with DBContext('w', None, True) as session:
            if not task_type:
                temp_name = session.query(TempList.temp_name).filter(TempList.temp_id == temp_id).one()
                task_type = temp_name[0]
            new_list = TaskList(task_name=task_name, task_type=task_type, hosts=str(hosts_dic), args=args,
                                details=details, description='', creator=submitter, executor=executor, status='0',
                                associated_user=temp_user_info, schedule=schedule, temp_id=temp_id,
                                start_time=exec_time)
        session.add(new_list)
        session.commit()
        ### 最后生成任务，若没有接手和执行时间 等待接手和修改最终执行时间
        new_task(new_list.list_id, temp_id, *group_list)


        ### 发送消息 exchange, exchange_type, routing_key
        with MessageQueueBase('task_scheduler', 'direct', 'the_task_id') as save_paper_channel:
            save_paper_channel.publish_message(str(new_list.list_id))
        return dict(code=0, msg="Task creation success, ID：{}".format(new_list.list_id), list_id=new_list.list_id)
    else:
        return dict(code=-3, msg="Host groupings and template groupings mismatch")


class AcceptTaskHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.write(dict(code=0, msg='获取csrf_key成功', csrf_key=self.new_csrf_key))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        return_data = create_task(**data)
        return self.write(return_data)


accept_task_urls = [
    (r"/v2/task/accept/", AcceptTaskHandler)
]
if __name__ == "__main__":
    pass
