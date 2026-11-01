# Three-workflow study

The class exports were not supplied. The instructions explicitly permit similar official library templates; these two exact-name templates were downloaded and their node parameters and connections inspected. Sanitized configuration snapshots accompany this analysis. Credential IDs and account references were omitted. These are configuration inspections, not successful executions of paid-service workflows.

## Workflow 1: PDF RAG

Official source: [template 5734](https://n8n.io/workflows/5734-build-a-pdf-based-rag-system-with-openai-pinecone-and-cohere-reranking/). Snapshot: [pdf_rag_template.json](pdf_rag_template.json).

Observed configuration:

- Form Trigger requires a single `.pdf` file under File.
- Its main connection enters Pinecone in insert mode, index `n8n`.
- Default Data Loader supplies binary documents, using custom splitting. A Recursive Character Text Splitter connects through `ai_textSplitter`.
- OpenAI Embeddings specifies dimensions 1024 and connects to both Pinecone instances through `ai_embedding`.
- Chat Trigger connects to AI Agent. Its system instruction says to answer from VectorDB and admit not knowing when information is absent.
- The agent has OpenAI Chat Model `gpt-4.1`, Simple Memory, and VectorDB attached through typed AI connections.
- VectorDB is Pinecone retrieve-as-tool, index `n8n`, topK 20, useReranker true. Cohere Reranker connects through `ai_reranker`.

Data boundary: form file → binary document loader → chunks/embeddings → index; chat message → agent → retrieved/reranked context → generated answer. AI sub-node connections do not represent ordinary sequential JSON item outputs. Actual uploaded file bytes, vectors, ranked documents, answer JSON, and timings are unavailable because this template was not executed. No source-grounding success is claimed from its system prompt alone.

Risks to check before running: embedding dimensions must match the actual Pinecone index; PDF parsing can lose content; reranking cannot recover absent chunks; credentials, quotas, and grounded citations require independent verification.

## Workflow 2: AI agent chat

Official source: [template 1954](https://n8n.io/workflows/1954-ai-agent-chat/). Snapshot: [ai_chat_template.json](ai_chat_template.json).

Observed configuration: Chat Trigger → AI Agent on the main connection. OpenAI Chat Model `gpt-4o-mini`, Simple Memory, and SerpAPI connect through `ai_languageModel`, `ai_memory`, and `ai_tool`. The agent parameters contain only empty options; no custom grounding instruction is visible in this snapshot.

Data boundary: a chat event supplies prompt/session data; model, memory, and search tool contribute through typed connectors; the agent produces the answer. Actual search calls, model output, session persistence, costs, and citations were not observed. Empty options mean defaults, not proof of successful configuration or an empty answer.

## Workflow 3: local ticket processing and node exercises

[workflow.json](../workflow.json) contains the requested minimal ticket path. Edit Fields creates the supplied fixture; it is not an incoming webhook. IF checks the ticket ID, allowed category, nonblank message, and allowed priority. True maps to an accepted record with a queue; false maps to a rejection. No ticket is persisted or sent to a support service.

[local_nodes.json](local_nodes.json) is a separate exercise to study ten distinct local node types without adding unnecessary steps to the ticket workflow: Manual Trigger, Edit Fields, IF, Split Out, Remove Duplicates, Sort, Limit, Switch, Merge, Aggregate. Two Set branches give Merge two actual inputs. Study examples are synthetic fixtures, not real customer records.

The node reference and lab proof distinguish actual local execution evidence from the two unexecuted template inspections.
