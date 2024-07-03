# PBL-Concorrencia-2-IWEB

__Autor - Weslei Silva Santos__

__INTRODUÇÃO:__  

Este projeto visa implementar um sistema de transações bancárias distribuídas que inclui três bancos fictícios inspirados em instituições reais: Bradesco, Neon e PicPay. O servidor oferece funcionalidades essenciais para operações bancárias, como criação de contas, login, saques e transferências. Além disso, o sistema suporta depósitos e transferências tanto dentro do mesmo banco quanto para bancos de destino diferentes.

_# COMO USAR O PROGRAMA_
   
Configuração Inicial

O sistema tem como código fonte a linguagem python, por isso é necessário que o ambiente que irá rodar o programa tenha o python instalado.
Link para baixar o python nos diferentes sistemas operacionais: https://www.python.org/downloads/ .
A versão utilizada foi a 3.12.

Também é necessário instalar a API do flask, usando o comando pip do python no prompt de comando (Todos os servidores necessitam do flask):
    
    pip install flask 
    
Instalar a biblioteca requests, que é responsável pelas solicitações via http (Tanto a aplicação, comunicação entre bancos e tabela de roteamento necessitam das requests). Instale usando o prompt de comando com:

    pip install requests

Instalar a biblioteca responsável pelo banco de dados (flask_sqlalchemy), que armazena os dados de conta e titulares (Apenas os servidores dos bancos utilizam o flask_sqlalchemy). Instale usando o prompt de comando com:  

    pip install flask_sqlalchemy
    
Por fim, instalar uma biblioteca adicional para exibir continualmente as informações de conta do banco, que é a biblioteca tabulate (Isso foi implementado pensando no docker, já que não tem como usar a extensão SQL Viewer na execução do container). Instale usando o prompt de comando com:  

    pip install tabulate


__UTILIZAÇÃO DO SISTEMA (Execução)__  

__Tabela de Roteamento (table_router.py)__  

A tabela de roteamento é responsável por armazenar as rotas específicas dos bancos. Quando um banco deseja realizar uma operação para outro banco, ele consulta essa tabela para determinar a rota correta do banco de destino.

Iniciar a tabela de roteamento: Execute o arquivo table_router.py utilizando Python. Este servidor ficará ativo aguardando o registro das rotas pelos bancos. Posteriormente, outros bancos poderão realizar operações distribuídas consultando esta tabela. 


__Bancos (Bradesco.py, Picpay.py e Neon.py)__

Os bancos são responsáveis por disponibilizar serviços à aplicação, como movimentação de saldo através de transferências, depósitos e saques. Além disso, cada banco deve registrar suas rotas na tabela de roteamento e consultar essa tabela para realizar operações distribuídas de forma eficiente.  

Iniciar bancos: Após a tabela de roteamento ser iniciada com sucesso, você pode proceder com a execução dos bancos. Para isso, execute os arquivos Bradesco.py, Picpay.py e Neon.py utilizando python. Depois que esses servidores estiverem em execução, o sistema estará pronto para receber requisições da aplicação.

__Aplicação (app.py)__

A aplicação é responsável por fornecer a interface interativa que permite aos clientes acessar as funcionalidades bancárias. Através desta interface, os clientes podem realizar operações bancárias utilizando as rotas registradas pelos bancos.

Iniciar aplicação: Execute o arquivo app.py utilizando python. O servidor mostrará a rota de acesso no terminal.  

Exemplo:

    $ python app.py  # Execução
    Serving Flask app 'app'
    Debug mode: on
    Running on http://172.31.160.1:9999 # Rota de acesso
    Restarting with stat
    Debugger is active!
    Debugger PIN: 746-199-761
Dessa forma, basta acessar a rota no navegador (http://172.31.160.1:9999) para que o cliente possa utilizar a aplicação e interagir com os serviços bancários disponibilizados.  

Após o acesso, é necessário:
 * Selecionar o banco que deseja fazer login ou criar conta, as opções de banco são:
   - Bradesco
   - Neon
   - Picpay
 * Selecionar a opção de operação (Estágio 1):
   - Fazer login:  
     Após inserir suas credenciais, se login for feito com sucesso será exibido o saldo e a opção de demais operações, como transferência e saque.
     Se o login falhar, o usuário não tem acesso as demais operações de cliente do banco.
     
   - Criar conta:  
      O usuário pode escolher ente conta pessoa fisica individual (PFI), conta pessoa fisica conjunta (PFC) e conta juridica (PJ).
      O usuário pode criar apenas uma conta individual com o seu CPF, e varias contas conjuntas, contanto que seja com titulares diferentes.
      Para conta juridica também só é possivel criar uma conta com o mesmo cnpj.
     
  *  Selecionar a opção de operação (Estágio 2- pós login):  
     Após fazer o login as operações disponíveis na dashboard são:  
     - Fazer depósito:  
       O usuário pode digitar qualquer conta que deseja fazer o depósito, informar o valor e selecionar o banco de destino.
       Caso a conta não seja encontrada ou ocorra um problema de comunicação com o banco de destino o depósito falha.
       Se o valor do depósito for 0, o mesmo não ocorre.
       
     - Realizar transferência TED:  
       O usuário pode digitar qualquer conta que deseja fazer a transferência, informar o valor e selecionar o banco de destino. Se o saldo for suficiente a transação ocorre com sucesso.
       Caso a conta não seja encontrada ou ocorra um problema de comunicação com o banco de destino o transação falha.
       Se o valor da transferência TED for 0, a mesma não ocorre.
       
     - Realizar transferência PIX:  
       O usuário pode digitar qualquer chave pix que deseja fazer a transferência, informar o valor que vai transferir de cada conta que possui. Se o saldo for suficiente a transação ocorre com sucesso.
       Caso a chave pix não tenha registro ou ocorra um problema de comunicação com o banco que a chave pix pertence a transação falha.

     - Sacar:  
       O usuário pode sacar valores da sua conta que está logado.
       Se o valor a ser sacado for maior que o valor do saldo, o saque falha.
       Se o valor a ser sacado for 0, o saque falha.

     - Minhas chaves pix:  
       O usuário pode vizualizar suas chaves pix.
       O usuário pode cadastrar uma chave pix que não exista em outra conta.
       Os tipos de chave são email, chave aléatória e telefone.
       O usuário pode apagar uma chave pix que tenha registrado.

     - Sair:  
       O usuário volta para a tela inicial.
       
__Execução dos containers:__

* Comandos para executar o sistema com o Docker:

Para carregar as imagens do DockerHub:

    docker pull wesleisantoss/table_router:latest
    docker pull wesleisantoss/bradesco:latest
    docker pull wesleisantoss/neon:latest
    docker pull wesleisantoss/picpay:latest
    docker pull wesleisantoss/app:latest

Para executar em qualquer máquina os containers:

    docker run --network=host -it wesleisantoss/table_router
    docker run --network=host -it -e IP_ROUTER=192.168.65.3  wesleisantoss/bradesco
    docker run --network=host -it -e IP_ROUTER=192.168.65.3  wesleisantoss/neon
    docker run --network=host -it -e IP_ROUTER=192.168.65.3  wesleisantoss/picpay
    docker run -p 9999:9999 -it -e IP_bradesco=192.168.65.3 -e IP_neon=192.168.65.3 -e IP_picpay=192.168.65.3 wesleisantoss/app

Para o correto funcionamento do sistema, execute a tabela de roteamento (wesleisantoss/table_router), depois coloque o ip onde está executando a tabela de roteamento nos bancos (wesleisantoss/bradesco, wesleisantoss/neon, wesleisantoss/picpay) em 'IP_ROUTER' e os execute. Depois coloque os ips de onde cada banco está executando na aplicação (wesleisantoss/app) usando 'IP_bradesco', 'IP_neon' e 'IP_picpay' e execute a aplicação.  
* A rota de acesso da aplicação será:
    http://localhost:9999/



__DIAGRAMA DO SISTEMA__

   ![Diagrama de Comunicação](./Diagrama%20do%20sistema.png)
