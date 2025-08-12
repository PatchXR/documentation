#!/usr/bin/env python3
"""
Setup script for Wiki.js integration

This script helps set up the wiki integration by:
1. Installing Python dependencies
2. Checking Wiki.js connectivity
3. Validating configuration
4. Running initial tests
"""

import os
import sys
import json
import subprocess
import requests
from pathlib import Path

def install_dependencies():
    """Install required Python packages."""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def check_config():
    """Check if configuration file exists and is valid."""
    config_file = 'wiki-config.json'
    
    if not os.path.exists(config_file):
        print(f"✗ Configuration file not found: {config_file}")
        print("Please copy wiki-config.json.example to wiki-config.json and edit it")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        required_fields = ['wiki_url', 'wiki_api_token', 'blocks_data_path']
        missing_fields = [field for field in required_fields if not config.get(field)]
        
        if missing_fields:
            print(f"✗ Missing required configuration fields: {', '.join(missing_fields)}")
            return False
        
        if config['wiki_api_token'] == 'PUT_YOUR_API_TOKEN_HERE':
            print("✗ Please set your Wiki.js API token in wiki-config.json")
            return False
        
        print("✓ Configuration file is valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON in configuration file: {e}")
        return False

def check_wiki_connectivity(config):
    """Test connection to Wiki.js instance."""
    print("Testing Wiki.js connectivity...")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{config['wiki_url']}/healthz", timeout=10)
        if response.status_code == 200:
            print("✓ Wiki.js instance is reachable")
        else:
            print(f"⚠ Wiki.js returned status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot reach Wiki.js instance: {e}")
        return False
    
    # Test GraphQL API with authentication
    try:
        headers = {
            'Authorization': f"Bearer {config['wiki_api_token']}",
            'Content-Type': 'application/json'
        }
        
        # Simple GraphQL query to test auth
        query = {
            'query': '''
            query {
                pages {
                    list(limit: 1) {
                        id
                        path
                    }
                }
            }
            '''
        }
        
        response = requests.post(
            f"{config['wiki_url']}/graphql",
            json=query,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' not in data:
                pages = data.get('data', {}).get('pages', {}).get('list', [])
                print(f"✓ Wiki.js API authentication successful (found {len(pages)} pages)")
                return True
            else:
                print(f"✗ GraphQL API error: {data['errors']}")
                return False
        else:
            print(f"✗ GraphQL API request failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ GraphQL API test failed: {e}")
        return False

def check_blocks_data(config):
    """Check if blocks data file exists and is readable."""
    blocks_data_path = config['blocks_data_path']
    
    # Handle relative paths
    if not os.path.isabs(blocks_data_path):
        blocks_data_path = os.path.join(os.path.dirname(__file__), blocks_data_path)
    
    if not os.path.exists(blocks_data_path):
        print(f"✗ Blocks data file not found: {blocks_data_path}")
        print("Please run the documentation build script first to generate blocks_data.json")
        return False
    
    try:
        with open(blocks_data_path, 'r') as f:
            data = json.load(f)
        
        if 'blocks' not in data:
            print("✗ Invalid blocks data format: missing 'blocks' key")
            return False
        
        blocks = data['blocks']
        web_blocks = [b for b in blocks if b.get('includeInWebDocumentation', False)]
        
        print(f"✓ Found {len(blocks)} total blocks, {len(web_blocks)} for web documentation")
        return True
        
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON in blocks data file: {e}")
        return False
    except Exception as e:
        print(f"✗ Error reading blocks data: {e}")
        return False

def run_dry_run():
    """Run the wiki population script in dry-run mode."""
    print("Running dry-run test...")
    try:
        result = subprocess.run([
            sys.executable, 'wiki-populate.py', '--dry-run', '--verbose'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✓ Dry-run completed successfully")
            print("The script is ready to populate your wiki!")
            return True
        else:
            print(f"✗ Dry-run failed with exit code: {result.returncode}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Dry-run timed out")
        return False
    except Exception as e:
        print(f"✗ Error running dry-run: {e}")
        return False

def main():
    """Main setup function."""
    print("=== Wiki.js Integration Setup ===\n")
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    success = True
    
    # Step 1: Install dependencies
    if not install_dependencies():
        success = False
    print()
    
    # Step 2: Check configuration
    if not check_config():
        success = False
        print("\nSetup incomplete. Please fix configuration issues and run setup again.")
        return
    
    # Load config for subsequent tests
    with open('wiki-config.json', 'r') as f:
        config = json.load(f)
    print()
    
    # Step 3: Check Wiki.js connectivity
    if not check_wiki_connectivity(config):
        success = False
    print()
    
    # Step 4: Check blocks data
    if not check_blocks_data(config):
        success = False
    print()
    
    # Step 5: Run dry-run test
    if success and not run_dry_run():
        success = False
    print()
    
    # Summary
    if success:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python wiki-populate.py --verbose")
        print("2. Check your Wiki.js instance for the populated content")
        print("3. Optionally add to your documentation build process")
    else:
        print("❌ Setup completed with errors. Please fix the issues above and run setup again.")
        sys.exit(1)

if __name__ == '__main__':
    main()