use anyhow::Result;
use serde_json::{json, Value};
use std::path::Path;
use std::time::Instant;
use crate::db;
use crate::models::McpToolCall;

pub enum McpTool {
    Calculate,
    QueryTransactions,
    Aggregate,
    Forecast,
    ComparePeriods,
    TaxEstimate,
    Plot,
}

impl McpTool {
    pub fn from_name(name: &str) -> Option<Self> {
        match name {
            "calculate"          => Some(Self::Calculate),
            "query_transactions" => Some(Self::QueryTransactions),
            "aggregate"          => Some(Self::Aggregate),
            "forecast"           => Some(Self::Forecast),
            "compare_periods"    => Some(Self::ComparePeriods),
            "tax_estimate"       => Some(Self::TaxEstimate),
            "plot"               => Some(Self::Plot),
            _ => None,
        }
    }

    pub fn execute(&self, args: &Value, db_path: Option<&Path>) -> Result<Value> {
        match self {
            Self::Calculate => execute_calculate(args),
            Self::QueryTransactions => execute_query_transactions(args, db_path),
            Self::Aggregate => execute_aggregate(args, db_path),
            Self::Forecast => execute_forecast(args, db_path),
            Self::ComparePeriods => execute_compare_periods(args, db_path),
            Self::TaxEstimate => execute_tax_estimate(args),
            Self::Plot => execute_plot(args),
        }
    }
}

pub fn dispatch(tool_name: &str, args: Value, db_path: Option<&Path>) -> Result<McpToolCall> {
    let start = Instant::now();
    let tool = McpTool::from_name(tool_name)
        .ok_or_else(|| anyhow::anyhow!("Unknown MCP tool: {}", tool_name))?;
    let result = tool.execute(&args, db_path)?;
    Ok(McpToolCall {
        tool_name: tool_name.to_string(),
        args,
        result,
        duration_ms: start.elapsed().as_millis() as u64,
    })
}

// ── calculate ─────────────────────────────────────────────────────────────────

fn execute_calculate(args: &Value) -> Result<Value> {
    let expr = args["expr"].as_str()
        .ok_or_else(|| anyhow::anyhow!("calculate: missing 'expr' argument"))?;
    let result = evalexpr::eval_number(expr)
        .map_err(|e| anyhow::anyhow!("Expression error: {}", e))?;
    Ok(json!({ "result": result, "expr": expr }))
}

// ── query_transactions ────────────────────────────────────────────────────────

fn execute_query_transactions(args: &Value, db_path: Option<&Path>) -> Result<Value> {
    let conn = open_db(db_path)?;
    let period = args["period"].as_str().unwrap_or("30d");
    let category = args["category"].as_str().filter(|s| *s != "all");
    let limit = args["limit"].as_i64().unwrap_or(100);

    let (date_from, date_to) = resolve_period(period);

    let q = db::TxQuery {
        limit,
        offset: 0,
        category,
        date_from: Some(&date_from),
        date_to: Some(&date_to),
        account_id: None,
    };

    let txns = db::query_transactions(&conn, &q)?;
    let total: f64 = txns.iter().map(|t| t.amount.abs()).sum();
    let count = txns.len();

    let rows: Vec<Value> = txns.iter().map(|t| json!({
        "id": t.id,
        "date": t.date.format("%Y-%m-%d").to_string(),
        "merchant": t.merchant_name,
        "amount": t.amount,
        "category": t.category,
    })).collect();

    Ok(json!({
        "transactions": rows,
        "total": total,
        "count": count,
        "period": period,
        "date_from": date_from,
        "date_to": date_to,
    }))
}

// ── aggregate ─────────────────────────────────────────────────────────────────

fn execute_aggregate(args: &Value, db_path: Option<&Path>) -> Result<Value> {
    let conn = open_db(db_path)?;
    let period = args["period"].as_str().unwrap_or("30d");
    let category = args["category"].as_str().filter(|s| *s != "all");
    let metric = args["metric"].as_str().unwrap_or("sum");

    let (date_from, date_to) = resolve_period(period);
    let agg = db::aggregate_transactions(&conn, category, &date_from, &date_to)?;

    let primary_value = match metric {
        "avg"   => agg.avg,
        "min"   => agg.min,
        "max"   => agg.max,
        "count" => agg.count as f64,
        _       => agg.sum,
    };

    Ok(json!({
        "metric": metric,
        "value": primary_value,
        "sum": agg.sum,
        "avg": agg.avg,
        "min": agg.min,
        "max": agg.max,
        "count": agg.count,
        "period": period,
        "category": category,
    }))
}

// ── forecast ─────────────────────────────────────────────────────────────────

fn execute_forecast(args: &Value, db_path: Option<&Path>) -> Result<Value> {
    let conn = open_db(db_path)?;
    let months_ahead = args["months_ahead"].as_i64().unwrap_or(3).max(1).min(24);
    let category = args["category"].as_str().filter(|s| *s != "all");

    // Use 6-month history for linear trend
    let history = db::get_monthly_cashflow(&conn, 6)?;

    let expense_series: Vec<f64> = history.iter().map(|(_, _, exp)| *exp).collect();
    let income_series: Vec<f64> = history.iter().map(|(_, inc, _)| *inc).collect();

    let projected_expense = linear_forecast(&expense_series, months_ahead as usize);
    let projected_income = linear_forecast(&income_series, months_ahead as usize);

    let _ = category; // future: filter by category

    Ok(json!({
        "months_ahead": months_ahead,
        "projected_monthly_expense": projected_expense,
        "projected_monthly_income": projected_income,
        "projected_monthly_net": projected_income - projected_expense,
        "method": "linear_trend",
        "based_on_months": history.len(),
    }))
}

fn linear_forecast(series: &[f64], steps_ahead: usize) -> f64 {
    if series.is_empty() {
        return 0.0;
    }
    if series.len() == 1 {
        return series[0];
    }
    let n = series.len() as f64;
    let x_mean = (n - 1.0) / 2.0;
    let y_mean: f64 = series.iter().sum::<f64>() / n;
    let mut num = 0.0_f64;
    let mut den = 0.0_f64;
    for (i, &y) in series.iter().enumerate() {
        let x = i as f64;
        num += (x - x_mean) * (y - y_mean);
        den += (x - x_mean).powi(2);
    }
    let slope = if den.abs() > 1e-10 { num / den } else { 0.0 };
    let intercept = y_mean - slope * x_mean;
    let x_next = n - 1.0 + steps_ahead as f64;
    (intercept + slope * x_next).max(0.0)
}

// ── compare_periods ───────────────────────────────────────────────────────────

fn execute_compare_periods(args: &Value, db_path: Option<&Path>) -> Result<Value> {
    let conn = open_db(db_path)?;
    let category = args["category"].as_str().filter(|s| *s != "all");
    let current_period  = args["current_period"].as_str().unwrap_or("this_month");
    let comparison_period = args["comparison_period"].as_str().unwrap_or("last_month");

    let (cur_from, cur_to) = resolve_period(current_period);
    let (cmp_from, cmp_to) = resolve_period(comparison_period);

    let cur_agg = db::aggregate_transactions(&conn, category, &cur_from, &cur_to)?;
    let cmp_agg = db::aggregate_transactions(&conn, category, &cmp_from, &cmp_to)?;

    let delta = cur_agg.sum - cmp_agg.sum;
    let delta_pct = if cmp_agg.sum.abs() > 0.01 {
        (delta / cmp_agg.sum) * 100.0
    } else {
        0.0
    };
    let significant = delta_pct.abs() > 10.0 && cur_agg.count > 2;

    Ok(json!({
        "current_period":    current_period,
        "comparison_period": comparison_period,
        "current_total":     cur_agg.sum,
        "comparison_total":  cmp_agg.sum,
        "delta":             delta,
        "delta_pct":         delta_pct,
        "significant":       significant,
        "direction":         if delta > 0.0 { "higher" } else { "lower" },
    }))
}

// ── tax_estimate ──────────────────────────────────────────────────────────────
// ATO FY2025-26 resident individual rates + Medicare levy + LITO

fn execute_tax_estimate(args: &Value) -> Result<Value> {
    let income: f64 = args["income"].as_f64()
        .ok_or_else(|| anyhow::anyhow!("tax_estimate: missing 'income'"))?;
    let capital_gains: f64 = args["capital_gains"].as_f64().unwrap_or(0.0);
    let held_over_12m: bool = args["held_over_12m"].as_bool().unwrap_or(false);

    let cgt_discount = if held_over_12m { 0.5 } else { 1.0 };
    let net_capital_gain = capital_gains * cgt_discount;
    let taxable_income = income + net_capital_gain;

    let base_tax = ato_income_tax(taxable_income);
    let lito = low_income_tax_offset(taxable_income);
    let medicare = medicare_levy(taxable_income);

    let payg = (base_tax - lito + medicare).max(0.0);
    let effective_rate = if taxable_income > 0.0 { payg / taxable_income * 100.0 } else { 0.0 };

    Ok(json!({
        "taxable_income":   taxable_income,
        "gross_income":     income,
        "capital_gains":    capital_gains,
        "net_capital_gain": net_capital_gain,
        "cgt_discount_applied": held_over_12m,
        "base_tax":         base_tax,
        "lito":             lito,
        "medicare_levy":    medicare,
        "payg":             payg,
        "effective_rate_pct": effective_rate,
        "fy": "2025-26",
    }))
}

fn ato_income_tax(income: f64) -> f64 {
    if income <= 18_200.0 {
        0.0
    } else if income <= 45_000.0 {
        (income - 18_200.0) * 0.19
    } else if income <= 135_000.0 {
        5_092.0 + (income - 45_000.0) * 0.325
    } else if income <= 190_000.0 {
        34_342.0 + (income - 135_000.0) * 0.37
    } else {
        54_842.0 + (income - 190_000.0) * 0.45
    }
}

fn low_income_tax_offset(income: f64) -> f64 {
    if income <= 37_500.0 {
        700.0
    } else if income <= 45_000.0 {
        700.0 - (income - 37_500.0) * 0.05
    } else if income <= 66_667.0 {
        325.0 - (income - 45_000.0) * 0.015
    } else {
        0.0
    }
}

fn medicare_levy(income: f64) -> f64 {
    // FY2025-26: 2% above $26,000 (single, no reduction zone for simplicity)
    if income > 26_000.0 { income * 0.02 } else { 0.0 }
}

// ── plot ──────────────────────────────────────────────────────────────────────

fn execute_plot(args: &Value) -> Result<Value> {
    let chart_type = args["type"].as_str().unwrap_or("bar");
    let title = args["title"].as_str().unwrap_or("Chart");

    // Return a Vega-Lite spec skeleton; frontend renders it via Recharts
    Ok(json!({
        "spec_type": "vega-lite",
        "chart_type": chart_type,
        "title": title,
        "data": args.get("data").cloned().unwrap_or(json!([])),
        "note": "Frontend renders this spec via Recharts",
    }))
}

// ── helpers ───────────────────────────────────────────────────────────────────

fn open_db(db_path: Option<&Path>) -> Result<rusqlite::Connection> {
    let path = db_path.ok_or_else(|| anyhow::anyhow!("MCP tool requires DB access but no path provided"))?;
    db::get_connection(path)
}

fn resolve_period(period: &str) -> (String, String) {
    use chrono::{Datelike, Duration, Local, NaiveDate};

    let today = Local::now().date_naive();
    let fmt = |d: NaiveDate| d.format("%Y-%m-%d").to_string();

    match period {
        "7d"          => (fmt(today - Duration::days(7)),   fmt(today)),
        "30d"         => (fmt(today - Duration::days(30)),  fmt(today)),
        "60d"         => (fmt(today - Duration::days(60)),  fmt(today)),
        "90d"         => (fmt(today - Duration::days(90)),  fmt(today)),
        "180d"        => (fmt(today - Duration::days(180)), fmt(today)),
        "365d" | "ytd" => (fmt(NaiveDate::from_ymd_opt(today.year(), 1, 1).unwrap()), fmt(today)),
        "this_month"  => (fmt(NaiveDate::from_ymd_opt(today.year(), today.month(), 1).unwrap()), fmt(today)),
        "last_month"  => {
            let first_this = NaiveDate::from_ymd_opt(today.year(), today.month(), 1).unwrap();
            let last_prev  = first_this - Duration::days(1);
            let first_prev = NaiveDate::from_ymd_opt(last_prev.year(), last_prev.month(), 1).unwrap();
            (fmt(first_prev), fmt(last_prev))
        }
        "this_quarter" => {
            let q_start_month = ((today.month() - 1) / 3) * 3 + 1;
            (fmt(NaiveDate::from_ymd_opt(today.year(), q_start_month, 1).unwrap()), fmt(today))
        }
        "last_quarter" => {
            let q_start_month = ((today.month() - 1) / 3) * 3 + 1;
            let this_q_start = NaiveDate::from_ymd_opt(today.year(), q_start_month, 1).unwrap();
            let prev_q_end   = this_q_start - Duration::days(1);
            let prev_q_start_month = ((prev_q_end.month() - 1) / 3) * 3 + 1;
            let prev_q_start = NaiveDate::from_ymd_opt(prev_q_end.year(), prev_q_start_month, 1).unwrap();
            (fmt(prev_q_start), fmt(prev_q_end))
        }
        "fy" => {
            // Australian financial year: July 1 – June 30
            let fy_start_year = if today.month() >= 7 { today.year() } else { today.year() - 1 };
            (fmt(NaiveDate::from_ymd_opt(fy_start_year, 7, 1).unwrap()), fmt(today))
        }
        "all" => ("2000-01-01".to_string(), fmt(today)),
        // Fall back: treat as N days
        other => {
            let days: i64 = other.trim_end_matches('d').parse().unwrap_or(30);
            (fmt(today - Duration::days(days)), fmt(today))
        }
    }
}
