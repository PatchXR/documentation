#!/usr/bin/env python3
"""
Complete Block Documentation Update Script

Updates documentation, portal, and wiki from NewPatch repository.
Run this whenever NewPatch blocks change.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description, cwd=None):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    print(f"Command: {command}")
    
    try:
        if isinstance(command, list):
            result = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        
        if result.stdout:
            print(f"✅ Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def copy_files(src, dst, description):
    """Copy files and handle errors."""
    print(f"\n📁 {description}...")
    print(f"From: {src}")
    print(f"To: {dst}")
    
    try:
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print("✅ File copied successfully")
        else:
            # Copy directory contents
            if not os.path.exists(dst):
                os.makedirs(dst)
            
            copied_count = 0
            for item in os.listdir(src):
                if not item.endswith('.meta'):  # Skip Unity meta files
                    src_item = os.path.join(src, item)
                    dst_item = os.path.join(dst, item)
                    if os.path.isfile(src_item):
                        shutil.copy2(src_item, dst_item)
                        copied_count += 1
            
            print(f"✅ Copied {copied_count} files")
        return True
    except Exception as e:
        print(f"❌ Error copying files: {e}")
        return False

def main():
    print("🚀 Starting Complete Block Documentation Update")
    print("=" * 50)
    
    # Check if we're in the right directory
    unity_project_path = '../NewPatch'
    if not os.path.exists(unity_project_path):
        unity_project_path = '../Patch2025'
        
    if not os.path.exists(os.path.join(unity_project_path, 'Assets/Blocks')):
        print(f"❌ Error: Unity repository (NewPatch or Patch2025) not found at {unity_project_path}!")
        print("Please make sure this script is run from the documentation folder")
        print("and that your Unity project folder is side-by-side with this one.")
        sys.exit(1)
    
    # Load config if available
    config = {}
    config_path = 'wiki-integration/wiki-config.json'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                import json
                config = json.load(f)
        except Exception:
            pass
    
    success = True
    
    # Step 1: Extract blocks from Unity Project to Documentation
    print(f"\n📖 STEP 1: {os.path.basename(unity_project_path)} → Documentation")
    print("Note: Wiki now reads directly from Assets/Blocks, so this step is optional for wiki updates")
    print("but still required for portal and RST documentation.")
    if not run_command(
        ['python', 'build_rst_from_blocks_json.py', '--verbose'],
        f"Extracting blocks from {os.path.basename(unity_project_path)}",
        cwd='.'
    ):
        success = False
    
    # Step 2: Copy blocks_data.json to Portal
    print("\n📱 STEP 2: Documentation → Portal")
    
    portal_path = '../patch-portal'
    if os.path.exists(portal_path):
        # Copy blocks data
        if not copy_files(
            'source/blocks_data.json',
            f'{portal_path}/static/blocks_data.json',
            "Copying blocks data to portal"
        ):
            success = False
        
        # Copy thumbnails
        if not copy_files(
            'source/_static/block-thumbnails',
            f'{portal_path}/static/block-thumbnails',
            "Copying thumbnails to portal"
        ):
            success = False
        
        print("\n✅ Portal files updated successfully")
        print("📡 Remember to commit and deploy the portal to portal.patchxr.io!")
    else:
        print(f"⚠️ Portal not found at {portal_path}, skipping portal update")
    
    # Step 3: Ask about Wiki update
    print("\n📚 STEP 3: Documentation → Wiki")
    
    wiki_path = 'wiki-integration'
    if os.path.exists(wiki_path):
        response = input("Do you want to update the wiki now? (y/N): ")
        if response.lower().startswith('y'):
            # Check if git sync is configured
            print("\n🔄 Wiki Update Method:")
            print("1. Git sync (recommended) - Generate markdown files locally")
            print("2. API update (legacy) - Direct API calls to Wiki.js")
            print("")
            
            method = input("Which method to use? (1/2) [1]: ").strip()
            
            if method == '2':
                # Legacy API method
                print("\n📝 Using API method...")
                print("⚠️  Note: This is slower and may timeout")
                if run_command(
                    ['python', 'wiki-populate-simple.py', '--verbose'],
                    "Updating wiki via API",
                    cwd=wiki_path
                ):
                    print("✅ Wiki updated successfully!")
                else:
                    print("❌ Wiki update failed")
                    success = False
            else:
                # Git sync method (default)
                print("\n📝 Using Git sync method...")
                # Try to get path from config first
                default_repo_path = config.get('wiki_repo_path')
                
                # Fallback to defaults
                if not default_repo_path or not os.path.exists(default_repo_path):
                    default_repo_path = os.path.expanduser("~/block-docs").replace("\\", "/")
                    # For Windows, also try the explicit path
                    if not os.path.exists(default_repo_path):
                        default_repo_path = "../../block-docs" # Try relative path
                    if not os.path.exists(default_repo_path):
                        default_repo_path = "C:/Users/mcbub/block-docs"
                
                if os.path.exists(default_repo_path):
                    print(f"Using default repo path: {default_repo_path}")
                    repo_path = default_repo_path
                else:
                    repo_path = input("Enter path to your wiki git repo: ").strip()
                    if not repo_path:
                        print("❌ No path provided")
                        success = False
                        repo_path = None
                
                if repo_path and os.path.exists(repo_path):
                    if run_command(
                        ['python', 'wiki-generate-markdown.py', '--output', repo_path],
                        "Generating markdown files",
                        cwd=wiki_path
                    ):
                        print("\n✅ Markdown files generated successfully!")
                        print("📤 Next steps:")
                        print(f"   1. cd {repo_path}")
                        print("   2. git add .")
                        print("   3. git commit -m 'Update block documentation'")
                        print("   4. git push")
                        print("   5. Wiki.js will sync automatically")
                    else:
                        print("❌ Markdown generation failed")
                        success = False
                else:
                    if repo_path:
                        print(f"❌ Directory not found: {repo_path}")
                    success = False
        else:
            print("⏭️  Skipping wiki update")
            print(f"   To update later: cd {wiki_path} && python wiki-generate-markdown.py")
    else:
        print(f"⚠️ Wiki integration not found at {wiki_path}")
    
    # Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 UPDATE COMPLETED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Deploy portal to portal.patchxr.io (if not done automatically)")
        print("2. Check wiki.patchxr.io for updated documentation")
        print("3. Verify thumbnails are displaying correctly")
    else:
        print("⚠️  UPDATE COMPLETED WITH SOME ERRORS")
        print("Please check the error messages above and fix any issues")
    
    print("\nUpdated components:")
    print("✅ Documentation (RST files, blocks_data.json)")
    if os.path.exists(portal_path):
        print("✅ Portal (blocks_data.json, thumbnails)")
    if os.path.exists(wiki_path):
        print("✅ Wiki (if selected)")

if __name__ == '__main__':
    main()