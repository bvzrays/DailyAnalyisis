from __future__ import annotations

import html
from typing import Any
from datetime import datetime

# ruff: noqa: E501


def _format_number(value: object) -> str:
    try:
        return f"{int(value or 0):,}"
    except (TypeError, ValueError):
        return "0"


def _format_cost(value: object) -> str:
    try:
        return f"{float(value or 0):.4f}"
    except (TypeError, ValueError):
        return "0.0000"


def _text(value: object) -> str:
    return html.escape(str(value or ""))


def build_overview_html(
    summary: dict[str, Any],
    trends: dict[str, Any],
    active_tasks: list[dict[str, Any]],
    generated_at: datetime | None = None,
) -> str:
    points = trends.get("points", []) if isinstance(trends, dict) else []
    points = points[-14:] if isinstance(points, list) else []
    maximum_requests = max(
        [int(point.get("request_count", 0) or 0) for point in points if isinstance(point, dict)]
        or [1]
    )

    chart_fragment = "".join(
        '<div class="bar-item">'
        f'<div class="bar-value">{int(point.get("request_count", 0) or 0)}</div>'
        f'<div class="bar" style="--height:{max(3, round(int(point.get("request_count", 0) or 0) / maximum_requests * 100)) if int(point.get("request_count", 0) or 0) else 0}%;"></div>'
        f'<div class="bar-label">{_text(point.get("date", ""))}</div>'
        "</div>"
        for point in points
        if isinstance(point, dict)
    ) or '<div class="empty">暂无趋势数据</div>'

    def breakdown_fragment(items: object) -> str:
        if not isinstance(items, list) or not items:
            return '<div class="empty">暂无数据</div>'
        return "".join(
            '<div class="row">'
            f'<span class="row-name">{_text(item.get("name", ""))}</span>'
            f'<span class="row-value">{_format_number(item.get("total_tokens"))} tokens</span>'
            "</div>"
            for item in items[:5]
            if isinstance(item, dict)
        ) or '<div class="empty">暂无数据</div>'

    tasks = active_tasks[:6] if isinstance(active_tasks, list) else []
    task_fragment = "".join(
        '<div class="task">'
        f'<div class="task-head"><span>{_text(task.get("group_name") or task.get("group_id"))}</span>'
        f'<span>{_text(task.get("current_stage"))}</span></div>'
        f'<div class="task-meta">{_text(task.get("platform"))} · '
        f'{_text(task.get("trigger_type"))} · 已运行 {_text(task.get("duration_s"))} 秒</div>'
        "</div>"
        for task in tasks
        if isinstance(task, dict)
    ) or '<div class="empty">当前没有运行中的任务</div>'

    summary_values = {
        "__GENERATED_AT__": _text((generated_at or datetime.now()).strftime("%Y-%m-%d %H:%M")),
        "__TOTAL_TRACES__": _format_number(summary.get("total_traces")),
        "__TODAY_TRACES__": _format_number(summary.get("today_traces")),
        "__TODAY_GROUPS__": _format_number(summary.get("today_active_groups")),
        "__SUCCESS_RATE__": f'{float(summary.get("success_rate", 0) or 0):.1f}%',
        "__AVG_DURATION__": f'{float(summary.get("avg_duration_ms", 0) or 0) / 1000:.1f}s',
        "__TOTAL_TOKENS__": _format_number(summary.get("total_tokens_spent")),
        "__TODAY_TOKENS__": _format_number(summary.get("today_tokens_spent")),
        "__TOTAL_COST__": _format_cost(summary.get("total_cost_spent")),
        "__TODAY_COST__": _format_cost(summary.get("today_cost_spent")),
        "__CHART__": chart_fragment,
        "__PROVIDERS__": breakdown_fragment(trends.get("provider_breakdown", [])),
        "__MODELS__": breakdown_fragment(trends.get("model_breakdown", [])),
        "__TASK_COUNT__": str(len(tasks)),
        "__TASKS__": task_fragment,
    }
    template = """
<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><style>
* { box-sizing: border-box; }
html, body { width: 1120px; margin: 0; padding: 0; background: #f5f7fb; }
body { color: #172033; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; }
.page { width: 1120px; padding: 30px 34px 28px; }
.header { display:flex; justify-content:space-between; align-items:end; margin-bottom:22px; }
.eyebrow { color:#5273d8; font-size:14px; font-weight:700; letter-spacing:2px; }
h1 { margin:5px 0 0; font-size:32px; line-height:1.15; }.time { color:#718096; font-size:14px; }
.metrics { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:16px; }
.metric, .panel { background:#fff; border:1px solid #e5eaf3; border-radius:14px; box-shadow:0 5px 16px rgba(52,72,112,.06); }
.metric { padding:16px 18px; min-height:92px; }.metric-label { color:#718096; font-size:13px; }
.metric-value { margin-top:8px; color:#1e3a8a; font-size:25px; font-weight:750; }
.layout { display:grid; grid-template-columns:1.35fr 1fr; gap:16px; }.panel { padding:18px 20px; }
.panel-title { display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; }
.panel-title strong { font-size:17px; }.panel-title span { color:#8a96aa; font-size:12px; }
.chart { height:205px; display:grid; grid-template-columns:repeat(14,1fr); gap:7px; align-items:end; border-bottom:1px solid #dfe5ef; padding:8px 0 0; }
.bar-item { height:100%; display:flex; flex-direction:column; justify-content:end; align-items:center; min-width:0; }
.bar-value { color:#6980b8; font-size:10px; height:17px; }.bar { width:24px; max-width:80%; height:var(--height); background:linear-gradient(180deg,#7895ed,#4563c5); border-radius:6px 6px 2px 2px; }
.bar-label { color:#8792a5; font-size:10px; margin-top:6px; white-space:nowrap; transform:rotate(-30deg); transform-origin:top center; }
.split { display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:18px; }.split h3 { margin:0 0 9px; font-size:13px; color:#53627b; }
.row { display:flex; justify-content:space-between; gap:10px; padding:7px 0; border-bottom:1px solid #eef1f6; font-size:12px; }
.row:last-child { border-bottom:0; }.row-name { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }.row-value { color:#425fc1; white-space:nowrap; font-weight:650; }
.consumption { display:grid; grid-template-columns:1fr 1fr; gap:10px; }.consumption-card { padding:12px; background:#f7f9fd; border-radius:10px; }
.consumption-card small { display:block; color:#7d899e; font-size:11px; }.consumption-card b { display:block; margin-top:5px; font-size:19px; color:#243b7a; }
.task { padding:10px 0; border-bottom:1px solid #eef1f6; }.task:last-child { border-bottom:0; }.task-head { display:flex; justify-content:space-between; gap:12px; font-size:13px; font-weight:650; }.task-meta { margin-top:5px; color:#7a879c; font-size:11px; }
.empty { padding:26px 0; color:#98a3b5; text-align:center; font-size:13px; }.footer { margin-top:17px; color:#8a96aa; font-size:11px; text-align:right; }
</style></head><body><main class="page">
<header class="header"><div><div class="eyebrow">DAILY ANALYISIS · GSCORE</div><h1>运行总览与统计</h1></div><div class="time">生成时间：__GENERATED_AT__</div></header>
<section class="metrics"><div class="metric"><div class="metric-label">今日分析任务</div><div class="metric-value">__TODAY_TRACES__</div></div><div class="metric"><div class="metric-label">今日活跃群</div><div class="metric-value">__TODAY_GROUPS__</div></div><div class="metric"><div class="metric-label">总分析次数</div><div class="metric-value">__TOTAL_TRACES__</div></div><div class="metric"><div class="metric-label">成功率</div><div class="metric-value">__SUCCESS_RATE__</div></div><div class="metric"><div class="metric-label">平均耗时</div><div class="metric-value">__AVG_DURATION__</div></div></section>
<section class="layout"><div class="panel"><div class="panel-title"><strong>近 14 日趋势</strong><span>请求次数 / Token</span></div><div class="chart">__CHART__</div><div class="split"><div><h3>服务商消耗</h3>__PROVIDERS__</div><div><h3>模型消耗</h3>__MODELS__</div></div></div>
<div class="panel"><div class="panel-title"><strong>Token 与成本消耗</strong><span>累计 / 今日</span></div><div class="consumption"><div class="consumption-card"><small>累计 Token</small><b>__TOTAL_TOKENS__</b></div><div class="consumption-card"><small>今日 Token</small><b>__TODAY_TOKENS__</b></div><div class="consumption-card"><small>累计成本</small><b>__TOTAL_COST__</b></div><div class="consumption-card"><small>今日成本</small><b>__TODAY_COST__</b></div></div><div class="panel-title" style="margin-top:24px;"><strong>当前运行任务</strong><span>__TASK_COUNT__ 个</span></div>__TASKS__</div></section>
<div class="footer">DailyAnalyisis</div></main></body></html>
"""
    for marker, value in summary_values.items():
        template = template.replace(marker, value)
    return template


__all__ = ["build_overview_html"]
