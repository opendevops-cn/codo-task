## 任务系统

###  部署文档

> <font size="4" color="#dd0000">此系统尽量分布式安装</font> 

### 修改配置
- 对settings 里面的配置文件进行修改
- 修改 doc/nginx_ops.conf 的server_name  例如 改为 task.opendevops.cn
- 修改 doc/supervisor_ops.conf 内容来控制进程数量
### 编译镜像
```
docker build . -t task_scheduler_image
```
### docker 启动
> 此处要保证 变量正确
```bash
cat >docker-compose.yml <<EOF
task_scheduler:
  restart: unless-stopped
  image: task_scheduler_image
  volumes:
    - /var/log/supervisor/:/var/log/supervisor/
    - /var/www/task_scheduler:/var/www/task_scheduler/
    - /root/ops_scripts:/root/ops_scripts
    - /sys/fs/cgroup:/sys/fs/cgroup
  ports:
    - "8020:80"
  environment:
EOF
docker-compose up -d
```
#### 启动后访问地址为 task.opendevops.cn：8020 在API网关上注册，注册示例参考API网关
## License

Everything is [GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.html).
