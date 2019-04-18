#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2019/3/19
Desc    : 对错误订单进行告警
"""

import datetime, time
from ast import literal_eval
from websdk.utils import SendSms, SendMail
from websdk.consts import const
from models.scheduler import TaskList, TaskMonitor
from websdk.configs import configs
from websdk.db_context import DBContext
from websdk.cache_context import cache_conn
from websdk.tools import convert, exec_shell


def send_alarm():
    with DBContext('r', None, False, **configs) as session:
        error_info = session.query(TaskList).filter(TaskList.schedule == 'start', TaskList.status == '4',
                                                    TaskList.start_time < datetime.datetime.now()).all()
        ### 查找出已经发出告警的订单
        old_warm = session.query(TaskMonitor).filter(TaskMonitor.call_status == 1).all()

    ### 没有错误订单则返回
    if not error_info:
        return

    old_warm_list = []
    error_list = []

    for o in old_warm:
        old_warm_list.append(o.list_id)

    old_warm_list = list(set(old_warm_list))

    with DBContext('w', None, True, **configs) as session:
        for i in error_info:
            error_list.append(int(i.list_id))
            if int(i.list_id) not in old_warm_list:
                print('The task-{0} is error'.format(i.list_id))
                call_info = 'ID-{} 任务-{} 类型-{}'.format(i.list_id, i.task_name[0:25], i.task_type[0:25])
                session.add(TaskMonitor(list_id=int(i.list_id), call_info=call_info, call_level=2,
                                        call_users=','.join(list(literal_eval(i.associated_user).values())[0]),
                                        call_status=0))

        ### 错误记录里面里面的订单已经修复
        for o in old_warm_list:
            if int(o) not in error_list:
                session.query(TaskMonitor).filter(TaskMonitor.list_id == int(o)).delete(synchronize_session=False)

        ### 删除报警记录
        session.query(TaskMonitor).filter(TaskMonitor.ctime < time.localtime(time.time() - 6000)).delete(
            synchronize_session=False)
        session.commit()

    time.sleep(1)
    ### 告警
    with DBContext('r', None, False, **configs) as session:
        my_call = session.query(TaskMonitor).filter(TaskMonitor.call_status == 0).all()
        ### 如果没有告警信息，则返回
        if not len(my_call):
            return

    redis_conn = cache_conn()
    cache_config_info = redis_conn.hgetall(const.APP_SETTINGS)
    if cache_config_info:
        config_info = convert(cache_config_info)
    else:
        config_info = configs['email_info']

    ### 禁用邮箱
    # sm = SendMail(mail_host=config_info.get(const.EMAIL_HOST), mail_port=config_info.get(const.EMAIL_PORT),
    #               mail_user=config_info.get(const.EMAIL_HOST_USER),
    #               mail_password=config_info.get(const.EMAIL_HOST_PASSWORD),
    #               mail_ssl=True if config_info.get(const.EMAIL_USE_SSL) == '1' else False)

    ### 发送短信实例化
    sms = SendSms(config_info.get(const.SMS_REGION), config_info.get(const.SMS_DOMAIN),
                  config_info.get(const.SMS_PRODUCT_NAME), config_info.get(const.SMS_ACCESS_KEY_ID),
                  config_info.get(const.SMS_ACCESS_KEY_SECRET))
    for i in my_call:
        sms_to_list = []
        email_to_list = []
        for user in i.call_users.split(','):
            info__contact = convert(redis_conn.hgetall(bytes(user + '__contact', encoding='utf-8')))
            if info__contact:
                sms_to_list.append(info__contact['tel'])
                email_to_list.append(info__contact['email'])
        print(sms_to_list, email_to_list, i.call_info)
        ### 发送邮件
        # sm.send_mail(",".join(email_to_list), '自动化订单', i.call_info)

        ### 以下为注释为单独报警的示例,具体根据自己的需求修改
        # import sys
        # sys.path.append(sys.path[0])
        # print(exec_shell('python3 alert.py {} {}'.format(",".join(sms_to_list), i.call_info)))

        ### 发送短信
        if sms_to_list:
            params = {"msg": i.call_info}  # 对应短信模板里设置的参数
            sms.send_sms(phone_numbers=",".join(sms_to_list), template_param=params,
                         sign_name=configs.get('sign_name')[0], template_code=configs.get('template_code')[0])

    ### 发送完禁用
    with DBContext('w', None, True, **configs) as session:
        session.query(TaskMonitor).filter(TaskMonitor.call_status == 0).update({TaskMonitor.call_status: 1})
        session.commit()

    return
