import requests
import threading
import time

# URLs dos bancos
BASE_URL_1 = "http://172.31.160.1:9635"
BASE_URL_2 = "http://172.31.160.1:9636"
BASE_URL_3 = "http://172.31.160.1:9637"

# Função para criar uma conta
def criar_conta(base_url, dados_conta):
    response = requests.post(f"{base_url}/criar_conta", json=dados_conta)
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Erro na criação da conta. Status: {response.status_code}. Resposta: {response.text}")
        return None

# Função para fazer depósito
def realizar_deposito(base_url, dados_deposito):
    response = requests.post(f"{base_url}/depositar", json=dados_deposito)
    try:
        print(f"Depósito: {response.json()}")
    except requests.exceptions.JSONDecodeError:
        print(f"Erro no depósito. Status: {response.status_code}. Resposta: {response.text}")

# Função para cadastrar chave PIX
def cadastrar_chave_pix(base_url, dados_pix):
    response = requests.post(f"{base_url}/pix/cadastrar", json=dados_pix)
    try:
        print(f"Cadastro de Chave PIX: {response.json()}")
    except requests.exceptions.JSONDecodeError:
        print(f"Erro no cadastro de chave PIX. Status: {response.status_code}. Resposta: {response.text}")

# Função para realizar transferência PIX
def realizar_transferencia_pix(base_url, chave_pix_destino, contas_origem):
    response = requests.post(f"{base_url}/transferencia/pix/enviar", json={
        'chave_pix_destino': chave_pix_destino,
        'contas_origem': contas_origem
    })
    try:
        print(f"Transferência PIX ({base_url}): {response.json()}")
    except requests.exceptions.JSONDecodeError:
        print(f"Erro na transferência PIX. Status: {response.status_code}. Resposta: {response.text}")

# Função para consultar saldo
def consultar_saldo(base_url, agencia, conta):
    response = requests.get(f"{base_url}/saldo", params={'agencia': agencia, 'conta': conta})
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Erro ao consultar saldo. Status: {response.status_code}. Resposta: {response.text}")
        return None

def teste_concorrencia_distribuida():
    # Dados para criação de contas e depósitos
    contas = [
        {'base_url': BASE_URL_1, 'dados': {'senha': '1234', 'tipo_conta': 'PFC', 'titulares': {'11111111111': 'Cliente1', '22222222222': 'Cliente2'}}, 'cod': '237'},
        {'base_url': BASE_URL_2, 'dados': {'senha': '1234', 'tipo_conta': 'PFI', 'cpf_ou_cnpj': '11111111111', 'nome': 'Cliente1'}, 'cod': '536'},
        {'base_url': BASE_URL_1, 'dados': {'senha': '1234', 'tipo_conta': 'PFI', 'cpf_ou_cnpj': '22222222222', 'nome': 'Cliente2'}, 'cod': '237'},
        {'base_url': BASE_URL_3, 'dados': {'senha': '1234', 'tipo_conta': 'PFI', 'cpf_ou_cnpj': '22222222222', 'nome': 'Cliente2'}, 'cod': '380'},
        {'base_url': BASE_URL_2, 'dados': {'senha': '1234', 'tipo_conta': 'PFI', 'cpf_ou_cnpj': '33333333333', 'nome': 'Cliente3'}, 'cod': '536'},
        {'base_url': BASE_URL_3, 'dados': {'senha': '1234', 'tipo_conta': 'PFI', 'cpf_ou_cnpj': '33333333333', 'nome': 'Cliente3'}, 'cod': '380'},
        {'base_url': BASE_URL_3, 'dados': {'senha': '1234', 'tipo_conta': 'PFI', 'cpf_ou_cnpj': '44444444444', 'nome': 'Cliente4'}, 'cod': '380'}
    ]

    depositos = []

    # Criando as contas e preparando os dados de depósito
    for conta in contas:
        resposta = criar_conta(conta['base_url'], conta['dados'])
        if resposta:
            agencia = resposta['agencia']
            numero_conta = resposta['conta']
            depositos.append({
                'base_url': conta['base_url'],
                'dados': {
                    'agencia': agencia,
                    'conta': numero_conta,
                    'valor': 200,
                    'banco_destino': conta['cod']
                }
            })

    # Realizando depósitos nas contas
    for deposito in depositos[:-1]:  # O último não precisa de depósito, pois é o destino
        realizar_deposito(deposito['base_url'], deposito['dados'])

    # Pequeno atraso para garantir que os depósitos sejam processados
    time.sleep(5)

    # Cadastrando a chave PIX na conta de destino
    chave_pix_destino = "75-98344-5581"
    dados_pix_destino = {
        'agencia': depositos[-1]['dados']['agencia'],
        'conta': depositos[-1]['dados']['conta'],
        'chave_pix': chave_pix_destino,
        'tipo_chave': 'Telefone'
    }
    cadastrar_chave_pix(depositos[-1]['base_url'], dados_pix_destino)

    # Pequeno atraso para garantir que o cadastro da chave PIX seja processado
    time.sleep(5)

    # Dados para transferências PIX
    contas_origem_pix_1 = [{'banco': depositos[0]['dados']['banco_destino'], 'agencia': depositos[0]['dados']['agencia'], 'conta': depositos[0]['dados']['conta'], 'valor': 50},
                           {'banco': depositos[1]['dados']['banco_destino'], 'agencia': depositos[1]['dados']['agencia'], 'conta': depositos[1]['dados']['conta'], 'valor': 50}]
    contas_origem_pix_2 = [{'banco': depositos[2]['dados']['banco_destino'], 'agencia': depositos[2]['dados']['agencia'], 'conta': depositos[2]['dados']['conta'], 'valor': 100},
                           {'banco': depositos[3]['dados']['banco_destino'], 'agencia': depositos[3]['dados']['agencia'], 'conta': depositos[3]['dados']['conta'], 'valor': 100},
                           {'banco': depositos[0]['dados']['banco_destino'], 'agencia': depositos[0]['dados']['agencia'], 'conta': depositos[0]['dados']['conta'], 'valor': 50}]
    contas_origem_pix_3 = [{'banco': depositos[4]['dados']['banco_destino'], 'agencia': depositos[4]['dados']['agencia'], 'conta': depositos[4]['dados']['conta'], 'valor': 75},
                           {'banco': depositos[5]['dados']['banco_destino'], 'agencia': depositos[5]['dados']['agencia'], 'conta': depositos[5]['dados']['conta'], 'valor': 75}]

    # Criando threads para executar as transferências simultaneamente
    threads = []
    threads.append(threading.Thread(target=realizar_transferencia_pix, args=(BASE_URL_1, chave_pix_destino, contas_origem_pix_1)))
    threads.append(threading.Thread(target=realizar_transferencia_pix, args=(BASE_URL_2, chave_pix_destino, contas_origem_pix_2)))
    threads.append(threading.Thread(target=realizar_transferencia_pix, args=(BASE_URL_3, chave_pix_destino, contas_origem_pix_3)))
    
    # Iniciando as threads
    for thread in threads:
        thread.start()

    # Aguardando todas as threads terminarem
    for thread in threads:
        thread.join()

    # Consultando saldos após as transferências
    saldos_esperados = {
        (depositos[0]['dados']['agencia'], depositos[0]['dados']['conta']): 100,
        (depositos[1]['dados']['agencia'], depositos[1]['dados']['conta']): 150,
        (depositos[2]['dados']['agencia'], depositos[2]['dados']['conta']): 100,
        (depositos[3]['dados']['agencia'], depositos[3]['dados']['conta']): 100,
        (depositos[4]['dados']['agencia'], depositos[4]['dados']['conta']): 125,
        (depositos[5]['dados']['agencia'], depositos[5]['dados']['conta']): 125,
        (depositos[6]['dados']['agencia'], depositos[6]['dados']['conta']): 500,  # Conta de destino
    }

    print("\nVerificação dos saldos após transferências:")
    for deposito in depositos:
        saldo_real = consultar_saldo(deposito['base_url'], deposito['dados']['agencia'], deposito['dados']['conta'])
        if saldo_real:
            saldo_real_valor = saldo_real.get('saldo', None)
            saldo_esperado = saldos_esperados[(deposito['dados']['agencia'], deposito['dados']['conta'])]
            print(f"Agência: {deposito['dados']['agencia']} Conta: {deposito['dados']['conta']} - Saldo esperado: {saldo_esperado} - Saldo real: {saldo_real_valor}")

if __name__ == "__main__":
    teste_concorrencia_distribuida()
