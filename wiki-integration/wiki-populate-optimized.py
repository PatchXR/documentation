#!/usr/bin/env python3
"""
Optimized Wiki.js Block Documentation Populator

Features:
- Parallel page creation for much faster updates
- Uses new block_folders.json structure from NewPatch
- Batch processing with rate limiting
- Progress tracking with ETA
"""

import argparse
import json
import os
import sys
import logging
import asyncio
import aiohttp
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import time

class OptimizedWikiPopulator:
    def __init__(self, config_path: str):
        """Initialize the Wiki populator with configuration."""
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.stats = {
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None
        }
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_level = logging.DEBUG if self.config.get('verbose', False) else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('wiki-populate-optimized.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_blocks_data(self) -> Dict:
        """Load block data from the documentation project."""
        blocks_data_path = self.config['blocks_data_path']
        
        if not os.path.exists(blocks_data_path):
            self.logger.error(f"Blocks data file not found: {blocks_data_path}")
            sys.exit(1)
            
        with open(blocks_data_path, 'r') as f:
            data = json.load(f)
            
        self.logger.info(f"Loaded {len(data['blocks'])} blocks from {blocks_data_path}")
        return data
    
    def load_folder_structure(self) -> List[Dict]:
        """Load the new folder structure from block_folders.json."""
        folder_path = self.config.get('block_folders_path', 
                                     'C:\\Users\\mcbub\\NewPatch\\Assets\\StreamingAssets\\block_folders.json')
        
        if not os.path.exists(folder_path):
            self.logger.warning(f"Block folders file not found: {folder_path}")
            return []
            
        with open(folder_path, 'r', encoding='utf-8') as f:
            folders = json.load(f)
            
        self.logger.info(f"Loaded {len(folders)} folder categories")
        return folders
    
    def get_block_folder_path(self, block_id: str, folders: List[Dict]) -> Tuple[str, str]:
        """Get the folder path for a block based on the new structure."""
        # Remove 'block:' prefix if present
        block_id_clean = block_id.replace('block:', '') if block_id.startswith('block:') else block_id
        
        def search_folders(folders_list, parent_path=""):
            for folder in folders_list:
                folder_name = folder['name'].lower().replace(' ', '-')
                current_path = f"{parent_path}/{folder_name}" if parent_path else folder_name
                
                # Check blocks in this folder
                for block in folder.get('blocks', []):
                    if block['id'] == f"block:{block_id_clean}" or block['id'] == block_id:
                        return current_path, folder['name']
                
                # Check children folders
                if 'children' in folder and folder['children']:
                    result = search_folders(folder['children'], current_path)
                    if result[0]:
                        return result
            
            return "", ""
        
        folder_path, category = search_folders(folders)
        return folder_path, category
    
    def find_thumbnail_url(self, block_name: str) -> Optional[str]:
        """Find thumbnail URL for a block using portal.patchxr.io."""
        thumbnails_path = self.config.get('thumbnails_path', '')
        possible_files = [
            f"{block_name}.png",
            f"{block_name.lower()}.png",
            f"{block_name.replace('_', '')}.png",
            f"{block_name.replace('_', '-')}.png"
        ]
        
        for filename in possible_files:
            image_path = os.path.join(thumbnails_path, filename)
            if os.path.exists(image_path):
                base_url = self.config.get('docs_base_url', 'https://portal.patchxr.io')
                return f"{base_url}/block-thumbnails/{filename}"
        
        return None
    
    def create_block_page_content(self, block: Dict, category: str) -> str:
        """Create markdown content for a block page."""
        content = []
        
        # Title
        content.append(f"# {block['name']}")
        content.append("")
        
        # Category badge
        if category:
            content.append(f"**Category**: {category}")
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
        
        # Metadata footer
        content.append("---")
        content.append("")
        content.append("*Auto-generated from block documentation*")
        
        return '\n'.join(content)
    
    async def create_page_async(self, session: aiohttp.ClientSession, path: str, title: str, 
                               content: str, tags: List[str] = None) -> bool:
        """Create a new page in Wiki.js using async requests."""
        mutation = """
        mutation CreatePage(
            $content: String!
            $description: String!
            $editor: String!
            $isPublished: Boolean!
            $isPrivate: Boolean!
            $locale: String!
            $path: String!
            $tags: [String]!
            $title: String!
        ) {
            pages {
                create(
                    content: $content
                    description: $description
                    editor: $editor
                    isPublished: $isPublished
                    isPrivate: $isPrivate
                    locale: $locale
                    path: $path
                    tags: $tags
                    title: $title
                ) {
                    responseResult {
                        succeeded
                        errorCode
                        slug
                        message
                    }
                    page {
                        id
                        path
                        title
                    }
                }
            }
        }
        """
        
        variables = {
            'content': content,
            'description': f"Documentation for {title} block",
            'editor': 'markdown',
            'isPublished': True,
            'isPrivate': False,
            'locale': self.config.get('locale', 'en'),
            'path': path,
            'tags': tags or [],
            'title': title
        }
        
        headers = {
            'Authorization': f"Bearer {self.config['wiki_api_token']}",
            'Content-Type': 'application/json'
        }
        
        try:
            async with session.post(
                f"{self.config['wiki_url']}/graphql",
                json={'query': mutation, 'variables': variables},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {})
                    if result.get('succeeded'):
                        return True
                    else:
                        error_msg = result.get('message', 'Unknown error')
                        if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                            self.stats['skipped'] += 1
                            return True
                        else:
                            self.logger.error(f"Failed to create page {path}: {error_msg}")
                else:
                    self.logger.error(f"Page creation failed: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"Error creating page {path}: {e}")
        
        return False
    
    async def create_pages_batch(self, pages_data: List[Tuple], batch_size: int = 10):
        """Create multiple pages concurrently in batches."""
        connector = aiohttp.TCPConnector(limit=batch_size)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            
            for i in range(0, len(pages_data), batch_size):
                batch = pages_data[i:i+batch_size]
                
                # Create tasks for this batch
                batch_tasks = [
                    self.create_page_async(session, *page_args)
                    for page_args in batch
                ]
                
                # Execute batch
                results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Update stats
                for j, result in enumerate(results):
                    if isinstance(result, Exception):
                        self.logger.error(f"Exception in batch: {result}")
                        self.stats['failed'] += 1
                    elif result:
                        self.stats['successful'] += 1
                    else:
                        self.stats['failed'] += 1
                
                # Progress update
                total_processed = i + len(batch)
                self.print_progress(total_processed, len(pages_data))
                
                # Rate limiting between batches
                if i + batch_size < len(pages_data):
                    await asyncio.sleep(1)
    
    def print_progress(self, current: int, total: int):
        """Print progress with ETA."""
        if self.stats['start_time']:
            elapsed = time.time() - self.stats['start_time']
            rate = current / elapsed if elapsed > 0 else 0
            eta = (total - current) / rate if rate > 0 else 0
            eta_str = str(timedelta(seconds=int(eta)))
            
            self.logger.info(
                f"Progress: {current}/{total} ({current*100/total:.1f}%) | "
                f"Success: {self.stats['successful']} | "
                f"Failed: {self.stats['failed']} | "
                f"Skipped: {self.stats['skipped']} | "
                f"Rate: {rate:.1f}/s | "
                f"ETA: {eta_str}"
            )
    
    async def process_blocks_async(self, dry_run: bool = False, limit: int = None):
        """Process blocks and create Wiki pages using async operations."""
        data = self.load_blocks_data()
        folders = self.load_folder_structure()
        
        # Filter blocks to include in documentation
        blocks = [b for b in data['blocks'] if b.get('includeInWebDocumentation', False)]
        
        if limit:
            blocks = blocks[:limit]
            self.logger.info(f"Limited to first {limit} blocks for testing")
        
        self.logger.info(f"Processing {len(blocks)} blocks (dry_run={dry_run})")
        
        # Prepare page data
        pages_data = []
        folder_blocks = {}  # Track blocks by folder for category pages
        
        for block in blocks:
            block_name = block['name']
            block_id = f"block:{block_name.lower()}"
            
            # Get folder path from new structure
            folder_path, category = self.get_block_folder_path(block_id, folders)
            
            # If not found in new structure, use old categories
            if not folder_path and block.get('categories'):
                category = block['categories'][0] if block['categories'] else 'uncategorized'
                folder_path = category.lower().replace(' ', '-')
            
            # Create page path
            path = f"/blocks/{folder_path}/{block_name.lower()}" if folder_path else f"/blocks/{block_name.lower()}"
            
            # Track for folder pages
            if folder_path not in folder_blocks:
                folder_blocks[folder_path] = []
            folder_blocks[folder_path].append(block)
            
            # Create content
            content = self.create_block_page_content(block, category)
            title = block.get('displayName', block_name)
            
            # Create tags
            tags = ['blocks']
            if category:
                tags.append(category.lower())
            tags.extend(block.get('tags', []))
            
            pages_data.append((path, title, content, tags))
        
        if dry_run:
            self.logger.info("Dry run - would create the following pages:")
            for path, _, _, _ in pages_data[:10]:
                self.logger.info(f"  {path}")
            if len(pages_data) > 10:
                self.logger.info(f"  ... and {len(pages_data) - 10} more")
            return
        
        # Create pages
        self.stats['start_time'] = time.time()
        await self.create_pages_batch(pages_data, batch_size=self.config.get('batch_size', 10))
        
        # Create folder index pages
        if self.config.get('create_category_pages', True):
            await self.create_folder_pages(folder_blocks, folders)
        
        # Final stats
        elapsed = time.time() - self.stats['start_time']
        self.logger.info(
            f"\nCompleted in {timedelta(seconds=int(elapsed))} | "
            f"Success: {self.stats['successful']} | "
            f"Failed: {self.stats['failed']} | "
            f"Skipped: {self.stats['skipped']}"
        )
    
    async def create_folder_pages(self, folder_blocks: Dict[str, List], folders: List[Dict]):
        """Create index pages for folders."""
        pages_data = []
        
        # Create pages for each folder
        for folder_path, blocks in folder_blocks.items():
            if not folder_path:
                continue
                
            # Find folder info
            folder_info = None
            for folder in folders:
                if folder['name'].lower().replace(' ', '-') == folder_path:
                    folder_info = folder
                    break
            
            if folder_info:
                title = f"{folder_info['name']} Blocks"
                icon = folder_info.get('icon', '')
                
                content = [f"# {icon} {title}" if icon else f"# {title}", ""]
                content.append(f"This category contains **{len(blocks)}** blocks:")
                content.append("")
                
                # Sort blocks alphabetically
                sorted_blocks = sorted(blocks, key=lambda x: x['name'].lower())
                
                for block in sorted_blocks:
                    block_path = f"/blocks/{folder_path}/{block['name'].lower()}"
                    desc = block.get('description', 'No description available')
                    if len(desc) > 100:
                        desc = desc[:97] + "..."
                    content.append(f"- [{block['name']}]({block_path}) - {desc}")
                
                content_str = '\n'.join(content)
                path = f"/blocks/{folder_path}"
                tags = ['blocks', 'category', folder_info['name'].lower()]
                
                pages_data.append((path, title, content_str, tags))
        
        # Create main blocks index
        main_content = ["# 📦 Blocks", ""]
        main_content.append("Welcome to the Blocks documentation! Blocks are the building components you use to create patches in PatchWorld.")
        main_content.append("")
        main_content.append("## Block Categories")
        main_content.append("")
        
        # Add categories in order from folders structure
        for folder in folders:
            if folder['id'] != 'block-folder-decor':  # Skip decor parent, show children
                folder_name = folder['name']
                folder_path = folder_name.lower().replace(' ', '-')
                icon = folder.get('icon', '')
                block_count = folder.get('assetCount', 0)
                
                main_content.append(f"### {icon} [{folder_name}](/blocks/{folder_path})")
                main_content.append(f"*{block_count} blocks*")
                main_content.append("")
        
        pages_data.append(("/blocks", "Blocks", '\n'.join(main_content), ['blocks', 'index']))
        
        # Create pages
        await self.create_pages_batch(pages_data, batch_size=5)

def run_cleanup(dry_run: bool = False):
    """Run the cleanup script."""
    cleanup_cmd = ['python', 'wiki-cleanup.py', '--blocks-only']
    if dry_run:
        cleanup_cmd.append('--dry-run')
    else:
        cleanup_cmd.append('--confirm')
    
    print("=== Cleaning up existing block pages ===")
    result = subprocess.run(cleanup_cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description='Optimized Wiki.js population')
    parser.add_argument('--config', '-c', default='wiki-config.json', 
                       help='Configuration file path')
    parser.add_argument('--dry-run', '-d', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    parser.add_argument('--limit', '-l', type=int, 
                       help='Limit number of blocks to process (for testing)')
    parser.add_argument('--batch-size', '-b', type=int, default=10,
                       help='Number of concurrent requests (default: 10)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up existing block pages before creating new ones')
    parser.add_argument('--cleanup-only', action='store_true',
                       help='Only clean up existing pages, do not create new ones')
    
    args = parser.parse_args()
    
    # Handle cleanup
    if args.cleanup or args.cleanup_only:
        if not run_cleanup(dry_run=args.dry_run):
            print("Cleanup failed, aborting...")
            sys.exit(1)
    
    # Only process blocks if not cleanup-only
    if not args.cleanup_only:
        # Update config with command line args
        populator = OptimizedWikiPopulator(args.config)
        populator.config['verbose'] = args.verbose
        populator.config['batch_size'] = args.batch_size
        
        # Add block_folders_path to config if not present
        if 'block_folders_path' not in populator.config:
            populator.config['block_folders_path'] = 'C:\\Users\\mcbub\\NewPatch\\Assets\\StreamingAssets\\block_folders.json'
        
        try:
            asyncio.run(populator.process_blocks_async(dry_run=args.dry_run, limit=args.limit))
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()