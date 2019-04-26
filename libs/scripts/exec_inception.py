#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
author : shenshuo
date   : 2018年4月24日
role   ：执行SQL优化
python3 pymysql 连接Inception ，在判断版本时会出现value error 问题
修改 pymysql connections.py
def _request_authentication(self):
    # https://dev.mysql.com/doc/internals/en/connection-phase-packets.html#packet-Protocol::HandshakeResponse
    if self.server_version.split('.', 1)[0] == 'Inception2':
        self.client_flag |= CLIENT.MULTI_RESULTS
    elif int(self.server_version.split('.', 1)[0]) >= 5:
        self.client_flag |= CLIENT.MULTI_RESULTS
"""

import fire
import json
import base64
import subprocess
import warnings
import socket
import re
from shortuuid import uuid

warnings.filterwarnings('ignore')
import pymysql


def _is_ip(value):
    """检测是否是IP"""
    ipv4_re = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')
    if ipv4_re.match(value): return True


def conver_url2ip(db_host):
    '''RDS URL 解析成IP,不然host过长,导致inception无法备份'''
    if not _is_ip(db_host):
        old_host = db_host
        db_host = socket.gethostbyname(db_host)
        print('[HOST URL] %s ===> [IP]%s' % (old_host, db_host))
    return db_host


def get_conf(**db_info):
    """获取SQL配置生产配置文件"""
    db_info['db_host'] = conver_url2ip(db_info['db_host'])
    db_info['db_port'] = int(db_info['db_port'])
    db_info['charset'] = 'utf8mb4'
    return db_info


def sql_data_deal(exec_sql):
    sql_all = []
    for sql_line in exec_sql.split('\n'):
        ###删除# -- 开始的行并去除空行
        # sql_deal = re.sub(r'#.*$|--.*$', '', sql_line).strip()
        sql_deal = re.sub(r'^#.*$|--.*$', '', sql_line)
        sql_all.append(sql_deal)

    ###把列表拼接成字符串
    sql_in = ''
    if sql_all:
        sql_single = ''.join(sql_all)
        ###去掉/*  */的注释
        sql_in = re.sub(r'\/\*(.*?)\*\/', '', sql_single)

    real_data = ''
    ###按;分隔语句
    sql_arr = sql_in.split(';')
    for sql_one in sql_arr:
        if sql_one:
            real_data += '{};\n'.format(sql_one)

    return real_data


def exec_inception_v3(way, exec_sql, inception_info, **db_info):
    exec_sql = sql_data_deal(exec_sql)
    # 执行还是校验
    operation = '--enable-check'
    if way == 'check':
        operation = '--enable-check'
    elif way == 'run':
        operation = '--enable-execute;--enable-ignore-warnings;--enable-force'

    # operation = '--execute=1'
    # operation = '--enable-execute;--enable-ignore-warnings;--enable-force'

    # 发布目标服务器
    connstr_target = get_conf(**db_info)
    ### 审核服务器
    connstr_inception = json.loads(inception_info)
    try:
        # 将待执行的sql语句组合成inception识别的格式
        # inception_remote_system_password=1234567;
        # inception_remote_system_user=root;
        # inception_remote_backup_port=3306;
        # inception_remote_backup_host=172.16.0.230;
        sql_with_format = '''/*--user={};--password={};--host={};{};--port={};*/ inception_magic_start;\n {} \ninception_magic_commit;'''.format(
            connstr_target['db_user'],
            connstr_target['db_pwd'],
            connstr_target['db_host'],
            operation,
            connstr_target['db_port'], exec_sql)

        # 连接至inception 服务器
        conn_inception = pymysql.connect(host=connstr_inception.get('host', '127.0.0.1'),
                                         port=int(connstr_inception.get('port', 6669)),
                                         user=connstr_inception.get('user', ''),
                                         password=connstr_inception.get('password', ''),
                                         charset=connstr_inception.get('charset', 'utf8mb4'))

        cur = conn_inception.cursor()

        cur.execute(sql_with_format)
        result = cur.fetchall()
        num_fields = len(cur.description)
        field_names = [i[0] for i in cur.description]
        print(field_names)
        # 打印出来Inception对MySQL语句的审计结果
        result_code = []
        for row in result:
            print(row[0], "|", row[1], "|", row[2], "|", row[3], "|", row[4], "|", row[5], "|", row[6], "|", row[7],
                  "|", row[8], "|", row[9], "|", row[10])
            result_code.append(row[2])

        cur.close()
        conn_inception.close()
        print(result_code)
        ## errlevel：返回值为非0的情况下，说明是有错的。1表示警告，不影响执行，2表示严重错误，必须修改
        if 1 in result_code:
            print('host:{}  warning, please check the log !!!'.format(connstr_target['db_host']))
            if way == 'check':
                print('有警告，可能导致执行失败，检查的时候会报错退出，当然要是确定没问题的话可以越过 !!!')
                exit(-2)

        elif 2 in result_code:
            print('host:{}  error, please check the log !!!'.format(connstr_target['db_host']))
            exit(-1)
        else:
            print('host:{} success !!!'.format(connstr_target['db_host']))

    except  Exception as err:
        print(err)
        exit(-2)
    finally:
        print('********************\n\n')


def main_v3(way, mysql_info, sql_data, inception):
    if way == 'check':
        print('开始检查数据')
    elif way == 'run':
        print('开始执行数据')
    else:
        print('未知执行方法，请检查参数')
        exit(-1)

    mysql_info = base64.b64decode(mysql_info)
    inception = base64.b64decode(inception)
    sql_data = base64.b64decode(sql_data)

    for i in bytes.decode(mysql_info).split(',,,'):
        db_info = json.loads(i)
        print('当前数据库：{}--{}'.format(db_info['db_code'], db_info['db_host']))
        exec_inception_v3(way, bytes.decode(sql_data), bytes.decode(inception), **db_info)


if __name__ == '__main__':
    fire.Fire(main_v3)

###python3.6 /tmp/codo-task/libs/scripts/exec_inception.py check eyJpZCI6IDIsICJkYl9jb2RlIjogIlNTLVNaTlctdGVzdDAxLXNhbHQwMkRCIiwgImRiX2hvc3QiOiAiMTcyLjE2LjAuMjEyIiwgImRiX3BvcnQiOiAiMzMwNiIsICJkYl91c2VyIjogInJvb3QiLCAiZGJfcHdkIjogIjY2NjY2NiIsICJkYl9lbnYiOiAiZGV2IiwgInByb3h5X2hvc3QiOiAiMTcyLjE2LjAuMjMwIiwgImRiX3R5cGUiOiAibXlzcWwiLCAiZGJfbWFyayI6ICJcdTUxOTkiLCAiYWxsX2RicyI6IG51bGwsICJzdGF0ZSI6IG51bGx9LCwseyJpZCI6IDEsICJkYl9jb2RlIjogIk9QUy1TWk5XLTAxLVZlcnNpb25EQiIsICJkYl9ob3N0IjogIjE3Mi4xNi4wLjIzMCIsICJkYl9wb3J0IjogIjMzMDYiLCAiZGJfdXNlciI6ICJyb290IiwgImRiX3B3ZCI6ICIxMjM0NTY3IiwgImRiX2VudiI6ICJkZXYiLCAicHJveHlfaG9zdCI6ICIxNzIuMTYuMC4yMzAiLCAiZGJfdHlwZSI6ICJteXNxbCIsICJkYl9tYXJrIjogIlx1NTE5OSIsICJhbGxfZGJzIjogbnVsbCwgInN0YXRlIjogbnVsbH0= dXNlIGZsb3dlcnRvd25fMDsKaW5zZXJ0IGludG8gc2hpbmV6b25lMiB2YWx1ZSgxKTs= eyJob3N0IjogIjE3Mi4xNi4wLjIzMCIsICJwb3J0IjogIjY2NjkiLCAiYmFja19ob3N0IjogIjE3Mi4xNi4wLjIzMCIsICJiYWNrX3BvcnQiOiAiMzMwNiIsICJiYWNrX3VzZXIiOiAicm9vdCIsICJiYWNrX3B3ZCI6ICIxMjM0NTY3In0=
