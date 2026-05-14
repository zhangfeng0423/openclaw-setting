#!/usr/bin/env python3
import sys
import subprocess
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fetch.py <url> [max_chars] [--stealth]")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # We ignore max_chars and stealth for now because the node script handles it via local Chrome
    script_dir = os.path.dirname(os.path.realpath(__file__))
    js_path = os.path.join(script_dir, 'fetch.js')
    
    # Check if --json is in args
    is_json = '--json' in sys.argv
    
    cmd = ['node', js_path, url]
    if is_json:
        cmd.append('--json')
        
    try:
        # Use the local nvm node
        env = os.environ.copy()
        env['PATH'] = '/Users/zhangfeng/.nvm/versions/node/v22.22.0/bin:' + env.get('PATH', '')
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode != 0:
            print(f"Error fetching URL: {result.stderr}", file=sys.stderr)
            sys.exit(1)
            
        print(result.stdout)
    except Exception as e:
        print(f"Error executing fetch: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
