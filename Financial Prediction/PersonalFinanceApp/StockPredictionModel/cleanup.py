"""
Cleanup script to remove unused files and consolidate directory structure
"""

import os
import shutil
import glob
from pathlib import Path
from datetime import datetime, timedelta

def cleanup_directory():
    """Clean up the StockPredictionModel directory"""
    
    base_dir = Path(__file__).parent
    print(f"Cleaning up directory: {base_dir}")
    
    # Files to remove (unused or redundant)
    files_to_remove = [
        'FinanceModel.py',  # Old model file, replaced by enhanced_model.py
        'test_improvements.py',  # Test file that's no longer needed
        'setup_cuda.py',  # CUDA setup is now handled in enhanced_model.py
        'model_accuracy_test_results.png',  # Old test results
        'xgboost_training.log',  # Old training log
        'finance_scraping.log',  # Old scraping log
        'IMPROVEMENTS.md',  # Documentation that's no longer relevant
        'data_collector.py',  # Replaced by incremental_data_collector.py
    ]
    
    # Remove specified files
    for file_name in files_to_remove:
        file_path = base_dir / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"Removed: {file_name}")
            except Exception as e:
                print(f"Could not remove {file_name}: {e}")
    
    # Clean up old backup directories (keep only the latest 2)
    backup_dirs = ['backups', 'model_backups']
    for backup_dir_name in backup_dirs:
        backup_dir = base_dir / backup_dir_name
        if backup_dir.exists():
            # Get all backup subdirectories
            backup_subdirs = [d for d in backup_dir.iterdir() if d.is_dir()]
            backup_subdirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the latest 2 backups
            for old_backup in backup_subdirs[2:]:
                try:
                    shutil.rmtree(old_backup)
                    print(f"Removed old backup: {old_backup.name}")
                except Exception as e:
                    print(f"Could not remove {old_backup.name}: {e}")
    
    # Clean up old log files (keep only the latest)
    logs_dir = base_dir / 'logs'
    if logs_dir.exists():
        log_files = list(logs_dir.glob('*.log'))
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Keep only the latest log file
        for old_log in log_files[1:]:
            try:
                old_log.unlink()
                print(f"Removed old log: {old_log.name}")
            except Exception as e:
                print(f"Could not remove {old_log.name}: {e}")
    
    # Clean up __pycache__ directories
    pycache_dirs = list(base_dir.rglob('__pycache__'))
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            print(f"Removed: {pycache_dir}")
        except Exception as e:
            print(f"Could not remove {pycache_dir}: {e}")
    
    # Consolidate backup directories
    old_backup_dir = base_dir / 'model_backups'
    new_backup_dir = base_dir / 'backups'
    
    if old_backup_dir.exists() and new_backup_dir.exists():
        # Move remaining backups from old directory to new directory
        for backup_subdir in old_backup_dir.iterdir():
            if backup_subdir.is_dir():
                try:
                    new_path = new_backup_dir / backup_subdir.name
                    if not new_path.exists():
                        shutil.move(str(backup_subdir), str(new_path))
                        print(f"Moved backup: {backup_subdir.name}")
                except Exception as e:
                    print(f"Could not move {backup_subdir.name}: {e}")
        
        # Remove the old backup directory
        try:
            shutil.rmtree(old_backup_dir)
            print("Removed old backup directory: model_backups")
        except Exception as e:
            print(f"Could not remove model_backups directory: {e}")
    
    # Clean up empty directories
    empty_dirs = ['processed_data', 'logs']
    for dir_name in empty_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists() and not any(dir_path.iterdir()):
            try:
                dir_path.rmdir()
                print(f"Removed empty directory: {dir_name}")
            except Exception as e:
                print(f"Could not remove {dir_name}: {e}")
    
    # Create a clean directory structure
    clean_dirs = ['backups', 'logs', 'models', 'data']
    for dir_name in clean_dirs:
        dir_path = base_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"Ensured directory exists: {dir_name}")
    
    print("\nCleanup completed!")
    print("\nNew directory structure:")
    print_directory_structure(base_dir)

def print_directory_structure(base_dir, max_depth=2, current_depth=0):
    """Print the directory structure"""
    if current_depth > max_depth:
        return
    
    indent = "  " * current_depth
    
    for item in sorted(base_dir.iterdir()):
        if item.is_file():
            size = item.stat().st_size
            size_str = f" ({size} bytes)" if size > 0 else ""
            print(f"{indent}📄 {item.name}{size_str}")
        elif item.is_dir():
            print(f"{indent}📁 {item.name}/")
            print_directory_structure(item, max_depth, current_depth + 1)

if __name__ == "__main__":
    cleanup_directory() 