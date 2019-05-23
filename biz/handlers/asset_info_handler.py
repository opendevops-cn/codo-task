#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2019/3/20
Desc    : 
"""

import json
from sqlalchemy import or_
from libs.base_handler import BaseHandler
from models.task_other import DB, DBTag, Tag, ServerTag, Server, ProxyInfo, model_to_dict
from websdk.db_context import DBContext


class DBHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default='888', strip=True)
        limit_start = (int(page_size) - 1) * int(limit)
        db_list = []
        with DBContext('r') as session:
            ### 通过TAG搜索
            if key == 'tag_name' and value:
                count = session.query(DB).outerjoin(DBTag, DB.id == DBTag.db_id).outerjoin(Tag, Tag.id ==
                                                                                           DBTag.tag_id).filter(
                    Tag.tag_name == value).count()
                db_info = session.query(DB).outerjoin(DBTag, DB.id == DBTag.db_id).outerjoin(Tag, Tag.id ==
                                                                                             DBTag.tag_id).filter(
                    Tag.tag_name == value).order_by(DB.id).offset(limit_start).limit(int(limit))
                for msg in db_info:
                    tag_list = []
                    data_dict = model_to_dict(msg)
                    data_dict['create_time'] = str(data_dict['create_time'])
                    db_tags = session.query(Tag.tag_name).outerjoin(DBTag, Tag.id == DBTag.tag_id).filter(
                        DBTag.db_id == data_dict['id']).all()
                    for t in db_tags:
                        tag_list.append(t[0])
                    data_dict['tag_list'] = tag_list
                    db_list.append(data_dict)
                return self.write(dict(code=0, msg='获取成功', count=count, data=db_list))

            ### 监听搜索
            if key and key != 'tag_name' and not value:
                count = session.query(DB).filter(or_(DB.db_code.like('%{}%'.format(key)),
                                                     DB.db_host.like('%{}%'.format(key)),
                                                     DB.proxy_host.like('%{}%'.format(key)),
                                                     DB.db_type.like('%{}%'.format(key)),
                                                     DB.db_mark.like('%{}%'.format(key)),
                                                     DB.state.like('%{}%'.format(key)),
                                                     DB.db_env.like('%{}%'.format(key)))).count()

                db_info = session.query(DB).filter(or_(DB.db_code.like('%{}%'.format(key)),
                                                       DB.db_host.like('%{}%'.format(key)),
                                                       DB.proxy_host.like('%{}%'.format(key)),
                                                       DB.db_type.like('%{}%'.format(key)),
                                                       DB.db_mark.like('%{}%'.format(key)),
                                                       DB.state.like('%{}%'.format(key)),
                                                       DB.db_env.like('%{}%'.format(key)))).order_by(DB.id).offset(
                    limit_start).limit(int(limit))

                for msg in db_info:
                    tag_list = []
                    data_dict = model_to_dict(msg)
                    data_dict['create_time'] = str(data_dict['create_time'])
                    db_tags = session.query(Tag.tag_name).outerjoin(DBTag, Tag.id == DBTag.tag_id).filter(
                        DBTag.db_id == data_dict['id']).all()
                    for t in db_tags:
                        tag_list.append(t[0])
                    data_dict['tag_list'] = tag_list
                    db_list.append(data_dict)

                return self.write(dict(code=0, msg='获取成功', count=count, data=db_list))

            ### 888查看所有的数据库
            if limit == '888':
                count = session.query(DB).count()
                db_info = session.query(DB).order_by(DB.id).all()
            else:
                if key and value:
                    count = session.query(DB).filter_by(**{key: value}).count()
                    db_info = session.query(DB).filter_by(**{key: value}).order_by(DB.id).offset(limit_start).limit(
                        int(limit))
                else:
                    count = session.query(DB).count()
                    db_info = session.query(DB).order_by(DB.id).offset(limit_start).limit(int(limit))

            for msg in db_info:
                tag_list = []
                data_dict = model_to_dict(msg)
                db_tags = session.query(Tag.tag_name).outerjoin(DBTag, Tag.id == DBTag.tag_id).filter(
                    DBTag.db_id == data_dict['id']).all()
                for t in db_tags:
                    tag_list.append(t[0])
                data_dict['create_time'] = str(data_dict['create_time'])
                data_dict['tag_list'] = tag_list
                db_list.append(data_dict)

        self.write(dict(code=0, msg='获取成功', count=count, data=db_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        db_code = data.get('db_code', None)
        db_host = data.get('db_host', None)
        db_port = data.get('db_port', 3306)
        db_user = data.get('db_user', None)
        db_pwd = data.get('db_pwd', None)
        db_env = data.get('db_env', None)
        proxy_host = data.get('proxy_host', None)
        db_type = data.get('db_type', 'mysql')
        db_mark = data.get('db_mark', '写')
        tag_list = data.get('tag_list', [])
        db_detail = data.get('db_detail', None)
        if not db_code or not db_host or not db_port or not db_user or not db_pwd or not db_env or not db_detail:
            return self.write(dict(code=-1, msg='关键参数不能为空'))

        with DBContext('r') as session:
            exist_id = session.query(DB.id).filter(DB.db_code == db_code, DB.db_host == db_host, DB.db_port == db_port,
                                                   DB.db_user == db_user, DB.db_env == db_env,
                                                   DB.proxy_host == proxy_host, DB.db_type == db_type,
                                                   DB.db_mark == db_mark).first()
        if exist_id:
            return self.write(dict(code=-2, msg='不要重复记录'))

        with DBContext('w', None, True) as session:
            new_db = DB(db_code=db_code, db_host=db_host, db_port=db_port, db_user=db_user, db_pwd=db_pwd,
                        db_env=db_env, proxy_host=proxy_host, db_type=db_type, db_mark=db_mark, db_detail=db_detail)
            session.add(new_db)

            all_tags = session.query(Tag.id).filter(Tag.tag_name.in_(tag_list)).order_by(Tag.id).all()
            if all_tags:
                for tag_id in all_tags:
                    session.add(DBTag(db_id=new_db.id, tag_id=tag_id[0]))

        return self.write(dict(code=0, msg='添加成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        db_id = data.get('id', None)
        db_code = data.get('db_code', None)
        db_host = data.get('db_host', None)
        db_port = data.get('db_port', 3306)
        db_user = data.get('db_user', None)
        db_pwd = data.get('db_pwd', None)
        db_env = data.get('db_env', None)
        proxy_host = data.get('proxy_host', None)
        db_type = data.get('db_type', 'mysql')
        db_mark = data.get('db_mark', '写')
        tag_list = data.get('tag_list', [])
        db_detail = data.get('db_detail', None)
        if not db_id or not db_code or not db_host or not db_port or not db_user or not db_pwd or not db_env or not db_detail:
            return self.write(dict(code=-1, msg='关键参数不能为空'))

        with DBContext('w', None, True) as session:
            all_tags = session.query(Tag.id).filter(Tag.tag_name.in_(tag_list)).order_by(Tag.id).all()
            session.query(DBTag).filter(DBTag.db_id == db_id).delete(synchronize_session=False)
            if all_tags:
                for tag_id in all_tags:
                    session.add(DBTag(db_id=int(db_id), tag_id=tag_id[0]))

            session.query(DB).filter(DB.id == int(db_id)).update({DB.db_code: db_code, DB.db_host: db_host,
                                                                  DB.db_port: db_port, DB.db_user: db_user,
                                                                  DB.db_pwd: db_pwd, DB.db_env: db_env,
                                                                  DB.proxy_host: proxy_host, DB.db_type: db_type,
                                                                  DB.db_mark: db_mark, DB.db_detail: db_detail})

        return self.write(dict(code=0, msg='编辑成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        db_id = data.get('db_id', None)
        id_list = data.get('id_list', None)

        with DBContext('w', None, True) as session:
            if db_id:
                session.query(DB).filter(DB.id == int(db_id)).delete(synchronize_session=False)
                session.query(DBTag).filter(DBTag.db_id == int(db_id)).delete(synchronize_session=False)
            elif id_list:
                for i in id_list:
                    session.query(DB).filter(DB.id == i).delete(synchronize_session=False)
                    session.query(DBTag).filter(DBTag.db_id == i).delete(synchronize_session=False)
            else:
                return self.write(dict(code=1, msg='关键参数不能为空'))
        return self.write(dict(code=0, msg='删除成功'))


class ServerHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default="888", strip=True)
        limit_start = (int(page_size) - 1) * int(limit)
        server_list = []
        with DBContext('r') as session:
            ### 通过TAG搜索
            if key == 'tag_name' and value:
                count = session.query(Server).outerjoin(ServerTag, Server.id == ServerTag.server_id
                                                        ).outerjoin(Tag, Tag.id == ServerTag.tag_id).filter(
                    Tag.tag_name == value).count()
                server_info = session.query(Server).outerjoin(ServerTag, Server.id == ServerTag.server_id
                                                              ).outerjoin(Tag, Tag.id == ServerTag.tag_id).filter(
                    Tag.tag_name == value).order_by(Server.id).offset(limit_start).limit(int(limit))

                for msg in server_info:
                    tag_list = []
                    data_dict = model_to_dict(msg)
                    data_dict['create_time'] = str(data_dict['create_time'])
                    db_tags = session.query(Tag.tag_name).outerjoin(ServerTag, Tag.id == ServerTag.tag_id).filter(
                        ServerTag.server_id == data_dict['id']).all()
                    for t in db_tags:
                        tag_list.append(t[0])
                    data_dict['tag_list'] = tag_list
                    server_list.append(data_dict)
                return self.write(dict(code=0, msg='获取成功', count=count, data=server_list))

            ### 监听搜索
            if key and key != 'tag_name' and not value:
                count = session.query(Server).filter(or_(Server.hostname.like('%{}%'.format(key)),
                                                         Server.ip.like('%{}%'.format(key)),
                                                         Server.state.like('%{}%'.format(key)))).count()
                server_info = session.query(Server).filter(or_(Server.hostname.like('%{}%'.format(key)),
                                                               Server.ip.like('%{}%'.format(key)),
                                                               Server.state.like('%{}%'.format(key)))).order_by(
                    Server.id).offset(limit_start).limit(int(limit))

                for msg in server_info:
                    tag_list = []
                    data_dict = model_to_dict(msg)
                    data_dict['create_time'] = str(data_dict['create_time'])
                    db_tags = session.query(Tag.tag_name).outerjoin(ServerTag, Tag.id == ServerTag.tag_id).filter(
                        ServerTag.server_id == data_dict['id']).all()
                    for t in db_tags:
                        tag_list.append(t[0])

                    data_dict['tag_list'] = tag_list
                    server_list.append(data_dict)

                return self.write(dict(code=0, msg='获取成功', count=count, data=server_list))

            if limit == "888":
                ### 888查看所有
                count = session.query(Server).count()
                server_info = session.query(Server).order_by(Server.id).all()
            else:
                ## 正常分页搜索
                if key and value:
                    count = session.query(Server).filter_by(**{key: value}).count()
                    server_info = session.query(Server).filter_by(**{key: value}).order_by(Server.id).offset(
                        limit_start).limit(int(limit))
                else:
                    count = session.query(Server).count()
                    server_info = session.query(Server).order_by(Server.id).offset(limit_start).limit(int(limit))

            for msg in server_info:
                tag_list = []
                data_dict = model_to_dict(msg)
                db_tags = session.query(Tag.tag_name).outerjoin(ServerTag, Tag.id == ServerTag.tag_id).filter(
                    ServerTag.server_id == data_dict['id']).all()
                for t in db_tags:
                    tag_list.append(t[0])
                data_dict['create_time'] = str(data_dict['create_time'])
                data_dict['tag_list'] = tag_list
                server_list.append(data_dict)

        self.write(dict(code=0, msg='获取成功', count=count, data=server_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        hostname = data.get('hostname', None)
        ip = data.get('ip', None)
        idc = data.get('idc', None)
        region = data.get('region', None)
        tag_list = data.get('tag_list', [])
        detail = data.get('detail', None)

        if not hostname or not ip:
            return self.write(dict(code=-1, msg='关键参数不能为空'))

        with DBContext('r') as session:
            exist_id = session.query(Server.id).filter(Server.hostname == hostname).first()
        if exist_id:
            return self.write(dict(code=-2, msg='不要重复记录'))

        with DBContext('w', None, True) as session:
            new_server = Server(hostname=hostname, ip=ip, idc=idc, region=region, detail=detail)
            session.add(new_server)

            all_tags = session.query(Tag.id).filter(Tag.tag_name.in_(tag_list)).order_by(Tag.id).all()
            if all_tags:
                for tag_id in all_tags:
                    session.add(ServerTag(server_id=new_server.id, tag_id=tag_id[0]))

        return self.write(dict(code=0, msg='添加成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        hostname = data.get('hostname', None)
        server_id = data.get('id', None)
        ip = data.get('ip', None)
        idc = data.get('idc', None)
        region = data.get('region', None)
        tag_list = data.get('tag_list', [])
        detail = data.get('detail', None)
        if not hostname or not ip:
            return self.write(dict(code=-1, msg='关键参数不能为空'))

        with DBContext('w', None, True) as session:
            exist_hostname = session.query(Server.hostname).filter(Server.id == server_id).first()
            if exist_hostname[0] != hostname:
                return self.write(dict(code=-2, msg='主机名不能修改'))

            session.query(ServerTag).filter(ServerTag.server_id == server_id).delete(synchronize_session=False)
            all_tags = session.query(Tag.id).filter(Tag.tag_name.in_(tag_list)).order_by(Tag.id).all()
            if all_tags:
                for tag_id in all_tags:
                    session.add(ServerTag(server_id=server_id, tag_id=tag_id[0]))

            session.query(Server).filter(Server.id == server_id).update({Server.hostname: hostname, Server.ip: ip,
                                                                         Server.idc: idc,
                                                                         Server.region: region, Server.detail: detail})

        return self.write(dict(code=0, msg='编辑成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        server_id = data.get('server_id', None)
        id_list = data.get('id_list', None)

        with DBContext('w', None, True) as session:
            if server_id:
                session.query(Server).filter(Server.id == server_id).delete(synchronize_session=False)
                session.query(ServerTag).filter(ServerTag.server_id == server_id).delete(synchronize_session=False)
            elif id_list:
                for i in id_list:
                    session.query(Server).filter(Server.id == i).delete(synchronize_session=False)
                    session.query(ServerTag).filter(ServerTag.server_id == i).delete(synchronize_session=False)
            else:
                return self.write(dict(code=1, msg='关键参数不能为空'))
        return self.write(dict(code=0, msg='删除成功'))


class TreeHandler(BaseHandler):
    def get(self, *args, **kwargs):
        _tree = [{
            "expand": True,
            "title": 'root',
            "children": [{
                "title": "server",
                "expand": False,
                "children": [
                ]
            }, {
                "title": 'DB',
                "expand": False,
                "children": []
            }]
        }]

        with DBContext('r') as session:
            db_tags = session.query(Tag).order_by(Tag.id).all()
            for msg in db_tags:
                db_dict = {}
                server_dict = {}
                data_dict = model_to_dict(msg)
                server_tags = session.query(ServerTag.id).outerjoin(Server, Server.id == ServerTag.server_id
                                                                    ).filter(ServerTag.tag_id == msg.id).all()
                server_dict['the_len'] = len(server_tags)
                server_dict['title'] = data_dict['tag_name'] + ' ({})'.format(len(server_tags))
                server_dict['tag_name'] = data_dict['tag_name']
                server_dict['node'] = 'server'
                _tree[0]["children"][0]['children'].append(server_dict)

                db_tags = session.query(DBTag.id).outerjoin(DB, DB.id == DBTag.db_id).filter(
                    DBTag.tag_id == msg.id).all()

                db_dict['the_len'] = len(db_tags)
                db_dict['tag_name'] = data_dict['tag_name']
                db_dict['node'] = 'DB'
                db_dict['title'] = data_dict['tag_name'] + ' ({})'.format(len(db_tags))
                _tree[0]["children"][1]['children'].append(db_dict)

        self.write(dict(code=0, msg='获取成功', data=_tree))


class TagAuthority(BaseHandler):
    def get(self, *args, **kwargs):
        nickname = self.get_current_nickname()
        tag_list = []

        with DBContext('r') as session:
            the_tags = session.query(Tag).order_by(Tag.id).all()

        for msg in the_tags:
            data_dict = model_to_dict(msg)
            data_dict.pop('create_time')
            if self.is_superuser:
                tag_list.append(data_dict)
            elif data_dict['users'] and nickname in data_dict['users'].split(','):
                tag_list.append(data_dict)
        return self.write(dict(code=0, msg='获取成功', data=tag_list))


class TAGHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default="888", strip=True)
        limit_start = (int(page_size) - 1) * int(limit)
        tag_list = []

        with DBContext('r') as session:
            if key == 'tag_name' and value:
                count = session.query(Tag).filter(Tag.tag_name.like('%{}%'.format(value))).count()
                all_tags = session.query(Tag).filter(Tag.tag_name.like('%{}%'.format(value))).order_by(Tag.id).offset(
                    limit_start).limit(int(limit))
            elif limit == '888':
                count = session.query(Tag).count()
                all_tags = session.query(Tag).order_by(Tag.id).all()
            elif key and key != 'tag_name' and value:
                count = session.query(Tag).filter_by(**{key: value}).count()
                all_tags = session.query(Tag).order_by(Tag.id).filter_by(**{key: value}).order_by(Tag.id).offset(
                    limit_start).limit(int(limit))
            else:
                count = session.query(Tag).count()
                all_tags = session.query(Tag).order_by(Tag.id).offset(limit_start).limit(int(limit))

            for msg in all_tags:
                db_list = []
                server_list = []
                data_dict = model_to_dict(msg)
                data_dict['create_time'] = str(data_dict['create_time'])
                if data_dict['users']:
                    data_dict['users'] = data_dict.get('users', '').split(',')
                else:
                    data_dict['users'] = []
                server_tags = session.query(ServerTag.id, Server.id).outerjoin(Server, Server.id == ServerTag.server_id
                                                                               ).filter(
                    ServerTag.tag_id == msg.id).all()
                for i in server_tags:
                    server_list.append(i[1])
                data_dict['servers'] = server_list
                data_dict['server_len'] = len(server_tags)

                db_tags = session.query(DBTag.id, DB.id, DB.db_code).outerjoin(DB, DB.id == DBTag.db_id).filter(
                    DBTag.tag_id == msg.id).all()
                for i in db_tags:
                    db_list.append(i[1])
                data_dict['db_len'] = len(db_tags)
                data_dict['dbs'] = db_list
                tag_list.append(data_dict)

        self.write(dict(code=0, msg='获取成功', count=count, data=tag_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        tag_name = data.get('tag_name')
        users = data.get('users')
        dbs = data.get('dbs')  ### ID列表
        servers = data.get('servers')  ### ID列表
        proxy_host = data.get('proxy_host', None)

        if not tag_name:
            return self.write(dict(code=-1, msg='标签名称不能为空'))

        with DBContext('r') as session:
            exist_id = session.query(Tag.id).filter(Tag.tag_name == tag_name).first()

        if exist_id:
            return self.write(dict(code=-2, msg='标签名称重复'))

        ### 判断是否存在
        with DBContext('w', None, True) as session:
            if users:
                users = ','.join(users)
            new_tag = Tag(tag_name=tag_name, users=users, proxy_host=proxy_host)
            session.add(new_tag)
            session.commit()
            if dbs:
                for db in dbs:
                    session.add(DBTag(db_id=int(db), tag_id=new_tag.id))
            if servers:
                for server in servers:
                    session.add(ServerTag(server_id=int(server), tag_id=new_tag.id))

        self.write(dict(code=0, msg='添加成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        tag_id = data.get('id')
        users = data.get('users')
        db_id_list = data.get('dbs')  ### ID列表
        server_id_list = data.get('servers')  ### ID列表
        proxy_host = data.get('proxy_host', None)

        with DBContext('w', None, True) as session:
            # if db_id_list:
            db_list, new_db_list, del_db_list = [], [], []
            in_db_tags = session.query(DB.id).outerjoin(DBTag, DBTag.db_id == DB.id).filter(
                DBTag.tag_id == tag_id).all()
            for i in in_db_tags:
                i = i[0]
                db_list.append(i)
                if i not in db_id_list:
                    del_db_list.append(i)
                    session.query(DBTag).filter(DBTag.db_id == i).delete(synchronize_session=False)

            for i in db_id_list:
                if i not in db_list:
                    session.add(DBTag(db_id=int(i), tag_id=tag_id))
                    new_db_list.append(i)

            # if server_id_list:
            server_list, new_server_list, del_server_list = [], [], []
            in_server_tags = session.query(Server.id).outerjoin(ServerTag, ServerTag.server_id == Server.id).filter(
                ServerTag.tag_id == tag_id).all()
            for i in in_server_tags:
                i = i[0]
                server_list.append(i)
                if i not in db_id_list:
                    del_server_list.append(i)
                    session.query(ServerTag).filter(ServerTag.server_id == i).delete(synchronize_session=False)

            for i in server_id_list:
                if i not in server_list:
                    session.add(ServerTag(server_id=int(i), tag_id=tag_id))
                    new_server_list.append(i)

            if users:
                users = ','.join(users)
            else:
                users = None
            session.query(Tag).filter(Tag.id == int(tag_id)).update({Tag.users: users, Tag.proxy_host: proxy_host})
            session.commit()

        self.write(dict(code=0, msg='修改成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        tag_id = data.get('tag_id')
        id_list = data.get('id_list')

        with DBContext('w', None, True) as session:
            if tag_id:
                session.query(Tag).filter(Tag.id == tag_id).delete(synchronize_session=False)
            elif id_list:
                for i in id_list:
                    session.query(Tag).filter(Tag.id == i).delete(synchronize_session=False)
            else:
                return self.write(dict(code=1, msg='关键参数不能为空'))
        self.write(dict(code=0, msg='删除成功'))


class ProxyHostHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        proxy_list = []
        with DBContext('r') as session:
            if key:
                proxy_info = session.query(ProxyInfo).filter(ProxyInfo.proxy_host == key).all()
            else:
                proxy_info = session.query(ProxyInfo).all()

        for msg in proxy_info:
            data_dict = model_to_dict(msg)
            proxy_list.append(data_dict)
        return self.write(dict(code=0, msg='获取成功', data=proxy_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        proxy_host = data.pop('proxy_host')
        detail = data.pop('detail')
        if not proxy_host or not detail:
            return self.write(dict(code=-1, msg='关键参数不能为空'))
        with DBContext('w', None, True) as session:
            session.add(ProxyInfo(proxy_host=proxy_host, detail=detail))

        self.write(dict(code=0, msg='添加代理完成，请完善相关信息'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        proxy_id = data.pop('id')
        edit_type = data.pop('edit_type')
        if not proxy_id or not edit_type:
            return self.write(dict(code=-1, msg='关键参数不能为空'))

        real_data = json.dumps(data)
        with DBContext('w', None, True) as session:
            if edit_type == 'inception':
                session.query(ProxyInfo).filter(ProxyInfo.id == proxy_id).update({ProxyInfo.inception: real_data})
            elif edit_type == 'salt':
                session.query(ProxyInfo).filter(ProxyInfo.id == proxy_id).update({ProxyInfo.salt: real_data})
            else:
                return self.write(dict(code=-2, msg='修改的类型超出范围'))

        self.write(dict(code=0, msg='修改完成'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        proxy_id = data.get('proxy_id')

        if not proxy_id:
            return self.write(dict(code=1, msg='关键参数不能为空'))

        with DBContext('w', None, True) as session:
            session.query(ProxyInfo).filter(ProxyInfo.id == proxy_id).delete(synchronize_session=False)

        self.write(dict(code=0, msg='删除成功'))


asset_info_urls = [
    (r"/other/v1/record/db/", DBHandler),
    (r"/other/v1/record/server/", ServerHandler),
    (r"/other/v1/record/tree/", TreeHandler),
    (r"/other/v1/record/tag/", TAGHandler),
    (r"/other/v1/record/tag_auth/", TagAuthority),
    (r"/other/v1/record/proxy/", ProxyHostHandler),
]
if __name__ == "__main__":
    pass
