#!/usr/bin/env python3
"""部署周报HTML到web"""
import sys, os, json

REPORTS_DIR = "/home/guowu/stock-reports"
WEB_DIR = "/vol2/1000/Web/stock-reports"  # 假设

if len(sys.argv) < 2:
    print("Usage: deploy_report.py 'HTML' stock1(code) stock2(code) ...")
    sys.exit(1)

html = sys.argv[1]
stocks = sys.argv[2:] if len(sys.argv) > 2 else []

# 保存到文件
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(WEB_DIR, exist_ok=True)

fname = f"weekly_report_20260614.html"
with open(os.path.join(REPORTS_DIR, fname), 'w', encoding='utf-8') as f:
    f.write(html)
with open(os.path.join(WEB_DIR, fname), 'w', encoding='utf-8') as f:
    f.write(html)

# 更新latest链接
latest_link = os.path.join(WEB_DIR, "latest.html")
if os.path.exists(latest_link):
    os.remove(latest_link)
os.symlink(fname, latest_link)

print(f"✅ 报告已部署: {fname}")
