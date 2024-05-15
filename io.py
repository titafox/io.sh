import os
import json
from typing import Tuple
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


# 监控 docker 状态
def get_docker_status():
    try:
        # 运行 'docker ps' 命令
        result = subprocess.run(['docker', 'ps'], stdout=subprocess.PIPE)
        # 获取命令的输出
        output = result.stdout.decode('utf-8')
        return output
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return e


# 将日志发送到服务器
def update_server_data(base_url, device_id, io_execution_log, ionet_device_cache):
    # 构建用于获取CSRF token和发送POST请求的完整URL
    csrf_url = f"{base_url}/update-server/"  # URL用于获取CSRF token
    post_url = f"{base_url}/update-server/"  # URL用于POST请求

    # 创建一个会话对象，用于维持cookie
    session = requests.Session()

    # 首先发送GET请求以获取CSRF token
    csrf_response = session.get(csrf_url)
    csrf_token = csrf_response.json()['csrfToken']

    # 准备要发送的数据
    data = {
        "csrfmiddlewaretoken": csrf_token,
        "server_identifier": device_id,
        "io_execution_log": f"{io_execution_log},docker:{get_docker_status()}",
        "custom_metadata": ionet_device_cache,

    }

    # 将数据转换为JSON格式
    json_data = json.dumps(data)

    # 设置请求头，包括CSRF token
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token
    }

    # 发送POST请求
    response = session.post(post_url, data=json_data, headers=headers)

    # 返回响应内容
    return response.text


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
            self.wfile.write(
                f"设备 ID 验证成功。正在执行程序。USER_ID:{USER_ID},DEVICE_ID:{DEVICE_ID},DEVICE_NAME:{DEVICE_NAME}".encode(
                    'utf-8'))
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
    # 执行 Shell 命令获取本地 IP 地址
    command = "hostname -I | awk '{print $1}' | tr '.' '-'"
    local_ip = subprocess.check_output(command, shell=True).decode().strip()

    return local_ip


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


def run_launch_binary(device_id: str, user_id: str, device_name: str, images=None) -> None:
    """运行 launch_binary_linux 命令"""
    if images == "del":
        """停止并移除所有 Docker 容器和镜像"""
        subprocess.run("docker stop $(docker ps -aq); docker rm $(docker ps -aq); docker rmi $(docker images -q)",
                       shell=True)
    else:
        """不删镜像"""
        subprocess.run("docker stop $(docker ps -aq); docker rm $(docker ps -aq)",
                       shell=True)
    # 检查是否已经下载并准备好了二进制文件
    download_and_prepare()
    # 执行命令
    command = f"./launch_binary_linux --device_id={device_id} --user_id={user_id} --operating_system=Linux --usegpus=true --device_name={device_name}"
    print("准备执行的命令行预览：", command)
    subprocess.run(command, shell=True)

    io_execution_log = f"time:{time.strftime('%Y-%m-%d %H:%M:%S')},user_id:{user_id},device_id:{device_id},device_name:{device_name}\n"
    # 记录日志
    with open(PATH + "/io_execution_log.txt", "a") as log_file:
        log_file.write(
            io_execution_log
        )

    # 更新服务器数据
    try:
        with open(IO_CONF, 'r') as file:
            ionet_device_cache = json.load(file)
            update_server_data("https://v.dshz.com", device_id, io_execution_log, ionet_device_cache)
    except Exception as e:
        print(f"更新服务器数据失败: {e}")


# 设置命令行参数解析
parser = argparse.ArgumentParser(description="IONET 脚本")
parser.add_argument("--user_id", help="指定用户 ID", type=str)
parser.add_argument("--device_id", help="指定设备 ID", type=str)
parser.add_argument("--http", help="启动 HTTP 服务", action="store_true")
parser.add_argument("--launch", help="run_launch_binary", action="store_true")
args = parser.parse_args()

# 环境变量设置
IO_CONF: str = PATH + '/ionet_device_cache.txt'
DEVICE_NAME: str = get_device_name()

# 脚本主逻辑
if __name__ == "__main__":
    """
    如果指定 http  则在 9700 端口上运行一个 http 服务，并且每隔24小时自动运行一遍 run_launch_binary 并删除所有 docker 镜像
    如果指定 launch 则运行一次 run_launch_binary 并且删除所有 docker 镜像
    否则运行一次 run_launch_binary 不删除 docker 镜像
    """

    DEVICE_ID, USER_ID = read_device_info(IO_CONF, args)
    if not USER_ID:
        USER_ID = input("请输入您的 io user_id: ")
    if not DEVICE_ID:
        DEVICE_ID = str(uuid.uuid4()).lower()

    if args.http:
        # 如果指定了 --http 参数，启动 HTTP 服务
        print(f"HTTP 服务器正在端口 9700 上运行。等待 device_name 验证...")
        print(f"使用http://你的ip地址:9700/?device_name={DEVICE_NAME} 验证设备 ID。")
        print(f"userid: {USER_ID}, deviceid: {DEVICE_ID}, devicename: {DEVICE_NAME}")
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()

        # 启动定时执行线程，每隔 6 小时运行一次 run_launch_binary，不删除镜像
        timed_execution_thread = threading.Thread(
            target=timed_execution,
            args=(21600, run_launch_binary, (DEVICE_ID, USER_ID, DEVICE_NAME))
        )
        timed_execution_thread.daemon = True
        timed_execution_thread.start()

        # 启动定时执行线程，每隔 24 小时运行一次 run_launch_binary，并删除镜像
        timed_execution_thread = threading.Thread(
            target=timed_execution,
            args=(86400, run_launch_binary, (DEVICE_ID, USER_ID, DEVICE_NAME, 'del'))  # 注意添加 'del' 参数
        )
        timed_execution_thread.daemon = True
        timed_execution_thread.start()

        # 等待 HTTP 服务器线程
        server_thread.join()
    elif args.launch:
        # 如果指定了 --launch 参数，运行 run_launch_binary，并删除镜像
        run_launch_binary(DEVICE_ID, USER_ID, DEVICE_NAME, images='del')
    else:
        # 否则直接运行 run_launch_binary，不删镜像
        run_launch_binary(DEVICE_ID, USER_ID, DEVICE_NAME)
