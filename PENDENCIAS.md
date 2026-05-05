# Monitoria da Qualidade — Estado do Projeto e Pendências

> **Última atualização:** 2026-04-29 (fim do dia)
> **Baseline congelado:** v0.3 (esta versão)
> **Princípio:** sem reescrever o passado. As próximas frentes apenas estendem o que está aqui.

## 🔒 Decisões de governança gravadas (não revisitar sem combinar)

**Decisão N1 — Modelo de nota após réplica acolhida (decidido em 2026-04-29):**
> Quando supervisor responder "Acolho — ajustar avaliação" na réplica do perito, **a `nota_final` original é preservada intocada** e uma nova coluna **`nota_ajustada`** recebe o novo valor. Todos os dashboards, KPIs, relatórios e exportações **usam a nota efetiva** definida como `COALESCE(nota_ajustada, nota_final)`. Isso garante auditoria total — em qualquer momento dá pra ver o que era antes e o que ficou depois da contestação. Esse é o **modelo Opção A** discutido na decisão da Pendência 5.

**Decisão N2 — Validação humana de monitorias automáticas (a confirmar):**
> Sugestão registrada: monitorias geradas pelo agente NotebookLM entram com `status='pendente_validacao'` e exigem aprovação do supervisor antes de virarem definitivas. Auto-aprovação só será considerada quando o KPI "% aprovadas sem alteração" passar de 90% por 3 meses consecutivos.

**Princípio guiando todas as queries:**
- Filtro `WHERE ativo = 1` SÓ vale para listas de seleção (dropdowns). NUNCA para relatórios, KPIs ou histórico.
- Toda query de relatório/KPI/dashboard que envolve nota DEVE usar `COALESCE(nota_ajustada, nota_final) AS nota_efetiva`.

---

## 1. O que está pronto nesta versão (v0.3)

### Stack
- **Backend:** Flask + SQLite
- **Frontend:** HTML + Tailwind 2.2.19 (CDN) + Chart.js 4.4.1 (CDN)
- **Deploy:** Render (Procfile + render.yaml)
- **Tipografia/UI:** Inter (system) + emojis nativos
- **Dependências:** `flask`, `werkzeug`, `gunicorn`, `openpyxl`

### Telas existentes
| Rota | Tela | Acesso |
|---|---|---|
| `/login` | Login | Público |
| `/dashboard` | Dashboard de qualidade (KPIs, gráficos, últimas monitorias) | Logado |
| `/formulario` | Nova Monitoria | Supervisor |
| `/historico` | Histórico completo de monitorias | Logado (perito vê só suas) |
| `/peritos` | Ranking e desempenho por perito | Supervisor |
| `/produtos` | Gestão de produtos (manual + upload CSV/XLSX) | Supervisor |
| `/monitoria/<id>` | Detalhe de uma monitoria | Logado (com regras) |
| `/uploads/monitorias/<id>/<arquivo>` | Servir anexos (login obrigatório) | Logado (perito vê só os seus) |

### Sidebar (em `templates/base.html`)
1. 📊 Dashboard
2. 📋 Nova Monitoria *(supervisor)*
3. 📅 Histórico
4. 👥 Peritos *(supervisor)*
5. 📦 Produtos *(supervisor)*

### Schema atual do banco (SQLite)
```
usuarios          (id, nome, email, senha_hash, perfil[supervisor|perito], ativo)
clientes          (id, nome)
produtos          (id, nome UNIQUE, ativo, created_at)
monitorias        (id, data_monitoria, data_tratativa, data_feedback,
                   colaborador_id, avaliador_id, cliente_id, produto_id,
                   numero_processo, observacoes, nota_final, created_at)
monitoria_itens   (id, monitoria_id, item_numero[1-8], marcado, observacao)
monitoria_anexos  (id, monitoria_id, item_numero, nome_original, nome_arquivo,
                   tamanho, mime_type, uploaded_at)
```

### Regras de cálculo de nota (hardcoded em `app.py:calculate_score`)
- Início: 100 pontos
- **Itens 1–3 (GRAVÍSSIMA):** se qualquer um marcado → nota = 0
- **Itens 4–5 (GRAVE):** cada um marcado → −60 pontos (mínimo 0)
- **Itens 6–8 (LEVE):** cada um marcado → −40 pontos (mínimo 0)

### Migração idempotente
- A função `ensure_schema()` em `app.py` roda no startup e adiciona automaticamente: tabela `produtos`, coluna `produto_id` em `monitorias`, coluna `observacao` em `monitoria_itens`, tabela `monitoria_anexos`. Idempotente — não sobrescreve nada existente.

### Concluído
- [x] **Versão inicial** do app (Flask + SQLite + dashboard) — 2026-04-09.
- [x] **Pré-preenchimento da data atual** no formulário (timezone-safe via backend `America/Sao_Paulo`) — 2026-04-29.
- [x] **Campo de Produto nas monitorias** — coluna `produto_id`, dropdown no formulário, filtro no dashboard — 2026-04-29.
- [x] **Tela de gestão de Produtos** — cadastro manual, upload em lote (CSV/XLSX), ativar/desativar (preserva histórico) — 2026-04-29.
- [x] **Tela de Histórico** — listagem completa com filtros (mês, ano, perito, cliente, produto), badges de status, clique abre o detalhe — 2026-04-29.
- [x] **Tela de Peritos** — ranking por nota média com badges (Excelente/Atenção/Crítico/Sem dados/Inativo) — 2026-04-29.
- [x] **Observação + anexos por critério** no formulário — bloco expansível ao marcar checkbox, suporta múltiplos arquivos (PDF, imagens, vídeo, planilha, doc), 25MB por monitoria — 2026-04-29.
- [x] **Detalhe da monitoria reformulado** — número dentro de círculo colorido por categoria, exibição da observação por critério e dos anexos clicáveis (download), breadcrumb apontando para Histórico — 2026-04-29.
- [x] **UI de réplica perito ↔ supervisor** (mockup funcional, sem e-mail) — botões Concordo/Não concordo, justificativa obrigatória se discordar, regra de única réplica por autor (UNIQUE no banco), supervisor só responde após réplica do perito, todas as réplicas exibidas em cards coloridos — 2026-04-29.

---

## 2. Pendências ativas

### Pendência 1 — Tela de Parâmetros (recalibrar critérios)
**Objetivo:** permitir que o supervisor edite os critérios de avaliação sem alterar código.

**Critérios:**
- Nova rota `/parametros` (acesso apenas supervisor).
- Permite editar os **textos** dos 8 apontamentos (nome + descrição).
- Permite editar os **descontos por severidade** (hoje hardcoded: GRAVÍSSIMA zera, GRAVE −60, LEVE −40).
- Histórico de versões dos parâmetros para auditoria (opcional v1).

**Decisão pendente com Henrique:**
- (a) Itens fixos de 1 a 8 com texto editável **(mais simples, mantém compatibilidade)**, ou
- (b) Estrutura totalmente dinâmica, permitindo adicionar/remover itens **(mais flexível, exige refator do cálculo de nota)**.

**Impacto técnico:**
- Novas tabelas: `criterios` (id, numero, severidade, nome, descricao, ativo), `severidades` (id, codigo, label, desconto, zera_nota).
- Refator de `calculate_score()` para ler do banco em vez de hardcoded.
- Novo template `templates/parametros.html`.
- Migração: criar tabelas, popular com dados atuais (ITEMS dict do `app.py`).

---

### Pendência 2 — Notificação por e-mail e tokens de acesso da réplica
**(parcial — UI funcional já entregue em v0.3; falta apenas a camada de notificação)**

**Já entregue na v0.3:**
- Tabela `monitoria_replicas` criada com `UNIQUE(monitoria_id, autor_tipo)` garantindo uma réplica por autor.
- Rota `POST /monitoria/<id>/replica` que valida decisão, exige justificativa quando "Não concordo", e bloqueia supervisor de responder antes do perito.
- UI completa de réplica integrada ao detalhe da monitoria: botões Concordo/Não concordo, textarea de justificativa que aparece dinamicamente, cards coloridos exibindo réplicas de perito e supervisor, regra de "uma vez por autor".

**Falta nesta pendência:**
- **E-mail automático** ao perito quando uma monitoria é registrada, com link.
- **E-mail automático** ao supervisor quando o perito envia réplica.
- **Tokens de acesso únicos** nos links (para acesso sem login direto, com expiração).
- **Registro de visualização** (`visto_perito_em`, `visto_supervisor_em` em `monitorias`).

**Decisão pendente:**
- Provedor de e-mail: SMTP corporativo Planetun? SendGrid? Resend?
- Definir template do e-mail e remetente (ex: `monitoria@planetun.com.br`).
- Tokens: JWT com expiração de 14 dias, ou aleatório armazenado no banco?

**Impacto técnico:**
- Novas colunas em `monitorias`: `visto_perito_em`, `visto_supervisor_em`, `token_acesso`.
- Serviço de envio de e-mail (`utils/email.py`).
- Nova rota: `/monitoria/acesso/<token>` (login via token, redireciona pra detalhe).

---

### Pendência 3 — Gestão de Peritos (cadastro + ativação + preservação histórica)
**Objetivo:** permitir gerenciar o quadro de peritos sem precisar mexer em `seed_data.py`, com garantia de preservação do histórico ao inativar.

**Critérios funcionais:**
1. **Cadastro manual** (botão "Adicionar perito" na tela `/peritos`):
   - Formulário com: nome, e-mail (validar `@planetun.com.br`), perfil (perito/supervisor).
   - Senha padrão `planetun123` ao criar (até a Pendência 2 entregar convite por e-mail).
   - Validação de duplicidade por e-mail.

2. **Cadastro em lote (upload):**
   - Upload de CSV/XLSX com colunas: `nome`, `email`, `perfil` (a 1ª linha pode ser cabeçalho, será detectado e ignorado).
   - Mesma validação de duplicidade — duplicados são pulados, não bloqueiam o lote inteiro.
   - Mensagem de retorno: "X cadastrados, Y ignorados (duplicados)".

3. **Ativar / Inativar perito:**
   - Botão na linha de cada perito em `/peritos`.
   - Inativar **não deleta** — apenas marca `ativo = 0`.

4. **🔒 Preservação histórica (regra não-negociável):**
   - Perito inativo **não aparece** no dropdown de "Nova Monitoria" (`WHERE perfil='perito' AND ativo=1`).
   - Perito inativo **continua aparecendo** em:
     - Tela `/peritos` (com badge "Inativo")
     - Histórico (`/historico`) — todas as monitorias dele permanecem visíveis e filtráveis
     - Dashboard — KPIs e gráficos seguem incluindo dados dele (regra: nenhuma query de relatório aplica `WHERE u.ativo=1`)
     - Detalhe de monitoria (`/monitoria/<id>`) — nome do perito permanece exibido
   - **Reativar** restaura a aparição no dropdown sem afetar nada do histórico.

**Princípio guiando o código:**
> O filtro `WHERE ativo = 1` só vale para **listas de seleção** (dropdowns, "quem pode ser avaliado agora?"). **Nunca** para relatórios, KPIs ou históricos. Um perito que saiu não apaga o trabalho dele — esse trabalho ficou registrado e segue contando.

**Impacto técnico:**
- Rotas a criar:
  - `GET /peritos/novo` — formulário manual
  - `POST /peritos/novo` — salva perito manual
  - `POST /peritos/upload` — upload CSV/XLSX
  - `POST /peritos/<id>/toggle` — alterna `ativo` (mesma assinatura do toggle de produtos)
  - `GET /peritos/<id>/editar` + `POST /peritos/<id>/editar` — editar dados básicos
- Generalizar o parser `_parse_produtos_csv` / `_parse_produtos_xlsx` para aceitar múltiplas colunas (refatorar para `_parse_lista_csv(stream, colunas)`).
- Atualizar `templates/peritos.html`:
  - Adicionar header com botão "➕ Adicionar perito" e card de upload (padrão da tela de Produtos).
  - Coluna nova "Ações" com botões Editar / Ativar-Desativar.
- **Auditoria de queries existentes:** revisar TODAS as queries em `app.py` (dashboard, histórico, peritos, detalhe) e confirmar que **nenhuma** filtra por `u.ativo = 1` em relatórios. Se alguma filtrar, remover.

**Decisão futura (após Pendência 2 estar pronta):**
- Em vez de senha padrão, enviar convite por e-mail com link de definição de senha.

---

### Pendência 4 — KPI de manifestações por supervisor (avaliação do avaliador) — **DESBLOQUEADA**
**Objetivo:** o trabalho do supervisor também precisa ser auditável. Se um supervisor avalia mal e seus peritos contestam frequentemente — e ele acaba acolhendo a maioria das contestações — isso é um sinal de que ele precisa calibrar o critério dele. Esse indicador vai pro próprio dashboard como métrica de qualidade do supervisor.

**Critérios:**
- Novo bloco no dashboard (visível só para supervisor) com:
  - **Total de manifestações recebidas** (quantas réplicas de peritos chegaram em monitorias que ele fez)
  - **% acolhidas** (réplicas onde o supervisor respondeu "Acolho — ajustar avaliação")
  - **% mantidas** (réplicas onde o supervisor respondeu "Mantenho a avaliação")
  - **% sem resposta ainda** (réplicas pendentes de resposta)
- Gráfico de tendência mensal (barras empilhadas: acolhidas vs mantidas).
- Filtrável por supervisor (quando o usuário logado é admin/dono) e por período (mês/ano).
- Tabela de "monitorias com manifestação" — linhas clicáveis para o detalhe.

**Decisão pendente:**
- Definir limite/alerta: a partir de quantos % acolhidas o supervisor recebe um aviso de que precisa rever sua calibração? (sugestão: > 40% acolhidas em 30 dias dispara um alerta amarelo).
- O dado bruto JÁ está sendo gravado em `monitoria_replicas` desde a v0.3 — falta só agregar e visualizar.
- **Nota efetiva no KPI:** o cálculo de "% acolhidas que mudaram a nota" usa `nota_ajustada` quando preenchida. Se for NULL mesmo após "Acolho", é só ajuste qualitativo sem mudança de nota.

**Impacto técnico:**
- Novas queries no `/api/dashboard-data`.
- Novo bloco em `templates/dashboard.html`.
- Eventual nova rota `/dashboard/manifestacoes` com tela detalhada.

---

### Pendência 5 — Exportação de relatório por perito (afeta faturamento) — **DESBLOQUEADA**
**Objetivo:** os resultados de monitoria impactam o faturamento dos peritos. Cada perito precisa receber/poder gerar um relatório mensal com suas notas para fechamento financeiro.

**Critérios:**
- Botão "📥 Exportar relatório" na tela `/peritos` (linha por linha) e em `/historico` (filtro aplicado).
- Conteúdo do relatório:
  - Cabeçalho: nome do perito, e-mail, período (mês/ano), data de geração.
  - Tabela de monitorias do perito no período: data, cliente, produto, nº processo, nota original, **nota efetiva** (após eventual ajuste por réplica acolhida), falhas apontadas, link para detalhe.
  - Totalizadores: nº de monitorias, **nota média efetiva**, % conformidade, distribuição por severidade.
  - Rodapé: assinatura do supervisor responsável + observação sobre direito a contestar.
- Formatos: **PDF** (arquivamento, faturamento) e **XLSX** (análise interna).
- Geração sob demanda + opção futura de envio automático mensal por e-mail (depende da Pendência 2).

**✅ Decisão tomada (2026-04-29):** Opção A. Preserva `nota_final` original; adiciona `nota_ajustada` (NULL por padrão, preenchida quando supervisor acolhe). Todos os dashboards e relatórios usam **nota efetiva = `COALESCE(nota_ajustada, nota_final)`**. Garante auditoria completa.

**Impacto técnico:**
- Nova coluna `nota_ajustada` em `monitorias` (via `ensure_schema()` no startup).
- Quando supervisor responde réplica com `decisao='concordo'` (acolhe): UI deve perguntar a nova nota e gravá-la em `nota_ajustada` (mexer no template de réplica + na rota `monitoria_replica`).
- Queries de KPI/dashboard/relatório passam a usar `COALESCE(nota_ajustada, nota_final) AS nota_efetiva`.
- Geração de PDF: biblioteca `reportlab` (adiciona em `requirements.txt`).
- Geração de XLSX: já temos `openpyxl`.
- Novas rotas: `/relatorio/perito/<id>?formato=pdf|xlsx&mes=&ano=`.

---

### Pendência 6 — Importação de monitorias automáticas (output do agente NotebookLM) — **AGUARDANDO 4 DECISÕES**
**Objetivo:** integrar o agente automático que hoje roda no NotebookLM da Planetun. O agente já faz auditoria — precisamos receber o resultado dele, casar com os 8 critérios + severidades da monitoria, e gerar uma monitoria automática.

**Critérios funcionais:**
- Receber o output do agente (formato a ser definido — ver decisão pendente).
- "Conversar com os critérios": traduzir o resultado do agente para a estrutura da monitoria (qual item marcar, severidade, observação por critério, anexos eventuais).
- Gerar a monitoria automaticamente, com:
  - **Origem marcada como "automática"** (nova coluna `origem` em `monitorias`).
  - **Status `pendente_validacao`** por padrão — supervisor revisa antes de virar definitiva (regra de governança: agente sugere, humano aprova).
  - Identificação do **lote/execução do agente** que gerou (para rastreabilidade e re-processamento).
- Tela `/monitorias/pendentes` (supervisor) com fila de monitorias geradas automaticamente, esperando aprovação. Botões: ✓ Aprovar (vira definitiva, dispara fluxo normal de réplica) / ✕ Rejeitar (descarta) / ✏️ Editar e aprovar (ajusta antes de aprovar).

**🔴 Decisões pendentes (precisamos de Henrique antes de implementar):**

1. **Qual o output atual do agente NotebookLM?**
   - (a) Texto livre (descrição em português)
   - (b) JSON estruturado (campos definidos)
   - (c) Documento Word/PDF
   - (d) Linha numa planilha
   - Cada formato muda o caminho técnico.

2. **Como o agente entrega esse output hoje?**
   - (a) Henrique copia/cola manualmente
   - (b) Sai num arquivo numa pasta (Drive, computador)
   - (c) E-mail
   - (d) Webhook/API (improvável no NotebookLM hoje)

3. **Modelo de integração:**
   - (a) **Upload manual** — Henrique faz upload do output (CSV/JSON) e a monitoria parseia e cria.
   - (b) **API/endpoint** — um glue code do lado do NotebookLM chama nosso endpoint via HTTP com o resultado.
   - (c) **Pasta watchada** — agente deposita arquivo num bucket/pasta, e um job da monitoria lê e processa.

4. **Tradução texto livre → critérios estruturados:**
   - Se o output for texto livre, vamos precisar de uma camada LLM (Claude API) que recebe: "este texto + estes 8 critérios + dados do processo" → devolve JSON com itens marcados, severidades e observações por critério. Custo: ~R$ 0,02–0,05 por monitoria. Trivial mesmo a 1000 monitorias/mês.

**Impacto técnico:**
- Novas colunas em `monitorias`: `origem` (manual|automatica|hibrida), `lote_agente`, `status_validacao` (pendente|validada|rejeitada), `validado_por_id`, `validado_em`.
- Novo endpoint `POST /api/monitorias/auto` (autenticado por API key) recebendo JSON estruturado.
- Se for caminho (a) upload manual: rota `/monitorias/importar` (supervisor) com parser CSV/JSON/XLSX.
- Se precisar de LLM: integração com Claude API (variável `ANTHROPIC_API_KEY`).
- Tela `/monitorias/pendentes` para revisão humana antes de validar.
- Schema de logs (tabela `agente_lotes`) para auditoria do que veio do agente.

**Importância estratégica:**
- Sai do modelo "supervisor faz tudo na mão" para "agente sugere, supervisor valida". Multiplica capacidade de avaliação por 5-10x.
- Mantém humano no loop — protege contra erro do agente.
- O dado de "% das sugestões do agente que foram aprovadas sem alteração" vira KPI da qualidade do próprio agente — analytics que retroalimenta o NotebookLM.

---

### Pendência 7 — Migração dos anexos para storage objeto (técnica)
**Objetivo:** garantir que anexos não sejam perdidos em redeploys do Render (filesystem efêmero).

**Critérios:**
- Migrar `uploads/monitorias/...` para Cloudflare R2 ou Backblaze B2 (mais baratos que S3).
- Manter assinatura da rota `/uploads/monitorias/<id>/<arquivo>` (transparente para o usuário).
- Variáveis de ambiente: `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET`, `R2_ENDPOINT`.

**Quando atacar:** quando os anexos virarem critério de auditoria ou quando o primeiro perito reclamar de evidência sumida. **Não é urgente, mas é dívida técnica conhecida.**

---

## 3. Próximo passo combinado

**Status no fim do dia 2026-04-29:**
- Decisão N1 tomada (modelo de nota = Opção A) → Pendências 4 e 5 desbloqueadas.
- Decisões pendentes restantes:
  - **Pendência 1 (Parâmetros):** itens fixos com texto editável **(a)** ou estrutura dinâmica **(b)**?
  - **Pendência 6 (Agente NotebookLM):** 4 perguntas registradas — formato do output, meio de entrega, modelo de integração, validação humana.

**Sequência sugerida quando voltar:**
1. **Pendência 5** (relatório por perito) — implementa a coluna `nota_ajustada`, ajusta UI da réplica para perguntar a nova nota quando "Acolho", entrega exportação PDF/XLSX. Toca diretamente no faturamento.
2. **Pendência 4** (KPI manifestações por supervisor) — reusa `nota_ajustada` e a tabela `monitoria_replicas`, adiciona o bloco no dashboard.
3. **Pendência 1** (Parâmetros) — após decisão a/b.
4. **Pendência 3** (Gestão de peritos completa).
5. **Pendência 2** (E-mail/tokens da réplica) — depende da escolha do provedor de e-mail.
6. **Pendência 6** (Agente NotebookLM) — aguarda as 4 decisões.
7. **Pendência 7** (Storage objeto) — quando filesystem do Render virar problema.

---

## 4. Estrutura de arquivos nesta versão

```
Monitoria da Qualidade/
├── app.py                          # 818 linhas — todas as rotas e lógica
├── init_db.py                      # schema completo para deploys frescos
├── seed_data.py                    # dados de exemplo (peritos, supervisores, clientes)
├── requirements.txt                # flask, werkzeug, gunicorn, openpyxl
├── render.yaml                     # config Render
├── Procfile                        # comando de start
├── monitoria.db                    # banco SQLite (gitignored)
├── PENDENCIAS.md                   # este arquivo — estado e roadmap
├── preview_render.py               # gerador de previews HTML
├── preview_*.html                  # previews gerados (5 telas)
├── static/
│   ├── logo_bar.png
│   ├── logo_icon.png
│   └── logo_planetun.png
├── templates/
│   ├── base.html                   # sidebar + estilos comuns
│   ├── login.html
│   ├── dashboard.html              # KPIs + gráficos + últimas monitorias
│   ├── formulario.html             # nova monitoria com obs+anexo por critério
│   ├── monitoria_detalhe.html      # detalhe de uma monitoria
│   ├── historico.html              # listagem completa
│   ├── peritos.html                # ranking
│   └── produtos.html               # gestão de produtos
└── uploads/
    └── monitorias/<id>/            # anexos (efêmero no Render)
```
