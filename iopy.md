# IONET 自动运维脚本

## 概述
`io.py` 是一个用于自动化运维的 Python 脚本。 可以让你从此走上幸福美满的撸 io 生活。
你可以配合使用大哥号服务，从前端获取到设备的device_id，然后通过http服务，让脚本自动处理设备的运维工作。
## 特点
- 自动处理 Docker 容器和镜像。
- 支持通过 HTTP 服务接收 `device_id` 验证。
- 提供手动运行、计划任务和 HTTP 服务触发三种模式。

## 安装
确保您的系统安装了 Python 3 和相关依赖。可以在 Linux 系统上通过以下命令安装 Python 3（如果尚未安装）：
为了大家安装简单，本代码不需要安装任何第三方库，直接用ubuntu 22.04自带的python3运行即可。

## 配置
将 ionet 脚本放置在 /var/ionet 目录下。

确保脚本具有执行权限：

```bash
chmod +x /var/ionet/ionet.py
```
如果需要，修改脚本中的相关配置，如 USER_ID 和 IO_CONF 路径。


## 运行
脚本可以通过以下方式运行：

- 手动执行：直接在终端中运行 python3 /var/ionet/io.py。
- 作为守护进程：通过 systemd 服务运行。

### 设置为 Systemd 服务
创建一个名为 ionet.service 的文件：
```bash
nano /etc/systemd/system/ionet.service
```
内容如下：
```ini
[Unit]
Description=IONET自动运维
After=network.target

[Service]
ExecStart=/usr/bin/python3 /var/ionet/io.py
User=root
Group=root
Restart=always

[Install]
WantedBy=multi-user.target
```
启动服务：
```bash
systemctl start ionet
systemctl enable ionet
```
查看服务状态：
```bash
systemctl status ionet
```

## 使用说明
脚本支持以下命令行参数：
- --user_id 和 --device_id 作为可选参数。
- 使用 --http 参数启动 HTTP 服务，该服务在端口 9700 上运行，并等待 device_name 验证。
  然后在浏览器输入如： http://192.168.20.25:9700/?device_name=192-168-20-25

- 使用 --cron 参数执行计划任务模式，该模式会在脚本开始运行时添加随机延迟。


## 安全注意事项
请确保在合适的环境中运行该脚本，特别是当以 root 用户执行时，请了解相关安全风险。在启动 http 服务后，接受的是一个 get 的请求，并且没有任何的安全验证，所以请确保在安全的网络环境中使用。

建议为服务器和你的控制台之间设立安全通道，如 VPN、SSH 隧道、内网访问等。将服务与公网隔离。

## 许可
此项目采用 MIT 许可证。你可以随便搞。

