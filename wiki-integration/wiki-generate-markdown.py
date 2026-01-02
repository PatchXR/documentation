#!/usr/bin/env python3
"""
Wiki.js Markdown Generator for Git Sync

Generates markdown files locally for Wiki.js git synchronization.
Much faster and more reliable than API approach.
"""

import argparse
import json
import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class MarkdownGenerator:
    def __init__(self, config_path: str, output_dir: str):
        """Initialize the markdown generator."""
        self.config = self.load_config(config_path)
        self.output_dir = Path(output_dir)
        self.blocks_data_path = Path(self.config['blocks_data_path'])
        self.block_folders_path = Path(self.config.get('block_folders_path', 
                                      'C:\\Users\\mcbub\\NewPatch\\Assets\\StreamingAssets\\block_folders.json'))
        self.block_path_map = {}  # Map block names to their folder paths
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def check_git_status(self) -> bool:
        """Check if the output directory is a git repo and if it's clean."""
        if not (self.output_dir / '.git').exists():
            print(f"[ERROR] {self.output_dir} is not a git repository!")
            print(f"Please run: cd {self.output_dir} && git init")
            return False
            
        # Check for uncommitted changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=self.output_dir,
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            print("[WARNING] You have uncommitted changes in the repository:")
            print(result.stdout)
            response = input("Do you want to continue anyway? (y/N): ")
            if not response.lower().startswith('y'):
                return False
                
        return True
    
    def prompt_git_pull(self) -> bool:
        """Prompt user to pull latest changes."""
        print("\n[Git Sync Check]")
        print("It's recommended to pull the latest changes before generating new content.")
        response = input("Do you want to pull latest changes now? (Y/n): ")
        
        if not response or response.lower().startswith('y'):
            print("Pulling latest changes...")
            result = subprocess.run(
                ['git', 'pull'],
                cwd=self.output_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"[ERROR] Git pull failed: {result.stderr}")
                return False
            else:
                print(f"[SUCCESS] {result.stdout.strip()}")
                
        return True
    
    def load_blocks_data(self) -> Dict:
        """Load block data from the documentation project."""
        if not self.blocks_data_path.exists():
            print(f"[ERROR] Blocks data file not found: {self.blocks_data_path}")
            sys.exit(1)
            
        with open(self.blocks_data_path, 'r') as f:
            return json.load(f)
    
    def load_folder_structure(self) -> List[Dict]:
        """Load the new folder structure from block_folders.json."""
        if not self.block_folders_path.exists():
            print(f"[WARNING] Block folders file not found: {self.block_folders_path}")
            return []
            
        with open(self.block_folders_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_block_folder_path(self, block_id: str, folders: List[Dict]) -> tuple[str, str, Dict]:
        """Get the folder path and category for a block based on the new structure."""
        block_id_clean = block_id.replace('block:', '') if block_id.startswith('block:') else block_id
        
        def search_folders(folders_list, parent_path=""):
            for folder in folders_list:
                folder_name = folder['name'].lower().replace(' ', '-')
                current_path = f"{parent_path}/{folder_name}" if parent_path else folder_name
                
                # Check blocks in this folder
                for block in folder.get('blocks', []):
                    # Clean the folder block ID for comparison
                    folder_block_name = block['id'].replace('block:', '')
                    
                    # Try multiple matching strategies
                    if (folder_block_name.lower() == block_id_clean.lower() or
                        folder_block_name.replace('_', '').lower() == block_id_clean.replace('_', '').lower() or
                        folder_block_name.replace('_', '-').lower() == block_id_clean.replace('_', '-').lower() or
                        block['name'].lower() == block_id_clean.lower()):
                        return current_path, folder['name'], folder
                
                # Check children folders
                if 'children' in folder and folder['children']:
                    result = search_folders(folder['children'], current_path)
                    if result[0]:
                        return result
            
            return "", "", {}
        
        return search_folders(folders)
    
    
    def find_thumbnail_url(self, block_name: str) -> Optional[str]:
        """Find thumbnail URL for a block."""
        thumbnails_path = self.config.get('thumbnails_path', '')
        possible_files = [
            f"{block_name}.png",
            f"{block_name.lower()}.png",
            f"{block_name.replace('_', '')}.png",
            f"{block_name.replace('_', '-')}.png"
        ]
        
        for filename in possible_files:
            image_path = Path(thumbnails_path) / filename
            if image_path.exists():
                base_url = self.config.get('docs_base_url', 'https://portal.patchxr.io')
                return f"{base_url}/block-thumbnails/{filename}"
        
        return None
    
    def create_block_content(self, block: Dict, category: str, folder_info: Dict, display_name: str = None) -> str:
        """Create markdown content for a block."""
        content = []
        
        # Title with emoji if available
        icon = folder_info.get('icon', '')
        # Use display name if provided, otherwise fall back to block name
        title = display_name or block['name']
        content.append(f"# {title}")
        
        content.append("")
        
        # Category
        if category:
            content.append(f"**Category**: {icon} {category}" if icon else f"**Category**: {category}")
            content.append("")
        
        # Thumbnail
        thumbnail_url = self.find_thumbnail_url(block['name'])
        if thumbnail_url:
            content.append(f"![{block['name']} thumbnail]({thumbnail_url})")
            content.append("")
        
        # Description
        if block.get('description'):
            content.append("## Description")
            content.append("")
            content.append(block['description'])
            content.append("")
        
        if block.get('longDescription'):
            content.append(block['longDescription'])
            content.append("")
        
        # Parts (inputs/outputs)
        if block.get('parts'):
            content.append("## Inputs, Outputs and Parts")
            content.append("")
            for part in block['parts']:
                part_type = part.get('type', '')
                type_str = f" *({part_type})*" if part_type else ""
                part_desc = part.get('description', '')
                content.append(f"**{part['name']}**{type_str}: {part_desc}")
                content.append("")
        
        # Related blocks
        if block.get('relatedBlocks'):
            content.append("## Related Blocks")
            content.append("")
            for related in block['relatedBlocks']:
                # Find the folder path for the related block
                related_lower = related.lower()
                if related_lower in self.block_path_map:
                    related_path = self.block_path_map[related_lower]
                    content.append(f"- [{related}](/blocks/{related_path}/{related_lower})")
                else:
                    # If path not found, still show the block but without link
                    content.append(f"- {related} (link not available)")
            content.append("")
        
        # Tags
        if block.get('tags'):
            content.append("## Tags")
            content.append("")
            content.append(", ".join(block['tags']))
            content.append("")
        
        # Footer
        content.append("---")
        
        return '\n'.join(content)
    
    def create_category_index(self, category_name: str, folder_info: Dict, blocks: List[tuple], folder_path: str) -> str:
        """Create index page for a category."""
        content = []
        icon = folder_info.get('icon', '')
        
        # Header with metadata for Wiki.js
        content.append("---")
        content.append(f"title: {category_name}")
        content.append(f"description: {category_name} blocks documentation")
        content.append("published: true")
        content.append(f"date: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')}")
        content.append("tags: blocks, category")
        content.append("editor: markdown")
        content.append(f"dateCreated: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')}")
        content.append("---")
        content.append("")
        
        # Title
        title = f"{icon} {category_name} Blocks" if icon else f"{category_name} Blocks"
        content.append(f"# {title}")
        content.append("")
        
        content.append(f"This category contains **{len(blocks)}** blocks.")
        content.append("")
        
        # Sort blocks by display name
        sorted_blocks = sorted(blocks, key=lambda x: x[1].lower())
        
        # List blocks
        content.append("## Available Blocks")
        content.append("")
        
        for block, display_name in sorted_blocks:
            desc = block.get('description', 'No description available')
            if len(desc) > 100:
                desc = desc[:97] + "..."
            # Link to blocks in the subfolder (e.g., /blocks/interfaces/button)
            content.append(f"- **[{display_name}](./{folder_path}/{block['name'].lower()})** - {desc}")
        
        content.append("")
        content.append("---")
        
        return '\n'.join(content)
    
    
    def create_main_index(self, folders: List[Dict], folder_blocks: Dict[str, List]) -> str:
        """Create main blocks index with table format."""
        content = []
        
        # Count total blocks
        total_blocks = sum(len(blocks[2]) for blocks in folder_blocks.values())
        
        # Header with metadata for Wiki.js
        content.append("---")
        content.append("title: Blocks")
        content.append("description: Comprehensive guide to all fundamental building blocks in PatchWorld")
        content.append("published: true")
        content.append(f"date: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')}")
        content.append("tags: blocks, index, documentation")
        content.append("editor: markdown")
        content.append(f"dateCreated: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S.000Z')}")
        content.append("---")
        content.append("")
        content.append("These are the fundamental building blocks available in PatchWorld. You can use these blocks to create patches, instruments, and interactive experiences.")
        content.append("")
        content.append("💡 **Note:** Beyond these basic blocks, PatchWorld offers:")
        content.append("- **Instruments & Devices** - Pre-built combinations of blocks for music and interaction")
        content.append("- **Imported Assets** - Custom 3D models, sounds, and creations from the community")
        content.append("- **Your Own Creations** - Save and share your patches as reusable devices")
        content.append("")
        content.append(f"**{total_blocks} blocks** available across **{len([f for f in folders if f['id'] != 'block-folder-decor'])}** categories")
        content.append("")
        content.append("---")
        content.append("")
        
        # Core Building Blocks table
        content.append("## 🎛️ Core Building Blocks")
        content.append("")
        content.append("| Category | Blocks | Description |")
        content.append("|----------|--------|-------------|")
        
        # Define descriptions for each category
        descriptions = {
            "Interfaces": "User interaction and control elements",
            "Controllers": "3D controllers and input devices",
            "Audio": "Sound generation and processing",
            "Visual": "Graphics, effects, and visual elements",
            "Motion": "Physics and movement control",
            "Logic": "Data flow and decision making",
            "Connectors": "Linking and routing signals",
            "Players": "Multiplayer and user management",
            "System": "System-level controls and utilities"
        }
        
        # Add non-decor folders to table
        for folder in folders:
            if folder['id'] != 'block-folder-decor':
                folder_name = folder['name']
                folder_path = folder_name.lower().replace(' ', '-')
                icon = folder.get('icon', '')
                # Always use actual count from folder_blocks
                if folder_path in folder_blocks:
                    block_count = len(folder_blocks[folder_path][2])
                else:
                    block_count = 0  # Don't show folders with no blocks
                
                desc = descriptions.get(folder_name, "")
                content.append(f"| **[{folder_name}](/blocks/{folder_path})** {icon} | {block_count} | {desc} |")
        
        
        content.append("")
        content.append("---")
        
        return '\n'.join(content)
    
    def clean_old_timestamps(self, dry_run: bool = False):
        """Remove old timestamp lines from existing files."""
        if dry_run:
            return
            
        blocks_dir = self.output_dir / 'blocks'
        if not blocks_dir.exists():
            return
            
        print("[CLEANUP] Removing old timestamps from existing files...")
        files_cleaned = 0
        
        # Clean all .md files recursively
        for md_file in blocks_dir.rglob('*.md'):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                cleaned_lines = []
                changed = False
                
                for line in lines:
                    if line.startswith('*Last updated:'):
                        changed = True
                        continue  # Skip this line
                    cleaned_lines.append(line)
                
                if changed:
                    # Write back without timestamp
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(cleaned_lines))
                    files_cleaned += 1
                    
            except Exception as e:
                print(f"[WARNING] Could not clean {md_file}: {e}")
        
        # Also clean main blocks.md
        main_blocks_file = self.output_dir / 'blocks.md'
        if main_blocks_file.exists():
            try:
                with open(main_blocks_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                cleaned_lines = []
                changed = False
                
                for line in lines:
                    if line.startswith('*Last updated:'):
                        changed = True
                        continue
                    cleaned_lines.append(line)
                
                if changed:
                    with open(main_blocks_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(cleaned_lines))
                    files_cleaned += 1
                    
            except Exception as e:
                print(f"[WARNING] Could not clean {main_blocks_file}: {e}")
        
        if files_cleaned > 0:
            print(f"[CLEANUP] Cleaned timestamps from {files_cleaned} files")
        else:
            print("[CLEANUP] No old timestamps found")

    def clean_output_directory(self, dry_run: bool = False):
        """Clean the output directory before generating new files."""
        # Note: We now skip full cleanup to preserve timestamps for unchanged files
        # Individual file updates will handle changes as needed
        if not dry_run:
            print(f"[INFO] Incremental update mode - preserving unchanged files")
            
            # Clean up old index.md files from previous structure
            blocks_dir = self.output_dir / 'blocks'
            if blocks_dir.exists():
                for folder in blocks_dir.iterdir():
                    if folder.is_dir():
                        index_file = folder / 'index.md'
                        if index_file.exists():
                            print(f"[CLEANUP] Removing old index file: {index_file}")
                            index_file.unlink()
    
    def generate_markdown_files(self, dry_run: bool = False, limit: int = None, auto_commit: bool = False):
        """Generate all markdown files."""
        # Check git status first
        if not dry_run and not self.check_git_status():
            return
        
        # Prompt for git pull (skip if auto-commit)
        if not dry_run and auto_commit:
            print("[INFO] Skipping git pull prompt in auto-commit mode")
        elif not dry_run and not self.prompt_git_pull():
            return
        
        # Load data
        print("\n[INFO] Loading block data...")
        blocks_data = self.load_blocks_data()
        folders = self.load_folder_structure()
        
        # Create a map of block names to block data for quick lookup
        blocks_by_name = {b['name']: b for b in blocks_data['blocks']}
        
        # Build list of blocks FROM the folder structure (not from blocks_data)
        blocks_to_process = []
        
        def collect_blocks_from_folders(folder_list, parent_path=""):
            for folder in folder_list:
                # Skip decor folder and its children
                if folder['id'] == 'block-folder-decor':
                    continue
                    
                folder_name = folder['name'].lower().replace(' ', '-')
                current_path = f"{parent_path}/{folder_name}" if parent_path else folder_name
                
                # Process blocks in this folder
                for folder_block in folder.get('blocks', []):
                    # Use the block ID to find the block
                    block_id = folder_block['id'].replace('block:', '')
                    
                    # Try to find by ID first, then by display name
                    if block_id in blocks_by_name:
                        block = blocks_by_name[block_id]
                    elif folder_block['name'].lower() in blocks_by_name:
                        block = blocks_by_name[folder_block['name'].lower()]
                    else:
                        # Block not found in blocks_data.json
                        print(f"[WARNING] Block not found in blocks_data: {folder_block['name']} (ID: {block_id})")
                        continue
                    
                    # Build path map for related blocks lookup
                    self.block_path_map[block['name'].lower()] = current_path
                    
                    # Add folder info to the block
                    blocks_to_process.append({
                        'block': block,
                        'folder_path': current_path,
                        'category': folder['name'],
                        'folder_info': folder,
                        'display_name': folder_block['name']  # Add display name from folder structure
                    })
                
                # Process children folders (won't include decor children now)
                if 'children' in folder and folder['children']:
                    collect_blocks_from_folders(folder['children'], current_path)
        
        # Collect all blocks from the folder structure
        collect_blocks_from_folders(folders)
        
        if limit:
            blocks_to_process = blocks_to_process[:limit]
            print(f"Limited to first {limit} blocks for testing")
        
        print(f"Processing {len(blocks_to_process)} blocks from folder structure...")
        
        # Clean output directory
        if not dry_run:
            self.clean_output_directory(dry_run)
        
        # Track blocks by folder
        folder_blocks = {}
        created_files = []
        
        # Process each block with its predetermined folder
        for block_data in blocks_to_process:
            block = block_data['block']
            folder_path = block_data['folder_path']
            category = block_data['category']
            folder_info = block_data['folder_info']
            
            block_name = block['name']
            
            # Track for category pages with display name
            if folder_path not in folder_blocks:
                folder_blocks[folder_path] = (category, folder_info, [])
            # Store both block and display name
            display_name = block_data.get('display_name', block['name'])
            folder_blocks[folder_path][2].append((block, display_name))
            
            # Create file path
            file_path = self.output_dir / 'blocks' / folder_path / f"{block_name.lower()}.md"
            
            if dry_run:
                print(f"Would create: {file_path}")
                created_files.append(str(file_path))
            else:
                # Create directory
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Generate content
                display_name = block_data.get('display_name', block['name'])
                content = self.create_block_content(block, category, folder_info, display_name)
                
                # Write file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                created_files.append(str(file_path))
        
        # Create category index pages directly at /blocks/category.md (Wiki.js native structure)
        for folder_path, (category, folder_info, blocks) in folder_blocks.items():
            # Create category page directly at /blocks/interfaces.md instead of /blocks/interfaces/index.md
            category_page_path = self.output_dir / 'blocks' / f"{folder_path}.md"
            
            if dry_run:
                print(f"Would create: {category_page_path}")
            else:
                content = self.create_category_index(category, folder_info, blocks, folder_path)
                
                with open(category_page_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        # Create main blocks.md
        main_index_path = self.output_dir / 'blocks.md'
        
        if dry_run:
            print(f"Would create: {main_index_path}")
        else:
            content = self.create_main_index(folders, folder_blocks)
            
            with open(main_index_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Summary
        print(f"\n[SUCCESS] Generated {len(created_files)} block files")
        print(f"[INFO] Output directory: {self.output_dir}")
        
        if not dry_run:
            print("\n[NEXT STEPS]:")
            
            # Ask if user wants to commit and push (unless auto-commit is enabled)
            if auto_commit:
                response = 'y'
            else:
                response = input("\nDo you want to commit and push changes now? (Y/n): ")
            
            if not response or response.lower().startswith('y'):
                print("\n[GIT] Adding files...")
                add_result = subprocess.run(
                    ['git', 'add', '.'],
                    cwd=self.output_dir,
                    capture_output=True,
                    text=True
                )
                
                if add_result.returncode != 0:
                    print(f"[ERROR] Git add failed: {add_result.stderr}")
                    return
                
                # Commit with timestamp
                commit_msg = f"Update block documentation - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                print(f"[GIT] Committing: {commit_msg}")
                
                commit_result = subprocess.run(
                    ['git', 'commit', '-m', commit_msg],
                    cwd=self.output_dir,
                    capture_output=True,
                    text=True
                )
                
                if commit_result.returncode != 0:
                    if 'nothing to commit' in commit_result.stdout:
                        print("[INFO] No changes to commit")
                        return
                    else:
                        print(f"[ERROR] Git commit failed: {commit_result.stderr}")
                        return
                else:
                    print(f"[SUCCESS] {commit_result.stdout.strip()}")
                
                # Push
                print("[GIT] Pushing to remote...")
                push_result = subprocess.run(
                    ['git', 'push'],
                    cwd=self.output_dir,
                    capture_output=True,
                    text=True
                )
                
                if push_result.returncode != 0:
                    print(f"[ERROR] Git push failed: {push_result.stderr}")
                    print("You can manually push later with: git push")
                else:
                    print("[SUCCESS] Pushed to remote!")
                    print("[INFO] Wiki.js will automatically sync the changes")
            else:
                print("\n[INFO] Skipping git operations")
                print("To commit later:")
                print(f"  cd {self.output_dir}")
                print("  git add .")
                print("  git commit -m 'Update block documentation'")
                print("  git push")

def main():
    parser = argparse.ArgumentParser(description='Generate markdown files for Wiki.js git sync')
    parser.add_argument('--config', '-c', default='wiki-config.json', 
                       help='Configuration file path')
    parser.add_argument('--output', '-o', default='C:\\Users\\mcbub\\block-docs',
                       help='Output directory (git repo)')
    parser.add_argument('--dry-run', '-d', action='store_true', 
                       help='Show what would be done without creating files')
    parser.add_argument('--limit', '-l', type=int, 
                       help='Limit number of blocks to process (for testing)')
    parser.add_argument('--auto-commit', '-a', action='store_true',
                       help='Automatically commit and push without prompting')
    
    args = parser.parse_args()
    
    # Create generator
    generator = MarkdownGenerator(args.config, args.output)
    
    # Add block_folders_path to config if not present
    if 'block_folders_path' not in generator.config:
        generator.config['block_folders_path'] = 'C:\\Users\\mcbub\\NewPatch\\Assets\\StreamingAssets\\block_folders.json'
    
    try:
        generator.generate_markdown_files(dry_run=args.dry_run, limit=args.limit, auto_commit=args.auto_commit)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()