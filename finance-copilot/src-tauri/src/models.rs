use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub id: String,
    pub date: DateTime<Utc>,
    pub merchant_name: String,
    pub merchant_logo_url: Option<String>,
    pub description: String,
    pub amount: f64,
    pub running_balance: f64,
    pub category: String,
    pub subcategory: Option<String>,
    pub account_id: String,
    pub account_name: String,
    pub tags: Vec<String>,
    pub is_anomaly: bool,
    pub anomaly_reason: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Holding {
    pub ticker: String,
    pub name: String,
    pub units: f64,
    pub avg_cost_basis: f64,
    pub current_price: f64,
    pub previous_close: f64,
    pub market_value_aud: f64,
    pub unrealised_pnl: f64,
    pub unrealised_pnl_pct: f64,
    pub allocation_pct: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpToolCall {
    pub tool_name: String,
    pub args: serde_json::Value,
    pub result: serde_json::Value,
    pub duration_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Recommendation {
    pub id: String,
    pub title: String,
    pub body: String,
    pub confidence: f64,
    pub category: String,
    pub priority: String,
    pub status: String,
    pub generated_at: DateTime<Utc>,
    pub mcp_calls: Vec<McpToolCall>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HardwareProfile {
    pub backend: String,
    pub model_tier: String,
    pub gpu_name: Option<String>,
    pub vram_gb: Option<f64>,
    pub ram_gb: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub id: String,
    pub role: String,
    pub content: String,
    pub mcp_calls: Vec<McpToolCall>,
}
