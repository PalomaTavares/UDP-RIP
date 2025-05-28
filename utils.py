import logging
import time
import threading
import ipaddress
import sys
from datetime import datetime

#configurando o logging
def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Reduz verbosidade de alguns módulos
    logging.getLogger('urllib3').setLevel(logging.WARNING)

#retorna IP local
def get_local_ip():
    import socket
    try:
        # Conecta a um endereço público para descobrir IP local
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

#valida formato do ip
def validate_ip_format(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

#Verifica se IP está na rede
def validate_network_ip(ip, network="127.0.1.0/24"):
    try:
        ip_obj = ipaddress.ip_address(ip)
        network_obj = ipaddress.ip_network(network, strict=False)
        return ip_obj in network_obj
    except ValueError:
        return False

#Formata pra exibição
def format_timestamp(timestamp=None):
    if timestamp is None:
        timestamp = time.time()
    
    return datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')

#Formata pra exibição
def format_duration(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"