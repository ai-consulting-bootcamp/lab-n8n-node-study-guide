# Lab proof: n8n Node Study Guide

Lab: "Become the person who reads the docs" (Week 4)

This file is the entry point for the reviewer. Screenshots are in `screenshots/`, workflow exports are in `workflows/`.

## Step 3.1: First workflow selected

**I selected Class Workflow 1, the PDF-based RAG system (the one built in class with the Upload Documents Form, OpenAI embeddings, a vector store and a chat agent), as the first workflow to analyse.** I chose it because it contains the most node types, as the lab suggests for Step 3.1.

- I imported the instructor's JSON file `rag chatbot with no reranker.json` (the instructor replaced the first "with reranker" file with this one during class) and ran it in my own n8n instance.
- Evidence tied to this workflow: `screenshots/form_params.png`, `screenshots/form_output.png`, `screenshots/vector_store.png`, `screenshots/embeddings.png`, `screenshots/chat_interface.png`, `screenshots/rag_agent.png`, `screenshots/rag_chat.png`, and the export `workflows/workflow1_rag.json`.
- One change from the class version: the Pinecone nodes failed on my account (see section 1), so I replaced them with Simple Vector Store and documented the reason.
- My own small workflow (Manual Trigger, Edit Fields, If) is Workflow 3 in this study guide. It is an extra I built, not the workflow I selected in Step 3.1.

## 1. Workflows analysed

| # | Workflow | Nodes |
|---|---|---|
| 1 | PDF RAG, indexing half (class workflow) | Upload Documents Form, Document Loader, Text Splitter, OpenAI Embeddings, Simple Vector Store (Insert Documents) |
| 2 | AI agent chat, chat half of the same RAG workflow | Chat Interface, RAG Agent, OpenAI Chat Model, Simple Vector Store (tool), Query Embeddings |
| 3 | My own small workflow | Manual Trigger, Edit Fields, If |

Note: the class materials did not contain a separate "AI agent chat" workflow, so I documented the Chat Interface and RAG Agent half of the RAG workflow as Workflow 2.

Note on the vector store: the class workflow uses Pinecone. My Pinecone index was created with a document schema, and n8n's Pinecone node failed with this error:

> This index has a document schema, so writes must go through the documents API. ... The vectors and records write endpoints do not support document schemas.

I replaced the Pinecone nodes with n8n's Simple Vector Store (memory key `lab_faq`) and the workflow then ran end to end. See sections 7 and 8.

## 2. Input payload (Workflow 3)

The Manual Trigger sends one empty item:

```json
[{}]
```

Edit Fields then adds the fields (see section 3).

## 3. Output record (Workflow 3)

Edit Fields output, and the item that arrived on the If node's True Branch:

```json
{ "name": "murat", "score": 75 }
```

## 4. Execution trace (Workflow 3)

![execution trace](screenshots/trace.png)

- All three nodes are green, each connection shows `1 item`.
- Logs: whole run succeeded in 204 ms, If node in 1 ms.
- If input: `name = murat`, `score = 75`. If output: True Branch has 1 item, False Branch shows "No output data in this branch".
- The condition is `{{ $json.score }}` is greater than `50`, so the item is routed to `true`.

## 5. RAG evidence (Workflows 1 and 2)

Indexing run: the upload form received `LagerFlow_Product_FAQ.pdf`. The form output contains (JSON view):

```json
{
  "documents": [ { "filename": "LagerFlow_Product_FAQ.pdf", "mimetype": "application/pdf", "size": 3602 } ],
  "submittedAt": "2026-11-03T23:59:49.899+01:00",
  "formMode": "test"
}
```

The connections after the splitter show `3 items`, so the 3.6 kB PDF produced 3 chunks.

Chat run: question "What does LagerFlow do?"

![chat and logs](screenshots/rag_chat.png)

- Answer: LagerFlow is cloud software for warehouse management (WMS) for small and medium logistics companies, with stock, incoming goods, picking, packing, shipping and handheld barcode scanner support. The answer ends with "Source used: LagerFlow Product FAQ".
- Logs show the agent decided to call the retrieval tool: OpenAI Chat Model (154 tokens, tool decision), Simple Vector Store1 (216 ms, 4 items retrieved), Query Embeddings (208 ms), then OpenAI Chat Model again (1,797 tokens) to write the answer. Total 6.053 s, 1,951 tokens.
- The answer matches the content of the uploaded PDF, and the system message tells the agent to answer only from retrieved context.

## 6. Node reference table

| Node | Parameters | Settings | What it does | JSON input | JSON output | Key transformation |
|---|---|---|---|---|---|---|
| Manual Trigger | none | default | Starts the run when I click Execute workflow | none (first node) | 1 empty item `{}` | Creates the start signal |
| Edit Fields (Set) | Mode: Manual Mapping; `name` String `murat`; `score` Number `75` | Include Other Input Fields: off | Adds fields to the item | empty item | `{ name, score }` | 2 fields added, types set (T string, # number) |
| If | Condition `{{ $json.score }}` is greater than `50` | Convert types where required: off | Routes the item to a true or false output | `{ name, score }` | same JSON on True Branch (1 item) | Routing only, data unchanged |
| Upload Documents Form (Form Trigger) | Form Title "Upload Documents for RAG"; element File, field name `documents`, accepted `.pdf, .csv, .json`; Respond When: Form Is Submitted | Authentication: None; Test URL and Production URL | Serves a web form and starts the workflow on submit | form submission | `documents[]` with filename, mimetype, size, plus `submittedAt`, `formMode` | Uploaded file becomes a binary item |
| Text Splitter | Chunk Size 1000, Chunk Overlap 0 | no options | Splits document text into chunks (sub-node, output shown through the parent) | PDF document (filename, extension, mime type, 3.6 kB) | 3 chunks (connection label "3 items") | One document to several chunks |
| OpenAI Embeddings | Model `text-embedding-3-small`, Dimensions 1536 | default | Turns text into vectors | chunk or question text | vector of 1536 values (label "1536 items") | Text to numbers |
| Simple Vector Store (Insert Documents) | Operation Mode Insert Documents; Memory Key `lab_faq`; Embedding Batch Size 200 | Clear Store: off; n8n warns data is in memory only | Stores documents and vectors | documents plus embeddings | 3 stored items | Chunks and vectors written to memory |
| Chat Interface (Chat Trigger) | Hosted Chat; Make Chat Publicly Available on; initial message; Response Mode Streaming | Authentication: None | Starts the flow on a chat message | chat message | `action`, `sessionId`, `chatInput` | Message becomes an item |
| RAG Agent (AI Agent) | Source for prompt: Connected Chat Trigger Node; prompt `{{ $json.chatInput }}`; system message (answer only from retrieved context, say "I couldn't find that in the uploaded documents" if missing, cite sources) | Streaming on; fallback model off; output format off | Decides when to call the retrieval tool and writes the answer | `chatInput` | `output` text with source line | Question to grounded answer |
| OpenAI Chat Model | Credential OpenAI; model `gpt-5.4-mini` (From list); Use Responses API on | no built-in tools, no options | The LLM used by the agent | prompt | text (2 calls in my run) | Prompt to text |

## 7. Mapping and risk explanation

- `score` is set as a Number in Edit Fields because the If node compares it with a number and "Convert types where required" is off. If `score` were a string, the comparison could fail or route wrongly.
- The If node does not change the data; it only decides the branch.
- The embedding dimension (1536) has to match between insert and query. Both OpenAI Embeddings nodes use `text-embedding-3-small` with 1536 dimensions. A mismatch would break retrieval.
- In the RAG flow the agent chooses to call the tool; the system message limits answers to retrieved content, which is the grounding control.

## 8. Explain: first failure mode I would monitor if this ran daily

**A missing or empty vector store.**

Evidence from my own work: the Store in Pinecone node failed with the document-schema error above, and earlier with "Index n8n not found". Both are integration and index problems that stop the knowledge base from being filled. After I switched to Simple Vector Store, a second risk appears: n8n warns that the data lives in memory, is lost if n8n restarts and may be cleared when memory is low. The agent would then answer "I couldn't find that in the uploaded documents" even though the workflow itself shows green.

Controls I would add: an error workflow with a notification, a check that the store contains items after each ingest, and a scheduled test question. Retry On Fail would help with temporary API errors but not with a wrong index type or a cleared store.

## 9. Limitations

- Simple Vector Store is in memory only (not persistent) and is accessible to all users of the instance.
- The Form and the Chat Interface use Authentication: None, and the chat is set to public, so anyone with the URL could use them once published.
- Only one chat question was tested; I did not measure retrieval quality or run a reranker.
- The Text Splitter uses chunk overlap 0, so a sentence cut at a chunk boundary could lose context.
- Text Splitter is a sub-node; its own output panel is empty until the parent node runs, so I took its chunk count from the connection labels.
- The class "with reranker" workflow (Cohere) was not used; the instructor replaced it with the "no reranker" version.

## 10. Files

- `workflows/workflow3_if.json`: Manual Trigger, Edit Fields, If
- `workflows/workflow1_rag.json`: RAG workflow (credentials not included)
- `screenshots/`: node configuration, input/output and trace screenshots

No API keys, tokens or personal data are included in these files.
