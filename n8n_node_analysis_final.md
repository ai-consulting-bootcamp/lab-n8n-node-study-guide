# n8n Node Analysis Lab — Final Submission

**Objective:** Analyse three n8n workflows and document ten distinct node types, including configuration, JSON input/output and field transformations. JSON excerpts are labelled where full execution data was not captured.

## Workflow 1 — PDF-based RAG with Pinecone and Cohere Reranker

**Flow:** PDF upload → Pinecone storage; chat question → retrieval → Cohere reranking → answer.

### Node 1 — Store in Pinecone

**Configuration**

| Parameter | Configuration |
|---|---|
| Credential | PineconeApi account 11 |
| Operation Mode | Insert Documents |
| Pinecone Index | lagerflow-faq |
| Embedding Batch Size | 200 |
| Options | No additional properties |
| Connected Embedding Model | text-embedding-3-small |
| Embedding Dimensions | 512 |

**Input JSON**

```json
[
  {
    "documents": [
      {
        "filename": "Healthcare AI Test Document.pdf",
        "mimetype": "application/pdf",
        "size": 97551
      }
    ],
    "submittedAt": "2026-11-03T01:07:18.422+01:00",
    "formMode": "test"
  }
]
```

**Output JSON**

```json
[
  {
    "metadata": {
      "source": "blob",
      "blobType": "application/pdf",
      "pdf": {
        "version": "1.10.100",
        "info": {
          "PDFFormatVersion": "1.7",
          "IsAcroFormPresent": false,
          "IsXFAPresent": false,
          "Author": "Martha Maha",
          "Creator": "Microsoft® Word for Microsoft 365",
          "Producer": "Microsoft® Word for Microsoft 365"
        },
        "totalPages": 1
      },
      "loc": {
        "lines": {
          "from": 1,
          "to": 18
        }
      }
    }
  }
]
```

**Transformation:** Uploaded PDF metadata and binary content are processed into document content and embeddings for insertion into `lagerflow-faq`; the observed output exposes PDF metadata and text-location fields.

*Evidence note:* Output is an excerpt, not a complete raw JSON export.

### Node 2 — Cohere Reranker

**Configuration**

| Parameter | Observed Value | Purpose |
|---|---|---|
| Credential | CohereApi account 10 | Authenticates requests to Cohere |
| Model | `rerank-v3.5` | Model used to score and rank retrieved documents |
| Top N | `3` | Limits the returned results to the three highest-ranked documents |

**Input JSON**

```json
{
  "query": "What services does MedCare Solutions provide? MedCare Solutions services offerings company description",
  "documents": [{"pageContent": "Healthcare AI Test Document — MedCare Solutions provides patient monitoring systems, digital patient records, healthcare staff training and AI-powered reporting.", "metadata": {"blobType": "application/pdf"}}]
}
```

**Output JSON**

```json
{
  "response": [{"pageContent": "Healthcare AI Test Document — MedCare Solutions provides patient monitoring systems, digital patient records, healthcare staff training and AI-powered reporting.", "metadata": {"blobType": "application/pdf", "relevanceScore": 0.878825}, "id": "caa82d8f-e1ff-4669-a0f8-6dc418109c57"}]
}
```

**Transformation:** Input `query` and `documents[]` become ranked `response[]` documents. `pageContent` and metadata are retained; `relevanceScore` is added. Top N is configured to 3.

*Evidence note:* Output is an excerpt, not a complete raw JSON export.

## Workflow 2 — RAG Chatbot (simple, no reranker)

**Flow:** Chat Trigger → RAG Agent using OpenAI Chat Model, Pinecone retrieval and query embeddings.

### Node 3 — Chat Trigger

**Configuration**

| Parameter | Value |
|---|---|
| Make Chat Publicly Available | Enabled |
| Mode | Hosted Chat |
| Authentication | None |
| Initial Message | Hello! I can answer questions about your uploaded documents. What would you like to know? |
| Make Available in n8n Chat Hub | Disabled |
| Additional Options | None |

**Input JSON**

No incoming JSON. This is a trigger node that starts the workflow when a chat message arrives.

**Output JSON**

```json
[
  {
    "action": "sendMessage",
    "sessionId": "0305f8c75fc44f6685db3b851d76a077",
    "chatInput": "What services does MedCare Solutions provide?"
  }
]
```

**Transformation:** An incoming chat event creates `action`, `sessionId` and `chatInput` fields; no prior JSON item is required.

### Node 4 — RAG Agent

**Configuration**

| Parameter | Value |
|---|---|
| Source for Prompt | Connected Chat Trigger Node |
| Prompt | `{{ $json.chatInput }}` |
| Require Specific Output Format | Disabled |
| Enable Fallback Model | Disabled |
| System Message | Answer questions using only retrieved document context; acknowledge when insufficient information is available |
| Enable Streaming | Enabled |

**Input JSON**

```json
[
  {
    "action": "sendMessage",
    "sessionId": "afe533d9360042659c4a7e5f8cef0e0d...",
    "chatInput": "How much does a business plan cost?"
  }
]
```

**Output JSON**

```json
[
  {
    "output": "The Business plan costs **1,290 EUR per month**, plus a **one-time setup fee of 2,500 EUR**.\nSource: **LagerFlow Product FAQ**"
  }
]
```

**Transformation:** The chat question is combined with retrieved context and transformed into a natural-language `output` answer; chat event fields are not included in the shown output.

### Node 5 — OpenAI Chat Model

**Configuration**

| Parameter | Value |
|---|---|
| Credential | `OpenAi_Actual` |
| Model Selection | From list |
| Model | `gpt-5.4-mini` |
| Use Responses API | Enabled |
| Built-in Tools | None configured |
| Additional Options | None configured |

**Input JSON**

The execution logs displayed the input as text rather than a complete JSON object.

The observed input contained the following instructions and question:

```text
System: You are a helpful assistant that answers questions
based ONLY on the retrieved document context.

If the context does not contain enough information to answer
the question confidently, respond with:
"I couldn't find that in the uploaded documents."

Always cite which documents you used to answer.

Human: How much does a business plan cost?
```

**Input observation:** The model received a system instruction defining how it should answer and a human message containing the user's question.

**Output JSON**

Raw model sub-node output JSON was **not captured**. The downstream RAG Agent returned an `output` field with a cited Business-plan price; that is not the model node’s verified raw JSON.

**Transformation:** The model consumes system/user instructions and generates text for the RAG Agent. The raw sub-node output JSON was not captured; the downstream agent response is shown only as supporting evidence.

*Evidence note:* The model sub-node output cannot be independently verified from the captured execution.

### Node 6 — Retrieve from Pinecone

**Configuration**

| Parameter | Value |
|---|---|
| Credential | `PineconeApi account 10` |
| Operation Mode | Retrieve Documents (As Tool for AI Agent) |
| Description | Retrieve relevant documents from the Pinecone vector store based on the user's query to answer questions about uploaded documents |
| Pinecone Index | `lagerflow-faq` |
| Limit | 5 |
| Include Metadata | Enabled |
| Rerank Results | Disabled |
| Additional Options | None |

**Input JSON**

```json
{
  "input": "business plan cost price fee cost of a business plan"
}
```

**Output JSON**

```json
{
  "response": [
    {
      "type": "text",
      "text": "{\"pageContent\":\"LagerFlow – Product FAQ. LagerFlow is warehouse management software for small and medium logistics companies. The Business plan costs 1,290 EUR per month, with a one-time setup fee of 2,500 EUR.\",\"metadata\":{\"blobType\":\"application/pdf\"}}"
    }
  ]
}
```

**Transformation:** The search text in `input` is used to retrieve PDF text and metadata in `response`; the input query is not returned as a separate field.

### Node 7 — Query Embeddings

**Configuration**

| Parameter | Value |
|---|---|
| Credential | `OpenAi_Actual` |
| Model | `text-embedding-3-small` |
| Dimensions | `512` |

**Input JSON**

```json
{
  "query": "business plan cost price fee cost of a business plan"
}
```

**Output JSON**

```json
{
  "response": [
    -0.0259246826171875,
    0.004795074462890625,
    0.07470703125,
    -0.0616455078125,
    -0.0005884170532226562,
    -0.041595458984375,
    0.0026264190673828125,
    0.09710693359375,
    0.0457763671875,
    -0.002635955810546875
  ]
}
```

**Transformation:** The text `query` becomes a numerical `response` embedding vector (512 dimensions); only ten observed values are reproduced.

*Evidence note:* Output is an excerpt, not a complete raw JSON export.

## Workflow 3 — My workflow 3 — Technology News Report

**Flow:** Manual Trigger → Message a Model → Edit Fields.

### Node 8 — Manual Trigger

**Configuration:** No parameters (manual execution trigger).

**Input JSON**

No incoming JSON (trigger node).

**Output JSON**

No populated JSON fields observed; downstream node received an empty item.

**Transformation:** This trigger starts the workflow without incoming JSON. No output fields were observed.

### Node 9 — Message a Model

**Configuration**

| Parameter | Value |
|---|---|
| Credential | `OpenAi_Actual` |
| Resource | Text |
| Operation | Message a Model |
| Model | `GPT-5.4-MINI` |
| System Prompt | Act as a news reporter; provide three recent news stories with headlines, summaries and source links |
| User Prompt | `Category: technology` |
| Simplify Output | Enabled |
| Built-in Tool | Web Search |
| Search Context Size | Medium |

**Input JSON**

```json
[
  {}
]
```

**Output JSON**

```json
[
  {
    "output": [
      {
        "type": "message",
        "status": "completed",
        "content": [
          {
            "type": "output_text",
            "annotations": [
              {
                "type": "url_citation",
                "start_index": 424,
                "end_index": 517,
                "title": "Nvidia and other Big Tech stocks lift the US market despite drops for Apple and much of Wall Street"
              }
            ]
          }
        ]
      }
    ]
  }
]
```

**Transformation:** The empty incoming item and configured prompts produce a structured `output[]` message with text and URL citation annotations.

*Evidence note:* Output is an excerpt, not a complete raw JSON export.

### Node 10 — Edit Fields (Set)

**Configuration**

| Parameter | Value |
|---|---|
| Mode | Manual Mapping |
| category | String: technology |
| report_status | String: completed |
| Include Other Input Fields | Enabled |
| Input Fields to Include | All |
| Additional Options | None |

**Input JSON**

```json
[
  {
    "output": [
      {
        "type": "message",
        "status": "completed",
        "content": [
          {
            "type": "output_text",
            "annotations": [
              {
                "type": "url_citation",
                "start_index": 424,
                "end_index": 517
              }
            ]
          }
        ]
      }
    ]
  }
]
```

**Output JSON**

```json
{
  "output": ["… original model response retained …"],
  "category": "technology",
  "report_status": "completed"
}
```

**Transformation:** The original `output[]` is preserved and two top-level string fields, `category` and `report_status`, are added.

*Evidence note:* Output is an excerpt, not a complete raw JSON export.

## Consolidated Reference Table

| # | Workflow | Distinct node type | Configuration highlight | Input → output | Main change |
|---:|---|---|---|---|---|
| 1 | 1 | Store in Pinecone | Insert Documents; index `lagerflow-faq`; batch 200 | PDF upload → document metadata/content | Load/embed/store |
| 2 | 1 | Cohere Reranker | `rerank-v3.5`; Top N 3 | Query + documents → scored documents | Score and rerank |
| 3 | 2 | Chat Trigger | Hosted Chat; no authentication | Chat message → session + question | Create chat fields |
| 4 | 2 | RAG Agent | Prompt from `chatInput`; streaming on | Question → grounded answer | Generate answer |
| 5 | 2 | OpenAI Chat Model | `gpt-5.4-mini`; Responses API on | Instructions → generated response (raw JSON unavailable) | LLM inference |
| 6 | 2 | Retrieve from Pinecone | Index `lagerflow-faq`; limit 5; metadata on | Search query → FAQ document chunks | Retrieve text/metadata |
| 7 | 2 | Query Embeddings | `text-embedding-3-small`; 512 dims | Query text → 512-number vector | Vectorize text |
| 8 | 3 | Manual Trigger | No parameters | No input → empty trigger item | Start execution |
| 9 | 3 | Message a Model | `GPT-5.4-MINI`; Web Search medium | Empty item + prompts → news/citations | Generate cited report |
| 10 | 3 | Edit Fields (Set) | Manual mapping; include all fields | Model output → original output + two fields | Add classification/status |

## Submission Evidence

The three workflows executed successfully in the inspected runs. Screenshots and shortened JSON extracts support the analysis; complete raw payloads were not available for every node. In particular, the OpenAI Chat Model raw output was not captured, and the Cohere Reranker excerpt shows only the first scored result.

Before submitting, ensure any screenshots are saved with the project and that no API keys or tokens appear in the files.
