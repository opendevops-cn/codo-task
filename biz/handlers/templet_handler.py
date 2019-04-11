#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
Author : shenshuo
date   : 2017年10月17日17:23:19
desc   : 任务调度模板管理
"""
import json, datetime
from libs.base_handler import BaseHandler
from websdk.db_context import DBContext
from websdk.base_handler import LivenessProbe
from models.scheduler import CommandList, TempList, TempDetails, ArgsList, TempToUser, ExecuteUser, model_to_dict


class CommandHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        cmd_list = []

        with DBContext('r') as session:
            if key and value:

                cmd_info = session.query(CommandList).filter_by(**{key: value}).order_by(CommandList.command_id).all()
            else:
                cmd_info = session.query(CommandList).order_by(CommandList.command_id).all()

        for msg in cmd_info:
            data_dict = model_to_dict(msg)
            data_dict['create_time'] = str(data_dict['create_time'])
            data_dict['update_time'] = str(data_dict['update_time'])
            cmd_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', data=cmd_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        command_name = data.get('command_name', None)
        command = data.get('command', None)
        args = data.get('args', None)
        force_host = data.get('force_host', None)
        if not command_name or not command:
            return self.write(dict(code=-1, msg='参数不能为空'))

        with DBContext('r') as session:
            cmd_info = session.query(CommandList.command_id).filter(CommandList.command_name == command_name).first()
        if cmd_info:
            return self.write(dict(code=-2, msg='名称不能重复'))

        with DBContext('w', None, True) as session:
            session.add(CommandList(command_name=command_name, command=command, args=args, force_host=force_host,
                                    creator=self.get_current_user()))

        return self.write(dict(code=0, msg='添加新命令成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        command_id = data.get('command_id', None)
        args = data.get('args', None)
        command = data.get('command', None)
        force_host = data.get('force_host', None)

        if not command_id:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(CommandList).filter(CommandList.command_id == command_id).update(
                {CommandList.command: command, CommandList.args: args, CommandList.force_host: force_host})
        return self.write(dict(code=0, msg='编辑成功,名称不能修改'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        command_id = data.get('command_id', None)
        if not command_id:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(CommandList).filter(CommandList.command_id == command_id).delete(synchronize_session=False)

        return self.write(dict(code=0, msg='删除成功'))


class ArgsHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        args_list = []

        with DBContext('r') as session:
            if key and value:
                args_info = session.query(ArgsList).filter_by(**{key: value}).order_by(ArgsList.args_id).all()
            else:
                args_info = session.query(ArgsList).order_by(ArgsList.args_id).all()

        for msg in args_info:
            data_dict = model_to_dict(msg)
            data_dict['update_time'] = str(data_dict['update_time'])
            args_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', data=args_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        args_name = data.get('args_name', None)
        args_self = data.get('args_self', None)
        if not args_name or not args_self:
            return self.write(dict(code=-1, msg='参数不能为空'))

        with DBContext('r') as session:
            args_exist = session.query(ArgsList.args_id).filter(ArgsList.args_name == args_name).first()
        if args_exist:
            return self.write(dict(code=-2, msg='名称不能重复'))

        with DBContext('w', None, True) as session:
            session.add(
                ArgsList(args_name=args_name, args_self=args_self, creator=self.get_current_user()))

        return self.write(dict(code=0, msg='添加成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        args_id = data.get('args_id', None)
        args_name = data.get('args_name', None)
        args_self = data.get('args_self', None)

        if not args_id or not args_self:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(ArgsList).filter(ArgsList.args_id == args_id).update({ArgsList.args_name: args_name,
                                                                                ArgsList.args_self: args_self})

        return self.write(dict(code=0, msg='编辑成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        args_id = data.get('args_id', None)
        if not args_id:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(ArgsList).filter(ArgsList.args_id == args_id).delete(synchronize_session=False)
        self.write(dict(code=0, msg='删除成功'))


class TemplateHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        temp_list = []

        with DBContext('r') as session:
            if key and value:
                temp_info = session.query(TempList).filter_by(**{key: value}).order_by(TempList.temp_id).all()
            else:
                temp_info = session.query(TempList).order_by(TempList.temp_id).all()

        for msg in temp_info:
            data_dict = model_to_dict(msg)
            data_dict.pop('create_time')
            data_dict.pop('update_time')
            temp_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', data=temp_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        temp_name = data.get('temp_name', None)
        if not temp_name:
            return self.write(dict(code=-1, msg='编排模板名称不能为空'))

        with DBContext('r') as session:
            info_exist = session.query(TempList.temp_id).filter(TempList.temp_name == temp_name).first()
        if info_exist:
            return self.write(dict(code=-2, msg='模板已存在'))

        with DBContext('w', None, True) as session:
            session.add(TempList(temp_name=temp_name, creator=self.get_current_user()))

        return self.write(dict(code=0, msg='模板创建成功，可以对此模板进行编辑了'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        temp_id = data.get('temp_id', None)
        if not temp_id:
            return self.write(dict(code=-1, msg='不能为空'))

        with DBContext('w', None, True) as session:
            session.query(TempList).filter(TempList.temp_id == temp_id).delete(synchronize_session=False)
        return self.write(dict(code=0, msg='删除成功'))


class TempDetailsHandler(BaseHandler):
    def get(self, *args, **kwargs):
        temp_id = self.get_argument('temp_id', default=None, strip=True)
        temp_list = []
        temp_user = []
        if not temp_id:
            return self.write(dict(code=-1, msg='模板ID不能为空'))

        with DBContext('r') as session:
            temp_info = session.query(TempDetails).filter(TempDetails.temp_id == temp_id).order_by(TempDetails.group,
                                                                                                   TempDetails.level).all()
            user_info = session.query(TempToUser).filter(TempToUser.temp_id == temp_id).all()

        for msg in temp_info:
            data_dict = model_to_dict(msg)
            data_dict.pop('update_time')
            temp_list.append(data_dict)

        for u in user_info:
            data_dict = model_to_dict(u)
            temp_user.append("{},,,{}".format(data_dict.get("user_id"), data_dict.get("nickname")))

        data_info = dict(temp_list=temp_list, temp_user=temp_user)

        return self.write(dict(code=0, msg='获取模板详情成功', data=data_info, temp_user=temp_user))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        new_temp_data = data.get('new_temp_data', None)
        temp_id = data.get('temp_id', None)

        if not temp_id:
            return self.write(dict(code=-1, msg='模板ID不能为空'))

        ### 先清空数据
        with DBContext('w', None, True) as session:
            session.query(TempDetails).filter(TempDetails.temp_id == str(temp_id)).delete(synchronize_session=False)

        if len(new_temp_data) < 1:
            return self.write(dict(code=0, msg='模板内容清空'))

        with DBContext('w', None, True) as session:
            for data_dict in new_temp_data:
                session.add(TempDetails(temp_id=temp_id, group=data_dict.get("group", 99),
                                        level=data_dict.get("level", 99),
                                        command_name=data_dict.get("command_name"),
                                        command=data_dict.get("command"), args=data_dict.get("args", ""),
                                        trigger=data_dict.get('trigger', 'order'),
                                        exec_user=str(data_dict.get('exec_user', 'root')),
                                        force_host=data_dict.get("force_host", ""),
                                        creator=self.get_current_user()))
        return self.write(dict(code=0, msg='修改成功'))

    def patch(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))

        new_user_info = data.get('new_user_info', None)
        temp_id = data.get('temp_id', None)

        ### 先清空数据
        with DBContext('w', None, True) as session:
            session.query(TempToUser).filter(TempToUser.temp_id == str(temp_id)).delete(synchronize_session=False)

        with DBContext('w', None, True) as session:
            for user_info in new_user_info:
                user_id = user_info.split(",,,")[0]
                nickname = user_info.split(",,,")[1]
                session.add(TempToUser(temp_id=temp_id, user_id=user_id, nickname=nickname))
        return self.write(dict(code=0, msg='修改成功'))


class ExecutiveUserHandler(BaseHandler):
    def get(self, *args, **kwargs):
        user_list = []

        with DBContext('r') as session:
            args_info = session.query(ExecuteUser).order_by(ExecuteUser.id).all()

        for msg in args_info:
            data_dict = model_to_dict(msg)
            data_dict['update_time'] = str(data_dict['update_time'])
            user_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', data=user_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        alias_user = data.get('alias_user', None)
        exec_user = data.get('exec_user', None)
        ssh_port = data.get('ssh_port', None)
        user_key = data.get('user_key', None)
        remarks = data.get('remarks', None)

        if not alias_user or not exec_user or not ssh_port or not user_key:
            return self.write(dict(code=-1, msg='参数不能为空'))

        if check_contain_chinese(alias_user):
            return self.write(dict(code=-1, msg='名称不能有汉字'))

        if check_contain_chinese(exec_user):
            return self.write(dict(code=-1, msg='名称不能有汉字'))

        with DBContext('r') as session:
            alias_exist = session.query(ExecuteUser.id).filter(ExecuteUser.alias_user == alias_user).first()

        if alias_exist:
            return self.write(dict(code=-2, msg='名称不能重复'))

        with DBContext('w', None, True) as session:
            session.add(ExecuteUser(alias_user=alias_user, exec_user=exec_user, ssh_port=ssh_port, user_key=user_key,
                                    remarks=remarks))
        return self.write(dict(code=0, msg='添加成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        exec_user_id = data.get('id', None)
        alias_user = data.get('alias_user', None)
        exec_user = data.get('exec_user', None)
        ssh_port = data.get('ssh_port', None)
        user_key = data.get('user_key', None)
        remarks = data.get('remarks', None)

        if not exec_user or not user_key:
            return self.write(dict(code=-1, msg='不能为空'))

        if check_contain_chinese(alias_user):
            return self.write(dict(code=-1, msg='名称不能有汉字'))

        if check_contain_chinese(exec_user):
            return self.write(dict(code=-1, msg='名称不能有汉字'))


        with DBContext('w', None, True) as session:
            session.query(ExecuteUser).filter(ExecuteUser.id == exec_user_id).update({ExecuteUser.exec_user: exec_user,
                                                                                      ExecuteUser.ssh_port: ssh_port,
                                                                                      ExecuteUser.user_key: user_key,
                                                                                      ExecuteUser.remarks: remarks})

        return self.write(dict(code=0, msg='编辑成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        exec_user_id = data.get('exec_user_id', None)
        if not exec_user_id:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(ExecuteUser).filter(ExecuteUser.id == exec_user_id).delete(synchronize_session=False)
        self.write(dict(code=0, msg='删除成功'))


def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

temp_urls = [
    (r"/v2/task_layout/command/", CommandHandler),
    (r"/v2/task_layout/temp/", TemplateHandler),
    (r"/v2/task_layout/details/", TempDetailsHandler),
    (r"/v2/task_layout/args/", ArgsHandler),
    (r"/v2/task_layout/user/", ExecutiveUserHandler),
    (r"/are_you_ok/", LivenessProbe),
]

if __name__ == "__main__":
    pass
