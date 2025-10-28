# Documentação da API

Esta API utiliza FastAPI para gerenciar usuários, formulários, respostas e integrações corporativas. Todas as rotas protegidas exigem autenticação JWT via cabeçalho `Authorization: Bearer <token>`, e muitas operações também dependem de permissões específicas associadas ao grupo do usuário autenticado.

## Visão Geral
- **Base URL padrão**: `http://localhost:8000`
- **Formato de dados**: JSON por padrão. Endpoints de upload utilizam `multipart/form-data`.
- **Autenticação**: Tokens JWT de acesso curto e refresh token.
- **Autorização**: Permissões por grupo. Quando indicado, inclua a permissão listada para acessar a rota.
- **Erros**: Respostas seguem o padrão `{"detail": "mensagem"}` com os códigos HTTP apropriados (`400`, `401`, `403`, `404`, `409`).

## Autenticação e sessão (`/auth`)
| Método | Caminho | Corpo | Resposta | Notas |
| --- | --- | --- | --- | --- |
| `POST` | `/auth/login` | `LoginInput` (`username`, `password`) | `LoginResponse` contendo tokens e dados do usuário | Requer que o usuário exista e esteja ativo.【F:app/routers/auth.py†L15-L39】|
| `POST` | `/auth/logout` | - | Mensagem de sucesso | Apenas invalida no cliente.【F:app/routers/auth.py†L41-L43】|
| `POST` | `/auth/refresh` | `{ "refresh_token": "..." }` | Novo `access_token` e `token_type` | Falha com `401` se o refresh token for inválido ou expirado.【F:app/routers/auth.py†L45-L56】|

Inclua `Authorization: Bearer <access_token>` em chamadas subsequentes. Para WebSockets, o token pode ser enviado em `?access_token=`, cookie `access_token`, cabeçalho `Authorization` ou `Sec-WebSocket-Protocol` com valor `Bearer <token>`.【F:app/dependencies/auth.py†L41-L73】

## Setup inicial (`/setup`)
| Método | Caminho | Corpo | Resposta | Notas |
| --- | --- | --- | --- | --- |
| `POST` | `/setup/` | `multipart/form-data` com `empresa_data` (JSON de `EmpresaCreate`), `usuario_data` (JSON de `UsuarioCreate`), opcional `logo_empresa` e `imagem_usuario` | `SetupResponse` com empresa e usuário criados | Somente permitido enquanto não existir administrador. Uploads são armazenados em `MEDIA_ROOT`.【F:app/routers/setup.py†L18-L83】|
| `GET` | `/setup/status` | - | Status de existência de admin, grupo admin e dados do usuário autenticado | Disponível com ou sem autenticação; utiliza token se enviado.【F:app/routers/setup.py†L85-L108】|

## Perfil (`/me`)
| Método | Caminho | Corpo | Resposta | Permissão |
| --- | --- | --- | --- | --- |
| `GET` | `/me` | - | `UsuarioResponse` com dados completos | Requer autenticação.【F:app/routers/perfil.py†L12-L14】|
| `DELETE` | `/me` | - | `204 No Content` | Remove o próprio usuário autenticado.【F:app/routers/perfil.py†L16-L18】|

## Usuários (`/usuarios`)
| Método | Caminho | Corpo | Resposta | Permissão |
| --- | --- | --- | --- | --- |
| `POST` | `/usuarios/` | `UsuarioCreate` | `LoginResponse` com tokens recém-gerados | `usuarios:criar` e ser admin (validação extra).【F:app/routers/user.py†L24-L65】|
| `GET` | `/usuarios/` | - | Lista de `UsuarioResponse` | `usuarios:ver`. URLs de imagem são absolutas.【F:app/routers/user.py†L68-L80】|
| `GET` | `/usuarios/{usuario_id}` | - | `UsuarioResponse` | `usuarios:ver`. Retorna `404` se não existir.【F:app/routers/user.py†L82-L91】|
| `GET` | `/usuarios/{usuario_id}/permissoes` | - | Objeto com permissões agregadas | Sem permissão explícita; retorna grupo e códigos efetivos.【F:app/routers/user.py†L93-L109】|
| `PUT` | `/usuarios/{usuario_id}` | `UsuarioUpdate` | `UsuarioResponse` atualizado | Apenas o próprio usuário pode editar; campos de grupo são bloqueados.【F:app/routers/user.py†L111-L145】|
| `PUT` | `/usuarios/grupo/{usuario_id}` | `UsuarioGrupoUpdate` | `UsuarioResponse` | `usuarios:editar`; altera somente o grupo.【F:app/routers/user.py†L147-L169】|
| `DELETE` | `/usuarios/{usuario_id}` | - | `204 No Content` | `usuarios:deletar`; impede autoexclusão e remoção de admins.【F:app/routers/user.py†L171-L194】|
| `PATCH` | `/usuarios/{usuario_id}/senha` | `{ "senha": "..." }` | `UsuarioResponse` | Usuário próprio ou admin.【F:app/routers/user.py†L198-L214】|
| `POST` | `/usuarios/me/imagem` | Upload `arquivo` | Metadados e URL pública | Salva ou substitui imagem do perfil autenticado.【F:app/routers/user.py†L226-L249】|
| `PUT` | `/usuarios/me/imagem` | Upload `arquivo` | Metadados e URL pública | Atualiza imagem existente.【F:app/routers/user.py†L251-L270】|
| `GET` | `/usuarios/me/imagem` | - | Redirect para URL pública | Retorna `404` se não cadastrada.【F:app/routers/user.py†L272-L280】|
| `GET` | `/usuarios/me/imagem/raw` | - | Arquivo binário | Cabeçalho `Content-Type` deduzido por extensão.【F:app/routers/user.py†L282-L289】|
| `GET` | `/usuarios/{usuario_id}/imagem` | - | Redirect para URL pública | Requer `usuarios:ver`.【F:app/routers/user.py†L291-L299】|
| `GET` | `/usuarios/{usuario_id}/imagem/raw` | - | Arquivo binário | Requer `usuarios:ver`.【F:app/routers/user.py†L301-L308】|

## Grupos (`/grupos`)
| Método | Caminho | Corpo | Resposta | Permissão |
| --- | --- | --- | --- | --- |
| `GET` | `/grupos/` | - | Lista de `GrupoComPermissoesResponse` ou itens resumidos | `grupos:ver`. Detalhes de permissões são retornados apenas se o usuário puder ver permissões.【F:app/routers/grupo.py†L20-L43】|
| `GET` | `/grupos/grupo-admin-id` | - | `{ "grupo_id": "..." }` | Utilizado para localizar o grupo administrador.【F:app/routers/grupo.py†L45-L48】|
| `POST` | `/grupos/` | `GrupoCreate` | `GrupoResponse` | Cria um novo grupo.【F:app/routers/grupo.py†L50-L55】|
| `PUT` | `/grupos/{grupo_id}` | `GrupoUpdate` | Mensagem de sucesso | `grupos:editar`; bloqueia alterações no grupo `admin`.【F:app/routers/grupo.py†L63-L92】|
| `DELETE` | `/grupos/{grupo_id}` | - | `204 No Content` | `grupos:deletar`; retorna `409` se houver usuários associados.【F:app/routers/grupo.py†L57-L81】|

## Permissões e ACL de formulários (`/permissoes`)
| Método | Caminho | Corpo | Resposta | Permissão |
| --- | --- | --- | --- | --- |
| `GET` | `/permissoes/` | - | Lista de `PermissaoResponse` | `permissoes:ver`.【F:app/routers/permissao.py†L13-L16】|
| `GET` | `/permissoes/{formulario_id}/acl` | - | Lista de `FormularioPermissaoOut` | `permissoes:configurar_acl`.【F:app/routers/permissao.py†L18-L30】|
| `PUT` | `/permissoes/{formulario_id}/acl` | `FormularioPermissaoIn` | `FormularioPermissaoOut` | Cria ou atualiza um registro ACL.【F:app/routers/permissao.py†L32-L44】|
| `PUT` | `/permissoes/{formulario_id}/acl/batch` | `FormularioPermissaoBatchIn` | Lista de `FormularioPermissaoOut` | Upsert em lote.【F:app/routers/permissao.py†L46-L61】|
| `DELETE` | `/permissoes/{formulario_id}/acl/{grupo_id}` | - | `204 No Content` | Remove ACL específica.【F:app/routers/permissao.py†L63-L69】|

## Formulários (`/formularios`)
| Método | Caminho | Corpo | Resposta | Permissão |
| --- | --- | --- | --- | --- |
| `POST` | `/formularios/` | `FormularioCreate` com perguntas | `FormularioOut` | `formularios:criar`.【F:app/routers/forms.py†L12-L21】|
| `GET` | `/formularios/` | Query `incluir_inativos` (bool) | Lista de `FormularioOut` | `formularios:ver`; filtra por ACL do grupo.【F:app/routers/forms.py†L23-L30】|
| `GET` | `/formularios/{formulario_id}` | - | `FormularioOut` | `formularios:ver`; valida ACL `pode_ver`.|【F:app/routers/forms.py†L32-L47】
| `DELETE` | `/formularios/{formulario_id}` | - | `204 No Content` | `formularios:apagar`; verifica ACL `pode_apagar`.【F:app/routers/forms.py†L49-L65】|
| `POST` | `/formularios/{formulario_id}/restaurar` | - | `204 No Content` | `formularios:restaurar`; exige permissão específica via ACL.【F:app/routers/forms.py†L76-L85】|
| `GET` | `/formularios/{formulario_id}/slug` | - | `{ "slug_publico": "..." }` | Recupera slug público ativo.【F:app/routers/forms.py†L67-L74】|
| `GET` | `/formularios/tipos-perguntas/` | - | Lista de tipos disponíveis | `formularios:criar`. Retorna `value` e `label` de cada enum.【F:app/routers/forms.py†L86-L90】|
| `GET` | `/formularios/publico/{slug}` | - | `FormularioPublicoResponse` | Acesso público sem autenticação.【F:app/routers/forms.py†L92-L104】|
| `POST` | `/formularios/{formulario_id}/publicar` | - | `{ "slug_publico", "recebendo_respostas" }` | `formularios:editar` e ACL `pode_editar`; ativa formulários públicos.【F:app/routers/forms.py†L106-L130】|
| `POST` | `/formularios/{formulario_id}/despublicar` | - | `{ "slug_publico", "recebendo_respostas" }` | `formularios:editar` e ACL `pode_editar`; desativa respostas públicas.【F:app/routers/forms.py†L132-L152】|

## Respostas (`/respostas`)
| Método | Caminho | Corpo | Resposta | Permissão |
| --- | --- | --- | --- | --- |
| `POST` | `/respostas/{form_slug}` | `RespostaCreatePublico` | `RespostaOut` | Público; registra IP e publica evento em tempo real.【F:app/routers/respostas.py†L15-L40】|
| `GET` | `/respostas/formulario/{formulario_id}` | - | Lista de `RespostaOut` | `respostas:ver`; filtra por grupo do usuário.|【F:app/routers/respostas.py†L42-L49】
| `GET` | `/respostas/{resposta_id}` | - | `RespostaOut` | `respostas:ver`. Retorna `404` se não existir.【F:app/routers/respostas.py†L51-L57】|
| `DELETE` | `/respostas/{resposta_id}` | - | `204 No Content` | `respostas:apagar`. Retorna `404` se não existir.【F:app/routers/respostas.py†L59-L64】|

## Empresa (`/empresa`)
| Método | Caminho | Corpo | Resposta | Permissão |
| --- | --- | --- | --- | --- |
| `GET` | `/empresa/` | - | `EmpresaResponse` | `empresa:ver`. Retorna a empresa única cadastrada.【F:app/routers/empresa.py†L16-L21】|
| `PUT` | `/empresa/` | `EmpresaUpdate` | `EmpresaResponse` | `empresa:editar`. Valida campos e existência.【F:app/routers/empresa.py†L23-L33】|
| `POST` | `/empresa/logo` | Upload `arquivo` | Metadados e URL pública | `empresa:editar`. Substitui a logo atual.【F:app/routers/empresa.py†L35-L56】|
| `PUT` | `/empresa/logo` | Upload `arquivo` | Metadados e URL pública | `empresa:editar`. Mesmo fluxo do POST.【F:app/routers/empresa.py†L58-L77】|
| `GET` | `/empresa/logo` | - | Redirect para URL pública | `empresa:ver`. Falha com `404` se não existir logo.【F:app/routers/empresa.py†L79-L86】|
| `GET` | `/empresa/logo/raw` | - | Arquivo binário | `empresa:ver`. Retorna `404` se arquivo ausente no disco.【F:app/routers/empresa.py†L88-L96】|

## Integrações (`/integracoes`)
| Método | Caminho | Corpo | Resposta | Permissão |
| --- | --- | --- | --- | --- |
| `POST` | `/integracoes` | `IntegracaoCreate` | `IntegracaoOut` | `integracoes:criar`.【F:app/routers/integracoes.py†L9-L15】|
| `GET` | `/integracoes` | - | Lista de `IntegracaoOut` | `integracoes:ver`.【F:app/routers/integracoes.py†L17-L20】|
| `GET` | `/integracoes/{integracao_id}` | - | `IntegracaoOut` | `integracoes:ver`; retorna `404` se ausente.【F:app/routers/integracoes.py†L22-L28】|
| `PATCH` | `/integracoes/{integracao_id}` | `IntegracaoEdit` | `IntegracaoOut` | `integracoes:editar` para alterar tipo/configuração.【F:app/routers/integracoes.py†L30-L33】|
| `PATCH` | `/integracoes/{integracao_id}/habilitacao` | `{ "habilitada": bool }` | `IntegracaoStatusOut` com `conexao_ok` | `integracoes:editar`; ajusta habilitação e testa conexão.【F:app/routers/integracoes.py†L35-L46】|

## WebSockets
### Formulários
- **`GET /ws/formularios/{formulario_id}`**: Requer `formularios:editar` e ACL `pode_editar`. Envia `estado_inicial`, atualizações `formulario_atualizado` e presença na sala. Mensagens aceitas:
  - `{"tipo": "update_formulario", "conteudo": { ... }}` com payload parcial para atualização.
- **`GET /ws/formularios/`**: Requer autenticação. Eventos importantes: `lista_inicial`, `usuarios_na_sala`, `ping/pong`. Permite solicitar incluir inativos com `{"tipo": "subscribe_formularios", "conteudo": {"incluir_inativos": true}}`.

Ambos utilizam o gerenciador de conexões para broadcast e limpam perguntas inativas nos payloads.【F:app/websockets/forms.py†L11-L112】【F:app/websockets/forms.py†L114-L181】

### Respostas
- **`GET /ws/respostas/formulario/{formulario_id}`**: Requer autenticação. Entrega `bootstrap_respostas` (últimas 50) e atualizações em tempo real sempre que novas respostas são criadas. Mensagens recebidas retornam `ack` para confirmar o recebimento.【F:app/websockets/respostas.py†L12-L49】

## Uploads e URLs de mídia
- Uploads de imagens de usuário e logo de empresa são processados e armazenados em `settings.MEDIA_ROOT`. Ao atualizar uma imagem existente, o arquivo anterior é removido.【F:app/routers/user.py†L231-L248】【F:app/routers/empresa.py†L35-L76】
- URLs públicas são construídas a partir de `settings.BASE_URL` + `settings.MEDIA_URL` e retornadas tanto em respostas JSON quanto via redirecionamento HTTP.【F:app/routers/user.py†L226-L248】【F:app/routers/empresa.py†L16-L55】

## Regras de permissões
- Permissões são avaliadas por código (ex.: `usuarios:ver`). O helper `require_permission` rejeita chamadas com `403` quando o código não está associado ao grupo do usuário.【F:app/dependencies/permissoes.py†L18-L35】
- Para WebSockets, `require_permission_ws` verifica tanto o token quanto as ACLs específicas do formulário antes de aceitar a conexão, encerrando com códigos `4401/4403` se falhar.【F:app/dependencies/permissoes.py†L49-L78】

Use esta documentação como referência para integrar clientes web, mobile ou integrações de terceiros à API.
