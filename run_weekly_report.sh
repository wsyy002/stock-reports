#!/bin/bash
# 手动生成并部署2026年7月5日周报
cd /home/guowu/stock-reports

echo "[$(date '+%H:%M:%S')] ===== 第1步: 运行 generate_report.py ====="
python3 generate_report.py 2>&1 | tee /tmp/generate_output.log
GEN_EXIT=${PIPESTATUS[0]}

echo "[$(date '+%H:%M:%S')] 退出码: $GEN_EXIT"

if [ -f weekly_report_20260705.html ]; then
    echo "[$(date '+%H:%M:%S')] ✅ 报告已生成!"
    ls -la weekly_report_20260705.html
    echo "[$(date '+%H:%M:%S')] ===== 第2步: 检查Git状态 ====="
    git status --short
    git log --oneline -3
    echo "[$(date '+%H:%M:%S')] ===== 第3步: Git Push ====="
    git push origin main 2>&1 | tail -10
    echo "[$(date '+%H:%M:%S')] ===== 完成! ====="
else
    echo "[$(date '+%H:%M:%S')] ❌ 报告未生成，查看错误..."
    cat /tmp/generate_output.log
fi

echo "[$(date '+%H:%M:%S')] ===== 检查报告目录 ====="
ls -la /home/guowu/stock-reports/weekly_report_202607* 2>/dev/null || echo "无202607文件"
ls -la /home/guowu/stock-reports/latest.html 2>/dev/null
readlink -f /home/guowu/stock-reports/latest.html 2>/dev/null || echo "无latest链接"
ls -la /vol2/1000/Web/stock-reports/ 2>/dev/null | grep 202607
echo "===== 全部完成 ====="
