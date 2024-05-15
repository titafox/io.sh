#!/bin/bash

# 定义下载路径和服务文件路径
DOWNLOAD_URL="https://dshz.vip.cpolar.cn/ionet_cofig/io.py"
SCRIPT_PATH="/var/ionet/io.py"
SERVICE_FILE="/etc/systemd/system/ionet.service"

# 检查 Python3 是否安装
if ! command -v python3 &> /dev/null; then
    echo "Python3 未安装。请先安装 Python3。"
    exit 1
fi

# 创建脚本所在目录
echo "创建脚本目录..."
mkdir -p /var/ionet

# 从 GitHub 下载脚本
echo "下载脚本中..."
curl -L $DOWNLOAD_URL -o $SCRIPT_PATH

# 确保脚本可执行
chmod +x $SCRIPT_PATH

# 创建服务文件
echo "创建服务文件..."
echo "[Unit]
Description=IONET自动运维
After=network.target

[Service]
ExecStart=/usr/bin/python3 $SCRIPT_PATH --http
User=root
Group=root
Restart=always

[Install]
WantedBy=multi-user.target" | sudo tee $SERVICE_FILE

# 重新加载 systemd 管理器配置
echo "重新加载系统服务..."
sudo systemctl daemon-reload

# 启动并激活服务
echo "启动并激活 IONET 服务..."
sudo systemctl start ionet
sudo systemctl enable ionet

echo "IONET 服务安装完成。"
