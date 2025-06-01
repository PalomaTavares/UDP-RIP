import sys
from network import NetworkManager
from router import Router

#TODO: clear prints

def print_help():
    print("Available commands:")
    print("  add <ip> <weight> - Add a neighbor")
    print("  del <ip>          - Remove a neighbor")
    print("  trace <ip>        - Trace route to destination")
    print("  list              - List current neighbors")
    print("  quit              - Exit the program")

def handle_add(router, args):
    if len(args) != 2:
        print("Usage: add <ip> <weight>")
        return
    ip, weight = args
    if router.add_neighbor(ip, weight):
        print(f"Added neighbor {ip} with weight {weight}")

def handle_del(router, args):
    if len(args) != 1:
        print("Usage: del <ip>")
        return
    ip = args[0]
    if router.remove_neighbor(ip):
        print(f"Removed neighbor {ip}")

def handle_trace(router, args):
    if len(args) != 1:
        print("Usage: trace <ip>")
        return
    ip = args[0]
    path = router.trace_route(ip)
    if path:
        print(f"Trace to {ip}: {', '.join(path)}")
    else:
        print(f"No route found to {ip}")

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
        print(f"{source}Invalid command: {' '.join(cmd)}")
        print_help()
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
        print("Usage: python main.py <address> <period> [startup]")
        sys.exit(1)

    address = sys.argv[1]
    try:
        period = int(sys.argv[2])
    except ValueError:
        print("Error: period must be an integer")
        sys.exit(1)

    router = Router(address, period)
    router.start_server()
    print(f"Router started at {address}")
    print_help()

    # Process startup commands if provided
    if len(sys.argv) > 3:
        process_startup_file(router, sys.argv[3])

    try:
        while True:
            cmd = input(f"{address}> ").strip().split()
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
