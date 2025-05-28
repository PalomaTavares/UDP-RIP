import sys
import threading
import time
from network import NetworkManager
from router import Router
from utils import setup_logging, get_local_ip

class RouterCLI:
    def __init__(self, local_ip, port=8080):
        self.local_ip = local_ip
        self.port = port
        self.router = Router(local_ip)
        self.network = NetworkManager(local_ip, port, self.router)
        self.running = True
        
        # Inicia servidor UDP em thread separada
        self.server_thread = threading.Thread(target=self.network.start_server, daemon=True)
        self.server_thread.start()
        
        print(f"Roteador iniciado em {local_ip}:{port}")
        print("Digite 'help' para ver comandos disponíveis")

    def parse_command(self, cmd_line):
        """Parse e executa comandos da CLI"""
        parts = cmd_line.strip().split()
        if not parts:
            return
            
        cmd = parts[0].lower()
        
        try:
            if cmd == "add" and len(parts) == 3:
                ip = parts[1]
                weight = float(parts[2])
                self.cmd_add(ip, weight)
                
            elif cmd == "del" and len(parts) == 2:
                ip = parts[1]
                self.cmd_del(ip)
                
            elif cmd == "trace" and len(parts) == 2:
                ip = parts[1]
                self.cmd_trace(ip)
                
            elif cmd == "list":
                self.cmd_list()
                
            elif cmd == "status":
                self.cmd_status()
                
            elif cmd == "help":
                print_help()
                
            elif cmd == "quit":
                self.running = False
                
            else:
                print(f"Comando inválido: {cmd_line}")
                print("Digite 'help' para ver comandos disponíveis")
                
        except Exception as e:
            print(f"Erro ao executar comando: {e}")
    
    def cmd_add(self, ip, weight):
        """Adiciona vizinho com peso especificado"""
        if not ip.startswith("127.0.1."):
            print(f"Erro: IP deve estar na rede 127.0.1.X")
            return
            
        if weight <= 0:
            print(f"Erro: Peso deve ser positivo")
            return
            
        success = self.router.add_neighbor(ip, weight)
        if success:
            # Teste de conectividade
            if self.network.test_connection(ip, self.port):
                print(f"Vizinho {ip} adicionado com peso {weight}")
            else:
                print(f"Vizinho {ip} adicionado, mas sem resposta (pode estar offline)")
        else:
            print(f"Erro ao adicionar vizinho {ip}")
    
    def cmd_del(self, ip):
        """Remove vizinho da tabela"""
        success = self.router.remove_neighbor(ip)
        if success:
            print(f"Vizinho {ip} removido")
        else:
            print(f"Vizinho {ip} não encontrado")
    
    def cmd_trace(self, ip):
        """Traça rota para destino"""
        route = self.router.trace_route(ip)
        if route:
            print(f"Rota para {ip}: {' -> '.join(route)}")
        else:
            print(f"Nenhuma rota encontrada para {ip}")
    
    def cmd_list(self):
        """Lista vizinhos atuais"""
        neighbors = self.router.get_neighbors()
        if neighbors:
            print("\nVizinhos atuais:")
            for ip, weight in neighbors.items():
                status = "online" if self.network.test_connection(ip, self.port) else "offline"
                print(f"  {ip} - peso: {weight} ({status})")
        else:
            print("Nenhum vizinho configurado")
    
    def cmd_status(self):
        """Mostra status do roteador"""
        print(f"\nStatus do Roteador:")
        print(f"  IP Local: {self.local_ip}:{self.port}")
        print(f"  Vizinhos: {len(self.router.get_neighbors())}")
        print(f"  Servidor: {'Ativo' if self.server_thread.is_alive() else 'Inativo'}")

    def run(self):
        """Loop principal da CLI"""
        try:
            while self.running:
                try:
                    cmd = input(f"{self.local_ip}> ")
                    self.parse_command(cmd)
                except KeyboardInterrupt:
                    print("\nEncerrando...")
                    break
                except EOFError:
                    break
        finally:
            self.network.stop_server()
            print("Roteador encerrado")

def print_help():
    """Exibe comandos disponíveis"""
    print("\nComandos disponíveis:")
    print("  add <ip> <weight>  - Adiciona vizinho com peso")
    print("  del <ip>          - Remove vizinho")
    print("  trace <ip>        - Traça rota para destino")
    print("  list              - Lista vizinhos atuais")
    print("  status            - Mostra status do roteador")
    print("  help              - Exibe esta ajuda")
    print("  quit              - Sair do programa")

def main():
    if len(sys.argv) != 2:
        print("Uso: python main.py <ip_local>")
        print("Exemplo: python main.py 127.0.1.1")
        sys.exit(1)
    
    local_ip = sys.argv[1]
    
    # Valida IP no formato 127.0.1.X
    if not local_ip.startswith("127.0.1."):
        print("Erro: IP deve estar na rede 127.0.1.X")
        sys.exit(1)
    
    # Configura logging
    setup_logging()
    
    try:
        cli = RouterCLI(local_ip)
        cli.run()
    except Exception as e:
        print(f"Erro ao iniciar roteador: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()