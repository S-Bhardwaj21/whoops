\---

name: assess\_cold\_chain\_compliance

description: Assess pharmaceutical cold-chain compliance using the governed temperature rule and evidence collected during shipment investigation.

\---



\# Assess Cold Chain Compliance



\## Purpose

Determine whether a pharmaceutical shipment is compliant using the governed cold-chain definition and evidence collected during shipment investigation.



\## Inputs

\- shipment\_id

\- investigation package from `investigate\_shipment`

\- governed compliance definition

\- applicable regulatory and SOP evidence



\## Allowed Tools

\- Snowflake SQL against governed compliance facts and semantic views

\- Cortex Search for approved regulatory and SOP documents

\- CoCo CLI evidence capture

\- Read-only access to shipment investigation and audit data



\## Governed Compliance Definition

The canonical compliance rule is:



COMPLIANT =

MAX(observed\_temperature) <= 8Â°C

AND

duration\_above\_8Â°C < 10 minutes



The governed definition is the authoritative business definition for this assessment.



Do not replace or modify the governed definition based on:

\- ERP status

\- Logistics interpretation

\- individual user opinion

\- unapproved documents

\- inferred business rules



\## Assessment Procedure

1\. Resolve the shipment using the governed shipment identifier.

2\. Retrieve the applicable governed compliance definition and its version.

3\. Inspect the IoT temperature evidence.

4\. Determine the maximum observed temperature.

5\. Determine the duration above the 8Â°C threshold.

6\. Evaluate both conditions independently.

7\. Retrieve the applicable regulatory clause and approved SOP evidence.

8\. Compare the observed evidence against the governed rule.

9\. Produce one consistent compliance determination.



\## Decision Logic

A shipment is `COMPLIANT` only when both conditions are satisfied:



\- maximum temperature is less than or equal to 8Â°C

\- duration above 8Â°C is less than 10 minutes



If either condition fails, the shipment is `NON\_COMPLIANT`.



If required evidence is unavailable, the result must be `UNDETERMINED`.



Never invent or estimate missing sensor readings.



\## Conflicting Evidence

If ERP, logistics, IoT, quality, or other systems provide conflicting interpretations:



\- report the conflict explicitly

\- use the governed compliance definition for the final assessment

\- cite the actual sensor evidence

\- cite the applicable regulatory/SOP evidence



Do not infer why another system produced a different status.



\## Regulatory Evidence

Regulatory documents provide supporting evidence and context.



Every regulatory citation must include:

\- document name

\- clause or section

\- page number when available

\- relevant evidence reference



Do not claim that a regulation requires a specific action unless the retrieved evidence supports that claim.



\## Output

Return:



\- shipment\_id

\- compliance\_status

\- maximum\_temperature

\- duration\_above\_threshold

\- temperature\_threshold

\- duration\_threshold

\- metric\_definition

\- metric\_definition\_version

\- sensor\_evidence

\- regulatory\_evidence

\- sop\_evidence

\- conflicting\_system\_statuses

\- unresolved\_evidence

\- assessment\_timestamp



\## Required Decision Explanation

The explanation must be concise and evidence-grounded.



It must state:

1\. the governed rule used

2\. the observed sensor result

3\. the resulting compliance status

4\. the supporting regulatory/SOP evidence



Do not include unsupported causes, motives, assumptions, or missing facts.


## Escalation Conditions

Escalate by reporting the evidence gap, NOT by escalating Snowflake privileges, when:

- the governed definition is unavailable
- sensor data is incomplete
- sensor timestamps are inconsistent
- shipment identity is ambiguous
- applicable regulatory evidence cannot be resolved
- required evidence sources materially conflict

If the current role cannot access required evidence, return `UNDETERMINED` and identify the inaccessible evidence.

Never switch roles, activate secondary roles, request privilege escalation, or use ACCOUNTADMIN to bypass an authorization failure.

Do not recommend granting additional privileges to the current role as part of the assessment.

\## Audit Requirement

Every completed assessment must provide the evidence and `metric\_definition\_version` required by `AUDIT\_COMPLIANCE\_DECISIONS`.
The assessment must be reproducible from the recorded evidence.

If the current role cannot access the audit record or required metric definition version, report that limitation. Do not bypass the access boundary or modify privileges.
