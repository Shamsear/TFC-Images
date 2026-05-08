import os
import shutil
import subprocess
from pathlib import Path

# Source and destination paths
SOURCE_BASE = "public/player_cards"
DEST_PATH = r"C:\Drive d\SS\playerdata\batches\enhanced_cards_standard"

def get_batch_folders():
    """Get all batch folders sorted by number"""
    batch_folders = []
    source_path = Path(DEST_PATH)
    
    if not source_path.exists():
        print(f"Error: Source path '{DEST_PATH}' does not exist")
        return []
    
    for folder in source_path.iterdir():
        if folder.is_dir() and folder.name.startswith("batch_"):
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
        add_result = subprocess.run(["git", "add", SOURCE_BASE], capture_output=True, text=True)
        if add_result.returncode != 0:
            print(f"  ✗ Git add failed!")
            print(f"  STDOUT: {add_result.stdout}")
            print(f"  STDERR: {add_result.stderr}")
            raise subprocess.CalledProcessError(add_result.returncode, "git add", add_result.stdout, add_result.stderr)
        print(f"  ✓ Git add successful")
        if add_result.stdout:
            print(f"  Output: {add_result.stdout}")
        
        # Commit with batch name
        commit_msg = f"Add {batch_name} ({copied_count} images)"
        print(f"  → Running: git commit -m '{commit_msg}'")
        commit_result = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
        if commit_result.returncode != 0:
            print(f"  ✗ Git commit failed!")
            print(f"  STDOUT: {commit_result.stdout}")
            print(f"  STDERR: {commit_result.stderr}")
            raise subprocess.CalledProcessError(commit_result.returncode, "git commit", commit_result.stdout, commit_result.stderr)
        print(f"  ✓ Git commit successful")
        if commit_result.stdout:
            print(f"  Output: {commit_result.stdout}")
        
        # Push to GitHub
        print(f"  → Running: git push")
        push_result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if push_result.returncode != 0:
            print(f"  ✗ Git push failed!")
            print(f"  STDOUT: {push_result.stdout}")
            print(f"  STDERR: {push_result.stderr}")
            raise subprocess.CalledProcessError(push_result.returncode, "git push", push_result.stdout, push_result.stderr)
        print(f"  ✓ Git push successful")
        if push_result.stdout:
            print(f"  Output: {push_result.stdout}")
        if push_result.stderr:
            print(f"  Info: {push_result.stderr}")
        
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
    
    # Get all batch folders
    batch_folders = get_batch_folders()
    
    if not batch_folders:
        print("No batch folders found!")
        return
    
    print(f"\nFound {len(batch_folders)} batch folders")
    print(f"Destination: {SOURCE_BASE}\n")
    
    # Process each batch
    total_copied = 0
    total_skipped = 0
    batches_processed = 0
    
    for i, batch_folder in enumerate(batch_folders, 1):
        print(f"\n[{i}/{len(batch_folders)}] Processing {batch_folder.name}")
        
        copied, skipped = copy_batch(batch_folder, SOURCE_BASE)
        total_copied += copied
        total_skipped += skipped
        
        # Push to GitHub after each batch
        if not git_push_batch(batch_folder.name, copied):
            print("\n⚠ Stopping batch processing due to error.")
            batches_processed = i
            break
        
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
