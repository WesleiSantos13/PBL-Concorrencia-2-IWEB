import requests
import threading
import time

# Configurações
base_url = "http://172.31.96.1:9635"
transferencia_endpoint = "/transferencia/enviar"
headers = {'Content-Type': 'application/json'}

# Dados da transferência
dados_transferencia = {
    "agencia_origem": "3080",
    "conta_origem": "453773",
    "agencia_destino": "3075",
    "conta_destino": "525303",
    "valor": 15,
    "banco_destino": "237"
}

lock = threading.Lock()

# Função para enviar transferência
def enviar_transferencia():
    global lock
    while True:
        with lock:
            response = requests.post(base_url + transferencia_endpoint, json=dados_transferencia, headers=headers)
            print(f"Status Code: {response.status_code}, Response: {response.json()}")
            if response.status_code == 200:
                break
            elif response.status_code == 423:
                print("Conta de origem em uso. Tentando novamente após 1 segundo...")
                time.sleep(1)  # Espera um pouco antes de tentar novamente

# Criar múltiplas threads para enviar transferências simultâneas
threads = []
for i in range(5):  # Número de requisições simultâneas
    thread = threading.Thread(target=enviar_transferencia)
    threads.append(thread)
    thread.start()

# Esperar todas as threads terminarem
for thread in threads:
    thread.join()
