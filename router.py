import time
import threading
import logging
from collections import defaultdict

from network import NetworkManager

logger = logging.getLogger(__name__)

PERIOD_TOLERANCE = 4

class Router(NetworkManager):
    def __init__(self, local_ip, period):
        
        super().__init__(local_ip)
        
        self.period = period

        self.incoming_neighbors = []
        
        # {ip: weight}
        self.neighbors = {}

        # {ip: num_updates since last neighbor update}
        self.last_update = {}

        # {dest: (next_hop, cost)}
        self.routing_table = defaultdict(lambda: (None, float('inf')))
        
        # Add this line for thread safety
        self.lock = threading.Lock()

    def send_update_messages(self):
        while True:
            time.sleep(self.period)
            
            with self.lock:
                routing_table = self.routing_table.copy()
            
            for neighbor_ip in self.incoming_neighbors:
                message = self.message_handler.create_update_message(self.local_ip, neighbor_ip, routing_table)
                self.send_message(neighbor_ip, message)

    def update_last_update(self):
        with self.lock:
            for neighbor_ip, last_update in self.last_update.items():
                self.last_update[neighbor_ip] += last_update + 1

                if last_update + 1 >= PERIOD_TOLERANCE * self.period:
                    del self.last_update[neighbor_ip]
                    del self.neighbors[neighbor_ip]

                for dst, (hop_id, _) in self.routing_table.items():
                    if hop_id == neighbor_ip:
                        del self.routing_table[dst]
    
    def start_server(self):
        super().start_server()
        threading.Thread(target=self.send_update_messages, daemon=True).start()

    def handle_data_message(self, message):
        if message.get("destination") == self.local_ip:
            print(message.get("payload"))

        else:
            next_hop = self.routing_table[message.get("destination")][0]
            self.send_message(next_hop, message)

    def handle_trace(self, message):
        source = message.get("source")
        destination = message.get("destination")
        routers = message.get("routers")
        routers.append(self.local_ip)

        if self.local_ip == destination:
            next_hop = self.routing_table[source][0]
            message =self.message_handler.create_data_message(self.local_ip, source, routers)
        
        else:
            next_hop = self.routing_table[destination][0]
            self.message_handler.create_trace_message(self.local_ip, next_hop, routers)
        
        self.send_message(next_hop, message)
        

    def handle_update(self, message):
        logger.debug("Received msg:", message)
        source = message.get("source")
        link_weight = self.neighbors[source]
        distances = message.get("distances", {})

        try:
            with self.lock:
                # udate last_update counter
                self.last_update[source] = 0
                
                # insert neighbor link
                if link_weight < self.routing_table[source][1]:
                    self.routing_table[source] = (source, link_weight)

                # insert dst_link
                for dst, (next_hop, dst_weight) in distances.items():
                    weight = link_weight + dst_weight
                    previous_weight = self.routing_table[dst][1]
                        
                    if weight < previous_weight:
                        self.routing_table[dst] = (source, weight)
        
        except Exception as e:
            logger.error(f"Erro ao atualizar rotas: {e}")

        logger.debug(self.routing_table)

    def handle_disconnect(self, neighbor_ip):
    # TODO: check if we should remove neighbors already or wait for the tolerance to end
        with self.lock:
            for dest, (next_hop, _) in self.routing_table.items():
                if next_hop == neighbor_ip:       
                    del self.routing_table[dest]

    def handle_message(self, message):
        if message.get("type") == "data":
            self.handle_data_message(message)
        
        elif message.get("type") == "connection":
            ip = message.get("source")
            weight = message.get("weight")
            with self.lock:
                self.neighbors[ip] = weight

        elif message.get("type") == "disconnection":
            ip = message.get("sender")
            
            if ip in self.incoming_neighbors:
                with self.lock:
                    del self.neighbors[ip]
                
                self.handle_disconnect(ip)

        elif message.get("type") == "update":
            # TODO: implement Split Horizon prevention
            self.handle_update(message)

        elif message.get("type") == "trace":
            self.handle_trace(message)

    
    # TODO: check how should we deal with connecting to inexistent neighbors yet
    # add vizinho com peso
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
                
            message = self.message_handler.create_conection_message(self.local_ip, neighbor_ip, weight)
            if not self.send_message(neighbor_ip, message):
                return False

            with self.lock:  # Use the lock for thread-safe operations
                self.incoming_neighbors.append(neighbor_ip)
                
            logger.info(f"Added neighbor {neighbor_ip} with weight {weight}")
            return True
            
        except ValueError:
            logger.error("Invalid weight (must be a number)")
            return False
    
    #TODO: check if we should warn neighbors about disconnections already or wait tolerance
    def remove_neighbor(self, neighbor_ip):
        try:
            with self.lock:
                if neighbor_ip in self.neighbors:
                    self.incoming_neighbors.remove(neighbor_ip)
                    
                    logger.info(f"Vizinho {neighbor_ip} removido")
                    
                    return True
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao remover vizinho {neighbor_ip}: {e}")
            return False
        
    def trace_route(self, destination):
        routers = [self.local_ip]
        message = self.message_handler.create_trace_message(self.local_ip, destination, routers)

        next_hop = self.get_next_hop(destination)
        self.send_message(next_hop, message)

    #Retorna cópia da tabela de vizinhos
    def get_neighbors(self):
        with self.lock:
            return self.neighbors.copy()
    
    #Retorna próximo salto para destino
    def get_next_hop(self, destination):
        with self.lock:
            return self.routing_table[destination][0]
