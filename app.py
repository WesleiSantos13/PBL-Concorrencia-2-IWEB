from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import os
import socket
from requests.exceptions import RequestException


# Aplicação responsável pela interface

app = Flask(__name__)

app.secret_key = 'chave_secreta'  

# Rotas dos bancos
bank_urls = {
    'bradesco': 'http://'+os.getenv('IP_bradesco')+':9635',
    'neon': 'http://'+os.getenv('IP_neon')+':9636',
    'picpay': 'http://'+os.getenv('IP_picpay')+':9637'
}

# Rota para a tela inial (index)
@app.route('/')
def index():
    return render_template('index.html')


# Rota para a tela de login
@app.route('/<bank>/login', methods=['GET', 'POST'])
def login(bank):
    # Obtém a URL base do banco a partir do dicionário banco_urls
    base_url = bank_urls.get(bank)

    # Se o método da requisição for POST, trata o envio do formulário
    if request.method == 'POST':
        # Obtém os dados do formulário de login
        agencia = request.form['agencia']
        conta = request.form['conta']
        senha = request.form['senha']
        cpf_ou_cnpj = request.form['cpf_ou_cnpj']

        try:
            # Envia os dados do formulário para a API de login do banco
            response = requests.post(f'{base_url}/login', json={
                'agencia': agencia,
                'conta': conta,
                'senha': senha,
                'cpf_ou_cnpj': cpf_ou_cnpj
            })

            # Se o login foi bem-sucedido
            if response.status_code == 200:
                # Armazena os dados da sessão
                session['agencia'] = agencia
                session['conta'] = conta
                session['bank'] = bank
                session['cpf_ou_cnpj'] = cpf_ou_cnpj
                # Exibe uma mensagem de sucesso
                flash('Login realizado com sucesso!', 'success')
                # Redireciona para o painel de controle
                return redirect(url_for('dashboard', bank=bank))
            else:
                # Exibe uma mensagem de erro caso as credenciais sejam inválidas
                flash('Falha no login. Verifique suas credenciais.', 'error')

        except RequestException:
            # Trata erros de requisição
            flash(f'Erro ao conectar com o banco {bank}', 'error')

        # Redireciona de volta para a página de login
        return redirect(url_for('login', bank=bank))

    # Renderiza a página de login para requisições GET
    return render_template('login.html', bank=bank)






# Rota para a tela de criar uma conta
@app.route('/<bank>/criar_conta', methods=['GET', 'POST'])
def criar_conta(bank):
    # Obtém a URL base do banco a partir do dicionário bank_urls
    base_url = bank_urls.get(bank)

    # Se o método da requisição for POST, trata o envio do formulário de criação de conta
    if request.method == 'POST':
        tipo_conta = request.form['tipo_conta']

        try:
            # Criação de conta PFI (Pessoa Física Individual)
            if tipo_conta == 'PFI':
                nome = request.form['nome']
                cpf_ou_cnpj = request.form['cpf_cnpj']
                senha = request.form['senha']

                # Envia os dados para a API de criação de conta do banco
                response = requests.post(f'{base_url}/criar_conta', json={
                    'nome': nome,
                    'cpf_ou_cnpj': cpf_ou_cnpj,
                    'senha': senha,
                    'tipo_conta': 'PFI'
                })

            # Criação de conta PFC (Pessoa Física Conjunta)
            elif tipo_conta == 'PFC':
                quantidade_titulares = int(request.form['quantidade_titulares'])
                titulares = {}
                for i in range(1, quantidade_titulares + 1):
                    nome = request.form[f'nome_titular{i}']
                    cpf = request.form[f'cpf_cnpj_titular{i}']
                    titulares[cpf] = nome
                senha = request.form['senha_conjunta']

                # Envia os dados para a API de criação de conta do banco
                response = requests.post(f'{base_url}/criar_conta', json={
                    'titulares': titulares,
                    'senha': senha,
                    'tipo_conta': 'PFC'
                })

            # Criação de conta PJ (Pessoa Jurídica)
            elif tipo_conta == 'PJ':
                razao_social = request.form['razao_social']
                cnpj = request.form['cnpj']
                senha = request.form['senha_juridica']

                # Envia os dados para a API de criação de conta do banco
                response = requests.post(f'{base_url}/criar_conta', json={
                    'nome': razao_social,
                    'cpf_ou_cnpj': cnpj,
                    'senha': senha,
                    'tipo_conta': 'PJ'
                })

            # Verifica a resposta da API de criação de conta
            if response.status_code == 200:
                data = response.json()
                flash(f'{data["mensagem"]}, Agência: {data["agencia"]}, Conta: {data["conta"]}', 'success')
            else:
                data = response.json()
                flash(data['erro'], 'error')

        except RequestException:
            # Trata erros de requisição http
            flash(f'Erro ao conectar com o banco {bank}', 'error')

        # Redireciona para a mesma página após o envio do formulário
        return redirect(url_for('criar_conta', bank=bank))

    # Renderiza a página de criação de conta para requisições GET
    return render_template('criar_conta.html', bank=bank)




# Rota para a tela de realizar depósito
@app.route('/<bank>/deposito', methods=['GET', 'POST'])
def deposito(bank):
    # Obtém a URL base do banco a partir do dicionário bank_urls
    base_url = bank_urls.get(bank)

    # Se o método da requisição for POST, trata o envio do formulário de depósito
    if request.method == 'POST':
        agencia = request.form['agencia']
        conta = request.form['conta']
        valor = float(request.form['valor'])
        banco_destino = request.form['banco_destino']

        # Monta os dados do depósito a serem enviados para a API do banco
        dados = {
            'agencia': agencia,
            'conta': conta,
            'valor': valor,
            'banco_destino': banco_destino
        }

        try:
            # Envia os dados para a API de depósito do banco
            response = requests.post(f'{base_url}/depositar', json=dados)
            data = response.json()
            # Verifica a resposta da API de depósito
            if response.status_code == 200:
                flash(data['mensagem'], 'success')
            else:
                flash(data['erro'], 'error')
        except RequestException:
            # Trata exceções de requisições HTTP
            flash(f'Erro ao conectar com o banco {bank}', 'error')

        # Redireciona para a mesma página após o envio do formulário
        return redirect(url_for('deposito', bank=bank))

    # Renderiza a página de depósito para requisições GET
    return render_template('deposito.html', bank=bank)





# Rota para a tela de dashboard
@app.route('/<bank>/dashboard')
def dashboard(bank):
    # Obtém a URL base do banco a partir do dicionário bank_urls
    base_url = bank_urls.get(bank)
       
    # Obtém a agência e a conta da sessão do usuário
    agencia = session.get('agencia')
    conta = session.get('conta')

    try:
        # Faz uma requisição GET para a API do banco para obter o saldo da conta
        response = requests.get(f'{base_url}/saldo', params={
            'agencia': agencia,
            'conta': conta
        })

        # Verifica se a resposta da API foi bem-sucedida
        if response.status_code == 200:
            # Obtém o saldo da resposta JSON
            saldo = response.json().get('saldo', 0)
        else:
            # Em caso de erro, define uma mensagem de erro para o saldo
            saldo = 'Erro ao obter saldo'
    except RequestException:
        # Trata exceções de requisições HTTP
        saldo = f'Erro ao conectar com o banco {bank}'

    # Renderiza a página de dashboard com o saldo obtido
    return render_template('dashboard.html', bank=bank, saldo=saldo)







# Rota para a tela de transferência TED
@app.route('/<bank>/transferencia_ted', methods=['GET', 'POST'])
def transferencia_ted(bank):
    # Obtém a URL base do banco a partir do dicionário bank_urls
    base_url = bank_urls.get(bank)

    # Obtém a agência e a conta de origem da sessão do usuário
    agencia_origem = session.get('agencia')
    conta_origem = session.get('conta')

    try:
        # Faz uma requisição GET para a API do banco para obter o saldo da conta de origem
        response = requests.get(f'{base_url}/saldo', params={'agencia': agencia_origem, 'conta': conta_origem})

        # Verifica se a resposta da API foi bem-sucedida
        if response.status_code == 200:
            # Obtém o saldo da resposta JSON
            saldo = response.json().get('saldo', 0)
        else:
            # Em caso de erro, define uma mensagem de erro para o saldo
            saldo = 'Erro ao obter saldo'
    except RequestException:
        # Trata exceções de requisições HTTP
        saldo = f'Erro ao conectar com o banco {bank}'

    # Verifica se o método da requisição é POST
    if request.method == 'POST':
        # Obtém os dados do formulário
        agencia_destino = request.form['agencia_destino']
        conta_destino = request.form['conta_destino']
        valor = float(request.form['valor'])
        banco_destino = request.form['banco_destino']

        # Monta o dicionário de dados para a requisição POST
        dados = {
            'agencia_origem': agencia_origem,
            'conta_origem': conta_origem,
            'agencia_destino': agencia_destino,
            'conta_destino': conta_destino,
            'valor': valor,
            'banco_destino': banco_destino
        }

        try:
            # Faz uma requisição POST para a API do banco para enviar a transferência TED
            response = requests.post(f'{base_url}/transferencia/ted/enviar', json=dados)
            data = response.json()

            # Verifica se a resposta da API foi bem-sucedida
            if response.status_code == 200:
                # Exibe uma mensagem de sucesso
                flash(f'{data["mensagem"]}', 'success')
            else:
                # Exibe uma mensagem de erro
                flash(f'{data["erro"]}', 'error')
        except RequestException:
            # Trata exceções de requisições HTTP
            flash(f'Erro ao conectar com o banco {bank}', 'error')

        # Redireciona para a página de transferência TED
        return redirect(url_for('transferencia_ted', bank=bank))

    # Renderiza a página de transferência TED com o saldo obtido
    return render_template('transferencia_ted.html', bank=bank, saldo=saldo)




# Função para obter as contas vinculadas a um cpf ou cnpj
def obter_contas_vinculadas(cpf_ou_cnpj, bank):
    # Faz uma requisição GET para obter as contas vinculadas a um CPF/CNPJ em um banco específico
    response = requests.get(f'{bank_urls.get(bank)}/obter_contas_todos_bancos', params={'cpf_ou_cnpj': cpf_ou_cnpj})
    # Verifica se a resposta da requisição não foi bem-sucedida (status diferente de 200)
    if response.status_code != 200:
        # Retorna None para contas e o conteúdo da resposta em formato JSON para detalhes do erro
        return None, response.json()  
    # Obtém a lista de contas a partir da resposta JSON
    contas = response.json().get('contas', [])
    # Retorna a lista de contas e None para indicar que não houve erro
    return contas, None


# Rota para tela de transferência pix
@app.route('/<bank>/transferencia_pix', methods=['GET', 'POST'])
def transferencia_pix(bank):
    # Obtém a URL base do banco a partir do dicionário bank_urls
    base_url = bank_urls.get(bank)

    # Verifica se o método da requisição é POST
    if request.method == 'POST':
        chave_pix_destino = request.form['chave_pix_destino']
        contas_origem = []

        # Coleta as informações das contas de origem e os valores a serem transferidos
        for conta in request.form.getlist('contas_origem'):
            banco, agencia, conta_num, saldo = conta.split(',')
            valor = request.form.get(f'valor_{banco}_{agencia}_{conta_num}')
            if valor and float(valor) > 0:
                contas_origem.append({'banco': banco, 'agencia': agencia, 'conta': conta_num, 'valor': float(valor)})

        dados = {'chave_pix_destino': chave_pix_destino, 'contas_origem': contas_origem}

        try:
            # Faz uma requisição POST para enviar a transferência PIX
            response = requests.post(f'{base_url}/transferencia/pix/enviar', json=dados)
            data = response.json()
            if response.status_code == 200:
                flash(data['mensagem'], 'success')
            else:
                flash(data['erro'], 'error')
        except RequestException:
            # Trata exceções de requisições HTTP, exibindo uma mensagem de erro
            flash(f'Erro ao conectar com os bancos', 'error')

        return redirect(url_for('transferencia_pix', bank=bank))

    # Obtém o CPF/CNPJ do usuário da sessão
    cpf_ou_cnpj = session.get('cpf_ou_cnpj')

    try:
        # Obtém as contas vinculadas ao CPF/CNPJ
        contas, erro = obter_contas_vinculadas(cpf_ou_cnpj, bank)
        if erro:
            flash('Erro ao obter contas', 'error')
            return redirect(url_for('dashboard', bank=bank))
    except RequestException:
        # Trata exceções de requisições HTTP
        flash(f'Erro ao conectar com o banco', 'error')
        return redirect(url_for('dashboard', bank=bank))

    # Renderiza a página de transferência PIX com as contas vinculadas
    return render_template('transferencia_pix.html', bank=bank, contas=contas)




# Rota para a tela de saque
@app.route('/<bank>/sacar', methods=['GET', 'POST'])
def sacar(bank):
    # Obtém a URL base do banco a partir do dicionário bank_urls
    base_url = bank_urls.get(bank)

    # Obtém a agência e conta da sessão do usuário
    agencia = session.get('agencia')
    conta = session.get('conta')

    try:
        # Obtém o saldo da conta do usuário
        response = requests.get(f'{base_url}/saldo', params={'agencia': agencia, 'conta': conta})
        if response.status_code == 200:
            saldo = response.json().get('saldo', 0)
        else:
            saldo = 'Erro ao obter saldo'
    except RequestException:
        # Trata exceções de requisições HTTP
        saldo = 'Erro ao conectar com o banco'

    if request.method == 'POST':
        valor = float(request.form['valor'])

        try:
            # Faz uma requisição POST para realizar o saque
            response = requests.post(f'{base_url}/sacar', json={'agencia': agencia, 'conta': conta, 'valor': valor})
            data = response.json()
            if response.status_code == 200:
                flash(data['mensagem'], 'success')
            else:
                flash(data['erro'], 'error')
        except RequestException:
            # Trata exceções de requisições HTTP
            flash(f'Erro ao conectar com o banco {bank}', 'error')

        return redirect(url_for('sacar', bank=bank))

    # Renderiza a página de saque com o saldo atual da conta
    return render_template('sacar.html', bank=bank, saldo=saldo)



# Rota para tela de visualização das chaves PIX
@app.route('/<bank>/minhas_chaves_pix', methods=['GET'])
def minhas_chaves_pix(bank):
    # Obtém a URL base do banco a partir do dicionário bank_urls
    base_url = bank_urls.get(bank)

    # Obtém a agência e conta da sessão do usuário
    agencia = session.get('agencia')
    conta = session.get('conta')

    try:
        # Faz uma requisição GET para visualizar as chaves PIX associadas à conta
        response = requests.get(f'{base_url}/pix/visualizar', params={'agencia': agencia, 'conta': conta})
        if response.status_code == 200:
            chaves_pix = response.json().get('chaves_pix', {})
        else:
            chaves_pix = {}
            flash('Erro ao visualizar chaves PIX.', 'error')
    except RequestException:
        # Trata exceções de requisições HTTP
        chaves_pix = {}
        flash(f'Erro ao conectar com o banco {bank}', 'error')

    # Renderiza a página de visualização de chaves PIX com as chaves obtidas
    return render_template('minhas_chaves_pix.html', bank=bank, chaves=chaves_pix)




# Rota para cadastrar chave PIX na tela de minhas chaves PIX
@app.route('/<bank>/cadastrar_chave_pix', methods=['POST'])
def cadastrar_chave_pix(bank):
    # Obtém a URL base do banco a partir do dicionário bank_urls
    base_url = bank_urls.get(bank)

    # Obtém a agência e a conta da sessão do usuário
    agencia = session.get('agencia')
    conta = session.get('conta')

    # Obtém o tipo de chave e o valor da chave do formulário de solicitação
    tipo_chave = request.form['tipo_chave']
    chave_pix = request.form['valor_chave']

    # Dados a serem enviados na requisição POST
    dados = {'agencia': agencia, 'conta': conta, 'chave_pix': chave_pix, 'tipo_chave': tipo_chave}

    try:
        # Faz uma requisição POST para cadastrar a chave PIX
        response = requests.post(f'{base_url}/pix/cadastrar', json=dados)
        data = response.json()

        # Se a requisição for bem-sucedida, exibe uma mensagem de sucesso
        if response.status_code == 200:
            flash(data['mensagem'], 'success')
        else:
            # Caso contrário, exibe uma mensagem de erro
            flash(data['mensagem'], 'error')
    except RequestException:
        # Trata exceções de requisições HTTP
        flash(f'Erro ao conectar com o banco {bank}', 'error')

    # Redireciona o usuário de volta para a página de visualização de chaves PIX
    return redirect(url_for('minhas_chaves_pix', bank=bank))




# Rota para apagar uma chave PIX na tela de visualização de chaves PIX
@app.route('/<bank>/apagar_chave_pix', methods=['POST'])
def apagar_chave_pix(bank):
    # Obtém a URL base do banco a partir do dicionário bank_urls
    base_url = bank_urls.get(bank)

    # Obtém a agência e a conta da sessão do usuário
    agencia = session.get('agencia')
    conta = session.get('conta')

    # Obtém o tipo de chave do formulário de solicitação
    tipo_chave = request.form['tipo_chave']

    # Dados a serem enviados na requisição POST
    dados = {
        'agencia': agencia,
        'conta': conta,
        'tipo_chave': tipo_chave
    }

    try:
        # Faz uma requisição POST para apagar a chave PIX
        response = requests.post(f'{base_url}/pix/apagar', json=dados)
        data = response.json()
        
        # Verifica se a requisição foi bem-sucedida e exibe uma mensagem adequada
        if response.status_code == 200:
            flash(data['mensagem'], 'success')
        else:
            flash(data['mensagem'], 'error')
    except RequestException:
        # Trata exceções de requisições HTTP
        flash(f'Erro ao conectar com o banco {bank}', 'error')

    # Redireciona o usuário de volta para a página de visualização de chaves PIX
    return redirect(url_for('minhas_chaves_pix', bank=bank))





# Rota para sair da conta
@app.route('/logout')
def logout():
    # Limpa a sessão
    session.clear()
    flash('Logout realizado com sucesso.', 'success')
    # Retorna para a tela inicial (index)
    return redirect(url_for('index'))


IP = socket.gethostbyname(socket.gethostname())
if __name__ == '__main__':
    app.run(port=9999, host=IP, debug=True)
