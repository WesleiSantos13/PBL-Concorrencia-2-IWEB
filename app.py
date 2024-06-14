from flask import Flask, render_template, request, redirect, url_for, flash
import requests

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Necessário para usar flash messages

bank_urls = {
    'bradesco': 'http://172.31.96.1:9635',
    'neon': 'http://172.31.96.1:9636',
    'picpay': 'http://172.31.96.1:9637'
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
            flash('Login realizado com sucesso!', 'success')
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
            flash(f'Conta criada com sucesso! Agência: {data["agencia"]}, Conta: {data["conta"]}', 'success')
        else:
            flash('Erro ao criar conta. Tente novamente.', 'error')

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

        response = requests.post(f'{base_url}/depositar', json={
            'agencia': agencia,
            'conta': conta,
            'valor': valor
        })

        if response.status_code == 200:
            flash('Depósito realizado com sucesso!', 'success')
        else:
            flash('Erro ao realizar depósito. Tente novamente.', 'error')

        return redirect(url_for('deposito', bank=bank))

    return render_template('deposito.html', bank=bank)


if __name__ == '__main__':
    app.run(port=9999, host='172.31.96.1', debug=True)
