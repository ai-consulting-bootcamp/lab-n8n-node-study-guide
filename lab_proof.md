| Node | Parameters | Settings | What It Does | JSON Input | JSON Output | Key Transformations |
| Node | Parameters | Settings | What It Does | JSON Input | JSON Output | Key Transformations |
|---|---|---|---|---|---|---|
| Store in Pinecone | Pinecone credential; operation: `Insert Documents`; index: `lagerflow-faq`; batch size: `200`; Document and Embedding inputs required | Settings tab not inspected | Inserts the uploaded document chunks and their embeddings into the selected Pinecone index | One uploaded PDF: `LagerFlow_Product_FAQ.pdf`, `application/pdf`, 3,602 bytes; the node also receives document and embedding inputs from connected nodes | 3 items. Each contains `pageContent` and metadata, including PDF information and `loc.lines`; observed line ranges: 1–16, 17–30, and 31–39 | PDF text is split into 3 document chunks, with metadata and line locations, then inserted into `lagerflow-faq`. The embedding vectors are not visible in this output. |
| Upload Documents Form | Form title: `Upload Documents for RAG`; authentication: none; required file field: `documents`; accepted types: `.pdf`, `.csv`, `.json` | Settings tab not inspected | Receives a file from the user and starts the document-ingestion workflow | No previous node; the user submits a file through the test form | One item with `documents` file metadata: `LagerFlow_Product_FAQ.pdf`, `application/pdf`, 3,602 bytes; also includes `submittedAt` and `formMode: test` | Form submission → n8n item containing the uploaded file and its metadata |
| OpenAI Embeddings | Required: OpenAI credential and text input; model: `text-embedding-3-small` | Dimensions: `512`; other settings not inspected | Converts document text into numeric vectors for storage and search | One item containing the FAQ text chunks in `documents` | One item with numeric vector data under `response`; dimensions are set to `512` | Text chunks → numeric embedding vectors |
| Document Loader | Required: binary file input; Type of Data: `Binary`; Mode: `Load All Input Data`; Data Format: `Automatically Detect by Mime Type`; Text Splitting: `Custom` | Options: none; Settings tab not inspected | Reads the uploaded PDF and extracts its text and metadata | One binary file: `LagerFlow_Product_FAQ.pdf`, `application/pdf`, 3,602 bytes | One item containing `response[0].pageContent` and `response[0].metadata`; metadata includes PDF details | Binary PDF → extracted text and document metadata |
| Text Splitter | Required: text input; Chunk Size: `1000`; Chunk Overlap: `0` | Options: none; Settings tab not inspected | Splits the extracted document text into smaller chunks for embedding and retrieval | One item containing the full extracted FAQ text in `textSplitter` | One item with 3 text chunks in `response` | Full document text → 3 smaller text chunks |
| OpenAI Chat Model | Required: OpenAI credential and model; selected model: `gpt-5.4-mini` | Responses API: on; built-in tools: none; options: none; Settings tab not inspected | Generates text when called by the RAG Agent | No direct input shown; receives the agent's request when invoked | No direct output shown here; returns generated text to the RAG Agent | Agent request and retrieved context → generated text for the agent |
| Retrieve from Pinecone | Required: Pinecone credential, index, and Embedding input; operation: `Retrieve Documents (As Tool for AI Agent)`; index: `lagerflow-faq`; limit: `5` | Include Metadata: on; Rerank Results: off; options: none; Settings tab not inspected | Searches Pinecone for document chunks relevant to the user's question and provides them to the RAG Agent | The agent's question, converted to an embedding by Query Embeddings; no input data is shown in this panel | No output is shown in this panel; during a successful chat run, it returns relevant document chunks and metadata | Embedded question → relevant chunks from Pinecone |
| If | Condition: `{{ $json.company_size }}` is greater than or equal to `50`; type conversion: on | Settings tab not inspected | Checks the company size and sends the item to the True or False branch | One item from `Edit Fields`: `name: Lena`, `company: ABC GmbH`, `company_size: 10`, `industry: logistics`, `job_title: Head of Operations`, and a message requesting a solution before January | One item in the `False Branch`; it contains the same input fields, including `company_size: 10` | Since `10` is less than `50`, the item was sent to the False branch. |
| Edit Fields2 | Mode: Manual Mapping; sets `Priority` to `normal`; sets `reply` to a message using `{{ $json.name }}` | Include Other Input Fields: on; Input Fields to Include: All; Settings tab not inspected | Adds a priority and a personalized reply while keeping the original input fields | One item from the `If` node’s False Branch, including `name: Lena`, `company: ABC GmbH`, and `company_size: 10` | One item with all original fields plus `Priority: normal` and a personalized `reply` addressed to Lena | Adds the `Priority` and `reply` fields; keeps the incoming fields unchanged. |
| Message a Model | Resource: Text; operation: Message a Model; model: GPT-5.4-MINI; messages include System and User roles | Settings tab not inspected | Sends the messages to the selected model and returns a generated response | One empty JSON item from the Manual Trigger; the prompt uses today’s date and asks for recent news based on the user’s category | One item with a completed message response, generated text, and URL citation annotations | Combines the date and prompt instructions, sends them to the model, and returns text with source citations. |


## 2. Execution Trace

The `If` node checked whether `company_size` was greater than or equal to `50`. Lena’s company size was `10`, so the item went to the False Branch. `Edit Fields2` kept the original fields and added `Priority: normal` and a personalized reply.

## 3. Input Payload and Output Record

### Input Payload

```json
{
  "name": "Lena",
  "email": "lena@example.com",
  "company": "ABC GmbH",
  "company_size": 10,
  "industry": "logistics",
  "job_title": "Head of Operations",
  "message": "We're moving our warehouses to a new system in January and need a solution before then."
}
```

### Output Record

```json
{
  "name": "Lena",
  "email": "lena@example.com",
  "company": "ABC GmbH",
  "company_size": 10,
  "industry": "logistics",
  "job_title": "Head of Operations",
  "message": "We're moving our warehouses to a new system in January and need a solution before then.",
  "Priority": "normal",
  "reply": "Hi Lena, thank you for your interest in our software! Here is our price list and a short product video: [link]. If you'd like a demo, just reply to this email."
}
```