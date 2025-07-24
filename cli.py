import click
import sqlite3
import os
from rich.console import Console
from rich.table import Table

DB_FILE = "monitor.db"
console = Console()

def get_db_connection():
    """建立数据库连接，如果文件不存在则返回None"""
    if not os.path.exists(DB_FILE):
        console.print(f"[bold red]错误:[/bold red] 数据库文件 '{DB_FILE}' 未找到。")
        console.print("请先运行 `main.py` 以生成监控数据。")
        return None
    try:
        conn = sqlite3.connect(DB_FILE)
        # 让返回的行可以像字典一样通过列名访问
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        console.print(f"[bold red]数据库连接错误:[/bold red] {e}")
        return None

@click.group()
def cli():
    """
    OSS Status Sentinel 的命令行查询工具。
    用于查询 'monitor.db' 中的监控历史数据。
    """
    pass

@cli.command(name="logs", help="显示最近的监控日志。")
@click.option('--limit', '-l', default=20, help="要显示的日志条数。", type=int)
def show_logs(limit):
    """显示最近的监控日志。"""
    conn = get_db_connection()
    if conn is None:
        return

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", (limit,))
    results = cursor.fetchall()
    conn.close()

    if not results:
        console.print("[yellow]数据库中没有找到任何日志。[/yellow]")
        return

    table = Table(title=f"最近 {limit} 条监控日志")
    table.add_column("时间戳", justify="left", style="cyan")
    table.add_column("服务名称", justify="left", style="magenta")
    table.add_column("状态", justify="center")
    table.add_column("状态码", justify="right", style="green")
    table.add_column("响应时间 (s)", justify="right", style="blue")
    table.add_column("详情", justify="left", style="white")

    for row in results:
        status_color = "green" if row['status'] == 'SUCCESS' else "red"
        status_text = f"✅ [bold {status_color}]{row['status']}[/]"

        # 清理 timestamp 显示，去掉微秒
        timestamp = row['timestamp'].split('.')[0]

        table.add_row(
            timestamp,
            row['service_name'],
            status_text,
            str(row['status_code'] or '-'),
            f"{row['response_time']:.4f}" if row['response_time'] is not None else '-',
            row['details'] or ''
        )

    console.print(table)


@cli.command(name="summary", help="显示每个服务的最新状态摘要。")
def show_summary():
    """显示每个服务的最新状态摘要。"""
    conn = get_db_connection()
    if conn is None:
        return

    cursor = conn.cursor()
    # 这个 SQL 查询会获取每个 service_name 分组中 ID 最大（即最新）的那一行
    cursor.execute("""
        SELECT h.* FROM history h
        INNER JOIN (
            SELECT service_name, MAX(id) AS max_id
            FROM history
            GROUP BY service_name
        ) AS latest ON h.service_name = latest.service_name AND h.id = latest.max_id
        ORDER BY h.service_name;
    """)
    results = cursor.fetchall()
    conn.close()

    if not results:
        console.print("[yellow]数据库中没有找到任何摘要信息。[/yellow]")
        return
    
    table = Table(title="服务状态摘要")
    table.add_column("服务名称", justify="left", style="magenta")
    table.add_column("当前状态", justify="center")
    table.add_column("最后检查时间", justify="left", style="cyan")
    table.add_column("响应时间 (s)", justify="right", style="blue")

    for row in results:
        status_color = "green" if row['status'] == 'SUCCESS' else "red"
        status_text = f"✅ [bold {status_color}]{row['status']}[/]"
        timestamp = row['timestamp'].split('.')[0]
        table.add_row(
            row['service_name'],
            status_text,
            timestamp,
            f"{row['response_time']:.4f}" if row['response_time'] is not None else '-'
        )
    
    console.print(table)


@cli.command(name="failures", help="列出最近的失败记录。")
@click.option('--limit', '-l', default=20, help="要显示的失败记录条数。", type=int)
def show_failures(limit):
    """列出最近的失败记录。"""
    conn = get_db_connection()
    if conn is None:
        return

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history WHERE status = 'FAILURE' ORDER BY timestamp DESC LIMIT ?", (limit,))
    results = cursor.fetchall()
    conn.close()

    if not results:
        console.print("[bold green]太棒了！[/bold green] 在最近的记录中没有找到失败项。")
        return

    table = Table(title=f"最近 {len(results)} 条失败记录")
    table.add_column("时间戳", justify="left", style="cyan")
    table.add_column("服务名称", justify="left", style="magenta")
    table.add_column("详情", justify="left", style="red")

    for row in results:
        timestamp = row['timestamp'].split('.')[0]
        table.add_row(
            timestamp,
            row['service_name'],
            row['details']
        )
    
    console.print(table)


if __name__ == "__main__":
    cli()
