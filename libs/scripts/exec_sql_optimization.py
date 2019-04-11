#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
author : shenshuo
date   : 2018年4月24日
desc   : 执行SQL优化
1. 更新生成配置   data: 2018年6月1日
2. 更新所有信息从参数获取  data 2019年4月10日

soar 安装
1 wget https://github.com/XiaoMi/soar/releases/download/0.9.0/soar.linux-amd64 -O soar
2 chmod a+x soar
3 mv soar /usr/bin/
"""

import fire
import json
import base64
import subprocess
from shortuuid import uuid


def get_conf_v3(dbname, db_info):
    """获取SQL配置生产配置文件"""
    conf_file = '/tmp/' + uuid() + '.ini'

    db_info = base64.b64decode(db_info)
    db_info = json.loads(bytes.decode(db_info))

    db_host, db_port, db_user, db_pwd = db_info.get('db_host'), db_info.get('3306'), db_info.get(
        'db_user'), db_info.get('db_pwd')

    with open(conf_file, 'w') as f:
        f.write("[sqladvisor]\n"
                "username={db_user}\n"
                "password={db_pwd}\n"
                "host={db_host}\n"
                "port={db_port}\n"
                "dbname={dbname}\n"
                .format(db_user=db_user, db_pwd=db_pwd, db_host=db_host, db_port=db_port, dbname=dbname))
    return conf_file, db_host


def exec_sqladvisor_v3(conf_file, sql_data):
    for s in sql_data.split(';'):
        if s:
            sub2 = subprocess.Popen('sqladvisor -f {} -q "{};" -v 1'.format(conf_file, s), shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = sub2.communicate()
            result = stdout.decode('utf-8').replace('\n\n', '\n')
            print(result)
        print("********\n")


def exec_soar_v1(db_info, sql_data, db_name, THE_WAY):
    db_info = base64.b64decode(db_info)
    db_info = json.loads(bytes.decode(db_info))
    sql_data = bytes.decode(sql_data)

    if db_info.get('db_env') == 'release' or db_info.get('db_env') == 'prd':
        soar_cmd = "soar -drop-test-temporary=false -online-dsn={}:{}@{}:{}/{}".format(db_info['db_user'],
                                                                                       db_info['db_pwd'],
                                                                                       db_info['db_host'],
                                                                                       db_info['db_port'],
                                                                                       db_name)
    else:
        soar_cmd = "soar -drop-test-temporary=false -test-dsn={}:{}@{}:{}/{}".format(db_info['db_user'],
                                                                                     db_info['db_pwd'],
                                                                                     db_info['db_host'],
                                                                                     db_info['db_port'],
                                                                                     db_name)

    if THE_WAY == 'score':
        # print('开始使用 soar 进行SQL评分，请确保工具的正确安装')
        cmd = 'echo "{}" | {}'.format(sql_data, soar_cmd)

    elif THE_WAY == 'prettify':
        # print('开始使用 soar 进行SQL美化，请确保工具的正确安装')
        cmd = 'echo "{}" | soar -report-type=pretty'.format(sql_data)

    elif THE_WAY == 'fingerprint':
        # print('开始使用 soar 进行SQL指纹，请确保工具的正确安装')
        cmd = 'echo "{}" | soar -report-type=fingerprint'.format(sql_data)

    elif THE_WAY == 'check':
        # print('开始使用 soar SQL语法检查，请确保工具的正确安装')
        cmd = 'echo "{}" | soar -only-syntax-check'.format(sql_data)
    else:
        cmd = 'echo "未知方法 请检查参数"'

    sub = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = sub.communicate()
    ret = sub.returncode

    if ret == 0:
        if THE_WAY == 'check':
            if not stdout:
                print('SQL语法检测通过')
            else:
                print(stdout.decode('utf-8'))
        else:
            print(stdout.decode('utf-8'))

    else:
        print(stdout.decode('utf-8'))


def main_v3(mysql_info, db_name, sql_data, THE_WAY):
    conf_file, db_host = get_conf_v3(db_name, mysql_info)
    sql_data = base64.b64decode(sql_data)
    if THE_WAY == 'index':
        ###开始使用SQLAdvisor进行索引优化
        exec_sqladvisor_v3(conf_file, bytes.decode(sql_data))
    else:
        exec_soar_v1(mysql_info, sql_data, db_name, THE_WAY)


if __name__ == '__main__':
    fire.Fire(main_v3)

### 例如
### python3.6 /tmp/codo-task/libs/scripts/exec_sql_optimization.py eyJpZCI6IDIsICJkYl9jb2RlIjogIlNTLVNaTlctdGVzdDAxLXNhbHQwMkRCIiwgImRiX2hvc3QiOiAiMTcyLjE2LjAuMjEyIiwgImRiX3BvcnQiOiAiMzMwNiIsICJkYl91c2VyIjogInJvb3QiLCAiZGJfcHdkIjogIjY2NjY2NiIsICJkYl9lbnYiOiAiZGV2IiwgInByb3h5X2hvc3QiOiAiMTcyLjE2LjAuMjMwIiwgImRiX3R5cGUiOiAibXlzcWwiLCAiZGJfbWFyayI6ICJcdTUxOTkiLCAiYWxsX2RicyI6IG51bGwsICJzdGF0ZSI6IG51bGx9 flowertown_0 c2VsZWN0ICogZnJvbSBzaGluZXpvbmUyOw==  index

### python3.6 /tmp/codo-task/libs/scripts/exec_sql_optimization.py eyJpZCI6IDIsICJkYl9jb2RlIjogIlNTLVNaTlctdGVzdDAxLXNhbHQwMkRCIiwgImRiX2hvc3QiOiAiMTcyLjE2LjAuMjEyIiwgImRiX3BvcnQiOiAiMzMwNiIsICJkYl91c2VyIjogInJvb3QiLCAiZGJfcHdkIjogIjY2NjY2NiIsICJkYl9lbnYiOiAiZGV2IiwgInByb3h5X2hvc3QiOiAiMTcyLjE2LjAuMjMwIiwgImRiX3R5cGUiOiAibXlzcWwiLCAiZGJfbWFyayI6ICJcdTUxOTkiLCAiYWxsX2RicyI6IG51bGwsICJzdGF0ZSI6IG51bGx9 flowertown_0 c2VsZWN0ICogZnJvbSBzaGluZXpvbmUyOw==  score