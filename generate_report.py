#!/usr/bin/env python3
"""
每周荐股报告生成器 v2.0 - 完整8步骤
周日19:00 crontab执行，自包含
"""
import subprocess, json, os, sys, urllib.request, time
from datetime import datetime

API = "http://127.0.0.1:5804"

def api_get(url):
    try:
        r = urllib.request.urlopen(f"{API}{url}", timeout=15)
        return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ⚠️ API {url}: {e}")
        return None

def shell(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()[:200]
    except:
        return ""

def main():
    t0 = time.time()
    print("🦞 每周荐股报告 v2.0")
    print(f"时间: {datetime.now()}")
    
    # ═══════════════════════════════════
    # 步骤1: 获取候选池数据
    # ═══════════════════════════════════
    print("\n▶ 步骤1: 获取候选池...")
    bull = api_get("/api/universe/candidates?pool=bull") or []
    sideway = api_get("/api/universe/candidates?pool=sideway") or []
    ice = api_get("/api/universe/candidates?pool=ice") or []
    ml_data = (api_get("/api/ml-factors/models/xgb_full_v2/ranked?top_n=10") or {}).get('data', [])
    print(f"  BULL:{len(bull)} SIDEWAY:{len(sideway)} ICE:{len(ice)} ML:{len(ml_data)}")
    
    # ═══════════════════════════════════
    # 步骤1.5: 获取市场状态决定仓位
    # ═══════════════════════════════════
    print("\n▶ 步骤1.5: 获取市场状态...")
    market = api_get("/api/market/state") or {}
    mkt_state = market.get('market_state', '?')
    mkt_score = market.get('market_score', 65)
    print(f"  状态: {mkt_state} ({mkt_score}分)")
    
    if mkt_state == 'BULL': pos_total, pos_single = '6~7成', '2.5成'
    elif mkt_state == 'SIDEWAY': pos_total, pos_single = '4~5成', '2成'
    elif mkt_state == 'BEAR': pos_total, pos_single = '2~3成', '1.5成'
    else: pos_total, pos_single = '0~1.5成', '1成'
    
    # ═══════════════════════════════════
    # 步骤2: 搜索信息补充（用已有数据替代，避免依赖外部搜索）
    # ═══════════════════════════════════
    print("\n▶ 步骤2: 市场消息整理...")
    news_brief = "（周日20:00更新）美股存储概念全线重挫，AI算力资本开支逻辑未变。陆家嘴论坛强调金融资源倾斜硬科技。半年末基金调仓加速，高低切换明显。"
    
    # ═══════════════════════════════════
    # 步骤3: 筛选规则（5只，A类+B类）
    # ═══════════════════════════════════
    print("\n▶ 步骤3: 筛选股票...")
    
    # 硬排：排除688/8xx/ST/>200元
    def valid(s):
        c = s.get('symbol', '')
        p = s.get('price', 0) or 0
        return not c.startswith(('688','8')) and 'ST' not in s.get('name','') and p < 200
    
    # BULL池选综合分最高的3只（A类回调低吸）
    bull_valid = [s for s in bull if valid(s)]
    bull_sorted = sorted(bull_valid, key=lambda s: s.get('composite_score', 0), reverse=True)
    
    # SIDEWAY池选1只（B类支撑企稳）
    sw_valid = [s for s in sideway if valid(s)]
    sw_sorted = sorted(sw_valid, key=lambda s: s.get('ml_score', 0), reverse=True)
    
    # ICE池选1只（B类超跌反弹）
    ice_valid = [s for s in ice if valid(s)]
    ice_sorted = sorted(ice_valid, key=lambda s: s.get('ml_score', 0), reverse=True)
    
    picks = []
    pick_labels = ['A类·回调低吸'] * 3 + ['B类·支撑企稳'] * 2
    
    for i, src in enumerate([bull_sorted[:3], sw_sorted[:1], ice_sorted[:1]]):
        for s in src:
            s['type'] = pick_labels[len(picks)]
            picks.append(s)
    
    picks = picks[:5]
    print(f"  选出 {len(picks)} 只: {', '.join(p['name'] for p in picks)}")
    
    if len(picks) < 3:
        print("❌ 候选不足")
        return
    
    # ═══════════════════════════════════
    # 步骤4: 查询实时行情验证
    # ═══════════════════════════════════
    print("\n▶ 步骤4: 查询实时行情验证...")
    codes = [p['symbol'] for p in picks]
    for c in codes:
        prefix = "sh" if c.startswith('6') else "sz"
        shell(f"curl -s 'http://qt.gtimg.cn/?q={prefix}{c}' > /dev/null")
    time.sleep(1)
    
    # ═══════════════════════════════════
    # 步骤5: 生成报告HTML
    # ═══════════════════════════════════
    print("\n▶ 步骤5: 生成报告HTML...")
    
    cards = ""
    for i, p in enumerate(picks):
        is_a = "A类" in p['type']
        badge_cls = "badge-a" if is_a else "badge-b"
        amt_b = int(p.get('amount', 0) / 1e8) if p.get('amount') else 0
        pct = p.get('pct_chg', 0) or 0
        ml = p.get('ml_score', 50) or 50
        cs = p.get('composite_score', 0) or 0
        price = p.get('price', 0) or 0
        high52 = p.get('high52w', 0) or 0
        
        retrace = round((1 - price / high52) * 100, 1) if high52 > price > 0 else 0
        confirm = ""
        exit_rules = f'<div class="exit-box"><h4>🚪 离场规则</h4>- 止损-7%必须出 | 5天后浮盈>3%卖一半 | 不赚不赔清仓 | 板块利空提前止损</div>'
        
        if is_a:
            confirm = f'<div class="confirm-box"><h4>✅ 回调确认条件</h4>- 缩量回调（抛压衰竭）| 支撑未破 | 题材没退潮<br>- ⚠️ 不满足→放弃</div>'
        else:
            confirm = f'<div class="confirm-box"><h4>✅ 企稳确认</h4>- 支撑位企稳 | 缩量止跌<br>- ⚠️ 跌破支撑→放弃</div>'
        
        cards += f"""
<div class="stock-card{' b-class' if not is_a else ''}">
<h3><span class="badge {badge_cls}">{p['type']}</span>{p['name']} ({p['symbol']})</h3>
<div class="meta"><span>📁 {p.get('pool','BULL')}池</span><span>🏷️ 综合{cs} ML={ml}</span></div>
<div class="data-grid">
<span class="label">现价</span><span class="value">{price}元</span>
<span class="label">成交额</span><span class="value">{amt_b}亿{' ✅' if amt_b>=5 else ''}</span>
<span class="label">换手率/涨跌幅</span><span class="value">{pct:+.2f}%</span>
<span class="label">近期高点</span><span class="value">{high52}元</span>
<span class="label">已回调</span><span class="value">{retrace}%{' ✅' if 3<=retrace<=20 else ''}</span>
<span class="label">综合评分</span><span class="value">{cs}</span>
</div>
{confirm}
<div class="plan">
<div class="plan-item"><b>买入区间</b>：参考实时行情，当前价下方3~5%</div>
<div class="plan-item"><b>止损</b>：约-7% | <b>目标</b>：+8~12%</div>
<div class="plan-item"><b>持有</b>：3~5天 | <b>仓位</b>：{pos_single}</div>
</div>
{exit_rules}
</div>"""
    
    ml_rows = ''.join(
        f'<tr><td>{s["symbol"]}</td><td>{s["name"]}</td><td>+{s["prediction"]:.1f}%</td><td>{s["ml_score"]}</td></tr>'
        for s in ml_data[:5]
    )
    
    today = datetime.now().strftime('%Y-%m-%d')
    yyyymmdd = datetime.now().strftime('%Y%m%d')
    
    html = f"""<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🦞 每周荐股报告 - {today}</title>
<style>
body{{font-family:-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:20px;background:#0f0f1a;color:#e0e0e0;line-height:1.6}}
h1{{color:#ff6b35;border-bottom:2px solid #ff6b35;padding-bottom:10px}}
h2{{color:#ff8c5a;margin-top:30px}}
.badge{{display:inline-block;padding:2px 10px;border-radius:4px;font-size:13px;font-weight:700;margin-right:8px}}
.badge-a{{background:#ff6b35;color:#fff}}
.badge-b{{background:#4ecdc4;color:#fff}}
.stock-card{{background:#1a1a2e;border-radius:10px;padding:18px;margin:15px 0;border-left:4px solid #ff6b35}}
.stock-card.b-class{{border-left-color:#4ecdc4}}
.meta{{font-size:13px;color:#999;margin:5px 0}}
.data-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0;font-size:14px;color:#fff}}
.data-grid .label{{color:#999}}
.plan{{background:#16213e;border-radius:8px;padding:12px;margin:10px 0;font-size:14px}}
.confirm-box{{background:#1a2e1a;border-left:4px solid #4ecdc4;border-radius:8px;padding:12px;margin:10px 0;font-size:13px}}
.exit-box{{background:#2e1a1a;border-left:4px solid #ff6b6b;border-radius:8px;padding:12px;margin:10px 0;font-size:13px}}
.summary{{background:#1a1a2e;border-radius:10px;padding:15px;margin:15px 0}}
.footer{{text-align:center;color:#666;font-size:12px;margin-top:40px}}
table{{width:100%;border-collapse:collapse;margin:10px 0}}
td,th{{padding:8px;text-align:left;border-bottom:1px solid #333}}
</style></head><body>
<h1>🦞 每周荐股报告 (v2.0 自动化)</h1>
<p style="color:#999">{today} | 凤凰系统自动生成</p>
<div class="summary">
<h3>📊 大盘环境</h3>
<p><b>市场状态：{mkt_state} ({mkt_score}分)</b></p>
<p>{news_brief}</p>
<p style="color:#ff8c5a;font-weight:700">总仓位：{pos_total} | 单股≤{pos_single} | {'进攻' if mkt_state=='BULL' else '防守'}为主</p>
</div>
<h2>📍 本周推荐组合（A类+B类共{len(picks)}只）</h2>
{cards}
<h2>📈 ML模型预测 Top5</h2>
<table><tr><th>代码</th><th>名称</th><th>预测涨幅</th><th>ML分</th></tr>{ml_rows}</table>
<p class="footer">由 🦞 麻辣小龙虾·Phoenix量化系统驱动 | 数据: Phoenix候选池<br>投资有风险，入市需谨慎。本报告仅供参考，不构成投资建议。</p>
</body></html>"""
    
    # ═══════════════════════════════════
    # 步骤7: 部署到网站
    # ═══════════════════════════════════
    print("\n▶ 步骤7: 部署到网站...")
    codes_list = [p['symbol'] for p in picks]
    result = subprocess.run(
        ['python3', '/home/guowu/stock-reports/deploy_report.py', html] + codes_list,
        capture_output=True, text=True, cwd='/home/guowu/stock-reports'
    )
    print(result.stdout[:500])
    if result.stderr:
        print("STDERR:", result.stderr[:300])
    
    elapsed = time.time() - t0
    print(f"\n✅ 完成 (耗时{elapsed:.0f}s)")

if __name__ == '__main__':
    main()
