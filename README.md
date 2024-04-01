# IONET 自动运维脚本

## 概述

原有的 io.sh 脚本已经弃用，新的 io.py 脚本已经上线。新脚本支持通过 HTTP 服务接收 `device_name` 验证，提供了更方便的运维功能。

**请注意本脚本只在Ubuntu 22.04上测试成功，其它系统请自行测试。**

`io.py` 是一个用于自动化运维的 Python 脚本。 可以让你从此走上幸福美满的撸 io 生活。
你可以配合使用[大哥号服务](https://github.com/titafox/ionet_dage)，从前端获取到设备的device_name，然后通过http服务，让脚本自动处理设备的运维工作。
## 特点
- 自动处理 Docker 容器和镜像。
- 支持通过 HTTP 服务接收 `device_id` 验证。
- 提供手动运行、计划任务和 HTTP 服务触发三种模式。

## 骚操作
在所有的服务器上运行和部署后，使用以下代码可以实现批量重置，这只是一个例子，实际使用过程中，可以和你自己的运维平台结合，实现更便捷的运维工作：
```bash
#!/bin/bash

# IP 地址列表
ips=("192.168.10.1" "192.168.10.2" "192.168.10.3" "192.168.10.5" "192.168.10.6" 
     "192.168.10.7" "192.168.10.8" "192.168.10.9" "192.168.10.10" "192.168.10.12"
     "192.168.10.14")

# 遍历 IP 地址并以后台任务的方式运行 wget
for ip in "${ips[@]}"; do
    # 构建 URL
    url="http://${ip}:9700/?device_name=$(echo ${ip} | tr '.' '-')"

    # 使用 wget 访问 URL，并将输出重定向到 /dev/null
    wget -O /dev/null "${url}" &
done

# 等待所有后台 wget 任务完成
wait
```


## 安装
确保您的系统安装了 Python 3 和相关依赖。可以在 Linux 系统上通过以下命令安装 Python 3（如果尚未安装）：
为了大家安装简单，本代码不需要安装任何第三方库，直接用ubuntu 22.04自带的python3运行即可。


执行如下命令，一键安装：

```bash
bash <(wget -qO- -o- https://raw.githubusercontent.com/titafox/io.sh/main/io.sh)
```

## 人肉安装

### 配置
将 ionet 脚本放置在 /var/ionet 目录下。

确保脚本具有执行权限：

```bash
chmod +x /var/ionet/ionet.py
```
如果需要，修改脚本中的相关配置，如 USER_ID 和 IO_CONF 路径。


### 运行
脚本可以通过以下方式运行：

- 手动执行：直接在终端中运行 python3 /var/ionet/io.py。
- 作为守护进程：通过 systemd 服务运行。

#### 设置为 Systemd 服务
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
ExecStart=/usr/bin/python3 /var/ionet/io.py --http
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

日常你可以直接进行手动重置：
```bash
python3 /var/ionet/io.py
```

脚本支持以下命令行参数：
- --user_id 和 --device_id 作为可选参数。
特别是在新配置服务的时候，可以通过这两个参数来指定用户 ID 和设备 ID，2 个可以单独使用，也可以一起使用。
```bash
python3 /var/ionet/io.py --user_id=123 --device_id=456
```

- 使用 --http 参数启动 HTTP 服务，该服务在端口 9700 上运行，并等待 device_name 验证。
  然后在浏览器输入如： http://192.168.20.25:9700/?device_name=192-168-20-25

- 使用 --cron 参数执行计划任务模式，该模式会在脚本开始运行时添加随机延迟。


## 安全注意事项
请确保在合适的环境中运行该脚本，特别是当以 root 用户执行时，请了解相关安全风险。在启动 http 服务后，接受的是一个 get 的请求，并且没有任何的安全验证，所以请确保在安全的网络环境中使用。

建议为服务器和你的控制台之间设立安全通道，如 VPN、SSH 隧道、内网 建立堡垒机等，将服务与公网隔离。

## 许可
此项目采用 MIT 许可证。你可以随便搞。

## 鸣谢
该代码最初是由**亦度**分享了一个从配置读取配置的一个脚本得到的灵感。最初他定义了一个IO_CONF，我们保留了他。

