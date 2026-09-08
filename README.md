# ExquemaTatico API

Backend do ExquemaTatico, um quadro tático de futebol digital. O usuário monta esquemas
(formação, jogada, bola parada), posiciona os dois times num campo e salva numa biblioteca
pessoal. Esta API guarda esses esquemas em SQLite e os expõe por REST com documentação
Swagger.

O frontend fica em outro repositório: `exquematatico-front`.

![Editor do ExquemaTatico consumindo esta API](docs/editor.png)

## Arquitetura

- `app.py`: cria a aplicação Flask (via flask-openapi3), declara os modelos Pydantic usados
  no Swagger, os handlers de erro e as rotas. As rotas são finas: recebem, chamam o serviço,
  respondem.
- `services.py`: regras de negócio. Valida o payload, monta as variações iniciais e executa
  as operações no banco em transação.
- `formacao.py`: converte a string de formação (`4-3-3`) nas coordenadas dos 11 jogadores e
  aplica o deslocamento que gera as variações Ofensivo e Defensivo.
- `formacoes_reais.py`: só dado, sem lógica. Posicionamento real das formações mais comuns,
  consultado por `formacao.py`.
- `database.py`: conexão SQLite (com `PRAGMA foreign_keys = ON`, necessário para o CASCADE
  funcionar), schema e `init_db()`, executado automaticamente ao subir a API.
- `seed.py`: opcional, cria dois esquemas de exemplo.

O banco é o arquivo `exquematatico.db`, criado ao lado de `app.py` na primeira execução.

### Modelo

Um **esquema** tem `nome`, `formacao`, `tipo` (`ofensivo`, `defensivo` ou `bola_parada`),
`anotacoes` e uma lista de **variações**.

Cada variação é um posicionamento completo dos dois times. Todo esquema nasce com três
variações fixas, geradas a partir da formação:

| Variação  | Chave       | O que representa                                  |
| --------- | ----------- | ------------------------------------------------- |
| Padrão    | `padrao`    | Os dois times em suas metades, formação neutra    |
| Ofensivo  | `ofensivo`  | O time da casa avança; o adversário recua          |
| Defensivo | `defensivo` | O time da casa recua; o adversário avança         |

Além dessas, o usuário adiciona quantas variações **personalizadas** quiser (chave `custom`,
nome livre). As três fixas não podem ser excluídas; as personalizadas sim.

Um payload que traga `variacoes` explicitamente precisa conter exatamente uma `padrao`, uma
`ofensivo` e uma `defensivo`, mais quantas `custom` quiser, com nomes distintos entre si. Como
a API recusa excluir as fixas depois, aceitar um payload sem elas deixaria o esquema num
estado que nenhuma rota consegue produzir nem corrigir.

Cada variação tem dois times, `casa` e `visitante`, com seus **jogadores**. Um jogador tem
`numero` (1-99, único no time), `papel` (texto curto, ex.: GOL, ZAG, PONTA), `em_campo` e as
coordenadas `x`/`y`.

`x` e `y` são a posição percentual (0 a 100) do centro da ficha em relação ao campo. `(0, 0)`
é o canto superior esquerdo e `(100, 100)` o inferior direito. Por serem percentuais, o
quadro é independente do tamanho da tela. Um jogador com `em_campo: false` está no banco, e
aí `x` e `y` são nulos.

O campo é horizontal, na proporção 111 x 72. A casa defende à esquerda (goleiro em `x = 6`) e
ataca para a direita; o adversário é o espelho, com o goleiro em `x = 94`.

Além dos jogadores, a variação guarda a **bola** (`{"x": ..., "y": ...}`, no centro por
padrão) e três camadas de marcação tática, todas opcionais e nas mesmas coordenadas
percentuais:

| Camada      | Conteúdo                                                              |
| ----------- | --------------------------------------------------------------------- |
| `desenhos`  | Setas: `tipo` `mov` (movimentação) ou `passe`, com `x1`/`y1`/`x2`/`y2` |
| `zonas`     | Retângulos: `time` (`casa`, `visitante`, `neutra`), `x`, `y`, `largura`, `altura` |
| `anotacoes` | Notas curtas: `texto` (até 40 caracteres), `x`, `y`                   |

As três são substituídas por inteiro a cada PUT da variação: o payload é o estado final, não
um delta. Enviar a variação sem uma delas esvazia aquela camada.

O limite é de 11 jogadores em campo por time. É permitido salvar com menos, para o usuário
montar o esquema aos poucos.

`criado_em` é gerado pelo servidor em ISO 8601 UTC. O cliente nunca o envia; o PUT preserva o
original e a duplicação gera um novo.

Mudar a `formacao` de um esquema existente regenera todas as variações a partir da formação
nova, inclusive as personalizadas, que mantêm o nome e recebem o posicionamento do Padrão. O
posicionamento anterior descreve a formação antiga e não sobrevive à troca — sem isso o campo
contradiz o rótulo do esquema. Enviar `variacoes` no mesmo PUT tem precedência: valem as
variações do payload.

### Formação

A formação lista os jogadores de linha do setor mais defensivo ao mais ofensivo, sem contar o
goleiro, e precisa somar 10: `4-3-3`, `4-4-2`, `4-2-3-1`, `3-5-2`.

As posições vêm de duas fontes. As formações de `formacoes_reais.py` (`4-3-3`, `4-4-2`,
`4-2-3-1`, `3-5-2`, `3-1-4-2` e `5-4-1`) usam posicionamento real, extraído de dados de
partidas.
Qualquer outra formação válida cai na regra geométrica de `formacao.py`, que distribui cada
setor numa faixa do campo e nomeia os papéis, virando lateral nas pontas de uma linha de
quatro e ponta nas pontas de um ataque de três.

Nos dois casos o retorno é o mesmo, e o espelhamento do adversário e o deslocamento das
variações se aplicam igual. A diferença aparece só na precisão do posicionamento: o dado real
distingue ponta direita de esquerda, por exemplo, enquanto a geometria usa um papel só.

## Instalação e execução

Requer Python 3.10 ou superior. Sem Docker, sem banco externo: o SQLite é um arquivo criado
automaticamente na primeira execução.

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed.py     # opcional: cria dois esquemas de exemplo
python app.py
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py     # opcional: cria dois esquemas de exemplo
python app.py
```

A API sobe em `http://localhost:5001`. A porta 5001 foi escolhida porque no macOS o AirPlay
Receiver ocupa a 5000 por padrão. Para usar outra porta, altere a última linha de `app.py` e a
constante `API_BASE_URL` em `js/api.js` no frontend.

Se `python -m venv` falhar no Ubuntu/Debian, instale o pacote `python3-venv`.

## Testes

```powershell
python -m unittest discover -p "test_*.py" -v
```

Duas suítes:

- `test_services.py` — validação de payload, geração de formação, CRUD, regeneração de
  variações, cascata do banco e migração de um banco criado antes das colunas da bola.
- `test_rotas.py` — as nove rotas por HTTP com `app.test_client()`: códigos de status,
  serialização, erros em JSON, CORS para a origem `null` do `file://` e o documento OpenAPI.

Cada suíte roda num SQLite temporário próprio, então nenhuma toca o `exquematatico.db` de
trabalho e nenhuma precisa da API no ar.

## Swagger

Documentação interativa em `http://localhost:5001/openapi`, com exemplos de payload em todas
as rotas. A especificação bruta fica em `http://localhost:5001/openapi/openapi.json`.

## Rotas

| Método | Rota                                          | Resposta                                          |
| ------ | --------------------------------------------- | ------------------------------------------------- |
| GET    | `/esquemas`                                   | 200 lista com variações; `?tipo=` filtra (400 se inválido) |
| GET    | `/esquemas/{id}`                              | 200 esquema completo, 404                          |
| POST   | `/esquemas`                                   | 201 esquema criado com as três variações, 400      |
| PUT    | `/esquemas/{id}`                              | 200 esquema atualizado, 400, 404                   |
| DELETE | `/esquemas/{id}`                              | 204, 404                                           |
| POST   | `/esquemas/{id}/duplicar`                     | 201 cópia com nome "Cópia de {nome}", 404          |
| POST   | `/esquemas/{id}/variacoes`                    | 201 esquema com a variação criada, 400, 404        |
| PUT    | `/esquemas/{id}/variacoes/{variacao_id}`      | 200 esquema atualizado, 400, 404                   |
| DELETE | `/esquemas/{id}/variacoes/{variacao_id}`      | 204, 400 (se for fixa), 404                        |

Erros sempre vêm como JSON `{"erro": "mensagem em pt-BR"}`.

Criar um esquema não exige posições: omitindo `variacoes`, a API monta Padrão, Ofensivo e
Defensivo a partir da formação.

```json
{
  "nome": "4-3-3 pressão alta",
  "formacao": "4-3-3",
  "tipo": "ofensivo",
  "anotacoes": "Pontas abertos, laterais apoiam."
}
```

Para reposicionar, envie a variação inteira no PUT:

```json
{
  "nome": "Padrão",
  "casa": [
    {"numero": 1, "papel": "GOL", "em_campo": true, "x": 6, "y": 50},
    {"numero": 12, "papel": "ATA", "em_campo": false, "x": null, "y": null}
  ],
  "visitante": [
    {"numero": 1, "papel": "GOL", "em_campo": true, "x": 94, "y": 50}
  ],
  "bola": {"x": 12, "y": 50},
  "desenhos": [{"tipo": "passe", "x1": 13.6, "y1": 81.5, "x2": 28.8, "y2": 66.8}],
  "zonas": [{"time": "casa", "x": 4, "y": 30, "largura": 22, "altura": 40}],
  "anotacoes": [{"texto": "Zagueiro abre", "x": 18, "y": 24}]
}
```

Adicionar uma variação personalizada sem enviar jogadores copia o Padrão como ponto de
partida:

```json
{"nome": "Escanteio pela direita"}
```

## CORS

`flask-cors` libera qualquer origem, então o frontend pode rodar em outra porta
(por exemplo `http://localhost:8000`) sem configuração extra.
