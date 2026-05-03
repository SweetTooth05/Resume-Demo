# Finance Management App — Project Context

## 0. Vision & Problem Statement

As the world moves more and more toward AI-driven and algorithmic trading, sophisticated financial reasoning is increasingly gated behind expensive advisors, opaque robo-advisor subscriptions, or cloud SaaS tools that demand the user surrender raw bank data to a third party.

This project's goal is to make AI-assisted personal finance available to a wider demographic of retail investors by shipping a **fully local desktop application** that:

1. Ingests the user's real bank transactions and portfolio holdings.
2. Reasons over them using a **fine-tuned Small Language Model (SLM)** running entirely on-device.
3. Produces actionable, personalised recommendations to **save more, spend better, and grow net worth** — without sending a single transaction off the machine.

The non-goal is to be a stock-picking oracle or a substitute for a licensed financial adviser. The product is a **personal finance copilot** that explains *what is happening with your money* and *what to consider next*.

---

## 1. Customer & Customer Needs

### 1.1 Target User

- Australian retail investors (initial market — driven by the choice of Basiq + ASX data sources).
- Tech-comfortable: owns a laptop/desktop with a recent CPU and ideally an NPU/iGPU/dGPU.
- Privacy-conscious: unwilling to upload bank statements to cloud-based budgeting apps.
- Has at least one transaction account and ideally a brokerage / superannuation account.

### 1.2 Core Needs

- A **quick, glanceable overview** of net worth, cashflow, and portfolio health.
- **Plain-English recommendations** based on actual spending patterns (not generic "spend less on coffee" advice).
- Confidence that **financial data never leaves the device**.
- Reasoning they can **audit** — every recommendation must show its working.

### 1.3 Customer Journey (End-to-End)

1. **Install & First Launch** — User downloads a single signed Windows installer (`.msi` or `.exe`). On first launch the app verifies the bundled SLM weights, runs a hardware probe (see §3.2), and selects an inference backend.
2. **Onboarding Questionnaire** — User answers ~8–12 questions about financial priorities (e.g., short-term saving goal, risk tolerance, retirement horizon, dependents, debt position). These answers are stored locally and prepended to the SLM's system prompt as user context.
3. **Bank Connection** — User creates a Basiq developer account (free tier sufficient for personal use) and pastes their API key into the app. The app uses Basiq's CDR-compliant flow to pull transactions for the user's nominated institutions.
4. **Initial Sync** — App pulls 24 months of historical transactions, normalises them into "story-form" JSON (see §4 Phase 1), and builds a local SQLite-backed transaction store.
5. **Portfolio Connection (Optional)** — User adds ASX tickers and unit counts manually, or imports a CSV from CommSec / Stake / SelfWealth. App pulls market data via EODHD (or Yahoo Finance fallback).
6. **First Insight** — Within 60 seconds of sync completion, the SLM generates a first-look briefing: cashflow summary, top 3 spending categories, anomaly flags, and 3 prioritised recommendations.
7. **Ongoing Use** — User can chat with the assistant ("Can I afford a $3k holiday in October?"), view dashboards, and accept/dismiss recommendations. A scheduled background job re-syncs nightly.
8. **Export & Audit** — User can export every recommendation, the underlying calculation (via MCP tool trace), and the source transactions to a PDF/CSV report.

---

## 2. Product Requirements

### 2.1 Deployment Model

Because this product targets a wide range of retail investors, and because the **financial data is too sensitive to ship to a server**, the application is delivered as a **local-only desktop executable**. All inference, storage, and reasoning happen on the user's machine. The only outbound network calls are to:

- **Basiq API** — bank transaction retrieval (TLS 1.3, certificate pinning).
- **EODHD API** (or equivalent) — market data for ASX tickers.
- **Application update server** — signed delta updates only; opt-out available.

No telemetry, no analytics, no cloud sync.

### 2.2 Functional Requirements

| ID  | Requirement |
|-----|-------------|
| F1  | Connect to one or more Australian bank accounts via Basiq. |
| F2  | Categorise transactions automatically using a deterministic rules engine + SLM fallback for ambiguous merchants. |
| F3  | Display net worth, cashflow (weekly/monthly/yearly), and category breakdown dashboards. |
| F4  | Generate natural-language recommendations and let the user accept, snooze, or dismiss them. |
| F5  | Provide a chat interface for ad-hoc questions over the user's data. |
| F6  | Route every numeric calculation through an MCP tool, never letting the SLM compute math directly. |
| F7  | Allow the user to fully wipe local data with one click. |
| F8  | Support fully offline operation once data is synced (no network required for inference). |

### 2.3 Non-Functional Requirements

- **First-token latency** ≤ 1.5 s on a mid-range 2024 laptop (e.g., Ryzen 7 7840U, 16 GB RAM).
- **End-to-end recommendation generation** ≤ 15 s for a 12-month context window.
- **Cold start** (app launch to interactive) ≤ 8 s.
- **Disk footprint** ≤ 6 GB total (model + runtime + app shell).
- **RAM footprint at idle** ≤ 1 GB; ≤ 6 GB during active inference on a 7B Q4 model.
- **Crash-free sessions** ≥ 99.5 % across the supported hardware matrix.

### 2.4 Technical Specifications

- **Target OS:** Windows 11 (x64) for v1. macOS (Apple Silicon) and Linux are stretch targets.
- **App Shell:** Tauri 2.x (Rust backend + WebView frontend) — chosen over Electron for smaller binary, lower RAM, and better integration with native NPU/GPU runtimes.
- **Frontend:** React + TypeScript + Tailwind, with Recharts (or Apache ECharts) for visualisations.
- **Local Store:** SQLite via `rusqlite`, encrypted at rest with SQLCipher using a key derived from a user passphrase (Argon2id).
- **Inference Engine:** `llama.cpp` (CUDA / Vulkan / DirectML / OpenVINO backends selected at runtime).
- **Model:** Qwen 2.5 / Qwen 3 (3B for low-end, 7B for default) fine-tuned with QLoRA, merged, then quantised to 4-bit GGUF.
- **Tool Layer:** Local MCP server bundled in-process exposing `calculate`, `plot`, `query_transactions`, `forecast`, `compare_periods`, and `tax_estimate` tools.
- **External APIs:** Basiq (banking), EODHD (market data), RBA (cash rate, inflation reference).

---

## 3. Technical Architecture

### 3.1 High-Level Component Diagram

```text
+--------------------------------------------------------------+
|                      Tauri Desktop Shell                     |
|  +------------------+        +-----------------------------+ |
|  | React UI (Web)   | <----> | Rust Core (commands, IPC)   | |
|  +------------------+        +--------------+--------------+ |
|                                             |                |
|         +-----------------------------------+--------------+ |
|         |                                                  | |
|  +------v------+  +-------------+  +-----------+  +------v-+|
|  | SQLite +    |  | MCP Tool    |  | Basiq /   |  | llama. ||
|  | SQLCipher   |  | Server      |  | EODHD     |  | cpp    ||
|  | (txns,      |  | (calc, plot,|  | clients   |  | (Qwen  ||
|  |  prefs,     |  |  forecast,  |  | (TLS 1.3) |  | GGUF + ||
|  |  embeddings)|  |  query, …)  |  |           |  | TQ KV) ||
|  +-------------+  +-------------+  +-----------+  +--------+|
+--------------------------------------------------------------+
```

### 3.2 Hardware Detection & Backend Selection

To make inference as efficient as possible, on first launch the application runs a **hardware probe** and picks the best available `llama.cpp` backend. The matrix:

| Detected Hardware                       | Preferred Backend       | Notes |
|-----------------------------------------|-------------------------|-------|
| NVIDIA GPU (compute ≥ 7.5, ≥ 6 GB VRAM) | CUDA                    | Fastest path; offload all layers. |
| AMD GPU (RDNA2+) or AMD iGPU (780M+)    | Vulkan or ROCm (if installed) | Vulkan is the safer default on Windows. |
| Intel Arc / Intel Iris Xe / Intel NPU   | OpenVINO (NPU) or SYCL  | Use NPU for prefill, iGPU for decode. |
| CPU only (AVX2+)                        | CPU (`-t` = physical cores) | Falls back to 3B model automatically. |

The probe is implemented in the Rust core via `wgpu` adapter enumeration plus vendor-specific SDK calls (NVML, ADLX, Intel Level Zero) and writes the chosen profile to `%APPDATA%/FinanceCopilot/hardware.json`.

### 3.3 Data Flow for a Single Recommendation

1. User asks a question (or scheduled job fires).
2. Rust core retrieves the relevant transactions from SQLite (RAG-style: BM25 + sentence-embedding hybrid, k≈40).
3. Context is rendered into "story-form" JSON and packed into the SLM's prompt window.
4. SLM responds either with prose reasoning **or** an MCP tool call.
5. If a tool call is emitted, the Rust core dispatches it, captures the result, and feeds it back into the SLM.
6. Final response is rendered in the UI, with a collapsible "show working" panel that exposes every tool call and its arguments.

---

## 4. Roadmap & Pipeline

### Phase 1 — Data Lake Construction

- **Bank Feeds:** Pull 24 months of transactions via Basiq (or, for the bootstrapping phase, export CSV from internet banking). A normaliser script converts each transaction into "story-form" JSON.
  - Example: `"On 2026-03-15, I spent $65 at Woolworths, which is 15% higher than my average Saturday grocery spend and 22% above my 90-day rolling Woolworths average."`
- **ASX Context:** Fetch daily OHLCV plus fundamental ratios for portfolio tickers via the EODHD API. Cache locally with daily TTL.
- **Macro Context:** Fetch RBA cash rate and ABS CPI prints monthly.
- **Synthesis:** Combine personal + market + macro records into a single JSONL training file. Target ~15k–25k records for SFT.

### Phase 2 — Supervised Fine-Tuning ("SFT" Stage)

- Apply **QLoRA** to a Qwen 2.5 / Qwen 3 base model (3B for the low-spec build, 7B for the default build).
- **Objective:** Teach the model to (a) reason in the financial domain in plain English, and (b) recognise when a numeric/visual question is being asked and respond *only* with an MCP tool call.
- **Dataset Mix (50/50):**
  - Personal-finance reasoning examples (anonymised synthetic + author's own data).
  - Tool-use examples, e.g. `Q: "What's my portfolio ROI year-to-date?" → A: <tool_call name="calculate_roi" args={"start": "2026-01-01"}/>`.
- **Validation:** Held-out 10% split, evaluated on (i) tool-call precision/recall, (ii) numerical hallucination rate, (iii) human rubric on recommendation quality.

### Phase 3 — TurboQuant Optimisation

- **Merge & Quantise:** Merge LoRA adapters back into the base Qwen model and quantise to **4-bit GGUF** (Q4_K_M).
- **Activate TurboQuant:** Configure the inference engine to use a **3.5-bit TurboQuant KV-cache**.
- **Why?** This allows the entire 12-month transaction history to sit in the model's active context (≈ 32k+ tokens) without slowing decode, so the model can cross-reference old transactions when answering new questions.

### Phase 4 — App Integration & Beta

- Wrap inference, MCP tools, and SQLite store inside the Tauri shell.
- Build the dashboard, chat, and recommendation UI surfaces.
- Run a closed beta with 5–10 users (friends/family) for 4 weeks.
- Iterate on recommendation quality based on accept/dismiss telemetry (collected **only locally**, surfaced to the user as their own analytics).

### Phase 5 — Public Release

- Sign and notarise the Windows installer.
- Publish a static landing page (no account system, no telemetry).
- Open-source the MCP tool layer and the data-prep pipeline; keep the fine-tuned weights as a separate downloadable artefact.

### Suggested Timeline (solo developer)

| Phase | Duration |
|-------|----------|
| 1 — Data lake | 3 weeks |
| 2 — SFT       | 4 weeks (incl. iteration) |
| 3 — TurboQuant | 1 week |
| 4 — App + Beta | 8 weeks |
| 5 — Release   | 2 weeks |
| **Total**     | **~18 weeks** |

---

## 5. Training Configuration

To make model training as efficient as possible, the following hyperparameters are recommended for the QLoRA stage:

| Hyperparameter   | Recommended Value                  | Reason                                                                          |
|------------------|------------------------------------|---------------------------------------------------------------------------------|
| Rank (r)         | 32 or 64                           | Financial data requires higher rank to capture precise numerical relationships. |
| Alpha            | 128                                | Keeps the adapter weight significant compared to the base model.                |
| Learning Rate    | 2 × 10⁻⁴                           | Standard for SLMs; prevents catastrophic forgetting.                            |
| Batch Size       | 4 (with gradient accumulation = 8) | Fits within iGPU / consumer-GPU memory limits.                                  |
| Target Modules   | All linear layers                  | Crucial for Qwen models to understand structured data like CSVs and JSONL.      |
| Epochs           | 2–3                                | Avoid overfitting on a small personal dataset.                                  |
| LR Schedule      | Cosine with 3% warmup              | Smooth convergence on small datasets.                                           |
| Weight Decay     | 0.01                               | Mild regularisation.                                                            |
| Max Seq Length   | 4096 (training) / 32k+ (inference) | Long enough to fit a full month of transactions per training example.           |
| Precision        | NF4 base + bf16 LoRA               | QLoRA standard.                                                                 |

### Quantization Process Using TurboQuant

Once the model is tuned and merged, TurboQuant is applied to the **KV cache** during inference. The following sketch illustrates the intended setup:

```python
import torch
from transformers import AutoModelForCausalLM
from turboquant import TurboQuantCache  # 2026 community implementation

model = AutoModelForCausalLM.from_pretrained(
    "./my-finance-qwen-tuned",
    device_map="auto",
)

cache = TurboQuantCache(bits=3.5, method="polar_qjl")

model.config.use_cache = True
model.set_kv_cache(cache)
```

In production the same model is exported to GGUF and loaded by `llama.cpp` with the equivalent TQ-KV flag enabled, so the Python stack above is **only used during training/research** — the shipped app does not bundle PyTorch.

---

## 6. Output Quality & Reasoning Assurance

To guarantee the quality and trustworthiness of recommendations, **reasoning and calculation are strictly separated**.

- The SLM is responsible for **language, framing, and judgement**.
- All numeric work — graphing, aggregation, forecasting, ROI/IRR/tax math — is delegated to **MCP tools** running in the Rust core.

Bundled MCP tools (v1):

| Tool               | Purpose                                                                |
|--------------------|------------------------------------------------------------------------|
| `calculate`        | Exact arbitrary-precision arithmetic. Replaces the model's mental math.|
| `query_transactions` | Structured query over the SQLite store (by date, category, merchant).|
| `aggregate`        | Sum / avg / min / max / percentile over a query result.                |
| `forecast`         | Time-series forecast (Holt-Winters or Prophet) for cashflow.           |
| `compare_periods`  | Diff two date ranges and return deltas + significance.                 |
| `plot`             | Render a chart spec (Vega-Lite) and return an image handle.            |
| `tax_estimate`     | ATO-rule-based PAYG and CGT estimator.                                 |

Every model response that contains a numeric claim **must** be backed by a recorded tool call. The UI exposes this as a "Show working" toggle.

### 6.1 Evaluation Harness

- **Numeric hallucination rate** — fraction of model claims unbacked by a tool call. Target: 0%.
- **Recommendation acceptance rate** — fraction of generated recommendations the user accepts (locally measured).
- **Tool-call precision/recall** — measured against a held-out set of 200 hand-labelled prompts.
- **Latency budget compliance** — see §2.3.

---

## 7. Security & Governance

Because the data is highly sensitive, the following controls are **non-negotiable**:

- **Local-first by construction.** All transaction data, embeddings, and model state stay on the user's device. The SLM never receives data over the network.
- **Encryption at rest.** SQLite database encrypted with SQLCipher; key derived from a user passphrase via Argon2id (memory cost 64 MiB, 3 iterations). Passphrase is never persisted.
- **Encryption in transit.** All API calls (Basiq, EODHD) use **TLS 1.3**, with **certificate pinning** to defeat MITM via rogue CAs.
- **API key handling.** Basiq and EODHD API keys are stored in the OS credential vault (Windows Credential Manager / macOS Keychain / Secret Service on Linux), never in plaintext config.
- **Memory hygiene.** Sensitive buffers (decrypted DB pages, raw API responses) are zeroed on drop using `zeroize`.
- **Code signing.** Windows installer is signed with an EV certificate; updates are signature-verified before apply (Tauri's built-in updater with a custom public key).
- **Sandboxed model execution.** The `llama.cpp` process is launched without network capabilities (Windows AppContainer / Linux seccomp profile).
- **Auditability.** A local-only structured log records every tool call, every API call, and every model prompt+response, with one-click export and one-click wipe.
- **Reproducibility.** Model weights are content-addressed (SHA-256) and verified on launch; tampering aborts startup.
- **Dependency hygiene.** `cargo audit` and `npm audit` run in CI; SBOM (CycloneDX) shipped with each release.
- **No telemetry.** Period. Crash dumps are local and require explicit user action to share.

---

## 8. Risks & Mitigations

| Risk                                                       | Likelihood | Impact | Mitigation                                                                                          |
|------------------------------------------------------------|------------|--------|-----------------------------------------------------------------------------------------------------|
| TurboQuant 3.5-bit KV is unstable on certain hardware      | Medium     | High   | Fall back to standard Q8 KV automatically; expose toggle in advanced settings.                       |
| Basiq free tier rate limits or pricing changes              | Medium     | High   | Abstract the bank-data interface; add CSV import + Akahu (NZ) + Plaid (US) adapters in v2.           |
| Model gives bad financial advice                            | Medium     | High   | Prominent in-product disclaimer; recommendations framed as "consider", never "do this"; tool-grounded math eliminates the most dangerous (numeric) errors. |
| Hardware too weak to run 7B model                           | High       | Medium | Auto-fallback to 3B; clearly communicate model tier in the UI.                                       |
| Regulatory exposure (giving "financial advice" in AU)       | Low–Medium | High   | Position as an *information and analytics* tool, not personal advice; obtain ASIC RG 36 review before public launch. |
| Model fine-tuning overfits author's own data                | Medium     | Medium | 50/50 mix with synthetic + public examples; held-out eval set; periodic re-tuning.                   |

---

## 9. Success Metrics (v1)

- **Activation:** ≥ 70% of installs reach a successful first sync within 24 hours.
- **Insight relevance:** ≥ 60% recommendation acceptance rate among beta users.
- **Performance:** Latency targets in §2.3 met on 90% of supported hardware.
- **Trust:** 0% numeric-hallucination rate in the eval harness across 3 consecutive releases.
- **Retention (personal use):** Author opens the app ≥ 4×/week for 8 consecutive weeks post-v1.

---

## 10. Out of Scope (for v1)

- Mobile apps (iOS/Android).
- Direct order execution / brokerage integration.
- Multi-user / household accounts.
- Cloud sync between devices.
- Tax filing (estimation only, not lodgement).
- Crypto wallets (consider for v2 via read-only addresses).

---

## 11. Future Extensions

- **v2:** macOS (Apple Silicon, Metal backend), Akahu (NZ) and Plaid (US) bank adapters, crypto read-only wallets.
- **v3:** Optional encrypted peer-to-peer sync between the user's own devices (no server).
- **v3:** Goal-based scenario simulator ("What happens to my retirement if I increase super contributions by 2%?").
- **v4:** Pluggable strategy modules for users who *do* want algorithmic trading suggestions on the ASX, with paper-trading mode by default.
