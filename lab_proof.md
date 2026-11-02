# n8n Node Reference Table

**Lab:** Become the person who reads the docs
**Author:** Ayhan Demir | Ironhack AI Consulting & Integration Bootcamp | November 2026


## Workflows analysed (also in the excel in same repo with more details and better UI)

| Key | Workflow | Nodes | Flow |
|---|---|---|---|
| **W1.a** | RAG Chatbot (simple, no reranker) | 10 | Ingest: Form Trigger -> Pinecone insert (Data Loader + Text Splitter + Embeddings). Chat: Chat Trigger -> AI Agent (Chat Model + Pinecone tool + Query Embeddings) |
| **W1.b** | RAG Chatbot (with reranker) | 11 | Same as W1.a, plus Cohere Reranker on the Pinecone tool and streaming chat |
| **W2** | AI chat Agent (news reporter) | 2 | Manual Trigger -> OpenAI "Message a model" with web search |
| **W3** | Lena Company size (lead routing) | 6 | Manual Trigger -> Edit Fields (sample lead) -> If company_size >= 50 -> true: Edit Fields1 -> OpenAI reply; false: Edit Fields2 (standard reply) |
| **W4** | Canyon AI Content Creator | 14 | Form Trigger -> Code -> HTTP GET (GitHub) -> Code -> HTTP POST (OpenAI) -> Code -> Form review -> If -> approve: Code -> Convert to File -> Form ending; rewrite: Code -> back to HTTP POST |

**17 distinct node types** analysed (plus Sticky Note), across 43 node instances.

# Reference table

| # | Node | Parameters | Settings | What It Does | JSON Input | JSON Output | Key Transformations |
|---|---|---|---|---|---|---|---|
| 1 | **Form Trigger**<br>`n8n-nodes-base.formTrigger` | Form Title (required)<br>Form Description (optional)<br>Form Elements (required): label, type, required flag<br>W1: 1 file field `documents`, accepts `.pdf, .csv, .json`<br>W4: 3 dropdowns (Channel, Product, Language) + text field Topic, all required<br>Options: Append n8n Attribution (off in W1), Button Label ("Generate draft" in W4) | Authentication: None (public form)<br>Test URL vs Production URL (webhookId)<br>Node settings default | Hosts a web form and starts the workflow when someone submits it | Browser form submission (HTTP POST) | W4: `{ "Channel": "Gravel", "Product": "...", "Language": "English", "Topic": "...", "submittedAt": "...", "formMode": "test" }`<br>W1: `{ submittedAt, formMode }` + uploaded file in **binary** `documents` | Form fields -> one n8n item. Field labels become JSON keys. Files go to binary, not JSON |
| 2 | **Chat Trigger**<br>`@n8n/n8n-nodes-langchain.chatTrigger` v1.4 | Make Chat Publicly Available: on (both)<br>Initial Message(s): W1.b greeting text, W1.a none<br>Options: Response Mode (W1.b **Streaming**, W1.a default "When Last Node Finishes") | Authentication: None<br>Public chat URL (webhookId) | Opens a hosted chat window; every user message starts one execution | User chat message | `{ "sessionId": "...", "action": "sendMessage", "chatInput": "What is ...?" }` | Chat text -> item with `chatInput`; `sessionId` ties messages of one conversation together |
| 3 | **Manual Trigger**<br>`n8n-nodes-base.manualTrigger` v1 | None | None | Starts the workflow from the editor button; for testing only (does not run when activated) | None (click) | One empty item: `[ {} ]` | Creates a single empty item so downstream nodes run once |
| 4 | **Edit Fields (Set)**<br>`n8n-nodes-base.set` v3.4 | Mode (required): Manual Mapping or JSON<br>"Edit Fields": JSON = Lena lead payload<br>"Edit Fields1": `priority = "High"` (string)<br>"Edit Fields2": `priority = "normal"`, `reply = "Hi {{ $json.name }}, thank you..."` (expression)<br>Include Other Input Fields: on (all three)<br>Options: Ignore Type Conversion Errors, Support Dot Notation (default) | Node settings default | Creates, overwrites or renames fields on each item | "Edit Fields": `{}` from Manual Trigger<br>"Edit Fields1/2": Lena lead item from If | "Edit Fields": `{ "name": "Lena", "email": "lena@example.com", "company": "ABC GmbH", "company_size": 10, "industry": "logistics", "job_title": "Head of Operations", "message": "..." }`<br>"Edit Fields2": same + `"priority": "normal", "reply": "Hi Lena, thank you..."` | Adds or overwrites fields; input fields kept because Include Other Input Fields is on; expressions resolved per item; types set per field (number 10 stays a number) |
| 5 | **If**<br>`n8n-nodes-base.if` | Conditions (required): left value, operator, right value<br>W3: `{{ $json.company_size }}` Number **>=** 50<br>W4: `{{ $json.Decision }}` String **equals** "Approve and save"<br>Combinator: AND<br>Options: Ignore Case, Convert types where required | Type validation: strict (both)<br>Case sensitive: on<br>Two outputs: true / false | Routes each item to the true or the false output | Any item | Same item, unchanged, on output 0 (true) or 1 (false)<br>W3 sample: Lena (10) goes to **false** -> "Edit Fields2" | No data change, routing only |
| 6 | **Code**<br>`n8n-nodes-base.code` v2 | Language: Python<br>Mode: Run Once for All Items (default, all five)<br>Python code (required); returns a list of `{"json": {...}}` items | Node settings default; errors raised in code stop the run with a clear message | Runs custom Python on the items | "Plan files": 1 brief item<br>"Build prompts": 10 items `{ data }` from Fetch files<br>"Check quality": OpenAI response<br>"Final post" / "Prepare rewrite": Review form answers | "Plan files": 10 items `{ path, url, channel, product, language, topic }`<br>"Build prompts": 1 item `{ channel, product, language, topic, model, system_prompt, user_prompt, banned_phrases, blocks }`<br>"Check quality": `{ round, draft, quality, problems, tokens_in, tokens_out, review_fields }`<br>"Final post": `{ file_name, markdown, quality, message }`<br>"Prepare rewrite": `{ model, system_prompt, user_prompt, feedback }` | Fan-out 1 -> 10 items, fan-in 10 -> 1; label mapping (Gravel -> gravel); markdown parsing and rule-based block selection; validation with `raise`; reads earlier nodes with `_('Build prompts')`; counts rewrite rounds with `_runIndex` |
| 7 | **HTTP Request**<br>`n8n-nodes-base.httpRequest` v4.2 | Method (required): GET / POST<br>URL (required): `{{ $json.url }}` / `https://api.openai.com/v1/chat/completions`<br>Authentication: None / Predefined Credential Type (OpenAI)<br>Send Body: on (POST), Body Content Type JSON, Specify Body: Using JSON (expression)<br>Options: Response > Response Format = **Text** ("Fetch files") | Credential: OpenAI API ("Write draft")<br>Options available: timeout, retry, batching, headers | Calls any HTTP API or URL | "Fetch files": 10 items with `url`<br>"Write draft": 1 item with `model`, `system_prompt`, `user_prompt` | "Fetch files": 10 items `{ "data": "<raw markdown text>" }`<br>"Write draft": OpenAI Chat Completions JSON `{ id, model, choices: [ { message: { role, content } } ], usage: { prompt_tokens, completion_tokens } }` | Runs once per input item (10 GETs); text response wrapped in `data`; JSON body prepared as a Python dict and serialised with `json.dumps` in the Code node; temperature 0.7 sent only for non gpt-5 / o-series models |
| 8 | **OpenAI** (Message a model)<br>`@n8n/n8n-nodes-langchain.openAi` v2.1 | Resource: Text<br>Operation: Message a Model<br>Model (required): gpt-5.4-mini<br>Messages (required): role + content<br>W2: system = news reporter rules; user = "category: technology"<br>W3: system = B2B sales assistant, max 3 sentences, 2 demo dates; user = expression with name, job title, company, message<br>Built-in Tools: Web Search, context size medium (W2 only)<br>Options: temperature, max tokens (default) | Credential: OpenAI API | Sends a prompt to an OpenAI model and returns its reply; in W2 the model can search the web | W2: `{}` from Manual Trigger<br>W3: Lena item with `priority: "High"` | One item with the model reply (text content plus response metadata) | Item fields -> prompt via expressions -> model text |
| 9 | **AI Agent**<br>`@n8n/n8n-nodes-langchain.agent` v3.1 | Prompt source: from connected Chat Trigger (`chatInput`)<br>Options: System Message (answer only from retrieved context; fallback "I couldn't find that in the uploaded documents."; cite documents), Enable Streaming: on<br>Sub-node slots: Chat Model (required), Memory (empty), Tool (Retrieve from Pinecone) | Node settings default | LLM that decides when to call its tools, then answers; here it calls the Pinecone retrieval tool first | `{ sessionId, action, chatInput }` | `{ "output": "<answer with cited documents>" }` (streamed to the chat in W1.b) | Question -> tool call(s) -> grounded answer. No memory attached, so each message is answered without chat history |
| 10 | **OpenAI Chat Model**<br>`@n8n/n8n-nodes-langchain.lmChatOpenAi` v1.3 | Model (required): gpt-5.4-mini<br>Built-in Tools: none<br>Options: temperature, max tokens, etc. (default) | Credential: OpenAI API | Sub-node that supplies the language model to the AI Agent | No main data; connected via `ai_languageModel` | No main data; returns completions to the Agent | Provides capability, not data mapping |
| 11 | **Pinecone Vector Store**<br>`@n8n/n8n-nodes-langchain.vectorStorePinecone` v1.3 | Operation Mode (required): Insert Documents / Retrieve Documents (As Tool for AI Agent)<br>Pinecone Index (required): `lagerflow-faq`<br>Tool: Description (required), Limit (topK) = 5, Rerank Results (on in W1.b)<br>Options: Namespace, Clear Namespace (insert), Include Metadata (tool) | Credential: Pinecone API | Insert: embeds chunks and stores vectors in the index. Tool: lets the Agent search the index for similar chunks | Insert: form item + binary file (processed by Data Loader, Text Splitter, Embeddings)<br>Tool: query string generated by the Agent | Insert: one item per stored chunk (text + metadata)<br>Tool: top 5 chunks with text + metadata, reranked in W1.b, returned to the Agent | File -> chunks -> 512-dim vectors -> index. Query -> vector -> nearest chunks |
| 12 | **Embeddings OpenAI**<br>`@n8n/n8n-nodes-langchain.embeddingsOpenAi` v1.2 | Model: default (not set in export)<br>Options: Dimensions = **512** (all four nodes), Batch Size, Strip New Lines, Timeout | Credential: OpenAI API | Sub-node that turns text into vectors | Text (chunks or the query) via `ai_embedding` | Arrays of 512 numbers | Text -> vector. Insert and query embeddings must use the same model and dimensions as the index |
| 13 | **Recursive Character Text Splitter**<br>`@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter` v1 | Chunk Size, Chunk Overlap (both left at default)<br>Options: none set | Node settings default | Sub-node that cuts long documents into smaller chunks | Document text via `ai_textSplitter` | Chunks of text | Splits by paragraph, then line, then word, until each chunk fits the chunk size |
| 14 | **Reranker Cohere**<br>`@n8n/n8n-nodes-langchain.rerankerCohere` v1 | No parameters set in export (defaults) | Credential: Cohere API | Sub-node that re-scores the retrieved chunks against the question and puts the most relevant first | Question + top 5 chunks via `ai_reranker` | Same chunks, reordered by relevance score | Order change only; this is the single difference in retrieval between W1.a and W1.b |
| 15 | **Form** (next page / ending)<br>`n8n-nodes-base.form` v1 | "Review draft": Define Form = Using JSON, Form Fields = `{{ $json.review_fields }}`; Options: Form Title "Review your draft", Button Label "Submit"<br>"Done": Operation = Completion, Respond With = Return Binary File, Completion Title, Completion Message (expression) | Needs a Form Trigger upstream (W4 "Brief"); execution waits for the user | Adds pages to a multi-step form; pauses the run until the user submits | "Review draft": `{ round, draft, quality, review_fields, ... }`<br>"Done": item with binary `.md` file | "Review draft": `{ "Decision": "Approve and save", "Final text": "...", "Feedback for a rewrite": "..." }`<br>"Done": completion page shown and file returned to the browser | Form built at runtime from JSON; human decision -> JSON fields for the If node |


## Variations of the same node across workflows

| Node | Variation |
|---|---|
| Form Trigger | File upload (W1) vs dropdowns + text (W4); v2.5 vs v2.2 |
| Chat Trigger | W1.b streams and greets; W1.a waits for the full answer, no greeting |
| Pinecone Vector Store | Same node in two modes: insert (ingest path) and retrieve-as-tool (chat path); reranker only in W1.b |
| If | Number comparison (W3) vs string equality on a human decision (W4) |
| HTTP Request | Plain GET returning text (W4 Fetch files) vs authenticated POST to OpenAI (W4 Write draft) |
| OpenAI | With built-in web search (W2) vs plain prompt with expressions (W3) |
| Edit Fields | JSON mode (whole payload) vs manual mapping (single fields) |



# Lab Proof: Extension Activities

## 1. Additional node analysis (W4)

The main reference table documents each node **type** once. This section goes one level deeper: every node **instance** in W4, in execution order, with its exact role in the data flow.

```
Brief -> Plan files -> Fetch files -> Build prompts -> Write draft (OpenAI) -> Check quality
      -> Review draft -> Approved? -> true:  Final post -> Make .md file -> Done
                                   -> false: Prepare rewrite -> Write draft (OpenAI)  (loop)
```

| # | Node (type) | Role in W4 | Key configuration | Items in -> out | Output fields |
|---|---|---|---|---|---|
| 1 | **Brief** (Form Trigger) | Collects the content brief | 3 required dropdowns (Channel, Product, Language) + required Topic; button "Generate draft" | 0 -> 1 | `Channel`, `Product`, `Language`, `Topic`, `submittedAt`, `formMode` |
| 2 | **Plan files** (Code, Python) | Maps form labels to app values and lists the 10 files to download | `REPO`, `BRANCH`, 7 knowledge base files + 3 templates; raises an error if channel, product or topic is missing | 1 -> 10 | `path`, `url`, `channel`, `product`, `language`, `topic` |
| 3 | **Fetch files** (HTTP Request) | Downloads each file from GitHub raw | GET `{{ $json.url }}`; Response Format = Text; no auth (public repo) | 10 -> 10 | `data` (raw markdown or template text) |
| 4 | **Build prompts** (Code, Python) | Splits the knowledge base at `##` headings, picks 4 blocks by rule (no RAG), fills the system and channel templates | Pairs downloads with `_('Plan files').all()`; raises an error if a file is missing, product facts are empty, a placeholder is unknown or the language is unsupported | 10 -> 1 | `system_prompt`, `user_prompt`, `banned_phrases`, `model`, `blocks` (+ brief fields) |
| 5 | **Write draft (OpenAI)** (HTTP Request) | Calls OpenAI Chat Completions directly | POST, predefined OpenAI credential, JSON body with model, temperature 0.7 (skipped for gpt-5 / o-series), system + user messages | 1 -> 1 | `choices[0].message.content`, `usage.prompt_tokens`, `usage.completion_tokens` |
| 6 | **Check quality** (Code, Python) | Deterministic quality gate, then builds the review form | Banned phrases, em dashes, markdown, emojis (max 2), hashtags (max 3), word range per channel; `_runIndex` counts rounds | 1 -> 1 | `round`, `draft`, `quality`, `problems`, `tokens_in`, `tokens_out`, `review_fields` |
| 7 | **Review draft** (Form, next page) | Human review step; execution waits | Form defined as JSON from `{{ $json.review_fields }}`: draft + quality (HTML), Decision dropdown, editable Final text, Feedback field | 1 -> 1 | `Decision`, `Final text`, `Feedback for a rewrite` |
| 8 | **Approved?** (If) | Routes on the human decision | `Decision` equals "Approve and save", strict, case sensitive | 1 -> 1 (true or false) | Unchanged |
| 9 | **Final post** (Code, Python) | Re-checks the (possibly edited) final text and builds the saved post | File name `{channel}_{product}_{lang}_{timestamp}.md`; front-matter audit header (model, quality, rounds, edited_by_marketer) | 1 -> 1 | `file_name`, `markdown`, `quality`, `message` |
| 10 | **Make .md file** (Convert to File) | Turns the markdown text into a file | Convert to Text File, source field `markdown`, file name from `file_name` | 1 -> 1 | Binary `data` (.md) |
| 11 | **Done** (Form, ending) | Shows the result and hands over the file | Completion, Return Binary File, message from `Final post` | 1 -> 0 | File download in the browser |
| 12 | **Prepare rewrite** (Code, Python) | Builds the rewrite prompt and loops back | Adds the current draft + feedback to the user prompt; if feedback is empty, uses the quality problems | 1 -> 1 | `model`, `system_prompt`, `user_prompt`, `feedback` |

---

## 2. Node combinations (common patterns)

| # | Pattern | Node chain | Used in | When to use | Watch out for |
|---|---|---|---|---|---|
| 1 | **Single-shot LLM call** | Manual Trigger -> OpenAI (Message a model) | W2 | One prompt, one answer, no data preparation | Expressions in prompts need the `=` prefix to be evaluated |
| 2 | **Rule-based routing** | Trigger -> Edit Fields -> If -> branch A / branch B | W3 | Deterministic decisions before spending on an LLM call | Strict type validation: numbers must arrive as numbers |
| 3 | **LLM only on the valuable branch** | If (true) -> Edit Fields -> OpenAI; If (false) -> Edit Fields (template reply) | W3 | Cost control: only high-priority leads get a generated reply | The cheap branch is easy to forget when testing |
| 4 | **RAG ingestion** | Form Trigger -> Pinecone (insert) + Default Data Loader + Text Splitter + Embeddings | W1.a, W1.b | Loading documents into a knowledge base | Embedding dimensions must match the index; re-uploads create duplicates |
| 5 | **RAG retrieval as a tool** | Chat Trigger -> AI Agent + Chat Model + Pinecone (retrieve as tool) + Query Embeddings | W1.a | Grounded Q&A over uploaded documents | Tool description drives when the Agent calls it; no memory by default |
| 6 | **RAG with reranking** | Pattern 5 + Reranker Cohere on the Pinecone tool | W1.b | When the top-K order matters more than recall | Extra API call and credential per question |
| 7 | **Fan-out / fan-in** | Code (1 -> N items) -> HTTP Request (runs per item) -> Code (N -> 1) | W4 | Fetching several files or calling an API per item | Item order must stay aligned when pairing results back |
| 8 | **Direct API call instead of an AI node** | Code (build body) -> HTTP Request (POST to OpenAI) -> Code (parse response) | W4 | Full control over the request and access to raw `usage` tokens | Credentials, model parameters and error handling are your job |
| 9 | **Deterministic quality gate** | HTTP Request (LLM) -> Code (rule checks) | W4 | Checking LLM output against hard rules before a human sees it | Rules live in code; keep them in one place |
| 10 | **Human in the loop with retry** | Form (review) -> If (approved?) -> false: Code (rewrite prompt) -> back to the LLM node | W4 | Approval before anything is saved or sent | Loop has no round limit; every round costs tokens |
| 11 | **File delivery** | Code (build content) -> Convert to File -> Form (ending, return binary) | W4 | Giving the user a downloadable result | Form ending only works after a Form Trigger |

---

## 3. Debugging guide - Method (any node)

1. Open the failed run in **Executions** and click the red node.
2. Compare the **Input** and **Output** panels: is the field missing, renamed, or of the wrong type?
3. Check the item count on the connection line between nodes.
4. Fix one node, then use **Execute step** on that node with **pinned data** upstream, so earlier nodes (and paid API calls) do not rerun.

