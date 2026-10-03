---
name: investigate_shipment
description: Investigate a pharmaceutical shipment by tracing its governed cold-chain ontology and collecting sensor, shipment, batch, supplier, regulatory, and SOP evidence.
---

# Investigate Shipment

## Purpose

Investigate a pharmaceutical shipment by tracing its governed ontology relationships and collecting evidence required for cold-chain compliance assessment.

## Inputs

- shipment_id
- investigation_reason
- optional batch_id
- optional supplier_lot_id

## Allowed Tools

- Read-only Snowflake SQL queries against approved governed objects
- Cortex Search for approved regulatory and SOP evidence
- CoCo CLI evidence capture
- Read-only access to compliance audit records

## Access Policy

This skill MUST operate using the role and privileges of the current investigation session.

NEVER switch roles, activate secondary roles, escalate privileges, or use ACCOUNTADMIN to bypass an authorization failure.

If the current role cannot access a required source, record the source as unresolved and continue using the approved governed views available to the current role.

Never bypass masking policies or row-access policies.

Do not retrieve masked sensor values from RAW_PAYLOAD or another underlying column when the governed sensor view intentionally masks those values.

## Approved Evidence Paths

Prefer governed Gold and secure views over direct Bronze access.

Approved objects include:

- COLD_CHAIN_COMPLIANCE.GOLD.GOLD_COMPLIANCE_FACTS
- COLD_CHAIN_COMPLIANCE.GOLD.SV_SHIPMENT_COMPLIANCE
- COLD_CHAIN_COMPLIANCE.GOLD.SV_COLD_CHAIN_ONTOLOGY
- COLD_CHAIN_COMPLIANCE.GOLD.SV_SHIPMENT_EVIDENCE
- COLD_CHAIN_COMPLIANCE.GOLD.SV_REGULATORY_EVIDENCE
- COLD_CHAIN_COMPLIANCE.GOLD.REGULATORY_EVIDENCE
- COLD_CHAIN_COMPLIANCE.GOLD.VW_QUALITY_SENSOR_EVIDENCE when the current role is authorized
- COLD_CHAIN_COMPLIANCE.GOLD.GOLD_COMPLIANCE_BREACHES
- COLD_CHAIN_COMPLIANCE.GOVERNANCE.AUDIT_COMPLIANCE_DECISIONS
- COLD_CHAIN_COMPLIANCE.GOVERNANCE.LEGACY_COMPLIANCE_DEFINITIONS

Direct Bronze access is permitted only when the current role is explicitly authorized for that object.

## Investigation Path

Follow the governed ontology:

Supplier Lot -> Part Batch -> IoT Sensor Stream -> Shipment -> Order -> Customer -> Regulatory Clause

For a shipment investigation:

1. Resolve the shipment through an approved governed object.
2. Identify the associated order and customer.
3. Resolve the associated part batch.
4. Resolve the supplier lot.
5. Retrieve the associated IoT temperature evidence through an approved governed sensor view.
6. Calculate or retrieve the observed temperature range and duration of any threshold excursion.
7. Retrieve applicable regulatory clauses and approved SOP evidence.
8. Retrieve the governed compliance definition and current compliance facts.
9. Retrieve relevant audit records and automated breach records.
10. Record all evidence references.

## Evidence Requirements

The investigation MUST distinguish:

- ERP shipment status
- observed IoT sensor evidence
- governed compliance definition
- regulatory/SOP evidence
- automated breach evidence
- audit evidence

Do not treat an ERP status such as "Compliant" as proof of regulatory compliance.

Temperature evidence MUST include when authorized and available:

- shipment_id
- timestamp
- observed temperature
- allowed temperature range
- excursion start
- excursion end
- excursion duration
- maximum observed temperature

Regulatory evidence MUST include:

- source document
- applicable clause
- page or section reference
- retrieved evidence text

## Decision Policy

This skill does not make the final compliance decision.

It produces the evidence package required by assess_cold_chain_compliance.

Never infer missing sensor readings, regulatory requirements, causes, or business decisions.

If required evidence is missing, masked, inaccessible, stale, or contradictory, explicitly mark the evidence as unresolved and identify the limitation.

## Escalation Conditions

Escalate the investigation by reporting the evidence gap, NOT by escalating Snowflake privileges, when:

- shipment identity cannot be resolved
- sensor data is missing for the required window
- required governed evidence is inaccessible
- timestamps are inconsistent
- multiple conflicting regulatory clauses apply
- the applicable compliance definition cannot be resolved
- evidence sources materially disagree

## Expected Output

Return a structured investigation package containing:

- shipment_id
- order_id
- customer_id
- batch_id
- supplier_lot_id
- ERP_status
- sensor_summary
- excursion_events
- regulatory_evidence
- sop_evidence
- evidence_conflicts
- missing_evidence
- evidence_references
- investigation_status

The output must be evidence-grounded and suitable for downstream compliance assessment.
