import time
import threading
import logging

from network import NetworkManager

logger = logging.getLogger(__name__)

PERIOD_TOLERANCE = 4
INFINITY_THRESHOLD = 100

class Router(NetworkManager):
    def __init__(self, local_ip, period):
        super().__init__(local_ip)
        
        self.period = period
        
        self.incoming_neighbors = {}
        
        # ip: num_updates since last update
        self.last_update = {}
        
        # dest: (next_hop, cost)
        self.routing_table = {}
        
        # For thread safety
        self.lock = threading.Lock()


    def send_update_messages(self):
        with self.lock:
            for neighbor_ip, weight in self.incoming_neighbors.items():
            
                routing_table = self.routing_table.copy()

                routing_table[self.local_ip] = (self.local_ip, weight)

                for dst, (next_hop, _) in self.routing_table.items():
                    if next_hop == neighbor_ip or dst == neighbor_ip:
                        del routing_table[dst]
                
                message = self.message_handler.create_update_message(self.local_ip, neighbor_ip, routing_table)
                self.send_message(neighbor_ip, message)

    def update_last_update(self):
        with self.lock:
            to_remove_neighbors = []

            for neighbor_ip, last_update in self.last_update.items():
                self.last_update[neighbor_ip] += 1

                if last_update + 1 >= PERIOD_TOLERANCE:
                    to_remove_neighbors.append(neighbor_ip)

            for neighbor_ip in to_remove_neighbors:
                del self.last_update[neighbor_ip]

            routes_to_remove = []
            for dst, (next_hop, _) in self.routing_table.items():
                
                if next_hop in to_remove_neighbors:
                    routes_to_remove.append(dst)

            for dst in routes_to_remove:
                del self.routing_table[dst]
            

    def handle_period(self):
        while True:
            time.sleep(self.period)

            self.send_update_messages()
            self.update_last_update()
    
    def start_server(self):
        super().start_server()
        threading.Thread(target=self.handle_period, daemon=True).start()

    def handle_data_message(self, message):
        if message.get("destination") == self.local_ip:
            print(message.get("payload"))

        else:
            destination = message.get("destination")
            next_hop = self.get_next_hop(destination)
            self.send_message(next_hop, message)

    def handle_trace(self, message):
        source = message.get("source")
        destination = message.get("destination")
        
        message["routers"].append(self.local_ip)
        routers = message.get("routers")

        if self.local_ip == destination:
            next_hop = self.get_next_hop(source)
            new_message = self.message_handler.create_data_message(self.local_ip, source, message)
        
        else:
            next_hop = self.get_next_hop(destination)
            new_message = self.message_handler.create_trace_message(source, destination, routers)
        
        self.send_message(next_hop, new_message)
        

    def handle_update(self, message):
        with self.lock:
            try:
                source = message.get("source")
                
                distances = message.get("distances", [])
                
                link_weight = distances[source][1]
                
                # update last_update
                self.last_update[source] = 0

                # remove old routes
                routes_to_remove = []
                for dst, (next_hop, dst_weight) in self.routing_table.items():
                    if next_hop == source:
                        routes_to_remove.append(dst)

                for dst in routes_to_remove:
                    del self.routing_table[dst]

                if link_weight < self.routing_table.get(source, (None, float('inf')))[1]:
                    self.routing_table[source] = (source, link_weight)
                
                for dst, (next_hop, dst_weight) in distances.items():
                    if dst == source:
                        continue
                    
                    weight = link_weight + dst_weight

                    # infinity threshold to avoid infinite loops
                    if weight > INFINITY_THRESHOLD:
                        continue
                    
                    # add new route
                    if self.routing_table.get(dst, None) is None:
                        self.routing_table[dst] = (source, weight)
                        continue                    
                    
                    # update new smaller route
                    if weight <= self.routing_table[dst][1]:
                        self.routing_table[dst] = (source, weight)
            
            except Exception as e:
                logger.error(f"Erro ao atualizar rotas: {e}")

            logger.debug(self.routing_table)

    def handle_message(self, message):
        if message.get("type") == "data":
            self.handle_data_message(message)

        elif message.get("type") == "update":
            self.handle_update(message)

        elif message.get("type") == "trace":
            self.handle_trace(message)

    
    def add_neighbor(self, neighbor_ip, weight):
        if neighbor_ip == self.local_ip:
            logger.error("Cannot add self as neighbor")
            return 
        
        if not neighbor_ip.startswith("127.0.1."):
            logger.error("Invalid IP address (must be in 127.0.1.0/24 range)")
            return 
        
        try:
            weight = float(weight)
            if weight <= 0:
                logger.error("Weight must be positive")
                return 

            # lock para thread-safe
            with self.lock:  
                self.incoming_neighbors[neighbor_ip] = weight
                
            logger.info(f"Added neighbor {neighbor_ip} with weight {weight}")
            return 
            
        except ValueError:
            logger.error("Invalid weight (must be a number)")
            return 
    
    def remove_neighbor(self, neighbor_ip):
        try:
            with self.lock:
                if neighbor_ip in self.incoming_neighbors.keys():
                    del self.incoming_neighbors[neighbor_ip]
                    
                    logger.info(f"Neighbor {neighbor_ip} removed")
                    
                    return 
                else:
                    return 
                    
        except Exception as e:
            logger.error(f"Error removing {neighbor_ip}: {e}")
            return False
        
    def trace_route(self, destination):
        routers = [self.local_ip]
        message = self.message_handler.create_trace_message(self.local_ip, destination, routers)

        next_hop = self.get_next_hop(destination)
        self.send_message(next_hop, message)

    def get_neighbors(self):
        with self.lock:
            return self.incoming_neighbors.copy()
    
    def get_next_hop(self, destination):
        with self.lock:
            route = self.routing_table.get(destination, None)

            return route[0] if route is not None else None