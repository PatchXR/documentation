#!/usr/bin/env python3
"""
Simple Wiki.js Block Documentation Populator

Simplified version that:
- References images from documentation server instead of uploading
- Focuses on fast, reliable page creation
- Includes cleanup options
"""

import argparse
import json
import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import requests
from datetime import datetime

class SimpleWikiPopulator:
    def __init__(self, config_path: str):
        """Initialize the Wiki populator with configuration."""
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f"Bearer {self.config['wiki_api_token']}",
            'Content-Type': 'application/json'
        })
        
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
                logging.FileHandler('wiki-populate-simple.log')
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
    
    def find_thumbnail_url(self, block_name: str) -> Optional[str]:
        """Find thumbnail URL for a block using portal.patchxr.io."""
        # Check if thumbnail exists in local thumbnails path
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
                # Return URL to portal.patchxr.io static files
                base_url = self.config.get('docs_base_url', 'https://portal.patchxr.io')
                return f"{base_url}/block-thumbnails/{filename}"
        
        return None
    
    def create_block_page_content(self, block: Dict) -> str:
        """Create markdown content for a block page."""
        content = []
        
        # Title
        content.append(f"# {block['name']}")
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
        
        # Categories
        if block.get('categories'):
            content.append("## Categories")
            content.append("")
            categories = [cat for cat in block['categories'] if cat != 'For removal']
            for category in categories:
                content.append(f"- {category}")
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
    
    def get_category_path(self, categories: List[str]) -> str:
        """Get the organized path for a block based on its categories."""
        if not categories:
            return "blocks/uncategorized"
        
        # Use the first category as the main category
        main_category = categories[0]
        
        # Handle category hierarchy like "Audio/Generators" -> "audio/generators"
        if '/' in main_category:
            parts = main_category.split('/')
            return f"blocks/{'/'.join(part.lower().replace(' ', '-') for part in parts)}"
        else:
            return f"blocks/{main_category.lower().replace(' ', '-')}"
    
    def create_page(self, path: str, title: str, content: str, tags: List[str] = None) -> bool:
        """Create a new page in Wiki.js."""
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
        
        try:
            response = self.session.post(
                f"{self.config['wiki_url']}/graphql",
                json={'query': mutation, 'variables': variables},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {}).get('succeeded'):
                    return True
                else:
                    error_msg = data.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {}).get('message', 'Unknown error')
                    # Skip duplicate errors quietly
                    if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                        return True
                    else:
                        self.logger.error(f"Failed to create page {path}: {error_msg}")
            else:
                self.logger.error(f"Page creation failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error creating page {path}: {e}")
        
        return False
    
    def create_category_page(self, category: str, blocks: List[Dict], is_subcategory: bool = False) -> bool:
        """Create a category index page."""
        if is_subcategory:
            # For subcategories like "Audio/Generators"
            category_path = category.lower().replace(' ', '-').replace('/', '/')
            path = f"/blocks/{category_path}"
            title = category.split('/')[-1] + " Blocks"  # "Generators Blocks"
        else:
            # For main categories like "Audio"
            category_path = category.lower().replace(' ', '-')
            path = f"/blocks/{category_path}"
            title = f"{category} Blocks"
        
        content = [f"# {title}", ""]
        content.append(f"This category contains **{len(blocks)}** blocks:")
        content.append("")
        
        # Sort blocks alphabetically
        sorted_blocks = sorted(blocks, key=lambda x: x['name'].lower())
        
        for block in sorted_blocks:
            # Use the organized path for the block
            block_categories = block.get('categories', [])
            block_path = self.get_category_path(block_categories)
            block_page_path = f"/{block_path}/{block['name'].lower()}"
            
            desc = block.get('description', 'No description available')
            # Truncate long descriptions
            if len(desc) > 100:
                desc = desc[:97] + "..."
            content.append(f"- [{block['name']}]({block_page_path}) - {desc}")
        
        content_str = '\n'.join(content)
        tags = ['blocks', 'category', category.lower()]
        
        return self.create_page(path, title, content_str, tags)
    
    def process_blocks(self, dry_run: bool = False, limit: int = None):
        """Process blocks and create Wiki pages."""
        data = self.load_blocks_data()
        blocks = [b for b in data['blocks'] if b.get('includeInWebDocumentation', False)]
        
        if limit:
            blocks = blocks[:limit]
            self.logger.info(f"Limited to first {limit} blocks for testing")
        
        self.logger.info(f"Processing {len(blocks)} blocks (dry_run={dry_run})")
        
        successful = 0
        failed = 0
        categories = {}
        
        for i, block in enumerate(blocks, 1):
            block_name = block['name']
            
            # Create page content
            content = self.create_block_page_content(block)
            
            # Use organized path based on categories
            block_categories = [cat for cat in block.get('categories', []) if cat != 'For removal']
            category_path = self.get_category_path(block_categories)
            path = f"/{category_path}/{block_name.lower()}"
            
            title = block.get('displayName', block_name)
            
            # Create tags
            tags = ['blocks']
            tags.extend(block_categories)
            tags.extend(block.get('tags', []))
            
            if dry_run:
                self.logger.info(f"[{i}/{len(blocks)}] Would create: {path}")
                successful += 1
            else:
                self.logger.info(f"[{i}/{len(blocks)}] Creating: {block_name}")
                if self.create_page(path, title, content, tags):
                    successful += 1
                    self.logger.info(f"  -> Created: {path}")
                else:
                    failed += 1
                    self.logger.error(f"  -> Failed: {path}")
            
            # Group by categories for index pages
            for category in block_categories:
                if category not in categories:
                    categories[category] = []
                categories[category].append(block)
        
        # Create category index pages
        if not dry_run and self.config.get('create_category_pages', True):
            self.logger.info(f"Creating {len(categories)} category pages...")
            
            # Group categories by main category for better organization
            main_categories = {}
            subcategories = {}
            
            for category, category_blocks in categories.items():
                if '/' in category:
                    # This is a subcategory like "Audio/Generators"
                    main_cat = category.split('/')[0]
                    if main_cat not in main_categories:
                        main_categories[main_cat] = []
                    main_categories[main_cat].extend(category_blocks)
                    subcategories[category] = category_blocks
                else:
                    # This is a main category
                    if category not in main_categories:
                        main_categories[category] = []
                    main_categories[category].extend(category_blocks)
            
            # Create main category pages
            for main_category, main_blocks in main_categories.items():
                if self.create_category_page(main_category, main_blocks, is_subcategory=False):
                    self.logger.info(f"Created main category page: {main_category}")
            
            # Create subcategory pages
            for subcategory, sub_blocks in subcategories.items():
                if self.create_category_page(subcategory, sub_blocks, is_subcategory=True):
                    self.logger.info(f"Created subcategory page: {subcategory}")
            
            # Create main blocks index page
            self.create_blocks_index_page(main_categories)
        
        self.logger.info(f"Finished: {successful} successful, {failed} failed")
    
    def create_blocks_index_page(self, main_categories: Dict[str, List[Dict]]) -> bool:
        """Create the main blocks index page."""
        path = "/blocks"
        title = "PatchWorld Blocks"
        
        content = [f"# {title}", ""]
        content.append("Welcome to the PatchWorld Blocks documentation! Blocks are the building components you use to create patches in PatchWorld.")
        content.append("")
        content.append("## Block Categories")
        content.append("")
        
        # Sort categories to match portal order
        category_order = [
            "Interfaces", "Audio", "Visuals", "Motion", "Logic", "Player", "System"
        ]
        
        # First show ordered categories
        for category in category_order:
            if category in main_categories:
                block_count = len(main_categories[category])
                category_path = f"/blocks/{category.lower().replace(' ', '-')}"
                content.append(f"### [{category}]({category_path})")
                content.append(f"*{block_count} blocks*")
                content.append("")
        
        # Then show any remaining categories
        for category, blocks in main_categories.items():
            if category not in category_order:
                block_count = len(blocks)
                category_path = f"/blocks/{category.lower().replace(' ', '-')}"
                content.append(f"### [{category}]({category_path})")
                content.append(f"*{block_count} blocks*")
                content.append("")
        
        content.append("---")
        content.append("")
        content.append("*This documentation is automatically generated from the PatchWorld application.*")
        
        content_str = '\n'.join(content)
        tags = ['blocks', 'index', 'documentation']
        
        return self.create_page(path, title, content_str, tags)

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
    parser = argparse.ArgumentParser(description='Simple Wiki.js population with cleanup')
    parser.add_argument('--config', '-c', default='wiki-config.json', 
                       help='Configuration file path')
    parser.add_argument('--dry-run', '-d', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    parser.add_argument('--limit', '-l', type=int, 
                       help='Limit number of blocks to process (for testing)')
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
        populator = SimpleWikiPopulator(args.config)
        populator.config['verbose'] = args.verbose
        
        try:
            populator.process_blocks(dry_run=args.dry_run, limit=args.limit)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()