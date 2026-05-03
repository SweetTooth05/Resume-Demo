mod basiq;
mod commands;
mod db;
mod inference;
mod mcp;
mod models;

use std::path::PathBuf;
use std::sync::Arc;
use tauri::Manager;
use log::info;

/// Shared app state passed to every Tauri command.
pub struct AppState {
    pub db_path: PathBuf,
    pub inference: Arc<inference::InferenceManager>,
}

pub fn run() {
    env_logger::init();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .setup(|app| {
            info!("Finance Copilot starting up");

            let app_dir = app.path().app_data_dir()
                .expect("Failed to get app data dir");
            std::fs::create_dir_all(&app_dir)?;

            let db_path = app_dir.join("finance.db");
            db::init_db(&db_path).expect("Failed to initialize database");
            info!("Database initialized at {:?}", db_path);

            // Detect hardware profile and pick backend flags
            let hw = commands::probe_hardware();
            let model_path = inference::resolve_model_path(&app_dir);
            let backend_flags = inference::backend_flags_for_profile(&hw.backend, hw.vram_gb);
            info!("Hardware: {:?} — backend: {} — model: {:?}", hw.gpu_name, hw.backend, model_path);

            let inference_mgr = Arc::new(inference::InferenceManager::new(
                model_path,
                backend_flags,
            ));

            app.manage(AppState {
                db_path,
                inference: inference_mgr,
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_transactions,
            commands::sync_transactions,
            commands::get_holdings,
            commands::get_recommendations,
            commands::wipe_all_data,
            commands::run_mcp_tool,
            commands::detect_hardware,
            commands::send_chat_message,
            commands::save_api_keys,
            commands::get_api_keys,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
