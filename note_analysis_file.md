# n8n Node Study Guide – Lab Proof

## 1. Workflows studied
- Workflow 1: PDF RAG – Part 1 (store PDF in Pinecone)
- Workflow 1: PDF RAG – Part 2 (chat with the PDF)
- Workflow 2: AI agent chat
- Workflow 3: (my choice)

## 2. Node notes

### Node: Upload Documents Form
- Parameters: 
Form URL: Test URL / Production URL
Authentication: None
Form Title: "Upload Documents for RAG"
Form Element: File upload, label "Upload Files", field name "documents", accepts .pdf, .csv, .json
Respond When: Form Is Submitted
- Settings: 
All default (Always Output Data off, Execute Once off,
Retry On Fail off, On Error: Stop Workflow).
Node: n8n Form Trigger, version 2.5
- What it does: It shows a web form where I upload a PDF. When I submit the form,
the workflow starts. It is the trigger (the starting point).
- Input: Nothing from another node, because it is the first node.
The input is the file I upload in the form.
- Output:
1 item with two parts:
Binary: the PDF file itself (LagerFlow_Product_FAQ.pdf, 3.6 kB)
JSON: information about the file (filename, mimetype, size)
plus the time I submitted (submittedAt) and formMode "test"
- What changed: The PDF I uploaded from outside n8n became n8n data: 1 item with the file stored as binary, plus JSON with the file info and submit time.
- Screenshots: (config / input / output)

### Node: Document Loader
- Parameters: 
Type of Data: Binary (reads the uploaded file)
Mode: Load All Input Data
Data Format: Automatically Detect by Mime Type (detects PDF)
Text Splitting: Custom (uses the connected Text Splitter node)
Options: none
- Settings:
All default (Always Output Data off, Execute Once off, Retry On Fail off, On Error: Stop Workflow).
Node: Default Data Loader, version 1.1
- What it does:
It takes the PDF file from the form and pulls out the text, so the text can be split into chunks and stored.
- Input: The PDF file (binary) from the Upload Documents Form.
- Output:
A list of text chunks. Each chunk has:
  - pageContent: a piece of the PDF text
  - metadata: source (blob), file type (application/pdf),
    PDF info (title "LagerFlow Product FAQ", version, author)
- What changed:
The binary PDF file became readable text, split into chunks, with metadata attached to each chunk.
- Screenshots: attached

### Node: Text Splitter
- Parameters: 
  Chunk Size: 1000 (max characters per chunk)
  - Chunk Overlap: 0
  - Options: none
- Settings: All default.
  Node: Recursive Character Text Splitter, version 1
- What it does: Cuts the long PDF text into smaller pieces (chunks), so they can be searched better.
- Input: The full text from the PDF as one long piece.
- Output: A list of 3 text chunks, each up to 1000 characters.
- What changed: One long text became 3 shorter chunks.
- Screenshots: Attached
- Risk: Overlap is 0, so a question and its answer can be split into different chunks (e g. "How long does setup take?" is in chunk 1, the answer is in chunk 2).

### Node: OpenAI Embeddings
- Parameters: 
  - Credential: OpenAi account
  - Model: text-embedding-3-small
  - Dimensions: 512
- Settings: All default.
  Node: Embeddings OpenAI, version 1.2
- What it does: Turns each text chunk into a list of numbers (a vector) that represents its meaning.
- Input: The 3 text chunks from the Text Splitter (documents[0], documents[1], documents[2]).
- Output: 3 vectors, each a list of 512 numbers.
- What changed: Text became numbers (vectors), so the meaning can be compared and searched.
- Risk: Pinecone index and Query Embeddings (Part 2) must use the same model and 512 dimensions, or the search won't work.
- Screenshots: attached

### Node: Store in Pinecone
- Parameters:
  - Credential: PineconeApi account
  - Operation Mode: Insert Documents
  - Pinecone Index: lagerflow-faq
  - Embedding Batch Size: 200
  - Options: none
  - Connected sub-nodes: OpenAI Embeddings, Document Loader
- What it does: Saves the text chunks and their vectors in the
  Pinecone index, so they can be searched later.
- Input: 1 item, the PDF file (binary) from the Upload Documents Form.
- Output: 3 items (one per stored chunk), each with metadata
  (source, PDF info, lines from/to) and pageContent (the text).
- What changed: 1 PDF became 3 stored chunks in Pinecone.
  The vectors are stored in Pinecone, not shown in the output.
- Risk: Insert always adds. Uploading the same PDF again
  creates duplicate chunks.
- Settings: All default.
  Node: Pinecone Vector Store, version 1.3

## 4. Proof of one run
- Input payload: chat question "How long does setup take?"
- Output record: "A normal setup takes 6 to 8 weeks. If the project has more than 3 warehouses, it takes 10 to 12 weeks.
  Source used: LagerFlow Product FAQ."
- Screenshot: attached

### Node: When chat message received
- Parameters:
  - Chat URL: (webhook URL)
  - Make Chat Publicly Available: on
  - Mode: Hosted Chat
  - Authentication: None
  - Initial Message: "Hi there! My name is Nathan. How can I assist you today?"
  - Make Available in n8n Chat Hub: off
- What it does: Opens a chat page. Each message the user sends
  starts the workflow. It is the trigger of Part 2.
- Input: Nothing from another node. The input is the message
  the user types in the chat.
- Output: 1 item with action ("sendMessage"), sessionId
  (ID of the conversation), and chatInput (the question).
- What changed: The typed chat message became n8n JSON data.
- Risk: Public and no authentication, so anyone with the link can use the chat and spend OpenAI credits.
- Settings: All default.
  Node: Chat Trigger, version 1.4

### Node: RAG Agent
- Parameters:
  - Source for Prompt: Connected Chat Trigger Node
  - Prompt: {{ $json.chatInput }} (takes the question from the input)
  - Require Specific Output Format: off
  - Enable Fallback Model: off
  - System Message: answer ONLY from retrieved documents; if not
    found, say "I couldn't find that in the uploaded documents";
    always cite the source
  - Enable Streaming: on
  - Connected: Chat Model (OpenAI), Tool (Retrieve from Pinecone),
    Memory: none
- What it does: Reads the question, uses the Pinecone tool to find
  matching chunks, and asks the chat model to write an answer.
- Input: action, sessionId, chatInput ("How long does setup take?")
- Output: output (the final answer text, in markdown)
- What changed: A question became an answer based on the PDF.
- Risks: No memory, so it forgets earlier messages.
  No fallback model, so if OpenAI fails the chat fails.

## Execution trace (RAG Agent Logs)
1. OpenAI Chat Model (1st call): gets system message + question,
   decides to use the Pinecone tool. (2705 ms, ~62 tokens)
2. Retrieve from Pinecone: searches the index
   - Query Embeddings: turns the question into a vector
3. OpenAI Chat Model (2nd call): gets the question + found chunks,
   writes the final answer.
Screenshot: agent logs attached

### Node: OpenAI Chat Model
- Parameters:
  - Credential: OpenAi account
  - Model: gpt-5.4-mini
  - Use Responses API: on
  - Built-in Tools: none
  - Options: none (defaults)
- What it does: The LLM that the RAG Agent uses to decide what to do
  and to write the final answer. It ran 2 times in one chat message.
- Input (run 2): messages = system message + question + tool call
  + chunks found in Pinecone (~2590 tokens)
- Output (run 2): text = final answer, plus token usage
  (2590 prompt + 45 completion = 2635 total)
- What changed: Question + retrieved chunks became a written answer.
- Note: Run 1 decided to call the Pinecone tool and rewrote the
  search query; run 2 wrote the answer.
- Settings: All default.
  Node: OpenAI Chat Model, version 1.3

### Node: Retrieve from Pinecone
- Parameters:
  - Credential: PineconeApi account
  - Operation Mode: Retrieve Documents (As Tool for AI Agent)
  - Description: tells the agent to use it for questions
    about uploaded documents
  - Pinecone Index: lagerflow-faq (same as Part 1)
  - Limit: 5
  - Include Metadata: on
  - Rerank Results: off (no Cohere reranking)
- What it does: Searches Pinecone for the chunks most similar
  to the question and gives them to the agent.
- Input: input = search query written by the AI
  ("How long does setup take? Find in uploaded documents...")
- Output: list of matching chunks with text and metadata.
  First result: the chunk with "6 to 8 weeks" (lines 17-30).
- What changed: A search query became a list of relevant chunks.
- Risks: Limit 5 but only 3 chunks exist, so all are returned.
  Rerank is off, so ranking may be worse with bigger documents.
- Settings: All default.
  Node: Pinecone Vector Store, version 1.3
- Same node type as "Store in Pinecone" (Part 1), but the mode is
  Retrieve as Tool instead of Insert Documents.

### Node: Query Embeddings
- Parameters:
  - Credential: OpenAi account
  - Model: text-embedding-3-small
  - Dimensions: 512
- What it does: Turns the search question into a vector, so Pinecone
  can compare it with the stored chunk vectors.
- Input: query = the search question written by the AI
- Output: 1 vector (list of 512 numbers)
- What changed: The question text became numbers.
- Check: Same model and dimensions as OpenAI Embeddings in Part 1
  (text-embedding-3-small, 512). This must match, or the search fails.
- Same node type as "OpenAI Embeddings" (Part 1): there it embedded
  3 chunks, here it embeds 1 question.
- Settings: All default.
  Node: Embeddings OpenAI, version 1.2

### Node: Simple Memory
- Parameters:
  - Session ID: Connected Chat Trigger Node
  - Session Key: {{ $json.sessionId }} (one memory per conversation)
  - Context Window Length: 5 (last 5 interactions are remembered)
- What it does: Stores the chat history, so the AI Agent can
  remember earlier messages in the same conversation.
- Input (run 2): action "saveContext", input "what is my name?",
  output "Your name is Barsha."
- Output: chatHistory = list of messages, each labeled
  HumanMessage or AIMessage, in order.
- What changed: A single question and answer were added to
  the saved conversation history.
- Risks: Memory is stored locally in n8n (not permanent, not shared
  across servers). Only the last 5 interactions are kept.
- Settings: All default.
  Node: Simple Memory, version 1.3

## Workflow 2: AI agent chat (built by me)
Nodes: When chat message received → AI Agent
       + OpenAI Chat Model + Simple Memory

Differences from the RAG workflow:
- Chat Trigger: Make Chat Publicly Available is OFF (safer).
- OpenAI Chat Model: same model (gpt-5.4-mini), same credential.
- AI Agent: has Simple Memory connected, but no tool (no Pinecone).
  So it remembers the conversation but cannot look up documents.
- RAG agent: has the Pinecone tool, but no memory.
  So it can look up documents but forgets earlier messages.

Test: "Hi, my name is Barsha" → "What is my name?" →
"Your name is Barsha." (memory works)
Screenshot: (images/agent_chat_memory_test.png)

- AI Agent: no System Message (Options empty), so no special rules.
  The RAG agent has a system message that limits answers to the
  documents and asks it to cite the source.
- Same prompt ({{ $json.chatInput }}) and same output field (output).

## Workflow 3: Joke workflow (built by me)
Manual Trigger → HTTP Request → Edit Fields

### Node: Manual Trigger (When clicking 'Execute workflow')
- Parameters: none
- What it does: Starts the workflow when I click "Execute workflow".
- Input: none
- Output: an empty item (just the "start" signal)
- What changed: nothing, it only starts the flow
- Settings: All default.
  Node: Manual Trigger, version 1

### Node: HTTP Request
- Parameters:
  - Method: GET
  - URL: https://official-joke-api.appspot.com/random_joke
  - Authentication: None
  - Send Query Parameters / Headers / Body: off
- What it does: Calls a public API and gets a random joke.
- Input: nothing (the trigger sends no data)
- Output: type, setup, punchline, id
- What changed: The API response became n8n JSON data.
- Risk: If the API is down or changes its fields, the workflow breaks.
- Settings: All default.
  Node: HTTP Request, version 4.4

### Node: Edit Fields (Set)
- Parameters:
  - Mode: Manual Mapping
  - question = {{ $json.setup }}
  - answer = {{ $json.punchline }}
  - Include Other Input Fields: off
- What it does: Keeps only the fields I need and renames them.
- Input: type, setup, punchline, id
- Output: question, answer
- What changed: 4 fields became 2, with clearer names;
  type and id were removed.
- Settings: All default.
  Node: Edit Fields (Set), version 3.4

# n8n Node Reference Table

| Node | Parameters | Settings | What It Does | JSON Input | JSON Output | Key Transformations |
|------|------------|----------|--------------|------------|-------------|---------------------|
| n8n Form Trigger (Upload Documents Form) | Form URL (Test/Production), Authentication: None, Form Title, Form Element: File "documents" (.pdf, .csv, .json), Respond When: Form Is Submitted | Default (On Error: Stop Workflow), v2.5 | Shows an upload form and starts the workflow | None (first node) | 1 item: JSON (filename, mimetype, size, submittedAt, formMode) + binary PDF | Uploaded file → n8n item with binary data |
| Default Data Loader | Type of Data: Binary, Mode: Load All Input Data, Data Format: Auto-detect by Mime Type, Text Splitting: Custom | Default, v1.1 | Reads the PDF and extracts its text | Binary PDF from the form | List of chunks: pageContent + metadata (source, blobType, PDF info) | Binary PDF → text with metadata |
| Recursive Character Text Splitter | Chunk Size: 1000, Chunk Overlap: 0 | Default, v1 | Cuts long text into smaller chunks | Full PDF text | 3 text chunks | 1 long text → 3 chunks |
| Embeddings OpenAI (used 2x) | Credential: OpenAi account, Model: text-embedding-3-small, Dimensions: 512 | Default, v1.2 | Turns text into vectors (numbers that represent meaning) | Part 1: 3 chunks. Part 2: 1 search query | Part 1: 3 vectors. Part 2: 1 vector (512 numbers each) | Text → vectors |
| Pinecone Vector Store (used 2x) | Credential: PineconeApi account, Index: lagerflow-faq. Store: Insert Documents, Batch Size 200. Retrieve: As Tool for AI Agent, Limit 5, Include Metadata on, Rerank off | Default, v1.3 | Stores chunks + vectors, or searches them | Store: binary PDF. Retrieve: search query from the AI | Store: 3 items (metadata + pageContent). Retrieve: matching chunks with metadata | Store: chunks → saved in Pinecone. Retrieve: query → relevant chunks |
| Chat Trigger (used 2x) | Mode: Hosted Chat, Authentication: None, Public: on (RAG) / off (agent chat), Initial Message (RAG only) | Default, v1.4 | Opens a chat and starts the workflow on each message | None (first node) | action, sessionId, chatInput | Typed message → n8n JSON |
| AI Agent (used 2x) | Prompt Source: Connected Chat Trigger, Prompt: {{ $json.chatInput }}, Output Format: off, Fallback Model: off, System Message (RAG only), Streaming on (RAG) | Default, v3.1 | Decides what to do, uses tools/memory, returns an answer | action, sessionId, chatInput | output (answer text) | Question → answer |
| OpenAI Chat Model (used 2x) | Credential: OpenAi account, Model: gpt-5.4-mini, Use Responses API: on | Default, v1.3 | The LLM that reasons and writes the answer | messages (system + question + tool results) | text + token usage | Prompt + context → generated text |
| Simple Memory | Session ID: Connected Chat Trigger, Session Key: {{ $json.sessionId }}, Context Window Length: 5 | Default, v1.3 | Remembers earlier messages in the same chat | action: saveContext, input, output | chatHistory (HumanMessage / AIMessage list) | New exchange → added to chat history |
| Manual Trigger | None | Default, v1 | Starts the workflow on button click | None | Empty item (start signal) | None, only starts the flow |
| HTTP Request | Method: GET, URL: official-joke-api random_joke, Authentication: None, Query/Headers/Body: off | Default, v4.4 | Calls an external API | Empty item from trigger | type, setup, punchline, id | API response → n8n JSON |
| Edit Fields (Set) | Mode: Manual Mapping, question = {{ $json.setup }}, answer = {{ $json.punchline }}, Include Other Input Fields: off | Default, v3.4 | Keeps, renames and creates fields | type, setup, punchline, id | question, answer | 4 fields → 2 renamed fields |                 |

## 4. Proof of one run
- Workflow export: (attach the .json file or paste it)
- Input payload: (e.g. the form JSON you just saw)
- Execution trace: (screenshot of the execution with green checks)
- Output record: (e.g. the Pinecone output, or the chat answer)

## 5. Risks and observations
-