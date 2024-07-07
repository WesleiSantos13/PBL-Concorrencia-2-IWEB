from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from threading import Lock
import socket
import requests
import random
import time
import os
from requests.exceptions import RequestException
import threading
from tabulate import tabulate


##### Servidor do Banco Picpay #######


# Configuração do banco de dados
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///picpay.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de dados
class Titular(db.Model): # Titular
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf_ou_cnpj = db.Column(db.String(14), unique=True, nullable=False)

# Relacionamento de titular e conta
conta_titular = db.Table('conta_titular',
    db.Column('conta_id', db.Integer, db.ForeignKey('conta.id'), primary_key=True),
    db.Column('titular_id', db.Integer, db.ForeignKey('titular.id'), primary_key=True)
)

# Conta
class Conta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agencia = db.Column(db.String(50), nullable=False)
    conta = db.Column(db.String(50), nullable=False, unique=True)
    senha = db.Column(db.String(50), nullable=False)
    saldo = db.Column(db.Float, default=0.0)
    chave_pix_email = db.Column(db.String(100), unique=True)
    chave_pix_aleatoria = db.Column(db.String(100), unique=True)
    numero_celular = db.Column(db.String(20), unique=True)
    tipo_conta = db.Column(db.String(3), nullable=False) 
    titulares = db.relationship('Titular', secondary=conta_titular, lazy='subquery',
        backref=db.backref('contas', lazy=True))
    
# Bloqueio
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
            # Tenta obter o lock para o recurso específico
            lock = Lock.query.filter_by(resource=resource).with_for_update(nowait=True).first()
            
            # Se o lock existe e não está bloqueado, bloqueia-o
            if lock and not lock.locked:
                lock.locked = True
                db.session.commit()
                return True
            # Se o lock não existe, cria um novo
            elif not lock:
                new_lock = Lock(resource=resource, locked=True)
                db.session.add(new_lock)
                db.session.commit()
                return True
        except SQLAlchemyError:
            db.session.rollback()  # Em caso de erro, faz rollback da transação
        time.sleep(0.1)  # Aguarda um curto período antes de tentar novamente
    return False  # Retorna False se o timeout for atingido sem conseguir o lock

# Função para liberar um bloqueio em um recurso específico
def release_lock(resource):
    try:
        # Busca pelo lock associado ao recurso
        lock = Lock.query.filter_by(resource=resource).first()
        
        # Se o lock existe e está bloqueado, libera-o
        if lock and lock.locked:
            lock.locked = False
            db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()  # Em caso de erro, faz rollback da transação





# Inicializa o banco de dados
with app.app_context():
    db.create_all()



# Configurações do banco
IP = socket.gethostbyname(socket.gethostname())
PORT = 9637
URL_SERVER = f'http://{IP}:{PORT}'
# Código do banco 
BANCO_ID = '380'


# URL de todos os bancos
bank_urls = {
    '237': 'http://'+os.getenv('IP_bradesco')+':9635',
    '536': 'http://'+os.getenv('IP_neon')+':9636'
}


# Gera uma agência única
def gerar_agencia():
    return f"{random.randint(4000, 4800)}"

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
        titulares_cpf = list(titulares_dados.keys())  # Pegar apenas os CPFs dos titulares

        for cpf, nome in titulares_dados.items():
            titular = Titular.query.filter_by(cpf_ou_cnpj=cpf).first()
            if not titular:
                titular = Titular(nome=nome, cpf_ou_cnpj=cpf)
                db.session.add(titular)
            else:
                # Verificar se os titulares já possuem conta conjunta juntos
                for conta_titular in titular.contas:
                    if conta_titular.tipo_conta == 'PFC' and set([t.cpf_ou_cnpj for t in conta_titular.titulares]) == set(titulares_cpf):
                        return jsonify({'erro': 'Titulares já possuem uma conta conjunta juntos'}), 400

            nova_conta.titulares.append(titular)

    else:  # Conta individual (PJ ou PFI)
        cpf_ou_cnpj = dados.get('cpf_ou_cnpj')
        nome = dados.get('nome')

        # Verificar se o CPF já possui registro em conta individual ou se o CNPJ já possui registro em uma conta jurídica
        titular_existente = Titular.query.filter_by(cpf_ou_cnpj=cpf_ou_cnpj).first()
        if titular_existente:
            # Se já possui conta individual
            if any(conta.tipo_conta == 'PFI' for conta in titular_existente.contas):
                return jsonify({'erro': f'O cliente com o CPF: ({cpf_ou_cnpj}) já possui uma conta individual'}), 400
            # Se o Cnpj possui registro em cota jurídica
            if any(conta.tipo_conta == 'PJ' for conta in titular_existente.contas):
                return jsonify({'erro': f'O CNPJ: ({cpf_ou_cnpj}) já possui registro em uma conta jurídica'}), 400

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

    # Se o valor a ser depositado estiver zerado ou negativo
    if valor <= 0:
        return jsonify({'erro': f'Você não pode depositar {valor} reais'}), 423

    # Se o depósito for para o mesmo banco de destino
    if banco_destino == BANCO_ID:
        # Filtrando conta
        conta_obj = Conta.query.filter_by(agencia=agencia_destino, conta=conta_destino).first()
        if not conta_obj:
            return jsonify({'erro': 'Conta de destino não encontrada'}), 404        

        lock_key_conta = f"{agencia_destino}-{conta_destino}"

        # Tenta adquirir o bloqueio para a conta de destino
        if not acquire_lock(lock_key_conta):
            return jsonify({'erro': 'A conta de destino está sendo usada em outra operação'}), 423

        try:
            conta_obj.saldo += valor
            db.session.commit()
            return jsonify({'mensagem': 'Depósito realizado com sucesso'}), 200
        finally:
            # Libera o bloqueio
            release_lock(lock_key_conta)

    # Se for para outro banco
    else:
        # Envia a transferência para o banco destino
        url_destino = f"{bank_urls[banco_destino]}/transferencia/receber"
        dados_transferencia = {"tipo": "DEP",'agencia_destino': agencia_destino,'conta_destino': conta_destino,'valor': valor,}

        try:
            response = requests.post(url_destino, json=dados_transferencia)
            data = response.json()
            if response.status_code == 200:
                return jsonify(data), 200
            else:
                return jsonify(data), response.status_code
        except RequestException:
            return jsonify({'erro': 'Falha na comunicação com o banco destino. Tente novamente mais tarde.'}), 503



# Rota para sacar valores da conta logada
@app.route('/sacar', methods=['POST'])
def sacar():
    dados = request.json
    agencia = dados.get('agencia')
    conta = dados.get('conta')
    valor = dados.get('valor')
    
    # Se o valor a ser sacado estiver zerado ou negativo
    if valor <= 0:
        return jsonify({'erro': f'Você não pode sacar {valor} reais'}), 423
    # Filtrando a conta
    conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
    if not conta_obj:
        return jsonify({'erro': 'Conta não encontrada'}), 404
    
    # Verificando se o saldo é suficiente
    if conta_obj.saldo < valor:
        return jsonify({'erro': 'Saldo insuficiente'}), 400    

    lock_key_conta = f"{agencia}-{conta}"
    
    # Tenta adquirir o bloqueio para a conta
    if not acquire_lock(lock_key_conta):
        return jsonify({'erro': 'A conta está sendo usada em outra operação'}), 423

    try:
        # Decrementa o saldo
        conta_obj.saldo -= valor
        db.session.commit()
        return jsonify({'mensagem': 'Saque realizado com sucesso'}), 200
    
    finally:
        # Libera o bloqueio
        release_lock(lock_key_conta)






# Rota para fazer login
@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    agencia = dados.get('agencia')
    conta = dados.get('conta')
    senha = dados.get('senha')
    cpf_ou_cnpj = dados.get('cpf_ou_cnpj')
    # Filtra a conta e o titular
    conta_obj = Conta.query.filter_by(conta=conta, agencia=agencia).first()
    titular_obj = Titular.query.filter_by(cpf_ou_cnpj=cpf_ou_cnpj).first()
    # Verifica as credenciais
    if conta_obj and conta_obj.senha == senha and titular_obj in conta_obj.titulares:
        return jsonify({'mensagem': 'Login bem-sucedido'}), 200
    else:
        return jsonify({'erro': 'Credenciais inválidas'}), 401


# Rota para ver o saldo da conta
@app.route('/saldo', methods=['GET'])
def saldo():
    agencia = request.args.get('agencia')
    conta = request.args.get('conta')
    # Filtra a conta atraves da agencia e conta
    conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
    if conta_obj:# Se a conta existe
        return jsonify({'saldo': conta_obj.saldo}), 200
    else:
        return jsonify({'erro': 'Cliente não encontrado'}), 404






# Rota para transferência ted
@app.route('/transferencia/ted/enviar', methods=['POST'])
def enviar_transferencia():
    dados = request.json
    agencia_origem = dados['agencia_origem']
    conta_origem = dados['conta_origem']
    agencia_destino = dados['agencia_destino']
    conta_destino = dados['conta_destino']
    valor = dados['valor']
    banco_destino = dados['banco_destino']

    # Se o valor a ser transferido estiver zerado ou negativo
    if valor <= 0:
        return jsonify({'erro': f'Você não pode transferir {valor} reais'}), 423

    # Filtra a conta
    conta_origem_obj = Conta.query.filter_by(agencia=agencia_origem, conta=conta_origem).first()
    # Se a conta não existir
    if not conta_origem_obj:
        return jsonify({'erro': 'Conta de origem não encontrada'}), 404

    # Tenta adquirir o bloqueio para a conta de origem
    lock_key_origem = f"{agencia_origem}-{conta_origem}"
    if not acquire_lock(lock_key_origem):
        return jsonify({'erro': 'A conta de origem está sendo usada em outra operação'}), 423

    try:
        # Se a transferência for para o mesmo banco de destino
        if banco_destino == BANCO_ID:
            conta_destino_obj = Conta.query.filter_by(agencia=agencia_destino, conta=conta_destino).first()
            # se a conta de destino não existir
            if not conta_destino_obj:
                return jsonify({'erro': 'Conta de destino não encontrada'}), 404
            # Se a transferência for para a mesma conta
            if conta_origem_obj == conta_destino_obj:
                return jsonify({'erro': 'Não é possível transferir para a mesma conta'}), 400
            # Verificando saldo
            if conta_origem_obj.saldo < valor:
                return jsonify({'erro': 'Saldo insuficiente'}), 400

            # Tenta adquirir o bloqueio para a conta de destino
            lock_key_destino = f"{agencia_destino}-{conta_destino}"
            if not acquire_lock(lock_key_destino):
                return jsonify({'erro': 'A conta de destino está sendo usada em outra operação'}), 423

            try:
                # Desconta o valor e incrementa em outra conta
                conta_origem_obj.saldo -= valor
                conta_destino_obj.saldo += valor
                db.session.commit()
                return jsonify({'mensagem': 'Transferência realizada com sucesso'}), 200
            finally:
                # Libera o bloqueio
                release_lock(lock_key_destino)
        
        # Se a transferência for para outro banco
        else:
            # Verifica o saldo
            if conta_origem_obj.saldo < valor:
                return jsonify({'erro': 'Saldo insuficiente'}), 400

            try:
                # Envia a transferência para o banco destino
                url_destino = f"{bank_urls[banco_destino]}/transferencia/receber"
                dados_transferencia = {
                    'tipo': 'TED',
                    'agencia_destino': agencia_destino,
                    'conta_destino': conta_destino,
                    'valor': valor
                }
                response = requests.post(url_destino, json=dados_transferencia)
                data = response.json()

                if response.status_code == 200:
                    # Desconta o valor
                    conta_origem_obj.saldo -= valor
                    db.session.commit()
                    return jsonify(data), 200
                else:
                    return jsonify(data), 404
            except RequestException:
                return jsonify({'erro': 'Falha na comunicação com o banco destino. Tente novamente mais tarde.'}), 503
    finally:
        # Libera o bloqueio
        release_lock(lock_key_origem)




# Rota para receber depósitos, transferências ted e pix
@app.route('/transferencia/receber', methods=['POST'])
def receber_transferencia():
    dados = request.json
    tipo = dados['tipo']
    valor = dados['valor']
    
    # Se for do tipo pix
    if tipo == 'PIX':
        chave_pix_destino = dados['chave_pix_destino']

        # Verifica se a chave PIX de destino existe e é válida
        conta_destino_obj = Conta.query.filter((Conta.chave_pix_email == chave_pix_destino) |(Conta.chave_pix_aleatoria == chave_pix_destino) | (Conta.numero_celular == chave_pix_destino)).first()
        # Se a chave pix não existe
        if not conta_destino_obj:
            return jsonify({'erro': 'Chave PIX de destino inválida'}), 400
        
        lock_key = f"{conta_destino_obj.agencia}-{conta_destino_obj.conta}"

    # Se for transferencia ted, deposito ou reversão de saldo de outro banco.
    elif tipo == 'TED' or tipo == 'DEP' or tipo == 'REVERT':
        agencia_destino = dados['agencia_destino']
        conta_destino = dados['conta_destino']
        # Filtra a conta
        conta_destino_obj = Conta.query.filter_by(agencia=agencia_destino, conta=conta_destino).first()
        # Se a conta não existir
        if not conta_destino_obj:
            return jsonify({'erro': 'Conta de destino não encontrada'}), 404

        lock_key = f"{agencia_destino}-{conta_destino}"
    else:
        return jsonify({'erro': 'Tipo de transferência inválido'}), 400

    # Tenta adquirir o bloqueio para a conta de destino
    if not acquire_lock(lock_key):
        return jsonify({'erro': 'A conta de destino está sendo usada em outra operação'}), 423

    try:
        conta_destino_obj.saldo += valor
        db.session.commit()
        if tipo == 'DEP':
            return jsonify({'mensagem': f'Deposito enviado com sucesso para banco {BANCO_ID}'}), 200
        elif tipo == 'REVERT':
            return jsonify({'mensagem': f'Saldo revertido com sucesso para o banco {BANCO_ID}'}), 200
        else:
            return jsonify({'mensagem': f'Transferência enviada com sucesso para o banco {BANCO_ID}'}), 200

    finally:
        # Libera o bloqueio
        release_lock(lock_key)





# Rota para que outros bancos possam saber se uma chave pix já está cadastrada
@app.route('/pix/chave', methods=['GET'])
def verificar_chave_pix():
    chave_pix = request.args.get('chave_pix')
    conta = Conta.query.filter(
        (Conta.chave_pix_email == chave_pix) | 
        (Conta.chave_pix_aleatoria == chave_pix) | 
        (Conta.numero_celular == chave_pix)
    ).first()
    if conta:
        return jsonify({'pertence': True}), 200
    else:
        return jsonify({'pertence': False}), 200
    

# Função para identificar o banco através da chave pix
def identificar_banco_destino(chave_pix):
    # Verifica se a chave Pix pertence a alguma conta no banco local
    conta_local = Conta.query.filter(
        (Conta.chave_pix_email == chave_pix) | (Conta.chave_pix_aleatoria == chave_pix) |(Conta.numero_celular == chave_pix)).first()

    if conta_local:
        return BANCO_ID
    
    # Se não encontrar no banco local, consulta outros bancos
    for banco_id, url in bank_urls.items():
        response = requests.get(f'{url}/pix/chave', params={'chave_pix': chave_pix})
        if response.status_code == 200:
            if response.json().get('pertence'):
                return banco_id
    
    return None




# Rota para transferencia pix, para transferir dinheiro de n contas de origem para 1
@app.route('/transferencia/pix/enviar', methods=['POST'])
def enviar_transferencia_pix():
    dados = request.json
    chave_pix_destino = dados['chave_pix_destino']
    contas_origem = dados['contas_origem']  # Lista de dicionários com agência, conta e valor a ser transferido de cada conta
    valor_total = sum(conta['valor'] for conta in contas_origem)
    
    # Se o valor da transferência for menor ou igual a 0, não deve existir transferência
    if valor_total <= 0:
        return jsonify({'erro': 'Valor a transferir zerado ou negativo'}), 404
    
    # Identificar o banco destino baseado na chave PIX
    banco_destino = identificar_banco_destino(chave_pix_destino)

    if not banco_destino:
        return jsonify({'erro': 'Chave PIX de destino não encontrada em nenhum banco'}), 404

    saldo_suficiente = True
    contas_descontadas = []

    # Iterando sobre cada conta origem para verificar o saldo e atualizar
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
            url_origem = bank_urls[banco_origem]
            try:
                response = requests.get(f'{url_origem}/saldo', params={'agencia': agencia_origem, 'conta': conta_origem})
                if response.json().get('saldo', 0.0) < valor:
                    saldo_suficiente = False
                    break
            except RequestException:
                print(f"Erro ao verificar saldo no banco {banco_origem}")
                return jsonify({'erro': f'Erro ao verificar saldo no banco {banco_origem}.'}), 503

    if not saldo_suficiente:
        return jsonify({'erro': 'Saldo insuficiente em uma ou mais contas de origem'}), 400

    # Descontar o valor das contas de origem e enviar a transferência
    for conta_info in contas_origem:
        banco_origem = conta_info['banco']
        agencia_origem = conta_info['agencia']
        conta_origem = conta_info['conta']
        valor = conta_info['valor']
        
        # Se for o mesmo banco de origem
        if banco_origem == BANCO_ID:
            # Tenta adquirir o bloqueio para a conta de origem
            lock_key = f"{agencia_origem}-{conta_origem}"
            if not acquire_lock(lock_key):
                return jsonify({'erro': 'A conta de origem está sendo usada em outra operação'}), 423

            try:
                # Desconta no banco atual
                conta_origem_obj = Conta.query.filter_by(agencia=agencia_origem, conta=conta_origem).first()
                conta_origem_obj.saldo -= valor
                db.session.commit()
                contas_descontadas.append((banco_origem, agencia_origem, conta_origem, valor))
            finally:
                # Libera o bloqueio
                release_lock(lock_key)
        # Descontar os valores correspondentes a outros bancos
        else:
            url_origem = bank_urls[banco_origem]
            try:
                response = requests.post(f'{url_origem}/transferencia/pix/descontar', json={
                    'agencia': agencia_origem,
                    'conta': conta_origem,
                    'valor': valor
                })
                if response.status_code == 200:
                    contas_descontadas.append((banco_origem, agencia_origem, conta_origem, valor))
                else:
                    raise RequestException
            except RequestException:
                print(f"Erro ao descontar saldo no banco {banco_origem}")
                # Reverter os saldos descontados em caso de erro
                for banco, agencia, conta, valor in contas_descontadas:
                    if banco == BANCO_ID:
                        lock_key = f"{agencia}-{conta}"
                        if acquire_lock(lock_key):
                            try:
                                conta_origem_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
                                conta_origem_obj.saldo += valor
                                db.session.commit()
                            finally:
                                release_lock(lock_key)
                    else:
                        url_origem = bank_urls[banco]
                        try:
                            requests.post(f'{url_origem}/transferencia/receber', json={
                                'tipo': 'REVERT',
                                'agencia_destino': agencia,
                                'conta_destino': conta,
                                'valor': valor
                            })
                        except RequestException:
                            print(f"Erro ao reverter saldo no banco {banco}")
                return jsonify({'erro': f'Erro ao descontar saldo no banco {banco_origem}.'}), 503

    # Enviar a transferência para o banco destino
    if banco_destino == BANCO_ID:
        # Transação local
        conta_destino_obj = Conta.query.filter(
            (Conta.chave_pix_email == chave_pix_destino) |(Conta.chave_pix_aleatoria == chave_pix_destino) | (Conta.numero_celular == chave_pix_destino)).first()
        if not conta_destino_obj:
            return jsonify({'erro': 'Conta de destino não encontrada no banco atual'}), 404

        # Tenta adquirir o bloqueio para a conta de destino
        lock_key = f"{conta_destino_obj.agencia}-{conta_destino_obj.conta}"
        if not acquire_lock(lock_key):
            return jsonify({'erro': 'A conta de destino está sendo usada em outra operação'}), 423

        try:
            conta_destino_obj.saldo += valor_total
            db.session.commit()
        finally:
            # Libera o bloqueio
            release_lock(lock_key)
    else:
        # Transação para outro banco
        url_destino = f"{bank_urls[banco_destino]}/transferencia/receber"
        dados_transferencia = {
            'tipo': 'PIX',
            'chave_pix_destino': chave_pix_destino,
            'valor': valor_total
        }
        try:
            response = requests.post(url_destino, json=dados_transferencia)
            if response.status_code != 200:
                data = response.json()
                raise RequestException(data)
        except RequestException as e:
            print(f"Erro ao enviar transferência para o banco destino: {str(e)}")
            # Em caso de falha na transferência, reverte o saldo descontado
            for banco, agencia, conta, valor in contas_descontadas:
                if banco == BANCO_ID:
                    lock_key = f"{agencia}-{conta}"
                    if acquire_lock(lock_key):  
                        try:
                            conta_origem_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
                            conta_origem_obj.saldo += valor # Devolve o valor
                            db.session.commit()
                        finally:
                            release_lock(lock_key)
                else:
                    url_origem = bank_urls[banco]
                    try:
                        requests.post(f'{url_origem}/transferencia/receber', json={
                            'tipo': 'REVERT',
                            'agencia_destino': agencia,
                            'conta_destino': conta,
                            'valor': valor
                        })
                    except RequestException:
                        print(f"Erro ao reverter saldo no banco {banco}")
            return jsonify({'erro': 'Falha na transferência PIX para o banco destino'}), 503

    return jsonify({'mensagem': 'Transferência PIX realizada com sucesso'}), 200



# Rota para descontar saldo em contas
@app.route('/transferencia/pix/descontar', methods=['POST'])
def descontar_saldo():
    dados = request.json
    agencia = dados['agencia']
    conta = dados['conta']
    valor = dados['valor']
    
    # Filtra a conta
    conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
    if not conta_obj:
        return jsonify({'erro': 'Conta não encontrada'}), 404
    # Verifica saldo
    if conta_obj.saldo < valor:
        return jsonify({'erro': 'Saldo insuficiente'}), 400

    # Tenta adquirir o bloqueio da conta 
    lock_key = f"{agencia}-{conta}"
    if not acquire_lock(lock_key):
        return jsonify({'erro': f'A conta {agencia}-{conta} está sendo usada em outra operação'}), 423

    try:
        conta_obj.saldo -= valor # desconta
        db.session.commit()
        return jsonify({'mensagem': 'Saldo descontado com sucesso'}), 200
    finally:
        # Libera o bloqueio
        release_lock(lock_key)




# Rota para buscar contas de um mesmo titular em todos os bancos
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
    
    # Faz uma chamada para cada banco
    for banco_id, url in bank_urls.items():
        try:
            # Chama a rota /obter_contas do outro banco
            response = requests.get(f'{url}/obter_contas', params={'cpf_ou_cnpj': cpf_ou_cnpj})
            # Adiciona as contas retornadas pelo outro banco
            contas_banco = response.json().get('contas', [])
            contas_local.extend(contas_banco)
        except RequestException:
            print(f"Erro ao obter contas do banco {banco_id}, pois ele está fora do ar.")
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






# Rota para cadastrar chave pix
@app.route('/pix/cadastrar', methods=['POST'])
def cadastrar_chave_pix():
    dados = request.json
    agencia = dados['agencia']
    conta = dados['conta']
    chave_pix = dados['chave_pix']
    tipo_chave = dados['tipo_chave']

    # Filtra a conta
    conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
    if not conta_obj:
        return jsonify({'mensagem': 'Conta não encontrada'}), 404

    # Verificar se a chave PIX já existe no banco atual em qualquer conta
    chave_existente = Conta.query.filter(
        (Conta.chave_pix_email == chave_pix) | (Conta.chave_pix_aleatoria == chave_pix) |(Conta.numero_celular == chave_pix) ).first()

    if chave_existente:
        return jsonify({'mensagem': 'Chave PIX já cadastrada'}), 400


    # Verificar em outros bancos
    for cod_banco, endereco_api in bank_urls.items():
        try:
            # Montar a URL para fazer a requisição GET para verificar a chave PIX
            url_verificacao = f"{endereco_api}/pix/chave?chave_pix={chave_pix}"
            # Fazer a requisição GET para verificar se a chave PIX existe no outro banco
            response = requests.get(url_verificacao)
            resposta_json = response.json()
            if resposta_json.get('pertence', False):
                return jsonify({'mensagem': f'Chave PIX já cadastrada no banco: {cod_banco}'}), 400
        except RequestException:
            print(f"Erro ao verificar chave PIX no banco {cod_banco}")
            return jsonify({'mensagem': 'Erro ao verificar chave PIX em outros bancos. Tente novamente mais tarde.'}), 503

    # Caso a chave PIX não exista no banco atual nem em outros bancos, cadastrar no banco atual
    if tipo_chave == 'Email':
        conta_obj.chave_pix_email = chave_pix
    elif tipo_chave == 'Aleatória':
        conta_obj.chave_pix_aleatoria = chave_pix
    elif tipo_chave == 'Telefone':
        conta_obj.numero_celular = chave_pix
    
    db.session.commit()
    return jsonify({'mensagem': 'Chave PIX cadastrada com sucesso'}), 200







# Rota para apagar chave pix
@app.route('/pix/apagar', methods=['POST'])
def apagar_chave_pix():
    dados = request.json
    agencia = dados['agencia']
    conta = dados['conta']
    tipo_chave = dados['tipo_chave']
    # Filtra a conta
    conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
    if not conta_obj:
        return jsonify({'mensagem': 'Conta não encontrada'}), 404
    # Deixa com valor none a chave a ser apagada
    elif tipo_chave == 'Email':
        conta_obj.chave_pix_email = None
    elif tipo_chave == 'Aleatória':
        conta_obj.chave_pix_aleatoria = None
    elif tipo_chave == 'Telefone':
        conta_obj.numero_celular = None

    db.session.commit()
    return jsonify({'mensagem': 'Chave PIX apagada com sucesso'}), 200



# Rota para visualizar as chaves pix registradas
@app.route('/pix/visualizar', methods=['GET'])
def visualizar_chaves_pix():
    agencia = request.args.get('agencia')
    conta = request.args.get('conta')
    # Filtra a conta
    conta_obj = Conta.query.filter_by(agencia=agencia, conta=conta).first()
    if not conta_obj:
        return jsonify({'mensagem': 'Conta não encontrada'}), 404
    # Seleciona os tipos de chave
    chaves_pix = {'Email': conta_obj.chave_pix_email,'Aleatória': conta_obj.chave_pix_aleatoria,'Telefone': conta_obj.numero_celular}
    # Filtrar chaves que não estão None
    chaves_pix_filtradas = {chave: valor for chave, valor in chaves_pix.items() if valor is not None}
    return jsonify({'chaves_pix': chaves_pix_filtradas}), 200




# Função para exibir o banco de dados periodicamente
def ver_database(intervalo):
    while True:
        with app.app_context():
            try:
                contas = Conta.query.all()

                # Preparando os dados para formatação em tabela
                table_data = []
                for conta in contas:
                    titulares_info = []
                    for titular in conta.titulares:
                        titular_info = f"{titular.nome} ({titular.cpf_ou_cnpj})"
                        titulares_info.append(titular_info)
                    titulares_str = ', '.join(titulares_info)
                    table_data.append([conta.id, conta.agencia, conta.conta, conta.saldo, titulares_str, conta.tipo_conta])

                # Exibindo os dados em formato de tabela
                headers = ['ID', 'Agência', 'Conta', 'Saldo', 'Titulares', 'Tipo de conta']
                print(tabulate(table_data, headers=headers))

                # Esperando o intervalo especificado em segundos
                time.sleep(intervalo)
            except SQLAlchemyError as e:
                print({'error': str(e)})
                time.sleep(intervalo)

                
if __name__ == '__main__':
    # Criando uma thread para executar ver_database
    thread = threading.Thread(target=ver_database, args=(10,))
    thread.start()
 
    # Executando o servidor Flask na thread principal
    app.run(port=PORT, host=IP, debug=True)
