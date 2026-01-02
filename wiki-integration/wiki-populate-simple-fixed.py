#!/usr/bin/env python3
"""
Simple Wiki.js Block Documentation Populator - FIXED VERSION

Simplified version that:
- References images from documentation server instead of uploading
- Focuses on fast, reliable page creation
- Includes cleanup options
- FIXES: Empty category handling and related blocks links
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
        # Build a map of block names to their categories for related blocks
        self.block_category_map = {}
        
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
        
        # Build the block category map for related blocks links
        for block in data['blocks']:
            # Only include blocks that are in web docs AND don't have DoNotInclude tag
            if (block.get('includeInWebDocumentation', False) 
                and 'DoNotInclude' not in block.get('tags', [])):
                # Filter and clean categories
                categories = [cat for cat in block.get('categories', []) 
                             if cat and cat not in ['For removal', 'For Hiding']]
                if categories:
                    # Store the first valid category for this block
                    self.block_category_map[block['name'].lower()] = categories[0]
        
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
    
    def get_related_block_path(self, block_name: str) -> str:
        """Get the correct path for a related block, including its category."""
        block_lower = block_name.lower()
        if block_lower in self.block_category_map:
            category = self.block_category_map[block_lower]
            category_path = category.lower().replace(' ', '-').replace('/', '/')
            return f"/blocks/{category_path}/{block_lower}"
        else:
            # Fallback if we can't find the block's category
            return f"/blocks/uncategorized/{block_lower}"
    
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
        
        # Categories - filter out empty categories
        if block.get('categories'):
            content.append("## Categories")
            content.append("")
            categories = [cat for cat in block['categories'] 
                         if cat and cat not in ['For removal', 'For Hiding']]
            for category in categories:
                content.append(f"- {category}")
            content.append("")
        
        # Related blocks - use correct paths with categories
        if block.get('relatedBlocks'):
            content.append("## Related Blocks")
            content.append("")
            for related in block['relatedBlocks']:
                related_path = self.get_related_block_path(related)
                content.append(f"- [{related}]({related_path})")
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
        # Filter out empty categories and unwanted ones
        valid_categories = [cat for cat in categories 
                           if cat and cat not in ['For removal', 'For Hiding']]
        
        if not valid_categories:
            return "blocks/uncategorized"
        
        # Use the first valid category as the main category
        main_category = valid_categories[0]
        
        # Handle category hierarchy like "Audio/Generators" -> "audio/generators"
        if '/' in main_category:
            parts = main_category.split('/')
            return f"blocks/{'/'.join(part.lower().replace(' ', '-') for part in parts)}"
        else:
            return f"blocks/{main_category.lower().replace(' ', '-')}"
    
    def create_page_with_description(self, path: str, title: str, content: str, description: str, tags: List[str] = None) -> bool:
        """Create a new page in Wiki.js with a custom description."""
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
            'description': description,
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
    
    def create_category_page(self, category: str, blocks: List[Dict], is_subcategory: bool = False, subcategories_dict: Dict = None) -> bool:
        """Create a category index page."""
        # Skip empty categories
        if not category:
            self.logger.warning("Skipping empty category")
            return False
            
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
        
        # For main categories with subcategories, organize by subcategory
        if not is_subcategory and subcategories_dict:
            # Find all subcategories for this main category
            relevant_subcats = {subcat: subblocks for subcat, subblocks in subcategories_dict.items() 
                               if subcat.startswith(category + '/')}
            
            if relevant_subcats:
                # Remove duplicates from blocks list
                unique_blocks = list({block['name']: block for block in blocks}.values())
                content.append(f"This category contains **{len(unique_blocks)}** blocks organized by type:")
                content.append("")
                
                # Group blocks by their subcategory
                blocks_by_subcat = {}
                blocks_without_subcat = []
                
                for block in unique_blocks:
                    block_cats = block.get('categories', [])
                    # Find if this block belongs to a subcategory
                    found_subcat = False
                    for cat in block_cats:
                        if cat.startswith(category + '/'):
                            if cat not in blocks_by_subcat:
                                blocks_by_subcat[cat] = []
                            blocks_by_subcat[cat].append(block)
                            found_subcat = True
                            break
                    if not found_subcat:
                        # Block belongs to main category but not a subcategory
                        if category in block_cats:
                            blocks_without_subcat.append(block)
                
                # Display subcategories
                for subcat in sorted(blocks_by_subcat.keys()):
                    subcat_name = subcat.split('/')[-1]
                    subcat_path = f"/blocks/{subcat.lower().replace(' ', '-').replace('/', '/')}"
                    content.append(f"## [{subcat_name}]({subcat_path})")
                    content.append("")
                    
                    # Sort blocks in this subcategory
                    sorted_subcat_blocks = sorted(blocks_by_subcat[subcat], key=lambda x: x['name'].lower())
                    for block in sorted_subcat_blocks:
                        block_categories = [cat for cat in block.get('categories', [])
                                          if cat and cat not in ['For removal', 'For Hiding']]
                        block_path = self.get_category_path(block_categories)
                        block_page_path = f"/{block_path}/{block['name'].lower()}"
                        
                        desc = block.get('description', 'No description available')
                        if len(desc) > 100:
                            desc = desc[:97] + "..."
                        content.append(f"- [{block['name']}]({block_page_path}) - {desc}")
                    content.append("")
                
                # Display blocks without subcategory if any
                if blocks_without_subcat:
                    content.append(f"## General {category}")
                    content.append("")
                    sorted_general = sorted(blocks_without_subcat, key=lambda x: x['name'].lower())
                    for block in sorted_general:
                        block_categories = [cat for cat in block.get('categories', [])
                                          if cat and cat not in ['For removal', 'For Hiding']]
                        block_path = self.get_category_path(block_categories)
                        block_page_path = f"/{block_path}/{block['name'].lower()}"
                        
                        desc = block.get('description', 'No description available')
                        if len(desc) > 100:
                            desc = desc[:97] + "..."
                        content.append(f"- [{block['name']}]({block_page_path}) - {desc}")
                    content.append("")
            else:
                # No subcategories, display as before
                content.append(f"This category contains **{len(blocks)}** blocks:")
                content.append("")
                sorted_blocks = sorted(blocks, key=lambda x: x['name'].lower())
                for block in sorted_blocks:
                    block_categories = [cat for cat in block.get('categories', [])
                                       if cat and cat not in ['For removal', 'For Hiding']]
                    block_path = self.get_category_path(block_categories)
                    block_page_path = f"/{block_path}/{block['name'].lower()}"
                    
                    desc = block.get('description', 'No description available')
                    if len(desc) > 100:
                        desc = desc[:97] + "..."
                    content.append(f"- [{block['name']}]({block_page_path}) - {desc}")
        else:
            # Subcategory page or main category without subcategories
            content.append(f"This category contains **{len(blocks)}** blocks:")
            content.append("")
            sorted_blocks = sorted(blocks, key=lambda x: x['name'].lower())
            for block in sorted_blocks:
                block_categories = [cat for cat in block.get('categories', [])
                                   if cat and cat not in ['For removal', 'For Hiding']]
                block_path = self.get_category_path(block_categories)
                block_page_path = f"/{block_path}/{block['name'].lower()}"
                
                desc = block.get('description', 'No description available')
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                content.append(f"- [{block['name']}]({block_page_path}) - {desc}")
        
        content_str = '\n'.join(content)
        tags = ['blocks', 'category', category.lower()]
        
        return self.create_page(path, title, content_str, tags)
    
    def process_blocks(self, dry_run: bool = False, limit: int = None):
        """Process blocks and create Wiki pages."""
        data = self.load_blocks_data()
        # Filter blocks: must be included in web docs AND not have "DoNotInclude" tag
        blocks = [b for b in data['blocks'] 
                 if b.get('includeInWebDocumentation', False) 
                 and 'DoNotInclude' not in b.get('tags', [])]
        
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
            
            # Use organized path based on categories (filter out unwanted categories)
            block_categories = [cat for cat in block.get('categories', []) 
                              if cat and cat not in ['For removal', 'For Hiding', '']]
            category_path = self.get_category_path(block_categories)
            path = f"/{category_path}/{block_name.lower()}"
            
            title = block.get('displayName', block_name)
            
            # Create tags (filter out empty strings)
            tags = ['blocks']
            tags.extend([cat for cat in block_categories if cat])
            tags.extend([tag for tag in block.get('tags', []) if tag])
            
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
            
            # Group by categories for index pages (filter out unwanted and empty categories)
            for category in block_categories:
                # Skip categories that shouldn't appear in wiki or are empty
                if category in ['For removal', 'For Hiding', ''] or not category:
                    continue
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
                if not category:  # Skip empty categories
                    continue
                    
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
            
            # Create main category pages (pass subcategories dict for organization)
            for main_category, main_blocks in main_categories.items():
                if main_category:  # Skip empty categories
                    if self.create_category_page(main_category, main_blocks, is_subcategory=False, subcategories_dict=subcategories):
                        self.logger.info(f"Created main category page: {main_category}")
            
            # Create subcategory pages
            for subcategory, sub_blocks in subcategories.items():
                if subcategory:  # Skip empty categories
                    if self.create_category_page(subcategory, sub_blocks, is_subcategory=True):
                        self.logger.info(f"Created subcategory page: {subcategory}")
            
            # Create main blocks index page - AFTER all other pages
            self.create_blocks_index_page(main_categories)
        
        self.logger.info(f"Finished: {successful} successful, {failed} failed")
    
    def update_index_page_only(self, dry_run: bool = False):
        """Update only the main index page without processing individual blocks."""
        self.logger.info("Updating main index page only...")
        
        # Load blocks data
        data = self.load_blocks_data()
        blocks = [b for b in data['blocks'] 
                 if b.get('includeInWebDocumentation', False) 
                 and 'DoNotInclude' not in b.get('tags', [])]
        
        # Group blocks by categories for the index page
        categories = {}
        for block in blocks:
            block_categories = [cat for cat in block.get('categories', []) 
                              if cat and cat not in ['For removal', 'For Hiding', '']]
            for category in block_categories:
                if category not in categories:
                    categories[category] = []
                categories[category].append(block)
        
        # Group categories by main category
        main_categories = {}
        for category, category_blocks in categories.items():
            if not category:
                continue
                
            if '/' in category:
                # This is a subcategory like "Audio/Generators"
                main_cat = category.split('/')[0]
                if main_cat not in main_categories:
                    main_categories[main_cat] = []
                main_categories[main_cat].extend(category_blocks)
            else:
                # This is a main category
                if category not in main_categories:
                    main_categories[category] = []
                main_categories[category].extend(category_blocks)
        
        if dry_run:
            self.logger.info("[DRY RUN] Would update main index page at /blocks")
            self.logger.info(f"Categories found: {list(main_categories.keys())}")
        else:
            # Delete existing index page first
            self.delete_page_if_exists("/blocks")
            
            # Create new index page
            if self.create_blocks_index_page(main_categories):
                self.logger.info("Successfully updated main index page")
            else:
                self.logger.error("Failed to update main index page")
    
    def delete_page_if_exists(self, path: str) -> bool:
        """Delete a page if it exists."""
        query = """
        query GetPage($path: String!) {
            pages {
                single(path: $path) {
                    id
                    path
                    title
                }
            }
        }
        """
        
        try:
            response = self.session.post(
                f"{self.config['wiki_url']}/graphql",
                json={'query': query, 'variables': {'path': path}},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                page = data.get('data', {}).get('pages', {}).get('single')
                if page and page.get('id'):
                    # Page exists, delete it
                    delete_mutation = """
                    mutation DeletePage($id: Int!) {
                        pages {
                            delete(id: $id) {
                                responseResult {
                                    succeeded
                                    message
                                }
                            }
                        }
                    }
                    """
                    
                    delete_response = self.session.post(
                        f"{self.config['wiki_url']}/graphql",
                        json={'query': delete_mutation, 'variables': {'id': page['id']}},
                        timeout=10
                    )
                    
                    if delete_response.status_code == 200:
                        delete_data = delete_response.json()
                        if delete_data.get('data', {}).get('pages', {}).get('delete', {}).get('responseResult', {}).get('succeeded'):
                            self.logger.info(f"Deleted existing page: {path}")
                            return True
        except Exception as e:
            self.logger.warning(f"Could not check/delete existing page: {e}")
        
        return False
    
    def create_blocks_index_page(self, main_categories: Dict[str, List[Dict]]) -> bool:
        """Create the main blocks index page."""
        path = "/blocks"
        title = "Blocks"
        
        content = []
        content.append("These are the fundamental building blocks available in PatchWorld. You can use these blocks to create patches, instruments, and interactive experiences.")
        content.append("")
        content.append("💡 **Note:** Beyond these basic blocks, PatchWorld offers:")
        content.append("- **Instruments & Devices** - Pre-built combinations of blocks for music and interaction")
        content.append("- **Imported Assets** - Custom 3D models, sounds, and creations from the community")
        content.append("- **Your Own Creations** - Save and share your patches as reusable devices")
        content.append("")
        
        # Calculate total unique blocks
        all_blocks = set()
        for blocks in main_categories.values():
            for block in blocks:
                all_blocks.add(block['name'])
        total_blocks = len(all_blocks)
        
        content.append(f"**{total_blocks} blocks** available across **{len(main_categories)} categories**")
        content.append("")
        content.append("---")
        content.append("")
        
        # Core categories section
        content.append("## 🎛️ Core Building Blocks")
        content.append("")
        
        # Define category groups with descriptions
        core_categories = {
            "Interfaces": "User interaction and control elements",
            "Audio": "Sound generation and processing",
            "Logic": "Data flow and decision making",
            "Connectors": "Linking and routing signals"
        }
        
        creative_categories = {
            "Visuals": "Visual effects and displays",
            "Motion": "Movement and animation",
            "Player": "User presence and interaction"
        }
        
        world_categories = {
            "Props": "Decorative and interactive objects",
            "Sky": "Environment and atmosphere",
            "Stages": "Performance spaces",
            "Terrains": "Ground and landscape"
        }
        
        # Display core categories in a table format
        content.append("| Category | Blocks | Description |")
        content.append("|----------|--------|-------------|")
        
        for category, description in core_categories.items():
            if category in main_categories:
                unique_blocks = list({block['name']: block for block in main_categories[category]}.values())
                block_count = len(unique_blocks)
                category_path = f"/blocks/{category.lower().replace(' ', '-')}"
                content.append(f"| **[{category}]({category_path})** | {block_count} | {description} |")
        
        content.append("")
        
        # Creative categories section
        content.append("## 🎨 Creative & Interactive")
        content.append("")
        content.append("| Category | Blocks | Description |")
        content.append("|----------|--------|-------------|")
        
        for category, description in creative_categories.items():
            if category in main_categories:
                unique_blocks = list({block['name']: block for block in main_categories[category]}.values())
                block_count = len(unique_blocks)
                category_path = f"/blocks/{category.lower().replace(' ', '-')}"
                content.append(f"| **[{category}]({category_path})** | {block_count} | {description} |")
        
        content.append("")
        
        # World building section
        content.append("## 🌍 World Building")
        content.append("")
        content.append("| Category | Blocks | Description |")
        content.append("|----------|--------|-------------|")
        
        for category, description in world_categories.items():
            if category in main_categories:
                unique_blocks = list({block['name']: block for block in main_categories[category]}.values())
                block_count = len(unique_blocks)
                category_path = f"/blocks/{category.lower().replace(' ', '-')}"
                content.append(f"| **[{category}]({category_path})** | {block_count} | {description} |")
        
        content.append("")
        
        # Other categories (System, Experimental, etc)
        other_cats = []
        for category, blocks in sorted(main_categories.items()):
            if (category not in core_categories and 
                category not in creative_categories and
                category not in world_categories and
                category not in ['For removal', 'For Hiding', ''] and 
                category):
                other_cats.append(category)
        
        if other_cats:
            content.append("## 🔧 Advanced & Experimental")
            content.append("")
            content.append("| Category | Blocks |")
            content.append("|----------|--------|")
            
            for category in other_cats:
                unique_blocks = list({block['name']: block for block in main_categories[category]}.values())
                block_count = len(unique_blocks)
                category_path = f"/blocks/{category.lower().replace(' ', '-')}"
                content.append(f"| **[{category}]({category_path})** | {block_count} |")
            
            content.append("")
        
        content.append("---")
        content.append("")
        content.append("## 🚀 Getting Started")
        content.append("")
        content.append("- **New to PatchWorld?** Start with [Interfaces](/blocks/interfaces) for controls and [Audio](/blocks/audio) for sound")
        content.append("- **Building worlds?** Check out [Props](/blocks/props) and [Stages](/blocks/stages)")
        content.append("- **Advanced patching?** Explore [Logic](/blocks/logic) and [Connectors](/blocks/connectors)")
        content.append("")
        content.append("---")
        content.append("")
        content.append("*This documentation is automatically generated from the PatchWorld application.*")
        
        content_str = '\n'.join(content)
        tags = ['blocks', 'index', 'documentation']
        
        self.logger.info(f"Creating main blocks index page at {path}")
        
        # Create the page with a better description
        return self.create_page_with_description(path, title, content_str, 
                                                 "Comprehensive guide to all fundamental building blocks in PatchWorld",
                                                 tags)

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
    parser = argparse.ArgumentParser(description='Simple Wiki.js population with cleanup - FIXED')
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
    parser.add_argument('--index-only', action='store_true',
                       help='Only update the main blocks index page')
    
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
            if args.index_only:
                # Only update the index page
                populator.update_index_page_only(dry_run=args.dry_run)
            else:
                # Normal processing
                populator.process_blocks(dry_run=args.dry_run, limit=args.limit)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()