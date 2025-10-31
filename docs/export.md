# Exportação

A funcionalidade de exportação permite extrair as respostas de um formulário em diferentes formatos, facilitando a análise e o uso dos dados coletados. Os formatos disponíveis são CSV, NDJSON e XLSX.

## Endpoint

```
GET /formularios/:id/exportar
```

## Parâmetros de consulta

| Parâmetro     | Descrição                                                                 | Valor padrão  |
| ------------- | ------------------------------------------------------------------------- | ------------- |
| `inicio`      | Data inicial para filtrar as respostas (formato ISO 8601).                | Sem filtro    |
| `fim`         | Data final para filtrar as respostas (formato ISO 8601).                  | Sem filtro    |
| `formato`     | Formato do arquivo exportado. Pode ser `csv`, `ndjson` ou `xlsx`.         | `csv`         |
| `fuso`        | Fuso horário para ajustar as datas no arquivo exportado (ex: `America/Sao_Paulo`). | UTC           |
| `separador`   | Separador usado no arquivo CSV (ex: `,` ou `;`).                          | `,`           |
| `apenas_ativas`| Se `true`, exporta apenas as perguntas ativas no momento da exportação.  | `false`       |

## Descrição dos formatos

- **CSV**: Arquivo de texto separado por vírgulas ou outro separador especificado, contendo as respostas organizadas em colunas, uma linha por resposta.
- **NDJSON**: Arquivo JSON com uma resposta por linha, ideal para processamento em lote e integração com outras ferramentas.
- **XLSX**: Planilha Excel contendo as respostas, com formatação adequada para visualização e análise.

Os dados exportados incluem todas as respostas do formulário, respeitando os filtros de data e estado das perguntas.

## Exemplos de requisições

- Exportação padrão em CSV:
  ```
  GET /formularios/123/exportar
  ```

- Exportação filtrando respostas entre duas datas:
  ```
  GET /formularios/123/exportar?inicio=2023-01-01T00:00:00Z&fim=2023-01-31T23:59:59Z
  ```

- Exportação apenas com perguntas ativas:
  ```
  GET /formularios/123/exportar?apenas_ativas=true
  ```

- Exportação em formato XLSX com fuso horário de São Paulo:
  ```
  GET /formularios/123/exportar?formato=xlsx&fuso=America/Sao_Paulo
  ```

## Autenticação

A exportação requer autenticação via JWT e a permissão `formularios:ver` para acesso ao formulário.

## Considerações de desempenho e timezone

Para garantir desempenho adequado, o banco de dados possui índice nas colunas `(formulario_id, criado_em)`, acelerando a filtragem por formulário e data.

As datas no arquivo exportado são ajustadas conforme o fuso horário informado no parâmetro `fuso`. Caso não seja informado, o padrão é UTC.

## Nome do arquivo exportado

O arquivo gerado terá o nome no formato:

```
form_<id>_respostas.<ext>
```

onde `<id>` é o identificador do formulário e `<ext>` é a extensão correspondente ao formato escolhido (`csv`, `ndjson` ou `xlsx`).
