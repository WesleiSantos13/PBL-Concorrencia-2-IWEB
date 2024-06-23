import requests
import threading

# Configurações
base_url = "http://172.31.96.1:9635"
transferencia_endpoint = "/transferencia/enviar"
headers = {'Content-Type': 'application/json'}

# Dados da transferência base
dados_transferencia_base = {
    "agencia_destino": "3075",
    "conta_destino": "525303",
    "valor": 50,
    "banco_destino": "237"
}

# Função para enviar transferência
def enviar_transferencia(agencia_origem, conta_origem):
    dados_transferencia = dados_transferencia_base.copy()
    dados_transferencia["agencia_origem"] = agencia_origem
    dados_transferencia["conta_origem"] = conta_origem
    response = requests.post(base_url + transferencia_endpoint, json=dados_transferencia, headers=headers)
    print(f"Agência de origem: {agencia_origem}, Conta de origem: {conta_origem}, Status Code: {response.status_code}, Response: {response.json()}")

# Função para enviar transferência de destino para origem
def enviar_transferencia_destino_para_origem():
    dados_transferencia = {
        "agencia_origem": "3075",
        "conta_origem": "525303",
        "agencia_destino": "3080",
        "conta_destino": "453773",
        "banco_destino": "237",
        "valor": 100
    }
    response = requests.post(base_url + transferencia_endpoint, json=dados_transferencia, headers=headers)
    print(f"Transferência de Destino para Origem - Agência de origem: 3075, Conta de origem: 525303, Status Code: {response.status_code}, Response: {response.json()}")

# Lista de agências e contas de origem
agencias_contas_origem = [
    ("3065", "110945"),
    ("3088", "298489"),
    ("3080", "453773"),
]

# Criar múltiplas threads para enviar transferências simultâneas
threads = []
for agencia, conta in agencias_contas_origem:
    thread = threading.Thread(target=enviar_transferencia, args=(agencia, conta))
    threads.append(thread)
    thread.start()

# Adicionar uma transferência de destino para uma das contas de origem simultaneamente
thread_destino_para_origem = threading.Thread(target=enviar_transferencia_destino_para_origem)
threads.append(thread_destino_para_origem)
thread_destino_para_origem.start()

# Esperar todas as threads terminarem
for thread in threads:
    thread.join()
