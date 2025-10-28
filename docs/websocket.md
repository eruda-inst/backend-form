# Documentação do funcionamento websocket

## ws://localhost:8000/ws/formularios/ID_DO_FORMULARIO

### Estrutura básica
Toda mensagem enviada via WebSocket segue este padrão:
```json
{
  "tipo": "<ação>",
  "conteudo": { ... }
}
```

---

### 1️⃣ Criar bloco
```json
{
  "tipo": "update_formulario",
  "conteudo": {
    "blocos_adicionados": [
      {
        "titulo": "Etapa 1: Dados Pessoais",
        "descricao": "Informações básicas do participante"
      }
    ]
  }
}
```

---

### 2️⃣ Editar bloco
```json
{
  "tipo": "update_formulario",
  "conteudo": {
    "blocos_editados": [
      {
        "id": "7149405b-9720-470e-a5d8-1b73e63eca50",
        "titulo": "Bloco 2 - O teste"
      }
    ]
  }
}
```

---

### 3️⃣ Remover bloco
```json
{
  "tipo": "update_formulario",
  "conteudo": {
    "blocos_removidos": [
      "7149405b-9720-470e-a5d8-1b73e63eca50"
    ]
  }
}
```

---

### 4️⃣ Criar pergunta
```json
{
  "tipo": "update_formulario",
  "conteudo": {
    "perguntas_adicionadas": [
      {
        "bloco_id": "fd460b53-a4af-4b8d-acc8-a8ada3877981",
        "texto": "Qual é o seu nome?",
        "tipo": "texto_simples",
        "obrigatoria": true,
        "ordem_exibicao":1
      }
    ]
  }
}
```

---

### 5️⃣ Editar pergunta
```json
{
  "tipo": "update_formulario",
  "conteudo": {
    "perguntas_editadas": [
      {
        "id": "39c15b3e-927d-4cc7-bb7a-24a02cc26a91",
        "texto": "Qual é o seu primeiro nome?",
        "obrigatoria": false,
        "bloco_id": "fd460b53-a4af-4b8d-acc8-a8ada3877981"
      }
    ]
  }
}
```

---

### 6️⃣ Remover pergunta
```json
{
  "tipo": "update_formulario",
  "conteudo": {
    "perguntas_removidas": [
      "39c15b3e-927d-4cc7-bb7a-24a02cc26a91"
    ]
  }
}
```


## ws://localhost:8000/ws/formularios/

### Apenas devolve todos os formulários que o usuário tem permissão para ver

## ws://localhost:8000/ws/respostas/formulario/ID_DO_FORMULARIO

### Apenas devolve todas as respostas dos formulários que o usuário tem permissão para ver