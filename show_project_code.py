import os

def print_file_contents(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.yaml', '.yml')):
                file_path = os.path.join(root, file)
                print(f"\n\n{'='*80}\nFile: {file_path}\n{'='*80}\n")
                try:
                    with open(file_path, 'r') as f:
                        print(f.read())
                except Exception as e:
                    print(f"Error reading file {file_path}: {str(e)}")

if __name__ == "__main__":
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print_file_contents(script_dir)
