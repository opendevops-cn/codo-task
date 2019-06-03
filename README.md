## 任务系统

###  部署文档

> <font size="4" color="#dd0000">此系统尽量分布式安装</font> 
#### 创建数据库
```sql
create database `do_task` default character set utf8mb4 collate utf8mb4_unicode_ci;
```

#### 修改配置
- 对settings 里面的配置文件进行修改，主要是数据库 缓存 消息队列
- 修改 doc/nginx_ops.conf 的server_name  例如 改为 task.opendevops.cn   可以不修改，只要在内部DNS可以解析到对应地址
- 修改 doc/supervisor_ops.conf 内容来控制任务并发数量  【exec_task】 默认10，建议根据服务器配置，和资源利用率进行修改

#### 编译镜像
```bash
docker build . -t codo_task_image
```
#### docker 启动
**此处要保证 变量正确**
```bash
docker-compose up -d
```
**初始化表结构**
```bash
docker exec -ti codo-task_codo-task_1  /usr/local/bin/python3 /var/www/codo-task/db_sync.py
```

#### 启动后访问地址为 task.opendevops.cn:8020 在API网关上注册，注册示例参考API网关
### 注册网关
> 参考[api网关](https://github.com/ss1917/api-gateway/blob/master/README.md)
## License

Everything is [GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.html).
