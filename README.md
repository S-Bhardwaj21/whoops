# WHOOPS

## Cold Chain Compliance Ontology for Pharma GCCs

**A governed, evidence-grounded compliance decision system built on
Snowflake**

WHOOPS is a Snowflake-native cold-chain compliance platform designed
around a simple operational problem:

> Different enterprise systems can answer the same compliance question
> differently because they use different definitions, evidence, and
> decision logic.

The system establishes a governed definition of cold-chain compliance,
connects that definition to the underlying shipment ontology and sensor
evidence, and exposes the resulting decision through governed Snowflake
objects, Cortex capabilities, CoCo skills, automated breach detection,
and a Streamlit command center.

The reference scenario is pharmaceutical shipment `SH-101`, where an ERP
system reports `COMPLIANT - DELIVERED`, while the governed cold-chain
rule identifies a temperature excursion that makes the shipment
`NON_COMPLIANT`.

------------------------------------------------------------------------

## 1. Executive Summary

WHOOPS treats compliance as a **data governance problem first and an AI
problem second**.

Instead of allowing each application, team, or AI workflow to
independently interpret the word "compliant", the platform defines one
canonical decision model and makes the evidence behind that decision
queryable.

For shipment `SH-101`:

  Signal                         Result
  ------------------------------ -------------------------
  ERP delivery status            `COMPLIANT - DELIVERED`
  Maximum observed temperature   `9.00 C`
  Allowed maximum                `8.00 C`
  Excursion duration             `14 minutes`
  Allowed excursion              `< 10 minutes`
  Governed decision              `NON_COMPLIANT`
  Definition version             `CC-COLDCHAIN-001`

The system can explain the decision using:

1.  The governed compliance definition.
2.  The underlying sensor evidence.
3.  The applicable internal cold-chain handling evidence.
4.  The audit record that preserves the decision context.

The architecture also demonstrates:

-   Snowflake Bronze/Silver/Gold data modeling.
-   Semantic Views for governed analytical definitions.
-   Cortex Search for evidence retrieval.
-   Cortex Analyst for natural-language analytical questions.
-   Cortex AI_COMPLETE for concise evidence-grounded explanations.
-   Snowflake Streams and Tasks for automated breach detection.
-   RBAC and masking for persona-specific access.
-   Audit records for compliance decisions and resolutions.
-   CoCo Skills for structured investigation and resolution workflows.
-   Streamlit for an operational command center.

------------------------------------------------------------------------

# 2. The Problem

Cold-chain pharmaceutical operations span multiple systems:

``` text
Supplier
   |
Supplier Lot
   |
Part / Product Batch
   |
IoT Sensor Stream
   |
Shipment
   |
Order
   |
Customer
   |
Quality / Regulatory Evidence
```

The operational problem is that these systems do not necessarily share
the same definition of compliance.

A shipment can simultaneously appear as:

``` text
ERP                 -> COMPLIANT - DELIVERED
Operations          -> NON_COMPLIANT
Quality              -> NON_COMPLIANT
Governed Definition  -> NON_COMPLIANT
```

This creates several risks:

-   contradictory operational decisions;
-   manual reconciliation;
-   slow quality investigations;
-   inconsistent AI answers;
-   weak auditability;
-   inability to explain which definition produced a decision.

WHOOPS addresses the root issue by making the compliance definition
itself a governed data object.

------------------------------------------------------------------------

# 3. Core Design Principle

## Compliance is a governed definition, not a free-form AI opinion.

The AI layer does not invent the compliance rule.

Instead:

``` text
Governed Definition
        |
        v
Structured Evidence
        |
        v
Deterministic Decision
        |
        v
AI Explanation
```

This separation is intentional.

The deterministic layer establishes the decision.

The AI layer retrieves, explains, investigates, and communicates the
decision.

This makes the system easier to audit and reduces the risk of an LLM
silently inventing compliance criteria.

------------------------------------------------------------------------

# 4. Canonical Compliance Rule

The reference policy implemented by WHOOPS is:

``` text
A shipment is COMPLIANT when:

MAX observed temperature <= 8 C

AND

duration above 8 C < 10 minutes
```

Therefore:

``` text
MAX temperature > 8 C
OR
excursion duration >= 10 minutes

=> NON_COMPLIANT
```

For `SH-101`:

``` text
Maximum temperature = 9.00 C
Allowed maximum     = 8.00 C

Excursion duration  = 14 minutes
Allowed duration     = < 10 minutes
```

Both criteria fail.

The governed definition is versioned as:

``` text
CC-COLDCHAIN-001
```

The version is recorded alongside the decision so that the meaning of a
historical decision remains identifiable.

------------------------------------------------------------------------

# 5. Reference Architecture

``` text
                         COLD CHAIN COMPLIANCE PLATFORM
                                      |
        +-----------------------------+-----------------------------+
        |                             |                             |
        v                             v                             v
   Raw Enterprise                 Sensor Evidence              Policy /
   Data Sources                   IoT Temperature              SOP Evidence
        |                             |                             |
        +-----------------------------+-----------------------------+
                                      |
                                      v
                              BRONZE LAYER
                                      |
                                      v
                              SILVER LAYER
                         Normalized Compliance Events
                                      |
                                      v
                               GOLD LAYER
                                      |
                 +--------------------+--------------------+
                 |                    |                    |
                 v                    v                    v
          Compliance Facts      Evidence Chunks       Breach Events
                 |                    |                    |
                 +--------------------+--------------------+
                                      |
                                      v
                           GOVERNED SEMANTIC VIEWS
                                      |
                 +--------------------+--------------------+
                 |                    |                    |
                 v                    v                    v
           Cortex Analyst      Cortex Search        AI_COMPLETE
                 |                    |                    |
                 +--------------------+--------------------+
                                      |
                                      v
                              CoCo Skills
                                      |
                                      v
                         Streamlit Command Center
                                      |
                                      v
                            Governance / Audit
```

------------------------------------------------------------------------

# 6. Data Architecture

WHOOPS uses a Bronze/Silver/Gold structure.

## Bronze

Bronze contains the source-oriented entities:

-   `SHIPMENTS`
-   `IOT_TEMP_LOGS`
-   `ORDERS`
-   `CUSTOMERS`
-   `PART_BATCHES`
-   `SUPPLIER_LOTS`

Raw sensor payloads are preserved in `RAW_PAYLOAD`.

The Bronze schema is defined in:

``` text
sql/01_bronze.sql
```

------------------------------------------------------------------------

## Silver

Silver creates a normalized compliance event representation.

The primary table is:

``` text
COLD_CHAIN_COMPLIANCE.SILVER.STG_COMPLIANCE_EVENTS
```

It consolidates:

-   shipment;
-   order;
-   batch;
-   supplier lot;
-   supplier;
-   customer;
-   sensor;
-   event time range;
-   maximum temperature;
-   duration above threshold;
-   reading count.

Schema definition:

``` text
sql/02_silver.sql
```

------------------------------------------------------------------------

## Gold

Gold contains decision-ready and evidence-oriented objects.

### `GOLD_COMPLIANCE_FACTS`

Stores the governed compliance result and its supporting metrics.

Key fields include:

``` text
SHIPMENT_ID
ORDER_ID
BATCH_ID
SUPPLIER_LOT_ID
CUSTOMER_ID
ERP_STATUS
MAX_TEMPERATURE_C
ALLOWED_MAX_TEMPERATURE_C
MINUTES_ABOVE_THRESHOLD
ALLOWED_EXCURSION_MINUTES
COMPLIANCE_STATUS
METRIC_DEFINITION_VERSION
DECISION_REASON
```

### `REGULATORY_EVIDENCE`

Stores evidence references used to support compliance investigations.

### `COMPLIANCE_DOCUMENT_CHUNKS`

Provides searchable evidence for Cortex Search.

### `GOLD_COMPLIANCE_BREACHES`

Stores automatically detected temperature breaches.

Gold definitions and secure views are maintained in:

``` text
sql/03_gold.sql
```

------------------------------------------------------------------------

# 7. Cold-Chain Ontology

The system models the business relationship explicitly:

``` text
Supplier Lot
    |
    v
Part Batch
    |
    v
IoT Sensor Stream
    |
    v
Shipment
    |
    v
Order
    |
    v
Customer
    |
    v
Regulatory / Compliance Evidence
```

For the reference scenario:

``` text
SUP-501
   |
LOT-501
   |
B-12
   |
SH-101
   |
ORD-101
   |
CUST-101
```

The ontology allows a natural-language investigation to move from a
compliance decision back through the business entities and evidence that
produced it.

The ontology is exposed through:

``` text
SV_COLD_CHAIN_ONTOLOGY
```

------------------------------------------------------------------------

# 8. Semantic Views

WHOOPS uses five Semantic Views as the governed analytical interface.

## 1. `SV_SHIPMENT_COMPLIANCE`

The canonical compliance interface.

Exposes:

-   shipment;
-   order;
-   batch;
-   supplier lot;
-   customer;
-   ERP status;
-   compliance status;
-   maximum temperature;
-   excursion duration;
-   definition version;
-   decision reason.

------------------------------------------------------------------------

## 2. `SV_SHIPMENT_EVIDENCE`

Connects the compliance result to its underlying measurements.

------------------------------------------------------------------------

## 3. `SV_COMPLIANCE_AUDIT`

Exposes the compliance decision and resolution audit trail.

------------------------------------------------------------------------

## 4. `SV_COLD_CHAIN_ONTOLOGY`

Represents the relationships between:

``` text
Supplier Lot -> Batch -> Shipment -> Order -> Customer
```

------------------------------------------------------------------------

## 5. `SV_REGULATORY_EVIDENCE`

Provides the evidence layer used by compliance investigations.

All five are defined in:

``` text
sql/04_semantic.sql
```

------------------------------------------------------------------------

# 9. Cortex Intelligence Layer

WHOOPS uses multiple Cortex capabilities for different jobs rather than
treating an LLM as the entire decision engine.

## Cortex Analyst

Cortex Analyst is used for natural-language analytical questions against
the governed semantic model.

Example:

``` text
Why is shipment SH-101 non-compliant?
```

The resulting analysis identifies:

-   `NON_COMPLIANT` status;
-   maximum temperature of `9.00 C`;
-   excursion duration of `14 minutes`;
-   allowed maximum of `8 C`;
-   allowed excursion threshold;
-   ERP status conflict;
-   decision reason.

The key design choice is that the question is grounded in the Semantic
View rather than an arbitrary collection of raw tables.

------------------------------------------------------------------------

## Cortex Search

Cortex Search indexes compliance evidence stored in:

``` text
GOLD.COMPLIANCE_DOCUMENT_CHUNKS
```

The search service is:

``` text
GOLD.COMPLIANCE_EVIDENCE_SEARCH
```

It supports evidence retrieval for investigation and explanation.

The repository definition is:

``` text
sql/05_search.sql
```

------------------------------------------------------------------------

## Cortex AI_COMPLETE

AI_COMPLETE is used for concise evidence-grounded explanation.

The model receives supplied evidence and is instructed not to infer:

-   motives;
-   undocumented causes;
-   missing system behavior;
-   unsupported regulatory claims.

The purpose is explanation, not autonomous invention of the compliance
rule.

------------------------------------------------------------------------

# 10. Evidence Model

WHOOPS separates the decision from the evidence supporting it.

For the reference shipment:

``` text
Evidence ID:
EVID-CC-001

Document:
Cold Chain Handling SOP

Clause:
CC-4.2 Temperature Excursion

Page:
42

Source type:
INTERNAL_SOP
```

The evidence states that refrigerated pharmaceutical shipments must
remain at or below `8 C`, and that an excursion above `8 C` lasting
`10 minutes or more` is considered non-compliant and requires Quality
review.

This is a **synthetic internal SOP used for the demonstration**.

It is intentionally not represented as an FDA regulation.

The architecture can accommodate regulatory documents, but this
repository does not claim that the demonstration SOP is itself an FDA
legal requirement.

------------------------------------------------------------------------

# 11. Automated Breach Detection

WHOOPS uses Snowflake Streams and Tasks to demonstrate event-driven
compliance monitoring.

## Stream

``` text
GOVERNANCE.IOT_TEMP_LOGS_STREAM
```

The stream captures new sensor events.

## Task

``` text
GOVERNANCE.TASK_DETECT_COLD_CHAIN_BREACHES
```

The task evaluates newly arrived temperature events.

When a temperature exceeds the configured threshold, a breach record is
written to:

``` text
GOLD.GOLD_COMPLIANCE_BREACHES
```

The reference automated event is:

``` text
BREACH-EVT-101-AUTO-001
```

with:

``` text
Shipment:   SH-101
Sensor:     SENSOR-101
Observed:   9.00 C
Threshold:  8.00 C
Type:       TEMPERATURE_ABOVE_THRESHOLD
Status:     OPEN
```

This demonstrates the transition from:

``` text
IoT Event
    ->
Stream
    ->
Task
    ->
Governed Breach Record
```

------------------------------------------------------------------------

# 12. Governance and Security

Governance is implemented as part of the architecture rather than added
after the AI layer.

## Roles

The project defines dedicated roles:

``` text
COLD_CHAIN_QUALITY
COLD_CHAIN_LOGISTICS
COLD_CHAIN_AUDIT_WRITER
```

------------------------------------------------------------------------

## Quality Access

Quality users can access authorized sensor evidence, including unmasked
temperature values.

The governed sensor interface is:

``` text
GOLD.VW_QUALITY_SENSOR_EVIDENCE
```

------------------------------------------------------------------------

## Logistics Access

Logistics users receive a governed compliance interface:

``` text
GOLD.VW_LOGISTICS_COMPLIANCE
```

The interface exposes operational compliance information without
granting unrestricted access to raw sensor measurements.

------------------------------------------------------------------------

## Dynamic Masking

Raw temperature data is protected using a masking policy:

``` text
GOVERNANCE.MASK_RAW_TEMPERATURE
```

The policy is associated with the:

``` text
GOVERNANCE.DATA_SENSITIVITY
```

tag.

The important distinction is:

``` text
Quality
    ->
authorized raw temperature evidence

Logistics
    ->
governed compliance information
```

This allows the application to demonstrate persona-aware access without
duplicating the underlying dataset.

------------------------------------------------------------------------

# 13. Audit Trail

Compliance decisions are recorded in:

``` text
GOVERNANCE.AUDIT_COMPLIANCE_DECISIONS
```

Important fields include:

``` text
AUDIT_ID
SHIPMENT_ID
COMPLIANCE_STATUS
RESOLUTION_ACTION
METRIC_DEFINITION_VERSION
SENSOR_EVIDENCE_REF
REGULATORY_EVIDENCE_REF
DECISION_REASON
ACTOR
DECIDED_AT
AUDIT_STATUS
```

The audit record captures not only the decision but also:

-   which metric definition was active;
-   which sensor evidence supported the decision;
-   which compliance evidence was referenced;
-   who performed the action;
-   when it occurred.

The audit-writing role is intentionally restricted to `SELECT` and
`INSERT`.

For controlled audit-writing sessions using:

``` sql
USE SECONDARY ROLES NONE;
```

the audit writer cannot update or delete existing audit records.

This is an append-only operational pattern, not a claim that Snowflake
makes the table universally immutable under every possible
administrative privilege.

------------------------------------------------------------------------

# 14. CoCo Skills

The project includes three project-specific CoCo Skills:

``` text
.cortex/skills/
├── assess_cold_chain_compliance/
├── execute_compliance_resolution/
└── investigate_shipment/
```

## `investigate_shipment`

Purpose:

-   trace the cold-chain ontology;
-   collect governed evidence;
-   retrieve supporting documentation;
-   inspect audit context;
-   respect the current session's privileges.

The skill explicitly avoids privilege escalation and role switching.

------------------------------------------------------------------------

## `assess_cold_chain_compliance`

Purpose:

-   apply the canonical compliance rule;
-   evaluate available evidence;
-   distinguish definitive findings from insufficient evidence;
-   return `UNDETERMINED` when the evidence is insufficient.

The skill does not bypass governance controls to manufacture a
definitive answer.

------------------------------------------------------------------------

## `execute_compliance_resolution`

Purpose:

-   execute an authorized resolution only after a definitive assessment;
-   preserve source data;
-   create a new audit record;
-   retain evidence references;
-   stop when authorization is insufficient.

Human authorization is required before a pending resolution is executed.

------------------------------------------------------------------------

# 15. Streamlit Command Center

The Streamlit application is the operational interface for the system.

Location:

``` text
app/app.py
```

The command center provides:

### Governed Decision

Displays:

``` text
NON_COMPLIANT
```

along with:

-   maximum temperature;
-   allowed threshold;
-   excursion duration;
-   allowed excursion;
-   definition version.

### System Conflict

Shows the different interpretations represented in the demo:

``` text
ERP          -> COMPLIANT - DELIVERED
Operations   -> NON_COMPLIANT
Quality      -> NON_COMPLIANT
Governed     -> NON_COMPLIANT
```

### Sensor Evidence

Displays the temperature trace for the shipment.

### Governing Evidence

Displays the supporting internal SOP evidence.

### AI Explanation

Provides a concise explanation grounded in the supplied evidence.

### Automated Breach Detection

Shows the latest breach generated by the Stream/Task pipeline.

### Audit Trail

Displays the historical decision and resolution records.

------------------------------------------------------------------------

# 16. Reference Investigation: SH-101

The end-to-end demo follows shipment `SH-101`.

## Shipment context

``` text
Shipment:       SH-101
Order:          ORD-101
Batch:          B-12
Supplier Lot:   LOT-501
Customer:       CUST-101
```

## ERP interpretation

``` text
COMPLIANT - DELIVERED
```

The ERP status reflects delivery success, not the complete governed
cold-chain definition.

## Sensor evidence

The shipment experienced a temperature excursion above `8 C`.

The original compliance window contains:

``` text
Maximum temperature: 9.00 C
Excursion duration:  14 minutes
```

## Governed decision

The canonical rule requires:

``` text
MAX temperature <= 8 C
AND
excursion duration < 10 minutes
```

The shipment fails both criteria.

Therefore:

``` text
NON_COMPLIANT
```

## Why this matters

The system does not simply overwrite the ERP interpretation.

It preserves the conflict:

``` text
ERP says:
COMPLIANT - DELIVERED

Governed cold-chain definition says:
NON_COMPLIANT
```

The conflict itself becomes explainable and auditable.

------------------------------------------------------------------------

# 17. End-to-End Decision Flow

``` text
1. IoT sensor event arrives
          |
          v
2. Bronze stores source event
          |
          v
3. Silver normalizes compliance evidence
          |
          v
4. Gold calculates governed compliance facts
          |
          v
5. Semantic Views expose the canonical model
          |
          +--------------------+
          |                    |
          v                    v
   Cortex Analyst        Cortex Search
          |                    |
          +---------+----------+
                    |
                    v
              AI explanation
                    |
                    v
             Streamlit UI
                    |
                    v
              Audit record
```

Separately:

``` text
New IoT Event
     |
     v
Stream
     |
     v
Task
     |
     v
GOLD_COMPLIANCE_BREACHES
```

------------------------------------------------------------------------

# 18. Repository Structure

``` text
whoops/
|
├── .cortex/
│   └── skills/
│       ├── assess_cold_chain_compliance/
│       │   └── SKILL.md
│       ├── execute_compliance_resolution/
│       │   └── SKILL.md
│       └── investigate_shipment/
│           └── SKILL.md
|
├── .streamlit/
│   └── secrets.toml
|
├── app/
│   └── app.py
|
├── data/
│   ├── raw/
│   │   ├── batches.json
│   │   ├── compliance_policies.json
│   │   ├── customers.json
│   │   ├── iot_temperature.json
│   │   ├── lots.json
│   │   ├── orders.json
│   │   ├── products.json
│   │   ├── shipments.json
│   │   ├── stability_studies.json
│   │   └── suppliers.json
│   └── seed/
|
├── docs/
│   └── DEPLOYED_DEFINITIONS.md
|
├── scripts/
│   └── seed_bronze.py
|
├── sql/
│   ├── 01_bronze.sql
│   ├── 02_silver.sql
│   ├── 03_gold.sql
│   ├── 04_semantic.sql
│   ├── 05_search.sql
│   ├── 06_agent.sql
│   ├── 07_governance.sql
│   └── 08_app.sql
|
├── .gitignore
├── README.md
└── requirements.txt
```

------------------------------------------------------------------------

# 19. SQL Deployment Order

The SQL directory is intentionally ordered according to the dependency
graph.

``` text
01_bronze.sql
      |
      v
02_silver.sql
      |
      v
03_gold.sql
      |
      v
04_semantic.sql
      |
      v
05_search.sql
      |
      v
06_agent.sql
      |
      v
07_governance.sql
      |
      v
08_app.sql
```

`06_agent.sql` documents the Cortex Analyst configuration boundary.

`08_app.sql` is intentionally empty because the Streamlit application is
deployed separately rather than as a Snowflake database object.

------------------------------------------------------------------------

# 20. Prerequisites

The implementation assumes:

-   Snowflake account with the required Cortex capabilities enabled;
-   Snowflake CLI / CoCo CLI;
-   Python 3.13.x;
-   Streamlit;
-   Snowflake Connector for Python;
-   a Snowflake warehouse such as `COMPUTE_WH`;
-   appropriate privileges to deploy the database objects.

Python dependencies are listed in:

``` text
requirements.txt
```

------------------------------------------------------------------------

# 21. Snowflake Database

The reference deployment uses:

``` text
Database:
COLD_CHAIN_COMPLIANCE
```

Schemas:

``` text
BRONZE
SILVER
GOLD
GOVERNANCE
```

The deployment also creates the required roles, semantic objects, Cortex
Search service, Stream, Task, masking policy, and governance objects.

A deployment snapshot is maintained in:

``` text
docs/DEPLOYED_DEFINITIONS.md
```

This file documents the deployed object definitions without including
private credentials.

------------------------------------------------------------------------

# 22. Local Configuration

The Streamlit application reads Snowflake connection configuration from:

``` text
.streamlit/secrets.toml
```

The repository intentionally does not commit private credentials.

Sensitive files are excluded through `.gitignore`.

Do not commit:

``` text
snowflake_private_key.p8
.streamlit/secrets.toml
.streamlit/snowflake_private_key.p8
snowflake_public_key.txt
```

The private key should remain local or be supplied through the
deployment platform's secret-management mechanism.

------------------------------------------------------------------------

# 23. Running the Application

From the project root:

``` cmd
cd C:\Users\Shreya\whoops
streamlit run app\app.py
```

The application connects to Snowflake using the configured key-pair
authentication.

The application uses a dedicated Quality connection when retrieving
authorized sensor evidence so that the temperature graph can display the
data permitted to the Quality persona without weakening the masking
policy for other roles.

------------------------------------------------------------------------

# 24. Validation

The deployed system was validated across the following dimensions.

## Compliance logic

Verified:

``` text
MAX temperature = 9.00 C
Allowed maximum = 8.00 C

Excursion = 14 minutes
Allowed = < 10 minutes

Decision = NON_COMPLIANT
```

## Semantic layer

Verified:

``` text
5 / 5 Semantic Views
```

were deployed.

## Evidence

Verified:

-   sensor evidence;
-   internal SOP evidence;
-   evidence references;
-   decision reason.

## Automation

Verified:

``` text
Stream
    ->
Task
    ->
GOLD_COMPLIANCE_BREACHES
```

with the automated breach:

``` text
BREACH-EVT-101-AUTO-001
```

## Governance

Verified:

-   Quality can access authorized raw sensor evidence;
-   Logistics receives governed compliance data;
-   raw temperature values are masked outside the authorized role;
-   audit-writing permissions are restricted;
-   controlled audit-writing sessions cannot update/delete audit
    records.

## Audit integrity

Final read-only verification produced:

``` text
9 / 9 PASS
```

The verification confirmed:

1.  controlled execution role;
2.  governed compliance status;
3.  latest audit record;
4.  audit record count;
5.  original audit records unchanged;
6.  ERP status unchanged;
7.  IoT event count intact;
8.  latest automated breach present;
9.  source shipment/sensor data unchanged.

No role escalation or secondary-role activation was used during the
final verification.

------------------------------------------------------------------------

# 25. Security Model

The project follows several security principles.

### Least privilege

Different personas receive different access paths.

### Data masking

Sensitive raw sensor values are protected with Snowflake masking
policies.

### Governed interfaces

Applications should query governed views and Semantic Views rather than
bypassing controls through raw tables.

### No privilege escalation in Skills

CoCo Skills are instructed not to:

-   switch roles;
-   activate secondary roles;
-   request privilege escalation;
-   use an ACCOUNTADMIN bypass;
-   bypass masking;
-   modify source sensor data.

### Source preservation

Historical shipment and sensor records are treated as evidence and are
not modified as part of compliance resolution.

### Audit preservation

Completed decisions and resolutions are recorded as new audit entries
rather than rewriting historical records.

------------------------------------------------------------------------

# 26. Design Decisions

## Why deterministic rules instead of an LLM deciding compliance?

Compliance decisions need reproducibility.

A language model can explain the decision, but the canonical rule should
remain explicit and inspectable.

------------------------------------------------------------------------

## Why Semantic Views?

Semantic Views provide a governed interface between enterprise data and
natural-language analytical experiences.

They reduce the need for each consumer to independently rediscover:

-   joins;
-   business definitions;
-   metrics;
-   dimensions;
-   relationships.

------------------------------------------------------------------------

## Why Cortex Search?

Compliance investigations frequently require supporting evidence rather
than only structured metrics.

Cortex Search provides a retrieval layer for document evidence.

------------------------------------------------------------------------

## Why multiple Cortex capabilities?

Each capability has a different role:

``` text
Semantic Views  -> governed business meaning
Cortex Analyst  -> analytical question answering
Cortex Search   -> evidence retrieval
AI_COMPLETE     -> controlled explanation
CoCo Skills     -> structured investigation/resolution workflow
```

This separation keeps the architecture understandable and testable.

------------------------------------------------------------------------

# 27. Limitations and Scope

This repository is a demonstration architecture using synthetic data.

It does not claim to implement:

-   a production pharmaceutical quality-management system;
-   a validated GxP environment;
-   legal interpretation of FDA regulations;
-   real production sensor ingestion;
-   complete electronic batch record management;
-   production-scale disaster recovery;
-   enterprise identity federation;
-   formal regulatory validation.

The internal SOP evidence used by the demo is synthetic and should not
be interpreted as legal or regulatory advice.

A production deployment would require validation against the
organization's approved quality procedures, stability studies,
regulatory requirements, identity controls, retention policies, and
change-management processes.

------------------------------------------------------------------------

# 28. Future Extensions

Potential production extensions include:

### Real sensor ingestion

Connect the Bronze layer to streaming telemetry instead of seeded JSON.

### Policy versioning

Store effective dates and policy versions so that historical shipments
are evaluated against the correct policy applicable at the time.

### More complex excursion models

Support:

-   cumulative excursions;
-   sensor uncertainty;
-   product-specific stability limits;
-   minimum temperature;
-   humidity;
-   light exposure;
-   route-specific thresholds.

### Human-in-the-loop quality workflows

Add explicit approval states:

``` text
Detected
    ->
Investigating
    ->
Quality Review
    ->
Approved / Rejected
    ->
Closed
```

### Production identity

Integrate enterprise identity providers and user-to-role mappings.

### Stronger audit controls

Use additional immutable storage and retention controls where required
by the organization's compliance framework.

------------------------------------------------------------------------

# 29. Hackathon Architecture Mapping

The project demonstrates the following capabilities:

  Requirement / Capability     Implementation
  ---------------------------- --------------------------------
  Governed data                Bronze / Silver / Gold
  Business ontology            `SV_COLD_CHAIN_ONTOLOGY`
  Governed metrics             `SV_SHIPMENT_COMPLIANCE`
  Natural-language analytics   Cortex Analyst
  Evidence retrieval           Cortex Search
  Generative explanation       Cortex AI_COMPLETE
  Agentic workflow             CoCo Skills
  Automated detection          Snowflake Stream + Task
  Persona-aware access         Snowflake RBAC
  Data protection              Dynamic masking
  Auditability                 `AUDIT_COMPLIANCE_DECISIONS`
  Operational UI               Streamlit
  Reproducible definitions     `docs/DEPLOYED_DEFINITIONS.md`

------------------------------------------------------------------------

# 30. The Demonstration

The strongest end-to-end demonstration is intentionally simple.

Ask:

``` text
Is shipment SH-101 compliant?
```

The system surfaces the conflict:

``` text
ERP:
COMPLIANT - DELIVERED

Governed cold-chain definition:
NON_COMPLIANT
```

Then ask:

``` text
Why?
```

The evidence chain becomes:

``` text
Shipment SH-101
      |
      v
Sensor SENSOR-101
      |
      v
Maximum = 9.00 C
      |
      v
14 minutes above 8 C
      |
      v
Governed definition CC-COLDCHAIN-001
      |
      v
NON_COMPLIANT
      |
      v
Supporting SOP evidence
      |
      v
Audit record
```

The important result is not merely that an AI produced an answer.

The important result is that **the answer is governed, explainable,
traceable, and consistent across consumers**.

------------------------------------------------------------------------

# 31. Project Philosophy

WHOOPS is built around one principle:

> **Don't ask AI to invent the definition of compliance. Govern the
> definition first, connect it to evidence, and then let AI operate on
> top of that foundation.**

That makes the AI layer more useful precisely because it is not
responsible for deciding what the enterprise's data means.

------------------------------------------------------------------------


