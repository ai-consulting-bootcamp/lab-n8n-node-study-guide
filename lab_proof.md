# Lab proof

The [data mapping workflow](node-study-data-mapping.json) takes a sample lead, maps it to a smaller record, and inserts it into the Lab Lead Records table. The export references the table in the original n8n project.

## Input payload

```json
{
  "request_id": "lab-001",
  "name": "Marta",
  "email": "marta@example.com",
  "company_size": 120,
  "source": "lab"
}
```

## Execution

[Execution #1595](evidence/execution-1595.png) succeeded in 29 ms. The manual trigger started the run. Create Sample Input produced one item, Map Lead Record reshaped it, and Save Lead Record inserted one row.

The mapping carries the request ID forward as the lead ID so the saved row can be traced back to its input. The contact fields match the destination column names. A company size of at least 50 produces high priority. Smaller companies receive normal priority. The output omits the source and company size because the table stores the resulting priority.

## Output record

```json
{
  "lead_id": "lab-001",
  "contact_name": "Marta",
  "contact_email": "marta@example.com",
  "priority": "high",
  "id": 1,
  "createdAt": "2026-11-03T23:13:45.867Z",
  "updatedAt": "2026-11-03T23:13:45.867Z"
}
```

The [table view](evidence/lead-record.png) shows the persisted row. Its timestamp is displayed in local time.

The first issue I would monitor in a daily run is duplicate lead IDs. Insert creates a new row each time, so a retry can store the same request twice. A count of repeated lead IDs would make that visible.

The [node analysis](node_analysis.md) covers the data mapping, agent chat and PDF RAG workflows.
