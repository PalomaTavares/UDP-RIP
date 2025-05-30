import time
import threading
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class Router:
    def __init__(self, local_ip):
        self.local_ip = local_ip
        self.neighbors = {}  # {ip: weight}
        self.lock = threading.Lock()  # Add this line for thread safety

    
    #add vizinho com peso
    def add_neighbor(self, neighbor_ip, weight):
        if neighbor_ip == self.local_ip:
            logger.error("Cannot add self as neighbor")
            return False
        
        if not neighbor_ip.startswith("127.0.1."):
            logger.error("Invalid IP address (must be in 127.0.1.0/24 range)")
            return False
        
        
        try:
            weight = float(weight)
            if weight <= 0:
                logger.error("Weight must be positive")
                return False
                
            with self.lock:  # Use the lock for thread-safe operations
                self.neighbors[neighbor_ip] = weight
                
            logger.info(f"Added neighbor {neighbor_ip} with weight {weight}")
            return True
            
        except ValueError:
            logger.error("Invalid weight (must be a number)")
            return False
    
    def remove_neighbor(self, neighbor_ip):
        try:
            with self.lock:
                if neighbor_ip in self.neighbors:
                    del self.neighbors[neighbor_ip]
                    del self.last_update[neighbor_ip]
                    
                    # Remove rotas que usam este vizinho como next_hop
                    to_remove = []
                    for dest, (next_hop, cost) in self.routing_table.items():
                        if next_hop == neighbor_ip:
                            to_remove.append(dest)
                    
                    for dest in to_remove:
                        del self.routing_table[dest]
                    
                    logger.info(f"Vizinho {neighbor_ip} removido")
                    self.recalculate_routes()
                    return True
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao remover vizinho {neighbor_ip}: {e}")
            return False
    
    #recebeu ping ou pong
    def update_neighbor_timestamp(self, neighbor_ip):
            with self.lock:
                if neighbor_ip in self.neighbors:
                    self.last_update[neighbor_ip] = time.time()
                    logger.debug(f"Timestamp atualizado para vizinho {neighbor_ip}")
                    return True
            return False

    #Retorna cópia da tabela de vizinhos
    def get_neighbors(self):
        with self.lock:
            return self.neighbors.copy()
    
    #Retorna cópia da tabela de roteamento
    def get_routing_table(self):
        with self.lock:
            return self.routing_table.copy()
    
    #Retorna próximo salto para destino
    def get_next_hop(self, destination):
        with self.lock:
            if destination in self.routing_table:
                return self.routing_table[destination][0]
            return None
        
    #Processa atualização de rotas de vizinho (Distance Vector)
    def process_route_update(self, sender_ip, routes):
        try:
            with self.lock:
                # Atualiza timestamp do vizinho
                if sender_ip in self.neighbors:
                    self.last_update[sender_ip] = time.time()
                
                # Aplica algoritmo Distance Vector
                updated = False
                sender_weight = self.neighbors.get(sender_ip, float('inf'))
                
                for dest, remote_cost in routes.items():
                    if dest == self.local_ip:
                        continue  # Ignora rotas para si mesmo
                    
                    # Calcula novo custo via este vizinho
                    new_cost = sender_weight + remote_cost
                    
                    # Verifica se é melhor rota
                    if (dest not in self.routing_table or 
                        new_cost < self.routing_table[dest][1]):
                        
                        self.routing_table[dest] = (sender_ip, new_cost)
                        updated = True
                        logger.debug(f"Rota atualizada: {dest} via {sender_ip} (custo {new_cost})")
                
                if updated:
                    self.recalculate_routes()
                    
        except Exception as e:
            logger.error(f"Erro ao processar atualização de {sender_ip}: {e}")
    
    #Traça rota para destino
    def trace_route(self, destination):
        path = [self.local_ip]
        current = self.local_ip
        visited = set()
        max_hops = 10
        
        try:
            for _ in range(max_hops):
                if current == destination:
                    return path
                
                if current in visited:
                    logger.warning(f"Loop detectado no trace para {destination}")
                    break
                
                visited.add(current)
                next_hop = self.get_next_hop(destination)
                
                if not next_hop:
                    logger.warning(f"Nenhuma rota encontrada para {destination}")
                    break
                
                path.append(next_hop)
                current = next_hop
            
            return path if current == destination else None
            
        except Exception as e:
            logger.error(f"Erro no trace route para {destination}: {e}")
            return None
    
    # Recalcula tabela de roteamento (Dijkstra simplificado)
    def recalculate_routes(self):
        try:
            # Implementação básica - pode ser melhorada com Dijkstra completo
            # Por agora, mantém lógica Distance Vector simples
            pass
            
        except Exception as e:
            logger.error(f"Erro ao recalcular rotas: {e}")
    
    #Remove vizinhos que não respondem há muito tempo
    def cleanup_expired_neighbors(self):
        try:
            current_time = time.time()
            expired = []
            
            with self.lock:
                for neighbor_ip, last_seen in self.last_update.items():
                    if current_time - last_seen > self.NEIGHBOR_TIMEOUT:
                        expired.append(neighbor_ip)
            
            for neighbor_ip in expired:
                logger.warning(f"Vizinho {neighbor_ip} expirado (sem resposta)")
                self.remove_neighbor(neighbor_ip)
                
        except Exception as e:
            logger.error(f"Erro na limpeza de vizinhos: {e}")
           
    #Inicia timer periódico para limpeza
    def start_cleanup_timer(self):
        def cleanup_loop():
            while True:
                time.sleep(self.UPDATE_INTERVAL)
                self.cleanup_expired_neighbors()
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
    
    #Retorna estatísticas do roteador"""
    def get_stats(self):
        with self.lock:
            return {
                'local_ip': self.local_ip,
                'neighbors_count': len(self.neighbors),
                'routes_count': len(self.routing_table),
                'neighbors': list(self.neighbors.keys()),
                'destinations': list(self.routing_table.keys())
            }