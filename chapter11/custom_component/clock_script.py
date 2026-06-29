import time
from datetime import datetime
import sys

def main():
    # Print a startup message
    print("TimePrinter component started successfully.", flush=True)
    
    try:
        while True:
            # Get the current local time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Print the time. flush=True is critical in Greengrass so the output 
            # goes to the component's log file immediately!
            print(f"Current time: {current_time}", flush=True)
            
            # Wait for 5 seconds
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("TimePrinter component stopping...", flush=True)
        sys.exit(0)

if __name__ == "__main__":
    main()				