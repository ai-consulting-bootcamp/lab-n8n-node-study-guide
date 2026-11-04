# n8n Node Analysis

## AI Agent Chat

[AI Agent Chat workflow export](node-study-ai-agent-chat.json)

| Node | Parameters | Settings | What It Does | JSON Input | JSON Output | Key Transformations |
|---|---|---|---|---|---|---|
| [Chat Trigger](evidence/agent-trigger.png) | Hosted Chat and initial greeting | Public access enabled, authentication None, Chat Hub disabled in the observed configuration | Starts a run from a chat message | What is 37 multiplied by 24? | action: sendMessage, sessionId, chatInput | Wraps the message with session and action fields. |
| [AI Agent](evidence/ai-agent.png) | Connected Chat Trigger Node, arithmetic system message | Structured output and fallback model disabled | Handles the question using the model and Calculator | chatInput: What is 37 multiplied by 24? | output: 888 — 37 times 24 equals 888. | Reads chatInput and returns the final answer in output. |
| [OpenAI Chat Model](evidence/agent-model.png) | gpt-5.4-mini, Responses API enabled | OpenAI credential, no built-in tools configured | Generates the tool call and final reply | Second call receives messages containing the question, Calculator call and tool result 888 | response.generations contains the final answer and tokenUsageEstimate.totalTokens is 150 | Turns the Calculator result into a short reply. The second call input includes the earlier tool call. |
| [Calculator](evidence/calculator.png) | No configurable parameters | Connected through Tool | Evaluates an arithmetic expression | input: 37*24 | response: "888" | Turns the expression into a result returned as a string. |

The [execution log](evidence/agent-tool-trace.png) shows a model call, a Calculator call, and a second model call.

## PDF RAG

[PDF RAG workflow export](node-study-pdf-rag.json)

| Node | Parameters | Settings | What It Does | JSON Input | JSON Output | Key Transformations |
|---|---|---|---|---|---|---|
| [Upload Documents Form](evidence/upload-form.png) | File field documents, accepted extensions .pdf, .csv, .json | Test form, no authentication, responds on submission | Accepts a document upload | Form submission with LagerFlow_Product_FAQ.pdf | One item with binary documents | Passes the uploaded PDF as binary data. |
| [Store in Pinecone](evidence/rag-ingestion.png) | Insert Documents, lagerflow-faq, batch size 200 | Pinecone credential, loader and embeddings connections | Indexes document chunks | One item with binary documents | Three items with pageContent and metadata | Turns one PDF into searchable chunks with document and line metadata. |
| Document Loader | Binary data, custom splitting | Connected to Store in Pinecone | Parses the uploaded PDF | Binary documents | Document text and PDF metadata at the loader boundary | Extracts text for splitting. The insertion output shows the resulting chunks. |
| Text Splitter | Recursive character splitter | Connected to Document Loader | Splits extracted text into chunks | Extracted FAQ text | Text chunks | The insertion output shows three chunks with line ranges. |
| OpenAI Embeddings / Query Embeddings | 512 dimensions in the configured export | OpenAI credential, embedding subnode connections | Embeds document chunks and search queries | Chunk text on insert, query text on retrieval | Vector at the embedding boundary | Both branches use vectors for similarity search. Exact vectors are not shown in the trace. |
| Retrieve from Pinecone | Tool mode, lagerflow-faq, top K 5 in the configured export | Pinecone credential, reranking enabled | Retrieves candidate FAQ passages for the agent | Agent search query | Retrieved document context | Uses query embeddings for search and calls Cohere to rank candidates. |
| [Cohere Reranker](evidence/cohere-reranker.png) | rerank-v3.5, Top N 3 | Cohere credential, connected to Retrieve from Pinecone | Scores retrieved passages against the query | query and documents containing pageContent, metadata and id | response array containing ranked passages | Preserves text and document IDs and adds metadata.relevanceScore. The first visible result scored 0.8783249. |
| [Chat Interface](evidence/rag-trigger.png) | Hosted Chat, initial greeting, Streaming response | Public chat enabled, authentication set to None | Starts the retrieval branch | Test chat question about employees and warehouses | One item with action, sessionId and chatInput | Wraps the question in a chat event with action sendMessage. |
| [OpenAI Chat Model (RAG)](evidence/rag-model.png) | gpt-5.4-mini, Use Responses API enabled | OpenAI credential, no built-in tools configured | Generates the final answer after retrieval | messages with system instructions, user question and retrieval context | response.generations with answer text, plus tokenUsage | The second call returned the FAQ citation and used 1,748 tokens. |
| RAG Agent | Chat prompt and document-grounding system message | OpenAI Chat Model and Pinecone tool connections | Answers using retrieved context | Question about target company size | Answer citing LagerFlow – Product FAQ | Converts the question and retrieved passages into a cited response. |

The [retrieval trace](evidence/rag-retrieval.png) shows a successful run in 5.801 s, including Query Embeddings and Cohere Reranker. The [chat response](evidence/rag-answer.png) identifies the target as companies with 20 to 500 employees and 1 to 10 warehouses.

## Data Mapping

The Save Lead Record screenshot comes from a separate insert. Execution #1595 and its stored row are documented in the proof.

| Node | Parameters | Settings | What It Does | JSON Input | JSON Output | Key Transformations |
|---|---|---|---|---|---|---|
| Manual Trigger | No parameters | Manual execution | Starts the test run | Editor click | One item passed to Create Sample Input | Starts the run without a business payload. |
| [Create Sample Input](evidence/sample-input.png) | Edit Fields in JSON mode | Other input fields excluded | Produces a sample lead | Trigger item | request_id, name, email, company_size, source | Builds one test record with numeric company_size. |
| [Map Lead Record](evidence/map-lead.png) | Edit Fields with four expression assignments | Manual mapping, other input fields excluded | Shapes the lead for storage | Sample lead with company_size 120 | lead_id, contact_name, contact_email, priority | Renames contact fields and derives high priority at 50 employees or more. |
| [Save Lead Record](evidence/save-lead.png) | Data Table row insert, Lab Lead Records | Automatic column mapping | Persists the mapped lead | Mapped record for lab-001 | Same record plus id, createdAt and updatedAt | Matches fields by name and returns the inserted row. |

The [proof](lab_proof.md) contains the complete payload, execution trace and stored record for this workflow.
