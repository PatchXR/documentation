# Wiki.js Integration for Block Documentation

This folder contains scripts and configuration files for automatically populating a Wiki.js instance with block documentation from the NewPatch project.

## Files

- `wiki-populate-simple.py` - Main script that populates Wiki.js with block documentation
- `wiki-cleanup.py` - Utility script to clean up existing block pages  
- `wiki-config.json` - Configuration file (edit this with your settings)
- `wiki-config.json.example` - Template configuration file
- `requirements.txt` - Python dependencies

## Quick Start

### Full Pipeline Update (Recommended)

To update the entire pipeline from NewPatch → Documentation → Portal → Wiki, run from the documentation root:

```bash
cd /path/to/documentation
python update-all.py
```

This script will:
1. Extract blocks from NewPatch to Documentation  
2. Copy files to Portal (blocks_data.json and thumbnails)
3. Ask if you want to update the Wiki
4. Remind you to commit and deploy the portal

### Manual Wiki Update

If you only want to update the Wiki.js instance:

1. **Install dependencies:**
   ```bash
   cd wiki-integration
   pip install -r requirements.txt
   ```

2. **Configure the script:**
   - Edit `wiki-config.json` with your Wiki.js URL and API token
   - Get API token from Wiki.js Admin > API Access

3. **Test the script (dry run):**
   ```bash
   python wiki-populate-simple.py --dry-run --verbose
   ```

4. **Run the script with cleanup:**
   ```bash
   python wiki-populate-simple.py --cleanup --verbose
   ```

## Configuration

Edit `wiki-config.json` with your settings:

- `wiki_url`: Your Wiki.js instance URL (e.g., "https://wiki.patchxr.io")
- `wiki_api_token`: API token from Wiki.js Admin panel
- `blocks_data_path`: Path to the blocks_data.json file (relative to this folder)
- `docs_base_url`: Base URL for thumbnail images (e.g., "https://portal.patchxr.io")
- `thumbnails_path`: Local path to block thumbnails folder
- `locale`: Wiki locale (default: "en")
- `create_category_pages`: Whether to create category index pages (default: true)

## Features

- **Automatic page creation**: Creates Wiki.js pages for each block with proper organization
- **Category organization**: Groups blocks by categories matching the portal structure
- **Portal thumbnails**: References thumbnails from portal.patchxr.io instead of uploading
- **Cleanup functionality**: Can clean up existing pages before creating new ones
- **Dry run testing**: Test changes before applying them
- **Category index pages**: Creates category overview pages with block listings
- **Cross-references**: Links related blocks together

## Usage Examples

### wiki-populate-simple.py

```bash
# Test what would be done without making changes
python wiki-populate-simple.py --dry-run --verbose

# Clean up existing pages and create new ones
python wiki-populate-simple.py --cleanup --verbose

# Just test cleanup without changes
python wiki-populate-simple.py --cleanup --dry-run

# Limit to first 10 blocks for testing
python wiki-populate-simple.py --limit 10 --verbose

# Use custom config file
python wiki-populate-simple.py --config my-config.json --verbose
```

### wiki-cleanup.py

```bash
# Test cleanup without making changes
python wiki-cleanup.py --dry-run

# Clean up all block pages with confirmation
python wiki-cleanup.py --confirm

# Clean up only blocks (not category pages)
python wiki-cleanup.py --blocks-only --confirm
```

## Wiki.js API Token

To get an API token:

1. Login to your Wiki.js admin panel
2. Go to Administration > API Access
3. Create a new API key
4. Copy the token to your `wiki-config.json` file

## Troubleshooting

- Check `wiki-populate.log` for detailed error messages
- Ensure your Wiki.js instance is accessible from your machine
- Verify API token has proper permissions
- Use `--dry-run` to test before making changes

## Complete Update Workflow

The complete update workflow when blocks change in NewPatch:

1. **Run the complete pipeline:**
   ```bash
   cd documentation
   python update-all.py
   ```
   
   This will:
   - Extract blocks from NewPatch (`build_rst_from_blocks_json.py`)
   - Copy `blocks_data.json` and thumbnails to Portal
   - Ask if you want to update Wiki.js
   - Remind you to deploy the portal

2. **Deploy portal changes:**
   - Commit portal changes to git
   - Deploy portal to portal.patchxr.io
   
3. **Verify wiki:**
   - Check wiki.patchxr.io for updated documentation
   - Verify thumbnails display correctly
   - Check category organization matches portal

## Integration with Build Process

Example Makefile addition:
```makefile
# Complete update pipeline
update-all:
	python update-all.py

# Wiki only
wiki-populate: 
	cd wiki-integration && python wiki-populate-simple.py --cleanup --verbose

# Test wiki changes  
wiki-test:
	cd wiki-integration && python wiki-populate-simple.py --dry-run --verbose
```

## Architecture

The complete flow:
```
NewPatch (Unity) → Documentation → Portal → Wiki.js
```

- **NewPatch**: Source Unity project with block definitions
- **Documentation**: Extracts and processes block data, creates RST docs
- **Portal**: Serves thumbnails and block library data  
- **Wiki.js**: Final documentation destination with organized pages