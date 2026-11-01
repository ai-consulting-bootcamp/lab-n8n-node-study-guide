# Official documentation checked

Checked during this lab on 2026-11-02 (Asia/Jerusalem). Runtime/node versions are recorded in the proof and workflow exports; documentation can evolve independently.

| Node or topic | Official reference |
| --- | --- |
| Manual Trigger | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.manualworkflowtrigger/ |
| Edit Fields (Set) | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.set/ |
| IF | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.if/ |
| Split Out | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitout/ |
| Remove Duplicates | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.removeduplicates/ |
| Sort | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.sort/ |
| Limit | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.limit/ |
| Switch | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.switch/ |
| Merge | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.merge/ |
| Aggregate | https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.aggregate/ |
| AI Agent | https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/ |
| Pinecone Vector Store | https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.vectorstorepinecone/ |
| Cohere Reranker | https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.rerankercohere/ |
| OpenAI Chat Model | https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatopenai/ |
| Simple Memory | https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.memorybufferwindow/ |
| Node controls/settings | https://docs.n8n.io/build/understand-workflows/workflow-components/work-with-nodes.md |
| Server CLI | https://docs.n8n.io/deploy/host-n8n/configure-n8n/use-the-command-line.md |

The implementation uses Set JSON Output mode and IF Boolean validation, not outdated Set `keepOnlySet` or older IF `value1` parameter syntax. For each local node, its exact serialized parameters are in the executed workflow JSON. No authentication is required for the ten local node types. Workflow execution order is v1. Unless explicitly set, node-level settings (retry, always-output-data, execute-once, error handling) remain defaults; these are different from operation parameters and node-specific options.
