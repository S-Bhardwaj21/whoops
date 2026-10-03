---
name: execute_compliance_resolution
description: Execute an authorized cold-chain compliance resolution while preserving evidence, approvals, and an append-only audit record.
---

# Execute Compliance Resolution

## Purpose

Execute the approved operational resolution for a cold-chain compliance assessment while preserving an auditable record of the decision, evidence, and definition version used.

## Inputs

- shipment_id
- compliance assessment
- metric_definition_version
- sensor evidence
- regulatory evidence
- SOP evidence
- resolution action

## Allowed Tools

- Snowflake SQL for approved resolution operations
- CoCo CLI evidence capture
- Compliance audit table
- Governed compliance facts
- Approved regulatory and SOP evidence

## Access Policy

This skill MUST operate using the role and privileges of the current session.

NEVER:
- switch roles
- activate secondary roles
- use ACCOUNTADMIN to bypass an authorization failure
- request or grant additional privileges
- bypass masking policies
- access underlying evidence through an unapproved path
- modify source shipment or sensor data to execute a resolution

If the current role cannot perform an authorized operation, report the authorization failure and stop. Do not escalate privileges.

## Resolution Policy

This skill executes a resolution only after `assess_cold_chain_compliance` has produced a definitive result.

Allowed compliance outcomes:

- `COMPLIANT`
- `NON_COMPLIANT`
- `UNDETERMINED`

`UNDETERMINED` cases must not be automatically treated as compliant or non-compliant.

## Resolution Actions

### COMPLIANT

When the shipment is compliant:

- record the compliant determination
- preserve the supporting sensor evidence
- preserve the applicable definition version
- record the regulatory/SOP evidence
- close the compliance exception only when the authorized resolution policy permits closure

### NON_COMPLIANT

When the shipment is non-compliant:

- record the non-compliant determination
- preserve the excursion evidence
- preserve the applicable regulatory/SOP evidence
- create a new resolution audit record
- route the shipment for Quality review when required
- prevent automatic closure of the exception

Do not modify or overwrite the original compliance assessment.

### UNDETERMINED

When evidence is insufficient:

- record the unresolved status when authorized
- identify missing evidence
- route for human review
- do not make assumptions
- do not close the exception

## Authorization

Never execute an operational action that is outside the explicitly authorized resolution policy.

If the requested action requires human approval, stop before execution and return:

- required approval
- reason approval is required
- evidence supporting the request
- current compliance status

Do not represent a pending approval as an executed resolution.

## Audit Requirements

Every completed resolution must create a new audit record containing:

- shipment_id
- compliance_status
- resolution_action
- metric_definition_version
- sensor_evidence_reference
- regulatory_evidence_reference
- SOP_evidence_reference
- actor_or_agent
- resolution_timestamp
- resolution_status

Audit history is append-only.

NEVER:
- UPDATE an existing audit record
- DELETE an existing audit record
- overwrite an existing audit record
- reuse an existing audit_id for a new resolution
- silently replace a previous decision

Each new resolution execution must receive a new unique audit record reference.

The audit record must allow a reviewer to reconstruct why the resolution occurred.

When writing the audit record, use only the privileges available to the current session.

If the current role cannot write the audit record, report the failure and stop. Do not switch roles or escalate privileges.

Do not claim that the audit table is universally immutable merely because the current session successfully inserted a record. Report immutability only in terms of the enforced append-only access boundary used by the resolution session.

## Evidence Integrity

Never modify, delete, or overwrite the original evidence used for the compliance determination.

Prefer governed evidence references and secure views over direct raw Bronze evidence.

If new evidence changes a previous determination:

1. create a new assessment
2. reference the previous assessment
3. record the new definition version if applicable
4. create a new audit record
5. preserve both audit records

Never silently replace a previous decision.

## Source Data Protection

Resolution execution MUST NOT modify:

- shipment records
- IoT sensor readings
- raw sensor payloads
- governed compliance facts
- regulatory evidence
- SOP evidence
- previous audit records

Resolution actions are recorded as new audit events rather than by rewriting source or historical records.

## Failure Handling

If a resolution operation fails:

- do not report the resolution as completed
- preserve the compliance assessment
- do not modify source data
- do not modify existing audit records
- record the failure only through an authorized append-only audit operation when available
- return the failure reason
- require retry or human intervention as appropriate

If an audit write succeeds but a later verification fails, report the resolution as requiring verification rather than silently retrying with an update or overwrite.

## Output

Return:

- shipment_id
- previous_compliance_status
- final_compliance_status
- resolution_action
- resolution_status
- metric_definition_version
- audit_record_reference
- evidence_references
- approval_required
- failure_reason
- source_data_modified
- previous_audit_records_modified
- privileges_escalated

## Completion Criteria

A resolution is complete only when:

1. the compliance assessment is definitive
2. the requested action is authorized
3. the action succeeds
4. a new audit record is successfully written
5. all evidence references are preserved
6. source shipment and sensor data remain unmodified
7. previous audit records remain unmodified
8. no privileges were escalated

Never claim successful resolution when any of these conditions has failed.