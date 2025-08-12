#!/usr/bin/env python3
"""
Test GraphQL API connectivity with detailed debugging
"""

import json
import requests

def test_graphql():
    # Load config
    with open('wiki-config.json', 'r') as f:
        config = json.load(f)
    
    wiki_url = config['wiki_url']
    api_token = config['wiki_api_token']
    
    print(f"Testing GraphQL API at: {wiki_url}/graphql")
    print(f"Using API token: {api_token[:20]}...")
    
    # Test 1: Simple introspection query
    headers = {
        'Authorization': f"Bearer {api_token}",
        'Content-Type': 'application/json'
    }
    
    # Very simple query to test auth
    query = {
        'query': '''
        {
            __type(name: "Query") {
                name
            }
        }
        '''
    }
    
    print("\n=== Test 1: Simple introspection ===")
    try:
        response = requests.post(
            f"{wiki_url}/graphql",
            json=query,
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print("GraphQL Errors:", data['errors'])
            else:
                print("✓ GraphQL API working!")
                
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Test 2: System info query
    query2 = {
        'query': '''
        query {
            system {
                info {
                    version
                }
            }
        }
        '''
    }
    
    print("\n=== Test 2: System info query ===")
    try:
        response = requests.post(
            f"{wiki_url}/graphql",
            json=query2,
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print("GraphQL Errors:", data['errors'])
            else:
                print("✓ System info query successful!")
                version = data.get('data', {}).get('system', {}).get('info', {}).get('version')
                if version:
                    print(f"Wiki.js version: {version}")
                
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Test 3: Pages query
    query3 = {
        'query': '''
        query {
            pages {
                list(orderBy: CREATED, orderByDirection: ASC) {
                    id
                    path
                    title
                }
            }
        }
        '''
    }
    
    print("\n=== Test 3: Pages list query ===")
    try:
        response = requests.post(
            f"{wiki_url}/graphql",
            json=query3,
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print("GraphQL Errors:", data['errors'])
            else:
                print("✓ Pages query successful!")
                pages = data.get('data', {}).get('pages', {}).get('list', [])
                print(f"Found {len(pages)} existing pages")
                
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == '__main__':
    test_graphql()