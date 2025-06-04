import sys
from network import NetworkManager
from router import Router

def handle_add(router, args):
    if len(args) != 2:
        return
    ip, weight = args
    router.add_neighbor(ip, weight)

def handle_del(router, args):
    if len(args) != 1:
        return
    ip = args[0]
    router.remove_neighbor(ip)

def handle_trace(router, args):
    if len(args) != 1:
        return
    ip = args[0]
    path = router.trace_route(ip)

def handle_list(router, args):
    neighbors = router.get_neighbors()
    if neighbors:
        print("Current neighbors:")
        for ip, weight in neighbors.items():
            print(f"  {ip}: weight {weight}")
    else:
        print("No neighbors configured")

def process_command(router, cmd, source=""):
    if not cmd:
        return False  # Continue loop
    command_map = {
        "add": handle_add,
        "del": handle_del,
        "trace": handle_trace,
        "list": handle_list,
        "quit": lambda r, a: "quit"
    }
    action = cmd[0].lower()
    handler = command_map.get(action)
    if handler:
        result = handler(router, cmd[1:])
        return result == "quit"
    else:
        return False

def process_startup_file(router, filepath):
    try:
        with open(filepath, 'r') as f:
            for line in f:
                cmd = line.strip().split()
                if process_command(router, cmd, source="Startup: "):
                    print("Startup requested quit. Ignored.")
    except Exception as e:
        print(f"Failed to process startup file '{filepath}': {e}")

def main():
    if len(sys.argv) < 3:
        sys.exit(1)

    address = sys.argv[1]
    try:
        period = int(sys.argv[2])
    except ValueError:
        print("Error: period must be an integer")
        sys.exit(1)

    router = Router(address, period)
    router.start_server()

    # Process startup commands if provided
    if len(sys.argv) > 3:
        process_startup_file(router, sys.argv[3])

    try:
        while True:
            cmd = input().strip().split()
            if process_command(router, cmd):
                break
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        router.stop_server()
        print("Router stopped")

if __name__ == "__main__":
    main()
