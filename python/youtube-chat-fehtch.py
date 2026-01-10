#!/usr/bin/env python3
import sys
import pytchat
import time

def main():
    if len(sys.argv) < 4:
        print("ERROR:Missing arguments", flush=True)
        sys.exit(1)
    
    video_id = sys.argv[1]
    post_cmd = sys.argv[2]
    del_cmd = sys.argv[3]
    
    try:
        chat = pytchat.create(video_id=video_id)
        print("CONNECTED", flush=True)
        
        while chat.is_alive():
            for c in chat.get().sync_items():
                message = c.message
                author = c.author.name
                
                # Check for post command
                if message.startswith(post_cmd):
                    parts = message.split()
                    if len(parts) >= 2:
                        level_id = parts[1]
                        print(f"LEVEL:{level_id}|{author}", flush=True)
                
                # Check for delete command
                if message.startswith(del_cmd):
                    print(f"DELETE:{author}", flush=True)
            
            time.sleep(1)
    
    except Exception as e:
        print(f"ERROR:{str(e)}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()