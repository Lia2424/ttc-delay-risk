#!/usr/bin/env python3
"""
Clean up old model files, keeping only the latest model.
"""

from pathlib import Path
import sys

MODEL_DIR = Path(__file__).parent.parent / "model"

# Files to always keep
KEEP_FILES = {
    'delay_risk_model_latest.pkl'  # Required - API uses this
}


def cleanup_models():
    """Remove old model files, keeping only the latest."""
    print("=" * 70)
    print("CLEANING UP MODEL FILES")
    print("=" * 70)
    
    if not MODEL_DIR.exists():
        print(f"❌ Model directory not found: {MODEL_DIR}")
        return
    
    all_files = list(MODEL_DIR.glob('*'))
    
    if not all_files:
        print("✅ Model directory is already empty")
        return
    
    print(f"\nFound {len(all_files)} files in model directory")
    
    # Find files to delete
    files_to_delete = []
    total_size = 0
    
    for file_path in all_files:
        if file_path.name not in KEEP_FILES:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            files_to_delete.append((file_path, size_mb))
            total_size += size_mb
    
    if not files_to_delete:
        print("\n✅ No files to delete - only keeping required files")
        return
    
    print(f"\n📋 Files to DELETE ({len(files_to_delete)} files, {total_size:.1f} MB):")
    for file_path, size_mb in files_to_delete:
        print(f"   - {file_path.name} ({size_mb:.1f} MB)")
    
    print(f"\n📋 Files to KEEP:")
    for file_path in all_files:
        if file_path.name in KEEP_FILES:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {file_path.name} ({size_mb:.1f} MB)")
    
    # Confirm deletion
    print(f"\n⚠️  About to delete {len(files_to_delete)} files ({total_size:.1f} MB)")
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Cleanup cancelled")
        return
    
    # Delete files
    deleted_count = 0
    deleted_size = 0
    
    for file_path, size_mb in files_to_delete:
        try:
            file_path.unlink()
            deleted_count += 1
            deleted_size += size_mb
            print(f"   ✅ Deleted: {file_path.name}")
        except Exception as e:
            print(f"   ❌ Error deleting {file_path.name}: {e}")
    
    print(f"\n✅ Cleanup complete!")
    print(f"   Deleted: {deleted_count} files ({deleted_size:.1f} MB)")
    print(f"   Kept: {len(KEEP_FILES)} file(s)")


if __name__ == "__main__":
    cleanup_models()

