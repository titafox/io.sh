#!/bin/bash
# Author: 木木哥
# Copyright (c) 2024 全体IONET 的头大者
# License: MIT


# 常量
USER_ID="6b1a07a3-f950-4856-a171-3b346b51df54"
IO_CONF='/var/ionet/ionet_device_cache.txt'
DEVICE_ID="" # DEVICE_ID默认不需要有值
DEVICE_NAME=$(hostname -I | awk '{print $1}' | tr '.' '-') # DEVICE_NAME默认是当前服务器的IP地址，但是点号变成了-号


echo "————————————计划任务的执行————————————"
# 如果是脚本执行，避免网内瞬间流量过大，随机延迟 0 到 30 分钟，每 5 秒为间隔
# 0 */6 * * * /var/ionet/io.sh cron
# 写入表达式 crontab -e
# 在打开的编辑器中，输入上面的表达式，然后保存并退出编辑器
# 查看当前的 crontab 任务 crontab -l
# 检查是否传递了 "cron" 参数，如果传递了，则表示是脚本执行,参考上面的注释
if [[ "$1" == "cron" ]]; then
    # 生成一个 0 到 360 之间的随机数，然后乘以 5，得到一个 0 到 1800 秒的随机延迟时间
    DELAY=$((RANDOM % 361 * 5))

    # 等待随机的秒数
    sleep ${DELAY}s
fi


echo -e "\033[32m————————————检查环境————————————\033[0m"

# 检查 jq 是否已安装，如果没有安装，则安装 jq
if ! command -v jq &> /dev/null; then
    echo "jq 未安装，正在安装 jq..."
    sudo apt update
    sudo apt install -y jq
fi

echo "—————停止并移除所有 Docker 容器和镜像—————"

# 停止并移除所有 Docker 容器和镜像
docker stop $(docker ps -aq); docker rm $(docker ps -aq); docker rmi $(docker images -q)

echo "————————————运行容器前准备————————————"
echo -e "当前服务器IP地址为: \033[32m$(hostname -I)\033[0m"

mkdir -p /var/ionet
cd /var/ionet || exit

if [ ! -f "/var/ionet/launch_binary_linux" ]; then
    curl -L https://github.com/ionet-official/io_launch_binaries/raw/main/launch_binary_linux -o launch_binary_linux
    chmod +x launch_binary_linux
fi


echo -e "\033[32m————————————当前时间是：$(date)————————————\033[0m"
echo "准备执行 launch_binary_linux"

echo -e "\033[31mDEVICE_NAME: ${DEVICE_NAME}\033[0m"

# 如果ionet_device_cache.txt文件存在则读取其中的device_id和user_id
# ionet_device_cache.txt 是在运行 launch_binary_linux 时生成的
if [ -f "${IO_CONF}" ]; then
    DEVICE_ID=$(jq -r '.device_id' "${IO_CONF}")
    echo -e "\033[31mDEVICE_ID: ${DEVICE_ID}\033[0m"
    echo -e "\033[31mUSER_ID: ${USER_ID}\033[0m"
else
  # 如果ionet_device_cache.txt文件不存在则自动生成一个新的device_id
    DEVICE_ID=$(tr '[:upper:]' '[:lower:]' < /proc/sys/kernel/random/uuid)
    echo "DEVICE_ID: ${DEVICE_ID}"
  # 这里要注意，如果从ionet_device_cache.txt文件中读取不到user_id，那么就会使用默认的user_id,也就是最上面定义的USER_ID
fi

# 显示一下 launch_binary_linux 的整个要运行的命令
echo "准备执行的命令预览："
echo "./launch_binary_linux --device_id=${DEVICE_ID} --user_id=${USER_ID} --operating_system=Linux --usegpus=true --device_name=${DEVICE_NAME}"
echo -e "\033[33m—————等待你 10 秒确认预览信息,按 Ctrl+C 取消—————\033[0m"
# 等待 10 秒，然后运行 launch_binary_linux，倒数计时
for i in {10..1}; do
    echo -e "\033[31mUSER_ID: ${USER_ID} ，剩余 $i 秒\033[0m"
    sleep 1
done

# 运行 launch_binary_linux

./launch_binary_linux --device_id="${DEVICE_ID}" \
                      --user_id="${USER_ID}" \
                      --operating_system="Linux" \
                      --usegpus=true \
                      --device_name="${DEVICE_NAME}"

# 执行完成写一个日志，把执行日期、user_id、device_id、device_name都写进去，方便查看，每次执行会追加到文件末尾
echo "$(date) -${USER_ID} - ${DEVICE_ID} - ${DEVICE_NAME} - 脚本执行成功" >> /var/ionet/io_execution_log.txt
