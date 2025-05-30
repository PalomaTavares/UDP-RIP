import socket
import threading
import time
import logging
from messages import MessageHandler

logger = logging.getLogger(__name__)

class NetworkManager:
    def __init__(self, local_ip, port):
        self.local_ip = local_ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((local_ip, port))
        self.running = True

    def start_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.local_ip, self.port))
            self.socket.settimeout(1.0)  # Timeout para permitir shutdown graceful
            
            self.running = True
            logger.info(f"Servidor UDP iniciado em {self.local_ip}:{self.port}")
            
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    self.handle_message(data, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Erro ao receber mensagem: {e}")
                        
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor: {e}")
        finally:
            self.cleanup_socket()

    #envia ping pro vizinho
    def send_ping(self, dest_ip):
        try:
            message = f"PING from {self.local_ip}"
            self.socket.sendto(message.encode(), (dest_ip, self.port))
            return True
        except Exception as e:
            logger.error(f"Error sending ping to {dest_ip}: {e}")
            return False

    def start_server(self):
        def receive_loop():
            while self.running:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    if data.decode().startswith("PING"):
                        response = f"PONG from {self.local_ip}"
                        self.socket.sendto(response.encode(), addr)
                except Exception as e:
                    if self.running:
                        logger.error(f"Receive error: {e}")

        threading.Thread(target=receive_loop, daemon=True).start()


    #para o servidor UDP
    def stop_server(self):
        self.running = False
        self.cleanup_socket()
        logger.info("Servidor UDP parado")

    #fechando socket
    def cleanup_socket(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

    # Processa mensagem recebida
    def handle_message(self, data, addr):
        try:
            message = self.message_handler.decode(data)
            sender_ip = addr[0]
            
            logger.debug(f"Mensagem recebida de {sender_ip}: {message}")
            
            # Processa os tipos de mensagem
            msg_type = message.get('type')
            
            if msg_type == 'ping':
                self.handle_ping(sender_ip, message)
            elif msg_type == 'pong':
                self.handle_pong(sender_ip, message)
            elif msg_type == 'route_update':
                self.handle_route_update(sender_ip, message)
            elif msg_type == 'trace_request':
                self.handle_trace_request(sender_ip, message)
            else:
                logger.warning(f"Tipo de mensagem desconhecido: {msg_type}")
                
        except Exception as e:
            logger.error(f"Erro ao processar mensagem de {addr}: {e}")

    #responde pong
    def handle_ping(self, sender_ip, message):
        response = {
            'type': 'pong',
            'sender': self.local_ip,
            'timestamp': time.time()
        }
        success = self.send_message(sender_ip, response)
        if success:
            logger.debug(f"Pong enviado para {sender_ip}")
        
        # Update neighbor timestamp when we receive ping
        self.router.update_neighbor_timestamp(sender_ip)

    #processa ping
    def handle_pong(self, sender_ip, message):
        logger.debug(f"Pong recebido de {sender_ip}")
        self.router.update_neighbor_timestamp(sender_ip)
    

    #Processa atualização de rota
    def handle_route_update(self, sender_ip, message):
        routes = message.get('routes', {})
        self.router.process_route_update(sender_ip, routes)

    #Processa trace
    def handle_trace_request(self, sender_ip, message):
        destination = message.get('destination')
        trace_id = message.get('trace_id')
        path = message.get('path', [])
        
        # Adiciona nó ao caminho
        path.append(self.local_ip)
        
        # Se este é o destino, retorna o caminho
        if destination == self.local_ip:
            response = {
                'type': 'trace_response',
                'trace_id': trace_id,
                'path': path,
                'destination_reached': True
            }
            self.send_message(sender_ip, response)
        else:
            # Encaminha para próximo hop
            next_hop = self.router.get_next_hop(destination)
            if next_hop and next_hop != sender_ip:
                forward_msg = {
                    'type': 'trace_request',
                    'destination': destination,
                    'trace_id': trace_id,
                    'path': path
                }
                self.send_message(next_hop, forward_msg)
    
    #Envia mensagem UDP para destino
    def send_message(self, dest_ip, message):
        try:
            data = self.message_handler.encode(message)
            
            # Cria socket temporário para envio
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(5.0)
                sock.sendto(data, (dest_ip, self.port))
                
            logger.debug(f"Mensagem enviada para {dest_ip}: {message['type']}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para {dest_ip}: {e}")
            return False
    
    def test_connection(self, dest_ip, port=None):
        if port is None:
            port = self.port
            
        try:
            ping_msg = {
                'type': 'ping',
                'sender': self.local_ip,
                'timestamp': time.time()
            }
            
            # Envia ping
            success = self.send_message(dest_ip, ping_msg)
            if not success:
                return False
            
            # Aguarda resposta (simples implementação)
            # Em implementação mais robusta, usaria callbacks ou threads
            time.sleep(0.1)
            return True
            
        except Exception as e:
            logger.debug(f"Teste de conexão falhou para {dest_ip}: {e}")
            return False

    #Envia mensagem para todos os vizinhos
    def broadcast_to_neighbors(self, message):
        neighbors = self.router.get_neighbors()
        success_count = 0
        
        for neighbor_ip in neighbors:
            if self.send_message(neighbor_ip, message):
                success_count += 1
        
        logger.debug(f"Broadcast enviado para {success_count}/{len(neighbors)} vizinhos")
        return success_count
    
     #Envia atualização de rotas para vizinhos
    def send_route_update(self):
        routes = self.router.get_routing_table()
        message = {
            'type': 'route_update',
            'sender': self.local_ip,
            'timestamp': time.time(),
            'routes': routes
        }
        
        return self.broadcast_to_neighbors(message)
