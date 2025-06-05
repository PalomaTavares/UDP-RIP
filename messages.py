import json
import logging

logger = logging.getLogger(__name__)

class MessageHandler:
    def __init__(self):
        self.max_message_size = 1024
    
    #mensagem python para bytes JSON
    def encode(self, message):
        try:
            json_str = json.dumps(message, ensure_ascii=False)
            data = json_str.encode('utf-8')
            
            if len(data) > self.max_message_size:
                logger.warning(f"Message too big: {len(data)} bytes")
            
            return data
            
        except Exception as e:
            logger.error(f"Error encoding message: {e}")
            raise
    
    def decode(self, data):
        try:
            json_str = data.decode('utf-8')
            message = json.loads(json_str)
            
            # Validação básica da estrutura
            if not isinstance(message, dict):
                raise ValueError("Message should be a dictionary")
            
            if 'type' not in message or 'source' not in message or 'destination' not in message:
                raise ValueError("Missing fields in message")
            
            return message
            
        except Exception as e:
            logger.error(f"Error decoding message: {e}")
            raise
    
    def create_conection_message(self, src_ip, dst_ip, weight):
        return {
            'type': 'connection',
            'source': src_ip,
            'destination': dst_ip,
            'weight': weight
        }
    
    def create_disconection_message(self, src_ip, dst_ip):
        return {
            'type': 'disconnection',
            'source': src_ip,
            'destination': dst_ip
        }
    
    def create_data_message(self, src_ip, dst_ip, payload):
        return {
            'type': 'data',
            'source': src_ip,
            'destination': dst_ip,
            'payload': payload
        }
    
    def create_update_message(self, src_ip, dst_ip, distances):
        return {
            'type': 'update',
            'source': src_ip,
            'destination': dst_ip,
            'distances': distances
        }
    
    def create_trace_message(self, src_ip, dst_ip, routers):
        return {
            'type': 'trace',
            'source': src_ip,
            'destination': dst_ip,
            'routers': routers
        }