#!/bin/bash

# 检查是否提供了 key 参数
if [ -z "$1" ]; then
  echo "Usage: $0 <key>"
  exit 1
fi

KEY=$1

# 下载 PINGPONG 文件
wget https://pingpong-build.s3.ap-southeast-1.amazonaws.com/linux/latest/PINGPONG

# 更新 apt-get 并安装所需的包
apt-get update
apt-get install -y ca-certificates curl

# 创建目录并下载 Docker 的官方 GPG 密钥
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

# 添加 Docker 仓库到 Apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# 更新 apt-get 并安装 Docker
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动并启用 Docker 服务
systemctl start docker
systemctl enable docker

# 赋予 PINGPONG 可执行权限
chmod +x ./PINGPONG

# 以后台方式运行 PINGPONG
nohup ./PINGPONG --key "$KEY" &
