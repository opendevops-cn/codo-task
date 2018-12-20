```
###组件栈
- python3.6
- tornado5.0
- MySQL.7
- Redis3.2
```

### 中间件变量
```bash
MYSQL_PASSWORD="init1234567"
REDIS_PASSWORD="init1234567"
MQ_USER="sz"
MQ_PASSWORD="init1234567"
```

### 基础环境python3
```bash
[ -f /usr/local/bin/python3 ] && echo "Python3 already exists" && exit -1
yum groupinstall Development tools -y
yum -y install zlib-devel
yum install -y python36-devel-3.6.3-7.el7.x86_64 openssl-devel libxslt-devel libxml2-devel libcurl-devel
cd /usr/local/src/
wget -q -c https://www.python.org/ftp/python/3.6.4/Python-3.6.4.tar.xz
tar xf  Python-3.6.4.tar.xz >/dev/null 2>&1 && cd Python-3.6.4
./configure >/dev/null 2>&1
make >/dev/null 2>&1 && make install >/dev/null 2>&1
if [ $? == 0 ];then
    echo "[安装python3] ==> OK"
else
    echo "[安装python3] ==> Faild"
    exit -1
fi
```
### docker docker-compose 安装
```bash
yum install -y yum-utils device-mapper-persistent-data lvm2
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum-config-manager --enable docker-ce-edge
yum install -y docker-ce
###启动
/bin/systemctl start docker.service
### 开机自启
/bin/systemctl enable docker.service
#安装docker-compose编排工具
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
pip3 install docker-compose
```
### 安装MySQL
```bash
# yum install -y yum-utils device-mapper-persistent-data lvm2 mysql
# yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
# yum-config-manager --enable docker-ce-edge
# yum install -y docker-ce
###启动
# /bin/systemctl start docker.service
# 安装docker-compose编排工具
# curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py
# pip3 install docker-compose

#编写mysql docker-compose.yml
cat >docker-compose.yml <<EOF
mysql:
  restart: unless-stopped
  image: mysql:5.7
  volumes:
    - /data/mysql:/var/lib/mysql
    - /data/mysql_conf:/etc/mysql/conf.d
  ports:
    - "3306:3306"
  environment:
    - MYSQL_ROOT_PASSWORD=${MYSQL_PASSWORD}
EOF

#启动mysql容器（在docker-compose.yml同级目录）
docker-compose up -d
echo  "mysql -h 127.0.0.1 -u root -p ${MYSQL_PASSWORD}"
```
### 安装 Redis
```bash
function init_redis()
{
    echo "Start init redis"
    ### 开启AOF
    sed -i 's#appendonly no$#appendonly yes#g' /etc/redis.conf
    ### 操作系统决定
    sed -i 's#appendfsync .*$$#appendfsync everysec$#g' /etc/redis.conf
    ### 修改绑定IP
    sed -i 's/^bind 127.0.0.1$/#bind 127.0.0.1/g' /etc/redis.conf
    ### 是否以守护进程方式启动
    sed -i 's#daemonize no$#daemonize yes#g' /etc/redis.conf
    ### 当时间间隔超过60秒，或存储超过1000条记录时，进行持久化
    sed -i 's#^save 60 .*$#save 60 1000#g' /etc/redis.conf
    ### 快照压缩
    sed -i 's#rdbcompression no$#rdbcompression yes#g' /etc/redis.conf
    ### 添加密码
    sed -i "s#.*requirepass .*#requirepass ${REDIS_PASSWORD}#g" /etc/redis.conf
    echo "Start init redis end, must restart redis !!!"
}

[ -f /usr/bin/redis-server ] && echo "redis already exists" && init_redis && exit 0
echo "Start install redis server "
yum -y install redis-3.2.*

init_redis
systemctl restart redis
systemctl status redis

if [ $? == 0 ]; then
        echo "install successful"
else
        echo "install error" && exit -2
fi
```
### 安装 RabbitMQ
```bash
yum install  -y rabbitmq-server
rabbitmq-plugins enable rabbitmq_management
rabbitmqctl add_user ${MQ_USER} ${MQ_PASSWORD}
rabbitmqctl set_user_tags ${MQ_USER} administrator
rabbitmqctl  set_permissions  -p  '/'  ${MQ_USER} '.' '.' '.'
systemctl restart rabbitmq-server
systemctl enable rabbitmq-server
```
### 中间件安装完毕，注意用户名密码非实际用户名密码
### 此处导入mysql 数据
```bash
mysql -h 127.0.0.1 -u root -p ${MYSQL_PASSWORD} -e "create database zhi default character set utf8mb4 collate utf8mb4_unicode_ci;"
mysql -h 127.0.0.1 -u root -p ${MYSQL_PASSWORD} < doc/dump.sql
```
### 项目变量 此处变量应为实际项目的真是配置，如果想使用集群 请自行配置中间件集群
```bash
# 域名
export DOMAIN_NAME="http://aaaa.shinezone.net.cn"
# 端口
export PROJECT_PORT=8888
# 写数据库
export DEFAULT_DB_DBHOST="172.16.0.223"
export DEFAULT_DB_DBPORT='3306'
export DEFAULT_DB_DBUSER='root'
export DEFAULT_DB_DBPWD='ljXrcyn7chaBU4F'
export DEFAULT_DB_DBNAME='zhi'
# 读数据库
export READONLY_DB_DBHOST='172.16.0.223'
export READONLY_DB_DBPORT='3306'
export READONLY_DB_DBUSER='root'
export READONLY_DB_DBPWD='ljXrcyn7chaBU4F'
export READONLY_DB_DBNAME='zhi'
# 消息队列
export DEFAULT_MQ_ADDR='172.16.0.223'
export DEFAULT_MQ_USER='yz'
export DEFAULT_MQ_PWD='vuz84B2IkbEtXWF'
# 缓存
export DEFAULT_REDIS_HOST='172.16.0.223'
export DEFAULT_REDIS_PORT=6379
export DEFAULT_REDIS_PASSWORD='123456'
```

### 使用docker部署服务   可以多主机分布式部署 使用nginx 代理API  任务执行程序通过消息队列分布扩展，定时任务只能起一个进程
- cd 项目目录
- doc/supervisor_ops.conf 进程数量
- 项目配置文件 settings.py
```bash
sed -i "s#\tserver_name .*#\tserver_name ${DOMAIN_NAME};#g" doc/nginx_ops.conf
docker build . -t devops_image
cat >docker-compose.yml <<EOF
auto_ops:
  restart: unless-stopped
  image: devops_image
  volumes:
    - /var/log/supervisor/:/var/log/supervisor/
    - /root/ops_scripts/:/root/ops_scripts/
    - /var/www/aaa_ops/:/var/www/aaa_ops/
    - /sys/fs/cgroup:/sys/fs/cgroup
  ports:
    - "${PROJECT_PORT}:80"
  environment:
    - DOMAIN_NAME=${DOMAIN_NAME}
    - PROJECT_PORT=${PROJECT_PORT}
    - DEFAULT_DB_DBHOST=${DEFAULT_DB_DBHOST}
    - DEFAULT_DB_DBPORT=${DEFAULT_DB_DBPORT}
    - DEFAULT_DB_DBUSER=${DEFAULT_DB_DBUSER}
    - DEFAULT_DB_DBPWD=${DEFAULT_DB_DBPWD}
    - DEFAULT_DB_DBNAME=${DEFAULT_DB_DBNAME}
    - READONLY_DB_DBHOST=${READONLY_DB_DBHOST}
    - READONLY_DB_DBPORT=${READONLY_DB_DBPORT}
    - READONLY_DB_DBUSER=${READONLY_DB_DBUSER}
    - READONLY_DB_DBPWD=${READONLY_DB_DBPWD}
    - READONLY_DB_DBNAME=${READONLY_DB_DBNAME}
    - DEFAULT_MQ_ADDR=${DEFAULT_MQ_ADDR}
    - DEFAULT_MQ_USER=${DEFAULT_MQ_USER}
    - DEFAULT_MQ_PWD=${DEFAULT_MQ_PWD}
    - DEFAULT_REDIS_HOST=${DEFAULT_REDIS_HOST}
    - DEFAULT_REDIS_PORT=${DEFAULT_REDIS_PORT}
    - DEFAULT_REDIS_PASSWORD=${DEFAULT_REDIS_PASSWORD}
  hostname: OPS-NW-aaa01-exec01
EOF
docker-compose up -d
```