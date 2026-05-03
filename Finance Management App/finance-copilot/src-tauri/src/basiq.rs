/// Basiq API client — pulls transactions for Australian bank accounts.
///
/// Basiq API v3: https://api.basiq.io/reference
/// Auth: API key → short-lived JWT token (1 hour TTL)
/// Rate limits: 50 req/min on free tier
use anyhow::{anyhow, Result};
use chrono::{Duration, NaiveDate, Utc};
use serde::{Deserialize, Serialize};
use zeroize::Zeroize;

const BASIQ_BASE: &str = "https://au-api.basiq.io";

// ── Wire types ────────────────────────────────────────────────────────────────

#[derive(Deserialize)]
struct TokenResponse {
    access_token: String,
}

#[derive(Deserialize, Debug)]
pub struct BasiqAccount {
    pub id: String,
    pub name: String,
    #[serde(rename = "institutionName")]
    pub institution_name: String,
    #[serde(rename = "accountNo")]
    pub account_no: Option<String>,
    pub balance: Option<String>,
    #[serde(rename = "type")]
    pub account_type: Option<String>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct BasiqTransaction {
    pub id: String,
    #[serde(rename = "postDate")]
    pub post_date: String,
    pub description: String,
    pub amount: String,
    pub balance: Option<String>,
    pub category: Option<String>,
    #[serde(rename = "subCategory")]
    pub sub_category: Option<String>,
    #[serde(rename = "merchant")]
    pub merchant: Option<BasiqMerchant>,
    #[serde(rename = "account")]
    pub account: BasiqRef,
}

#[derive(Deserialize, Debug, Clone)]
pub struct BasiqMerchant {
    pub name: Option<String>,
    #[serde(rename = "logoUrl")]
    pub logo_url: Option<String>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct BasiqRef {
    pub id: String,
}

#[derive(Deserialize)]
struct AccountsResponse {
    data: Vec<BasiqAccount>,
}

#[derive(Deserialize)]
struct TransactionsResponse {
    data: Vec<BasiqTransaction>,
    links: Option<PaginationLinks>,
}

#[derive(Deserialize)]
struct PaginationLinks {
    next: Option<String>,
}

// ── Client ───────────────────────────────────────────────────────────────────

pub struct BasiqClient {
    http: reqwest::blocking::Client,
    token: Option<String>,
    user_id: Option<String>,
}

impl BasiqClient {
    pub fn new() -> Self {
        let http = reqwest::blocking::Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .expect("failed to build HTTP client");
        Self { http, token: None, user_id: None }
    }

    /// Exchange API key for a short-lived JWT. Call once per session.
    pub fn authenticate(&mut self, api_key: &str) -> Result<()> {
        let response: TokenResponse = self.http
            .post(format!("{}/token", BASIQ_BASE))
            .header("Authorization", format!("Basic {}", base64_encode(api_key)))
            .header("Content-Type", "application/x-www-form-urlencoded")
            .header("basiq-version", "3.0")
            .body("scope=SERVER_ACCESS")
            .send()?
            .error_for_status()
            .map_err(|e| anyhow!("Basiq auth failed: {}", e))?
            .json()?;

        self.token = Some(response.access_token);

        // Retrieve or create the user associated with this key
        self.user_id = Some(self.get_or_create_user()?);
        Ok(())
    }

    fn bearer(&self) -> Result<String> {
        self.token.as_ref()
            .map(|t| format!("Bearer {}", t))
            .ok_or_else(|| anyhow!("Not authenticated. Call authenticate() first."))
    }

    fn get_or_create_user(&self) -> Result<String> {
        #[derive(Deserialize)]
        struct UsersResponse { data: Vec<serde_json::Value> }
        #[derive(Deserialize)]
        struct UserObj { id: String }

        let bearer = self.bearer()?;
        let resp: UsersResponse = self.http
            .get(format!("{}/users", BASIQ_BASE))
            .header("Authorization", &bearer)
            .header("basiq-version", "3.0")
            .send()?
            .error_for_status()?
            .json()?;

        if let Some(user) = resp.data.first() {
            if let Some(id) = user["id"].as_str() {
                return Ok(id.to_string());
            }
        }

        // Create a new user
        let user: UserObj = self.http
            .post(format!("{}/users", BASIQ_BASE))
            .header("Authorization", &bearer)
            .header("basiq-version", "3.0")
            .header("Content-Type", "application/json")
            .json(&serde_json::json!({"email": "user@local.device"}))
            .send()?
            .error_for_status()?
            .json()?;

        Ok(user.id)
    }

    pub fn list_accounts(&self) -> Result<Vec<BasiqAccount>> {
        let user_id = self.user_id.as_ref()
            .ok_or_else(|| anyhow!("Not authenticated"))?;
        let bearer = self.bearer()?;

        let resp: AccountsResponse = self.http
            .get(format!("{}/users/{}/accounts", BASIQ_BASE, user_id))
            .header("Authorization", &bearer)
            .header("basiq-version", "3.0")
            .send()?
            .error_for_status()?
            .json()?;

        Ok(resp.data)
    }

    /// Fetch all transactions for the last `months` months, paginating automatically.
    pub fn fetch_transactions(&self, months: u32) -> Result<Vec<BasiqTransaction>> {
        let user_id = self.user_id.as_ref()
            .ok_or_else(|| anyhow!("Not authenticated"))?;
        let bearer = self.bearer()?;

        let from_date = (Utc::now() - Duration::days(months as i64 * 30))
            .format("%Y-%m-%d").to_string();

        let mut all: Vec<BasiqTransaction> = Vec::new();
        let mut url = Some(format!(
            "{}/users/{}/transactions?filter[postDate.from]={}&limit=500",
            BASIQ_BASE, user_id, from_date
        ));

        while let Some(next_url) = url {
            let resp: TransactionsResponse = self.http
                .get(&next_url)
                .header("Authorization", &bearer)
                .header("basiq-version", "3.0")
                .send()?
                .error_for_status()?
                .json()?;

            all.extend(resp.data);
            url = resp.links.and_then(|l| l.next);

            // Respect free tier: 50 req/min
            std::thread::sleep(std::time::Duration::from_millis(200));
        }

        Ok(all)
    }
}

// ── Normalisation to story-form ───────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct NormalisedTransaction {
    pub id: String,
    pub post_date: NaiveDate,
    pub merchant_name: String,
    pub merchant_logo_url: Option<String>,
    pub description: String,
    pub amount_aud: f64,
    pub running_balance: f64,
    pub category: String,
    pub subcategory: Option<String>,
    pub account_id: String,
    pub story_form: String,
}

pub fn normalise(tx: &BasiqTransaction, account_name: &str) -> Option<NormalisedTransaction> {
    let amount: f64 = tx.amount.parse().ok()?;
    let balance: f64 = tx.balance.as_deref().unwrap_or("0").parse().unwrap_or(0.0);
    let post_date = NaiveDate::parse_from_str(&tx.post_date[..10], "%Y-%m-%d").ok()?;
    let merchant_name = tx.merchant.as_ref()
        .and_then(|m| m.name.clone())
        .unwrap_or_else(|| tx.description.clone());
    let logo_url = tx.merchant.as_ref().and_then(|m| m.logo_url.clone());
    let category = tx.category.clone().unwrap_or_else(|| "other".to_string());

    let story = build_story(post_date, &merchant_name, amount, &category, account_name);

    Some(NormalisedTransaction {
        id: tx.id.clone(),
        post_date,
        merchant_name,
        merchant_logo_url: logo_url,
        description: tx.description.clone(),
        amount_aud: amount,
        running_balance: balance,
        category: category.to_lowercase(),
        subcategory: tx.sub_category.clone(),
        account_id: tx.account.id.clone(),
        story_form: story,
    })
}

fn build_story(date: NaiveDate, merchant: &str, amount: f64, category: &str, account: &str) -> String {
    let date_str = date.format("%Y-%m-%d");
    if amount > 0.0 {
        format!("On {}, I received ${:.2} into {} ({}).", date_str, amount, account, category)
    } else {
        format!("On {}, I spent ${:.2} at {} ({}) from {}.", date_str, amount.abs(), merchant, category, account)
    }
}

fn base64_encode(s: &str) -> String {
    const ALPHABET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let bytes = s.as_bytes();
    let mut out = String::with_capacity((bytes.len() + 2) / 3 * 4);
    let mut i = 0;
    while i < bytes.len() {
        let b0 = bytes[i] as usize;
        let b1 = if i + 1 < bytes.len() { bytes[i + 1] as usize } else { 0 };
        let b2 = if i + 2 < bytes.len() { bytes[i + 2] as usize } else { 0 };
        out.push(ALPHABET[(b0 >> 2) & 0x3F] as char);
        out.push(ALPHABET[((b0 & 0x3) << 4) | ((b1 >> 4) & 0xF)] as char);
        out.push(if i + 1 < bytes.len() { ALPHABET[((b1 & 0xF) << 2) | ((b2 >> 6) & 0x3)] as char } else { '=' });
        out.push(if i + 2 < bytes.len() { ALPHABET[b2 & 0x3F] as char } else { '=' });
        i += 3;
    }
    out
}

impl Drop for BasiqClient {
    fn drop(&mut self) {
        if let Some(ref mut t) = self.token {
            t.zeroize();
        }
    }
}
