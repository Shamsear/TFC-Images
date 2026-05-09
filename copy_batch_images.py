import os
import shutil
import subprocess
from pathlib import Path

# Source and destination paths
SOURCE_BASE = "public/player_cards"
DEST_PATH = r"D:\Games\SS\playerdata\batches\enhanced_cards_standard"

def get_batch_folders(start_from=None):
    """Get all batch folders sorted by number, optionally starting from a specific batch"""
    batch_folders = []
    source_path = Path(DEST_PATH)
    
    if not source_path.exists():
        print(f"Error: Source path '{DEST_PATH}' does not exist")
        return []
    
    for folder in source_path.iterdir():
        if folder.is_dir() and folder.name.startswith("batch_"):
            batch_number = int(folder.name.split("_")[1])
            if start_from is None or batch_number >= start_from:
                batch_folders.append(folder)
    
    # Sort by batch number
    batch_folders.sort(key=lambda x: int(x.name.split("_")[1]))
    return batch_folders

def copy_batch(batch_folder, source_path):
    """Copy all images from a batch folder to destination"""
    dest = Path(source_path)
    dest.mkdir(parents=True, exist_ok=True)
    
    images = list(batch_folder.glob("*.png"))
    total = len(images)
    
    print(f"\nCopying {total} images from {batch_folder.name}...")
    
    copied = 0
    skipped = 0
    
    for img in images:
        dest_file = dest / img.name
        
        # Skip if file already exists
        if dest_file.exists():
            skipped += 1
            continue
        
        try:
            shutil.copy2(img, dest_file)
            copied += 1
            
            # Progress indicator
            if copied % 50 == 0:
                print(f"  Copied {copied}/{total} images...")
        except Exception as e:
            print(f"  Error copying {img.name}: {e}")
    
    print(f"✓ Completed {batch_folder.name}: {copied} copied, {skipped} skipped")
    return copied, skipped

def git_push_batch(batch_name, copied_count):
    """Commit and push changes to GitHub after each batch"""
    if copied_count == 0:
        print("  No new files to commit, skipping git push")
        return True
    
    try:
        print(f"\n  Pushing {batch_name} to GitHub...")
        
        # Add all new images
        print("  → Running: git add")
        add_result = subprocess.run(["git", "add", SOURCE_BASE], capture_output=True, text=True, check=True)
        print(f"  ✓ Git add successful")
        
        # Commit with batch name
        commit_msg = f"Add {batch_name} ({copied_count} images)"
        print(f"  → Running: git commit")
        commit_result = subprocess.run(["git", "commit", "-m", commit_msg, "--quiet"], capture_output=True, text=True, check=True)
        print(f"  ✓ Git commit successful")
        
        # Push to GitHub with compression
        print(f"  → Running: git push")
        push_result = subprocess.run(
            ["git", "push", "--quiet", "--no-progress"],
            capture_output=True, 
            text=True, 
            check=True,
            env={**os.environ, "GIT_SSH_COMMAND": "ssh -o Compression=yes"}
        )
        print(f"  ✓ Git push successful")
        
        print(f"\n  ✓ Successfully pushed {batch_name} to GitHub")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n  ✗ Git command failed with exit code {e.returncode}")
        print(f"  Command: {e.cmd}")
        if e.stdout:
            print(f"  STDOUT: {e.stdout}")
        if e.stderr:
            print(f"  STDERR: {e.stderr}")
        print("\n  Stopping batch processing due to git error.")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error during git push: {type(e).__name__}: {e}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")
        print("\n  Stopping batch processing due to unexpected error.")
        return False

def main():
    print("=" * 60)
    print("Batch Image Copy Tool")
    print("=" * 60)
    
    # Ask if user wants to resume from a specific batch
    resume_input = input("\nResume from batch number? (press Enter to start from beginning, or enter batch number like 436): ").strip()
    start_batch = int(resume_input) if resume_input else None
    
    # Get all batch folders
    batch_folders = get_batch_folders(start_from=start_batch)
    
    if not batch_folders:
        print("No batch folders found!")
        return
    
    print(f"\nFound {len(batch_folders)} batch folders")
    print(f"Destination: {SOURCE_BASE}\n")
    
    # Ask user for batch grouping
    print("\nPush strategy:")
    print("  1. Push after each batch (safest, slowest) - ~2000+ pushes remaining")
    print("  2. Group 10 batches per push (recommended) - ~200 pushes remaining")
    print("  3. Group 20 batches per push (faster) - ~100 pushes remaining")
    print("  4. Group 50 batches per push (fastest) - ~40 pushes remaining")
    print("  5. Custom number of batches per push")
    choice = input("\nChoose option (1-5, default=2): ").strip() or "2"
    
    batches_per_push_map = {"1": 1, "2": 10, "3": 20, "4": 50}
    
    if choice in batches_per_push_map:
        batches_per_push = batches_per_push_map[choice]
    elif choice == "5":
        batches_input = input("How many batches per push? (recommended: 10-50): ").strip()
        batches_per_push = int(batches_input) if batches_input else 10
    else:
        batches_per_push = 10
        print(f"Invalid choice, using default: {batches_per_push} batches per push")
    
    # Process each batch
    total_copied = 0
    total_skipped = 0
    batches_processed = 0
    batch_group_names = []
    batch_group_copied = 0
    
    for i, batch_folder in enumerate(batch_folders, 1):
        print(f"\n[{i}/{len(batch_folders)}] Processing {batch_folder.name}")
        
        copied, skipped = copy_batch(batch_folder, SOURCE_BASE)
        total_copied += copied
        total_skipped += skipped
        batch_group_names.append(batch_folder.name)
        batch_group_copied += copied
        
        # Push to GitHub after group of batches
        should_push = (i % batches_per_push == 0) or (i == len(batch_folders))
        if should_push:
            group_name = f"{batch_group_names[0]}-{batch_group_names[-1]}" if len(batch_group_names) > 1 else batch_group_names[0]
            if not git_push_batch(group_name, batch_group_copied):
                print("\n⚠ Stopping batch processing due to error.")
                batches_processed = i
                break
            batch_group_names = []
            batch_group_copied = 0
        
        batches_processed = i
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total images copied: {total_copied}")
    print(f"Total images skipped: {total_skipped}")
    print(f"Batches processed: {batches_processed}/{len(batch_folders)}")
    
    if batches_processed == len(batch_folders):
        print("\n✓ All batches completed successfully!")
    else:
        print(f"\n⚠ Stopped at batch {batches_processed} due to error.")
        print(f"  Remaining batches: {len(batch_folders) - batches_processed}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")
