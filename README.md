# PBL-Concorrencia-2-IWEB-

__Autor - Weslei Silva Santos__

_# COMO USAR O PROGRAMA_
   
Configuração Inicial

O sistema tem como código fonte a linguagem python, por isso é necessário que o ambiente que irá rodar o programa tenha o python instalado.
Link para baixar o python nos diferentes sistemas operacionais: https://www.python.org/downloads/ .
A versão utilizada foi a 3.12.

Também é necessário instalar a API do flask, usando o comando pip do python no prompt de comando (Todos os servidores necessitam do flask):
    
    pip install flask 
    
Instalar a biblioteca requests, que é responsável pelas solicitações via http (Tanto a aplicação e a comunicação entre bancos necessitam das requests). Instale usando o prompt de comando com:

    pip install requests

Instalar a biblioteca responsável pelo banco de dados (flask_sqlalchemy), que armazena os dados de conta e titulares (Apenas os servidores dos bancos utilizam o flask_sqlalchemy). Instale usando o prompt de comando com:  

    pip install flask_sqlalchemy
    
Por fim, instalar uma biblioteca adicional para exibir continualmente as informações de conta do banco, que é a biblioteca tabulate (Isso foi implementado pensando no docker, já que não tem como usar a extensão SQL Viewer na execução do container). Instale usando o prompt de comando com:  

    pip install tabulate


__UTILIZAÇÃO DO SISTEMA (Execução)__  

__Bancos (Bradesco.py, Picpay.py e Neon.py)__

Os bancos são responsáveis por disponibilizar serviços à aplicação, como movimentação de saldo através de transferências, depósitos e saques. Além disso, cada banco pode fazer operações para outros bancos.  
Iniciar bancos: Para isso, execute os arquivos Bradesco.py, Picpay.py e Neon.py utilizando python. Depois que esses servidores estiverem em execução, o sistema estará pronto para receber requisições da aplicação.

__Aplicação (app.py)__

A aplicação serve como uma interface interativa, permitindo que os clientes acessem diversas funcionalidades bancárias. Por meio dessa interface, os clientes podem realizar operações bancárias utilizando as rotas registradas pelos diferentes bancos.  
Iniciar aplicação: Execute o arquivo app.py utilizando python. O servidor mostrará a rota de acesso no terminal.  

Exemplo:

    $ python app.py  # Execução
    Serving Flask app 'app'
    Debug mode: on
    Running on http://172.31.160.1:9999 # Rota de acesso
    Restarting with stat
    Debugger is active!
    Debugger PIN: 746-199-761
    
Dessa forma, basta acessar a rota no navegador (http://172.31.160.1:9999) para que se possa utilizar a aplicação e interagir com os serviços bancários disponibilizados.  

* Após o acesso, é necessário:
 * Selecionar o banco que deseja fazer login ou criar conta, as opções de banco são:
   - Bradesco
   - Neon
   - Picpay  
     
 * Selecionar a opção de operação (Estágio 1):
   - Fazer login:  
     Após inserir suas credenciais, se login for feito com sucesso será exibido o saldo e a opção de demais operações, como transferência, saque e etc.
     Se o login falhar, o usuário não tem acesso as demais operações de cliente do banco.
     
   - Criar conta:  
      O usuário pode escolher entre conta pessoa fisica individual (PFI), conta pessoa fisica conjunta (PFC) e conta juridica (PJ).
      O usuário pode criar apenas uma conta individual com o seu CPF, e varias contas conjuntas, contanto que seja com titulares diferentes.
      Para conta juridica, também só é possivel criar uma conta com o mesmo cnpj.
     
  *  Selecionar a opção de operação (Estágio 2- pós login):  
     Após fazer o login as operações disponíveis na dashboard são:  
     - Fazer depósito:  
       O usuário pode digitar qualquer conta que deseja fazer o depósito, informar o valor e selecionar o banco de destino.
       Caso a conta não seja encontrada ou ocorra um problema de comunicação com o banco de destino o depósito falha.
       Se o valor do depósito for menor ou igual a 0, o mesmo não ocorre.
       
     - Realizar transferência TED:  
       O usuário pode digitar qualquer conta que deseja fazer a transferência, informar o valor e selecionar o banco de destino. Se o saldo for suficiente a transação ocorre com sucesso.
       Caso a conta não seja encontrada ou ocorra um problema de comunicação com o banco de destino o transação falha.
       Se o valor da transferência TED for menor ou igual a 0, a mesma não ocorre.
       
     - Realizar transferência PIX:  
       O usuário pode inserir qualquer chave PIX para realizar a transferência e informar o valor a ser transferido de cada uma de suas contas. Se o saldo for suficiente, a transação será concluída com sucesso.  
       Caso a chave pix não tenha registro ou ocorra um problema de comunicação com o banco que a chave pix pertence, a transação falha.

     - Sacar:  
       O usuário pode sacar valores da sua conta que está logado.
       Se o valor a ser sacado for maior que o valor do saldo, o saque falha.
       Se o valor a ser sacado for menor ou igual a 0, o saque falha.

     - Minhas chaves pix:  
       O usuário pode vizualizar suas chaves pix.
       O usuário pode cadastrar uma chave pix que não exista em outra conta.
       Os tipos de chave são email, chave aléatória e telefone.
       O usuário pode apagar qualquer chave pix que tenha registrado.

     - Sair:  
       O usuário volta para a tela inicial (logout).
       
__Execução dos containers:__

* Comandos para executar o sistema com o Docker:

Para carregar as imagens do DockerHub:

    docker pull wesleisantoss/bradesco:latest
    docker pull wesleisantoss/neon:latest
    docker pull wesleisantoss/picpay:latest
    docker pull wesleisantoss/app:latest

Para executar em qualquer máquina os containers:

    docker run --network=host -it -e IP_neon=172.16.103.2 -e IP_picpay=172.16.103.3 wesleisantoss/bradesco  
    docker run --network=host -it -e IP_bradesco=172.16.103.1 -e IP_picpay=172.16.103.3  wesleisantoss/neon
    docker run --network=host -it -e IP_bradesco=172.16.103.1 -e IP_neon=172.16.103.2 wesleisantoss/picpay
    docker run -p 9999:9999 -it -e IP_bradesco=172.16.103.1 -e IP_neon=172.16.103.2 -e IP_picpay=172.16.103.3 wesleisantoss/app

Para garantir o correto funcionamento do sistema, certifique-se de colocar os IPs corretos onde cada banco está sendo executado. Por exemplo, ao executar wesleisantoss/bradesco, defina IP_neon e IP_picpay com os IPs das máquinas onde os bancos Neon e PicPay estão rodando. Repita o mesmo processo para os demais bancos (wesleisantoss/neon e wesleisantoss/picpay). Depois, configure a aplicação (wesleisantoss/app) com os IPs de onde cada banco está executando usando as variáveis IP_bradesco, IP_neon e IP_picpay e então execute a aplicação.  

* Devido ao mapeamento de porta na execução do app, a url de acesso do app ficará com o endereço IP interno da rede Docker. No entanto, esse endereço IP é acessível apenas dentro da rede Docker, não externamente. Por isso, é necessário usar o endereço IP da máquina host (o IP real da máquina onde o container está rodando).

* Exemplo: 

   Se a url for http://172.17.0.2:9999 colocando o ip da máquina onde o container está executando, a nova url ficará mais ou menos assim:

      http://172.16.103.4:9999/

__INTRODUÇÃO:__  

  Este projeto visa implementar um sistema de transações bancárias distribuídas, que inclui três bancos fictícios inspirados em instituições reais: Bradesco, Neon e PicPay. O servidor oferece funcionalidades essenciais para operações bancárias, como criação de contas, login, saques, transferência TED e PIX. Além disso, o sistema suporta depósitos e transferências tanto dentro do mesmo banco quanto para bancos de destino diferentes.


                                                 #DIAGRAMA DO SISTEMA:

   ![Diagrama de Comunicação](./Diagrama%20do%20sistema.png)

* O app pode selecionar qual banco irá acessar, ele pode escolher entre Bradesco, Picpay e Neon.
* Quando a operação de um banco tiver outro banco como destino, ele irá acessar as rotas dos outros bancos para poder realizar a mesma.
* Todos as comunicações entre os componentes do diagrama ocorre via HTTP.



* __FUNCIONALIDADES:__

  __FILES:__ _Bradesco.py, Neon.py e Picpay.py_
Esses files são destinados para os servidores do banco, eles possuem o mesmo código fonte, com apenas algumas alterações na porta, ID e o nome do banco de dados, conforme abaixo.

_Bradesco.py:__  
* app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bradesco.db'
* PORT = 9635
* BANCO_ID = '237'

_Neon.py:__  
* app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neon.db'
* PORT = 9635
* BANCO_ID = '536'

_Picpay.py:__  
* app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///picpay.db'
* PORT = 9637
* BANCO_ID = '380'

* __Banco de Dados:__
  - Nos bancos, são usadas quatro tabelas no banco de dados flask_sqlalchemy. Aqui estão as tabelas e suas funções:

1. Tabela Titular:    
Descrição: Representa os titulares das contas no banco.  
Colunas:  
  id: Identificador único do titular (chave primária).  
  nome: Nome do titular.  
  cpf_ou_cnpj: Documento único do titular, seja CPF ou CNPJ (único e não nulo).  
  
  
2. Tabela conta_titular:    
Descrição: Tabela de associação para relacionar titulares e contas. É uma tabela de junção muitos-para-muitos.  
Colunas:  
  conta_id: Identificador da conta (chave estrangeira).  
  titular_id: Identificador do titular (chave estrangeira).  

3. Tabela Conta:  
Descrição: Representa as contas bancárias.  
Colunas:  
  id: Identificador único da conta (chave primária).  
  agencia: Agência bancária da conta.  
  conta: Número da conta.  
  senha: Senha da conta.  
  saldo: Saldo da conta (padrão é 0.0).  
  chave_pix_email: Chave PIX baseada em e-mail (único).  
  chave_pix_aleatoria: Chave PIX aleatória (único).  
  numero_celular: Número de celular associado à conta (único).  
  tipo_conta: Tipo de conta (por exemplo, PFI, PFC e PJ).  
  titulares: Relacionamento muitos-para-muitos com a tabela Titular usando a tabela conta_titular.  

   
4. Tabela Lock:  
Descrição: Representa os bloqueios em recursos específicos para gerenciar concorrência (ex: Bloquear um conta através da agencia e conta ou através da chave pix).  
Colunas:  
  id: Identificador único do bloqueio (chave primária).  
  resource: Recurso que está sendo bloqueado (único e não nulo).  
  locked: Estado do bloqueio (verdadeiro se bloqueado, falso caso contrário).  
  timestamp: Data e hora em que o bloqueio foi criado (definido automaticamente).  

__Funções de Bloqueio:__  
* Função acquire_lock: Tenta adquirir um bloqueio exclusivo em um recurso específico. Se o recurso já estiver bloqueado, a função aguardará até que o bloqueio possa ser adquirido ou o tempo limite seja atingido.  
* Função release_lock: Libera um bloqueio em um recurso específico, permitindo que outros processos possam adquirir o bloqueio no futuro.


__Rotas do servidor:__  
* Rota /login  
  Esta rota permite que um usuário faça login em sua conta bancária.  
  Recepção dos Dados: Recebe dados JSON do cliente contendo agencia, conta, senha e cpf_ou_cnpj.  

* Rota /criar_conta  
  Esta rota permite que o usuário crie uma conta do tipo que escolher (PFI, PFC, PJ)
  Recepção dos Dados: Recebe dados JSON do cliente contendo senha e tipo_conta.
     - Se a conta for conjunta ela recebe um conjunto de titulares com nome, CPFs.
     - Se a conta for individual ou jurídica, ele recebe o CPF ou CNPJ e nome do titular. (Para conta jurídica o nome do titular irá representar a razão social da empresa ou organização).

* Rota /depositar  
  Essa rota permite que o usuário faça depositos em qualquer conta, em qualquer banco.  
  Recepção dos Dados: Recebe dados JSON do cliente contendo a agência de destino, conta de destino, o banco ao qual a conta pertence (banco de destino) e o valor a ser transferido.  

* Rota /sacar  
  Essa rota permite que o usuário faça saques em sua conta logada.  
  Recepção dos Dados: Recebe dados JSON do cliente contendo a agência, conta e valor.  

* Rota /saldo  
  Essa rota permite vizualizar o saldo da conta.  
  Recepção dos Dados: Recebe dados JSON do cliente contendo a agência e conta.  

* Rota /transferencia/ted/enviar  
  Essa rota permite enviar valores para uma conta específica de qualquer banco.  
  Recepção dos Dados: Recebe dados JSON do cliente contendo a agência e conta de origem, a agência e conta de destino e o valor a ser transferido.

* Rota /transferencia/pix/enviar  
  Essa rota permite que o cliente envie valores de diferentes contas vinculadas ao seu CPF para outra conta, por meio da chave PIX.  (N para 1)  
  Recepção dos Dados: Recebe dados JSON do cliente contendo as contas de origem com suas informações de agência, conta, banco e valor a ser transferido de cada banco.

* Rota /transferencia/receber  
  Essa rota é a que fica responsável por receber depósitos ou transferência (TED ou PIX) de outros bancos.  
  Recepção dos Dados: Recebe um JSON contendo o tipo de transferência (TED, PIX ou DEP para depósito) e o valor a ser transferido. Para transferências PIX, inclui a chave PIX do destinatário. Para transferências TED e depósitos, inclui o número da agência e o número da conta de destino.

* Rota /pix/chave  
  Essa rota permite que outros bancos verifiquem se uma chave PIX já está cadastrada no banco atual.  
  Recepção dos Dados: A rota recebe a chave PIX a ser verificada.

* Rota /transferencia/pix/descontar  
  Essa rota permite descontar saldo de uma conta específica no banco.  
  Recepção dos Dados: A rota recebe um JSON contendo o número da agência da conta, o número da conta e o valor a ser descontado.  

* Rota /transferencia/pix/reverter  
  Essa rota permite reverter o saldo de uma conta específica em caso de falha na transferência.  
  Recepção dos Dados: A rota recebe um JSON contendo o número da agência da conta, o número da conta e o valor a ser revertido.

* Rota /obter_contas_todos_bancos  
  Essa rota busca todas as contas de um mesmo titular em todos os bancos.  
  Recepção dos Dados: A rota recebe o CPF ou CNPJ como parâmetro de consulta.

* Rota /obter_contas  
  Essa rota busca todas as contas de um titular específico no banco atual.  
  Recepção dos Dados: A rota recebe o CPF ou CNPJ como parâmetro de consulta.

* Rota /pix/cadastrar  
  Essa rota cadastra uma nova chave PIX para uma conta específica.  
  Recepção dos Dados: A rota recebe um JSON contendo a agência, conta, chave PIX e o tipo da chave (Email, Aleatória ou Telefone).

* Rota /pix/apagar  
  Essa rota apaga uma chave PIX previamente cadastrada em uma conta.  
  Recepção dos Dados: A rota recebe um JSON contendo a agência, conta e o tipo da chave (Email, Aleatória ou Telefone).

* Rota /pix/visualizar  
  Essa rota permite visualizar todas as chaves PIX registradas para uma conta específica.  
  Recepção dos Dados: A rota recebe os parâmetros de consulta contendo a agência e a conta.
  
