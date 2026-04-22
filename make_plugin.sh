#!/bin/bash

# Define the output name
PLUGIN_NAME="language_clean_plugin.zip"

# Remove old zip if it exists
rm -f "$PLUGIN_NAME"

# Zip necessary files
# -r: recursive (for images folder)
zip -r "$PLUGIN_NAME" \
    __init__.py \
    action.py \
    cleaner.py \
    config.py \
    config_widget.py \
    images/ \
    README.md \
    plugin-import-name-language_clean_plugin.txt

echo "Plugin created: $PLUGIN_NAME"
