
import cleaner
import difflib
import sys
import os

def main():
    original_file = 'pg4300-images.html'
    golden_diff_file = 'pg4300-images.golden.diff'
    
    if not os.path.exists(original_file):
        print(f"Error: {original_file} not found.")
        sys.exit(1)
        
    with open(original_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Normalize original lines to LF for consistent diffing
    original_lines = original_content.replace('\r\n', '\n').splitlines(keepends=True)
    
    print("Running cleaner...")
    cleaned_content = cleaner.clean_text(original_content)
    cleaned_lines = cleaned_content.splitlines(keepends=True)
    
    # Generate the unified diff
    print("Generating diff...")
    diff = difflib.unified_diff(
        original_lines, 
        cleaned_lines, 
        fromfile=original_file, 
        tofile='pg4300-images-cleaned.html',
        lineterm='\n'
    )
    actual_diff = "".join(diff)
    
    with open(golden_diff_file, 'w', encoding='utf-8') as f:
        f.write(actual_diff)
    
    print(f"Successfully updated {golden_diff_file} ({len(actual_diff)} characters).")

if __name__ == '__main__':
    main()
