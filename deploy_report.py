#!/usr/bin/env python3
"""每周荐股报告 网站部署脚本
生成HTML → git push → 触发Cloudflare Pages自动部署
"""
import os, sys, subprocess, shutil
from datetime import datetime

REPO_DIR = "/home/guowu/stock-reports"
REPORTS_DIR = os.path.join(REPO_DIR, "reports")
INDEX_FILE = os.path.join(REPO_DIR, "index.html")
PROXY = "socks5://192.168.101.2:1080"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def create_report_html(date_str, report_content):
    """生成一份报告的HTML文件"""
    filename = f"{date_str}.html"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🦞 每周荐股报告 | {date_str}</title>
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<div class="header">
  <a href="/" style="color:#58a6ff;text-decoration:none;">← 返回首页</a>
  <h1>🦞 每周荐股报告</h1>
  <div class="subtitle">{datetime.now().strftime('%Y年%m月%d日')} · 周日</div>
</div>
<div class="report-content">
{report_content}
</div>
<div class="footer">
  <p>由 🦞 麻辣小龙虾 自动生成 | 数据来源: 公开市场信息</p>
  <p>投资有风险，入市需谨慎。本报告仅供参考，不构成投资建议。</p>
</div>
</body>
</html>"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    log(f"✅ 报告HTML已生成: {filename}")
    return filename

def update_index(date_str):
    """更新首页，追加最新报告链接"""
    today_item = f'<li><a href="/reports/{date_str}.html"><span class="date">{date_str}</span><span class="tag">最新</span></a></li>\n'
    
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 如果已经有了今天的条目，不重复添加
    if f"/reports/{date_str}.html" in content:
        return
    
    # 在 <ul class="report-list"> 之后添加新条目
    old = '<ul class="report-list">\n'
    new = old + today_item
    content = content.replace(old, new)
    
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    log(f"✅ 首页已更新")

def push_to_github():
    """推送到GitHub"""
    env = os.environ.copy()
    env["all_proxy"] = PROXY
    env["GIT_TERMINAL_PROMPT"] = "0"
    
    try:
        subprocess.run(["git", "add", "-A"], cwd=REPO_DIR, env=env, timeout=15)
        subprocess.run(["git", "commit", "-m", f"📊 更新荐股报告 {datetime.now().strftime('%Y-%m-%d')}"],
                      cwd=REPO_DIR, env=env, timeout=15)
        result = subprocess.run(["git", "push", "-u", "origin", "main"],
                               cwd=REPO_DIR, env=env, timeout=30,
                               capture_output=True, text=True)
        if result.returncode == 0:
            log("✅ 已推送到GitHub，Cloudflare Pages 自动部署中...")
            return True
        else:
            log(f"⚠️ push结果: {result.stderr.strip()}")
            return "nothing" in result.stderr or "Everything up-to-date" in result.stderr
    except subprocess.TimeoutExpired:
        log("❌ git push超时")
        return False

def update_search_index(date_str, stock_names, keywords):
    """更新搜索索引"""
    import json
    index_file = os.path.join(REPO_DIR, "search_index.json")
    index = []
    if os.path.exists(index_file):
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)
        except:
            index = []
    # 检查是否已有当天记录
    for entry in index:
        if entry["date"] == date_str:
            entry["stocks"] = stock_names
            entry["keywords"] = keywords
            break
    else:
        index.append({"date": date_str, "stocks": stock_names, "keywords": keywords})
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    log(f"✅ 搜索索引已更新")

def deploy(date_str, report_content, stock_names=None, keywords=None):
    """完整部署流程"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    create_report_html(date_str, report_content)
    update_index(date_str)
    if stock_names:
        update_search_index(date_str, stock_names, keywords or [])
    success = push_to_github()
    if success:
        log(f"🎉 部署完成！https://github.com/wsyy002/stock-reports")
        log(f"📖 Cloudflare Pages 部署后即可访问")
    return success

if __name__ == "__main__":
    # 命令行用法：python3 deploy_report.py "报告内容(HTML)"
    if len(sys.argv) > 1:
        content = sys.argv[1]
    else:
        content = "<p>暂无报告内容</p>"
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    deploy(date_str, content)
