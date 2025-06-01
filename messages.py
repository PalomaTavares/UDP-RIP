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
                logger.warning(f"Mensagem muito grande: {len(data)} bytes")
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao codificar mensagem: {e}")
            raise
    
    #JSON para Python
    def decode(self, data):
        try:
            json_str = data.decode('utf-8')
            message = json.loads(json_str)
            
            # Validação básica da estrutura
            if not isinstance(message, dict):
                raise ValueError("Mensagem deve ser um dicionário JSON")
            
            if 'type' not in message:
                raise ValueError("Mensagem deve ter campo 'type'")
            
            return message
            
        except Exception as e:
            logger.error(f"Erro ao decodificar mensagem: {e}")
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
    
    def validate_message(self, message):
        required_fields = ['type', 'source', 'destination']
        
        for field in required_fields:
            if field not in message:
                raise ValueError(f"Campo obrigatório ausente: {field}")
        
        # Validações específicas por tipo
        msg_type = message['type']
        
        if msg_type == "data":
            if 'payload' not in message:
                raise ValueError("Mensagem data deve ter campo 'payload'")
            
        elif msg_type == 'update':
            if 'distances' not in message:
                raise ValueError("Mensagem route_update deve ter campo 'routes'")
            if not isinstance(message['routes'], dict):
                raise ValueError("Campo 'routes' deve ser um dicionário")
        
        elif msg_type == 'trace':
            required = ['destination', 'trace_id', 'path']
            for field in required:
                if field not in message:
                    raise ValueError(f"trace_request deve ter campo '{field}'")
        
        return True
    
    #formata o log
    def format_message_for_log(self, message):
        try:
            msg_type = message.get('type', 'unknown')
            sender = message.get('sender', 'unknown')
            
            if msg_type == 'update':
                routes_count = len(message.get('routes', {}))
                return f"{msg_type} from {sender} ({routes_count} routes)"
            
            elif msg_type == 'trace':
                dest = message.get('destination', message.get('trace_id', 'unknown'))
                return f"{msg_type} from {sender} (dest: {dest})"
            
            else:
                return f"{msg_type} from {sender}"
                
        except Exception:
            return str(message)[:100] + "..." if len(str(message)) > 100 else str(message)