#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Contact : 191715030@qq.com
Author  : shenshuo
Date    : 2019/4/25
Desc    : 
"""
import time, datetime, json, subprocess

exec_timeout = 30


def exec_shell(log_key, real_cmd, cmd):
    print("task_log", json.dumps(
        {"log_key": log_key, "exec_time": str(datetime.datetime.now()), "result": "[CMD]: {}".format(cmd)}))
    start_time = time.time()
    sub = subprocess.Popen(real_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        ret = subprocess.Popen.poll(sub)
        current_time = time.time()
        duration = current_time - start_time
        ### 处理输出
        try:
            result = sub.stdout.readline().decode('utf-8').replace('\n', '')
        except Exception as e:
            result = e
        if result:
            print("task_log", json.dumps(
                {"log_key": log_key, "exec_time": str(datetime.datetime.now()), "result": result}))

        ### 判断状态进行处理
        if ret == 0:
            try:
                result = sub.stdout.readline().decode('utf-8').replace('\n', '')
            except Exception as e:
                result = e
            if result:
                print("task_log",
                      json.dumps({"log_key": log_key, "exec_time": str(datetime.datetime.now()), "result": result}))

            sub.communicate()
            break
        elif ret is None:
            if duration >= exec_timeout:
                sub.terminate()
                sub.wait()
                sub.communicate()
                print("task_log", json.dumps(
                    {"log_key": log_key, "exec_time": str(datetime.datetime.now()),
                     "result": "execute timeout, execute time {}, it's killed.".format(duration)}))

                break
            # time.sleep(1)
        else:
            out, err = sub.communicate()
            try:
                result = err.decode('utf-8').replace('\n', '')
            except Exception as e:
                result = str(e)

            print("task_log",
                  json.dumps({"log_key": log_key, "exec_time": str(datetime.datetime.now()), "result": result}))
            break
    return ret


exec_shell('xxxxxx', 'ls', 'ls')
