#!/usr/bin/env python3

import argparse
import os
import json
import pathlib
import shutil
import csv

# Construct the argument parser
parser = argparse.ArgumentParser(description='Convert the block .json files in the NewPatch repository to .rst documentation.')
parser.add_argument('--path', '-p', help='The path to the blocks folder (NewPatch/Assets/Blocks)', default='../NewPatch/Assets/Blocks')
parser.add_argument('--clean', '-c', help='Removes all the files generated by this script', action='store_true', default=False)
parser.add_argument('--verbose', '-v', help='Print info to the terminal while running.', action='store_true', default=False)

# Parse the command line args
args = parser.parse_args()

blocksFolder = args.path
verbose = args.verbose

if verbose:
    print(f'Checking if the given blocks folder {blocksFolder} exists')

# Check if the given path exists
if not os.path.exists(blocksFolder):
    print(f'Error: the given path to the Blocks folder ({blocksFolder}) could not be found. \n\nPlease check if the documentation and NewPatch repositories reside in the same folder. Alternatively, supply the correct path using the --path PATH command line option.')

if verbose:
    print('Cleaning the Blocks folder')

for root, dirs, files in os.walk('source/Blocks'):
    if root != 'source/Blocks':
        for f in files:
            path = os.path.join(root, f)

            if verbose:
                print(f'Removing {path}')

            os.remove(path)

for root, dirs, files in os.walk('source/Blocks'):
    for f in files:
        path = os.path.join(root, f)

        if verbose:
            print(f'Removing {path}')

        os.remove(path)

    if root != 'source/Blocks':
        if verbose:
            print(f'Removing directory {root}')

        shutil.rmtree(root)

# Reads and parses the given file from JSON into a dictionary
def readAndParseBlockJson(path):
    with open(path, 'r') as f:
        text = f.read()
        block = json.loads(text)
        return block

blocks = []

if verbose:
    print(f'Reading and parsing block files')

for root, dirs, files in os.walk(blocksFolder):
    for file in files:

        # We're only interested in .json files in the subfolders of the blocks folder.
        if root == blocksFolder:
            continue

        if file.endswith('.json'):
            path = os.path.join(root, file)

            try:
                if verbose:
                    print(f'Reading and parsing {path}')

                block = readAndParseBlockJson(path)
                blocks.append(block)
            except Exception as e:
                print(f'Error while reading and parsing file {path}.')
                print(e)

# Sort blocks by menuPath
blocks = sorted(blocks, key=lambda x: x['menuPath'])




# Takes a block description dictionary and outputs a string with
# the generated .rst documentation.
def generateRstDocumentationForBlock(block):
    result = ''

    # Title
    result += block['name'] + '\n'
    result += ''.join(['=' for c in block['name']]) + '\n\n'
    result += f'.. _{block["name"]}:\n\n'

    # Description
    result += '**Description**\n\n'
    result += block['description'] + '\n\n'

    if 'longDescription' in block:
        result += block['longDescription'] + '\n\n'

    # Inputs
    result += '**Inputs, output and other parts**\n\n'
    
    for part in block['parts']:
        typeString = f' ({part["type"]})' if part['type'] != "" else ""
        result += f'*{part["name"]}*{typeString} {part["description"]}\n\n'

    relatedBlocks = block['relatedBlocks']
        
    if len(relatedBlocks) > 0:
        result += '**See also:**\n\n'

        relatedBlockNames = [b['name'] for b in relatedBlocks]
        relatedBlockLinks = [f':ref:`{n} <{n}>`' for n in relatedBlockNames]

        result += ', '.join(relatedBlockLinks) + "\n\n"

    return result

# Utility function that gets a block by name, e.g. 's_mul'. Used
# for debugging.
def getBlockByName(blocks, name):
    return [b for b in blocks if b['name'] == name][0]

if verbose:
    print(f'Generating documentation')

for block in blocks:
    if verbose:
        print(f'Generating documentation for {block["name"]}')

    if block['includeInWebDocumentation']:
        rst = generateRstDocumentationForBlock(block)

        dir = os.path.join('source/Blocks/', block['menuPath'])

        pathlib.Path(dir).mkdir(parents=True, exist_ok=True)

        path = os.path.join(dir, block['name'] + '_generated.rst')

        with open(path, 'w') as f:
            f.write(rst)

if verbose:
    print(f'Reading Blocks.rst template')

# Read the Blocks.rst template file
blocksTocTreeTemplate = ''

with open('Blocks_template.rst', 'r') as f:
    blocksTocTreeTemplate = f.read()

if verbose:
    print(f'Generating toc tree')

# Generate the blocks toctree item string
blocksTocTreeItems = ''

for block in blocks:
    blocksTocTreeItems += f'   Blocks/{block["menuPath"]}/{block["name"]}\n'

# Replace the field in the template with the generated items
blocksTocTreeFile = blocksTocTreeTemplate.replace('{blocks-toctree-items}', blocksTocTreeItems)

if verbose:
    print(f'Writing Blocks.rst')

# Write the Blocks.rst file
with open('source/Blocks.rst', 'w') as f:
    f.write(blocksTocTreeFile)

if verbose:
    print(f'Reading subsection toc file template')

subfolderTocFileTemplate = ''

with open('blocks_subsection_template.rst', 'r') as f:
    subfolderTocFileTemplate = f.read()

# Make sure the blocks subdirs all have toctree files
for root, dirs, files in os.walk('source/Blocks'):
    p = pathlib.Path(root)

    pathToTocFile = pathlib.Path.joinpath(p.parent, p.name + '.rst')
    tocFileText = subfolderTocFileTemplate.replace('{title}', p.name.capitalize()).replace('{folder}', p.name)
    
    if verbose:
        print(f'Writing {pathToTocFile}')

    with open(pathToTocFile, 'w') as f:
        f.write(tocFileText)

def generateCsvRowForBlock(block):
    row = [
        block['name'], 
        block['description'], 
        block.get('longDescription', ''),  
        block['menuPath']  # Adding the category/menuPath information

    ]
    
    # Assuming that the block['parts'] is a list and 'name', 'type', and 'description' are always present.
    parts_string = '; '.join([f'{part["name"]} ({part["type"]}) {part["description"]}' for part in block['parts']])
    row.append(parts_string)

    # Adding related blocks (joined by ", ")
    relatedBlocks = block.get('relatedBlocks', [])
    relatedBlockNames = [b['name'] for b in relatedBlocks]
    row.append(", ".join(relatedBlockNames))

    return row

# Now, let's also generate the CSV data
output_filename = 'blocks_data.csv'

with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    
    # Writing headers first

    csvwriter.writerow(['Name', 'Description', 'Long Description', 'menuPath', 'Parts', 'Related Blocks'])

    
    for block in blocks:
        if block['includeInWebDocumentation']:
            csv_row = generateCsvRowForBlock(block)
            csvwriter.writerow(csv_row)

if verbose:
    print(f"Data written to {output_filename}")



if verbose:
    print(f'Done')
