from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import os
import socket
app = Flask(__name__)

app.secret_key = 'chave_secreta'  

#'+os.getenv('IP_neon')+'

bank_urls = {
    'bradesco': 'http://10.0.0.113:9635',
    'neon': 'http://10.0.0.113:9636',
    'picpay': 'http://10.0.0.113:9637'
}

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/<bank>/login', methods=['GET', 'POST'])
def login(bank):
    base_url = bank_urls.get(bank)
    if not base_url:
        flash('Banco não encontrado.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        agencia = request.form['agencia']
        conta = request.form['conta']
        senha = request.form['senha']
        cpf_ou_cnpj = request.form['cpf_ou_cnpj']

        response = requests.post(f'{base_url}/login', json={
            'agencia': agencia,
            'conta': conta,
            'senha': senha,
            'cpf_ou_cnpj': cpf_ou_cnpj
        })

        if response.status_code == 200:
            session['agencia'] = agencia
            session['conta'] = conta
            session['bank'] = bank
            session['cpf_ou_cnpj'] = cpf_ou_cnpj
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard', bank=bank))
        else:
            flash('Falha no login. Verifique suas credenciais.', 'error')

        return redirect(url_for('login', bank=bank))

    return render_template('login.html', bank=bank)

@app.route('/<bank>/criar_conta', methods=['GET', 'POST'])
def criar_conta(bank):
    base_url = bank_urls.get(bank)
    if not base_url:
        flash('Banco não encontrado.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        tipo_conta = request.form['tipo_conta']
        if tipo_conta == 'PFI':
            nome = request.form['nome']
            cpf_ou_cnpj = request.form['cpf_cnpj']
            senha = request.form['senha']

            response = requests.post(f'{base_url}/criar_conta', json={
                'nome': nome,
                'cpf_ou_cnpj': cpf_ou_cnpj,
                'senha': senha,
                'tipo_conta': 'PFI'
            })

        elif tipo_conta == 'PFC':
            quantidade_titulares = int(request.form['quantidade_titulares'])
            titulares = {}
            for i in range(1, quantidade_titulares + 1):
                nome = request.form[f'nome_titular{i}']
                cpf = request.form[f'cpf_cnpj_titular{i}']
                titulares[cpf] = nome
            senha = request.form['senha_conjunta']

            response = requests.post(f'{base_url}/criar_conta', json={
                'titulares': titulares,
                'senha': senha,
                'tipo_conta': 'PFC'
            })

        elif tipo_conta == 'PJ':
            razao_social = request.form['razao_social']
            cnpj = request.form['cnpj']
            senha = request.form['senha_juridica']

            response = requests.post(f'{base_url}/criar_conta', json={
                'nome': razao_social,
                'cpf_ou_cnpj': cnpj,
                'senha': senha,
                'tipo_conta': 'PJ'
            })

        if response.status_code == 200:
            data = response.json()
            flash(f'{data['mensagem']}, Agência: {data["agencia"]}, Conta: {data["conta"]}', 'success')
        else:
            data = response.json()
            flash(data['erro'], 'error')

        return redirect(url_for('criar_conta', bank=bank))

    return render_template('criar_conta.html', bank=bank)


@app.route('/<bank>/deposito', methods=['GET', 'POST'])
def deposito(bank):
    base_url = bank_urls.get(bank)
    if not base_url:
        flash('Banco não encontrado.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        agencia = request.form['agencia']
        conta = request.form['conta']
        valor = float(request.form['valor'])
        banco_destino = request.form['banco_destino']

        dados = {
            'agencia': agencia,
            'conta': conta,
            'valor': valor,
            'banco_destino': banco_destino
        }

        response = requests.post(f'{base_url}/depositar', json=dados)
        data = response.json()
        if response.status_code == 200:
            flash(f'{data['mensagem']}', 'success')
        else:
            flash(f'{data['erro']}', 'error')

        return redirect(url_for('deposito', bank=bank))

    return render_template('deposito.html', bank=bank)



@app.route('/<bank>/dashboard')
def dashboard(bank):
    base_url = bank_urls.get(bank)
    if not base_url:
        flash('Banco não encontrado.', 'error')
        return redirect(url_for('index'))

    agencia = session.get('agencia')
    conta = session.get('conta')

    response = requests.get(f'{base_url}/saldo', params={
        'agencia': agencia,
        'conta': conta
    })

    if response.status_code == 200:
        saldo = response.json().get('saldo', 0)
    else:
        saldo = 'Erro ao obter saldo'

    return render_template('dashboard.html', bank=bank, saldo=saldo)


@app.route('/<bank>/transferencia_ted', methods=['GET', 'POST'])
def transferencia_ted(bank):
    base_url = bank_urls.get(bank)
    if not base_url:
        flash('Banco não encontrado.', 'error')
        return redirect(url_for('dashboard', bank=bank))

    agencia_origem = session.get('agencia')
    conta_origem = session.get('conta')

    if not agencia_origem or not conta_origem:
        flash('Informações de agência e conta não encontradas na sessão.', 'error')
        return redirect(url_for('dashboard', bank=bank))

    response = requests.get(f'{base_url}/saldo', params={'agencia': agencia_origem, 'conta': conta_origem})

    if response.status_code == 200:
        saldo = response.json().get('saldo', 0)
    else:
        saldo = 'Erro ao obter saldo'

    if request.method == 'POST':
        agencia_destino = request.form['agencia_destino']
        conta_destino = request.form['conta_destino']
        valor = float(request.form['valor'])
        banco_destino = request.form['banco_destino']

        dados = {
            'agencia_origem': agencia_origem,
            'conta_origem': conta_origem,
            'agencia_destino': agencia_destino,
            'conta_destino': conta_destino,
            'valor': valor,
            'banco_destino': banco_destino
        }

        response = requests.post(f'{base_url}/transferencia/ted/enviar', json=dados)
        data = response.json()
        if response.status_code == 200:
            flash(f'{data['mensagem']}', 'success')
        else:
            flash(f'{data['erro']}', 'error')

        return redirect(url_for('transferencia_ted', bank=bank))

    return render_template('transferencia_ted.html', bank=bank, saldo=saldo)



def obter_contas_vinculadas(cpf_ou_cnpj, bank):
    response = requests.get(f'{bank_urls.get(bank)}/obter_contas_todos_bancos', params={'cpf_ou_cnpj': cpf_ou_cnpj})
    if response.status_code != 200:
        return None, response.json()
    contas = response.json().get('contas', [])
    return contas, None


@app.route('/<bank>/transferencia_pix', methods=['GET', 'POST'])
def transferencia_pix(bank):
    base_url = bank_urls.get(bank)
    if not base_url:
        flash('Banco não encontrado.', 'error')
        return redirect(url_for('dashboard', bank=bank))

    if request.method == 'POST':
        chave_pix_destino = request.form['chave_pix_destino']
        contas_origem = []

        for conta in request.form.getlist('contas_origem'):
            banco, agencia, conta_num, saldo = conta.split(',')
            valor = request.form.get(f'valor_{banco}_{agencia}_{conta_num}')
            if valor and float(valor) > 0:
                contas_origem.append({
                    'banco': banco,
                    'agencia': agencia,
                    'conta': conta_num,
                    'valor': float(valor)
                })

        dados = {
            'chave_pix_destino': chave_pix_destino,
            'contas_origem': contas_origem
        }

        response = requests.post(f'{base_url}/transferencia/pix/enviar', json=dados)
        if response.status_code == 200:
            flash('Transferência PIX realizada com sucesso', 'success')
        else:
            flash('Erro ao realizar transferência PIX: ' + response.json().get('message', 'Erro desconhecido'), 'error')

        return redirect(url_for('transferencia_pix', bank=bank))


    cpf_ou_cnpj = session.get('cpf_ou_cnpj')
    if not cpf_ou_cnpj:
        flash('CPF/CNPJ não encontrado na sessão.', 'error')
        return redirect(url_for('dashboard', bank=bank))

    contas, erro = obter_contas_vinculadas(cpf_ou_cnpj, bank)
    if erro:
        flash('Erro ao obter contas: ' + str(erro), 'error')
        return redirect(url_for('dashboard', bank=bank))

    return render_template('transferencia_pix.html', bank=bank, contas=contas)




@app.route('/<bank>/sacar', methods=['GET', 'POST'])
def sacar(bank):
    base_url = bank_urls.get(bank)
    if not base_url:
        flash('Banco não encontrado.', 'error')
        return redirect(url_for('dashboard', bank=bank))

    agencia = session.get('agencia')
    conta = session.get('conta')

    if not agencia or not conta:
        flash('Informações de agência e conta não encontradas na sessão.', 'error')
        return redirect(url_for('dashboard', bank=bank))

    response = requests.get(f'{base_url}/saldo', params={'agencia': agencia, 'conta': conta})

    if response.status_code == 200:
        saldo = response.json().get('saldo', 0)
    else:
        saldo = 'Erro ao obter saldo'

    if request.method == 'POST':
        valor = float(request.form['valor'])

        response = requests.post(f'{base_url}/sacar', json={
            'agencia': agencia,
            'conta': conta,
            'valor': valor
        })

        if response.status_code == 200:
            flash('Saque realizado com sucesso', 'success')
        else:
            flash('Erro ao realizar saque: ' + response.json().get('message', 'Erro desconhecido'), 'error')

        return redirect(url_for('sacar', bank=bank))

    return render_template('sacar.html', bank=bank, saldo=saldo)


@app.route('/<bank>/minhas_chaves_pix', methods=['GET'])
def minhas_chaves_pix(bank):
    base_url = bank_urls.get(bank)
    if not base_url:
        flash('Banco não encontrado.', 'error')
        return redirect(url_for('dashboard', bank=bank))

    agencia = session.get('agencia')
    conta = session.get('conta')

    response = requests.get(f'{base_url}/pix/visualizar', params={'agencia': agencia, 'conta': conta})
    if response.status_code == 200:
        chaves_pix = response.json().get('chaves_pix', {})
    else:
        flash('Erro ao visualizar chaves PIX.', 'error')
        chaves_pix = {}

    return render_template('minhas_chaves_pix.html', bank=bank, chaves=chaves_pix)

@app.route('/<bank>/cadastrar_chave_pix', methods=['POST'])
def cadastrar_chave_pix(bank):
    base_url = bank_urls.get(bank)
    if not base_url:
        flash('Banco não encontrado.', 'error')
        return redirect(url_for('minhas_chaves_pix', bank=bank))

    agencia = session.get('agencia')
    conta = session.get('conta')
    tipo_chave = request.form['tipo_chave']
    chave_pix = request.form['valor_chave']

    dados = {
        'agencia': agencia,
        'conta': conta,
        'chave_pix': chave_pix,
        'tipo_chave': tipo_chave
    }

    response = requests.post(f'{base_url}/pix/cadastrar', json=dados)
    if response.status_code == 200:
        flash('Chave PIX cadastrada com sucesso!', 'success')
    else:
        flash('Erro ao cadastrar chave PIX.', 'error')

    return redirect(url_for('minhas_chaves_pix', bank=bank))

@app.route('/<bank>/apagar_chave_pix', methods=['POST'])
def apagar_chave_pix(bank):
    base_url = bank_urls.get(bank)
    if not base_url:
        flash('Banco não encontrado.', 'error')
        return redirect(url_for('minhas_chaves_pix', bank=bank))

    agencia = session.get('agencia')
    conta = session.get('conta')
    tipo_chave = request.form['tipo_chave']

    dados = {
        'agencia': agencia,
        'conta': conta,
        'tipo_chave': tipo_chave
    }

    response = requests.post(f'{base_url}/pix/apagar', json=dados)
    if response.status_code == 200:
        flash('Chave PIX apagada com sucesso!', 'success')
    else:
        flash('Erro ao apagar chave PIX.', 'error')

    return redirect(url_for('minhas_chaves_pix', bank=bank))


@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso.', 'success')
    return redirect(url_for('index'))


IP = socket.gethostbyname(socket.gethostname())
if __name__ == '__main__':
    app.run(port=9999, host=IP, debug=True)
