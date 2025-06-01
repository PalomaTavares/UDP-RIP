import socket
import threading
import time
import logging
from messages import MessageHandler

logger = logging.getLogger(__name__)

PORT = 55151

class NetworkManager:
    def __init__(self, local_ip):
        self.local_ip = local_ip
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((local_ip, PORT))
        self.running = True
        self.message_handler = MessageHandler()

    def handle_message(self, message):        
        pass

    def receive_loop(self):
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                message = self.message_handler.decode(data)
                logger.info(f"Mensagem recebida de {addr}: {message}")

                self.handle_message(message)

            except Exception as e:
                if self.running:
                    logger.error(f"Erro ao receber mensagem: {e}")

    def start_server(self):
        self.running = True
        threading.Thread(target=self.receive_loop, daemon=True).start()


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
    
    #Envia mensagem UDP para destino
    def send_message(self, dest_ip, message):
        try:
            data = self.message_handler.encode(message)
            
            print(dest_ip, PORT)
            self.socket.sendto(data, (dest_ip, PORT))
                
            logger.debug(f"Mensagem enviada para {dest_ip}: {message['type']}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para {dest_ip}: {e}")
            return False
