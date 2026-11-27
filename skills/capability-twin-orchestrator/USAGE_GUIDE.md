# Capability Twin Orchestrator Skill Usage Guide

This guide provides detailed information on how to use the Capability Twin Orchestrator skill effectively.

## Basic Usage

The Capability Twin Orchestrator skill is designed to coordinate complete Capability Twin workflows following the 5-layer enterprise architecture framework.

### Simple Workflow Coordination

```python
result = Skill("capability-twin-orchestrator", config={
    "workflow_type": "analysis",
    "input_data": requirements,
    "target_domain": "Odoo 19"
})
```

### Advanced Usage

For more complex workflow coordination, you can specify additional parameters:

```python
result = Skill("capability-twin-orchestrator", config={
    "workflow_type": "integration",
    "input_data": requirements,
    "target_domain": "Odoo 19",
    "max_steps": 10,
    "parallel_execution": true
})
```

## Workflow Types

### 1. Analysis Workflows

Coordinate analysis workflows:
- Ecosystem discovery steps
- Technical analysis tasks
- Function analysis procedures
- Domain analysis processes

### 2. Integration Workflows

Coordinate integration workflows:
- Supply-side analysis
- Demand-side analysis
- Capability extraction
- Custom capability generation

### 3. Solution Workflows

Coordinate solution workflows:
- Implementation planning
- Architecture design
- Development coordination
- Quality assurance

## Best Practices

1. Use appropriate workflow types for your needs
2. Maintain clear workflow state and progress tracking
3. Implement error handling and recovery mechanisms
4. Use parallel execution when appropriate
5. Document workflow decisions and progress
6. Keep business scenarios in `.feature` files — never duplicate them in deliverables

## Business Scenario Gate (Gherkin BDD)

Every workflow runs a spec gate before analysis and again at Step 10→11:

```python
Skill("capability-twin-orchestrator", config={
    "target_module": "mrp",
    "workflow_type": "full_analysis",
    "bdd": {"enabled": True, "blocking": True}
})
```

- `status: blocked` + `blocked_at` means a spec error stopped the pipeline; fix
  `skills/gherkin-bdd/features/<module>/*.feature` and rerun.
- `satisfies_module: false` means no spec exists for that module (the gate fell back to the
  repo baseline). Analysis may continue, but scenario-dependent deliverables are skipped.
- `render_deliverables_bundle` derives `scenario_ids`, `gherkin_feature`,
  `generated_uat_table` and related fields from the spec and reports `blocked_templates`
  for anything it refused to render.
- Drafts only: `{"bdd": {"blocking": false}}` records the failure without stopping the run.
  It is not a way to claim G2/G3 completion.

## Ontology Context Layer

Every workflow attaches a bounded, anchored ontology subgraph to `shared_context["ontology"]`
before sub-agents run. It is enabled by default; no extra step or skill is required.

```python
Skill("capability-twin-orchestrator", params={
    "target_module": "mrp",
    "workflow_type": "full_analysis",
    "ontology": {"enabled": True, "hops": 1, "max_nodes": 40}
})
```

- `status: ok` — subgraph ready; `nodes` carry `source_anchor` and can be cited directly.
- `status: open-question` — ontology is built but has no node for this module; do not
  claim the module was analyzed from semantic evidence.
- `status: unavailable` — `ontology/manifest.json` or the query script is missing.
  Build it with `python scripts/build_ontology.py --source "$ODOO_SOURCE_PATH" --out ontology`.
- `status: disabled` — only via explicit `ontology.enabled=false` (draft use).

The ontology never satisfies step evidence and never changes workflow status; it only
reduces the source exploration AI has to do. The result contains `ontology_context` as a
fingerprint, while the full subgraph remains in `final_shared_context["ontology"]`.

## Common Use Cases

### Ecosystem Analysis
- Coordinate ecosystem discovery workflows
- Manage multi-step analysis processes
- Track analysis progress and results
- Integrate analysis results

### Capability Development
- Coordinate capability extraction workflows
- Manage solution development processes
- Track capability progress and implementation
- Validate capability completeness

### System Integration
- Coordinate integration workflows
- Manage cross-domain analysis processes
- Track integration progress and results
- Validate integration quality

## Error Handling

The skill provides detailed error messages for:
- Invalid workflow types
- Missing input parameters
- Workflow execution failures
- State management issues

## Performance Considerations

- For complex workflows, consider step batching
- Batch workflow coordination operations when possible
- Monitor workflow progress and performance
- Implement checkpointing for long-running workflows