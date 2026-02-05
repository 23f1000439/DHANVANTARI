import os

def generate_context(root_dir, output_file, extensions=None, ignore_dirs=None):
    if extensions is None:
        extensions = ['.py', '.js', '.html', '.css', '.sql', '.md']
    if ignore_dirs is None:
        ignore_dirs = {'.git', '__pycache__', 'venv', 'node_modules', '.gemini', '.idea', '.vscode', '.venv_libs'}

    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# DHANVANTARI Codebase Context\n\n")
        
        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                _, ext = os.path.splitext(file)
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, root_dir)
                    
                    # Skip the output file itself if it's in the directory
                    if os.path.abspath(file_path) == os.path.abspath(output_file):
                        continue
                        
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            
                        outfile.write(f"## File: {rel_path}\n\n")
                        outfile.write(f"```{ext[1:]}\n")
                        outfile.write(content)
                        outfile.write(f"\n```\n\n")
                        print(f"Added {rel_path}")
                    except Exception as e:
                        print(f"Error reading {rel_path}: {e}")

if __name__ == "__main__":
    generate_context('.', 'DHANVANTARI_CONTEXT.md')
    print("Context file generated: DHANVANTARI_CONTEXT.md")
