"""Check recorded execution evidence; does not simulate or rerun n8n."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load(name):
    return json.loads((ROOT / name).read_text())

def run_data(name):
    execution = load(f'evidence/{name}-execution.json')
    assert execution['status'] == 'success' and execution['finished'] is True
    assert not execution['data']['resultData'].get('error')
    return execution['data']['resultData']['runData']

def items(data, node, branch=0):
    assert data[node][0]['executionStatus'] == 'success'
    return [item['json'] for item in data[node][0]['data']['main'][branch]]

def main():
    valid, invalid, study = (run_data(name) for name in ('valid', 'invalid', 'nodes'))
    assert list(valid) == ['Manual Trigger', 'Edit Fields (Set)', 'IF (Validation)', 'Structured Output']
    assert list(invalid) == ['Manual Trigger', 'Edit Fields (Set)', 'IF (Validation)', 'Rejection Output']
    assert items(valid, 'Edit Fields (Set)') == [load('sample_input.json')]
    assert items(valid, 'IF (Validation)') == [load('sample_input.json')]
    assert items(valid, 'IF (Validation)', 1) == []
    assert items(valid, 'Structured Output') == [load('sample_output.json')]
    assert load('sample_output.json') == {**load('sample_input.json'), 'status': 'accepted', 'queue': 'portal-support'}
    assert items(invalid, 'Edit Fields (Set)') == [load('evidence/invalid_input.json')]
    assert items(invalid, 'IF (Validation)') == []
    assert items(invalid, 'IF (Validation)', 1) == [load('evidence/invalid_input.json')]
    assert items(invalid, 'Rejection Output') == [load('evidence/invalid_output.json')]
    assert load('evidence/invalid_output.json')['status'] == 'rejected'
    config = load('study/local_nodes.json')
    types = {node['type'] for node in config['nodes'] if node['name'] in study}
    assert len(types) == 10
    assert len(items(study, 'Split Out')) == 3
    assert len(items(study, 'Remove Duplicates')) == 2
    assert [item['rank'] for item in items(study, 'Sort')] == [1, 2]
    assert items(study, 'Limit') == [{'ticket_id': 'T-001', 'rank': 1}]
    assert items(study, 'Switch', 1) == []
    merged = items(study, 'Merge')
    assert [item['label'] for item in merged] == ['A', 'B']
    assert items(study, 'Aggregate') == [{'records': merged}]
    for name, data in (('valid', valid), ('invalid', invalid), ('nodes', study)):
        for node, runs in data.items():
            for run in runs:
                assert run['executionStatus'] == 'success'
                for source in run.get('source', []):
                    previous = data[source['previousNode']][source.get('previousNodeRun', 0)]
                    assert previous['executionIndex'] < run['executionIndex']
                    assert previous['data']['main'][source.get('previousNodeOutput', 0)]
    print('PASS: 3 real n8n traces, both IF routes, exact input/output mapping, 10 executed node types, study transformations, and predecessor links.')

if __name__ == '__main__':
    main()
