from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from threading import Lock
import socket
import requests
import random
import time
import os

ip_table_router = '172.31.160.1'
url_table_router = 'http://' + ip_table_router + ':4326'

# Configuração do banco de dados
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neon.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de dados
class Titular(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf_ou_cnpj = db.Column(db.String(14), unique=True, nullable=False)

conta_titular = db.Table('conta_titular',
    db.Column('conta_id', db.Integer, db.ForeignKey('conta.id'), primary_key=True),
    db.Column('titular_id', db.Integer, db.ForeignKey('titular.id'), primary_key=True)
)

class Conta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agencia = db.Column(db.String(50), nullable=False)
    conta = db.Column(db.String(50), nullable=False, unique=True)
    senha = db.Column(db.String(50), nullable=False)
    saldo = db.Column(db.Float, default=0.0)
    chave_pix_cpf_cnpj = db.Column(db.String(100), unique=True)
    chave_pix_email = db.Column(db.String(100), unique=True)
    chave_pix_aleatoria = db.Column(db.String(100), unique=True)
    numero_celular = db.Column(db.String(20), unique=True)
    tipo_conta = db.Column(db.String(3), nullable=False) 
    titulares = db.relationship('Titular', secondary=conta_titular, lazy='subquery',
        backref=db.backref('contas', lazy=True))

class Lock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource = db.Column(db.String(255), unique=True, nullable=False)
    locked = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

# Função para adquirir um bloqueio 
def acquire_lock(resource, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            lock = Lock.query.filter_by(resource=resource).with_for_update(nowait=True).first()
            if lock and not lock.locked:
                lock.locked = True
                db.session.commit()
                return True
            elif not lock:
                new_lock = Lock(resource=resource, locked=True)
                db.session.add(new_lock)
                db.session.commit()
                return True
        except SQLAlchemyError:
            db.session.rollback()
        time.sleep(0.1)
    return False

# Função para liberar um bloqueio em um recurso específico
def release_lock(resource):
    try:
        lock = Lock.query.filter_by(resource=resource).first()
        if lock and lock.locked:
            lock.locked = False
            db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()


# Inicializa o banco de dados
with app.app_context():
    db.create_all()


def obter_tabela_roteamento():
    response = requests.get(url_table_router + '/get_banks')
    if response.status_code == 200:
        return response.json()
    else:
        print('Erro ao obter tabela de roteamento:', response.json())
        return {}

def atualizar_tabela_roteamento(cod_banco, url_banco):
    dados = {
        'banco_id': cod_banco,
        'url': url_banco
    }
    response = requests.put(url_table_router + '/put_banks', json=dados)
    if response.status_code == 200:
        print('Tabela de roteamento atualizada com sucesso.')
    else:
        print('Erro ao atualizar tabela de roteamento:', response.json())

# Configurações do banco
IP = socket.gethostbyname(socket.gethostname())
PORT = 9636
URL_SERVER = f'http://{IP}:{PORT}'
# Colocando o código do banco e a url na tabela de roteamento
BANCO_ID = '536'
atualizar_tabela_roteamento(BANCO_ID, URL_SERVER)


# Gera uma agência única
def gerar_agencia():
    return f"{random.randint(2000, 2200)}"

# Gera um número de conta único
def gerar_conta():
    while True:
        conta = f"{random.randint(100000, 999999)}"
        if not Conta.query.filter_by(conta=conta).first():
            return conta

# Rota para criar conta
@app.route('/criar_conta', methods=['POST'])
def criar_conta():
    dados = request.json
    senha = dados.get('senha')
    tipo_conta = dados.get('tipo_conta')

    agencia = gerar_agencia()
    conta = gerar_conta()
    nova_conta = Conta(agencia=agencia, conta=conta, senha=senha, tipo_conta=tipo_conta)

    if tipo_conta == 'PFC':  # Conta conjunta
        titulares_dados = dados.get('titulares')
        # Verificar se os titulares já têm uma conta conjunta juntos--------------------------- nao funciona
        for cpf, nome in titulares_dados.items():
            titular = Titular.query.filter_by(cpf_ou_cnpj=cpf).first()
            if not titular:
                titular = Titular(nome=nome, cpf_ou_cnpj=cpf)
                db.session.add(titular)
            else:
                for conta_titular in titular.contas:
                    if conta_titular.tipo_conta == 'PFC' and set(conta_titular.titulares) == set(titulares_dados.keys()):
                        return jsonify({'erro': 'Titulares já possuem uma conta conjunta juntos'}), 400

            nova_conta.titulares.append(titular)

    else:  # Conta individual (PJ ou PFI)
        cpf_ou_cnpj = dados.get('cpf_ou_cnpj')
        nome = dados.get('nome')

        # Verificar se o CPF já possui registro em conta individual ou se o CNPJ já possui registro em uma conta jurídica
        titular_existente = Titular.query.filter_by(cpf_ou_cnpj=cpf_ou_cnpj).first()
        if titular_existente:
            if any(conta.tipo_conta == 'PFI' for conta in titular_existente.contas):
                return jsonify({'erro': 'O cliente já possui uma conta individual'}), 400
            
            if any(conta.tipo_conta == 'PJ' for conta in titular_existente.contas):
                return jsonify({'erro': 'O CNPJ já possui registro em uma conta jurídica'}), 400

        titular = Titular.query.filter_by(cpf_ou_cnpj=cpf_ou_cnpj).first()
        if not titular:
            titular = Titular(nome=nome, cpf_ou_cnpj=cpf_ou_cnpj)
            db.session.add(titular)
        nova_conta.titulares.append(titular)
    db.session.add(nova_conta)
    db.session.commit()
    return jsonify({'mensagem': 'Conta criada com sucesso', 'agencia': agencia,'conta': conta}), 200




# Rota para fazer depósito
@app.route('/depositar', methods=['POST'])
def depositar():
    dados = request.json
    agencia_destino = dados['agencia']
    conta_destino = dados['conta']
    valor = dados['valor']
    banco_destino = dados['banco_destino']

    # Verifica se o banco destino está na tabela de roteamento
    banco_urls = obter_tabela_roteamento()
    if banco_destino not in banco_urls:
        return jsonify({'erro': 'Banco de destino não encontrado'}), 404

    # Envia a transferência para o banco destino
    url_destino = f"{banco_urls[banco_destino]}/transferencia/receber"
    dados_transferencia = {
        "tipo": "DEP",
        'agencia_destino': agencia_destino,
        'conta_destino': conta_destino,
        'valor': valor,
    }
    response = requests.post(url_destino, json=dados_transferencia)
    if response.status_code == 200:
        return jsonify({'mensagem': 'Depósito realizado com sucesso'}), 200
    else:
        return jsonify({'erro': 'Falha no depósito'}), response.status_code



@app.route('/sacar', methods=['POST'])
def sacar():
    dados = request.json
    agencia = dados.get('agencia')
    conta = dados.get('conta')
    valor = dados.get('valor')
    
    lock_key_conta = f"{agencia}-{conta}"
    
    # Tenta adquirir o bloqueio para a conta
    if not acquire_lock(lock_key_conta):
        return jsonify({'erro': 'A conta está sendo usada em outra operação'}), 423

    try:
        conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
        if not conta_obj:
            return jsonify({'erro': 'Conta não encontrada'}), 404

        if conta_obj.saldo < valor:
            return jsonify({'erro': 'Saldo insuficiente'}), 400

        conta_obj.saldo -= valor
        db.session.commit()

        return jsonify({'mensagem': 'Saque realizado com sucesso'}), 200
    except Exception as e:
        return jsonify({'erro': 'Ocorreu um erro ao processar a solicitação'}), 500
    finally:
        # Libera o bloqueio
        release_lock(lock_key_conta)







@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    agencia = dados.get('agencia')
    conta = dados.get('conta')
    senha = dados.get('senha')
    cpf_ou_cnpj = dados.get('cpf_ou_cnpj')

    conta_obj = Conta.query.filter_by(conta=conta, agencia=agencia).first()
    titular_obj = Titular.query.filter_by(cpf_ou_cnpj=cpf_ou_cnpj).first()

    if conta_obj and conta_obj.senha == senha and titular_obj in conta_obj.titulares:
        return jsonify({'mensagem': 'Login bem-sucedido'}), 200
    else:
        return jsonify({'erro': 'Credenciais inválidas'}), 401

@app.route('/saldo', methods=['GET'])
def saldo():
    agencia = request.args.get('agencia')
    conta = request.args.get('conta')
    conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
    if conta_obj:
        return jsonify({'saldo': conta_obj.saldo}), 200
    else:
        return jsonify({'erro': 'Cliente não encontrado'}), 404







@app.route('/transferencia/ted/enviar', methods=['POST'])
def enviar_transferencia():
    dados = request.json
    agencia_origem = dados['agencia_origem']
    conta_origem = dados['conta_origem']
    agencia_destino = dados['agencia_destino']
    conta_destino = dados['conta_destino']
    valor = dados['valor']
    banco_destino = dados['banco_destino']

    conta_origem_obj = Conta.query.filter_by(agencia=agencia_origem, conta=conta_origem).first()

    if conta_origem == conta_destino:
        return jsonify({'erro': 'Não é possível transferir para a mesma conta'}), 400

    if not conta_origem_obj:
        return jsonify({'erro': 'Conta de origem não encontrada'}), 404

    if conta_origem_obj.saldo < valor:
        return jsonify({'erro': 'Saldo insuficiente'}), 400

    # Verifica se o banco destino está na tabela de roteamento
    banco_urls = obter_tabela_roteamento()
    if banco_destino not in banco_urls:
        return jsonify({'erro': 'Banco de destino não encontrado'}), 404

    # Tenta adquirir o bloqueio para a conta de origem
    lock_key_origem = f"{agencia_origem}-{conta_origem}"
    if not acquire_lock(lock_key_origem):
        return jsonify({'erro': 'A conta de origem está sendo usada em outra operação'}), 423

    try:
        # Envia a transferência para o banco destino
        url_destino = f"{banco_urls[banco_destino]}/transferencia/receber"
        dados_transferencia = {
            'tipo': 'TED',
            'agencia_destino': agencia_destino,
            'conta_destino': conta_destino,
            'valor': valor,
        }
        response = requests.post(url_destino, json=dados_transferencia)

        if response.status_code == 200:
            conta_origem_obj.saldo -= valor
            db.session.commit()
            return jsonify({'mensagem': 'Transferência realizada com sucesso'}), 200
        else:
            return jsonify({'erro': 'Falha na transferência para o banco destino'}), response.status_code
    finally:
        # Libera o bloqueio
        release_lock(lock_key_origem)





@app.route('/transferencia/receber', methods=['POST'])
def receber_transferencia():
    dados = request.json
    tipo = dados['tipo']
    valor = dados['valor']
    
    if tipo == 'PIX':
        chave_pix_destino = dados['chave_pix_destino']

        # Verifica se a chave PIX de destino existe e é válida
        conta_destino = Conta.query.filter(
            (Conta.chave_pix_cpf_cnpj == chave_pix_destino) | 
            (Conta.chave_pix_email == chave_pix_destino) | 
            (Conta.chave_pix_aleatoria == chave_pix_destino) | 
            (Conta.numero_celular == chave_pix_destino)
        ).first()

        if not conta_destino:
            return jsonify({'erro': 'Chave PIX de destino inválida'}), 400

        lock_key_destino = f"pix-{chave_pix_destino}"
    elif tipo == 'TED' or tipo == 'DEP':
        agencia_destino = dados['agencia_destino']
        conta_destino = dados['conta_destino']

        conta_destino = Conta.query.filter_by(agencia=agencia_destino, conta=conta_destino).first()

        if not conta_destino:
            return jsonify({'erro': 'Conta de destino não encontrada'}), 404

        lock_key_destino = f"{agencia_destino}-{conta_destino}"
    else:
        return jsonify({'erro': 'Tipo de transferência inválido'}), 400

    # Tenta adquirir o bloqueio para a conta de destino
    if not acquire_lock(lock_key_destino):
        return jsonify({'erro': 'A conta de destino está sendo usada em outra operação'}), 423

    try:
        conta_destino.saldo += valor
        db.session.commit()
        return jsonify({'mensagem': 'Transferência recebida com sucesso'}), 200
    finally:
        # Libera o bloqueio
        release_lock(lock_key_destino)






@app.route('/pix/chave', methods=['GET'])
def verificar_chave_pix():
    chave_pix = request.args.get('chave_pix')
    conta = Conta.query.filter(
        (Conta.chave_pix_cpf_cnpj == chave_pix) | 
        (Conta.chave_pix_email == chave_pix) | 
        (Conta.chave_pix_aleatoria == chave_pix) | 
        (Conta.numero_celular == chave_pix)
    ).first()
    if conta:
        return jsonify({'pertence': True}), 200
    else:
        return jsonify({'pertence': False}), 200

def identificar_banco_destino(chave_pix):
    banco_urls = obter_tabela_roteamento()
    
    for banco_id, url in banco_urls.items():
        response = requests.get(f'{url}/pix/chave', params={'chave_pix': chave_pix})
        if response.status_code == 200:
            if response.json().get('pertence'):
                return banco_id
    
    return None


@app.route('/transferencia/pix/enviar', methods=['POST'])
def enviar_transferencia_pix():
    dados = request.json
    chave_pix_destino = dados['chave_pix_destino']
    contas_origem = dados['contas_origem']  # Lista de dicionários com agencia, conta e valor a ser transferido de cada conta
    valor_total = sum(conta['valor'] for conta in contas_origem)

    if valor_total == 0:
        return jsonify({'erro': 'Valor a transferir zerado'}), 404

    # Identificar o banco destino baseado na chave PIX
    banco_destino = identificar_banco_destino(chave_pix_destino)
    if not banco_destino:
        return jsonify({'erro': 'Chave PIX de destino não encontrada em nenhum banco'}), 404

    saldo_suficiente = True
 
    # Iterarando sobre cada conta origem para verificar o saldo e atualizar
    for conta_info in contas_origem:
        banco_origem = conta_info['banco']
        agencia_origem = conta_info['agencia']
        conta_origem = conta_info['conta']
        valor = conta_info['valor']

        # Verificar se a conta de origem existe e tem saldo suficiente
        if banco_origem == BANCO_ID:
            conta_origem_obj = Conta.query.filter_by(agencia=agencia_origem, conta=conta_origem).first()
            if not conta_origem_obj or conta_origem_obj.saldo < valor:
                saldo_suficiente = False
                break
        else:
            # Consulta o saldo no outro banco
            banco_urls = obter_tabela_roteamento()          
            url_origem = banco_urls[banco_origem]
            response = requests.get(f'{url_origem}/saldo', params={'agencia': agencia_origem, 'conta': conta_origem})
            if response.status_code != 200 or response.json().get('saldo', 0.0) < valor:
                saldo_suficiente = False
                break

    if not saldo_suficiente:
        return jsonify({'erro': 'Saldo insuficiente em uma ou mais contas de origem'}), 400

    # Descontar o valor das contas de origem e enviar a transferência
    for conta_info in contas_origem:
        banco_origem = conta_info['banco']
        agencia_origem = conta_info['agencia']
        conta_origem = conta_info['conta']
        valor = conta_info['valor']

        if banco_origem == BANCO_ID:
            lock_key = f"{agencia_origem}-{conta_origem}"
            if not acquire_lock(lock_key):
                return jsonify({'erro': 'A conta de origem está sendo usada em outra operação'}), 423

            try:
                conta_origem_obj = Conta.query.filter_by(agencia=agencia_origem, conta=conta_origem).first()
                conta_origem_obj.saldo -= valor
                db.session.commit()
            finally:
                release_lock(lock_key)
        else:
            banco_urls = obter_tabela_roteamento()
            url_origem = banco_urls[banco_origem]
            response = requests.post(f'{url_origem}/transferencia/pix/descontar', json={
                'agencia': agencia_origem,
                'conta': conta_origem,
                'valor': valor
            })
            if response.status_code != 200:
                return jsonify({'erro': f'Erro ao descontar saldo no banco {banco_origem}'}), response.status_code

    # Enviar a transferência para o banco destino
    banco_urls = obter_tabela_roteamento()
    url_destino = f"{banco_urls[banco_destino]}/transferencia/receber"
    dados_transferencia = {
        'tipo': 'PIX',
        'chave_pix_destino': chave_pix_destino,
        'valor': valor_total
    }
    response = requests.post(url_destino, json=dados_transferencia)

    if response.status_code == 200:
        return jsonify({'mensagem': 'Transferência PIX realizada com sucesso'}), 200
    else:
        # Em caso de falha na transferência, reverte o saldo descontado
        for conta_info in contas_origem:
            banco_origem = conta_info['banco']
            agencia_origem = conta_info['agencia']
            conta_origem = conta_info['conta']
            valor = conta_info['valor']

            if banco_origem == BANCO_ID:
                lock_key = f"{agencia_origem}-{conta_origem}"
                if acquire_lock(lock_key):  # Adicionar bloqueio ao reverter saldo
                    try:
                        conta_origem_obj = Conta.query.filter_by(agencia=agencia_origem, conta=conta_origem).first()
                        conta_origem_obj.saldo += valor
                        db.session.commit()
                    finally:
                        release_lock(lock_key)
            else:
                banco_urls = obter_tabela_roteamento()
                url_origem = banco_urls[banco_origem]
                requests.post(f'{url_origem}/transferencia/pix/reverter', json={
                    'agencia': agencia_origem,
                    'conta': conta_origem,
                    'valor': valor
                })
        return jsonify({'erro': 'Falha na transferência PIX para o banco destino'}), response.status_code






# Rota para descontar saldo em contas de outros bancos
@app.route('/transferencia/pix/descontar', methods=['POST'])
def descontar_saldo():
    dados = request.json
    agencia = dados['agencia']
    conta = dados['conta']
    valor = dados['valor']
    lock_key = f"{agencia}-{conta}"

    if not acquire_lock(lock_key):
        return jsonify({'erro': f'A conta {agencia}-{conta} está sendo usada em outra operação'}), 423

    try:
        conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
        if not conta_obj:
            return jsonify({'erro': 'Conta não encontrada'}), 404

        if conta_obj.saldo < valor:
            return jsonify({'erro': 'Saldo insuficiente'}), 400
        conta_obj.saldo -= valor
        db.session.commit()
    finally:
        release_lock(lock_key)
    return jsonify({'mensagem': 'Saldo descontado com sucesso'}), 200




# Rota para reverter saldo em caso de falha na transferência
@app.route('/transferencia/pix/reverter', methods=['POST'])
def reverter_saldo():
    dados = request.json
    agencia = dados['agencia']
    conta = dados['conta']
    valor = dados['valor']
    lock_key = f"{agencia}-{conta}"

    if not acquire_lock(lock_key):
        return jsonify({'erro': f'A conta {agencia}-{conta} está sendo usada em outra operação'}), 423

    try:
        conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
        if not conta_obj:
            return jsonify({'erro': 'Conta não encontrada'}), 404

        conta_obj.saldo += valor
        db.session.commit()
    finally:
        release_lock(lock_key)

    return jsonify({'mensagem': 'Saldo revertido com sucesso'}), 200






# Rota para buscar contas de todos os bancos
@app.route('/obter_contas_todos_bancos', methods=['GET'])
def obter_contas_todos_bancos():
    cpf_ou_cnpj = request.args.get('cpf_ou_cnpj')

    # Obtém o titular com o CPF/CNPJ fornecido no banco atual
    titular_obj = Titular.query.filter_by(cpf_ou_cnpj=cpf_ou_cnpj).first()
    if not titular_obj:
        return jsonify({'erro': 'Cliente não encontrado'}), 404

    # Lista para armazenar todas as contas (do banco atual e dos outros bancos)
    contas_local = []
    
    # Adiciona as contas do banco atual
    for conta in titular_obj.contas:
        contas_local.append({
            'banco': BANCO_ID,
            'agencia': conta.agencia,
            'conta': conta.conta,
            'saldo': conta.saldo
        })

    # Obter tabela de roteamento que contém URLs dos outros bancos
    banco_urls = obter_tabela_roteamento()
    
    # Faz uma chamada para cada banco na tabela de roteamento
    for banco_id, url in banco_urls.items():
        if banco_id != BANCO_ID:
            try:
                # Chama a rota /obter_contas do outro banco
                response = requests.get(f'{url}/obter_contas', params={'cpf_ou_cnpj': cpf_ou_cnpj})
                if response.status_code == 200:
                    # Adiciona as contas retornadas pelo outro banco
                    contas_banco = response.json().get('contas', [])
                    contas_local.extend(contas_banco)
                else:
                    print(f"Erro ao obter contas do banco {banco_id}: {response.json()}")
            except requests.RequestException as e:
                print(f"Erro ao obter contas do banco {banco_id}: {e}")

    # Retorna a lista combinada de contas
    return jsonify({'contas': contas_local}), 200

# Rota para obter contas do banco atual
@app.route('/obter_contas', methods=['GET'])
def obter_contas():
    cpf_ou_cnpj = request.args.get('cpf_ou_cnpj')

    # Obtém o titular com o CPF/CNPJ fornecido no banco atual
    titular_obj = Titular.query.filter_by(cpf_ou_cnpj=cpf_ou_cnpj).first()
    if not titular_obj:
        return jsonify({'erro': 'Cliente não encontrado'}), 404

    # Lista para armazenar as contas do banco atual
    contas_local = []
    
    # Adiciona as contas do banco atual
    for conta in titular_obj.contas:
        contas_local.append({
            'banco': BANCO_ID,
            'agencia': conta.agencia,
            'conta': conta.conta,
            'saldo': conta.saldo
        })

    # Retorna a lista de contas do banco atual
    return jsonify({'contas': contas_local}), 200




@app.route('/transferencia/pix/receber', methods=['POST'])
def receber_transferencia_pix():
    dados = request.json
    chave_pix_destino = dados['chave_pix_destino']
    valor = dados['valor']

    # Verifica se a chave PIX de destino existe e é válida
    conta_destino = Conta.query.filter(
        (Conta.chave_pix_cpf_cnpj == chave_pix_destino) | 
        (Conta.chave_pix_email == chave_pix_destino) | 
        (Conta.chave_pix_aleatoria == chave_pix_destino) | 
        (Conta.numero_celular == chave_pix_destino)
    ).first()

    if not conta_destino:
        return jsonify({'erro': 'Chave PIX de destino inválida'}), 400

    conta_destino.saldo += valor
    db.session.commit()

    return jsonify({'mensagem': 'Transferência PIX recebida com sucesso'}), 200



@app.route('/pix/cadastrar', methods=['POST'])
def cadastrar_chave_pix():
    dados = request.json
    agencia = dados['agencia']
    conta = dados['conta']
    chave_pix = dados['chave_pix']
    tipo_chave = dados['tipo_chave']

    conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
    if not conta_obj:
        return jsonify({'mensagem': 'Conta não encontrada'}), 404

    # Verificar se a chave PIX já existe no banco atual
    elif conta_obj.chave_pix_email == chave_pix:
        return jsonify({'mensagem': 'Chave PIX já cadastrada'}), 400
    elif conta_obj.chave_pix_aleatoria == chave_pix:
        return jsonify({'mensagem': 'Chave PIX já cadastrada'}), 400
    elif conta_obj.numero_celular == chave_pix:
        return jsonify({'mensagem': 'Chave PIX já cadastrada'}), 400

    # Obter a tabela de roteamento de bancos
    banco_urls = obter_tabela_roteamento()

    # Verificar em outros bancos conforme a tabela de roteamento
    for tipo_banco, endereco_api in banco_urls.items():
        # Montar a URL para fazer a requisição GET para verificar a chave PIX
        url_verificacao = f"{endereco_api}/pix/chave?chave_pix={chave_pix}"
        
        # Fazer a requisição GET para verificar se a chave PIX existe no outro banco
        try:
            response = requests.get(url_verificacao)
            if response.status_code == 200:
                resposta_json = response.json()
                if resposta_json.get('pertence', False):
                    return jsonify({'mensagem': f'Chave PIX já cadastrada no banco: {tipo_banco}'}), 400
        except requests.exceptions.RequestException as e:
            # Tratar erros de requisição, se necessário
            print(f"Erro ao tentar acessar {endereco_api}: {str(e)}")
            pass  # Você pode decidir o que fazer em caso de erro de requisição

    # Caso a chave PIX não exista no banco atual nem em outros bancos, cadastrar no banco atual
    if tipo_chave == 'Email':
        conta_obj.chave_pix_email = chave_pix
    elif tipo_chave == 'Aleatória':
        conta_obj.chave_pix_aleatoria = chave_pix
    elif tipo_chave == 'Telefone':
        conta_obj.numero_celular = chave_pix
    else:
        return jsonify({'mensagem': 'Tipo de chave PIX inválido'}), 400

    db.session.commit()
    return jsonify({'mensagem': 'Chave PIX cadastrada com sucesso'}), 200







@app.route('/pix/apagar', methods=['POST'])
def apagar_chave_pix():
    dados = request.json
    agencia = dados['agencia']
    conta = dados['conta']
    tipo_chave = dados['tipo_chave']

    conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
    if not conta_obj:
        return jsonify({'mensagem': 'Conta não encontrada'}), 404


    elif tipo_chave == 'Email':
        conta_obj.chave_pix_email = None
    elif tipo_chave == 'Aleatória':
        conta_obj.chave_pix_aleatoria = None
    elif tipo_chave == 'Telefone':
        conta_obj.numero_celular = None
    else:
        return jsonify({'mensagem': 'Chave PIX não encontrada ou tipo inválido'}), 400

    db.session.commit()
    return jsonify({'mensagem': 'Chave PIX apagada com sucesso'}), 200

@app.route('/pix/visualizar', methods=['GET'])
def visualizar_chaves_pix():
    agencia = request.args.get('agencia')
    conta = request.args.get('conta')

    conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
    if not conta_obj:
        return jsonify({'mensagem': 'Conta não encontrada'}), 404

    chaves_pix = {
        'Email': conta_obj.chave_pix_email,
        'Aleatória': conta_obj.chave_pix_aleatoria,
        'Telefone': conta_obj.numero_celular
    }

    # Filtrar chaves que não estão None
    chaves_pix_filtradas = {chave: valor for chave, valor in chaves_pix.items() if valor is not None}

    return jsonify({'chaves_pix': chaves_pix_filtradas}), 200

if __name__ == '__main__':
    app.run(port=PORT, host=IP, debug=True)
