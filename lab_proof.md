# n8n Node Study Guide – Lab Proof

## 1. Workflow exports
- RAG system: [rag_workflow.json]
- AI agent chat: [ai_agent_chat.json]
- Joke workflow: [joke_workflow.json]

## 2. Critical path (RAG workflow)
- INPUT: a chat question from the user
- DECIDE: the question (chatInput) is required; it is routed to the
  AI Agent, which searches the Pinecone index "lagerflow-faq"
- BUILD: Chat Trigger → AI Agent (+ Chat Model, Pinecone tool,
  Query Embeddings) → answer
- VERIFY: one successful run, shown below
- EXPLAIN: see Risks at the end

## 3. Input payload
```json
{
  "action": "sendMessage",
  "sessionId": "d9e25c9c93ff4888a067cd4230bfcaf7",
  "chatInput": "How long does setup take?"
}
```

## 4. Execution trace
1. Chat Trigger received the question.
2. OpenAI Chat Model (1st call) decided to use the Pinecone tool
   and rewrote the search query.
3. Retrieve from Pinecone + Query Embeddings found the matching chunk
   (lines 17–30, "A normal setup takes 6 to 8 weeks...") as the 1st result.
4. OpenAI Chat Model (2nd call) wrote the answer
   (2590 prompt + 45 completion = 2635 tokens).

![agent logs](images/rag_agent_logs.png)

## 5. Output record
```json
{
  "output": "A normal setup takes **6 to 8 weeks**. If the project has **more than 3 warehouses**, it takes **10 to 12 weeks**.\n\nSource used: **LagerFlow Product FAQ**."
}
```
![chat answer](images/chat_answer.png)

## Risks and observations
1. Chunk Overlap is 0: a question and its answer can be split into
   different chunks (it worked in my test, but could fail for others).
2. Embedding model and dimensions (text-embedding-3-small, 512) must
   match in Part 1, Part 2 and the Pinecone index, or search fails.
3. Insert Documents always adds: uploading the same PDF twice
   creates duplicate chunks.
4. Rerank is off (no Cohere), and Limit 5 > 3 chunks, so all chunks
   are returned; the search is not really tested with this small PDF.
5. RAG agent has no memory; the AI agent chat has memory but no
   document tool.
6. Form and RAG chat have no authentication: anyone with the link
   can upload files or use the chat (and spend OpenAI credits).
7. Joke workflow depends on an external API; if it changes or
   goes down, the workflow breaks.

Simplification: the critical path only needs Chat Trigger → AI Agent
→ Pinecone retrieve. Memory and reranking are extras.

Note: Check note_analysis_file.md for analysis