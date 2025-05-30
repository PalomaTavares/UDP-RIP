import sys
from network import NetworkManager
from router import Router

def print_help():
    print("Available commands:")
    print("  add <ip> <weight> - Add a neighbor")
    print("  list              - List current neighbors")
    print("  quit              - Exit the program")

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <local_ip>")
        print("Example: python main.py 127.0.1.1")
        sys.exit(1)

    local_ip = sys.argv[1]
    router = Router(local_ip)
    network = NetworkManager(local_ip, 55151)
    network.start_server()

    print(f"Router started at {local_ip}")
    print_help()

    while True:
        try:
            cmd = input(f"{local_ip}> ").strip().split()
            if not cmd:
                continue
                
            if cmd[0] == "add" and len(cmd) == 3:
                ip, weight = cmd[1], cmd[2]
                if router.add_neighbor(ip, weight):
                    print(f"Successfully added {ip}")
                    if network.send_ping(ip):
                        print(f"Neighbor {ip} is responsive")
                    else:
                        print(f"Warning: Could not reach {ip}")
                        
            elif cmd[0] == "list":
                neighbors = router.get_neighbors()
                if neighbors:
                    print("Current neighbors:")
                    for ip, weight in neighbors.items():
                        print(f"  {ip}: weight {weight}")
                else:
                    print("No neighbors configured")
                    
            elif cmd[0] == "quit":
                break
                
            else:
                print("Invalid command")
                print_help()
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    network.stop_server()
    print("Router stopped")

if __name__ == "__main__":
    main()