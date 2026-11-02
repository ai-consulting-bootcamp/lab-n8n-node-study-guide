# Become the person who reads the docs

> **How you'll submit this lab**
>
> This repo is your lab. Fork it, do the work described below in your fork, then open a pull
> request back into this repository. An AI reviewer will check your PR against `rubric.md` and
> leave feedback directly on the PR. See `README.md` for the full workflow.

## Learning Goal

You will build one n8n Node Study Guide workflow path and prove data moves from input to output correctly.

## Working Context

This lab turns a manual handoff into a small automated workflow.
You define one input, one transformation, and one output a reviewer can inspect.
Avoid broad automation. Prove the critical path first.

## Proof of Learning

Submit one `lab_proof.md` with the workflow export or configuration, one execution trace, one input payload, and one output record.

## Pseudocode

```text
INPUT: source event, message, ticket, or payload
DECIDE: required fields, routing rule, and destination
BUILD: trigger -> transform -> action
VERIFY: inspect one successful run and output artifact
EXPLAIN: justify the mapping and operational risk
```



## Build

## Step-by-Step Instructions

### Step 1: Set Up n8n Environment for Testing

Do: Ensure you have a working n8n instance ready for workflow analysis.

**Actions:**
1. **Access n8n:**
   - If using n8n Cloud: Log in to your account at [n8n.cloud](https://n8n.cloud)
   - If using self-hosted: Ensure your local n8n instance is running and accessible

2. **Verify Setup:**
   - Create a test workflow to confirm n8n is functioning
   - Add a simple node (e.g., Manual Trigger + Set node) and execute it
   - Verify you can see input/output data in the execution view

3. **Prepare for Analysis:**
   - Open a new browser tab or workspace for documentation
   - Have a markdown editor or spreadsheet ready to record your findings

---

### Step 2: Access Class Workflows

Do: Obtain copies of the workflows demonstrated in class for analysis.

**Actions:**

You should have access to these three workflows shared in class:
File RAG_Chatbot_with_reranker.json :
   - **Workflow 1:** Build a PDF-based RAG system with OpenAI, Pinecone and Cohere reranking
   - **Workflow 2:** AI agent chat

File templaten8n_track_token_spend.json:
   - **Workflow 3:** Qualification of Lead priority
     





**Open Each Workflow:**
   - Click on each workflow to open it in the n8n editor
   - Familiarize yourself with the overall structure and node connections
   - Note which nodes are used in each workflow

---

### Step 3: Analyze Workflows and Document Nodes

Do: Systematically analyze each node in the workflows and create a comprehensive reference table.

**Actions:**

#### 3.1: Select Your First Workflow
- Start with **Workflow 1** (PDF-based RAG system) or **Workflow 2** (AI agent chat)
- These workflows contain more nodes and are better for learning

#### 3.2: Analyze Each Node in the Workflow

For **each node** in the workflow, follow these steps:

1. **Click on the node** to open its configuration panel

2. **Document Parameters:**
   - List all parameters visible in the node configuration
   - Note which parameters are required vs. optional
   - Record example values or settings used

3. **Document Settings:**
   - Check the "Settings" tab (if available)
   - Note authentication methods, response formats, and other options
   - Record any special configurations

4. **Analyze JSON Payload Movement:**
   - Click **"Execute Node"** or run the workflow up to this node
   - In the execution view, examine the **input data** (data coming into the node)
   - Examine the **output data** (data leaving the node)
   - Document the structure of both input and output JSON

5. **Identify Transformations:**
   - Compare input JSON to output JSON
   - Note what fields were added, removed, or modified
   - Document any data type conversions or structural changes

6. **Record Your Findings:**
   - Add the node to your reference table (see template below)
   - Include screenshots of:
     - Node configuration
     - Input JSON structure
     - Output JSON structure

#### 3.3: Repeat for All Workflows

- Complete the analysis for **Workflow 1**, **Workflow 2**, and your **Workflow 3**
- Aim to analyze **at least 10 different node types** across all workflows
- If you encounter duplicate node types, note any variations in configuration

#### 3.4: Create Your Reference Table

Do: Document all analyzed nodes in a single comprehensive table.

Use the template below to create your reference table. You can create this in:
- Markdown file (`.md`)
- Spreadsheet (Google Sheets, Excel)
- Documentation tool (Notion, Confluence)

**Table Template:**

**Table template:**
```markdown
# n8n Node Reference Table

| Node | Parameters | Settings | What It Does | JSON Input | JSON Output | Key Transformations |
|------|------------|----------|--------------|------------|-------------|---------------------|
| Webhook | Method, Path, Response Mode | Auth, Response Code | Receives HTTP requests | HTTP request | n8n data format | HTTP → n8n format |
| HTTP Request | Method, URL, Auth | Response Format (under Options), Headers | Makes API calls | n8n data | API response | n8n → API → n8n |
| Set | Assignments (field name + value pairs) | Keep Only Set | Transforms fields | Any JSON | Modified JSON | Field manipulation |
| Code | Code (JavaScript or Python) | Mode (Run Once / Run Per Item) | Executes custom code | Any JSON | Any JSON | Custom transformation |
| IF | Condition, Value1, Operation, Value2 | Combine Conditions | Routes based on condition | Any JSON | Same JSON (routed) | Conditional routing |
| OpenAI | Resource, Operation ("Generate a Chat Completion", formerly "Message a Model"), Model, Messages | Options (temperature, max tokens) | Calls OpenAI API | Prompt data | AI response | Text generation |
| Switch | Rules | Mode | Multi-way routing | Any JSON | Same JSON (routed) | Multi-route |
| Merge | Mode | Options | Combines data streams | Multiple items | Merged items | Data combination |
| Split In Batches | Batch Size | Options | Splits into batches | Array | Batches | Array splitting |
| Wait | Amount, Unit | Resume | Pauses workflow | Any JSON | Same JSON (delayed) | Time delay |
| XML | Property Name, Direction | — | Converts XML ↔ JSON | XML string or JSON | JSON or XML string | Format conversion |
| Notion | Resource (Database Page, Block, Page, Data Source), Operation | — | Notion API calls | n8n data | Notion response | Database operations |
```

> 💡 **Tip:** n8n renames and restructures node operations regularly (the OpenAI and Notion nodes above both changed their operation names in 2025-2026). If a node in your workflow looks different from what a teammate describes, check the node's official docs page under [n8n's integrations library](https://docs.n8n.io/integrations/) before assuming you configured it wrong. It's often just a version difference.

----

## Submission Guidelines


## Extension Activities (Optional)

1. **Analyze more nodes:** Study additional nodes (Google Sheets, Slack, etc.)
2. **Create node combinations:** Document common node patterns
3. **Build debugging guide:** Create guide for troubleshooting node issues
4. **Performance analysis:** Measure node execution times
5. **Create templates:** Build reusable node configurations

---

## Resources

- [n8n Node Documentation](https://docs.n8n.io/integrations/)
- [n8n Expressions Guide](https://docs.n8n.io/code/expressions/)
- [n8n Community Forum](https://community.n8n.io/)

---

## Troubleshooting

**Issue:** Node not transforming data as expected
- **Solution:** Check expressions use correct syntax (`{{ $json.field }}`), verify data structure matches expectations

**Issue:** JSON structure unclear
- **Solution:** Use a Set node to isolate and inspect specific fields, add a Code node to `console.log` the structure, check the execution output panel by clicking the node after running

**Issue:** Node parameters confusing
- **Solution:** Read node-specific documentation, test with simple data first, use node tooltips

## Verify

The reviewer can inspect one run trace and see the observable output in the destination.

## Explain

What is the first failure mode you would monitor if this workflow ran daily?

## Submission Sanity Check

Before you submit:
- Keep only files for this lab.
- Name files clearly.
- Remove secrets, API keys, tokens, and unrelated data.
- Make `lab_proof.md` the entry point for the reviewer.

## Optional Stretch

- Add one operational control: retry handling, error notification, duplicate detection, audit logging, or a second route.
- Create a small UI with vibecoding only if it safely submits or previews the workflow input. Deploy only if no credentials are exposed.
