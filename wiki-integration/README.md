# Wiki.js Integration for Block Documentation

This folder contains scripts and configuration files for automatically populating a Wiki.js instance with block documentation from the NewPatch project.

## Files

- `wiki-populate.py` - Main script that extracts block data and populates Wiki.js
- `wiki-config.json` - Configuration file (edit this with your settings)
- `wiki-config.json.example` - Template configuration file
- `requirements.txt` - Python dependencies
- `setup.py` - Setup script for easy installation

## Quick Start

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
   python wiki-populate.py --dry-run --verbose
   ```

4. **Run the script:**
   ```bash
   python wiki-populate.py --verbose
   ```

## Configuration

Edit `wiki-config.json` with your settings:

- `wiki_url`: Your Wiki.js instance URL (e.g., "http://194.195.245.119:3000")
- `wiki_api_token`: API token from Wiki.js Admin panel
- `blocks_data_path`: Path to the blocks_data.json file (relative to this folder)
- `thumbnails_path`: Path to block thumbnails folder

## Features

- **Automatic page creation**: Creates Wiki.js pages for each block
- **Category organization**: Groups blocks by categories with index pages
- **Markdown conversion**: Converts RST documentation to Markdown
- **Image handling**: Processes block thumbnails
- **Incremental updates**: Only updates changed content
- **Cross-references**: Links related blocks together

## Usage Examples

```bash
# Test what would be done without making changes
python wiki-populate.py --dry-run

# Run with verbose output
python wiki-populate.py --verbose

# Use custom config file
python wiki-populate.py --config my-config.json

# Combine options
python wiki-populate.py --config prod-config.json --verbose
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

## Integration with Documentation Build

You can integrate this with your existing documentation build process by adding it to your Makefile or build scripts.

Example addition to Makefile:
```makefile
wiki-populate: build
	cd wiki-integration && python wiki-populate.py --verbose

wiki-test:
	cd wiki-integration && python wiki-populate.py --dry-run --verbose
```