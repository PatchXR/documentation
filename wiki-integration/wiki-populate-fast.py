#!/usr/bin/env python3
"""
Fast Wiki.js Block Documentation Populator

Optimized version that:
- Uploads images to Wiki.js assets
- Batches operations for better performance
- Skips unnecessary API calls
"""

import argparse
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
import requests
import base64
import mimetypes
from datetime import datetime

class FastWikiPopulator:
    def __init__(self, config_path: str):
        """Initialize the Wiki populator with configuration."""
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f"Bearer {self.config['wiki_api_token']}",
            'Content-Type': 'application/json'
        })
        self.uploaded_images = {}  # Cache for uploaded image URLs
        
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
                logging.FileHandler('wiki-populate-fast.log')
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
    
    def upload_image(self, image_path: str, block_name: str) -> Optional[str]:
        """Upload an image to Wiki.js and return the URL."""
        if not os.path.exists(image_path):
            self.logger.warning(f"Image not found: {image_path}")
            return None
        
        # Check cache first
        if image_path in self.uploaded_images:
            return self.uploaded_images[image_path]
        
        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Prepare for upload
            filename = f"{block_name}.png"
            
            # Wiki.js asset upload mutation
            mutation = """
            mutation UploadAsset($file: Upload!) {
                assets {
                    createFile(file: $file, folderId: 0) {
                        responseResult {
                            succeeded
                            errorCode
                            message
                        }
                        file {
                            id
                            filename
                            ext
                            kind
                            mime
                            fileSize
                            metadata
                        }
                    }
                }
            }
            """
            
            # Prepare multipart form data
            files = {
                'operations': (None, json.dumps({
                    'query': mutation,
                    'variables': {'file': None}
                })),
                'map': (None, json.dumps({'0': ['variables.file']})),
                '0': (filename, image_data, 'image/png')
            }
            
            # Remove Content-Type header for multipart upload
            headers = {'Authorization': f"Bearer {self.config['wiki_api_token']}"}
            
            response = requests.post(
                f"{self.config['wiki_url']}/graphql",
                files=files,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data', {}).get('assets', {}).get('createFile', {}).get('responseResult', {}).get('succeeded'):
                    file_info = data['data']['assets']['createFile']['file']
                    image_url = f"{self.config['wiki_url']}/a/{file_info['filename']}"
                    self.uploaded_images[image_path] = image_url
                    self.logger.info(f"Uploaded image: {filename}")
                    return image_url
                else:
                    error_msg = data.get('data', {}).get('assets', {}).get('createFile', {}).get('responseResult', {}).get('message', 'Unknown error')
                    self.logger.error(f"Failed to upload image {filename}: {error_msg}")
            else:
                self.logger.error(f"Image upload failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error uploading image {image_path}: {e}")
        
        return None
    
    def create_block_page_content(self, block: Dict, image_url: Optional[str] = None) -> str:
        """Create markdown content for a block page."""
        content = []
        
        # Title and description
        content.append(f"# {block['name']}")
        content.append("")
        
        # Add image if available
        if image_url:
            content.append(f"![{block['name']} thumbnail]({image_url})")
            content.append("")
        
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
        content.append(f"- **Categories**: {', '.join(block.get('categories', []))}")
        
        return '\n'.join(content)
    
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
                    # Skip duplicate errors
                    if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                        self.logger.info(f"Page already exists: {path}")
                        return True
                    else:
                        self.logger.error(f"Failed to create page {path}: {error_msg}")
            else:
                self.logger.error(f"Page creation failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error creating page {path}: {e}")
        
        return False
    
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
        
        for i, block in enumerate(blocks, 1):
            block_name = block['name']
            self.logger.info(f"[{i}/{len(blocks)}] Processing: {block_name}")
            
            # Handle thumbnail image
            image_url = None
            if self.config.get('upload_images', True):
                thumbnails_path = self.config.get('thumbnails_path', '')
                image_path = os.path.join(thumbnails_path, f"{block_name}.png")
                
                if not os.path.exists(image_path):
                    # Try common variations
                    variations = [
                        f"{block_name.lower()}.png",
                        f"{block_name.replace('_', '')}.png",
                        f"{block_name.replace('_', '-')}.png"
                    ]
                    for variation in variations:
                        test_path = os.path.join(thumbnails_path, variation)
                        if os.path.exists(test_path):
                            image_path = test_path
                            break
                
                if not dry_run and os.path.exists(image_path):
                    image_url = self.upload_image(image_path, block_name)
            
            # Create page content
            content = self.create_block_page_content(block, image_url)
            path = f"/blocks/{block_name.lower()}"
            title = block.get('displayName', block_name)
            tags = ['blocks'] + block.get('categories', []) + block.get('tags', [])
            
            if dry_run:
                self.logger.info(f"[DRY RUN] Would create page: {path}")
                if image_url:
                    self.logger.info(f"[DRY RUN] Would include image: {image_url}")
                successful += 1
            else:
                if self.create_page(path, title, content, tags):
                    successful += 1
                    self.logger.info(f"Created: {path}")
                else:
                    failed += 1
                    self.logger.error(f"Failed: {path}")
        
        self.logger.info(f"Finished: {successful} successful, {failed} failed")

def main():
    parser = argparse.ArgumentParser(description='Fast Wiki.js population with image support')
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
    
    populator = FastWikiPopulator(args.config)
    populator.config['verbose'] = args.verbose
    
    try:
        # Import cleanup functionality
        if args.cleanup or args.cleanup_only:
            import subprocess
            cleanup_cmd = ['python', 'wiki-cleanup.py', '--blocks-only']
            if args.dry_run:
                cleanup_cmd.append('--dry-run')
            else:
                cleanup_cmd.append('--confirm')
            
            print("=== Cleaning up existing block pages ===")
            result = subprocess.run(cleanup_cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            if result.returncode != 0:
                print("Cleanup failed, aborting...")
                sys.exit(1)
        
        # Only process blocks if not cleanup-only
        if not args.cleanup_only:
            populator.process_blocks(dry_run=args.dry_run, limit=args.limit)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()