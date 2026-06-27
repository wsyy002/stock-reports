#!/usr/bin/env python3
"""部署周报HTML到全部目录，更新index.html"""
import sys, os, re
from datetime import datetime

DIRS = [
    "/vol2/1000/Web/stock-reports",
    "/home/guowu/stock-reports",
]
INDEX_DIR = "/home/guowu/stock-reports"

if len(sys.argv) < 2:
    print("Usage: deploy_report.py 'HTML' stock1(code) stock2(code) ...")
    sys.exit(1)

html = sys.argv[1]
stocks = sys.argv[2:] if len(sys.argv) > 2 else []

today = datetime.now()
date_str = today.strftime('%Y-%m-%d')
yyyymmdd = today.strftime('%Y%m%d')
fname = f"weekly_report_{yyyymmdd}.html"

# 1. 保存 HTML 文件到所有目录
for d in DIRS:
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, fname), 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✅ 写入 {d}/{fname}")

# 2. 保存日期名格式到 reports/ 子目录
reports_dir = os.path.join(INDEX_DIR, "reports")
os.makedirs(reports_dir, exist_ok=True)
with open(os.path.join(reports_dir, f"{date_str}.html"), 'w', encoding='utf-8') as f:
    f.write(html)

# 3. 更新 latest.html 链接
for d in DIRS:
    lpath = os.path.join(d, "latest.html")
    if os.path.exists(lpath) or os.path.islink(lpath):
        os.remove(lpath)
    os.symlink(fname, lpath)

# 4. 更新 index.html 添加新报告
index_path = os.path.join(INDEX_DIR, "index.html")
if os.path.exists(index_path):
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if date_str in content:
        print(f"  ↪ index.html 已有 {date_str}，跳过")
    else:
        new_entry = f'  <li><a href="{fname}"><span class="date">{date_str}</span><span class="tag">最新</span></a></li>'
        content = content.replace('<ul class="report-list" id="reportList">',
                                  f'<ul class="report-list" id="reportList">\n{new_entry}', 1)
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ index.html 已添加 {date_str}")

# 5. 提交到 Git 并推送到 GitHub（触发 Cloudflare Pages 自动部署）
import subprocess
git_dir = INDEX_DIR
try:
    subprocess.run(["git", "add", fname, f"reports/{date_str}.html", "index.html"],
                   cwd=git_dir, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", f"📊 每周荐股报告 {date_str}"],
                   cwd=git_dir, capture_output=True, check=True)
    result = subprocess.run(["git", "push", "origin", "main"],
                           cwd=git_dir, capture_output=True, text=True, check=True)
    print(f"  ✅ GitHub推送成功 (Cloudflare Pages 将自动部署)")
except subprocess.CalledProcessError as e:
    if "nothing to commit" in str(e.stderr or e.stdout or "").lower():
        print(f"  ↪ Git无变更，跳过推送")
    else:
        print(f"  ⚠️ Git推送失败: {e.stderr or e.stdout}")

print(f"✅ 报告 {fname} 已部署 -> https://stock.jyfg.de5.net/")
