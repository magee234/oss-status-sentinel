import yaml
import requests
import time
import smtplib
from email.mime.text import MIMEText
import os

# --- 从环境变量中加载敏感信息 (更安全的方式) ---
# 你需要在你的VPS环境中设置这些环境变量
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
FROM_EMAIL = os.getenv('FROM_EMAIL')
TO_EMAIL = os.getenv('TO_EMAIL')

def send_notification(subject, body):
    """发送邮件通知"""
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL, TO_EMAIL]):
        print("警告: 邮件通知的配置不完整，跳过发送。请检查环境变量。")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, [TO_EMAIL], msg.as_string())
            print(f"通知邮件已发送至 {TO_EMAIL}")
    except Exception as e:
        print(f"错误: 邮件发送失败: {e}")

def check_service(service):
    """检查单个服务的状态"""
    url = service.get('url')
    method = service.get('method', 'GET').upper()
    expected_status = service.get('expected_status', 200)
    name = service.get('name')
    headers = {'User-Agent': 'OSS-Status-Sentinel/1.0'}

    try:
        response = requests.request(method, url, timeout=10, headers=headers)
        if response.status_code == expected_status:
            print(f"✅ {name} 正常 (状态码: {response.status_code})")
            return True
        else:
            print(f"❌ {name} 异常! 状态码: {response.status_code} (期望: {expected_status})")
            # 发送通知
            subject = f"【监控警报】: {name} 服务异常"
            body = f"你好,\n\n你的服务 '{name}' 检测到异常。\n\nURL: {url}\n期望状态码: {expected_status}\n实际状态码: {response.status_code}\n\n请尽快检查。\n\n- OSS Status Sentinel"
            send_notification(subject, body)
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name} 请求失败! 错误: {e}")
        subject = f"【监控警报】: {name} 请求失败"
        body = f"你好,\n\n你的服务 '{name}' 无法访问。\n\nURL: {url}\n错误详情: {e}\n\n请尽快检查。\n\n- OSS Status Sentinel"
        send_notification(subject, body)
        return False

def main():
    """主函数，加载配置并开始监控循环"""
    try:
        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("错误: 'config.yml' 文件未找到。请根据 config.yml.example 创建一个。")
        return
    except yaml.YAMLError as e:
        print(f"错误: 'config.yml' 文件格式错误: {e}")
        return

    services = config.get('services', [])
    check_interval_seconds = config.get('check_interval_seconds', 300)

    print("--- 开源项目状态哨兵开始运行 ---")
    while True:
        print(f"\n--- 开始新一轮检查 ({time.ctime()}) ---")
        for service in services:
            check_service(service)
        print(f"--- 本轮检查完毕，等待 {check_interval_seconds} 秒 ---")
        time.sleep(check_interval_seconds)

if __name__ == "__main__":
    main()
