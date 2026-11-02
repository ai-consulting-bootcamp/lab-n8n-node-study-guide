# n8n Node Reference Table

## Workflow 1: PDF-Based RAG — Document Ingestion

**Source n8n Workflow:** RAG Chatbot (with reranker)

### Node 1: Upload Documents Form

**Node Type:** n8n Form Trigger (v2.5)  
**Category:** Trigger / Input  
**Execution Status:** Successful  
**Output Items:** 1

#### 1. Purpose

The "Upload Documents Form" node is the entry point for the document ingestion pipeline.

It provides a web form where users can upload PDF, CSV, or JSON files. Submitting the form triggers the n8n workflow and makes the uploaded document available for downstream processing.

The node does not extract text, generate embeddings, or store documents in Pinecone. These operations are handled by subsequent nodes.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Form URLs | Test URL / Production URL | Separate endpoints for testing and production |
| Authentication | None | No authentication configured |
| Form Title | Upload Documents for RAG | Title displayed in the form |
| Form Description | Upload PDF, CSV, or JSON files to add to the knowledge base | Instructions displayed to users |
| Form Element Label | Upload Files | Label of the upload field |
| Element Type | File | Enables file uploads |
| Custom Field Name | documents | Internal name of the uploaded file field |
| Accepted File Types | .pdf, .csv, .json | Accepted file extensions |

#### 3. Settings

| Setting | Configured Value |
|---|---|
| Always Output Data | Off |
| Execute Once | Off |
| Retry On Fail | Off |
| On Error | Stop Workflow |
| Notes | Empty |
| Display Note in Flow | Off |
| Node Version | 2.5 |

The node uses the default error-handling behavior. Automatic retries are disabled, and unhandled node errors stop the workflow execution.

#### 4. Input Data

As a trigger node, the Form Trigger does not receive input from another n8n node.

Instead, it receives an external form submission containing an uploaded file.

**Test Input:**
- File: `LagerFlow_Product_FAQ.pdf`
- File Type: PDF
- File Size: 3,602 bytes
- Submission Mode: Test

#### 5. JSON Output

The successful execution produced one item with the following JSON structure:

```json
[
  {
    "documents": [
      {
        "filename": "LagerFlow_Product_FAQ.pdf",
        "mimetype": "application/pdf",
        "size": 3602
      }
    ],
    "submittedAt": "2026-11-02T17:34:35.332+01:00",
    "formMode": "test"
  }
]
```

**Output Fields:**

| Field | Description |
|---|---|
| documents | Array containing uploaded file metadata |
| filename | Original filename |
| mimetype | MIME type of the uploaded file |
| size | File size in bytes |
| submittedAt | Timestamp of the form submission |
| formMode | Indicates whether the submission was made in test or production mode |

#### 6. Binary Output

The node also provides the uploaded PDF as binary data.

| Property | Value |
|---|---|
| Binary Field | documents |
| File Name | LagerFlow_Product_FAQ.pdf |
| File Extension | pdf |
| MIME Type | application/pdf |
| File Size | 3.6 kB |

The binary data contains the actual uploaded document, while the JSON output provides metadata about the submission.

#### 7. Key Transformations

The node transforms an external form submission into n8n-compatible workflow data.

**Data Flow:**

`User uploads PDF → Form Trigger → JSON metadata + Binary file → Store in Pinecone`

Key observations:

- The uploaded document is made available as binary data.
- File metadata is provided in structured JSON format.
- A submission timestamp and form mode are added to the output.
- No text extraction, chunking, or embedding generation occurs within this node.
- The output is passed to the next stage of the RAG ingestion pipeline.

#### 8. Execution Evidence

A test execution was completed successfully using `LagerFlow_Product_FAQ.pdf`.

**Observed Results:**
- Execution successful
- One output item generated
- JSON metadata available
- PDF binary data available
- Test submission confirmed

**Evidence:**
- Form Trigger Parameters and Settings screenshots captured during the lab.
- Successful form submission and JSON/Binary output observed.
- Workflow configuration available in the n8n JSON export.

*Note: Screenshot paths are placeholders and should be updated to match the actual repository structure.*

#### 9. Operational Risks

The form currently has no authentication configured. If the production URL is publicly accessible, unauthorized users could potentially submit documents.

Additional considerations include file size limits, input validation, and preventing untrusted documents from being added to the knowledge base.

#### 10. Conclusion

The Form Trigger successfully receives uploaded documents and converts the form submission into structured JSON metadata and binary file data.

The test confirms that the document is available for subsequent processing in the RAG ingestion pipeline. It does not yet prove that text extraction, embedding generation, or Pinecone storage completed successfully.

---

### Node 2: Store in Pinecone

**Node Type:** Pinecone Vector Store  
**Category:** Vector Database / Storage  
**Execution Status:** Execution output provided; database persistence not independently verified  
**Target Index:** `lagerflow-faq`

#### 1. Purpose

The "Store in Pinecone" node manages document ingestion into the Pinecone vector database. It works with connected sub-nodes to load documents, split their content into chunks, generate embeddings, and store the resulting vectors for semantic retrieval.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Credential | PineconeApi account 3 | Pinecone API connection |
| Operation Mode | Insert Documents | Inserts embedded documents into the vector store |
| Pinecone Index | lagerflow-faq | Target index configured for the lab |
| Embedding Batch Size | 200 | Batch size used during embedding processing |
| Options | None | No additional options configured |

#### 3. Settings

No custom settings were reported for this node. Default behavior is retained.

#### 4. Input Data

The parent node receives the uploaded PDF through the "Upload Documents Form" trigger.

Connected sub-nodes provide the document loading, text splitting, and embedding functionality.

**Test document:** `LagerFlow_Product_FAQ.pdf`

#### 5. JSON Output

The provided execution output includes processed document content and metadata.

Observed fields include:

- `pageContent`
- `metadata.source`
- `metadata.blobType`
- `metadata.pdf`
- `metadata.loc.lines`

The complete execution response was not captured in the provided excerpt.

#### 6. Binary Output

The uploaded PDF enters the ingestion pipeline as binary data under the property `documents`.

The Pinecone storage operation is designed to persist vectorized document content, not the original PDF file as a binary attachment.

#### 7. Key Transformations

`Uploaded PDF → Document Loader → Text Splitter → OpenAI Embeddings → Pinecone Vector Store`

The pipeline converts a source document into text chunks and embedding vectors suitable for semantic search.

#### 8. Execution Evidence

The provided execution excerpt contains extracted PDF content and metadata, indicating that document processing occurred.

The configured target index is `lagerflow-faq`.

Successful persistence in Pinecone should be verified through the node's execution status or the Pinecone index records.

**Screenshot reference:** Store in Pinecone parameters and execution output.

#### 9. Operational Risks

- Incorrect index selection can lead to missing retrieval results.
- Embedding dimensions must match the Pinecone index configuration.
- Repeated insertion may create duplicate document entries.
- API or credential failures can interrupt ingestion.

#### 10. Conclusion

The Pinecone node is configured for document insertion into `lagerflow-faq` using the connected document-processing and embedding sub-nodes. The execution excerpt demonstrates processed document data, while successful database storage requires separate confirmation.

---

### Node 3: OpenAI Embeddings

**Node Type:** Embeddings OpenAI  
**Category:** AI / Embeddings  
**Execution Status:** Used as a sub-node of the ingestion pipeline

#### 1. Purpose

The "OpenAI Embeddings" node converts text chunks into numerical vector representations. These vectors enable similarity-based retrieval in Pinecone.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Credential | OpenAI Acc IR | OpenAI API connection |
| Model | text-embedding-3-small | Model used to generate embeddings |
| Dimensions | 512 | Number of dimensions per output vector |
| Additional Options | None | No further options configured |

#### 3. Settings

No custom settings were recorded for this node.

#### 4. Input Data

The embedding model processes text chunks provided through the connected document ingestion pipeline.

The source is the uploaded PDF `LagerFlow_Product_FAQ.pdf`.

#### 5. JSON Output

No standalone JSON output was captured.

The node generates embedding vectors that are consumed internally by the Pinecone Vector Store.

#### 6. Binary Output

None expected. The output consists of numerical vectors rather than binary files.

#### 7. Key Transformations

`Text Chunk → OpenAI Embedding Model → 512-Dimensional Vector`

The resulting vectors represent document content numerically for semantic similarity search.

#### 8. Execution Evidence

The node was configured with `text-embedding-3-small` and 512 dimensions.

The lab index `lagerflow-faq` was created with a matching vector dimension of 512.

A standalone embedding vector was not captured.

#### 9. Operational Risks

- Embedding dimensionality must match the vector database index.
- API requests can incur costs and be subject to rate limits.
- Different embedding models or configurations may produce incompatible vector representations.

#### 10. Conclusion

The node provides 512-dimensional embeddings for the RAG ingestion process. Its dimensional configuration matches the lab's Pinecone index.

---

### Node 4: Document Loader

**Node Type:** Default Data Loader  
**Category:** Document Processing  
**Execution Status:** Processed document content observed

#### 1. Purpose

The "Document Loader" node reads uploaded binary documents and extracts their content for processing by the RAG pipeline.

It uses MIME-type detection to identify the document format and delegates chunking to a connected custom text splitter.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Type of Data | Binary | Reads binary input files |
| Mode | Load All Input Data | Processes available input data |
| Data Format | Automatically Detect by Mime Type | Determines document format from MIME type |
| Text Splitting | Custom | Uses an external connected text splitter |
| Options | None | No additional options |

#### 3. Settings

| Setting | Configured Value |
|---|---|
| Always Output Data | Off |
| Execute Once | Off |
| Retry On Fail | Off |
| On Error | Stop Workflow |
| Notes | Empty |
| Display Note in Flow | Off |

#### 4. Input Data

The loader receives the uploaded file from the Form Trigger.

**Input Document:**

- Filename: `LagerFlow_Product_FAQ.pdf`
- MIME Type: `application/pdf`
- Binary Property: `documents`
- File Size: Approximately 3.6 kB

#### 5. JSON Output

The execution excerpt contains processed document data with fields such as:

```json
{
  "pageContent": "Monday to Saturday, 7:00 to 20:00. Enterprise: 24/7 phone support ...",
  "metadata": {
    "source": "blob",
    "blobType": "application/pdf",
    "pdf": {
      "totalPages": 1
    },
    "loc": {
      "lines": {
        "from": 31,
        "to": 39
      }
    }
  }
}
```

This is a shortened representation of the observed output. Additional PDF metadata fields were present.

#### 6. Binary Output

The input PDF is binary data. The loader transforms its contents into text documents with metadata rather than returning an unchanged binary attachment.

#### 7. Key Transformations

`PDF Binary Data → PDF Text Extraction → Text Document + Metadata`

The resulting document can then be divided into chunks and converted into embeddings.

#### 8. Execution Evidence

The provided output confirms:

- Extraction of readable FAQ text
- Identification of the PDF MIME type
- Recognition of one source page
- Preservation of source metadata
- Line-range information in the processed document

#### 9. Operational Risks

- Scanned PDFs may require OCR before usable text can be extracted.
- Invalid or unsupported documents can fail during parsing.
- Complex PDF layouts may produce imperfect text ordering.
- Missing metadata may reduce traceability.

#### 10. Conclusion

The Document Loader converts the uploaded PDF into structured text content and metadata, preparing it for chunking and embedding generation.

---

### Node 5: Text Splitter

**Node Type:** Recursive Character Text Splitter (v1)  
**Category:** Text Processing / Chunking  
**Execution Status:** Chunk-related metadata observed in the ingestion output

#### 1. Purpose

The "Text Splitter" node divides extracted document text into smaller chunks.

This supports efficient embedding generation and improves the granularity of subsequent document retrieval.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Chunk Size | 1000 | Target maximum chunk size in characters |
| Chunk Overlap | 0 | No intentional character overlap between adjacent chunks |
| Options | None | No additional options configured |

#### 3. Settings

| Setting | Configured Value |
|---|---|
| Always Output Data | Off |
| Execute Once | Off |
| Retry On Fail | Off |
| On Error | Stop Workflow |
| Notes | Empty |
| Display Note in Flow | Off |

#### 4. Input Data

The splitter operates on text extracted from `LagerFlow_Product_FAQ.pdf` by the Document Loader.

#### 5. JSON Output

The execution excerpt includes a processed text section with a `pageContent` field and metadata identifying the source line range.

Observed line range:

```json
{
  "loc": {
    "lines": {
      "from": 31,
      "to": 39
    }
  }
}
```

The exact total number of generated chunks was not established from the provided excerpt.

#### 6. Binary Output

None expected. The splitter processes and returns text documents rather than binary files.

#### 7. Key Transformations

`Extracted Document Text → Recursive Splitting → Smaller Text Chunks`

The splitter attempts to preserve natural text boundaries while staying within the configured chunk size.

With `Chunk Overlap = 0`, neighboring chunks do not intentionally repeat content.

#### 8. Execution Evidence

The provided output contains text and associated line-range metadata consistent with processed document chunks.

Configured values were verified through the node's Parameters and Settings screenshots.

#### 9. Operational Risks

- Chunks may split related information across boundaries.
- Zero overlap can cause loss of context between neighboring chunks.
- Oversized or undersized chunks can negatively affect retrieval quality.
- The appropriate chunk size depends on document structure and use case.

#### 10. Conclusion

The Text Splitter is configured to create chunks with a target size of 1000 characters and no overlap. It prepares extracted document content for embedding generation and vector storage.

---

## Workflow 2: AI Agent Chat — Document Question Answering

**Source n8n Workflow:** RAG Chatbot (with reranker)

### Node 6: Chat Interface

**Node Type:** When Chat Message Received / Chat Trigger (v1.4)  
**Category:** Trigger / User Interaction  
**Execution Status:** Successful chat response observed
**Output Items:** Not yet observed

#### 1. Purpose

The "Chat Interface" node provides the user-facing entry point for the RAG chatbot.

It receives messages submitted through the n8n chat interface and starts the conversational workflow. The user's question is forwarded to the RAG Agent for processing.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Public | true | Makes the chat interface publicly accessible when deployed |
| Initial Messages | Hello! I can answer questions about your uploaded documents. What would you like to know? | Welcome message displayed to the user |
| Response Mode | Streaming | Allows responses to be delivered incrementally |
| Webhook ID | Configured | Unique identifier for the chat trigger endpoint |

#### 3. Settings

No node-specific settings overrides are included in the exported JSON. The effective values of the standard Settings tab were not independently captured.

#### 4. Input Data

The node receives an external chat message rather than data from an upstream n8n node.

An example input would be a user asking which languages LagerFlow supports.

#### 5. JSON Output

No actual JSON output was provided.

The expected output contains the incoming chat message and may include session-related information used to identify the conversation. The exact field structure must be confirmed through execution.

#### 6. Binary Output

No binary output is expected for ordinary text-based chat messages.

#### 7. Key Transformations

`User Chat Message → Chat Trigger → RAG Agent`

The node transforms an external user interaction into workflow input. It does not perform document retrieval or generate the final answer itself.

#### 8. Execution Evidence

The exported workflow confirms a connected chat trigger with a public chat interface and streaming response mode.

A successful chat test is documented in the Workflow 2 Execution Evidence section.

**Screenshot reference:** Chat Interface configuration and chat execution.

#### 9. Operational Risks

- A publicly accessible chat endpoint may be exposed to unauthorized or excessive use.
- Unexpected user inputs require appropriate downstream handling.
- Streaming responses depend on compatible downstream node configuration.
- The export does not establish whether rate limiting or other protections are in place.

#### 10. Conclusion

The Chat Interface serves as the conversational entry point of the RAG workflow. It accepts user questions and forwards them to the connected AI agent.

---

### Node 7: RAG Agent

**Node Type:** AI Agent (v3.1)  
**Category:** AI / Agent Orchestration  
**Execution Status:** Successful agent-generated chat response observed

#### 1. Purpose

The "RAG Agent" orchestrates the document-based question-answering process.

It receives user messages, uses an OpenAI chat model for reasoning and response generation, and can call a Pinecone retrieval tool to obtain relevant document context.

The agent is instructed to answer only from retrieved documents and to cite the sources it uses.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| System Message | Custom document-grounding instructions | Defines the agent's behavior |
| Enable Streaming | true | Enables incremental answer delivery |
| Language Model Connection | OpenAI Chat Model | Provides the model used by the agent |
| Tool Connection | Retrieve from Pinecone | Provides access to document retrieval |

**System Message:**

> You are a helpful assistant that answers questions based ONLY on the retrieved document context. If the context does not contain enough information to answer the question confidently, respond with: "I couldn't find that in the uploaded documents." Always cite which documents you used to answer.

#### 3. Settings

No node-specific settings overrides are included in the workflow export. Standard Settings tab values were not independently captured.

#### 4. Input Data

The agent receives user messages from the Chat Interface.

It can additionally obtain retrieved document context through its connected Pinecone tool.

#### 5. JSON Output

No actual agent execution output was provided.

The expected result is an answer to the user's question, based on retrieved context when relevant.

The exact JSON structure and citation behavior remain to be verified through testing.

#### 6. Binary Output

No binary output is expected for the configured text-based question-answering workflow.

#### 7. Key Transformations

`User Question → AI Agent → Pinecone Retrieval Tool → Retrieved Context → AI-Generated Answer`

The agent coordinates language-model processing and external tool use rather than directly storing documents.

#### 8. Execution Evidence

The workflow export confirms the following connections:

- Chat Interface → RAG Agent
- OpenAI Chat Model → RAG Agent
- Retrieve from Pinecone → RAG Agent

Streaming is enabled.

A successful document-grounded chatbot response was observed. Individual internal tool calls were not independently verified.

#### 9. Operational Risks

- The agent may generate unsupported answers if document grounding is insufficient.
- Missing retrieval results may prevent useful answers.
- Source citations must be checked rather than assumed to be correct.
- Tool failures or API errors may interrupt execution.
- The system message alone does not guarantee that hallucinations are eliminated.

#### 10. Conclusion

The RAG Agent is the central orchestration component of the conversational pipeline. It combines language-model capabilities with document retrieval and applies instructions intended to restrict answers to available source material.

---

### Node 8: OpenAI Chat Model

**Node Type:** OpenAI Chat Model (v1.3)  
**Category:** AI / Language Model  
**Execution Status:** Configuration verified; model response not yet documented

#### 1. Purpose

The "OpenAI Chat Model" provides the language model used by the RAG Agent.

It processes messages and retrieved information to support answer generation and agent decision-making.

Unlike the OpenAI Embeddings node, it produces language-model responses rather than document embedding vectors.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Credential | OpenAI Acc IR | OpenAI API connection |
| Model | gpt-5.4-mini | Selected chat language model |
| Built-in Tools | None configured | No built-in model tools specified |
| Options | None | No additional model options configured |

#### 3. Settings

No node-specific settings overrides are included in the exported JSON. The effective standard Settings tab values were not independently captured.

#### 4. Input Data

The model is connected to the RAG Agent through the `ai_languageModel` connection.

The agent supplies the model with conversational context and relevant information during execution.

#### 5. JSON Output

No standalone model output was captured.

The model's responses are consumed by the agent, which controls the final conversational answer.

#### 6. Binary Output

No binary output is expected in this configuration.

#### 7. Key Transformations

`Agent Messages + Context → OpenAI Chat Model → Model Response`

The model generates language responses, while the agent coordinates when and how the model is used.

#### 8. Execution Evidence

The workflow export confirms:

- Selected model: `gpt-5.4-mini`
- Configured OpenAI credentials
- Connection to the RAG Agent
- No additional built-in tools or model options in the exported configuration

No model response was included in the provided execution evidence.

#### 9. Operational Risks

- Model responses may contain inaccuracies.
- Token usage and API calls can incur costs.
- Model availability, rate limits, and credentials affect execution.
- A language model does not automatically have access to the PDF; document access is provided through the agent's retrieval tool.

#### 10. Conclusion

The OpenAI Chat Model supplies the language-generation capability used by the RAG Agent. Its role differs from the embedding nodes, which create numerical vectors for retrieval.

---

### Node 9: Retrieve from Pinecone

**Node Type:** Pinecone Vector Store (v1.3)  
**Category:** Vector Database / Retrieval Tool  
**Execution Status:** Configuration verified; retrieval results not yet documented  
**Target Index:** `lagerflow-faq`

#### 1. Purpose

The "Retrieve from Pinecone" node gives the RAG Agent access to relevant documents stored in the Pinecone vector database.

It performs semantic retrieval using a query embedding and applies a connected Cohere Reranker to improve the ordering of retrieved documents.

The node is configured as an AI tool that can be called by the agent.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Credential | PineconeApi account 3 | Pinecone API connection |
| Operation Mode | Retrieve Documents as Tool | Makes retrieval available to the AI Agent |
| Tool Description | Retrieve relevant documents from the Pinecone vector store based on the user's query to answer questions about uploaded documents | Describes the retrieval tool's function |
| Pinecone Index | lagerflow-faq | Source index for document retrieval |
| Top K | 5 | Configured number of retrieval results |
| Use Reranker | true | Enables the connected reranking component |
| Options | None | No additional options configured |

#### 3. Settings

No node-specific settings overrides are included in the workflow export. The effective Settings tab values were not independently captured.

#### 4. Input Data

The node receives retrieval requests through the RAG Agent's tool connection.

Its query embedding is produced using the connected Query Embeddings node.

The retrieval target is the `lagerflow-faq` index.

#### 5. JSON Output

No actual retrieval result JSON was provided.

The expected output consists of relevant retrieved document content and associated metadata.

The exact returned field structure, result count, and relevance scores require execution verification.

#### 6. Binary Output

No binary PDF is expected from normal semantic retrieval.

The tool retrieves stored text representations and associated metadata.

#### 7. Key Transformations

`User Query → Query Embedding → Pinecone Similarity Search → Cohere Reranking → Retrieved Document Context`

The workflow first searches for semantically relevant information and then uses reranking to improve the relevance ordering of the retrieved results.

#### 8. Execution Evidence

The workflow export confirms:

- Retrieval mode: `retrieve-as-tool`
- Pinecone index: `lagerflow-faq`
- Top K: `5`
- Reranker enabled
- Connections to Query Embeddings, Cohere Reranker, and RAG Agent

No actual retrieval results were included in the supplied execution evidence.

#### 9. Operational Risks

- An incorrect or empty index leads to missing retrieval context.
- Query embeddings must be compatible with stored document embeddings.
- Poor initial retrieval can limit the effectiveness of reranking.
- API latency may increase when reranking is enabled.
- Relevant source material can still be missed by retrieval.

#### 10. Conclusion

The node provides the RAG Agent with semantic document retrieval from `lagerflow-faq`, enhanced by Cohere reranking.

Its configuration is consistent with the ingestion pipeline's selected index.

---

### Node 10: Query Embeddings

**Node Type:** Embeddings OpenAI (v1.2)  
**Category:** AI / Query Vectorization  
**Execution Status:** Configuration verified; query vector not yet captured

#### 1. Purpose

The "Query Embeddings" node converts a user's retrieval query into a numerical embedding vector.

This enables Pinecone to compare the query with previously stored document vectors.

It uses the same embedding configuration as the document ingestion pipeline.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Credential | OpenAI Acc IR | OpenAI API connection |
| Model | text-embedding-3-small | Embedding model identified from the earlier node configuration |
| Dimensions | 512 | Vector dimensions |
| Additional Options | None | No further options configured |

The model name was established through the earlier embedding-node screenshot. The JSON export explicitly includes the dimensions but does not repeat the model identifier.

#### 3. Settings

No node-specific settings overrides are included in the workflow export. The effective Settings tab values were not independently captured.

#### 4. Input Data

The node processes retrieval queries supplied through the connected Pinecone retrieval operation.

Example query:

`Which languages does LagerFlow support?`

#### 5. JSON Output

No standalone query embedding output was captured.

The expected result is a 512-dimensional numerical vector used internally for similarity search.

#### 6. Binary Output

None expected. Query embeddings are numerical vectors.

#### 7. Key Transformations

`User Retrieval Query → Embedding Model → 512-Dimensional Query Vector`

Pinecone compares this vector with stored document embeddings to identify semantically similar content.

#### 8. Execution Evidence

The exported configuration confirms:

- Dimensions: `512`
- OpenAI credentials configured
- Connection to Retrieve from Pinecone through `ai_embedding`

The document ingestion embedding node also uses 512 dimensions.

#### 9. Operational Risks

- Inconsistent embedding dimensions can cause retrieval failures.
- Different embedding configurations can reduce retrieval compatibility.
- Embedding requests depend on API access and service availability.
- Poorly formulated queries may retrieve irrelevant information.

#### 10. Conclusion

The Query Embeddings node converts user queries into vectors compatible with the document embeddings stored in the `lagerflow-faq` index.

It enables semantic matching between the user's question and the uploaded documents.

---

### Node 11: Cohere Reranker

**Node Type:** Cohere Reranker (v1)  
**Category:** AI / Retrieval Optimization  
**Execution Status:** Configuration verified; reranked results not yet documented

#### 1. Purpose

The "Cohere Reranker" improves the relevance ordering of documents retrieved from Pinecone.

After the vector database identifies candidate documents, the reranker evaluates their relevance to the user's query.

This introduces a second relevance-assessment stage to the RAG retrieval process.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Credential | CohereApi account 3 | Cohere API connection |
| Additional Parameters | None explicitly exported | Default node configuration |

The workflow export does not explicitly specify a reranking model or other model-specific parameters.

#### 3. Settings

No node-specific settings overrides are included in the workflow export. The effective Settings tab values were not independently captured.

#### 4. Input Data

The reranker works with the user's retrieval query and candidate documents obtained through the Pinecone retrieval operation.

It is connected to Retrieve from Pinecone through the `ai_reranker` connection.

#### 5. JSON Output

No actual reranking output was provided.

The expected result is a relevance-based ordering or selection of retrieved document candidates, consumed by the retrieval node.

The exact returned scores and document structure were not captured.

#### 6. Binary Output

No binary output is expected.

The reranker operates on queries and document text.

#### 7. Key Transformations

`Retrieved Candidate Documents + User Query → Cohere Relevance Evaluation → Reranked Documents`

The first retrieval stage finds semantically similar documents. Reranking then evaluates those candidates more directly against the query.

#### 8. Execution Evidence

The workflow export confirms:

- Cohere API credentials configured
- Connection to Retrieve from Pinecone via `ai_reranker`
- Reranking enabled in the Pinecone retrieval node

No successful reranking execution or score output was supplied.

#### 9. Operational Risks

- Reranking introduces additional API requests, latency, and potential costs.
- Poor candidate retrieval cannot always be corrected by reranking.
- Missing or invalid Cohere credentials may prevent successful execution.
- Reranking quality depends on the selected model and retrieved content.

#### 10. Conclusion

The Cohere Reranker provides a second-stage relevance assessment for documents retrieved through Pinecone.

It is intended to improve the quality of the context supplied to the RAG Agent.

---

### Evidence

- Workflow configuration: n8n JSON export
- Uploaded test document: `LagerFlow_Product_FAQ.pdf`
- Chat execution: Screenshot of the question and generated answer
- Document processing: Extracted PDF text and metadata observed in execution output

### Conclusion

The RAG chatbot produced a relevant response grounded in the LagerFlow FAQ and included a source reference.

The workflow demonstrates the integration of document ingestion, vector retrieval, and AI-powered question answering using n8n.

### Workflow 2: Execution Evidence

**Test Input:**

> What's most important in the document? Give me two sentences.

**Observed Result:**

The chatbot generated a relevant summary of the LagerFlow Product FAQ, including the company's warehouse management software, target customers, main features, and pricing information.

The response identified "LagerFlow Product FAQ" as its source.

**Execution Status:** Successful chat response observed.

**Validation:** The answer was consistent with the uploaded document. The screenshot confirms the visible result, but does not independently verify the internal retrieval and reranking steps.

**Evidence:** Screenshot of the successful chatbot conversation.

---

## Workflow 3: LagerFlow Support Ticket Classifier

**Workflow Type:** Custom n8n Workflow  
**Purpose:** Rule-based support ticket classification  
**Total Nodes:** 5  
**Distinct Node Types:** 3  
**External APIs Required:** None

### Workflow Overview

This workflow demonstrates basic automation concepts in n8n by classifying incoming support tickets according to a simple keyword-based rule.

A manually triggered workflow generates a sample support ticket. An IF node checks whether the message contains the word `down`. Depending on the result, the workflow assigns either `High` or `Normal` priority.

**Workflow Structure:**

`Manual Trigger → Edit Fields → IF → True: Set High Priority / False: Set Normal Priority`

The workflow introduces three additional node types: Manual Trigger, Edit Fields (Set), and IF.

---

### Node 12: When Clicking 'Execute Workflow'

**Node Type:** Manual Trigger  
**Category:** Trigger  
**Execution Status:** Successful  
**Output Items:** 1

#### 1. Purpose

The Manual Trigger starts the workflow when the user clicks the execution button in n8n.

It is particularly useful for testing workflows without external webhooks, schedules, or API integrations.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Trigger Type | Manual | Starts when the workflow is manually executed |
| Additional Parameters | None | No further configuration required |

#### 3. Settings

No custom settings were documented.

#### 4. Input Data

The node does not require input from a previous node.

The execution is initiated manually through the n8n interface.

#### 5. JSON Output

The Manual Trigger typically generates a single empty JSON item:

```json
[
  {}
]
```

#### 6. Binary Output

None.

#### 7. Key Transformations

`Manual Execution → Workflow Trigger → Initial JSON Item`

The node starts the workflow without transforming external data.

#### 8. Execution Evidence

The workflow screenshot confirms successful execution of the Manual Trigger with one item passed to the following Edit Fields node.

#### 9. Operational Risks

Manual execution requires user interaction and is not suitable for unattended production automation.

#### 10. Conclusion

The Manual Trigger provides a simple entry point for testing the custom support ticket classification workflow.

---

### Node 13: Edit Fields

**Node Type:** Edit Fields (Set)  
**Category:** Data Transformation  
**Execution Status:** Successful  
**Output Items:** 1

#### 1. Purpose

The Edit Fields node creates a structured sample support ticket.

It demonstrates how n8n can generate or transform JSON data using manually configured fields.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Mode | Manual Mapping | Fields are defined manually |
| ticket_id | LF-001 | Unique ticket identifier |
| customer | Müller Logistik GmbH | Customer name |
| message | Our warehouse system is down. We cannot process orders. | Support request |

All three fields use the String data type.

#### 3. Settings

No custom settings were documented.

#### 4. Input Data

The node receives the initial item generated by the Manual Trigger.

#### 5. JSON Output

The following output was observed during successful execution:

```json
[
  {
    "ticket_id": "LF-001",
    "customer": "Müller Logistik GmbH",
    "message": "Our warehouse system is down. We cannot process orders."
  }
]
```

#### 6. Binary Output

None.

#### 7. Key Transformations

`Initial JSON Item → Field Creation → Structured Support Ticket`

The node adds ticket information that can be evaluated by subsequent workflow steps.

#### 8. Execution Evidence

The observed output confirms successful creation of all three fields.

**Output Items:** 1

#### 9. Operational Risks

- Manually defined values are static.
- Invalid field names or values may cause downstream problems.
- A production workflow would require a real data source.

#### 10. Conclusion

The Edit Fields node successfully generates a structured support ticket and demonstrates basic JSON data creation in n8n.

---

### Node 14: If

**Node Type:** IF  
**Category:** Conditional Logic  
**Execution Status:** Successful  
**Output Items:** 1 in True Branch

#### 1. Purpose

The IF node evaluates a condition and routes incoming data into separate execution branches.

In this workflow, it determines whether a support ticket should be classified as high priority.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Value 1 | `{{ $json.message }}` | Reads the support message |
| Data Type | String | Performs a text comparison |
| Operation | contains | Checks whether text contains a substring |
| Value 2 | down | Keyword indicating a potential outage |

#### 3. Settings

No custom settings were documented.

#### 4. Input Data

The IF node receives the JSON object generated by Edit Fields.

**Input Message:**

`Our warehouse system is down. We cannot process orders.`

#### 5. JSON Output

The following item was observed in the True Branch:

```json
[
  {
    "ticket_id": "LF-001",
    "customer": "Müller Logistik GmbH",
    "message": "Our warehouse system is down. We cannot process orders."
  }
]
```

**True Branch:** 1 item  
**False Branch:** 0 items in the observed execution

#### 6. Binary Output

None.

#### 7. Key Transformations

`Support Ticket → Keyword Check → True or False Branch`

The IF node evaluates the message but preserves the incoming JSON fields.

#### 8. Execution Evidence

The execution screenshot confirms that the message contains the word `down` and was correctly routed through the True Branch.

#### 9. Operational Risks

- Keyword detection is a simple rule, not semantic understanding.
- Urgent messages without the word `down` may be classified incorrectly.
- Messages containing the keyword in unrelated contexts can produce false positives.
- More advanced classification would require additional rules or AI-based processing.

#### 10. Conclusion

The IF node successfully evaluates the configured condition and directs the support ticket to the high-priority processing branch.

---

### Node 15: Set High Priority

**Node Type:** Edit Fields (Set)  
**Category:** Data Transformation  
**Execution Status:** Successful  
**Output Items:** 1

#### 1. Purpose

The Set High Priority node assigns a high-priority label to tickets that satisfy the IF condition.

It preserves the original ticket information and adds a new priority field.

#### 2. Parameters

| Parameter | Configured Value | Description |
|---|---|---|
| Mode | Manual Mapping | Defines fields manually |
| Field Name | priority | New JSON field |
| Type | String | Priority is stored as text |
| Value | High | Assigned priority |
| Include Other Input Fields | Enabled | Preserves incoming ticket data |
| Input Fields to Include | All | Includes all original fields |
| Options | None | No additional options |

#### 3. Settings

No custom settings were documented.

#### 4. Input Data

The node receives tickets routed through the True Branch of the IF node.

#### 5. JSON Output

The following output was observed:

```json
[
  {
    "ticket_id": "LF-001",
    "customer": "Müller Logistik GmbH",
    "message": "Our warehouse system is down. We cannot process orders.",
    "priority": "High"
  }
]
```

#### 6. Binary Output

None.

#### 7. Key Transformations

`Support Ticket → Add priority: High → Classified Ticket`

The original JSON fields remain available.

#### 8. Execution Evidence

The execution screenshot confirms:

- Successful node execution
- One output item
- Original fields preserved
- New `priority` field added with the value `High`

#### 9. Operational Risks

- The priority value is static.
- Classification accuracy depends entirely on the preceding IF condition.
- Incorrect field-preservation settings could remove necessary ticket information.

#### 10. Conclusion

The Set High Priority node successfully enriches urgent support tickets with a `High` priority classification.

---

### Node 16: Set Normal Priority

**Node Type:** Edit Fields (Set)  
**Category:** Data Transformation  
**Execution Status:** Configured and connected; execution not yet verified

#### 1. Purpose

The Set Normal Priority node assigns a normal-priority label to tickets that do not satisfy the IF condition.

It provides the alternative processing path for non-matching support requests.

#### 2. Parameters

| Parameter | Intended Value | Description |
|---|---|---|
| Mode | Manual Mapping | Defines fields manually |
| Field Name | priority | Priority field |
| Type | String | Stores priority as text |
| Value | Normal | Assigned priority |
| Include Other Input Fields | Enabled | Preserves existing ticket data |
| Input Fields to Include | All | Includes original ticket fields |

The node was added to the False Branch. The complete parameter configuration was not independently captured in the provided screenshot.

#### 3. Settings

No custom settings were documented.

#### 4. Input Data

The node is connected to the False Branch of the IF node.

It is intended to receive support tickets whose messages do not contain the keyword `down`.

#### 5. JSON Output

No actual execution output was captured for this branch.

**Expected output for a non-matching ticket:**

```json
[
  {
    "ticket_id": "LF-001",
    "customer": "Müller Logistik GmbH",
    "message": "I would like information about your pricing plans.",
    "priority": "Normal"
  }
]
```

This is an illustrative expected result, not an observed execution record.

#### 6. Binary Output

None expected.

#### 7. Key Transformations

`Non-Matching Support Ticket → Add priority: Normal → Classified Ticket`

#### 8. Execution Evidence

The workflow screenshot confirms the node is connected to the False Branch.

The provided test message was routed through the True Branch, so the Normal Priority node was not executed in that test.

#### 9. Operational Risks

- Tickets requiring urgent support may be incorrectly classified as normal if they do not contain the configured keyword.
- A static priority label cannot account for complex business requirements.
- The branch requires a separate test to confirm its output.

#### 10. Conclusion

The Set Normal Priority node provides the alternative path for normal-priority support requests. Its connection is confirmed, while successful execution remains unverified.

---

### Workflow 3: Execution Evidence

#### Test Objective

Verify that a structured support ticket can be generated, evaluated using conditional logic, and enriched with a priority classification.

#### Test Input

```json
{
  "ticket_id": "LF-001",
  "customer": "Müller Logistik GmbH",
  "message": "Our warehouse system is down. We cannot process orders."
}
```

#### Expected Behavior

The IF node detects the keyword `down`, routes the ticket through the True Branch, and the final Edit Fields node assigns `High` priority.

#### Observed Output

```json
{
  "ticket_id": "LF-001",
  "customer": "Müller Logistik GmbH",
  "message": "Our warehouse system is down. We cannot process orders.",
  "priority": "High"
}
```

#### Execution Results

| Step | Result |
|---|---|
| Manual Trigger | Successful |
| Edit Fields | Successful |
| IF Condition | True Branch selected |
| Set High Priority | Successful |
| Set Normal Priority | Not executed in the observed test |

**Overall Result:** Successful execution of the high-priority classification path.

#### Conclusion

The custom workflow demonstrates manual triggering, structured JSON creation, conditional routing, and data enrichment.

The successful test validates the high-priority classification path. The normal-priority branch is configured as an alternative path but has not yet been independently tested.

---

## Consolidated Node Reference Table

| # | Node | Node Type | Workflow |
|---|---|---|---|
| 1 | Upload Documents Form | Form Trigger | 1 |
| 2 | Store in Pinecone | Pinecone Vector Store | 1 |
| 3 | OpenAI Embeddings | Embeddings OpenAI | 1 |
| 4 | Document Loader | Default Data Loader | 1 |
| 5 | Text Splitter | Recursive Character Text Splitter | 1 |
| 6 | Chat Interface | Chat Trigger | 2 |
| 7 | RAG Agent | AI Agent | 2 |
| 8 | OpenAI Chat Model | OpenAI Chat Model | 2 |
| 9 | Retrieve from Pinecone | Pinecone Vector Store | 2 |
| 10 | Query Embeddings | Embeddings OpenAI | 2 |
| 11 | Cohere Reranker | Cohere Reranker | 2 |
| 12 | When Clicking 'Execute Workflow' | Manual Trigger | 3 |
| 13 | Edit Fields | Edit Fields (Set) | 3 |
| 14 | If | IF | 3 |
| 15 | Set High Priority | Edit Fields (Set) | 3 |
| 16 | Set Normal Priority | Edit Fields (Set) | 3 |

### Lab Summary

| Requirement | Documented Result |
|---|---|
| Workflow 1 | PDF-Based RAG — Document Ingestion |
| Workflow 2 | AI Agent Chat — Document Question Answering |
| Workflow 3 | LagerFlow Support Ticket Classifier |
| Total Documented Nodes | 16 |
| Distinct Node Types | 12 |
| Document Processing Test | Observed |
| AI Chat Test | Successful response observed |
| Custom Workflow Test | High-priority path successful |

Workflows 1 and 2 are separate functional paths within one n8n workflow export. Workflow 3 is a separately created custom workflow.

### Final Conclusion

The lab demonstrates understanding of n8n triggers, data transformation, conditional logic, AI agents, vector databases, embedding generation, document processing, and retrieval optimization.

Three functional workflow paths have been documented, covering 16 nodes and 12 distinct node types.

Observed execution evidence is included where available, and unverified steps are explicitly identified.