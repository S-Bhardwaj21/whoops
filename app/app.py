import streamlit as st
import pandas as pd
from pathlib import Path
import snowflake.connector

st.set_page_config(
    page_title="Cold Chain Command Center",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {
    max-width: 1400px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}
.hero {
    padding: 1.5rem 0 1rem 0;
}
.hero h1 {
    font-size: 2.4rem;
    margin-bottom: 0.2rem;
}
.hero p {
    color: #777;
    font-size: 1.05rem;
}
.status-card {
    padding: 1.5rem;
    border-radius: 14px;
    border: 1px solid #ddd;
    background: #fafafa;
    color: #111827;
}
.evidence {
    border-left: 4px solid #888;
    padding: 0.8rem 1rem;
    background: #fafafa;
    border-radius: 4px;
    color: #111827;
}
.status {
    font-size: 2rem;
    font-weight: 800;
}
.red {
    color: #d62728;
}
.green {
    color: #16803c;
}
.metric-label {
    color: #777;
    font-size: 0.85rem;
}
.metric-value {
    font-size: 1.45rem;
    font-weight: 700;
}
.section {
    margin-top: 2rem;
    margin-bottom: 0.8rem;
}
.audit {
    padding: 0.8rem 1rem;
    border-bottom: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_connection():
    config = st.secrets["snowflake"]
    private_key_path = Path(config["private_key_file"]).resolve()
    return snowflake.connector.connect(
        account=config["account"],
        user=config["user"],
        private_key_file=str(private_key_path),
        database=config["database"],
        schema=config["schema"],
        warehouse=config["warehouse"],
    )

def query_df(sql, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or ())
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=columns)
    finally:
        cursor.close()

def query_one(sql, params=None):
    df = query_df(sql, params)
    if df.empty:
        return None
    return df.iloc[0]

def get_compliance_fact(shipment_id):
    return query_one(
        """
        SELECT
            SHIPMENT_ID,
            ORDER_ID,
            BATCH_ID,
            SUPPLIER_LOT_ID,
            CUSTOMER_ID,
            ERP_STATUS,
            MAX_TEMPERATURE_C,
            ALLOWED_MAX_TEMPERATURE_C,
            MINUTES_ABOVE_THRESHOLD,
            ALLOWED_EXCURSION_MINUTES,
            COMPLIANCE_STATUS,
            METRIC_DEFINITION_VERSION,
            DECISION_REASON
        FROM COLD_CHAIN_COMPLIANCE.GOLD.GOLD_COMPLIANCE_FACTS
        WHERE SHIPMENT_ID = %s
        """,
        (shipment_id,),
    )

def get_evidence(shipment_id):
    return query_df(
        """
        SELECT
            EVIDENCE_ID,
            SHIPMENT_ID,
            DOCUMENT_NAME,
            CLAUSE_REFERENCE,
            PAGE_NUMBER,
            SOURCE_TYPE,
            EVIDENCE_TEXT
        FROM COLD_CHAIN_COMPLIANCE.GOLD.REGULATORY_EVIDENCE
        WHERE SHIPMENT_ID = %s
        ORDER BY PAGE_NUMBER
        """,
        (shipment_id,),
    )

def get_audit(shipment_id):
    return query_df(
        """
        SELECT
            AUDIT_ID,
            SHIPMENT_ID,
            COMPLIANCE_STATUS,
            RESOLUTION_ACTION,
            METRIC_DEFINITION_VERSION,
            SENSOR_EVIDENCE_REF,
            REGULATORY_EVIDENCE_REF,
            DECISION_REASON,
            ACTOR,
            DECIDED_AT,
            AUDIT_STATUS
        FROM COLD_CHAIN_COMPLIANCE.GOVERNANCE.AUDIT_COMPLIANCE_DECISIONS
        WHERE SHIPMENT_ID = %s
        ORDER BY DECIDED_AT
        """,
        (shipment_id,),
    )

@st.cache_resource
def get_quality_connection():
    config = st.secrets["snowflake"]
    private_key_path = Path(config["private_key_file"]).resolve()
    return snowflake.connector.connect(
        account=config["account"],
        user=config["user"],
        private_key_file=str(private_key_path),
        database=config["database"],
        schema=config["schema"],
        warehouse=config["warehouse"],
        role="COLD_CHAIN_QUALITY",
    )

def get_sensor_data(shipment_id):
    conn = get_quality_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT
                EVENT_TS,
                TEMPERATURE_C,
                SENSOR_ID,
                SENSOR_STATUS
            FROM COLD_CHAIN_COMPLIANCE.GOLD.VW_QUALITY_SENSOR_EVIDENCE
            WHERE SHIPMENT_ID = %s
            ORDER BY EVENT_TS
            """,
            (shipment_id,),
        )
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=columns)
    finally:
        cursor.close()

def get_latest_breach(shipment_id):
    return query_one(
        """
        SELECT
            BREACH_ID,
            SHIPMENT_ID,
            SENSOR_ID,
            TEMPERATURE_C,
            THRESHOLD_C,
            BREACH_TYPE,
            STATUS
        FROM COLD_CHAIN_COMPLIANCE.GOLD.GOLD_COMPLIANCE_BREACHES
        WHERE SHIPMENT_ID = %s
        ORDER BY BREACH_ID DESC
        LIMIT 1
        """,
        (shipment_id,),
    )

def generate_ai_explanation(fact, evidence):
    evidence_text = "\n".join(
        evidence["EVIDENCE_TEXT"].astype(str).tolist()
    ) if not evidence.empty else "No evidence text available."
    prompt = f"""
Explain this cold-chain compliance decision in exactly 2 concise sentences.

Use ONLY the supplied evidence.
Do not infer motives, causes, system behavior, or missing facts.

Shipment: {fact["SHIPMENT_ID"]}
ERP status: {fact["ERP_STATUS"]}
Governed status: {fact["COMPLIANCE_STATUS"]}
Maximum temperature: {fact["MAX_TEMPERATURE_C"]} C
Allowed maximum: {fact["ALLOWED_MAX_TEMPERATURE_C"]} C
Minutes above threshold: {fact["MINUTES_ABOVE_THRESHOLD"]}
Allowed excursion duration: {fact["ALLOWED_EXCURSION_MINUTES"]} minutes
Metric definition: {fact["METRIC_DEFINITION_VERSION"]}
Decision reason: {fact["DECISION_REASON"]}

Evidence:
{evidence_text}
"""
    result = query_one(
        """
        SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(
            'claude-sonnet-4-6',
            %s
        ) AS EXPLANATION
        """,
        (prompt,),
    )
    if result is None:
        return "AI explanation unavailable."
    return str(result["EXPLANATION"])

st.sidebar.title("Cold Chain")
st.sidebar.caption("Compliance Command Center")

page = st.sidebar.radio(
    "Navigate",
    ["Investigate Shipment", "Governance", "Audit Trail"],
)

st.sidebar.divider()
st.sidebar.caption("Shipment")

shipment_id = st.sidebar.selectbox(
    "Shipment",
    ["SH-101"],
)

st.sidebar.caption("Persona")

persona = st.sidebar.selectbox(
    "View as",
    ["Quality", "Logistics", "Compliance"],
)

try:
    fact = get_compliance_fact(shipment_id)
    if fact is None:
        st.error(f"No governed compliance record found for {shipment_id}.")
        st.stop()
    evidence_df = get_evidence(shipment_id)
except Exception as exc:
    st.error("Unable to connect to the Cold Chain Compliance Snowflake environment.")
    st.exception(exc)
    st.stop()

st.markdown("""
<div class="hero">
    <h1>Cold Chain Command Center</h1>
    <p>Investigate pharmaceutical shipments using governed evidence, rules, and audit history.</p>
</div>
""", unsafe_allow_html=True)

if page == "Investigate Shipment":
    st.caption(f"Shipment investigation / {shipment_id}")
    col1, col2, col3 = st.columns(3)
    with col1:
        status_class = "green" if fact["COMPLIANCE_STATUS"] == "COMPLIANT" else "red"
        st.markdown(
            f"""
            <div class="status-card">
                <div class="metric-label">GOVERNED DECISION</div>
                <div class="status {status_class}">{fact["COMPLIANCE_STATUS"]}</div>
                <div>Definition: <b>{fact["METRIC_DEFINITION_VERSION"]}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="status-card">
                <div class="metric-label">MAX TEMPERATURE</div>
                <div class="metric-value">{fact["MAX_TEMPERATURE_C"]:.2f} C</div>
                <div>Allowed: &lt;= {fact["ALLOWED_MAX_TEMPERATURE_C"]:.2f} C</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="status-card">
                <div class="metric-label">EXCURSION DURATION</div>
                <div class="metric-value">{fact["MINUTES_ABOVE_THRESHOLD"]} min</div>
                <div>Allowed: &lt; {fact["ALLOWED_EXCURSION_MINUTES"]} min</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div class="section"><h2>Why is this shipment non-compliant?</h2></div>',
        unsafe_allow_html=True,
    )
    st.info(
        f"The governed rule requires the maximum observed temperature to remain at or below "
        f"{fact['ALLOWED_MAX_TEMPERATURE_C']} C and the duration above that threshold "
        f"to remain below {fact['ALLOWED_EXCURSION_MINUTES']} minutes."
    )
    st.subheader("System Conflict")
    conflict = {
        "ERP": (
            fact["ERP_STATUS"],
            "Delivery status only",
        ),
        "Operations": (
            "NON_COMPLIANT",
            "Temperature range",
        ),
        "Quality": (
            "NON_COMPLIANT",
            "Temperature and excursion duration",
        ),
        "Governed": (
            fact["COMPLIANCE_STATUS"],
            "Canonical rule",
        ),
    }
    cols = st.columns(4)
    for col, (source, (status, reason)) in zip(cols, conflict.items()):
        with col:
            st.markdown(f"### {source}")
            st.markdown(f"**{status}**")
            st.caption(reason)
    st.markdown(
        '<div class="section"><h2>Sensor Evidence</h2></div>',
        unsafe_allow_html=True,
    )
    if persona == "Quality":
        sensor_df = get_sensor_data(shipment_id)
        if not sensor_df.empty:
            sensor_df["EVENT_TS"] = pd.to_datetime(
                sensor_df["EVENT_TS"],
                errors="coerce",
            )
            sensor_df["TEMPERATURE_C"] = pd.to_numeric(
                sensor_df["TEMPERATURE_C"],
                errors="coerce",
            )
            sensor_df = sensor_df.dropna(
                subset=["EVENT_TS", "TEMPERATURE_C"]
            )
            sensor_df = sensor_df.sort_values("EVENT_TS")
            import altair as alt
            chart = alt.Chart(sensor_df).mark_line(
                point=True
            ).encode(
                x=alt.X(
                    "EVENT_TS:T",
                    title="Time",
                    axis=alt.Axis(format="%H:%M"),
                ),
                y=alt.Y(
                    "TEMPERATURE_C:Q",
                    title="Temperature (C)",
                    scale=alt.Scale(domain=[6, 10]),
                ),
                tooltip=[
                    alt.Tooltip(
                        "EVENT_TS:T",
                        title="Time",
                        format="%H:%M",
                    ),
                    alt.Tooltip(
                        "TEMPERATURE_C:Q",
                        title="Temperature",
                        format=".2f",
                    ),
                    alt.Tooltip(
                        "SENSOR_ID:N",
                        title="Sensor",
                    ),
                ],
            ).properties(
                height=380
            )
            st.altair_chart(
                chart,
                use_container_width=True,
            )
            st.caption(
                f"Live IoT readings from the governed Quality sensor view. "
                f"Maximum observed temperature: "
                f"{sensor_df['TEMPERATURE_C'].max():.2f} C."
            )
        else:
            st.warning("No sensor readings found.")
    else:
        st.info(
            "Raw sensor temperatures are protected for this persona. "
            "The governed compliance result remains visible."
        )
    st.markdown(
        '<div class="section"><h2>Governing Evidence</h2></div>',
        unsafe_allow_html=True,
    )
    if evidence_df.empty:
        st.warning("No governing evidence found.")
    else:
        for _, evidence in evidence_df.iterrows():
            st.markdown(
                f"""
                <div class="evidence">
                <b>{evidence["DOCUMENT_NAME"]}</b><br>
                Clause: <b>{evidence["CLAUSE_REFERENCE"]}</b> / Page {evidence["PAGE_NUMBER"]}<br><br>
                {evidence["EVIDENCE_TEXT"]}
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown(
        '<div class="section"><h2>AI Explanation</h2></div>',
        unsafe_allow_html=True,
    )
    try:
        ai_explanation = generate_ai_explanation(
            fact,
            evidence_df,
        )
        st.write(ai_explanation)
    except Exception as exc:
        st.warning("Cortex AI explanation is temporarily unavailable.")
        st.caption(str(exc))
    breach = get_latest_breach(shipment_id)
    if breach is not None:
        st.markdown(
            '<div class="section"><h2>Automated Breach Detection</h2></div>',
            unsafe_allow_html=True,
        )
        st.success(
            f"Live breach detected by Stream and Task: {breach['BREACH_ID']}"
        )
        breach_cols = st.columns(4)
        breach_cols[0].metric(
            "Observed temperature",
            f"{breach['TEMPERATURE_C']:.2f} C",
        )
        breach_cols[1].metric(
            "Threshold",
            f"{breach['THRESHOLD_C']:.2f} C",
        )
        breach_cols[2].metric(
            "Breach type",
            str(breach["BREACH_TYPE"]),
        )
        breach_cols[3].metric(
            "Status",
            str(breach["STATUS"]),
        )
elif page == "Governance":
    st.title("Governance")
    st.subheader(f"Persona: {persona}")
    if persona == "Logistics":
        st.success(f"Governed decision: {fact['COMPLIANCE_STATUS']}")
        st.info("Raw sensor temperature is protected for this persona.")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Excursion duration",
                f"{fact['MINUTES_ABOVE_THRESHOLD']} min",
            )
        with col2:
            st.metric(
                "Compliance definition",
                fact["METRIC_DEFINITION_VERSION"],
            )
    elif persona == "Quality":
        st.success("Full sensor evidence available.")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Maximum temperature",
                f"{fact['MAX_TEMPERATURE_C']:.2f} C",
            )
        with col2:
            st.metric(
                "Readings above threshold",
                fact["MINUTES_ABOVE_THRESHOLD"],
            )
        with col3:
            st.metric(
                "Excursion duration",
                f"{fact['MINUTES_ABOVE_THRESHOLD']} min",
            )
    else:
        st.success("Decision, evidence, and audit information available.")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Governed status",
                fact["COMPLIANCE_STATUS"],
            )
        with col2:
            st.metric(
                "Definition version",
                fact["METRIC_DEFINITION_VERSION"],
            )
    st.divider()
    st.subheader("Canonical Definition")
    st.code(
        "MAX observed temperature <= "
        f"{fact['ALLOWED_MAX_TEMPERATURE_C']} C\n"
        "AND\n"
        f"duration above {fact['ALLOWED_MAX_TEMPERATURE_C']} C "
        f"< {fact['ALLOWED_EXCURSION_MINUTES']} minutes"
    )
    st.caption(
        "This governed definition is stored in the Gold compliance layer and "
        "drives the canonical compliance decision."
    )
    st.subheader("Governed Decision Source")
    governed_df = pd.DataFrame(
        [{
            "Shipment": fact["SHIPMENT_ID"],
            "ERP Status": fact["ERP_STATUS"],
            "Governed Status": fact["COMPLIANCE_STATUS"],
            "Metric Version": fact["METRIC_DEFINITION_VERSION"],
            "Max Temperature C": fact["MAX_TEMPERATURE_C"],
            "Minutes Above Threshold": fact["MINUTES_ABOVE_THRESHOLD"],
        }]
    )
    st.dataframe(
        governed_df,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.title("Audit Trail")
    st.subheader(shipment_id)
    audit_df = get_audit(shipment_id)
    if audit_df.empty:
        st.info("No audit records found.")
    else:
        for _, audit in audit_df.iterrows():
            decided_at = audit["DECIDED_AT"]
            st.markdown(
                f"""
                <div class="audit">
                <b>{decided_at}</b> / {audit["RESOLUTION_ACTION"]}<br>
                <small>
                {audit["AUDIT_ID"]} / {audit["COMPLIANCE_STATUS"]} /
                {audit["METRIC_DEFINITION_VERSION"]} /
                {audit["AUDIT_STATUS"]}
                </small>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.divider()
        st.subheader("Audit Records")
        display_df = audit_df[
            [
                "AUDIT_ID",
                "COMPLIANCE_STATUS",
                "RESOLUTION_ACTION",
                "METRIC_DEFINITION_VERSION",
                "SENSOR_EVIDENCE_REF",
                "REGULATORY_EVIDENCE_REF",
                "ACTOR",
                "AUDIT_STATUS",
                "DECIDED_AT",
            ]
        ]
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )
        st.info(
            "The original compliance decision is preserved in the audit trail. "
            "Resolution records are recorded separately rather than replacing the original decision."
        )