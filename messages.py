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
    
    #JSON para Python"
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
    
    def create_ping_message(self, sender_ip):
        return {
            'type': 'ping',
            'sender': sender_ip,
            'timestamp': self._get_timestamp()
        }
    
    def create_pong_message(self, sender_ip):
        return {
            'type': 'pong',
            'sender': sender_ip,
            'timestamp': self._get_timestamp()
        }
    
    def create_route_update_message(self, sender_ip, routes):
        return {
            'type': 'route_update',
            'sender': sender_ip,
            'timestamp': self._get_timestamp(),
            'routes': routes
        }
    
    def create_trace_request_message(self, sender_ip, destination, trace_id, path=None):
        return {
            'type': 'trace_request',
            'sender': sender_ip,
            'destination': destination,
            'trace_id': trace_id,
            'path': path or [sender_ip],
            'timestamp': self._get_timestamp()
        }
    
    def create_trace_response_message(self, sender_ip, trace_id, path, destination_reached=False):
        return {
            'type': 'trace_response',
            'sender': sender_ip,
            'trace_id': trace_id,
            'path': path,
            'destination_reached': destination_reached,
            'timestamp': self._get_timestamp()
        }
    
    def create_error_message(self, sender_ip, error_type, error_msg):
        return {
            'type': 'error',
            'sender': sender_ip,
            'error_type': error_type,
            'error_message': error_msg,
            'timestamp': self._get_timestamp()
        }
    
    def validate_message(self, message):
        required_fields = ['type', 'sender', 'timestamp']
        
        for field in required_fields:
            if field not in message:
                raise ValueError(f"Campo obrigatório ausente: {field}")
        
        # Validações específicas por tipo
        msg_type = message['type']
        
        if msg_type == 'route_update':
            if 'routes' not in message:
                raise ValueError("Mensagem route_update deve ter campo 'routes'")
            if not isinstance(message['routes'], dict):
                raise ValueError("Campo 'routes' deve ser um dicionário")
        
        elif msg_type == 'trace_request':
            required = ['destination', 'trace_id', 'path']
            for field in required:
                if field not in message:
                    raise ValueError(f"trace_request deve ter campo '{field}'")
        
        elif msg_type == 'trace_response':
            required = ['trace_id', 'path', 'destination_reached']
            for field in required:
                if field not in message:
                    raise ValueError(f"trace_response deve ter campo '{field}'")
        
        return True
    
    def get_timestamp(self):
        import time
        return time.time()
    
    def format_message_for_log(self, message):
        """Formata mensagem para log"""
        try:
            msg_type = message.get('type', 'unknown')
            sender = message.get('sender', 'unknown')
            
            if msg_type == 'route_update':
                routes_count = len(message.get('routes', {}))
                return f"{msg_type} from {sender} ({routes_count} routes)"
            
            elif msg_type in ['trace_request', 'trace_response']:
                dest = message.get('destination', message.get('trace_id', 'unknown'))
                return f"{msg_type} from {sender} (dest: {dest})"
            
            else:
                return f"{msg_type} from {sender}"
                
        except Exception:
            return str(message)[:100] + "..." if len(str(message)) > 100 else str(message)