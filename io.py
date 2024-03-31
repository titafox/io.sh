import socket
import os
import json
from typing import Tuple
import random
import subprocess
import uuid
import requests
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import urllib.parse
import time


# 设置路径为你自己的各种乱七八糟跟 io 有关数据的存放路径
PATH = "/var/ionet"

def timed_execution(interval, function, args):
    while True:
        time.sleep(interval)
        function(*args)

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 解析查询参数
        query_string = self.path.split('?', 1)[-1]
        query_params = urllib.parse.parse_qs(query_string)
        received_device_name = query_params.get('device_name', [None])[0]

        if received_device_name == DEVICE_NAME:
            self.send_response(200)
            self.end_headers()
            self.wfile.write("设备 ID 验证成功。正在执行程序。".encode('utf-8'))
            run_launch_binary(DEVICE_ID, USER_ID, DEVICE_NAME)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write("无效的设备 ID。".encode('utf-8'))

def start_server():
    server_address = ('', 9700)
    httpd = HTTPServer(server_address, RequestHandler)
    httpd.serve_forever()


def get_device_name() -> str:
    """获取本地 IP 地址并转换为 DEVICE_NAME"""
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip.replace('.', '-')


def read_device_info(io_conf: str, cmd_args: argparse.Namespace) -> Tuple[str, str]:
    """从 IO_CONF 读取设备信息"""
    if os.path.isfile(io_conf):
        with open(io_conf, 'r') as file:
            data = json.load(file)
            device_id = data.get('device_id', cmd_args.device_id or str(uuid.uuid4()).lower())
            user_id = data.get('user_id', cmd_args.user_id or '')
            return device_id, user_id
    return cmd_args.device_id or str(uuid.uuid4()).lower(), cmd_args.user_id or ''


def download_and_prepare() -> None:
    """下载并准备运行所需的二进制文件"""
    url = "https://github.com/ionet-official/io_launch_binaries/raw/main/launch_binary_linux"
    path = PATH
    os.makedirs(path, exist_ok=True)
    os.chdir(path)
    if not os.path.isfile("launch_binary_linux"):
        r = requests.get(url)
        with open("launch_binary_linux", "wb") as file:
            file.write(r.content)
        subprocess.run(["chmod", "+x", "launch_binary_linux"])


def run_launch_binary(device_id: str, user_id: str, device_name: str) -> None:
    """运行 launch_binary_linux 命令"""

    """停止并移除所有 Docker 容器和镜像"""
    subprocess.run("docker stop $(docker ps -aq); docker rm $(docker ps -aq); docker rmi $(docker images -q)",
                   shell=True)

    # 检查是否已经下载并准备好了二进制文件
    download_and_prepare()
    # 执行命令
    command = f"./launch_binary_linux --device_id={device_id} --user_id={user_id} --operating_system=Linux --usegpus=true --device_name={device_name}"
    print("准备执行的命令行预览：", command)
    subprocess.run(command, shell=True)

    # 记录日志
    with open(PATH + "/io_execution_log.txt", "a") as log_file:
        log_file.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} -{user_id} - {device_id} - {device_name} - 脚本执行成功\n")


# 设置命令行参数解析
parser = argparse.ArgumentParser(description="IONET 脚本")
parser.add_argument("--user_id", help="指定用户 ID", type=str)
parser.add_argument("--device_id", help="指定设备 ID", type=str)
parser.add_argument("--http", help="启动 HTTP 服务", action="store_true")
parser.add_argument("--cron", help="为计划任务执行随机延迟", action="store_true")
args = parser.parse_args()

# 环境变量设置
IO_CONF: str = PATH + '/ionet_device_cache.txt'
DEVICE_NAME: str = get_device_name()

# 脚本主逻辑
if __name__ == "__main__":
    # 随机延迟逻辑
    if args.cron:
        delay = random.randint(0, 360) * 5
        time.sleep(delay)

    DEVICE_ID, USER_ID = read_device_info(IO_CONF, args)
    if not USER_ID:
        USER_ID = input("请输入您的 io user_id: ")
    if not DEVICE_ID:
        DEVICE_ID = str(uuid.uuid4()).lower()

    if args.http:
        # 如果指定了 --http 参数，启动 HTTP 服务
        print(f"HTTP 服务器正在端口 9700 上运行。等待 device_name 验证...")
        print(f"userid: {USER_ID}, deviceid: {DEVICE_ID}, devicename: {DEVICE_NAME}")
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()
        server_thread.join()
    else:
        # 否则直接执行
        run_launch_binary(DEVICE_ID, USER_ID, DEVICE_NAME)

    if args.http:
        # 如果指定了 --http 参数，启动 HTTP 服务
        print(f"HTTP 服务器正在端口 9700 上运行。等待 device_name 验证...")
        print(f"userid: {USER_ID}, deviceid: {DEVICE_ID}, devicename: {DEVICE_NAME}")
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()

        # 启动定时执行线程，每隔 6 小时运行一次 run_launch_binary
        timed_execution_thread = threading.Thread(
            target=timed_execution,
            args=(21600, run_launch_binary, (DEVICE_ID, USER_ID, DEVICE_NAME))
        )
        timed_execution_thread.daemon = True
        timed_execution_thread.start()

        # 等待 HTTP 服务器线程
        server_thread.join()
    else:
        run_launch_binary(DEVICE_ID, USER_ID, DEVICE_NAME)
