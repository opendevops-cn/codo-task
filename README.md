## 后端管理平台
[更新日志](https://github.com/ss1917/do_mg/releases)

[部署文档](https://github.com/ss1917/do_mg/tree/master/doc/deployment.md)

[在线访问]()

### 简介
&emsp;&emsp; do_mg是基于tornado框架 restful风格的API 实现后台管理，搭配使用admin-front前端([iView](https://www.iviewui.com)+ [vue](https://cn.vuejs.org/))组成的一套后台用户 权限以及系统管理的解决方案（提供登录，注册 密码修改 鉴权 用户管理 角色管理 权限管理 前端组件管理 前端路由管理 通知服务API 系统基础信息接口）
本项目为open-ops开源项目提供后台支持，也可以基于此项目基础项目开发自己的站点，更多基础功能还在不断开发中，如果想要查看更新动态，你可以到[更新日志](https://github.com/ss1917/do_mg/releases)查看最新更新，如果你是新手想快速部署，你可以去[部署文档](https://github.com/ss1917/do_mg/tree/master/doc/deployment.md) 查看  
### 功能

- 登录/登出 （支持谷歌动态码）

- 密码修改

- 鉴权 /权限刷新

- 用户管理   用户系统基于RBAC模型的

- 角色管理  

- 权限管理  （后端路由）基于角色

- 菜单管理（前端路由）基于角色

- 组件管理（前端组件）基于角色

- 通知管理 （提供发送短信，发送邮件API）

- 系统配置  

- 系统日志 （从API网关获取日志，当然也可以自行从基类获取）

  

### 结构

```shell
.
├── doc
│   ├── data.sql
│   ├── deployment.md
│   ├── nginx_ops.conf
│   ├── requirements.txt
│   └── supervisor_ops.conf
├── docker-compose.yml
├── Dockerfile
├── libs
│   ├── base_handler.py            重写基类
│   ├── mail_login.py              邮箱登录/需要用户自己定义
│   ├── my_verify.py               鉴权
├── mg
│   ├── applications.py            
│   ├── handlers
│   │   ├── app_mg_handler.py         系统相关
│   │   ├── components_handler.py     组件管理
│   │   ├── functions_handler.py      权限管理
│   │   ├── login_handler.py          登录/登出/获取菜单、组件
│   │   ├── menus_handler.py          菜单管理
│   │   ├── notifications_handler.py  通知管理
│   │   ├── roles_handler.py          角色管理
│   │   ├── users_handler.py          用户管理
│   │   └── verify_handler.py
│   └── subscribe.py                  日志接收
├── models
│   ├── admin.py                      ORM
├── README.md
├── settings.py                       配置
└── startup.py                        启动文件
```



### 展示
