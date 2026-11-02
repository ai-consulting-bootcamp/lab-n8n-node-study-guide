# lab_proof.md — Become the person who reads the docs

**Student:** Nicolò
**Date:** 2026-11-02
**n8n instance:** class instance (URL omitted)

## Contents
1. n8n Node Reference Table
2. Workflow A — Lena-qualify lead (configuration, input payload, execution trace, output record)
3. Workflow B — RAG Chatbot (with reranker) (configuration, input payload, execution trace, output record)
4. Verify / Explain

> Secrets check: no API keys, tokens or credential values are included. Credentials are listed by type only. Form, chat and webhook URLs are omitted.

---

## 1. n8n Node Reference Table

| Node | Parameters | Settings | What It Does | JSON Input | JSON Output | Key Transformations |
|------|------------|----------|--------------|------------|-------------|---------------------|
| Manual Trigger (`manualTrigger` v1) | none | default | ✏️ | none (click on "Execute workflow") | `{}` (1 empty item) | ✏️ |
| Edit Fields — raw mode (`set` v3.4) | Mode: raw JSON; JSON Output (lead object); Include Other Fields: all | default | ✏️ | `{}` | Lead object: name, email, company, company_size, industry, job_title, message | ✏️ |
| If (`if` v2.3) | Condition: `{{ $json.company_size }}` number ≥ 50; Combinator: AND | Case sensitive: on; Type validation: strict | ✏️ | Lead object | True: lead object (1 item) · False: `[]` | ✏️ |
| Edit Fields1 — manual mode (`set` v3.4) | Mode: manual mapping; Assignment: Priority = "high" (string); Include Other Fields: all | default | ✏️ | Lead object | Lead object + `Priority: "high"` | ✏️ |
| Message a model (`openAi` v2.1) | Resource: text; Operation: response; Model: gpt-5.4-mini; Messages: system + user (expression with `$today`, name, job_title, company, message); Simplify: on | Credential: OpenAI API | ✏️ | Lead object + Priority | `{ output: [ { role: "assistant", content: [ { type: "output_text", text: "Hi Lena, …" } ] } ] }` | ✏️ |
| Upload Documents Form (`formTrigger` v2.5) | Title, Description; Field: file `documents`, multiple, .pdf/.csv/.json, not required; Response mode: on received | Authentication: none | ✏️ | Form submission (HTTP) | not run in this capture | ✏️ |
| Store in Pinecone (`vectorStorePinecone` v1.3, insert) | Mode: insert; Index: lagerflow-faq; Embedding batch size: 200 | Credential: Pinecone API | ✏️ | not run in this capture | not run in this capture | ✏️ |
| OpenAI Embeddings (`embeddingsOpenAi` v1.2) | Model: text-embedding-3-small; Dimensions: 512 | Credential: OpenAI API | ✏️ | sub-node (no main input) | sub-node (no main output) | ✏️ |
| Document Loader (`documentDefaultDataLoader` v1.1) | Data type: binary; Mode: all input data; Loader: auto; Text splitting: custom | default | ✏️ | sub-node | sub-node | ✏️ |
| Text Splitter (`textSplitterRecursiveCharacterTextSplitter` v1) | Chunk size: 1000; Chunk overlap: 0 | default | ✏️ | sub-node | sub-node | ✏️ |
| Chat Interface (`chatTrigger` v1.4) | Public: true; Mode: hosted chat; Initial message; Response mode: streaming | Authentication: none | ✏️ | Message typed in chat | `{ action: "sendMessage", sessionId, chatInput: "whats the cost?" }` | ✏️ |
| RAG Agent (`agent` v3.1) | Prompt: `{{ $json.chatInput }}`; System message (answer only from context, cite sources); Streaming: on | default | ✏️ | `{ action, sessionId, chatInput }` | `{ output: "The uploaded document says LagerFlow has three monthly plans: …" }` | ✏️ |
| OpenAI Chat Model (`lmChatOpenAi` v1.3) | Model: gpt-5.4-mini; Responses API: on | Credential: OpenAI API | ✏️ | sub-node (called 2× by agent) | sub-node | ✏️ |
| Retrieve from Pinecone (`vectorStorePinecone` v1.3, retrieve-as-tool) | Mode: retrieve as tool; Tool description; Index: n8n; Limit (topK): 5; Include metadata: on; Rerank results: on | Credential: Pinecone API | ✏️ | `{ input: "cost pricing price fee charges total cost expenses what is the cost" }` | `{ response: [3 × { type: "text", text: { pageContent, metadata, id } }] }` | ✏️ |
| Query Embeddings (`embeddingsOpenAi` v1.2) | Model: text-embedding-3-small; Dimensions: 512 | Credential: OpenAI API | ✏️ | sub-node | sub-node | ✏️ |
| Cohere Reranker (`rerankerCohere` v1) | Model: rerank-v3.5; Top N: 3 | Credential: Cohere API | ✏️ | sub-node | sub-node | ✏️ |

✏️ = write in your own words.

**Version notes vs. the lab template:**
- The If node (v2.3) uses a condition builder (left value / operator / right value, plus a combinator). It does not use separate Value1 / Operation / Value2 fields.
- The OpenAI node here is "Message a model" with resource `text` and operation `response`.

---

## 2. Workflow A — Lena-qualify lead

### 2.1 Configuration
**Flow:** When clicking 'Execute workflow' → Edit Fields → If
- If **true** → Edit Fields1 → Message a model
- If **false** → Edit Fields2 (priority = "normal", reply = templated price-list email)

**Edit Fields** — Set v3.4, mode raw, include other fields: all

**If** — v2.3
- `{{ $json.company_size }}` number gte 50
- AND combinator, case sensitive, strict type validation

**Edit Fields1** — Set v3.4, manual mapping
- Priority = "high" (string), include other fields: all

**Message a model** — OpenAI v2.1
- Resource: text, operation: response, model: gpt-5.4-mini, simplify: on
- System: "You are a friendly sales assistant for a B2B software company. Write replies of maximum three sentences. Always suggest two demo dates next week."
- User: `=Today is {{ $today }}. Write a reply to {{ $json.name }}, {{ $json.job_title }} at {{ $json.company }}. Her message: {{ $json.message }}`

### 2.2 Input payload
```json
{
  "name": "Lena",
  "email": "lena@example.com",
  "company": "ABC GmbH",
  "company_size": 100,
  "industry": "logistics",
  "job_title": "Head of Operations",
  "message": "We're moving our warehouses to a new system in January and need a solution before then."
}
```

### 2.3 Execution trace
Status: **success** (manual / test execution)

| # | Node | Status | Time | Items in → out |
|---|------|--------|------|----------------|
| 1 | When clicking 'Execute workflow' | success | 1 ms | 0 → 1 |
| 2 | Edit Fields | success | 0 ms | 1 → 1 |
| 3 | If | success | 1 ms | 1 → true: 1 / false: 0 |
| 4 | Edit Fields1 | success | 1 ms | 1 → 1 |
| 5 | Message a model | success | 2,798 ms | 1 → 1 |
| — | Edit Fields2 | not executed (false branch empty) | — | — |

**Edit Fields1 output:**
```json
{
  "name": "Lena",
  "email": "lena@example.com",
  "company": "ABC GmbH",
  "company_size": 100,
  "industry": "logistics",
  "job_title": "Head of Operations",
  "message": "We're moving our warehouses to a new system in January and need a solution before then.",
  "Priority": "high"
}
```

### 2.4 Output record
```json
{
  "output": [
    {
      "type": "message",
      "status": "completed",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "Hi Lena, thanks for reaching out — that sounds like a perfect fit for planning now so you're ready before the January rollout. I'd be happy to show you how our solution can support the warehouse transition and help you stay on schedule; would Tuesday, November 10 or Thursday, November 12 work for a demo next week?"
        }
      ]
    }
  ]
}
```

---

## 3. Workflow B — RAG Chatbot (with reranker)

### 3.1 Configuration
**Path A — Ingestion** (not executed in this capture)
- Upload Documents Form → Store in Pinecone
- Sub-nodes on Store in Pinecone:
  - OpenAI Embeddings (embedding)
  - Document Loader (document)
- Text Splitter is a sub-node on Document Loader.

**Path B — Chat / retrieval** (executed)
- Chat Interface → RAG Agent
- Sub-nodes on RAG Agent:
  - OpenAI Chat Model (model)
  - Retrieve from Pinecone (tool)
- Sub-nodes on Retrieve from Pinecone:
  - Query Embeddings (embedding)
  - Cohere Reranker (reranker)

Node parameters are in the reference table above.

### 3.2 Input payload
Chat message: **"whats the cost?"**
```json
{
  "action": "sendMessage",
  "sessionId": "65360ab1…",
  "chatInput": "whats the cost?"
}
```

### 3.3 Execution trace
Status: **success** (test execution, chat path only)

| # | Node | Items | Note |
|---|------|-------|------|
| 1 | Chat Interface | 1 out | Receives chat message |
| 2 | RAG Agent | 1 in → 1 out | Calls the model and the retrieval tool |
| 2a | OpenAI Chat Model | called 2× | Sub-node of agent |
| 2b | Retrieve from Pinecone | 1 in → 1 out (3 results) | Tool input written by the agent |
| 2c | Query Embeddings | — | Embeds the tool query |
| 2d | Cohere Reranker | 3 results kept | Top N = 3 |

**Retrieve from Pinecone input:**
```json
{ "input": "cost pricing price fee charges total cost expenses what is the cost" }
```

**Retrieve from Pinecone output** (3 results; same shape each, text shortened):
```json
{
  "response": [
    {
      "type": "text",
      "text": {
        "pageContent": "LagerFlow – Product FAQ … 3. How much does LagerFlow cost? There are three plans, billed per month: Basic costs 490 EUR … one-time setup fee of 2,500 EUR for all plans. …",
        "metadata": {
          "blobType": "application/pdf",
          "loc.lines.from": 1,
          "loc.lines.to": 16,
          "pdf.info.Title": "LagerFlow Product FAQ",
          "pdf.totalPages": 1,
          "source": "blob"
        },
        "id": "563fc999-…"
      }
    }
  ]
}
```
Result ids: 563fc999-…, 666f4271-…, c028c871-…
All three results have identical pageContent and metadata.

### 3.4 Output record
```json
{
  "output": "The uploaded document says LagerFlow has three monthly plans:\n\n- Basic: 490 EUR/month\n- Business: 1,290 EUR/month\n- Enterprise: custom price\n\nThere is also a one-time setup fee of 2,500 EUR for all plans.\n\nSource used: **LagerFlow – Product FAQ**"
}
```

---

## 4. Verify / Explain

**Execution evidence that proves the workflows ran:**
✏️

**Mapping justification (why the fields map the way they do):**
✏️

**What is the first failure mode you would monitor if this workflow ran daily?**
✏️
