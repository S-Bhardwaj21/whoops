import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

datasets = {
    "suppliers.json": [
        {"supplier_id": "SUP-001", "name": "Aster Biologics", "country": "India", "status": "approved"},
        {"supplier_id": "SUP-002", "name": "NorthStar Pharma Logistics", "country": "Singapore", "status": "approved"}
    ],
    "products.json": [
        {"product_id": "PROD-001", "name": "Vaccine-X", "category": "Biologic", "storage_min_c": 2.0, "storage_max_c": 8.0},
        {"product_id": "PROD-002", "name": "Therapy-Y", "category": "Biologic", "storage_min_c": 2.0, "storage_max_c": 8.0}
    ],
    "lots.json": [
        {"lot_id": "LOT-001", "supplier_id": "SUP-001", "product_id": "PROD-001", "manufacture_date": "2026-08-01"},
        {"lot_id": "LOT-002", "supplier_id": "SUP-002", "product_id": "PROD-002", "manufacture_date": "2026-08-12"}
    ],
    "batches.json": [
        {"batch_id": "B-12", "lot_id": "LOT-001", "product_id": "PROD-001", "stability_study_id": "STAB-001", "status": "released"},
        {"batch_id": "B-13", "lot_id": "LOT-002", "product_id": "PROD-002", "stability_study_id": "STAB-002", "status": "released"}
    ],
    "stability_studies.json": [
        {
            "study_id": "STAB-001",
            "batch_id": "B-12",
            "storage_min_c": 2.0,
            "storage_max_c": 8.0,
            "max_excursion_duration_min": 10,
            "requires_quality_review": True,
            "version": "2.1"
        },
        {
            "study_id": "STAB-002",
            "batch_id": "B-13",
            "storage_min_c": 2.0,
            "storage_max_c": 8.0,
            "max_excursion_duration_min": 10,
            "requires_quality_review": True,
            "version": "1.4"
        }
    ],
    "shipments.json": [
        {
            "shipment_id": "SH-101",
            "batch_id": "B-12",
            "order_id": "O-5001",
            "supplier_id": "SUP-001",
            "destination_customer_id": "C-001",
            "status": "DELIVERED",
            "legacy_compliance_flag": "COMPLIANT"
        },
        {
            "shipment_id": "SH-102",
            "batch_id": "B-13",
            "order_id": "O-5002",
            "supplier_id": "SUP-002",
            "destination_customer_id": "C-002",
            "status": "DELIVERED",
            "legacy_compliance_flag": "COMPLIANT"
        }
    ],
    "orders.json": [
        {"order_id": "O-5001", "customer_id": "C-001", "shipment_id": "SH-101", "priority": "HIGH"},
        {"order_id": "O-5002", "customer_id": "C-002", "shipment_id": "SH-102", "priority": "STANDARD"}
    ],
    "customers.json": [
        {"customer_id": "C-001", "name": "Apollo Specialty Care", "segment": "Hospital"},
        {"customer_id": "C-002", "name": "NorthCare Medical", "segment": "Hospital"}
    ],
    "iot_temperature.json": [
        {"event_id": "EVT-1001", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:00:00", "temperature_c": 7.2},
        {"event_id": "EVT-1002", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:01:00", "temperature_c": 7.8},
        {"event_id": "EVT-1003", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:02:00", "temperature_c": 8.4},
        {"event_id": "EVT-1004", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:03:00", "temperature_c": 9.1},
        {"event_id": "EVT-1005", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:04:00", "temperature_c": 9.1},
        {"event_id": "EVT-1006", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:05:00", "temperature_c": 9.1},
        {"event_id": "EVT-1007", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:06:00", "temperature_c": 9.1},
        {"event_id": "EVT-1008", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:07:00", "temperature_c": 9.1},
        {"event_id": "EVT-1009", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:08:00", "temperature_c": 9.1},
        {"event_id": "EVT-1010", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:09:00", "temperature_c": 9.1},
        {"event_id": "EVT-1011", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:10:00", "temperature_c": 9.1},
        {"event_id": "EVT-1012", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:11:00", "temperature_c": 9.1},
        {"event_id": "EVT-1013", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:12:00", "temperature_c": 9.1},
        {"event_id": "EVT-1014", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:13:00", "temperature_c": 9.1},
        {"event_id": "EVT-1015", "shipment_id": "SH-101", "timestamp": "2026-09-30T02:14:00", "temperature_c": 7.6},
        {"event_id": "EVT-2001", "shipment_id": "SH-102", "timestamp": "2026-09-30T03:00:00", "temperature_c": 5.9},
        {"event_id": "EVT-2002", "shipment_id": "SH-102", "timestamp": "2026-09-30T03:01:00", "temperature_c": 6.1}
    ],
    "compliance_policies.json": [
        {
            "policy_id": "CC-POL-001",
            "name": "Cold Chain Policy",
            "version": "1.3",
            "definition": "Shipment is compliant when temperatures remain within the approved stability range; excursions beyond the range that exceed the approved duration require quality review.",
            "default_storage_min_c": 2.0,
            "default_storage_max_c": 8.0,
            "default_max_excursion_duration_min": 10,
            "owner": "Quality Assurance",
            "status": "active"
        }
    ]
}

for filename, rows in datasets.items():
    path = OUT / filename
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    print(f"Wrote {len(rows):>3} rows -> {path}")

print(f"\nBronze seed complete: {len(datasets)} files")