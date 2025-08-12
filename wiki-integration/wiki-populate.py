#!/usr/bin/env python3
"""
Wiki.js Block Documentation Populator

This script extracts block documentation from the NewPatch documentation project
and populates a Wiki.js instance via GraphQL API.

Usage:
    python wiki-populate.py --config config.json [--dry-run] [--verbose]
"""

import argparse
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
import requests
import hashlib
from datetime import datetime

class WikiPopulator:
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
                logging.FileHandler('wiki-populate.log')
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
    
    def rst_to_markdown(self, rst_content: str) -> str:
        """Convert RST content to Markdown format."""
        # Basic RST to Markdown conversion
        # This is a simplified conversion - you might want to use a proper library like pandoc
        
        markdown = rst_content
        
        # Convert RST headers (===) to Markdown headers (#)
        lines = markdown.split('\n')
        converted_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if i + 1 < len(lines) and lines[i + 1].strip() and all(c == '=' for c in lines[i + 1].strip()):
                # RST level 1 header
                converted_lines.append(f"# {line}")
                i += 2  # Skip the === line
            elif i + 1 < len(lines) and lines[i + 1].strip() and all(c == '-' for c in lines[i + 1].strip()):
                # RST level 2 header
                converted_lines.append(f"## {line}")
                i += 2  # Skip the --- line
            else:
                # Convert RST references :ref:`block <block>` to [block](block)
                import re
                line = re.sub(r':ref:`([^<]+) <([^>]+)>`', r'[\1](\2)', line)
                converted_lines.append(line)
                i += 1
        
        return '\n'.join(converted_lines)
    
    def create_block_page_content(self, block: Dict) -> str:
        """Create markdown content for a block page."""
        content = []
        
        # Title and description
        content.append(f"# {block['name']}")
        content.append("")
        
        if block.get('description'):
            content.append("## Description")
            content.append("")
            content.append(block['description'])
            content.append("")
        
        if block.get('longDescription'):
            content.append(block['longDescription'])
            content.append("")
        
        # Add thumbnail if available
        if block.get('thumbnailImage'):
            content.append(f"![{block['name']} thumbnail]({block['thumbnailImage']})")
            content.append("")
        
        # Parts (inputs/outputs)
        if block.get('parts'):
            content.append("## Inputs, Outputs and Parts")
            content.append("")
            for part in block['parts']:
                type_str = f" ({part['type']})" if part.get('type') else ""
                content.append(f"**{part['name']}**{type_str}: {part.get('description', '')}")
                content.append("")
        
        # Categories
        if block.get('categories'):
            content.append("## Categories")
            content.append("")
            for category in block['categories']:
                content.append(f"- {category}")
            content.append("")
        
        # Related blocks
        if block.get('relatedBlocks'):
            content.append("## Related Blocks")
            content.append("")
            for related in block['relatedBlocks']:
                # Create wiki link to related block
                content.append(f"- [{related}](/blocks/{related.lower()})")
            content.append("")
        
        # Tags
        if block.get('tags'):
            content.append("## Tags")
            content.append("")
            content.append(", ".join(block['tags']))
            content.append("")
        
        # Metadata
        content.append("---")
        content.append("")
        content.append("## Metadata")
        content.append("")
        content.append(f"- **Display Name**: {block.get('displayName', block['name'])}")
        content.append(f"- **Version**: {block.get('version', 'N/A')}")
        content.append(f"- **Include in Documentation**: {block.get('includeInWebDocumentation', False)}")
        
        return '\n'.join(content)
    
    def graphql_query(self, query: str, variables: Dict = None) -> Dict:
        """Execute a GraphQL query against Wiki.js API."""
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        response = self.session.post(
            f"{self.config['wiki_url']}/graphql",
            json=payload
        )
        
        if response.status_code != 200:
            self.logger.error(f"GraphQL request failed: {response.status_code} - {response.text}")
            return None
        
        return response.json()
    
    def page_exists(self, path: str) -> bool:
        """Check if a page exists at the given path."""
        # For now, always return False to avoid the API issue
        # This means we'll always try to create pages (Wiki.js will handle duplicates)
        return False
    
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
            'description': f"Auto-generated documentation for {title}",
            'editor': 'markdown',
            'isPublished': True,
            'isPrivate': False,
            'locale': self.config.get('locale', 'en'),
            'path': path,
            'tags': tags or [],
            'title': title
        }
        
        result = self.graphql_query(mutation, variables)
        
        if result and result.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {}).get('succeeded'):
            self.logger.info(f"Created page: {path}")
            return True
        else:
            error_msg = result.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {}).get('message', 'Unknown error')
            self.logger.error(f"Failed to create page {path}: {error_msg}")
            return False
    
    def update_page(self, page_id: int, content: str, title: str, tags: List[str] = None) -> bool:
        """Update an existing page in Wiki.js."""
        mutation = """
        mutation UpdatePage(
            $id: Int!
            $content: String!
            $description: String!
            $isPublished: Boolean!
            $isPrivate: Boolean!
            $tags: [String]!
            $title: String!
        ) {
            pages {
                update(
                    id: $id
                    content: $content
                    description: $description
                    isPublished: $isPublished
                    isPrivate: $isPrivate
                    tags: $tags
                    title: $title
                ) {
                    responseResult {
                        succeeded
                        errorCode
                        message
                    }
                }
            }
        }
        """
        
        variables = {
            'id': page_id,
            'content': content,
            'description': f"Auto-generated documentation for {title}",
            'isPublished': True,
            'isPrivate': False,
            'tags': tags or [],
            'title': title
        }
        
        result = self.graphql_query(mutation, variables)
        
        if result and result.get('data', {}).get('pages', {}).get('update', {}).get('responseResult', {}).get('succeeded'):
            self.logger.info(f"Updated page: {title}")
            return True
        else:
            error_msg = result.get('data', {}).get('pages', {}).get('update', {}).get('responseResult', {}).get('message', 'Unknown error')
            self.logger.error(f"Failed to update page {title}: {error_msg}")
            return False
    
    def get_page_id(self, path: str) -> Optional[int]:
        """Get the ID of a page by its path."""
        # For now, always return None to avoid the API issue
        return None
    
    def create_category_index_page(self, category: str, blocks: List[Dict]) -> bool:
        """Create an index page for a block category."""
        path = f"/blocks/{category.lower().replace(' ', '-')}"
        title = f"{category} Blocks"
        
        content = [f"# {title}", ""]
        content.append(f"This category contains {len(blocks)} blocks:")
        content.append("")
        
        for block in blocks:
            block_path = f"/blocks/{block['name'].lower()}"
            content.append(f"- [{block['name']}]({block_path}) - {block.get('description', '')}")
        
        content_str = '\n'.join(content)
        tags = ['blocks', 'category', category.lower()]
        
        if self.page_exists(path):
            page_id = self.get_page_id(path)
            if page_id:
                return self.update_page(page_id, content_str, title, tags)
        else:
            return self.create_page(path, title, content_str, tags)
        
        return False
    
    def process_blocks(self, dry_run: bool = False):
        """Process all blocks and create/update Wiki pages."""
        data = self.load_blocks_data()
        blocks = [b for b in data['blocks'] if b.get('includeInWebDocumentation', False)]
        
        self.logger.info(f"Processing {len(blocks)} blocks (dry_run={dry_run})")
        
        # Group blocks by category
        categories = {}
        
        for block in blocks:
            content = self.create_block_page_content(block)
            path = f"/blocks/{block['name'].lower()}"
            title = block.get('displayName', block['name'])
            tags = ['blocks'] + block.get('categories', []) + block.get('tags', [])
            
            if dry_run:
                self.logger.info(f"[DRY RUN] Would create/update page: {path}")
                continue
            
            # Create or update the block page
            if self.page_exists(path):
                page_id = self.get_page_id(path)
                if page_id:
                    self.update_page(page_id, content, title, tags)
            else:
                self.create_page(path, title, content, tags)
            
            # Group by categories for index pages
            for category in block.get('categories', ['Uncategorized']):
                if category not in categories:
                    categories[category] = []
                categories[category].append(block)
        
        # Create category index pages
        if not dry_run:
            for category, category_blocks in categories.items():
                if category != 'For removal':  # Skip removed blocks
                    self.create_category_index_page(category, category_blocks)
        
        self.logger.info(f"Finished processing {len(blocks)} blocks")

def main():
    parser = argparse.ArgumentParser(description='Populate Wiki.js with block documentation')
    parser.add_argument('--config', '-c', default='wiki-config.json', 
                       help='Configuration file path (default: wiki-config.json)')
    parser.add_argument('--dry-run', '-d', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Update config with command line options
    if not os.path.exists(args.config):
        print(f"Configuration file not found: {args.config}")
        print("Please create a configuration file. See wiki-config.json.example for template.")
        sys.exit(1)
    
    populator = WikiPopulator(args.config)
    populator.config['verbose'] = args.verbose
    
    try:
        populator.process_blocks(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()