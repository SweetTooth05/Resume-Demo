/// Manages a llama-server subprocess and streams tokens back as Tauri events.
///
/// Architecture:
///   1. On first chat, start llama-server pointing at model.gguf
///   2. POST /v1/chat/completions with stream=true
///   3. Parse SSE lines, emit "chat-token" Tauri events per chunk
///   4. Emit "chat-done" when stream ends
///   5. llama-server stays alive between chats (model stays loaded in RAM/VRAM)
///
/// Model path resolution (in order):
///   1. FINANCE_COPILOT_MODEL_PATH env var
///   2. <app_data_dir>/model.gguf
///   3. <exe_dir>/resources/model.gguf
use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::{AppHandle, Emitter};

const SERVER_PORT: u16 = 18_422;
const SERVER_STARTUP_TIMEOUT_SECS: u64 = 30;
const CTX_SIZE: u32 = 32_768;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChatTokenEvent {
    pub message_id: String,
    pub token: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChatDoneEvent {
    pub message_id: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChatErrorEvent {
    pub message_id: String,
    pub error: String,
}

pub struct InferenceManager {
    server_process: Arc<Mutex<Option<Child>>>,
    model_path: PathBuf,
    backend_flags: Vec<String>,
}

impl InferenceManager {
    pub fn new(model_path: PathBuf, backend_flags: Vec<String>) -> Self {
        Self {
            server_process: Arc::new(Mutex::new(None)),
            model_path,
            backend_flags,
        }
    }

    pub fn ensure_server_running(&self) -> Result<()> {
        let mut guard = self.server_process.lock().unwrap();

        if let Some(ref mut child) = *guard {
            if child.try_wait()?.is_none() {
                return Ok(()); // still alive
            }
        }

        if !self.model_path.exists() {
            return Err(anyhow!(
                "Model not found at {:?}. Place your fine-tuned finance-qwen-Q4_K_M.gguf there.",
                self.model_path
            ));
        }

        let server_bin = find_server_binary()?;
        log::info!("Starting llama-server: {:?}", server_bin);

        let mut cmd = Command::new(&server_bin);
        cmd.arg("-m").arg(&self.model_path)
           .arg("--port").arg(SERVER_PORT.to_string())
           .arg("-c").arg(CTX_SIZE.to_string())
           .arg("--host").arg("127.0.0.1")
           .arg("-np").arg("1")
           .arg("--log-disable")
           .stdout(Stdio::null())
           .stderr(Stdio::null());

        for flag in &self.backend_flags {
            cmd.arg(flag);
        }

        let child = cmd.spawn()
            .map_err(|e| anyhow!("Failed to start llama-server: {}", e))?;
        *guard = Some(child);
        drop(guard);

        self.wait_for_ready()?;
        log::info!("llama-server ready on port {}", SERVER_PORT);
        Ok(())
    }

    fn wait_for_ready(&self) -> Result<()> {
        let start = std::time::Instant::now();
        loop {
            if start.elapsed() > Duration::from_secs(SERVER_STARTUP_TIMEOUT_SECS) {
                return Err(anyhow!(
                    "llama-server did not start within {} seconds. Check model path and binary.",
                    SERVER_STARTUP_TIMEOUT_SECS
                ));
            }
            // Use std::net to check TCP port open (no blocking HTTP client in async context)
            if std::net::TcpStream::connect(format!("127.0.0.1:{}", SERVER_PORT)).is_ok() {
                // Port is open — give server 200 ms to finish its HTTP setup
                std::thread::sleep(Duration::from_millis(200));
                return Ok(());
            }
            std::thread::sleep(Duration::from_millis(500));
        }
    }

    pub fn stop(&self) {
        let mut guard = self.server_process.lock().unwrap();
        if let Some(ref mut child) = *guard {
            let _ = child.kill();
            let _ = child.wait();
        }
        *guard = None;
    }
}

/// Spawn a background task that streams a chat completion and emits Tauri events.
pub fn stream_chat(
    manager: Arc<InferenceManager>,
    app: AppHandle,
    message_id: String,
    messages: Vec<serde_json::Value>,
) {
    tokio::spawn(async move {
        // ensure_server_running blocks on TCP polling — run on dedicated thread
        let mgr = manager.clone();
        if let Err(e) = tokio::task::spawn_blocking(move || mgr.ensure_server_running()).await
            .unwrap_or_else(|e| Err(anyhow!("spawn_blocking panic: {}", e)))
        {
            let _ = app.emit("chat-error", ChatErrorEvent {
                message_id,
                error: e.to_string(),
            });
            return;
        }

        let url = format!("http://127.0.0.1:{}/v1/chat/completions", SERVER_PORT);
        let body = json!({
            "messages": messages,
            "stream": true,
            "temperature": 0.7,
            "max_tokens": 1024,
        });

        let client = reqwest::Client::new();
        let response = match client.post(&url).json(&body).send().await {
            Ok(r) => r,
            Err(e) => {
                let _ = app.emit("chat-error", ChatErrorEvent {
                    message_id,
                    error: format!("llama-server request failed: {}", e),
                });
                return;
            }
        };

        // Parse SSE stream manually — chunk-by-chunk, line-splitting
        let mut line_buf = String::new();
        let mut byte_stream = response;

        loop {
            let chunk = match byte_stream.chunk().await {
                Ok(Some(c)) => c,
                Ok(None) => break,
                Err(e) => {
                    log::warn!("Stream read error: {}", e);
                    break;
                }
            };

            line_buf.push_str(&String::from_utf8_lossy(&chunk));

            while let Some(newline_pos) = line_buf.find('\n') {
                let line = line_buf[..newline_pos].trim().to_string();
                line_buf = line_buf[newline_pos + 1..].to_string();

                if line.is_empty() || line == "data: [DONE]" {
                    continue;
                }
                let json_str = line.strip_prefix("data: ").unwrap_or(&line);
                if let Ok(chunk_val) = serde_json::from_str::<serde_json::Value>(json_str) {
                    if let Some(token) = chunk_val["choices"][0]["delta"]["content"].as_str() {
                        let _ = app.emit("chat-token", ChatTokenEvent {
                            message_id: message_id.clone(),
                            token: token.to_string(),
                        });
                    }
                }
            }
        }

        let _ = app.emit("chat-done", ChatDoneEvent { message_id });
    });
}

pub fn resolve_model_path(app_data_dir: &Path) -> PathBuf {
    if let Ok(env_path) = std::env::var("FINANCE_COPILOT_MODEL_PATH") {
        return PathBuf::from(env_path);
    }
    app_data_dir.join("model.gguf")
}

pub fn backend_flags_for_profile(backend: &str, vram_gb: Option<f64>) -> Vec<String> {
    let mut flags = Vec::new();
    match backend {
        "cuda" | "vulkan" => {
            let layers = vram_to_gpu_layers(vram_gb);
            flags.push("-ngl".to_string());
            flags.push(layers.to_string());
        }
        "openvino" => {
            flags.push("--device".to_string());
            flags.push("GPU".to_string());
        }
        _ => {
            let threads = std::thread::available_parallelism()
                .map(|n| n.get())
                .unwrap_or(4);
            flags.push("-t".to_string());
            flags.push(threads.to_string());
        }
    }
    flags
}

fn vram_to_gpu_layers(vram_gb: Option<f64>) -> u32 {
    match vram_gb.unwrap_or(0.0) as u32 {
        v if v >= 12 => 99,
        v if v >= 8  => 28,
        v if v >= 6  => 20,
        _            => 10,
    }
}

fn find_server_binary() -> Result<PathBuf> {
    let candidates: Vec<PathBuf> = vec![
        std::env::current_exe()
            .unwrap_or_default()
            .parent()
            .unwrap_or(Path::new("."))
            .join("resources/llama-server"),
        PathBuf::from("llama-server"),
        PathBuf::from("llama-server.exe"),
    ];

    for candidate in candidates {
        if candidate.exists() || which_in_path(&candidate) {
            return Ok(candidate);
        }
    }

    Err(anyhow!(
        "llama-server binary not found. Build llama.cpp and place llama-server in resources/. \
         See: https://github.com/ggerganov/llama.cpp"
    ))
}

fn which_in_path(bin: &Path) -> bool {
    Command::new(bin)
        .arg("--version")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .is_ok()
}
