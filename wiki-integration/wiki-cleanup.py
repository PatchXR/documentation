#!/usr/bin/env python3
"""
Wiki.js Cleanup Tool

Removes block pages from Wiki.js for testing purposes.
"""

import argparse
import json
import logging
import requests
from typing import List, Dict

class WikiCleanup:
    def __init__(self, config_path: str):
        """Initialize the Wiki cleanup tool."""
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f"Bearer {self.config['wiki_api_token']}",
            'Content-Type': 'application/json'
        })
        
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def graphql_query(self, query: str, variables: Dict = None) -> Dict:
        """Execute a GraphQL query."""
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        response = self.session.post(
            f"{self.config['wiki_url']}/graphql",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            self.logger.error(f"GraphQL request failed: {response.status_code}")
            return None
        
        return response.json()
    
    def list_all_pages(self) -> List[Dict]:
        """Get all pages from the wiki."""
        query = """
        query {
            pages {
                list {
                    id
                    path
                    title
                    createdAt
                    updatedAt
                }
            }
        }
        """
        
        result = self.graphql_query(query)
        if result and result.get('data', {}).get('pages', {}).get('list'):
            return result['data']['pages']['list']
        return []
    
    def find_block_pages(self, all_pages: List[Dict]) -> List[Dict]:
        """Find pages that look like block documentation."""
        block_pages = []
        
        for page in all_pages:
            path = page.get('path', '')
            title = page.get('title', '')
            
            # Check if it's in /blocks/ path or has block-like characteristics
            if (path.startswith('blocks/') or 
                path.startswith('/blocks/') or
                'block' in title.lower() or
                any(cat in title.lower() for cat in ['audio', 'control', 'math', 'logic', 'visual'])):
                block_pages.append(page)
        
        return block_pages
    
    def delete_page(self, page_id: int, title: str) -> bool:
        """Delete a page by ID."""
        mutation = """
        mutation DeletePage($id: Int!) {
            pages {
                delete(id: $id) {
                    responseResult {
                        succeeded
                        errorCode
                        message
                    }
                }
            }
        }
        """
        
        result = self.graphql_query(mutation, {'id': page_id})
        
        if result and result.get('data', {}).get('pages', {}).get('delete', {}).get('responseResult', {}).get('succeeded'):
            self.logger.info(f"✓ Deleted: {title} (ID: {page_id})")
            return True
        else:
            error_msg = result.get('data', {}).get('pages', {}).get('delete', {}).get('responseResult', {}).get('message', 'Unknown error')
            self.logger.error(f"✗ Failed to delete {title}: {error_msg}")
            return False
    
    def cleanup_block_pages(self, dry_run: bool = False, confirm: bool = False):
        """Clean up block pages."""
        self.logger.info("Scanning for pages to clean up...")
        
        all_pages = self.list_all_pages()
        self.logger.info(f"Found {len(all_pages)} total pages")
        
        block_pages = self.find_block_pages(all_pages)
        self.logger.info(f"Found {len(block_pages)} potential block pages")
        
        if not block_pages:
            self.logger.info("No block pages found to clean up")
            return
        
        # Show what will be deleted
        print("\nPages that will be deleted:")
        for page in block_pages:
            print(f"  - {page['title']} ({page['path']}) [ID: {page['id']}]")
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Would delete {len(block_pages)} pages")
            return
        
        if not confirm:
            response = input(f"\nReally delete {len(block_pages)} pages? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                self.logger.info("Cleanup cancelled")
                return
        
        # Delete pages
        deleted = 0
        failed = 0
        
        for page in block_pages:
            if self.delete_page(page['id'], page['title']):
                deleted += 1
            else:
                failed += 1
        
        self.logger.info(f"Cleanup complete: {deleted} deleted, {failed} failed")
    
    def cleanup_specific_paths(self, paths: List[str], dry_run: bool = False):
        """Clean up pages with specific path patterns."""
        all_pages = self.list_all_pages()
        
        pages_to_delete = []
        for page in all_pages:
            for pattern in paths:
                if pattern in page['path']:
                    pages_to_delete.append(page)
                    break
        
        self.logger.info(f"Found {len(pages_to_delete)} pages matching patterns: {paths}")
        
        if dry_run:
            for page in pages_to_delete:
                print(f"[DRY RUN] Would delete: {page['title']} ({page['path']})")
            return
        
        # Delete them
        for page in pages_to_delete:
            self.delete_page(page['id'], page['title'])

def main():
    parser = argparse.ArgumentParser(description='Clean up Wiki.js block pages')
    parser.add_argument('--config', '-c', default='wiki-config.json', 
                       help='Configuration file path')
    parser.add_argument('--dry-run', '-d', action='store_true', 
                       help='Show what would be deleted without deleting')
    parser.add_argument('--confirm', '-y', action='store_true', 
                       help='Skip confirmation prompt')
    parser.add_argument('--blocks-only', '-b', action='store_true', 
                       help='Only delete pages under /blocks/ path')
    parser.add_argument('--paths', nargs='+', 
                       help='Specific path patterns to delete')
    
    args = parser.parse_args()
    
    cleanup = WikiCleanup(args.config)
    
    if args.paths:
        cleanup.cleanup_specific_paths(args.paths, dry_run=args.dry_run)
    elif args.blocks_only:
        cleanup.cleanup_specific_paths(['/blocks/', 'blocks/'], dry_run=args.dry_run)
    else:
        cleanup.cleanup_block_pages(dry_run=args.dry_run, confirm=args.confirm)

if __name__ == '__main__':
    main()