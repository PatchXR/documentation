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
    
    def create_block_content(self, block: Dict, category: str, folder_info: Dict) -> str:
        """Create markdown content for a block."""
        content = []
        
        # Title with emoji if available
        icon = folder_info.get('icon', '')
        if icon:
            content.append(f"# {block['name']}")
        else:
            content.append(f"# {block['name']}")
        
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
                content.append(f"- [{related}](/blocks/{related.lower()})")
            content.append("")
        
        # Tags
        if block.get('tags'):
            content.append("## Tags")
            content.append("")
            content.append(", ".join(block['tags']))
            content.append("")
        
        # Footer
        content.append("---")
        content.append("")
        content.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        
        return '\n'.join(content)
    
    def create_category_index(self, category_name: str, folder_info: Dict, blocks: List[Dict]) -> str:
        """Create index page for a category."""
        content = []
        icon = folder_info.get('icon', '')
        
        # Title
        title = f"{icon} {category_name} Blocks" if icon else f"{category_name} Blocks"
        content.append(f"# {title}")
        content.append("")
        
        content.append(f"This category contains **{len(blocks)}** blocks.")
        content.append("")
        
        # Sort blocks
        sorted_blocks = sorted(blocks, key=lambda x: x['name'].lower())
        
        # List blocks
        content.append("## Available Blocks")
        content.append("")
        
        for block in sorted_blocks:
            desc = block.get('description', 'No description available')
            if len(desc) > 100:
                desc = desc[:97] + "..."
            content.append(f"- **[{block['name']}](./{block['name'].lower()}.md)** - {desc}")
        
        content.append("")
        content.append("---")
        content.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        
        return '\n'.join(content)
    
    def create_main_index(self, folders: List[Dict], folder_blocks: Dict[str, List]) -> str:
        """Create main blocks index."""
        content = []
        
        content.append("# Blocks Documentation")
        content.append("")
        content.append("Welcome to the Blocks documentation! Blocks are the building components you use to create patches in PatchWorld.")
        content.append("")
        content.append("## Block Categories")
        content.append("")
        
        # Process main folders (not including Decor parent)
        for folder in folders:
            if folder['id'] != 'block-folder-decor':
                folder_name = folder['name']
                folder_path = folder_name.lower().replace(' ', '-')
                icon = folder.get('icon', '')
                block_count = folder.get('assetCount', 0)
                
                content.append(f"### [{folder_name}](./blocks/{folder_path}/index.md) {icon}" if icon else f"### [{folder_name}](./blocks/{folder_path}/index.md)")
                content.append(f"*{block_count} blocks*")
                content.append("")
            else:
                # Process Decor children
                content.append("### Decor")
                content.append("")
                for child in folder.get('children', []):
                    child_name = child['name']
                    child_path = f"decor/{child_name.lower().replace(' ', '-')}"
                    icon = child.get('icon', '')
                    block_count = child.get('assetCount', 0)
                    
                    content.append(f"- {icon} [{child_name}](./blocks/{child_path}/index.md) - *{block_count} items*")
                content.append("")
        
        content.append("---")
        content.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        
        return '\n'.join(content)
    
    def clean_output_directory(self, dry_run: bool = False):
        """Clean the output directory before generating new files."""
        blocks_dir = self.output_dir / 'blocks'
        
        if blocks_dir.exists():
            if dry_run:
                print(f"Would remove: {blocks_dir}")
            else:
                print(f"[CLEANUP] Cleaning existing blocks directory...")
                shutil.rmtree(blocks_dir)
    
    def generate_markdown_files(self, dry_run: bool = False, limit: int = None):
        """Generate all markdown files."""
        # Check git status first
        if not dry_run and not self.check_git_status():
            return
        
        # Prompt for git pull
        if not dry_run and not self.prompt_git_pull():
            return
        
        # Load data
        print("\n[INFO] Loading block data...")
        blocks_data = self.load_blocks_data()
        folders = self.load_folder_structure()
        
        # Create a map of block names to block data for quick lookup
        blocks_by_name = {b['name'].lower(): b for b in blocks_data['blocks']}
        
        # Build list of blocks FROM the folder structure (not from blocks_data)
        blocks_to_process = []
        
        def collect_blocks_from_folders(folder_list, parent_path=""):
            for folder in folder_list:
                folder_name = folder['name'].lower().replace(' ', '-')
                current_path = f"{parent_path}/{folder_name}" if parent_path else folder_name
                
                # Process blocks in this folder
                for folder_block in folder.get('blocks', []):
                    block_name = folder_block['name']
                    # Find the full block data
                    if block_name.lower() in blocks_by_name:
                        block = blocks_by_name[block_name.lower()]
                        # Add folder info to the block
                        blocks_to_process.append({
                            'block': block,
                            'folder_path': current_path,
                            'category': folder['name'],
                            'folder_info': folder
                        })
                
                # Process children folders
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
            
            # Track for category pages
            if folder_path not in folder_blocks:
                folder_blocks[folder_path] = (category, folder_info, [])
            folder_blocks[folder_path][2].append(block)
            
            # Create file path
            file_path = self.output_dir / 'blocks' / folder_path / f"{block_name.lower()}.md"
            
            if dry_run:
                print(f"Would create: {file_path}")
                created_files.append(str(file_path))
            else:
                # Create directory
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Generate content
                content = self.create_block_content(block, category, folder_info)
                
                # Write file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                created_files.append(str(file_path))
        
        # Create category index pages
        for folder_path, (category, folder_info, blocks) in folder_blocks.items():
            index_path = self.output_dir / 'blocks' / folder_path / 'index.md'
            
            if dry_run:
                print(f"Would create: {index_path}")
            else:
                index_path.parent.mkdir(parents=True, exist_ok=True)
                content = self.create_category_index(category, folder_info, blocks)
                
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        # Create main index
        main_index_path = self.output_dir / 'index.md'
        
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
            print("1. Review the generated files")
            print("2. Commit changes: git add . && git commit -m 'Update block documentation'")
            print("3. Push to GitHub: git push")
            print("4. Wiki.js will automatically sync the changes")

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
    
    args = parser.parse_args()
    
    # Create generator
    generator = MarkdownGenerator(args.config, args.output)
    
    # Add block_folders_path to config if not present
    if 'block_folders_path' not in generator.config:
        generator.config['block_folders_path'] = 'C:\\Users\\mcbub\\NewPatch\\Assets\\StreamingAssets\\block_folders.json'
    
    try:
        generator.generate_markdown_files(dry_run=args.dry_run, limit=args.limit)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()