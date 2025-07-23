import yaml
import requests
import time
import smtplib
from email.mime.text import MIMEText
import os
import sqlite3 # [新增] 导入 sqlite3 库
import datetime # [新增] 导入 datetime 库用于记录时间戳

# --- 环境变量部分保持不变 ---
SMTP_SERVER = os.getenv('SMTP_SERVER')
# ... (其他SMTP配置不变) ...
FROM_EMAIL = os.getenv('FROM_EMAIL')
TO_EMAIL = os.getenv('TO_EMAIL')

DB_FILE = "monitor.db" # [新增] 定义数据库文件名

def init_db():
    """
    [新增] 初始化数据库。如果表不存在，则创建它。
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # 创建 history 表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            service_name TEXT NOT NULL,
            url TEXT NOT NULL,
            status TEXT NOT NULL,
            status_code INTEGER,
            response_time REAL,
            details TEXT
        )
        ''')
        conn.commit()
        conn.close()
        print("数据库初始化成功。")
    except sqlite3.Error as e:
        print(f"数据库初始化错误: {e}")

def log_to_db(log_data):
    """
    [新增] 将单条监控记录写入数据库。
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO history (timestamp, service_name, url, status, status_code, response_time, details)
        VALUES (:timestamp, :service_name, :url, :status, :status_code, :response_time, :details)
        ''', log_data)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"写入数据库时出错: {e}")


def send_notification(subject, body):
    """邮件通知功能保持不变"""
    # ... (代码不变) ...
    pass

def check_service(service):
    """
    [修改] 检查单个服务，并记录结果到数据库。
    """
    name = service.get('name')
    url = service.get('url')
    method = service.get('method', 'GET').upper()
    expected_status = service.get('expected_status', 200)
    headers = {'User-Agent': 'OSS-Status-Sentinel/1.1'} # 版本号+0.1

    log_data = {
        "timestamp": datetime.datetime.now(),
        "service_name": name,
        "url": url,
        "status": "FAILURE", # 默认失败
        "status_code": None,
        "response_time": None,
        "details": ""
    }

    try:
        start_time = time.time()
        response = requests.request(method, url, timeout=10, headers=headers)
        end_time = time.time()
        
        log_data["response_time"] = round(end_time - start_time, 4)
        log_data["status_code"] = response.status_code

        if response.status_code == expected_status:
            print(f"✅ {name} 正常 (状态码: {response.status_code}, 耗时: {log_data['response_time']}s)")
            log_data["status"] = "SUCCESS"
        else:
            print(f"❌ {name} 异常! 状态码: {response.status_code} (期望: {expected_status})")
            log_data["details"] = f"状态码不匹配: 收到 {response.status_code}, 期望 {expected_status}"
            subject = f"【监控警报】: {name} 服务异常"
            body = f"你好,\n\n你的服务 '{name}' 检测到异常。\n\nURL: {url}\n期望状态码: {expected_status}\n实际状态码: {response.status_code}\n\n请尽快检查。\n\n- OSS Status Sentinel"
            send_notification(subject, body)
            
    except requests.exceptions.RequestException as e:
        end_time = time.time() # 记录一下大致时间
        log_data["response_time"] = round(end_time - start_time, 4) if 'start_time' in locals() else None
        log_data["details"] = str(e)
        print(f"❌ {name} 请求失败! 错误: {e}")
        subject = f"【监控警报】: {name} 请求失败"
        body = f"你好,\n\n你的服务 '{name}' 无法访问。\n\nURL: {url}\n错误详情: {e}\n\n请尽快检查。\n\n- OSS Status Sentinel"
        send_notification(subject, body)
    
    # [修改] 无论成功失败，都调用函数将结果记入数据库
    log_to_db(log_data)


def main():
    """
    [修改] 主函数，增加数据库初始化步骤。
    """
    # ... (读取配置文件的代码不变) ...
    try:
        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("错误: 'config.yml' 文件未找到。")
        return
    except yaml.YAMLError as e:
        print(f"错误: 'config.yml' 文件格式错误: {e}")
        return

    # [新增] 在启动监控循环前，先初始化数据库
    init_db()

    services = config.get('services', [])
    check_interval_seconds = config.get('check_interval_seconds', 300)

    print("--- 开源项目状态哨兵开始运行 (V1.1 - 带数据库记录) ---")
    while True:
        # ... (循环部分不变) ...
        print(f"\n--- 开始新一轮检查 ({time.ctime()}) ---")
        for service in services:
            check_service(service)
        print(f"--- 本轮检查完毕，等待 {check_interval_seconds} 秒 ---")
        time.sleep(check_interval_seconds)

if __name__ == "__main__":
    main()
