import requests
import threading
import time

BASE_URL = "http://172.31.160.1:9635"

# Função para criar uma conta
def criar_conta(dados_conta):
    response = requests.post(f"{BASE_URL}/criar_conta", json=dados_conta)
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Erro na criação da conta. Status: {response.status_code}. Resposta: {response.text}")
        return None

# Função para cadastrar chave PIX
def cadastrar_chave_pix(base_url, dados_pix):
    response = requests.post(f"{base_url}/pix/cadastrar", json=dados_pix)
    try:
        print(f"Cadastro de Chave PIX: {response.json()}")
    except requests.exceptions.JSONDecodeError:
        print(f"Erro no cadastro de chave PIX. Status: {response.status_code}. Resposta: {response.text}")


# Função para fazer depósito
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

# Função para realizar saque
def realizar_saque(agencia, conta, valor):
    response = requests.post(f"{BASE_URL}/sacar", json={
        'agencia': agencia,
        'conta': conta,
        'valor': valor
    })
    print(f"Saque: {response.json()}")

# Função para realizar transferência TED
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

# Função para realizar transferência PIX
def realizar_transferencia_pix(chave_pix_destino, contas_origem):
    response = requests.post(f"{BASE_URL}/transferencia/pix/enviar", json={
        'chave_pix_destino': chave_pix_destino,
        'contas_origem': contas_origem
    })
    print(f"Transferência PIX: {response.json()}")

# Função para consultar saldo
def consultar_saldo(agencia, conta):
    response = requests.get(f"{BASE_URL}/saldo", params={'agencia': agencia, 'conta': conta})
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Erro ao consultar saldo. Status: {response.status_code}. Resposta: {response.text}")
        return None

def teste_operacoes_simultaneas():
    # Dados para criação de contas e depósitos
    contas = [
        {'senha': '1234', 'tipo_conta': 'PFC', 'titulares': {'11111111111': 'Cliente1', '22222222222': 'Cliente2'}},
        {'senha': '1234', 'tipo_conta': 'PFI', 'cpf_ou_cnpj': '11111111111', 'nome': 'Cliente1'},
        {'senha': '1234', 'tipo_conta': 'PFI', 'cpf_ou_cnpj': '22222222222', 'nome': 'Cliente2'}
    ]

    depositos = []

    # Criando as contas e preparando os dados de depósito
    for conta in contas:
        resposta = criar_conta(conta)
        if resposta:
            agencia = resposta['agencia']
            numero_conta = resposta['conta']
            depositos.append({
                'agencia': agencia,
                'conta': numero_conta,
                'valor': 200,
                'banco_destino': '237'
            })

    # Realizando depósitos nas contas
    for deposito in depositos:
        realizar_deposito(deposito['agencia'], deposito['conta'], deposito['valor'], deposito['banco_destino'])

    # Pequeno atraso para garantir que os depósitos sejam processados
    time.sleep(5)

    # Dados para transferências e saques
    agencia_dep = depositos[0]['agencia'] # Conta conjunta cliente 1 e 2
    conta_dep = depositos[0]['conta']

    
    agencia_dest2 = depositos[2]['agencia'] # Conta individual cliente 2
    conta_dest2 = depositos[2]['conta']
    chave_pix_destino = "75-98344-5581"

    # Cadastrando a chave PIX na conta de destino
    chave_pix_destino = "75-98344-5581"
    dados_pix_destino = {
        'agencia':  agencia_dest2,
        'conta': conta_dest2,
        'chave_pix': chave_pix_destino,
        'tipo_chave': 'Telefone'
    }
    cadastrar_chave_pix(BASE_URL, dados_pix_destino)

    # O cliente 1 que vai fazer a transferência via pix para o cliente 2.
    contas_origem_pix = [
        {'banco': "237", 'agencia': depositos[0]['agencia'], 'conta': depositos[0]['conta'], 'valor': 50}, # Conta conjunta cliente 1 e 2
        {'banco': "237", 'agencia': depositos[1]['agencia'], 'conta': depositos[1]['conta'], 'valor': 50} # Conta individual cliente 1
    ]

    # Criando threads para executar as operações simultaneamente
    threads = []
    threads.append(threading.Thread(target=realizar_deposito, args=(agencia_dep, conta_dep, 200, '237'))) # Conta conjunta recebe mais 200 reais
    threads.append(threading.Thread(target=realizar_saque, args=(agencia_dep, conta_dep, 50))) # Conta conjunta menos 50 reais do saque
    threads.append(threading.Thread(target=realizar_transferencia_ted, args=(agencia_dep, conta_dep, agencia_dest2, conta_dest2, 100, '237'))) # Conta conjunta envia 100 reais para a conta individual do cliente 2
    threads.append(threading.Thread(target=realizar_transferencia_pix, args=(chave_pix_destino, contas_origem_pix))) # Conta individual do cliente 2 recebe 100 reais
    #threads.append(threading.Thread(target=realizar_transferencia_pix, args=(chave_pix_destino, contas_origem_pix))) # Conta individual do cliente 2 recebe 100 reais
    #threads.append(threading.Thread(target=realizar_transferencia_pix, args=(chave_pix_destino, contas_origem_pix))) # Conta individual do cliente 2 recebe 100 reais

    # Iniciando as threads
    for thread in threads:
        thread.start()

    # Aguardando todas as threads terminarem
    for thread in threads:
        thread.join()

    # Consultando saldos após as operações
    saldos_esperados = {
        (depositos[0]['agencia'], depositos[0]['conta']): 200,
        (depositos[1]['agencia'], depositos[1]['conta']): 150,
        (depositos[2]['agencia'], depositos[2]['conta']): 400
    }

    print("\nVerificação dos saldos após operações:")
    for deposito in depositos:
        saldo_real = consultar_saldo(deposito['agencia'], deposito['conta'])
        if saldo_real:
            saldo_real_valor = saldo_real.get('saldo', None)
            saldo_esperado = saldos_esperados[(deposito['agencia'], deposito['conta'])]
            print(f"Agência: {deposito['agencia']} Conta: {deposito['conta']} - Saldo esperado: {saldo_esperado} - Saldo real: {saldo_real_valor}")

if __name__ == "__main__":
    teste_operacoes_simultaneas()
