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

Instalar a biblioteca responsável pelo banco de dados (SQLAlchemy), que armazena os dados de conta e titulares (Apenas os servidores dos bancos utilizam o SQLAlchemy). Instale usando o prompt de comando com:  

    pip install SQLAlchemy
    
Por fim, instalar uma biblioteca adicional para exibir continualmente as informações de conta do banco, que é a biblioteca tabulate (Isso foi implementado pensando no docker, já que não tem como usar a extensão SQL Viewer na execução do container). Instale usando o prompt de comando com:  

    pip install tabulate


__Utilização do Programa (Execução)__  

__Tabela de Roteamento (table_router.py)__  

A tabela de roteamento é responsável por armazenar as rotas específicas dos bancos. Quando um banco deseja realizar uma operação para outro banco, ele consulta essa tabela para determinar a rota correta do banco de destino.

Iniciar a tabela de roteamento: Execute o arquivo table_router.py utilizando Python. Este servidor ficará ativo aguardando o registro das rotas pelos bancos. Posteriormente, outros bancos poderão realizar operações distribuídas consultando esta tabela. 


__Bancos(Bradesco.py, Picpay.py e Neon.py)__

Os bancos são responsáveis por disponibilizar serviços à aplicação, como movimentação de saldo através de transferências, depósitos e saques. Além disso, cada banco deve registrar suas rotas na tabela de roteamento e consultar essa tabela para realizar operações distribuídas de forma eficiente.  

Iniciar bancos: Depois da tabela de roteamento executada
