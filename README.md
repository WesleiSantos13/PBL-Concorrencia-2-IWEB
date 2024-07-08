# PBL-Concorrencia-2 - Operações Bancárias Distribuídas

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

    docker run --network=host -it -e IP_neon=172.16.103.2 -e IP_picpay=172.16.103.4 wesleisantoss/bradesco  
    docker run --network=host -it -e IP_bradesco=172.16.103.1 -e IP_picpay=172.16.103.4  wesleisantoss/neon
    docker run --network=host -it -e IP_bradesco=172.16.103.1 -e IP_neon=172.16.103.2 wesleisantoss/picpay
    docker run -p 9999:9999 -it -e IP_bradesco=172.16.103.1 -e IP_neon=172.16.103.2 -e IP_picpay=172.16.103.4 wesleisantoss/app

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
Descrição: Representa os bloqueios em recursos específicos para gerenciar concorrência (ex: Bloquear um conta através da agencia e conta).  
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
  Essa rota é a que fica responsável por receber depósitos, transferência (TED ou PIX) e valores revertidos de outros bancos.  
  Recepção dos Dados: Recebe um JSON contendo o tipo de transferência (TED, PIX, DEP para depósito e REVERT para valores revertidos) e o valor a ser transferido. Para transferências PIX, inclui a chave PIX do destinatário. Para transferências TED, depósitos e reversão de saldo, inclui o número da agência e o número da conta de destino.

* Rota /pix/chave  
  Essa rota permite que outros bancos verifiquem se uma chave PIX já está cadastrada no banco atual.  
  Recepção dos Dados: A rota recebe a chave PIX a ser verificada.

* Rota /transferencia/pix/descontar  
  Essa rota permite descontar saldo de uma conta específica no banco.  
  Recepção dos Dados: A rota recebe um JSON contendo o número da agência da conta, o número da conta e o valor a ser descontado.  

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
  
__Frontend:__

* Pasta _templates_:
  Nessa pasta está os arquivos das telas em HTML.  
  * As telas são:  
    - Index  
    - Login  
    - Criar conta  
    - Depósito  
    - Transferência PIX  
    - Transferência TED  
    - Sacar  
    - Minhas chaves pix  
    - Dashboard

* Pasta _static_:  
  Nessa pasta está um arquivo único de CSS (styles.css) responsável pelas formas, cores e padrões da aplicação.

* Arquivo _app.py_  
  Este arquivo é responsável por integrar as funcionalidades das rotas com a interface do usuário (Back-end e Front-end).



# Especificações conforme o Barema:
1. __Permite gerenciar contas? O sistema realiza o gerenciamento de contas? Criar e realizar transações?__
- Sim, o sistema permite criar contas, realizar depósitos, fazer transações do tipo PIX, e do tipo TED.

2. __Permite selecionar e realizar transferência entre diferentes contas? É possível transacionar entre diferentes bancos? Por exemplo, enviar do banco A, B e
C, para o banco D?__ 
- Sim, a funcionalidade de transferência PIX permite realizar transferências entre diferentes contas, incluindo contas de bancos distintos. Na tela de transferência PIX, o usuário verá todas as suas contas existentes, tanto no banco atual quanto em outros bancos. Essa listagem de contas é possível devido à vinculação do atributo 'cpf_ou_cnpj' com as contas no momento da sua criação.  

- Na tela de transferência, o usuário poderá inserir a chave PIX de destino e os valores a serem transferidos de cada conta desejada. Isso possibilita enviar dinheiro de contas de diferentes bancos (por exemplo, dos bancos Bradesco e Neon) para uma conta em outro banco (por exemplo, o banco Picpay), de forma simples e eficiente.

3. __Comunicação entre servidores. Os bancos estão se comunicando com o protocolo adequado?__
- Sim, os bancos estão se comunicando via protocolo HTTP (Hypertext Transfer Protocol). Essa comunicação facilita a transferência de valores entre contas de maneira segura e eficiente, utilizando diversas rotas específicas para diferentes operações. As principais rotas incluem:  

  - /depositar
  - /transferencia/ted/enviar
  - /transferencia/pix/enviar
  - /transferencia/receber
  - /transferencia/pix/descontar
  - /transferencia/pix/reverter
  - /obter_contas

  - O HTTP é adequado para essa comunicação entre bancos por várias razões. Ele é um protocolo amplamente padronizado, o que facilita a integração entre sistemas de diferentes bancos. Além disso, o HTTP é simples de implementar, permitindo a troca de dados estruturados em formatos JSON. Ele também é adequado para sistemas escaláveis e distribuídos, permitindo que os servidores dos bancos possam aumentar a capacidade de seus sistemas conforme necessário.

4. __Sincronização em um único servidor. Como tratou a concorrência em um único servidor, quando chegam mais de um pedido de transação a um único servidor?__
-  A concorrência em um único servidor é tratada utilizando um mecanismo de bloqueio (lock) baseado em uma tabela de bloqueios (locks) no banco de dados. O objetivo é garantir que cada transação que afete uma conta específica seja processada de maneira segura, evitando inconsistências nos saldos das contas.
  
- A concorrência é tratada da seguinte maneira:
  - Aquisição de Bloqueio (Lock):
    - Quando uma operação é iniciada, o sistema tenta adquirir um bloqueio exclusivo para o recurso (neste caso, a conta bancária específica) utilizando a função acquire_lock(resource).  
    - O bloqueio é implementado como uma entrada na tabela Lock com a coluna locked que indica se o recurso está atualmente bloqueado.  
    - A função tenta repetidamente adquirir o bloqueio até um determinado tempo limite (timeout), esperando um curto período entre as tentativas (time.sleep(0.1)).
      
  - Liberação de Bloqueio:
    - Após a conclusão da operação, seja ela bem-sucedida ou não, o sistema libera o bloqueio utilizando a função release_lock(resource), que marca o recurso como desbloqueado (locked = False).

  - Operações Críticas:
    - As operações críticas, como depósitos, saques e transferências, são envolvidas por tentativas de aquisição e liberação de bloqueio.  
    - Se a aquisição do bloqueio falhar (por exemplo, porque o recurso está sendo utilizado por outra transação), a operação retorna uma resposta de erro apropriada (por exemplo, 423 'A conta de destino está sendo usada em outra operação').
       
  - Durante a aquisição do bloqueio (with_for_update(nowait=True)), o sistema utiliza operações no banco de dados para garantir que a verificação e a atualização do estado do bloqueio sejam atômicas.  
  - Se uma operação falhar, o sistema realiza um rollback para garantir que o estado do banco de dados permaneça consistente.  

  - Resumindo, quando múltiplos pedidos de transação são recebidos para uma conta, o bloqueio garante que apenas um processo por vez possa modificar o saldo, assegurando a consistência e evitando conflitos de dados.
    
5. __Algoritmo da concorrencia distribuída está teoricamente bem empregado? Qual algoritmo foi utilizado? Está correto para a solução?__
  - O sistema utiliza um mecanismo de locks distribuídos para gerenciar o acesso concorrente às contas bancárias. Cada conta é associada a uma chave de bloqueio (lock_key), garantindo que apenas um processo por vez possa modificar o saldo da conta. Esse método é fundamental para manter a consistência dos dados no ambiente distribuído, impedindo condições de corrida que poderiam ocorrer se múltiplos processos tentassem modificar o mesmo recurso simultaneamente.
    
  - Por exemplo, ao realizar uma transferência TED do banco Bradesco para o banco Neon, a rota /transferencia/receber no banco Neon escuta e processa a transação recebida. Antes de modificar o saldo da conta de destino, a rota adquire um lock específico para essa conta (representado pela lock_key associada à agência e conta). Esse lock é crucial para garantir que outras transações ou operações que afetem a mesma conta sejam bloqueadas temporariamente, assegurando a integridade dos dados durante a modificação do saldo.
    
  - Então, cada banco é responsável por gerenciar seus próprios locks, garantindo que a concorrência seja controlada localmente. Isso significa que a rota /transferencia/receber em cada banco atua de forma distribuída, bloqueando apenas as contas relevantes para as transações que chegam.

* Algoritmo de transferência PIX:  
  - Na transferência PIX, o sistema utiliza um algoritmo inspirado no Two-Phase Commit. A primeira fase é a de preparação, onde todas as contas de origem são verificadas para garantir que possuem saldo suficiente para a transferência. Cada conta é identificada pelo CPF ou CNPJ, e são adquiridos o código do banco, número de agência, número de conta e saldo.

  - Na segunda fase, os valores são descontados das contas de origem, similar à fase de commit do Two-Phase Commit. Se houver qualquer erro durante o desconto de alguma conta, o processo entra em uma fase de abortar, revertendo os saldos já descontados e cancelando a transferência.

  - Caso a fase de desconto ocorra com sucesso, a próxima etapa é direcionar o valor total das contas de origem para a conta de destino, através da chave PIX. Se ocorrer algum erro na transferência, os valores das contas de origem são revertidos, garantindo a integridade das transações.

    

6. __Algoritmo está tratrando o problema na prática? A implementação do algoritmo está funcionamento corretamente?__

- Na prática, o sistema implementado demonstra adequação ao contexto bancário, garantindo que operações como depósitos, transferências TED e PIX sejam tratadas de maneira confiável, mesmo sob cargas de trabalho distribuídas entre diferentes bancos.

- Para ilustrar a eficácia dos locks implementados, considere o cenário onde uma conta está recebendo duas transferências simultâneas: uma de outra conta no mesmo banco e outra de um banco externo. Quando a conta recebe a primeira transferência, um lock é adquirido temporariamente para garantir que apenas uma transação modifique seu saldo por vez. Enquanto isso, a segunda transferência, vinda de um banco externo, tenta adquirir o mesmo lock.

-  A tentativa de adquirir o lock é limitada a um timeout de 10 segundos. Se a conta consegue liberar o lock dentro desse período, a segunda transação poderá ser realizada. Caso contrário, se o lock não é liberado a tempo, a segunda transação é cancelada, garantindo que a integridade dos dados seja preservada e que apenas uma operação seja processada por vez para a conta em questão.
- As rotas que usam o sistema de locks são: a rota de saque, deposito, transferencia ted e pix, a rota de receber transferência e descontar valores.

* Algoritmo de transferência PIX:  
  - O algoritmo da transferência PIX consegue descontar o valor de cada conta de origem e transferir o total para a conta de destino. Em caso de qualquer erro durante o processo, os saldos descontados são revertidos para garantir a consistência dos dados.
  
7. __Tratamento da confiabilidade. Quando um dos bancos perde a conexão, o sistema continua funcionando corretamente? E quando o banco retorna à conexão?__
   
- Sim, quando o banco perde a conexão, a aplicação perde o contato com o servidor. No entanto, isso não resulta em erros graves na aplicação devido aos tratamentos de erro implementados. A aplicação continua tentando acessar as funcionalidades do banco, mas não consegue até que a conexão seja restabelecida. Quando a conexão volta, o sistema retorna ao funcionamento normal, permitindo que as operações sejam retomadas sem perda de dados ou inconsistências significativas.

  
8. __Pelo menos uma transação concorrente é realizada ? Como foi tratado o caso em que mais de duas transações ocorrem no mesmo banco de forma concorrente? O saldo fica correto? Os clientes conseguem realizar as transações?__
   
- Sim, o tratamento da concorrência é feito utilizando locks, conforme mencionado anteriormente. Quando uma transação é iniciada, um lock é adquirido para a conta específica, impedindo outras operações na mesma conta. As demais transações tentam adquirir o lock durante um período de até 10 segundos. Se o tempo se esgotar, apenas a transação que conseguiu obter o lock primeiro é realizada. No entanto, se o lock for liberado dentro do prazo, as transações subsequentes que conseguirem adquirir o bloqueio também são realizadas. Dessa forma, o saldo das contas permanece correto, e os clientes conseguem realizar suas transações de maneira consistente.


__Testes:__

Foram realizados dois testes, um para a concorrência distribuída e o outro para a concorrência em um único servidor.  

_concorrencia_distribuida.py:_  

No teste da concorrência distribuída foram criadas 7 contas no total, uma delas sendo conjunta e as outras 6 individuais. Entre essas 6 estava a conta de destino.  
Inicialmente, foi feito um depósito em cada conta no valor de 200 reais, exceto na conta de destino:

    Depósito: {'mensagem': 'Depósito realizado com sucesso'}
    Depósito: {'mensagem': 'Depósito realizado com sucesso'}
    Depósito: {'mensagem': 'Depósito realizado com sucesso'}
    Depósito: {'mensagem': 'Depósito realizado com sucesso'}
    Depósito: {'mensagem': 'Depósito realizado com sucesso'}
    Depósito: {'mensagem': 'Depósito realizado com sucesso'}
    
Cadastrando uma chave pix na conta de destino:

    Cadastro de Chave PIX: {'mensagem': 'Chave PIX cadastrada com sucesso'}
    
Depois, foram feitas 3 transferências pix para uma mesma conta para uma mesma conta do banco picpay:

    Transferência PIX (http://172.31.160.1:9637): {'mensagem': 'Transferência PIX realizada com sucesso'}
    Transferência PIX (http://172.31.160.1:9635): {'mensagem': 'Transferência PIX realizada com sucesso'}
    Transferência PIX (http://172.31.160.1:9636): {'mensagem': 'Transferência PIX realizada com sucesso'}

* Verificação dos saldos após transferências:
  
      Agência: 3071 Conta: 423313 - Saldo esperado: 100 - Saldo real: 100.0
      Agência: 2309 Conta: 350947 - Saldo esperado: 150 - Saldo real: 150.0
      Agência: 3013 Conta: 438669 - Saldo esperado: 100 - Saldo real: 100.0
      Agência: 4280 Conta: 471768 - Saldo esperado: 100 - Saldo real: 100.0
      Agência: 2031 Conta: 392858 - Saldo esperado: 125 - Saldo real: 125.0
      Agência: 4505 Conta: 366228 - Saldo esperado: 125 - Saldo real: 125.0
      Agência: 4078 Conta: 790459 - Saldo esperado: 500 - Saldo real: 500.0

Após isso, observa-se que todas ocorreram com sucesso, ou seja, a concorrência foi tratada corretamente.  
É importante ressaltar que todas essas transferências foram realizadas dos três bancos (Bradesco, Neon e PicPay) para um único banco (PicPay).

* À medida que se aumenta o número de transferências, algumas podem começar a falhar devido ao bloqueio de contas.

Ex:
- Aumentando mais uma transferência pix (mesmo teste com mais uma transferência).  
 
      Transferência PIX (http://172.31.160.1:9637): {'mensagem': 'Transferência PIX realizada com sucesso'}
      Transferência PIX (http://172.31.160.1:9637): {'mensagem': 'Transferência PIX realizada com sucesso'}
      Transferência PIX (http://172.31.160.1:9636): {'mensagem': 'Transferência PIX realizada com sucesso'}
      Transferência PIX (http://172.31.160.1:9635): {'erro': 'Falha na transferência PIX para o banco destino'}
  
- Então, a última transferência falha, devido ao bloqueio da conta de destino que está recebendo várias transferências concorrentes.

* Verificação dos saldos após transferências:
  
      Agência: 3689 Conta: 493661 - Saldo esperado: 100 - Saldo real: 150.0 # A falha ocorreu na transferência PIX desta conta.
      Agência: 2306 Conta: 597990 - Saldo esperado: 150 - Saldo real: 200.0 # A falha ocorreu na transferência PIX desta conta.
      Agência: 3047 Conta: 491849 - Saldo esperado: 100 - Saldo real: 100.0
      Agência: 4774 Conta: 503156 - Saldo esperado: 100 - Saldo real: 100.0
      Agência: 2323 Conta: 881032 - Saldo esperado: 50 - Saldo real: 50.0
      Agência: 4586 Conta: 368771 - Saldo esperado: 50 - Saldo real: 50.0
      Agência: 4464 Conta: 531200 - Saldo esperado: 650 - Saldo real: 550.0 # Conta de destino

Ou seja, as contas que falharam em transferir foram aquelas que estavam na transferência pix que não conseguiu adquirir o lock.

_concorrencia_local.py:_ 

No teste de concorrência em um único servidor, foram criadas três contas no banco bradesco: uma conta conjunta entre os clientes 1 e 2, e duas contas individuais, cada uma pertencente aos clientes 1 e 2, respectivamente.  
Inicialmente foi feito um depósito em cada conta no valor de 200 reais:

      Depósito: {'mensagem': 'Depósito realizado com sucesso'}
      Depósito: {'mensagem': 'Depósito realizado com sucesso'}
      Depósito: {'mensagem': 'Depósito realizado com sucesso'}

Depois, foi cadastrada uma chave pix na conta individual do cliente 2.

      Cadastro de Chave PIX: {'mensagem': 'Chave PIX cadastrada com sucesso'}

A seguir vieram as operações simultaneas:

      Depósito: {'mensagem': 'Depósito realizado com sucesso'}  # Mais um depósito na conta conjunta no valor de 200 reais.
      Saque: {'mensagem': 'Saque realizado com sucesso'} # Saque efetuado da conta conjunta no valor de 50 reais.
      Transferência TED: {'mensagem': 'Transferência realizada com sucesso'} # Transferência TED da conta conjunta para a conta individual do cliente 2 no valor de 100 reais.
      Transferência PIX: {'mensagem': 'Transferência PIX realizada com sucesso'} # Transferêcia pix das contas de origem do cliente 1 (conta conjunta e conta individual) no valor de 100 reais (50 reais de cada conta de origem).

* Verificação dos saldos após operações:
  
      Agência: 3719 Conta: 524714 - Saldo esperado: 200 - Saldo real: 200.0
      Agência: 3727 Conta: 654941 - Saldo esperado: 150 - Saldo real: 150.0
      Agência: 3637 Conta: 703450 - Saldo esperado: 400 - Saldo real: 400.0

Após isso, observou-se que todas as operações ocorreram com sucesso, indicando que a concorrência foi tratada corretamente.  
A conta conjunta, que teve o maior número de operações, apresentou um saldo coerente.  
Assim como no teste de concorrência distribuída, à medida que o número de operações aumenta, a probabilidade de uma transação ser cancelada devido ao bloqueio de recursos também aumenta. 

Ex:
- Aumentando mais duas transferência pix (mesmo teste com mais duas transferência).

      Depósito: {'mensagem': 'Depósito realizado com sucesso'}  
      Transferência PIX: {'mensagem': 'Transferência PIX realizada com sucesso'}
      Saque: {'mensagem': 'Saque realizado com sucesso'}
      Transferência PIX: {'mensagem': 'Transferência PIX realizada com sucesso'}
      Transferência TED: {'erro': 'A conta de origem está sendo usada em outra operação'}
      Transferência PIX: {'erro': 'A conta de origem está sendo usada em outra operação'}
  
  Nesse caso, durante as operações simultâneas, uma transferência PIX e uma TED falharam devido ao bloqueio.

  Verificação dos saldos após operações:

      Agência: 3232 Conta: 474422 - Saldo esperado: 100 - Saldo real: 250.0
      Agência: 3683 Conta: 436082 - Saldo esperado: 50 - Saldo real: 100.0
      Agência: 3032 Conta: 307237 - Saldo esperado: 600 - Saldo real: 400.0
  
   Observou-se que, apesar de duas transferências terem sido canceladas, os saldos permaneceram corretos.

__CONCLUSÃO:__
