# Lab Proof — n8n Node Study Guide

**Lab:** Become the person who reads the docs
**Source files analyzed:** `RAG_Chatbot_with_reranker.json`, `templaten8n_track_token_spend.json`
**Method:** Static analysis of the exported workflow JSON (node parameters, settings, and connections), backed by one real execution trace captured in `evidence/` for the Workflow 2 chat/Q&A critical path — see [Section 7](#7-execution-evidence) for the captured input, node outputs, and final answer, and for what is still outstanding on Workflows 1 and 3.

---

## 1. Introduction and Learning Objective

The goal of this lab is to become able to read an n8n workflow export the way a reviewer or on-call engineer would: identify every node, its configured parameters and settings, the shape of the JSON flowing in and out of it, and the transformation it performs on that data. This document analyzes three workflows found in two JSON export files, builds a node reference table covering every distinct node type present, traces representative data-flow paths, and documents the operational risks of each workflow.

Two JSON files were provided. One of them (`RAG_Chatbot_with_reranker.json`) contains a single n8n workflow definition with **two independent trigger paths** that are often discussed as "two workflows" (document ingestion, and chat Q&A). This distinction is addressed explicitly in [Section 3](#3-workflow-architecture-and-data-flow-analysis), because it affects how connections should be read.

## 2. Overview of the Three Workflows

| # | Workflow (as implemented) | Source file | Trigger(s) | Purpose |
|---|---|---|---|---|
| 1 | RAG document ingestion path | `RAG_Chatbot_with_reranker.json` | Form Trigger | Upload a PDF/CSV/JSON file, split it, embed it, and store it in a Pinecone vector index. |
| 2 | RAG chat / AI agent path | `RAG_Chatbot_with_reranker.json` | Chat Trigger | Let a user ask questions; an AI agent retrieves relevant chunks from Pinecone (reranked with Cohere) and answers using only that retrieved context. |
| 3 | LLM spend tracker | `templaten8n_track_token_spend.json` | Schedule Trigger (every 15 min) | Poll the n8n API for recent executions, extract every LLM call's token usage, price it, log it to a data table, and alert Slack if a workflow exceeds its daily budget. |



## 3. Workflow Architecture and Data-Flow Analysis

### 3.1 File 1 is one workflow with two trigger paths, not two separate workflows

`RAG_Chatbot_with_reranker.json` contains a single top-level workflow object (`"name": "RAG Chatbot (with reranker)"`) with 9 functional nodes and one `connections` map. Within that one workflow there are **two disconnected trigger entry points** that never share a `main` connection:

- **Ingestion path:** `Upload Documents Form` → `Store in Pinecone`, fed by `OpenAI Embeddings` (`ai_embedding`) and `Document Loader` (`ai_document`, itself fed by `Text Splitter` via `ai_textSplitter`).
- **Chat/Q&A path:** `Chat Interface` → `RAG Agent`, fed by `OpenAI Chat Model` (`ai_languageModel`) and `Retrieve from Pinecone` (`ai_tool`, itself fed by `Query Embeddings` via `ai_embedding` and `Cohere Reranker` via `ai_reranker`).

The two paths are **not connected by any `main` data edge** — there is no node that passes data directly from the ingestion side to the chat side. They are linked only **implicitly**, through the shared Pinecone index name (`"value": "n8n"`) that both `Store in Pinecone` and `Retrieve from Pinecone` point to. In other words: data written by the ingestion path becomes retrievable by the chat path only because both nodes are configured against the same external vector index — not because of any in-workflow wiring. This matters operationally: you can trigger the chat path with an empty/stale index if ingestion hasn't run yet, and n8n's editor will not flag that as a wiring problem because, from the workflow's point of view, there isn't one.

```
[Upload Documents Form]──main──▶[Store in Pinecone]
              (ai_embedding) [OpenAI Embeddings]──▶┘
              (ai_document)  [Document Loader]──▶┘
                 (ai_textSplitter) [Text Splitter]──▶[Document Loader]

                         ·· shared Pinecone index "n8n" ··

[Chat Interface]──main──▶[RAG Agent]
         (ai_languageModel) [OpenAI Chat Model]──▶┘
         (ai_tool) [Retrieve from Pinecone]──▶┘
                (ai_embedding) [Query Embeddings]──▶┘
                (ai_reranker)  [Cohere Reranker]──▶┘
```

### 3.2 File 2: LLM spend tracker — linear pipeline with a budget branch

```
[Every 15 minutes] (schedule)
        │ main
        ▼
[Set configuration]  (prices, budget, overrides, pause flag)
        │ main
        ▼
[Get recent executions]  (n8n API: list executions incl. run data)
        │ main
        ▼
[Extract LLM calls and cost]  (Code: one item per LLM call, token usage → USD)
        │ main
        ▼
[Skip calls already logged]  (Data Table: rowNotExists on callKey)
        │ main
        ▼
[Insert usage rows]  (Data Table: insert)
        │ main
        ▼
[Get today's usage]  (Data Table: get rows finishedAt >= start of day)
        │ main
        ▼
[Find workflows over budget]  (Code: sum per workflowId, compare to budget)
        │ main
        ▼
[Pause over-budget workflows?]  (IF: pauseOverBudget == true)
   ├─ true ─▶ [Unpublish workflow] ─▶ [Send budget alert to Slack]
   └─ false ─────────────────────────▶ [Send budget alert to Slack]
```

This is a single deterministic pipeline — there is no AI agent, language model, or autonomous decision-making in this workflow. Every branch is a plain `IF` node evaluating a boolean configuration value, not a model decision.

## 4. n8n Node Reference Table

17 distinct node types are present across the two files (well above the 10-node minimum). Duplicated node types with materially different configuration are called out as separate rows and cross-referenced.

| Node (name — type) | Used in | Parameters (as configured) | Settings | What It Does | JSON Input | JSON Output | Key Transformations |
|---|---|---|---|---|---|---|---|
| **Upload Documents Form** — `n8n-nodes-base.formTrigger` | WF1 (ingest) | `formTitle`="Upload Documents for RAG"; one file field `documents` accepting `.pdf,.csv,.json`; `appendAttribution: false` | `alwaysOutputData: false`; typeVersion 2.5 | Entry point. Renders a public web form and starts the workflow when a file is submitted. | HTTP form POST with multipart file | `{ "documents": { binary file data }, "submittedAt": ... }` | HTTP form submission → n8n item with binary data property |
| **Store in Pinecone** — `@n8n/n8n-nodes-langchain.vectorStorePinecone` | WF1 (ingest) | `mode: "insert"`; `pineconeIndex.value: "n8n"` (list-resolved) | typeVersion 1.3; consumes `ai_embedding` and `ai_document` sub-connections, not just `main` | Writes embedded document chunks into the named Pinecone index. | Binary file item (main) + vectors (ai_embedding) + loaded docs (ai_document) | Insert confirmation / pass-through item | Converts chunked text + embeddings into persisted vector-store records |
| **OpenAI Embeddings** — `@n8n/n8n-nodes-langchain.embeddingsOpenAi` | WF1 (ingest), also as **Query Embeddings** in WF2 (chat) | `options.dimensions: 512` | typeVersion 1.2; sub-node, connects via `ai_embedding` only, no `main` port | Calls OpenAI's embeddings API to turn text into a 512-dim vector. Used twice with identical config: once to embed uploaded document chunks, once (as "Query Embeddings") to embed the user's question for retrieval. | Text string(s) | Array of float vectors | Text → numeric embedding vector |
| **Document Loader** — `@n8n/n8n-nodes-langchain.documentDefaultDataLoader` | WF1 (ingest) | `dataType: "binary"`; `textSplittingMode: "custom"` | typeVersion 1.1; feeds `Store in Pinecone` via `ai_document` | Reads the uploaded binary file and hands it to the configured text splitter before it becomes vector-store documents. | Binary file data | Array of LangChain `Document` objects (text + metadata) | Binary file → structured document objects, split per the linked Text Splitter |
| **Text Splitter** — `@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter` | WF1 (ingest) | `options: {}` (defaults — n8n default chunk size 1000 / overlap 200 when unset) | typeVersion 1; connects to `Document Loader` via `ai_textSplitter` | Breaks extracted document text into overlapping chunks sized for embedding. | Raw extracted text | Array of text chunks | Long text → many smaller overlapping chunks |
| **Chat Interface** — `@n8n/n8n-nodes-langchain.chatTrigger` | WF2 (chat) | `public: true`; `initialMessages`: greeting text; `options.responseMode: "streaming"` | typeVersion 1.4 | Entry point for the Q&A path. Hosts a public chat widget and streams the agent's reply back to the user. | User-typed chat message | `{ "chatInput": "<user message>", "sessionId": "..." }` | HTTP/websocket chat turn → n8n chat-trigger item |
| **RAG Agent** — `@n8n/n8n-nodes-langchain.agent` | WF2 (chat) | `options.systemMessage`: instructs the agent to answer **only** from retrieved context and say "I couldn't find that in the uploaded documents" otherwise, and to cite sources; `options.enableStreaming: true` | typeVersion 3.1; orchestrates its connected `ai_languageModel` and `ai_tool` sub-nodes | The autonomous decision-maker: receives the user's question, decides whether/how to call the Pinecone retrieval tool, and composes the final answer with the connected LLM. | `{ "chatInput": "<question>" }` plus conversation state | `{ "output": "<answer text>" }` streamed to the chat UI | User question → (tool call decision) → retrieved context → grounded natural-language answer |
| **OpenAI Chat Model** — `@n8n/n8n-nodes-langchain.lmChatOpenAi` | WF2 (chat) | `model.value: "gpt-5.4-mini"`; `builtInTools: {}` | typeVersion 1.3; sub-node, connects via `ai_languageModel` only | Supplies the underlying LLM the `RAG Agent` reasons and writes with. | Agent's constructed prompt/messages | Model completion (text + token usage) | Prompt → generated text + `tokenUsage` metadata |
| **Retrieve from Pinecone** — `@n8n/n8n-nodes-langchain.vectorStorePinecone` | WF2 (chat) | `mode: "retrieve-as-tool"`; `toolDescription`: tells the agent what this tool is for; `pineconeIndex.value: "n8n"`; `topK: 5`; `useReranker: true` | typeVersion 1.3; exposed to the agent via `ai_tool`, distinct mode from the ingest-side instance above | Exposed to `RAG Agent` as a callable tool: given the query embedding, fetch the top-5 most similar chunks from the index, then rerank them. | Query embedding vector | Top-5 (post-rerank) document chunks + similarity scores | Vector similarity search + rerank → ranked context chunks for the agent |
| **Cohere Reranker** — `@n8n/n8n-nodes-langchain.rerankerCohere` | WF2 (chat) | `{}` (no exposed parameters beyond credential selection) | typeVersion 1; sub-node, connects via `ai_reranker` into `Retrieve from Pinecone` | Re-scores the Pinecone similarity results against the original query using Cohere's rerank model, improving relevance over raw vector similarity. | Candidate chunks + query text | Re-ordered/filtered chunk list | Similarity-ranked list → relevance-ranked list |
| **Every 15 minutes** — `n8n-nodes-base.scheduleTrigger` | WF3 | `rule.interval`: `minutes`, `minutesInterval: 15` | typeVersion 1.3 | Entry point. Fires the whole spend-tracking pipeline on a fixed interval. | None (time-based) | `{ "timestamp": "<ISO datetime>" }` | Clock tick → triggered execution |
| **Set configuration** — `n8n-nodes-base.set` | WF3 | 4 assignments: `pricesPer1M` (object, JSON string of per-model $/1M token prices), `dailyBudgetUsd` (number, `5`), `budgetOverrides` (object, `{}`), `pauseOverBudget` (boolean, `false`) | typeVersion 3.4 | Centralizes all tunable configuration so downstream Code nodes read it by reference (`$('Set configuration').first().json`) instead of hardcoding values. | Trigger item (empty) | `{ pricesPer1M, dailyBudgetUsd, budgetOverrides, pauseOverBudget }` | Empty trigger payload → named configuration fields |
| **Get recent executions** — `n8n-nodes-base.n8n` | WF3 (also **Unpublish workflow** below, different operation) | `resource: "execution"`; `limit: 100`; `options.activeWorkflows: true` | typeVersion 1; `credentials: {}` — **no n8n API credential is attached in this export** | Calls n8n's own REST API to fetch up to 100 recent executions, including each one's run data (needed to read token usage). | Config item (unused) | Array of execution objects: `{ id, workflowId, workflowData, status, stoppedAt, data.resultData.runData, ... }` | Trigger → external API call → execution history as n8n items |
| **Extract LLM calls and cost** — `n8n-nodes-base.code` | WF3 (also **Find workflows over budget** below, different script) | JavaScript, Run Once for All Items. Reads `pricesPer1M` from `Set configuration`; walks each execution's `resultData.runData`, finds the `ai_languageModel` output per node run, reads `tokenUsage`/`tokenUsageEstimate`, matches the model name against `pricesPer1M` by exact match or longest prefix, computes `costUsd` | typeVersion 2 | Flattens nested execution/run data into one flat item per individual LLM call, with model, token counts, and computed USD cost. Skips its own workflow's executions and any execution still running (`!ex.stoppedAt`). | One item per execution (nested `runData`) | One item **per LLM call**: `{ callKey, executionId, workflowId, workflowName, nodeName, model, promptTokens, completionTokens, totalTokens, estimated, costUsd, executionStatus, finishedAt }` | Nested execution JSON → flat, priced, per-call records; 1 execution item can expand into 0–N output items |
| **Skip calls already logged** — `n8n-nodes-base.dataTable` | WF3 (also **Insert usage rows**, **Get today's usage** below, different operations) | `operation: "rowNotExists"`; filter condition `keyName: "callKey"`, `keyValue: "={{ $json.callKey }}"`; `dataTableId` left unresolved (empty `value`/`cachedResultName`) | typeVersion 1.1 | Deduplication gate: passes through only calls whose `callKey` is not already a row in the data table, preventing the same LLM call from being logged twice across 15-minute polling cycles. | `{ callKey, ... }` per call | Same item, filtered — only new `callKey`s pass | Filters out already-logged rows; no field changes to surviving items |
| **Insert usage rows** — `n8n-nodes-base.dataTable` | WF3 | `operation` implied `insert` (default for this node without an explicit operation key); `columns.mappingMode: "autoMapInputData"`; `dataTableId` unresolved | typeVersion 1.1 | Writes each new, deduplicated LLM-call record as a row in the shared data table. | `{ callKey, executionId, workflowId, model, promptTokens, costUsd, ... }` | Insert acknowledgment / inserted row echo | In-memory item → persisted data-table row |
| **Get today's usage** — `n8n-nodes-base.dataTable` | WF3 | `operation: "get"`; `returnAll: true`; filter `keyName: "finishedAt"`, `condition: "gte"`, `keyValue: "={{ $now.startOf('day').toISO() }}"` | typeVersion 1.1; `executeOnce: true`; `alwaysOutputData: false` | Reads back every row logged today (regardless of which polling cycle wrote it) so spend can be summed per workflow for the whole day, not just this run. | Trigger/pass-through item | Array of today's data-table rows: `{ workflowId, workflowName, costUsd, ... }` | Point-in-time query filter → full day's accumulated rows |
| **Find workflows over budget** — `n8n-nodes-base.code` | WF3 | JavaScript. Reads `budgetOverrides`/`dailyBudgetUsd` from `Set configuration`; sums `costUsd` per `workflowId`; uses `$getWorkflowStaticData('global')` to remember which workflow/day combo was already alerted, so it alerts **once per workflow per day** | typeVersion 2 | Aggregates today's rows into per-workflow totals, compares each to its budget (override or default), and emits one alert item only for workflows that just crossed the threshold for the first time today. | Array of today's usage rows | 0–N items: `{ workflowId, workflowName, spendUsd, budgetUsd, calls, message }` | Many per-call rows → one summary item per **newly** over-budget workflow; stateful dedup via workflow static data |
| **Pause over-budget workflows?** — `n8n-nodes-base.if` | WF3 | Single boolean condition: `={{ $('Set configuration').first().json.pauseOverBudget }}` is `true`; `typeValidation: "strict"` | typeVersion 2.2 | Routes each over-budget alert item down one of two branches depending on a global configuration flag, not on the item's own data. | `{ workflowId, spendUsd, message, ... }` | Same item, unmodified, sent to the "true" or "false" output branch | Pure conditional routing — no field changes |
| **Unpublish workflow** — `n8n-nodes-base.n8n` | WF3 | `operation: "deactivate"`; `workflowId.value: "={{ $json.workflowId }}"` (mode `id`) | typeVersion 1; `credentials: {}` — no API credential attached in export | On the "true" branch only: calls the n8n API to deactivate the offending workflow, stopping it from running (and spending) further today. | `{ workflowId, ... }` | n8n API deactivation response | Alert item → external state change (workflow goes inactive) |
| **Send budget alert to Slack** — `n8n-nodes-base.slack` | WF3 | `select: "channel"`; `channelId` unresolved (empty); `text: "={{ $('Find workflows over budget').item.json.message }}"` | typeVersion 2.3; `webhookId` present; `credentials: {}` — no Slack credential attached in export | Posts the human-readable budget-exceeded message to the configured Slack channel. Reached from both IF branches, so the alert fires whether or not the workflow was also paused. | `{ message: "LLM budget exceeded: ..." }` | Slack API response (message timestamp/channel) | Structured alert data → chat message string sent to external system |
| **Sticky Note** (×6) — `n8n-nodes-base.stickyNote` | WF3 | Freeform `content` (Markdown), `width`/`height`/`color` | typeVersion 1 | Documentation only — annotates sections of the canvas (setup instructions, data-table schema, per-stage explanations). Not part of execution; carries no data connections. | N/A | N/A | No data transformation — canvas annotation only |

**Node-type count:** 17 distinct types (`formTrigger`, `vectorStorePinecone`, `embeddingsOpenAi`, `documentDefaultDataLoader`, `textSplitterRecursiveCharacterTextSplitter`, `chatTrigger`, `agent`, `lmChatOpenAi`, `rerankerCohere`, `scheduleTrigger`, `set`, `n8n`, `code`, `dataTable`, `if`, `slack`, `stickyNote`) — exceeds the 10-type minimum. `vectorStorePinecone`, `embeddingsOpenAi`, `n8n`, `code`, and `dataTable` each appear more than once with different `mode`/`operation` configuration, documented above as the same row with both uses called out, per the lab's instruction to note configuration differences rather than inventing extra rows.

**AI sub-nodes vs. regular nodes:** every `@n8n/n8n-nodes-langchain.*` node in Workflow 1/2 (`vectorStorePinecone`, `embeddingsOpenAi`, `documentDefaultDataLoader`, `textSplitterRecursiveCharacterTextSplitter`, `lmChatOpenAi`, `rerankerCohere`) is a **LangChain sub-node**: it has no `main` input/output and only functions when wired into a root node (`Store in Pinecone`'s ingestion role, or `RAG Agent`) via a typed connection (`ai_embedding`, `ai_document`, `ai_textSplitter`, `ai_tool`, `ai_languageModel`, `ai_reranker`). All `n8n-nodes-base.*` nodes in Workflow 3 are regular nodes that pass data exclusively through `main`.

## 5. JSON Data Flow — Representative Node Walkthroughs

### Node: Retrieve from Pinecone (Workflow 2 — chat path)

**Purpose:** Given the user's question, find the most relevant previously-ingested document chunks and hand them to the agent as tool output.

**Input JSON** *(illustrative — shape inferred from node configuration, not an observed execution)*:
```json
{
  "query": "What does the uploaded policy say about refund windows?",
  "embedding": [0.0123, -0.0481, "... 512 floats ..."]
}
```

**Configuration:** `mode: "retrieve-as-tool"` exposes this node to `RAG Agent` as a callable tool (the agent, not the workflow, decides when to call it). `topK: 5` caps the initial Pinecone similarity search at 5 matches. `useReranker: true` routes those 5 matches through the connected `Cohere Reranker` (`ai_reranker` connection) before returning them. The query vector itself comes from `Query Embeddings` over the `ai_embedding` connection — this node never calls OpenAI directly.

**Output JSON** *(illustrative)*:
```json
{
  "documents": [
    { "pageContent": "Refunds are available within 30 days of purchase...", "metadata": { "source": "refund-policy.pdf", "chunk": 3 }, "score": 0.91 },
    { "pageContent": "...", "metadata": { "source": "refund-policy.pdf", "chunk": 4 }, "score": 0.77 }
  ]
}
```

**Transformation:** A natural-language question becomes a numeric vector (upstream), the vector becomes an unordered similarity-ranked candidate list (Pinecone), and that candidate list becomes a relevance-reranked, trimmed list (Cohere) — three distinct transformations chained before any text reaches the agent.

**Downstream dependency:** `RAG Agent` receives this tool's output as part of its reasoning context and is instructed by its `systemMessage` to answer **only** from this content, citing the source documents, or to explicitly say it found nothing — so the quality of this node's output directly bounds the quality and honesty of the final answer.

---

### Node: Extract LLM calls and cost (Workflow 3)

**Purpose:** Convert raw n8n execution history into flat, priced, per-call usage records.

**Input JSON** *(illustrative, based on the n8n Execution API shape the code explicitly reads — `ex.data.resultData.runData`, `ex.workflowData.nodes`, `ex.stoppedAt`)*:
```json
{
  "id": "4821",
  "workflowId": "17",
  "status": "success",
  "stoppedAt": "2026-11-02T08:14:03.000Z",
  "workflowData": { "name": "Support Email Agent", "nodes": [ { "name": "OpenAI Chat Model", "parameters": { "model": { "value": "gpt-4o-mini" } } } ] },
  "data": { "resultData": { "runData": {
    "OpenAI Chat Model": [ { "data": { "ai_languageModel": [[ { "json": { "tokenUsage": { "promptTokens": 512, "completionTokens": 128, "totalTokens": 640 } } } ]] } } ]
  } } }
}
```

**Configuration:** The node reads `pricesPer1M` from `Set configuration` via `$('Set configuration').first().json`, resolving the price either by exact model-name match or by the longest matching key prefix (handles dated model IDs like `gpt-4o-mini-2024-07-18`). It explicitly skips its own workflow's own executions (`ex.workflowId === $workflow.id`) and any execution not yet `stoppedAt` (still running).

**Output JSON** *(illustrative)*:
```json
{
  "callKey": "4821:OpenAI Chat Model:0",
  "executionId": "4821",
  "workflowId": "17",
  "workflowName": "Support Email Agent",
  "nodeName": "OpenAI Chat Model",
  "model": "gpt-4o-mini",
  "promptTokens": 512,
  "completionTokens": 128,
  "totalTokens": 640,
  "estimated": false,
  "costUsd": 0.0001524,
  "executionStatus": "success",
  "finishedAt": "2026-11-02T08:14:03.000Z"
}
```

**Transformation:** One execution item containing a deeply nested `runData` object (potentially several node runs, each potentially several model calls) is expanded into **zero to many** flat output items, one per LLM call, with a new synthetic key (`callKey`) and a computed field (`costUsd`) that did not exist in the source data.

**Downstream dependency:** `Skip calls already logged` uses `callKey` as the dedup key against the data table; `Insert usage rows` auto-maps every field of this output directly into table columns, so a field typo or type mismatch here (e.g., `costUsd` as a string) would propagate into the stored row.

---

### Node: Find workflows over budget (Workflow 3)

**Purpose:** Turn many individual call-cost rows into one alert decision per workflow per day.

**Input JSON** *(illustrative — array of rows from `Get today's usage`)*:
```json
[
  { "workflowId": "17", "workflowName": "Support Email Agent", "costUsd": 0.00015 },
  { "workflowId": "17", "workflowName": "Support Email Agent", "costUsd": 4.98 },
  { "workflowId": "9", "workflowName": "Lead Scorer", "costUsd": 1.10 }
]
```

**Configuration:** Sums `costUsd` per `workflowId`, compares each sum to `budgetOverrides[workflowId]` if present, else `dailyBudgetUsd` (expression: `Number(overrides[workflowId] ?? settings.dailyBudgetUsd)`). Uses `$getWorkflowStaticData('global')` to persist an `alerted` map across the workflow's own executions, resetting it when the stored `alertDay` no longer matches today — this is what limits Slack alerts to once per workflow per calendar day rather than once per 15-minute cycle.

**Output JSON** *(illustrative, for the example above with `dailyBudgetUsd: 5`)*:
```json
{
  "workflowId": "17",
  "workflowName": "Support Email Agent",
  "spendUsd": 4.9802,
  "budgetUsd": 5,
  "calls": 2,
  "message": "LLM budget exceeded: \"Support Email Agent\" (id 17) spent $4.9802 today, budget $5, 2 call(s). It is still running."
}
```
*(Note: in this specific example $4.98 < $5 budget, so no alert would actually fire — included to show the summation and message-building logic; an alert requires `s.usd > budget`.)*

**Transformation:** Many narrow, per-call rows collapse into few wide, per-workflow summary items; a stateful, cross-execution "already alerted today" check filters out items that would otherwise re-fire every 15 minutes.

**Downstream dependency:** `Pause over-budget workflows?` reads a *global* configuration flag (not anything on this item) to decide whether to also route to `Unpublish workflow`; `Send budget alert to Slack` reads this item's pre-built `message` field verbatim as the Slack message text — all formatting happens here, not in the Slack node.

## 6. Workflow-Specific Analysis

### Workflow 1 — PDF-Based RAG (ingestion + retrieval)

- **Ingestion (confirmed in JSON):** `Upload Documents Form` accepts `.pdf`, `.csv`, `.json` uploads → `Document Loader` reads the binary with `dataType: "binary"` → `Text Splitter` (recursive character splitter, default size/overlap since `options: {}`) chunks the extracted text → `OpenAI Embeddings` (512 dimensions) embeds each chunk → `Store in Pinecone` writes chunks + vectors into the `"n8n"` Pinecone index in `insert` mode.
- **Retrieval + answering (confirmed in JSON):** `Chat Interface` opens a streaming public chat session → `RAG Agent` receives the message → the agent can call `Retrieve from Pinecone` (`retrieve-as-tool` mode) as a tool, which embeds the query via `Query Embeddings`, fetches `topK: 5` matches, and reranks them with `Cohere Reranker` → `OpenAI Chat Model` (`gpt-5.4-mini`) generates the final answer, constrained by the agent's system message to answer only from retrieved context and to say so explicitly when it can't.
- **Ingestion vs. Q&A boundary:** these are two separate executions of the same workflow file, triggered by two different triggers, and — per Section 3.1 — they are connected only through the shared external Pinecone index, not through in-workflow data edges. Document ingestion must run (and its Pinecone write must complete) before a chat question about that document can be answered correctly; the JSON contains no mechanism that enforces that ordering.
- **Where data is transformed/stored/retrieved:** text → chunks (`Text Splitter`) → vectors (`OpenAI Embeddings` / `Query Embeddings`) → persisted index records (`Store in Pinecone`) → similarity-ranked candidates (`Retrieve from Pinecone`'s Pinecone call) → relevance-reranked candidates (`Cohere Reranker`) → grounded natural-language answer (`RAG Agent` + `OpenAI Chat Model`).

### Workflow 2 — AI Agent Chat

- **Conversation start:** a user opens the public chat widget created by `Chat Interface` (`@n8n/n8n-nodes-langchain.chatTrigger`, `public: true`).
- **Message entry:** each typed message arrives as the trigger's main output and is passed directly to `RAG Agent`.
- **Model connection:** `RAG Agent` is wired to exactly one `ai_languageModel` sub-node, `OpenAI Chat Model` (`gpt-5.4-mini`).
- **Memory:** no memory sub-node (e.g., `@n8n/n8n-nodes-langchain.memoryBufferWindow`) is present or connected in this export — the agent has no explicit conversation memory beyond whatever `Chat Interface`'s `sessionId` and n8n's default chat session handling provide. This should be verified against the live workflow if multi-turn memory is expected.
- **Tools:** exactly one tool is connected — `Retrieve from Pinecone` in `retrieve-as-tool` mode. The agent decides, per message, whether to invoke it (deterministic orchestration ends at "pass the message to the agent"; everything after that — whether to search, what to search for, how to phrase the answer — is a model decision, not fixed workflow logic).
- **Response generation and return:** the agent streams its answer (`enableStreaming: true` on both the agent and the chat trigger's `responseMode: "streaming"`) back through `Chat Interface` to the user's browser.

### Workflow 3 — LLM Spend Tracking (real implementation, not "lead qualification")

- **Trigger:** `Every 15 minutes` (`scheduleTrigger`).
- **n8n API interaction:** two calls — `Get recent executions` (`resource: "execution"`, lists up to 100 recent executions **with run data**, needed to see token usage) and, conditionally, `Unpublish workflow` (`operation: "deactivate"`, called only if `pauseOverBudget` is `true`).
- **Where token usage originates:** inside each execution's stored `data.resultData.runData`, specifically the `ai_languageModel` connection output of any LangChain chat-model sub-node, which n8n populates with `tokenUsage` (exact, provider-reported) or `tokenUsageEstimate` (n8n's own estimate when the provider doesn't report usage — e.g., some configurations of OpenAI's Responses API, per the workflow's own sticky note).
- **Usage → cost calculation:** `Extract LLM calls and cost` multiplies `promptTokens`/`completionTokens` by the matching model's `input`/`output` price from `pricesPer1M` (per-million-token prices) and divides by `1e6`. **Token usage (a count) and monetary cost (a derived dollar figure) are different things here** — the `totalTokens` field is read directly from the execution; `costUsd` only exists because someone maintains `pricesPer1M` with current, correct provider prices. If that price table is stale or missing a model, `costUsd` is `null` and the call is excluded from budget sums (tracked separately as `unpriced`) — so a silent pricing gap will under-report real spend without raising an error.
- **Data tables:** one shared table (ID left unresolved as `""` in this export — must be selected per-installation) used three ways: `rowNotExists` (dedup check), `insert` (write), `get` with a `finishedAt >= start of day` filter (daily read-back for aggregation).
- **Budget evaluation and Slack:** `Find workflows over budget` sums today's `costUsd` per `workflowId`, compares to an override or the default `dailyBudgetUsd`, and uses workflow static data to alert at most once per workflow per day; `Send budget alert to Slack` posts the resulting message, reached regardless of whether `Unpublish workflow` also ran.
- **Final output:** a Slack message in the configured channel (channel itself unresolved in this export) stating which workflow, how much it spent, its budget, how many calls, and whether it was also deactivated.

## 7. Execution Evidence

### 7.1 Captured run — Workflow 2 (chat/Q&A path)

**Critical path executed:** `Chat Interface` → `RAG Agent` → (`OpenAI Chat Model`, `Retrieve from Pinecone` → `Query Embeddings` + `Cohere Reranker`) → answer. This is the path chosen in the original test plan: it is short enough to inspect in one execution view, it exercises the most distinct node types of the three workflows (trigger, agent, 3 AI sub-node types, reranker), and it produces an observable, human-readable output that is easy to check against the input question. The source document was a one-page test PDF, **"LagerFlow – Product FAQ"** (a fictional warehouse-management SaaS company, created for this test), ingested beforehand through the `Upload Documents Form` → `Store in Pinecone` path.

All raw evidence files referenced below are in [`evidence/`](./evidence/): `chat_interface.png`, `query_embedding_Chatbot_output.json`, `retreived_from_pinecone.json`, `reranker_output.json`. None contain credentials, API keys, or secrets — only chat text, an embedding vector, and retrieved document content/metadata.

**1. Input payload** (typed into the public chat widget, visible in `evidence/chat_interface.png`):
```
How much does LagerFlow cost?
```

**2. `Query Embeddings` output** — confirms the question was converted into a vector before retrieval (`evidence/query_embedding_Chatbot_output.json` holds the tail of the 512-dimension vector configured on this node; full excerpt):
```json
[ "...", -0.06488037109375, 0.01454925537109375, 0.05914306640625, 0.01064300537109375,
  -0.06695556640625, -0.0677490234375, -0.0027942657470703125, -0.020111083984375,
  0.06683349609375, 0.027130126953125, 0.02880859375, -0.0361328125,
  0.043609619140625, -0.015777587890625, 0.00295257568359375, 0.0306243896484375 ]
```
This is a tail excerpt of the full vector (copied from the n8n output panel, not re-typed), consistent with the `OpenAI Embeddings`/`Query Embeddings` node's configured `dimensions: 512`.

**3. `Retrieve from Pinecone` output** — two ranked chunks returned from the shared `"n8n"` Pinecone index, each as a JSON-encoded `pageContent` + `metadata` string (full content in `evidence/retreived_from_pinecone.json`):
```json
{
  "pageContent": "LagerFlow – Product FAQ\nFictional company, made for training only. Version: November 2026.\n...\n3. How much does LagerFlow cost?\nThere are three plans, billed per month: Basic costs 490 EUR (1 warehouse, up to 10 users). Business costs 1,290 EUR (up to 3 warehouses, up to 50 users). Enterprise has a custom price (more than 3 warehouses). There is a one-time setup fee of 2,500 EUR for all plans. 4. How long does setup take?",
  "metadata": {
    "blobType": "application/pdf",
    "loc.lines.from": 1, "loc.lines.to": 16,
    "pdf.info.Title": "LagerFlow Product FAQ",
    "pdf.info.CreationDate": "D:20261031230902+00'00'",
    "source": "blob"
  },
  "id": "a79254d8-a892-4e56-835c-beca2163e568"
}
```
A second, near-duplicate chunk (`id: aa85f12e-d145-4029-8cbb-8e1e5c4ed9a1`) was also retrieved — expected here since the one-page source PDF is shorter than the configured chunk size, so the splitter produced overlapping chunks covering the same page.

**4. Cohere reranker contribution** — `evidence/reranker_output.json` is a copy of the same `aa85f12e-...` chunk's `metadata` block **after** reranking, showing the field the reranker adds on top of Pinecone's raw similarity match:
```json
{ "...": "...", "relevanceScore": 0.7038554, "id": "aa85f12e-d145-4029-8cbb-8e1e5c4ed9a1" }
```
`relevanceScore` is not a Pinecone field — it is written by `Cohere Reranker` over the `ai_reranker` connection into `Retrieve from Pinecone`, confirming the rerank step actually ran and scored the candidates (per the node's `useReranker: true` setting) rather than passing raw vector-similarity order straight through.

**5. Final output record** — from `evidence/chat_interface.png`, the `RAG Agent`'s streamed answer shown in the chat panel:
```
LagerFlow has three monthly plans: Basic costs 490 EUR, Business costs 1,290 EUR, and
Enterprise has a custom price. There is also a one-time setup fee of 2,500 EUR for all
plans. Source: LagerFlow – Product FAQ.
```
The screenshot's execution log panel confirms the full node path ran successfully: `Chat Interface → RAG Agent` (overall **Success in 4.264s, ~1751 tokens**), with `Retrieve from Pinecone` reported individually as **Success in 979ms**, and `Query Embeddings` / `Cohere Reranker` nested underneath it as its sub-node calls.

**Success criteria check:**
- ✅ End-to-end execution status: success (no error nodes in the log tree).
- ✅ Answer is grounded: every figure in the answer (490 EUR, 1,290 EUR, custom Enterprise price, 2,500 EUR setup fee) traces directly to the retrieved `pageContent` text in step 3 — no fabricated numbers.
- ✅ Citation present: the answer ends with `Source: LagerFlow – Product FAQ.`, matching `pdf.info.Title` in the retrieved chunk's metadata, as instructed by the `RAG Agent`'s system message.
- ✅ Reranking is demonstrably active: `relevanceScore` is present on the retrieved chunk, a field only the Cohere reranker adds.
- ⬜ Not tested in this run: the "I couldn't find that in the uploaded documents" fallback for an out-of-scope question. A second run with an unanswerable question (e.g., "What is LagerFlow's refund policy?", which this one-page FAQ does not cover) is still needed to confirm that fallback path and remains open.

### 7.2 Still outstanding

- **Workflow 1 (ingestion path):** no direct evidence of `Upload Documents Form → Document Loader → Text Splitter → OpenAI Embeddings → Store in Pinecone` was captured on its own — its success is inferred here only indirectly, from the fact that Workflow 2 could retrieve the LagerFlow FAQ content at all. A direct capture (e.g., a screenshot of `Store in Pinecone`'s output after uploading a new file) would close this gap.
- **Workflow 3 (LLM spend tracker):** not executed. Per Section 8, this workflow also ships with empty `credentials`/unresolved `dataTableId`/`channelId`, so a first manual run (per its own sticky-note setup instructions) is required before any evidence can be captured here.
- **Fallback-answer behavior:** as noted above, a run with an out-of-scope question has not yet been captured to confirm the agent's "not found" response path.


## 8. Operational Risks and Failure Modes

### Workflow 1/2 — RAG system

| Risk | Why it could fail | How to detect | Consequence | Mitigation |
|---|---|---|---|---|
| Chat answers before ingestion completes or indexes an empty/wrong namespace | No workflow-level dependency links ingestion to chat (Section 3.1) — only the external Pinecone index name ties them together | Agent answers "I couldn't find that" for content that was supposedly just uploaded; Pinecone index shows 0 or stale vector count | Users get wrong/empty answers and may distrust the tool | Add a check (e.g., a Pinecone count check or a "last indexed" timestamp) before enabling chat, or at minimum document the required run order |
| Pinecone/OpenAI/Cohere API failures | Any of 3 external APIs (OpenAI embeddings, Pinecone, Cohere) can rate-limit, time out, or reject a request; no retry/error-handling settings are visible in this export | Execution fails or the agent returns a generic error; n8n execution list shows `error` status | User-visible failure mid-conversation; for ingestion, a partially-embedded/partially-stored document | Add `retryOnFail`/`onError: continueErrorOutput` settings and a fallback user-facing message |
| Poor retrieval relevance despite reranking | `topK: 5` is a fixed, possibly too-small or too-large window; chunking uses default split params that may split mid-sentence/mid-table for some document types (PDF tables, CSV) | Agent cites a source but the cited chunk doesn't actually support the answer; manual spot-check of retrieved chunks vs. answer | Confidently wrong or weakly-supported answers despite the "only answer from context" instruction | Tune `topK` and chunk size per document type; periodically sample real conversations against retrieved context |
| Unsupported file content | `acceptFileTypes: ".pdf,.csv,.json"` accepts the file type but the Document Loader's actual parsing success for scanned/image-only PDFs or malformed CSV/JSON is not guaranteed by this config alone | `Document Loader`/`Text Splitter` output is empty or near-empty for a given upload | Silent knowledge gaps — the document "uploaded successfully" but contributes nothing retrievable | Add a post-ingestion check (e.g., chunk count > 0) and surface it to the uploader |

### Workflow 3 — LLM spend tracker

| Risk | Why it could fail | How to detect | Consequence | Mitigation |
|---|---|---|---|---|
| Missing/invalid credentials | `Get recent executions`, `Unpublish workflow`, `Send budget alert to Slack`, and all `Data Table` nodes export with **empty `credentials: {}` and unresolved `dataTableId`/`channelId`** — these must be set per-installation | First real run fails immediately at `Get recent executions` or later nodes with an authentication/"resource not found" error | The entire tracker is silently non-functional from day one if not configured, giving a false sense that spend is being monitored | Treat initial setup (API key, data table selection, Slack channel) as a hard precondition; verify with one manual run before enabling the schedule, exactly as the workflow's own sticky note instructs |
| Stale or missing model prices in `pricesPer1M` | `priceFor()` returns `null` for any model not an exact or prefix match in the hardcoded JSON string; prices themselves can go stale as providers change pricing | `costUsd: null` rows accumulate, `unpriced` count grows in Slack messages, but **no error is raised and no alert is guaranteed to fire** | Real spend is under-reported; a workflow could blow well past its real-dollar budget without an alert, because the unpriced calls never contribute to the sum compared against `dailyBudgetUsd` | Alert (separately) when `unpriced` count/ratio is high; review `pricesPer1M` on a schedule tied to provider pricing-page changes |
| Executions still running at poll time | `if (!ex.stoppedAt) continue;` intentionally skips in-flight executions, deferring them to the next 15-minute poll | A very long-running execution's cost isn't counted until it finishes, potentially well after the actual spend occurred | Budget alerts can lag real spend by however long the slowest execution takes, defeating "alert before the month's budget burns" for very long-running loops | Reduce the interval for latency-sensitive setups, or add a secondary "still running" cost estimate pass |
| Duplicate/double-counted rows if the dedup key assumptions are wrong | `callKey` is `${executionId}:${nodeName}:${runIndex}` — correct only if n8n never reuses an execution ID or reorders `runData` entries for retried executions | Data table row counts don't match number of actual LLM calls; same execution/node/run combination logged twice with different data if retried | Inflated reported spend, false budget-exceeded alerts | Add a uniqueness constraint on `callKey` at the data-table level if supported, and spot-check counts after a retried execution |
| Slack alert failure | `channelId` is unresolved in this export and must be selected; Slack API itself can rate-limit or the bot can lose channel access | `Send budget alert to Slack` node errors are visible in the execution log but, since this node is the last step, nothing downstream signals the failure elsewhere | A real budget overrun goes completely unnoticed if the one and only notification channel silently fails | Add a fallback notification channel (e.g., email) or at least surface Slack-send failures to a separate monitoring execution-failure alert in n8n itself |

**First failure mode to monitor if Workflow 3 ran daily:** **missing/invalid credentials and unresolved resource IDs** (the n8n API credential, the Data Table ID, and the Slack channel ID are all empty/unresolved in this export). This is prioritized over the pricing and timing risks because it is a **total failure, not a degraded one** — if any of these three bindings isn't completed, the entire pipeline either errors out immediately at `Get recent executions` or silently produces no usable rows/alerts, meaning nobody is actually being warned about budget overruns at all, which is the one job this workflow has. The pricing-staleness and running-execution-lag risks only degrade accuracy; this one removes the safety net entirely. Concretely: watch the n8n execution list for this workflow for `error` status immediately after `Get recent executions`, `Skip calls already logged`/`Insert usage rows`, or `Send budget alert to Slack` — any of the three failing silently (or erroring) on day one means the monitor itself isn't being monitored.

## 9. Key Learning Observations

- **A single workflow file can contain multiple logical "workflows."** Reading the `connections` map, not the file's description or variable names, is the only reliable way to know whether two trigger paths are actually wired together or merely coexist in the same file (Section 3.1).
- **AI sub-nodes (`@n8n/n8n-nodes-langchain.*`) use typed connections (`ai_embedding`, `ai_tool`, `ai_languageModel`, `ai_reranker`, `ai_document`, `ai_textSplitter`), not `main`.** They cannot be understood by looking at `main` connections alone — the `connections` object's keys for each sub-node must be read directly.
- **A node's title/description in documentation or a sticky note is not proof of its behavior — the `parameters` block is.** Reading Workflow 3's actual node-by-node logic, rather than assuming its function from a title, is exactly the scenario this lab is designed to train against.
- **Token usage and monetary cost are computed in two different places and can silently diverge.** `totalTokens` is read straight from provider/estimate data; `costUsd` depends entirely on a manually maintained price table and is `null`, not zero, when pricing is missing — a detail easy to miss when skimming the Code node.
- **Where credentials/IDs are left empty in an export is itself useful information.** An unresolved `dataTableId`, `channelId`, or empty `credentials: {}` is not a bug in the JSON — it is the expected state of a shareable template, and it tells you exactly what a deployer must configure before the first run, which is also exactly where "missing config" failures will surface first.
- **Deterministic orchestration and model decision-making are cleanly separable in the JSON.** In Workflow 2, everything up to "pass the message to `RAG Agent`" is fixed wiring; everything after is a model decision (whether to call the retrieval tool, what to retrieve, how to answer) — useful for reasoning about where non-determinism (and thus unpredictable risk) actually enters a workflow.

## 10. References

- n8n node/integrations documentation: https://docs.n8n.io/integrations/
- n8n expressions guide (`{{ $json.field }}` and related syntax used throughout Workflow 3's Set/IF/Slack nodes): https://docs.n8n.io/code/expressions/
- n8n executions and debugging (execution view, input/output inspection): https://docs.n8n.io/
- n8n Data Tables: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.datatable/
- n8n AI/LangChain nodes overview (agent, sub-nodes, tool connections): https://docs.n8n.io/advanced-ai/
- n8n Code node: https://docs.n8n.io/code/code-node/
- n8n Community Forum: https://community.n8n.io/
