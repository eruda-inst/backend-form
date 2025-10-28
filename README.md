# backend-form

Este repositório serve como o backend de uma aplicação destinada à criação, visualização e gerenciamento de formulários.
Ele deverá disponibilizar endpoints para que clientes possam definir novos formulários, consultar respostas e administrar os formulários já cadastrados.

Embora a estrutura atual seja simples, este projeto é o ponto inicial para o desenvolvimento da API que irá persistir e manipular dados de formulários.

## Gerenciamento de Usuários

A aplicação fornece um conjunto de endpoints para cadastro, consulta, atualização e exclusão de usuários. As senhas são armazenadas de forma segura utilizando hash (bcrypt).

## Documentação da API

Uma descrição completa de todos os endpoints, requisitos de autenticação, permissões e fluxos WebSocket está disponível em [docs/API.md](docs/API.md).

### Instalação

```bash
pip install -r requirements.txt
```

### Execução

```bash
uvicorn app.main:app --reload
```
