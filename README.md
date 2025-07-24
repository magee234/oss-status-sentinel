# OSS Status Sentinel

OSS Status Sentinel (开源项目状态哨兵) 是一个轻量级的、可配置的监控工具，用于检查您的开源项目、个人网站或API端点的健康状况，并将历史记录保存到本地SQLite数据库中。

本项目还包含一个命令行工具 (`cli.py`)，用于方便地查询和展示监控数据。

## 功能

- **后台监控** (`main.py`): 7x24小时运行，持续检查服务状态。
- **数据库记录**: 所有检查结果（包括时间戳、状态、响应时间等）都保存在 `monitor.db` SQLite文件中。
- **邮件警报**: 在服务异常时发送邮件通知。
- **CLI查询** (`cli.py`): 提供美观、易用的命令行界面来查看监控数据。

## 如何使用

### 1. 运行监控服务

1. 克隆本仓库并进入目录: `git clone ...` `cd oss-status-sentinel`
2. **安装依赖**: `pip install -r requirements.txt`
3. 复制 `config.yml.example` 为 `config.yml` 并修改。
4. 运行主监控脚本: `python main.py` (建议使用`systemd`等工具让其在后台永久运行)

### 2. 使用命令行工具查询数据

在你运行监控服务一段时间后，`monitor.db` 文件就会被创建。你可以使用`cli.py`来查询它。

**命令格式**: `python cli.py [COMMAND]`

**可用命令**:

- `logs`: 显示最近的监控日志。
  ```bash
  # 显示最近20条日志 (默认)
  python cli.py logs
  # 显示最近5条日志
  python cli.py logs --limit 5

summary: 显示每个服务的最新状态摘要。
Generated bash
python cli.py summary

failures: 列出最近的失败记录。
Generated bash
# 显示最近20条失败记录
python cli.py failures
# 显示最近50条失败记录
python cli.py failures -l 50

未来计划
将监控历史记录写入数据库。 (已完成)
创建一个命令行工具 (CLI) 来查询数据库中的监控历史。 (已完成)
增加对更多通知渠道的支持（如 Discord, Slack, Telegram）。
创建一个简单的Web仪表盘来可视化状态历史。
