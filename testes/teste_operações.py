import requests
import threading

BASE_URL = "http://172.31.160.1:9635"  # URL base do seu aplicativo Flask

def realizar_deposito(agencia, conta, valor, banco_destino):
    response = requests.post(f"{BASE_URL}/depositar", json={
        'agencia': agencia,
        'conta': conta,
        'valor': valor,
        'banco_destino': banco_destino
    })
    try:
        print(f"Depósito: {response.json()}")
    except requests.exceptions.JSONDecodeError:
        print(f"Erro no depósito. Status: {response.status_code}. Resposta: {response.text}")


def realizar_saque(agencia, conta, valor):
    response = requests.post(f"{BASE_URL}/sacar", json={
        'agencia': agencia,
        'conta': conta,
        'valor': valor
    })
    print(f"Saque: {response.json()}")

def realizar_transferencia_ted(agencia_origem, conta_origem, agencia_destino, conta_destino, valor, banco_destino):
    response = requests.post(f"{BASE_URL}/transferencia/ted/enviar", json={
        'agencia_origem': agencia_origem,
        'conta_origem': conta_origem,
        'agencia_destino': agencia_destino,
        'conta_destino': conta_destino,
        'valor': valor,
        'banco_destino': banco_destino
    })
    print(f"Transferência TED: {response.json()}")

def realizar_transferencia_pix(chave_pix_destino, contas_origem):
    response = requests.post(f"{BASE_URL}/transferencia/pix/enviar", json={
        'chave_pix_destino': chave_pix_destino,
        'contas_origem': contas_origem
    })
    print(f"Transferência PIX: {response.json()}")

def teste_operacoes_simultaneas():
    # Dados de exemplo
    agencia_dep = "3055"
    conta_dep = "292492"
    valor_dep = 200
    banco_destino_dep = '237'

    agencia_dest = "3080"
    conta_dest = "145650"
    valor = 100
    banco_destino = '237'
    chave_pix_destino = "zib"

    contas_origem_pix = [
        {'banco': "237", 'agencia': "3055", 'conta': "292492", 'valor': 50},
        {'banco': "536", 'agencia': "2035", 'conta': "246279", 'valor': 50}
    ]

    # Criando threads para executar as operações simultaneamente
    threads = []
    threads.append(threading.Thread(target=realizar_deposito, args=(agencia_dep, conta_dep, valor_dep, banco_destino_dep)))
    threads.append(threading.Thread(target=realizar_saque, args=(agencia_dep, conta_dep, valor)))
    threads.append(threading.Thread(target=realizar_transferencia_ted, args=(agencia_dep, conta_dep, agencia_dest, conta_dest, valor, banco_destino)))
    threads.append(threading.Thread(target=realizar_transferencia_pix, args=(chave_pix_destino, contas_origem_pix)))

    # Iniciando as threads
    for thread in threads:
        thread.start()

    # Aguardando todas as threads terminarem
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    teste_operacoes_simultaneas()
