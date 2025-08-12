#!/usr/bin/env python3
"""
Debug image upload to Wiki.js
"""

import json
import requests
import os

def debug_image_upload():
    # Load config
    with open('wiki-config.json', 'r') as f:
        config = json.load(f)
    
    wiki_url = config['wiki_url']
    api_token = config['wiki_api_token']
    
    # Test if we can access assets
    headers = {
        'Authorization': f"Bearer {api_token}",
        'Content-Type': 'application/json'
    }
    
    print("=== Testing Wiki.js Assets API ===")
    
    # Query existing assets
    query = {
        'query': '''
        query {
            assets {
                list {
                    id
                    filename
                    ext
                    kind
                    mime
                    fileSize
                }
            }
        }
        '''
    }
    
    try:
        response = requests.post(
            f"{wiki_url}/graphql",
            json=query,
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print("GraphQL Errors:", data['errors'])
            else:
                assets = data.get('data', {}).get('assets', {}).get('list', [])
                print(f"Found {len(assets)} existing assets:")
                for asset in assets[:5]:  # Show first 5
                    print(f"  - {asset['filename']} ({asset['kind']}, {asset['fileSize']} bytes)")
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

    # Test simple image upload
    print("\n=== Testing simple image upload ===")
    
    # Find a test image
    thumbnails_path = config.get('thumbnails_path', '')
    test_image = None
    
    for filename in os.listdir(thumbnails_path):
        if filename.endswith('.png'):
            test_image = os.path.join(thumbnails_path, filename)
            break
    
    if test_image:
        print(f"Testing upload of: {test_image}")
        
        # Try different upload methods
        print("\n--- Method 1: Direct file upload ---")
        try:
            with open(test_image, 'rb') as f:
                files = {
                    'file': (os.path.basename(test_image), f, 'image/png')
                }
                
                upload_headers = {'Authorization': f"Bearer {api_token}"}
                
                response = requests.post(
                    f"{wiki_url}/u",  # Common upload endpoint
                    files=files,
                    headers=upload_headers,
                    timeout=30
                )
                
                print(f"Upload status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Upload failed: {e}")
            
        print("\n--- Method 2: Check Wiki.js upload endpoints ---")
        # Check what endpoints are available
        try:
            response = requests.get(f"{wiki_url}/", timeout=10)
            print(f"Main page status: {response.status_code}")
            
            # Try to find upload info in the page
            if 'upload' in response.text.lower():
                print("Upload functionality detected in main page")
            
        except Exception as e:
            print(f"Main page check failed: {e}")
            
    else:
        print("No test images found")

if __name__ == '__main__':
    debug_image_upload()