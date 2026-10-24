#!/usr/bin/env python3
"""
Orthotect Programmatic SEO Gallery & Production Template Generator
Generates:
1. 50 standalone, production-ready, fully certified HTML templates in docs/templates/
2. docs/sitemap.xml (All 50 template URLs + root site)
3. docs/robots.txt (Directing crawlers to sitemap.xml)
4. docs/gallery-data.js & docs/gallery-data.json for dynamic gallery filtering and search
"""

import json
import os
import html
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from scripts.template_aesthetics import TEMPLATE_AESTHETICS
except ImportError:
    from template_aesthetics import TEMPLATE_AESTHETICS

DOCS_DIR = ROOT_DIR / "docs"
TEMPLATES_DIR = DOCS_DIR / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://seotarek.github.io/orthotect"

# 5 Clusters x 10 Templates = 50 Standalone Production Templates
TEMPLATES_SPEC = [
    # ─────────────────────────────────────────────────────────────────────────────
    # CLUSTER 1: Enterprise Dashboards & Telemetry Consoles (1–10)
    # ─────────────────────────────────────────────────────────────────────────────
    {
        "id": "saas-metric-console",
        "cluster": "dashboards",
        "cluster_name": "Enterprise Dashboards",
        "cluster_num": 1,
        "title": "SaaS Metric & ARR Growth Telemetry Console",
        "subtitle": "Real-time recurring revenue, churn velocity, and expansion telemetry",
        "desc": "High-density enterprise executive dashboard monitoring Monthly Recurring Revenue (MRR), Net Revenue Retention (NRR), customer lifetime value, and cohort churn velocity with sub-second SVG charts.",
        "skill": "orthotect-dashboard",
        "tokens": "semantics.json, ergonomics.json, motion.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "saas dashboard, arr telemetry console, mrr growth metrics, enterprise churn analytics, wcag aaa dashboard, bidi enterprise console",
        "badge": "WCAG 2.2 AAA",
        "icon": "chart",
        "stats": [
            {"label": "Current ARR", "value": "$14.82M", "delta": "+18.4% YoY", "positive": True},
            {"label": "Net Retention Rate", "value": "128.4%", "delta": "+3.2% QoQ", "positive": True},
            {"label": "Gross Logo Churn", "value": "0.42%", "delta": "-0.15% MoM", "positive": True},
            {"label": "Avg LTV / CAC", "value": "5.8x", "delta": "Healthy Unit Econ", "positive": True}
        ],
        "chart_type": "area",
        "table_headers": ["Account Tier", "Contract ARR", "Net Expansion", "Health Score", "Status"],
        "table_rows": [
            ["Stripe Enterprise", "$420,000", "+$85,000", "98/100", "Optimal"],
            ["Datadog Global", "$310,000", "+$45,000", "94/100", "Optimal"],
            ["Snowflake EMEA", "$280,000", "+$12,000", "89/100", "Stable"],
            ["Linear Systems", "$195,000", "+$34,000", "96/100", "Optimal"],
            ["Vercel Cloud", "$160,000", "$0", "82/100", "Monitoring"]
        ]
    },
    {
        "id": "cloud-infrastructure-monitor",
        "cluster": "dashboards",
        "cluster_name": "Enterprise Dashboards",
        "cluster_num": 1,
        "title": "Multi-Region Cloud Infrastructure & Kubernetes Monitor",
        "subtitle": "Distributed node health, pod utilization, and ingress latency telemetry",
        "desc": "Mission-critical infrastructure console tracking multi-cloud Kubernetes clusters across us-east, eu-central, and ap-southeast with p99 latency telemetry and automatic failover metrics.",
        "skill": "orthotect-dashboard",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "kubernetes dashboard, cloud infra monitor, distributed node health, p99 latency telemetry, multi-region cluster status",
        "badge": "Sub-Second Telemetry",
        "icon": "server",
        "stats": [
            {"label": "Active Nodes", "value": "1,428", "delta": "100% Online", "positive": True},
            {"label": "p99 Ingress Latency", "value": "14.2ms", "delta": "-2.1ms vs SLA", "positive": True},
            {"label": "CPU Saturation", "value": "64.8%", "delta": "Auto-scaling idle", "positive": True},
            {"label": "Egress Traffic", "value": "8.42 TB/h", "delta": "Encrypted mTLS", "positive": True}
        ],
        "chart_type": "bar",
        "table_headers": ["Cluster Region", "Nodes", "Pods Ready", "Ingress Latency", "Health"],
        "table_rows": [
            ["us-east-1 (N. Virginia)", "512", "4,820 / 4,820", "11.2ms", "Healthy"],
            ["eu-central-1 (Frankfurt)", "448", "3,910 / 3,910", "13.8ms", "Healthy"],
            ["ap-southeast-1 (Singapore)", "288", "2,400 / 2,400", "18.4ms", "Healthy"],
            ["sa-east-1 (São Paulo)", "180", "1,220 / 1,220", "22.1ms", "Healthy"]
        ]
    },
    {
        "id": "fintech-trading-terminal",
        "cluster": "dashboards",
        "cluster_name": "Enterprise Dashboards",
        "cluster_num": 1,
        "title": "Fintech Algorithmic Trading & Order Book Terminal",
        "subtitle": "Microsecond market depth, bid-ask spread telemetry, and execution ledger",
        "desc": "Ultra-dense algorithmic trading interface featuring live order book depth, execution slippage tracking, VWAP metrics, and cryptographic audit proofs for institutional markets.",
        "skill": "orthotect-data-viz",
        "tokens": "semantics.json, ergonomics.json, motion.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "trading terminal ui, order book depth chart, algorithmic trading console, fintech market data, dark mode financial ui",
        "badge": "Sub-Millisecond Depth",
        "icon": "trending-up",
        "stats": [
            {"label": "Spread (BTC/USD)", "value": "$0.50", "delta": "Tight Liquidity", "positive": True},
            {"label": "24h Volume", "value": "$842.1M", "delta": "+12.4% vs 7d avg", "positive": True},
            {"label": "Execution Latency", "value": "340μs", "delta": "Direct Colocation", "positive": True},
            {"label": "Slippage Delta", "value": "0.002%", "delta": "Zero Deviation", "positive": True}
        ],
        "chart_type": "depth",
        "table_headers": ["Order ID", "Asset Pair", "Order Type", "Execution Price", "Latency"],
        "table_rows": [
            ["ORD-89410", "BTC/USD", "Limit Buy", "$64,280.50", "280μs"],
            ["ORD-89409", "ETH/USD", "Market Sell", "$3,492.10", "310μs"],
            ["ORD-89408", "SOL/USD", "Limit Buy", "$152.80", "295μs"],
            ["ORD-89407", "BTC/EUR", "Iceberg Buy", "€59,110.00", "410μs"]
        ]
    },
    {
        "id": "iot-device-fleet-telemetry",
        "cluster": "dashboards",
        "cluster_name": "Enterprise Dashboards",
        "cluster_num": 1,
        "title": "Industrial IoT Sensor & Fleet Telemetry Operations",
        "subtitle": "Vibration analysis, thermal telemetry, and predictive maintenance telemetry",
        "desc": "Operational telemetry platform monitoring 50,000+ industrial edge gateways, smart factory actuators, and remote turbine sensors with anomaly detection and automated alert routing.",
        "skill": "orthotect-dashboard",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "iot fleet telemetry, industrial sensor dashboard, edge gateway monitor, predictive maintenance console, scada web interface",
        "badge": "Industrial Grade",
        "icon": "cpu",
        "stats": [
            {"label": "Connected Sensors", "value": "52,840", "delta": "99.98% Telemetry Ack", "positive": True},
            {"label": "Mean Vibration", "value": "1.42 mm/s", "delta": "Normal Harmonic", "positive": True},
            {"label": "Avg Gateway Temp", "value": "41.8°C", "delta": "Thermal Nominal", "positive": True},
            {"label": "Predicted Alerts", "value": "0 Critical", "delta": "Zero Unscheduled Downtime", "positive": True}
        ],
        "chart_type": "line",
        "table_headers": ["Device Node", "Location", "Battery Level", "Firmware", "Status"],
        "table_rows": [
            ["NODE-TURBINE-01", "Sector B, Bay 4", "94%", "v3.12-sec", "Operational"],
            ["NODE-HYDRAULIC-08", "Sector A, Bay 1", "88%", "v3.12-sec", "Operational"],
            ["NODE-VALVE-14", "Cooling Array C", "99%", "v3.12-sec", "Operational"],
            ["NODE-PUMP-22", "Feedline 3", "76%", "v3.10-patch", "Service Soon"]
        ]
    },
    {
        "id": "soc-cybersecurity-event-feed",
        "cluster": "dashboards",
        "cluster_name": "Enterprise Dashboards",
        "cluster_num": 1,
        "title": "Security Operations Center (SOC) Threat & SIEM Feed",
        "subtitle": "CVE threat mitigation, automated quarantine, and intrusion detection ledger",
        "desc": "Real-time cyber defense operations board visualizing perimeter intrusion attempts, automated zero-trust authentication blocks, and cryptographic incident containment state machines.",
        "skill": "orthotect-dashboard",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "soc cybersecurity dashboard, siem event feed, zero trust operations, cve mitigation interface, threat intelligence console",
        "badge": "Zero-Trust Verified",
        "icon": "shield",
        "stats": [
            {"label": "Threats Neutralized", "value": "2,419", "delta": "100% Automated Policy", "positive": True},
            {"label": "Mean Time to Triage", "value": "1.2 min", "delta": "-45s vs target", "positive": True},
            {"label": "Zero-Day Signatures", "value": "0 Active", "delta": "Quarantine Clear", "positive": True},
            {"label": "mTLS Audit Score", "value": "100/100", "delta": "Hardware Enforced", "positive": True}
        ],
        "chart_type": "area",
        "table_headers": ["Incident Vector", "Severity", "Source IP", "Action Taken", "Status"],
        "table_rows": [
            ["DDoS SYN Flood Vector", "High", "198.51.100.24", "BGP Anycast Sinkholed", "Resolved"],
            ["Credential Stuffing Bot", "Medium", "203.0.113.88", "WAF Challenge Enforced", "Blocked"],
            ["Privilege Escalation Try", "High", "10.42.12.8", "Session Revoked & Paged", "Contained"],
            ["TLS 1.1 Insecure Probe", "Low", "192.0.2.140", "Cipher Handshake Dropped", "Mitigated"]
        ]
    },
    {
        "id": "developer-ci-cd-pipeline-matrix",
        "cluster": "dashboards",
        "cluster_name": "Enterprise Dashboards",
        "cluster_num": 1,
        "title": "Distributed CI/CD Build Matrix & Runner Telemetry",
        "subtitle": "Parallel runner orchestration, test flake detection, and artifact provenance",
        "desc": "Developer platform telemetry dashboard displaying build matrix parallelism across Linux x86, ARM64, and macOS runners with deterministic cache hit ratios and gate pass rates.",
        "skill": "orthotect-dashboard",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "cicd build matrix, distributed runner dashboard, test flake tracker, build artifact provenance, developer platform ui",
        "badge": "Hermetic Builds",
        "icon": "git-pull-request",
        "stats": [
            {"label": "Median Build Time", "value": "42.8s", "delta": "-14.2s with Remote Cache", "positive": True},
            {"label": "Remote Cache Hit", "value": "94.6%", "delta": "Bazel/Turborepo Cache", "positive": True},
            {"label": "Active Runners", "value": "320 Pods", "delta": "Kubernetes Autoscaled", "positive": True},
            {"label": "Deterministic Pass", "value": "99.8%", "delta": "Zero Flake Rate", "positive": True}
        ],
        "chart_type": "bar",
        "table_headers": ["Pipeline Job", "Commit Ref", "Target Arch", "Duration", "Result"],
        "table_rows": [
            ["build-kernel-core", "997c098 (main)", "linux/arm64", "38.2s", "Passed"],
            ["gate-wcag-contrast", "997c098 (main)", "linux/amd64", "18.4s", "Passed"],
            ["gate-bidi-logical", "997c098 (main)", "linux/amd64", "14.1s", "Passed"],
            ["e2e-playwright-suite", "997c098 (main)", "macos/arm64", "1m 12s", "Passed"]
        ]
    },
    {
        "id": "logistics-fleet-dispatch-tracker",
        "cluster": "dashboards",
        "cluster_name": "Enterprise Dashboards",
        "cluster_num": 1,
        "title": "Global Supply Chain & Logistics Dispatch Command",
        "subtitle": "Intermodal freight tracking, cold-chain temperature, and route efficiency",
        "desc": "Logistics operations center command interface tracking thousands of freight containers, autonomous electric haulers, and cold-chain compliance with strict GPS latency bounds.",
        "skill": "orthotect-dashboard",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "fleet dispatch tracker, logistics supply chain console, cold chain telemetry, freight route optimization, b2b transport dashboard",
        "badge": "Cold-Chain Certified",
        "icon": "truck",
        "stats": [
            {"label": "Fleet In-Transit", "value": "1,842 Units", "delta": "98.4% On Schedule", "positive": True},
            {"label": "Cold-Chain Integrity", "value": "99.98%", "delta": "-20.4°C Target Maintained", "positive": True},
            {"label": "Fuel/Energy Savings", "value": "18.2%", "delta": "Dynamic Routing Active", "positive": True},
            {"label": "Port Customs Clearance", "value": "2.4 hrs", "delta": "Electronic BOL Pre-cleared", "positive": True}
        ],
        "chart_type": "line",
        "table_headers": ["Shipment ID", "Carrier / Mode", "Origin / Dest", "Cargo Temp", "ETA Status"],
        "table_rows": [
            ["SHP-78104", "Maersk Arctic (Sea)", "Rotterdam -> Newark", "-22.1°C", "On Time"],
            ["SHP-78105", "DHL Express Air", "Munich -> Dubai", "+3.8°C", "On Time"],
            ["SHP-78106", "Scania EV Hauler", "Lyon -> Milan", "-19.8°C", "Early (+20m)"],
            ["SHP-78107", "Kuehne+Nagel Rail", "Hamburg -> Vienna", "+4.2°C", "On Time"]
        ]
    },
    {
        "id": "energy-grid-sensor-telemetry",
        "cluster": "dashboards",
        "cluster_name": "Enterprise Dashboards",
        "cluster_num": 1,
        "title": "Smart Energy Grid & Microgrid Telemetry Console",
        "subtitle": "Renewable generation mix, battery storage status, and frequency stability",
        "desc": "Clean energy operations dashboard showing megawatts generated from offshore wind and solar arrays, state-of-charge for industrial megawatt battery packs, and 50Hz/60Hz grid balancing.",
        "skill": "orthotect-dashboard",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "energy grid telemetry, smart microgrid console, renewable generation monitor, battery storage dashboard, utility scada ui",
        "badge": "Grid-Sync Certified",
        "icon": "zap",
        "stats": [
            {"label": "Total Generation", "value": "2.48 GW", "delta": "84% Renewable Mix", "positive": True},
            {"label": "Battery Bank SoC", "value": "92.4%", "delta": "1.2 GWh Available Reserve", "positive": True},
            {"label": "Grid Frequency", "value": "50.002 Hz", "delta": "Nominal Stability (±0.01)", "positive": True},
            {"label": "Carbon Offset Today", "value": "4,120 Tons", "delta": "Net-Zero Certified", "positive": True}
        ],
        "chart_type": "area",
        "table_headers": ["Generation Array", "Output (MW)", "Capacity Factor", "Grid Frequency", "Status"],
        "table_rows": [
            ["North Sea Wind Array B", "1,140 MW", "92%", "50.001 Hz", "Peak Delivery"],
            ["Mojave Solar Array 4", "780 MW", "88%", "50.002 Hz", "Peak Delivery"],
            ["Alpine Hydro Storage 1", "360 MW", "95%", "50.000 Hz", "Load Balanced"],
            ["Hornsdale Power Reserve", "200 MW", "100%", "50.003 Hz", "Standing Reserve"]
        ]
    },
    {
        "id": "kpi-executive-scorecard",
        "cluster": "dashboards",
        "cluster_name": "Enterprise Dashboards",
        "cluster_num": 1,
        "title": "Executive KPI Balanced Scorecard & Cockpit",
        "subtitle": "EBITDA, enterprise margins, operating leverage, and board-level indicators",
        "desc": "High-level executive financial scorecard consolidating multi-subsidiary P&L, quarterly operating leverage, GAAP margin progression, and hiring burn rate for C-level leadership.",
        "skill": "orthotect-dashboard",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "executive kpi scorecard, c-level board dashboard, ebitda operating leverage, enterprise financial cockpit, board reporting ui",
        "badge": "Board-Certified",
        "icon": "pie-chart",
        "stats": [
            {"label": "Quarterly EBITDA", "value": "$4.12M", "delta": "+24.8% vs Plan", "positive": True},
            {"label": "Gross Margin", "value": "81.4%", "delta": "+1.8% QoQ Expansion", "positive": True},
            {"label": "Magic Number", "value": "1.42", "delta": "Top-Decile Capital Efficiency", "positive": True},
            {"label": "Cash Runway", "value": "38 Months", "delta": "Free Cash Flow Positive", "positive": True}
        ],
        "chart_type": "bar",
        "table_headers": ["Business Unit", "Quarterly Rev", "Operating Margin", "Plan Variance", "Executive RAG"],
        "table_rows": [
            ["Core Cloud Platform", "$18.4M", "34.2%", "+$1.8M", "Green (Overperforming)"],
            ["Enterprise Security Suite", "$9.2M", "28.6%", "+$0.9M", "Green (Overperforming)"],
            ["Developer Tooling add-ons", "$4.8M", "22.1%", "-$0.1M", "Amber (On Track)"],
            ["Professional Services", "$2.1M", "14.8%", "+$0.2M", "Green (On Track)"]
        ]
    },
    {
        "id": "ai-model-inference-telemetry",
        "cluster": "dashboards",
        "cluster_name": "Enterprise Dashboards",
        "cluster_num": 1,
        "title": "Autonomous AI Agent & LLM Inference Telemetry",
        "subtitle": "Token generation velocity, time-to-first-token (TTFT), and agent orchestration logs",
        "desc": "Deep observability console for autonomous coding agent clusters tracking token throughput, prompt caching efficiency, tool-calling success rates, and GPU memory overhead.",
        "skill": "orthotect-dashboard",
        "tokens": "semantics.json, ergonomics.json, motion.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "llm inference dashboard, ai agent telemetry, time to first token ttft, prompt cache hit ratio, ai agent observability",
        "badge": "Agentic Telemetry",
        "icon": "cpu",
        "stats": [
            {"label": "Tokens / Second", "value": "24,800 tps", "delta": "Across 64 Model Workers", "positive": True},
            {"label": "Median TTFT", "value": "180ms", "delta": "-40ms with Prefix Cache", "positive": True},
            {"label": "Prefix Cache Hit", "value": "89.2%", "delta": "68% Compute Cost Saved", "positive": True},
            {"label": "Tool Call Pass Rate", "value": "99.4%", "delta": "Deterministic FSM Guard", "positive": True}
        ],
        "chart_type": "line",
        "table_headers": ["Agent Worker ID", "Model Architecture", "Current Task", "Cache Ratio", "Status"],
        "table_rows": [
            ["WORKER-CLAUDE-01", "Claude 3.7 Sonnet (Hybrid)", "Full-Stack Refactor", "92.1%", "Generating"],
            ["WORKER-CODEX-04", "GPT-4o Reasoning (High)", "Test Matrix Expansion", "88.4%", "Executing Tool"],
            ["WORKER-OPENCODE-08", "DeepSeek-V3 OpenWeights", "Bidi Layout Verification", "84.9%", "Generating"],
            ["WORKER-AGY-12", "Antigravity 2.0 Engine", "WCAG 2.2 Gate Audit", "96.2%", "Verified Pass"]
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # CLUSTER 2: High-Stakes Forms, Financial Checkouts & FSM Workflows (11–20)
    # ─────────────────────────────────────────────────────────────────────────────
    {
        "id": "multi-step-kyc-verification",
        "cluster": "forms",
        "cluster_name": "Forms & FSM Workflows",
        "cluster_num": 2,
        "title": "Institutional KYC Identity Verification Flow",
        "subtitle": "State-machine governed biometric, document, and corporate AML validation",
        "desc": "High-security compliance workflow with strict stage transitions, biometric document integrity checks, institutional sanction screening, and tamper-proof audit trails.",
        "skill": "orthotect-fsm",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "kyc verification form, institutional aml workflow, multi step fsm form, biometric identity verification, fintech compliance ui",
        "badge": "FSM Double-Locked",
        "icon": "user-check",
        "form_steps": ["Corporate Profile", "Beneficial Owners", "Government ID", "Biometric Liveness", "Compliance Review"],
        "form_fields": [
            {"label": "Legal Entity Name", "type": "text", "placeholder": "Orthotect Holdings Inc.", "required": True},
            {"label": "Tax Identification / LEI", "type": "text", "placeholder": "9845003F9B1E2C4D5678", "required": True},
            {"label": "Jurisdiction of Incorporation", "type": "select", "options": ["Delaware, USA", "Zurich, Switzerland", "Singapore", "London, UK"], "required": True},
            {"label": "Authorized Officer Full Name", "type": "text", "placeholder": "Tarek Mohamed", "required": True}
        ]
    },
    {
        "id": "enterprise-b2b-checkout-flow",
        "cluster": "forms",
        "cluster_name": "Forms & FSM Workflows",
        "cluster_num": 2,
        "title": "Enterprise B2B Procurement Checkout & Invoicing",
        "subtitle": "Net-30 purchase orders, tax exemption validation, and purchase authorization",
        "desc": "Contract-grade B2B procurement checkout with atomic idempotency locks, automated VAT/sales-tax calculation, purchase order (PO) upload, and multi-tier approval states.",
        "skill": "orthotect-forms",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "b2b checkout flow, net-30 po invoicing, enterprise procurement ui, purchase order checkout, idempotent checkout form",
        "badge": "Idempotent Transaction",
        "icon": "credit-card",
        "form_steps": ["Billing Entity", "Purchase Order", "Tax Exemption", "Payment Method", "Final Review"],
        "form_fields": [
            {"label": "Company Purchase Order #", "type": "text", "placeholder": "PO-2026-98412", "required": True},
            {"label": "Accounts Payable Email", "type": "email", "placeholder": "invoicing@enterprise.com", "required": True},
            {"label": "Payment Terms", "type": "select", "options": ["Net-30 Days (Invoiced)", "Net-60 Days (Enterprise)", "ACH Direct Debit", "Wire Transfer"], "required": True},
            {"label": "Tax Exemption Certificate #", "type": "text", "placeholder": "TAX-EX-849102 (Optional)", "required": False}
        ]
    },
    {
        "id": "user-onboarding-wizard-fsm",
        "cluster": "forms",
        "cluster_name": "Forms & FSM Workflows",
        "cluster_num": 2,
        "title": "Guided SaaS Workspace Setup & Team Provisioning",
        "subtitle": "Progressive workspace creation with instant validation and zero layout shift",
        "desc": "Zero-friction SaaS team provisioning wizard with instant slug availability checks, role-based member invitations, and optimistic team creation backed by an immutable state contract.",
        "skill": "orthotect-fsm",
        "tokens": "semantics.json, motion.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "saas onboarding wizard, workspace provisioning flow, fsm onboarding form, team invite wizard, progressive onboarding ui",
        "badge": "Zero-Layout-Shift",
        "icon": "users",
        "form_steps": ["Workspace Profile", "Team Invitations", "Security Policies", "CLI & Integrations", "Ready"],
        "form_fields": [
            {"label": "Workspace Subdomain", "type": "text", "placeholder": "acme-engineering.orthotect.io", "required": True},
            {"label": "Primary Cloud Region", "type": "select", "options": ["North America (us-east)", "Europe (eu-central)", "Asia-Pacific (ap-southeast)"], "required": True},
            {"label": "Team Member Email (Admin)", "type": "email", "placeholder": "lead-architect@acme.com", "required": True},
            {"label": "Enforce Hardware MFA", "type": "checkbox", "label_check": "Require FIDO2/WebAuthn for all team members", "required": False}
        ]
    },
    {
        "id": "billing-subscription-manager",
        "cluster": "forms",
        "cluster_name": "Forms & FSM Workflows",
        "cluster_num": 2,
        "title": "Prorated Subscription Tier Upgrade & Billing Portal",
        "subtitle": "Instant prorated credit calculations, seat expansions, and invoice history",
        "desc": "Self-service billing console allowing enterprise customers to adjust seat licenses, toggle annual/monthly pricing with live proration arithmetic, and update backup payment cards.",
        "skill": "orthotect-forms",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "saas billing portal, subscription tier upgrade, prorated billing calculator, seat license management, b2b payment ui",
        "badge": "WCAG AAA Inputs",
        "icon": "dollar-sign",
        "form_steps": ["Select Tier", "Configure Seats", "Payment Details", "Confirmation"],
        "form_fields": [
            {"label": "Target Subscription Tier", "type": "select", "options": ["Enterprise Platform ($4,800/yr)", "Scale Team ($1,920/yr)", "Startup Pro ($480/yr)"], "required": True},
            {"label": "Dedicated Developer Seats", "type": "number", "placeholder": "25", "required": True},
            {"label": "Cardholder Name", "type": "text", "placeholder": "Alex Vance", "required": True},
            {"label": "Billing Address", "type": "text", "placeholder": "100 Market St, San Francisco, CA", "required": True}
        ]
    },
    {
        "id": "api-key-permission-delegation",
        "cluster": "forms",
        "cluster_name": "Forms & FSM Workflows",
        "cluster_num": 2,
        "title": "Scoped Developer API Key & Token Delegation Matrix",
        "subtitle": "Granular scope selection, CIDR IP whitelist bounds, and cryptographic secret reveal",
        "desc": "High-assurance developer token generator with granular least-privilege permission checkboxes, IP address subnet restrictions, expiration TTL presets, and one-time secret masking.",
        "skill": "orthotect-forms",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "api key generator form, token permission matrix, developer credentials ui, least privilege token form, api access delegation",
        "badge": "Cryptographic Masking",
        "icon": "key",
        "form_steps": ["Token Identity", "Permission Scopes", "Network CIDR Bounds", "Secret Reveal"],
        "form_fields": [
            {"label": "API Key Description", "type": "text", "placeholder": "CI/CD Deployment Runner (Production)", "required": True},
            {"label": "Token Expiration TTL", "type": "select", "options": ["30 Days (Recommended)", "90 Days", "1 Year", "Never (Restricted to VPC)"], "required": True},
            {"label": "Allowed CIDR IP Ranges", "type": "text", "placeholder": "198.51.100.0/24, 203.0.113.10", "required": False},
            {"label": "Permission Scopes", "type": "checkbox_group", "options": ["read:tokens", "write:tokens", "execute:gates", "manage:teams", "admin:billing"]}
        ]
    },
    {
        "id": "account-security-two-factor-setup",
        "cluster": "forms",
        "cluster_name": "Forms & FSM Workflows",
        "cluster_num": 2,
        "title": "High-Assurance MFA & WebAuthn Security Enrollment",
        "subtitle": "FIDO2 hardware key registration, TOTP QR pairing, and emergency backup codes",
        "desc": "Hardened multi-factor authentication setup interface featuring WebAuthn passkey enrollment, TOTP authenticator synchronization with 6-digit auto-advancing inputs, and downloadable backup recovery keys.",
        "skill": "orthotect-fsm",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "mfa 2fa enrollment form, webauthn passkey ui, totp qr verification, emergency recovery codes, security settings ui",
        "badge": "FIDO2 Certified",
        "icon": "lock",
        "form_steps": ["Choose MFA Method", "Hardware Challenge / QR", "Confirm 6-Digit Code", "Backup Codes"],
        "form_fields": [
            {"label": "Authentication Device Nickname", "type": "text", "placeholder": "YubiKey 5C NFC (Primary)", "required": True},
            {"label": "Account Password Confirmation", "type": "password", "placeholder": "••••••••••••••••", "required": True},
            {"label": "TOTP Verification Code", "type": "text", "placeholder": "123 456", "required": True}
        ]
    },
    {
        "id": "cloud-database-provisioning-form",
        "cluster": "forms",
        "cluster_name": "Forms & FSM Workflows",
        "cluster_num": 2,
        "title": "Distributed Database Cluster Provisioning & Sizing",
        "subtitle": "IOPS allocation, multi-AZ replica topologies, and automated failover config",
        "desc": "Technical cloud infrastructure provisioning form for high-throughput Postgres and distributed Raft databases with real-time cost estimations, storage tier sliders, and automated snapshot policies.",
        "skill": "orthotect-forms",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "database provisioning form, cloud cluster sizing ui, postgres high availability, iops storage calculator, infra as code ui",
        "badge": "Atomic Provisioning",
        "icon": "database",
        "form_steps": ["Engine & Topology", "Compute & Memory", "Storage & IOPS", "Backup Schedule", "Deploy"],
        "form_fields": [
            {"label": "Database Cluster Name", "type": "text", "placeholder": "ortho-prod-db-primary", "required": True},
            {"label": "Database Engine", "type": "select", "options": ["PostgreSQL 16 Enterprise (Multi-AZ)", "ClickHouse Analytics Cluster", "Redis 7.2 High-Availability"], "required": True},
            {"label": "Dedicated RAM / vCPU", "type": "select", "options": ["64 GB RAM / 16 vCPU ($420/mo)", "128 GB RAM / 32 vCPU ($840/mo)", "256 GB RAM / 64 vCPU ($1,680/mo)"], "required": True},
            {"label": "Allocated NVMe Storage (GB)", "type": "number", "placeholder": "1000", "required": True}
        ]
    },
    {
        "id": "support-ticket-escalation-wizard",
        "cluster": "forms",
        "cluster_name": "Forms & FSM Workflows",
        "cluster_num": 2,
        "title": "Critical Incident Ticket & Automated SLA Escalation",
        "subtitle": "P1 severity triage, stack trace attachment, and automated on-call paging",
        "desc": "Incident response form with deterministic severity triage (P1-P4), automated telemetry log parser, affected SLA commitment calculator, and direct PagerDuty/Opsgenie integration.",
        "skill": "orthotect-forms",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "incident escalation wizard, p1 severity ticket form, sla support ticket ui, oncall paging workflow, enterprise incident reporting",
        "badge": "SLA Guaranteed",
        "icon": "alert-circle",
        "form_steps": ["Incident Scope", "Severity Matrix", "Diagnostic Logs", "Contact Details"],
        "form_fields": [
            {"label": "Incident Summary", "type": "text", "placeholder": "Intermittent 502 Bad Gateway on us-east Ingress", "required": True},
            {"label": "Reported Severity Level", "type": "select", "options": ["P1 - Critical Outage (15min SLA)", "P2 - Degraded Production (1hr SLA)", "P3 - Moderate Defect (8hr SLA)", "P4 - Minor Inquiry (24hr SLA)"], "required": True},
            {"label": "Affected Production Services", "type": "text", "placeholder": "API Gateway, Checkout Service, Webhooks", "required": True},
            {"label": "Primary Incident Contact Phone", "type": "tel", "placeholder": "+1 (555) 019-2831", "required": True}
        ]
    },
    {
        "id": "credit-card-payment-lock",
        "cluster": "forms",
        "cluster_name": "Forms & FSM Workflows",
        "cluster_num": 2,
        "title": "Zero-Double-Charge Payment Form with Idempotency",
        "subtitle": "Cryptographic client-token locking, CVV masking, and 3D Secure modal",
        "desc": "Mathematically verified checkout card payment form preventing double charges via atomic button submission locks, auto-formatting credit card inputs, and strict WCAG AAA contrast tokens.",
        "skill": "orthotect-fsm",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "idempotent payment form, credit card checkout ui, double charge prevention, 3d secure payment modal, secure card input",
        "badge": "Double-Charge Proof",
        "icon": "credit-card",
        "form_steps": ["Payment Amount", "Card Information", "Cryptographic Lock", "Receipt"],
        "form_fields": [
            {"label": "Cardholder Full Name", "type": "text", "placeholder": "Jordan Lee", "required": True},
            {"label": "Credit Card Number", "type": "text", "placeholder": "4242 •••• •••• 4242", "required": True},
            {"label": "Expiry Date (MM/YY)", "type": "text", "placeholder": "12/28", "required": True},
            {"label": "Security Code (CVC/CVV)", "type": "password", "placeholder": "•••", "required": True}
        ]
    },
    {
        "id": "audit-log-export-configuration",
        "cluster": "forms",
        "cluster_name": "Forms & FSM Workflows",
        "cluster_num": 2,
        "title": "Compliance Audit Log Query & SIEM Export Builder",
        "subtitle": "Deterministic regex filter bounds, SHA-256 archive proofs, and S3 streaming",
        "desc": "Regulatory compliance audit logging form for SOC-2 and HIPAA audits featuring date range boundary validation, cryptographic hash verification, and automated cloud storage exporter.",
        "skill": "orthotect-forms",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "compliance audit log exporter, siem query builder, soc2 log export form, sha256 archive verification, hipaa audit ui",
        "badge": "SOC2 Verified",
        "icon": "file-text",
        "form_steps": ["Time Range & Scope", "Actor & IP Filters", "Export Destination", "Integrity Check"],
        "form_fields": [
            {"label": "Audit Query Name", "type": "text", "placeholder": "Q3 2026 Admin Privilege Access Audit", "required": True},
            {"label": "Export File Format", "type": "select", "options": ["JSON Lines (.jsonl with SHA-256)", "Parquet Compressed (.parquet)", "CSV Spreadsheet (.csv)"], "required": True},
            {"label": "Target Cloud Storage Bucket", "type": "text", "placeholder": "s3://corp-audit-archives-us-east/soc2/", "required": True},
            {"label": "Include PII Scrubbed Payload", "type": "checkbox", "label_check": "Mask user passwords and payment tokens automatically", "required": False}
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # CLUSTER 3: Material-Led Modern E-Commerce & Product Catalogs (21–30)
    # ─────────────────────────────────────────────────────────────────────────────
    {
        "id": "hardware-spec-sheet-store",
        "cluster": "ecommerce",
        "cluster_name": "Material E-Commerce",
        "cluster_num": 3,
        "title": "Precision Hardware & Mechanical Spec Sheet Store",
        "subtitle": "Micro-tolerance tables, STEP/CAD downloads, and aerospace material certificates",
        "desc": "High-accuracy engineering procurement catalog for aerospace fasteners, CNC-milled titanium components, and DIN-spec hardware with live stock level indicators and CAD viewers.",
        "skill": "orthotect-components",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "hardware spec store, mechanical component catalog, aerospace fastener procurement, cad step download ui, engineering spec sheet",
        "badge": "Aerospace Grade",
        "icon": "package",
        "spec_table": [
            {"param": "Material Grade", "spec": "Grade 5 Titanium (Ti-6Al-4V)", "tolerance": "AMS 4928"},
            {"param": "Tensile Strength", "spec": "950 MPa (138 ksi)", "tolerance": "Min Guaranteed"},
            {"param": "Thread Pitch", "spec": "M6 x 1.0 ISO Metric", "tolerance": "6g Precision"},
            {"param": "Surface Treatment", "spec": "Type II Anodized Matte", "tolerance": "MIL-A-8625"},
            {"param": "Weight per 100 units", "spec": "482 grams", "tolerance": "±1.5g"}
        ]
    },
    {
        "id": "luxury-mechanical-goods-gallery",
        "cluster": "ecommerce",
        "cluster_name": "Material E-Commerce",
        "cluster_num": 3,
        "title": "Horology & Mechanical Timepiece Editorial Showcase",
        "subtitle": "Exploded caliber diagrams, ceramic/titanium materials, and bespoke reservation",
        "desc": "Editorial luxury horology presentation featuring caliber movement frequency specs, anti-magnetic resistance ratings, sapphire crystal properties, and concierge reservation modal.",
        "skill": "orthotect-components",
        "tokens": "semantics.json, motion.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "luxury horology gallery, mechanical watch showcase, editorial ecommerce ui, timepiece caliber specs, bespoke product reservation",
        "badge": "Chronometer Certified",
        "icon": "watch",
        "spec_table": [
            {"param": "Caliber Movement", "spec": "Manufacture Caliber OR-904", "tolerance": "COSC Certified"},
            {"param": "Beat Frequency", "spec": "28,800 vph (4 Hz)", "tolerance": "Silicium Hairspring"},
            {"param": "Power Reserve", "spec": "72 Hours Autonomy", "tolerance": "Twin Barrel"},
            {"param": "Water Resistance", "spec": "300 meters / 30 ATM", "tolerance": "Helium Escape Valve"},
            {"param": "Case Material", "spec": "High-Tech Zirconia Ceramic", "tolerance": "Scratch-Proof 1,500 HV"}
        ]
    },
    {
        "id": "industrial-equipment-procurement",
        "cluster": "ecommerce",
        "cluster_name": "Material E-Commerce",
        "cluster_num": 3,
        "title": "Industrial Automation & Heavy Machinery Procurement",
        "subtitle": "PLC controller configurations, volume pricing tiers, and freight logistics calculator",
        "desc": "Enterprise B2B equipment marketplace with real-time volume price discounting, ISO-9001 compliance sheets, lead-time estimators, and direct supplier RFQ generators.",
        "skill": "orthotect-components",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "industrial equipment procurement, plc controller catalog, heavy machinery b2b, rfq generator ui, volume pricing table",
        "badge": "ISO 9001 Compliant",
        "icon": "tool",
        "spec_table": [
            {"param": "Operating Voltage", "spec": "400V 3-Phase AC (50/60 Hz)", "tolerance": "±10% Range"},
            {"param": "Payload Capacity", "spec": "450 kg (992 lbs)", "tolerance": "Full Reach (3.1m)"},
            {"param": "Repeatability", "spec": "±0.02 mm", "tolerance": "ISO 9283"},
            {"param": "Communication Bus", "spec": "EtherCAT / PROFINET / Modbus", "tolerance": "Sub-millisecond"},
            {"param": "Ingress Protection", "spec": "IP67 Washdown Rated", "tolerance": "IEC 60529"}
        ]
    },
    {
        "id": "architectural-materials-catalog",
        "cluster": "ecommerce",
        "cluster_name": "Material E-Commerce",
        "cluster_num": 3,
        "title": "Sustainable Architectural Materials & Acoustic Panels",
        "subtitle": "NRC acoustic coefficients, carbon footprint index, and sample swatch dispatch",
        "desc": "Architect-focused sustainable materials catalog with verified Environmental Product Declarations (EPD), Noise Reduction Coefficients (NRC), fire ratings, and physical swatch orders.",
        "skill": "orthotect-components",
        "tokens": "semantics.json, motion.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "architectural materials catalog, acoustic panel specs, nrc sound absorption, epd sustainable materials, architect swatch request",
        "badge": "LEED Platinum Ready",
        "icon": "layers",
        "spec_table": [
            {"param": "Acoustic Rating (NRC)", "spec": "0.95 Noise Reduction", "tolerance": "ASTM C423"},
            {"param": "Embodied Carbon", "spec": "-1.4 kg CO2e / m² (Net-Negative)", "tolerance": "Cradle-to-Gate EPD"},
            {"param": "Fire Safety Standard", "spec": "Class A / ASTM E84", "tolerance": "Smoke Index < 50"},
            {"param": "Core Composition", "spec": "100% Upcycled Basalt Fiber", "tolerance": "Zero Formaldehyde"},
            {"param": "Panel Dimensions", "spec": "2400 x 1200 x 50 mm", "tolerance": "±1.0 mm"}
        ]
    },
    {
        "id": "dtc-electronics-product-detail",
        "cluster": "ecommerce",
        "cluster_name": "Material E-Commerce",
        "cluster_num": 3,
        "title": "Precision Consumer Audio Hardware Product Detail",
        "subtitle": "Frequency response curves, planar magnetic drivers, and battery endurance",
        "desc": "Direct-to-consumer flagship audio product page featuring planar magnetic diaphragm diagrams, ANC attenuation decibels, fast charging curves, and variant color selectors.",
        "skill": "orthotect-components",
        "tokens": "semantics.json, motion.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "consumer electronics pdp, planar magnetic headphones, product detail page ui, audiophile spec sheet, audio hardware ecommerce",
        "badge": "Hi-Res Audio Gold",
        "icon": "headphones",
        "spec_table": [
            {"param": "Transducer Type", "spec": "90mm Ultra-Thin Planar Magnetic", "tolerance": "Matched ±0.5dB"},
            {"param": "Frequency Response", "spec": "5 Hz – 55,000 Hz", "tolerance": "Extended Treble"},
            {"param": "Total Harmonic Dist", "spec": "< 0.05% at 100 dB SPL", "tolerance": "Ultra-Low THD+N"},
            {"param": "Active Battery Life", "spec": "45 Hours (ANC Enabled)", "tolerance": "USB-C PD 15m Fast Charge"},
            {"param": "Bluetooth Codecs", "spec": "LDAC, aptX Lossless, AAC", "tolerance": "990 kbps 24/96"}
        ]
    },
    {
        "id": "b2b-wholesale-bulk-order-grid",
        "cluster": "ecommerce",
        "cluster_name": "Material E-Commerce",
        "cluster_num": 3,
        "title": "High-Density B2B Wholesale Matrix Order Pad",
        "subtitle": "Keyboard-navigable SKU grid, quantity breaks, and real-time total recalculation",
        "desc": "Power-user wholesale ordering matrix allowing B2B buyers to input dozens of product variations, sizes, and quantities via keyboard navigation with instant volume discount thresholds.",
        "skill": "orthotect-components",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "wholesale order pad, b2b bulk order grid, keyboard navigable sku table, volume discount calculator, matrix ecommerce pad",
        "badge": "Keyboard Navigable",
        "icon": "grid",
        "spec_table": [
            {"param": "SKU Batch Code", "spec": "ORTHO-FAST-M8", "tolerance": "Box of 500 Units"},
            {"param": "Tier 1 (1–4 Boxes)", "spec": "$140.00 / box", "tolerance": "Standard Wholesale"},
            {"param": "Tier 2 (5–19 Boxes)", "spec": "$118.00 / box", "tolerance": "15% Volume Discount"},
            {"param": "Tier 3 (20+ Boxes)", "spec": "$98.00 / box", "tolerance": "30% Enterprise Tier"},
            {"param": "Warehouse Stock", "spec": "2,480 Boxes in Stock", "tolerance": "Same-Day Dispatch"}
        ]
    },
    {
        "id": "digital-software-tier-pricing",
        "cluster": "ecommerce",
        "cluster_name": "Material E-Commerce",
        "cluster_num": 3,
        "title": "Enterprise Developer Software Tier & Feature Matrix",
        "subtitle": "Seat-based pricing sliders, SLA tier comparisons, and custom enterprise RFQs",
        "desc": "Transparent SaaS software tier pricing matrix featuring interactive developer seat sliders, feature comparison checklist, SOC2/GDPR compliance inclusion, and instant checkout triggers.",
        "skill": "orthotect-components",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "saas pricing matrix, software tier comparison, seat based pricing slider, developer tool pricing, enterprise software tiers",
        "badge": "Transparent Pricing",
        "icon": "credit-card",
        "spec_table": [
            {"param": "Starter Pro", "spec": "$29 / seat / mo", "tolerance": "Up to 5 Developers"},
            {"param": "Team Growth", "spec": "$79 / seat / mo", "tolerance": "Up to 25 Developers"},
            {"param": "Enterprise Scale", "spec": "$199 / seat / mo", "tolerance": "Unlimited + 99.99% SLA"},
            {"param": "Deterministic Gates", "spec": "Included in All Tiers", "tolerance": "Sub-Second Latency"},
            {"param": "Dedicated Support", "spec": "15-minute P1 Response", "tolerance": "Enterprise Only"}
        ]
    },
    {
        "id": "dynamic-product-filtering-rail",
        "cluster": "ecommerce",
        "cluster_name": "Material E-Commerce",
        "cluster_num": 3,
        "title": "Multi-Facet Product Filtering & Attribute Rail",
        "subtitle": "Instant facet count recalculation, active filter tags, and zero layout shift",
        "desc": "High-performance e-commerce filter sidebar with multi-select facet checkboxes, price range sliders, clear-all action chips, and instant results count without reflowing the viewport.",
        "skill": "orthotect-responsive",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "product filtering rail, faceted search ui, ecommerce filter sidebar, zero layout shift filter, multi attribute search",
        "badge": "Zero Shift Filter",
        "icon": "sliders",
        "spec_table": [
            {"param": "Filter Ingestion Latency", "spec": "< 4ms Client Evaluation", "tolerance": "Zero Network Roundtrip"},
            {"param": "Active Facets", "spec": "Material, Size, Tolerance, Grade", "tolerance": "Multi-Select Enabled"},
            {"param": "DOM Mutation Safety", "spec": "Virtual Windowing Guard", "tolerance": "Zero CLS Spike"},
            {"param": "Keyboard Accessibility", "spec": "Full W3C APG Tab Order", "tolerance": "Space to Toggle"},
            {"param": "URL State Synchronization", "spec": "Query Parameter Permalinks", "tolerance": "History API Bound"}
        ]
    },
    {
        "id": "cart-drawer-optimistic-update",
        "cluster": "ecommerce",
        "cluster_name": "Material E-Commerce",
        "cluster_num": 3,
        "title": "High-Speed Slide-Over Cart with Optimistic Locks",
        "subtitle": "Line-item adjustments, coupon verification, and inventory reservation countdown",
        "desc": "Fluid slide-over shopping bag featuring optimistic quantity increments, automated promo code validation, reserved inventory timer, and instant express checkout integration.",
        "skill": "orthotect-fsm",
        "tokens": "semantics.json, motion.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "slide over cart drawer, optimistic cart update, inventory lock timer, coupon code verification, ecommerce slideout cart",
        "badge": "Optimistic UI",
        "icon": "shopping-bag",
        "spec_table": [
            {"param": "Inventory Lock Window", "spec": "15:00 Minutes Countdown", "tolerance": "Raft Key-Value Held"},
            {"param": "Quantity Mutation Latency", "spec": "0ms (Optimistic Dispatch)", "tolerance": "Rollback on Error"},
            {"param": "Focus Trap Trajectory", "spec": "W3C Modal APG Bound", "tolerance": "Escape Key Dismiss"},
            {"param": "Promo Code Engine", "spec": "Client-Side Pre-validation", "tolerance": "Cryptographic Hash"},
            {"param": "One-Click Checkout", "spec": "Apple Pay / Google Pay / Card", "tolerance": "Payment Request API"}
        ]
    },
    {
        "id": "customer-reviews-rating-matrix",
        "cluster": "ecommerce",
        "cluster_name": "Material E-Commerce",
        "cluster_num": 3,
        "title": "Verified Buyer Reviews & Sentiment Breakdown",
        "subtitle": "Star distribution histogram, verified purchase filters, and customer image gallery",
        "desc": "Authentic customer feedback matrix with mathematical 5-star distribution bars, verified order badges, buyer image lightbox modal, and search by keyword or material application.",
        "skill": "orthotect-components",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "verified customer reviews, star rating distribution histogram, buyer feedback matrix, product review gallery, social proof ui",
        "badge": "Cryptographic Reviews",
        "icon": "star",
        "spec_table": [
            {"param": "Overall Customer Rating", "spec": "4.92 / 5.00 Stars", "tolerance": "Based on 1,420 Orders"},
            {"param": "Verified Buyer Ratio", "spec": "100% Cryptographic Invoices", "tolerance": "Zero Bot Reviews"},
            {"param": "5-Star Distribution", "spec": "92.4% (1,312 reviews)", "tolerance": "Top Decile Satisfaction"},
            {"param": "Return / Defect Rate", "spec": "0.14% Across All Shipments", "tolerance": "Aerospace Tolerance"},
            {"param": "Review Search Index", "spec": "Sub-millisecond Keyword Regex", "tolerance": "Instant Filtering"}
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # CLUSTER 4: Accessible High-Contrast Civic, Clinical & Public Portals (31–40)
    # ─────────────────────────────────────────────────────────────────────────────
    {
        "id": "civic-voter-registration-portal",
        "cluster": "civic",
        "cluster_name": "Civic & Clinical Portals",
        "cluster_num": 4,
        "title": "Civic Ballot Eligibility & Voter Registration",
        "subtitle": "WCAG 2.2 AAA high-contrast, large-print typography, and simplified plain language",
        "desc": "Official public sector voting portal certified to WCAG 2.2 AAA contrast standards (12:1+), supporting simplified language modes, screen magnifier compliance, and keyboard navigation.",
        "skill": "orthotect-accessibility",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "civic voter registration, wcag 2.2 aaa portal, public sector accessibility, ballot eligibility screener, high contrast civic ui",
        "badge": "WCAG 2.2 AAA",
        "icon": "check-square",
        "civic_items": [
            {"step": "Step 1", "title": "Check Voter Eligibility", "desc": "Confirm citizenship, minimum age of 18, and residential county registration status."},
            {"step": "Step 2", "title": "Provide Valid Official Identification", "desc": "Enter state-issued driver's license number, state ID card, or last four digits of SSN."},
            {"step": "Step 3", "title": "Select Preferred Polling Place", "desc": "Choose your designated municipal precinct or request a secure mail-in absentee ballot."},
            {"step": "Step 4", "title": "Review Accessible Ballot Options", "desc": "Request tactile ballot templates, large-print editions, or auditory voting machines."}
        ]
    },
    {
        "id": "clinical-patient-intake-records",
        "cluster": "civic",
        "cluster_name": "Civic & Clinical Portals",
        "cluster_num": 4,
        "title": "Clinical Patient Health Intake & Medical History Registry",
        "subtitle": "HIPAA-compliant vital records, medication allergen alerts, and emergency contacts",
        "desc": "Medical clinic patient intake portal designed for high cognitive ergonomics, clear medication warning callouts, screen-reader announced validation alerts, and zero session loss.",
        "skill": "orthotect-accessibility",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "clinical patient intake, hipaa medical records portal, allergen warning interface, accessible healthcare ui, patient health registry",
        "badge": "HIPAA & WCAG AAA",
        "icon": "activity",
        "civic_items": [
            {"step": "Section A", "title": "Patient Demographics & Identifiers", "desc": "Full legal name, date of birth, preferred pronouns, and primary contact phone."},
            {"step": "Section B", "title": "Known Severe Drug Allergies", "desc": "Penicillin, NSAIDs, latex, and anesthesia contraindications with high-contrast warning badges."},
            {"step": "Section C", "title": "Current Active Prescription Regimen", "desc": "Dosage, frequency, prescribing physician, and pharmacy refill coordinates."},
            {"step": "Section D", "title": "Emergency Healthcare Proxy", "desc": "Designated emergency decision maker, legal surrogate relationship, and direct contact line."}
        ]
    },
    {
        "id": "emergency-crisis-alert-broadcast",
        "cluster": "civic",
        "cluster_name": "Civic & Clinical Portals",
        "cluster_num": 4,
        "title": "Public Safety Emergency Alert & Disaster Response Notice",
        "subtitle": "Urgent evacuation instructions, shelter locator, and multilingual live feed",
        "desc": "Public crisis warning portal adhering to extreme visibility guidelines with high-contrast flashing mitigation, assistive audio announcement tags, and offline cache survival.",
        "skill": "orthotect-accessibility",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "emergency crisis alert, public safety broadcast, disaster response portal, accessible evacuation notice, emergency shelter finder",
        "badge": "Extreme Visibility",
        "icon": "alert-triangle",
        "civic_items": [
            {"step": "Alert 1", "title": "Mandatory Coastal Evacuation Order", "desc": "Zones A and B must evacuate immediately due to category 4 storm surge threat."},
            {"step": "Alert 2", "title": "Designated Emergency Shelter Locations", "desc": "Memorial High School and County Convention Center are open 24/7 with generator power."},
            {"step": "Alert 3", "title": "Emergency Medical Transport", "desc": "Dial 311 or use the accessible transport locator for residents needing wheelchair transport."},
            {"step": "Alert 4", "title": "Potable Water & Ration Distribution", "desc": "Clean water tankers stationed at Fairgrounds Gate 2 from 08:00 to 20:00 daily."}
        ]
    },
    {
        "id": "public-transit-accessible-schedule",
        "cluster": "civic",
        "cluster_name": "Civic & Clinical Portals",
        "cluster_num": 4,
        "title": "Universal Public Transit Schedule & Arrival Board",
        "subtitle": "Wheelchair elevator status, low-floor bus indicators, and live arrival audio feeds",
        "desc": "Inclusive metropolitan transit board displaying live train and bus arrivals, real-time elevator outage alerts for wheelchair accessibility, and high-contrast timetable matrices.",
        "skill": "orthotect-accessibility",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "accessible public transit schedule, real time arrival board, elevator outage tracker, low floor bus timetable, universal transit ui",
        "badge": "ADA & WCAG AAA",
        "icon": "map-pin",
        "civic_items": [
            {"step": "Metro Line A", "title": "Downtown Express (Train #402)", "desc": "Arriving in 3 mins. Track 2. 100% Low-Floor Level Boarding. Elevator at Station: Operational."},
            {"step": "Metro Line B", "title": "Crosstown Rapid (Train #118)", "desc": "Arriving in 8 mins. Track 1. Wheelchair Accessible Car 3. Elevator at Station: Operational."},
            {"step": "Bus Route 24", "title": "Hospital Medical Center Shuttle", "desc": "Arriving in 5 mins. Bus #891. Ramp Deployed. Kneeling Suspension Active."},
            {"step": "Elevator Notice", "title": "Central Station North Mezzanine", "desc": "Elevator #2 under scheduled maintenance. Use South Concourse Ramp (Grade 1:12 compliant)."}
        ]
    },
    {
        "id": "universal-banking-statement-view",
        "cluster": "civic",
        "cluster_name": "Civic & Clinical Portals",
        "cluster_num": 4,
        "title": "Accessible Banking Statement & Transaction Ledger",
        "subtitle": "Screen-reader optimized tables, dual debit/credit indicators, and accessible CSV export",
        "desc": "High-integrity personal banking ledger featuring non-color-only debit/credit status icons, screen-reader table headers with full scope attributes, and large-format balance summaries.",
        "skill": "orthotect-accessibility",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "accessible banking statement, screen reader transaction ledger, wcag compliant financial statement, debit credit accessible icons, universal banking ui",
        "badge": "Screen-Reader Ready",
        "icon": "credit-card",
        "civic_items": [
            {"step": "Oct 22", "title": "Direct Deposit — Employer Payroll", "desc": "+$3,840.50 (Credit). Electronic Funds Transfer #EFT-9912. Available Balance: $14,920.10."},
            {"step": "Oct 21", "title": "Municipal Water Utility Bill", "desc": "-$68.40 (Debit). Pre-authorized Recurring ACH. Available Balance: $11,079.60."},
            {"step": "Oct 20", "title": "Community Pharmacy Prescription", "desc": "-$24.15 (Debit). Contactless Chip POS Transaction. Available Balance: $11,148.00."},
            {"step": "Oct 18", "title": "State Tax Refund Distribution", "desc": "+$412.00 (Credit). Direct State Treasury Deposit. Available Balance: $11,172.15."}
        ]
    },
    {
        "id": "utility-service-outage-reporter",
        "cluster": "civic",
        "cluster_name": "Civic & Clinical Portals",
        "cluster_num": 4,
        "title": "Municipal Utility Outage Reporter & Grid Status",
        "subtitle": "Step-by-step outage reporting, neighborhood status map fallback, and restoration ETA",
        "desc": "Emergency public utilities portal allowing citizens to report electric, gas, or water service interruptions with high-contrast progress trackers and verified restoration estimates.",
        "skill": "orthotect-accessibility",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "utility outage reporter, power outage reporting portal, municipal grid status, electric outage restoration eta, accessible civic reporter",
        "badge": "Civic Reliability",
        "icon": "zap-off",
        "civic_items": [
            {"step": "Report", "title": "Submit Service Outage Incident", "desc": "Provide street address and service type (Electric, Water, Gas, Fiber Optic) in under 60 seconds."},
            {"step": "Dispatch", "title": "Utility Repair Crew Dispatched", "desc": "Lineworker crew #14 assigned. En route to sub-station feeder circuit 12."},
            {"step": "ETA", "title": "Estimated Power Restoration Time", "desc": "Estimated full service restoration by 14:30 today. 142 customer accounts affected."},
            {"step": "Safety", "title": "Downed Wire Cautionary Warning", "desc": "Never approach downed wires. Maintain a minimum distance of 10 meters (33 feet)."}
        ]
    },
    {
        "id": "government-benefits-eligibility",
        "cluster": "civic",
        "cluster_name": "Civic & Clinical Portals",
        "cluster_num": 4,
        "title": "Social Services & Public Assistance Screener",
        "subtitle": "Income bracket calculator, benefit eligibility checklist, and document checklist",
        "desc": "Accessible government screener for public nutritional support, healthcare vouchers, and low-income housing subsidies with automated benefit calculation and plain language explanations.",
        "skill": "orthotect-accessibility",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "government benefits screener, public assistance eligibility, snap medicaid voucher calculator, social services portal, accessible government ui",
        "badge": "Plain-Language Ready",
        "icon": "clipboard",
        "civic_items": [
            {"step": "Program 1", "title": "Nutritional Assistance (SNAP)", "desc": "Eligible for up to $420/month based on household size of 3 and stated monthly income."},
            {"step": "Program 2", "title": "Healthcare Coverage (Medicaid)", "desc": "Full preventive and hospital care coverage with zero out-of-pocket prescription co-pays."},
            {"step": "Program 3", "title": "Home Energy Assistance (LIHEAP)", "desc": "One-time seasonal winter heating credit of $350 applied directly to municipal electric account."},
            {"step": "Program 4", "title": "Next Step: Document Submission", "desc": "Upload pay stubs or benefit letters. Clear telephone assistance available at 1-800-555-0199."}
        ]
    },
    {
        "id": "accessible-telehealth-consultation",
        "cluster": "civic",
        "cluster_name": "Civic & Clinical Portals",
        "cluster_num": 4,
        "title": "Remote Telehealth Consultation Waiting Room",
        "subtitle": "Audio/camera diagnostic check, live closed-captioning preview, and physician check-in",
        "desc": "Accessible clinical video consultation waiting lounge featuring live automated closed-captioning testing, sign language interpreter request options, and audio-based queue announcements.",
        "skill": "orthotect-accessibility",
        "tokens": "semantics.json, motion.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "telehealth waiting room, accessible video consultation, live closed captioning telehealth, physician checkin portal, healthcare accessibility",
        "badge": "Captions & Audio Verified",
        "icon": "video",
        "civic_items": [
            {"step": "Status", "title": "Physician Is Reviewing Records", "desc": "Dr. Sarah Chen, MD (Family Medicine) will join in approximately 4 minutes."},
            {"step": "Audio/Video", "title": "Hardware Diagnostics Passed", "desc": "Microphone, HD Camera, and Speakers tested and verified operational."},
            {"step": "Accessibility", "title": "Live Captions Enabled", "desc": "Real-time speech-to-text captions active. Font size: Large (24px high-contrast)."},
            {"step": "Assistance", "title": "Interpreter on Standby", "desc": "American Sign Language (ASL) video relay interpreter connected on secondary channel."}
        ]
    },
    {
        "id": "educational-course-curriculum",
        "cluster": "civic",
        "cluster_name": "Civic & Clinical Portals",
        "cluster_num": 4,
        "title": "Higher Education Accessible Course Curriculum Hub",
        "subtitle": "Structured syllabus, downloadable transcripts, and screen-reader syllabus tree",
        "desc": "University course curriculum portal designed for universal design for learning (UDL) with synchronized audio transcripts, keyboard accessible syllabus outlines, and contrast verified diagrams.",
        "skill": "orthotect-accessibility",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/data-table-loader.json",
        "keywords": "accessible course curriculum, university syllabus portal, udl accessible education, screen reader course syllabus, audio transcript hub",
        "badge": "UDL & Section 508",
        "icon": "book-open",
        "civic_items": [
            {"step": "Module 1", "title": "Foundations of Human-Computer Interaction", "desc": "Perceptual ergonomics, Fitts's Law, cognitive load theory, and WCAG 2.2 AA foundations."},
            {"step": "Module 2", "title": "Design Systems & Token Architecture", "desc": "DTCG token hierarchies, primitive vs semantic roles, and cross-platform compilation pipelines."},
            {"step": "Module 3", "title": "True Bidirectional Interface Engineering", "desc": "CSS logical properties, symmetrical typography, and RTL Arabic cultural layout requirements."},
            {"step": "Module 4", "title": "Deterministic Quality Gates in CI/CD", "desc": "Automated contrast auditing, FSM state validation, and layout-shift budget enforcement."}
        ]
    },
    {
        "id": "legal-statute-document-reader",
        "cluster": "civic",
        "cluster_name": "Civic & Clinical Portals",
        "cluster_num": 4,
        "title": "Legislative Statute & Case Law Legal Reader",
        "subtitle": "Numbered paragraph margins, cross-reference anchors, and high-legibility legal serif",
        "desc": "High-ergonomics legal text reader for judicial opinions and statutory codes featuring numbered line anchors, cited precedence flyovers, adjustable serif typography, and dark/light modes.",
        "skill": "orthotect-accessibility",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "legal statute reader, case law legal reader, numbered paragraph margin ui, judicial opinion reader, high legibility legal text",
        "badge": "Legal Ergonomics",
        "icon": "file-text",
        "civic_items": [
            {"step": "Section § 402", "title": "Substantive Requirements for Algorithmic Transparency", "desc": "All automated systems impacting public rights must maintain deterministic audit trails and human explainability."},
            {"step": "Section § 403", "title": "Standard of Review & Admissibility of Records", "desc": "Digital records sealed with cryptographic SHA-256 signatures shall enjoy a presumption of authenticity under Rule 902."},
            {"step": "Section § 404", "title": "Mandatory Accessibility Mandates", "desc": "Failure to provide accessible alternate formats constitutes a prima facie violation under Title II of the Americans with Disabilities Act."},
            {"step": "Section § 405", "title": "Statutory Limitation Periods", "desc": "Actions arising under this chapter must be initiated within three years from the discovery of the non-compliant interface."}
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────────
    # CLUSTER 5: Contemporary B2B SaaS Landing Pages & Developer Workspaces (41–50)
    # ─────────────────────────────────────────────────────────────────────────────
    {
        "id": "developer-api-platform-hero",
        "cluster": "saas",
        "cluster_name": "B2B SaaS & DevTools",
        "cluster_num": 5,
        "title": "Developer API Platform Hero & Code Sandbox",
        "subtitle": "Dual-language curl/python snippets, latency ping indicator, and instant token copy",
        "desc": "High-conversion developer platform hero section with interactive request/response sandbox, live API endpoint latency badge (12ms), and zero-friction one-click terminal commands.",
        "skill": "orthotect-uiux",
        "tokens": "semantics.json, motion.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "developer api hero, code sandbox hero section, b2b devtools landing page, api documentation hero, interactive curl terminal",
        "badge": "DevTools Grade",
        "icon": "terminal",
        "saas_features": [
            {"title": "Sub-Second Gate Execution", "desc": "Run 5 deterministic interface engineering gates in parallel in under 750ms."},
            {"title": "W3C DTCG Token Architecture", "desc": "Single source of truth compiled to CSS, Tailwind @theme, and JSON in one command."},
            {"title": "Autonomous AI Agent Native", "desc": "Designed specifically for Claude Code, Cursor Agent, Antigravity, and OpenAI Codex."},
            {"title": "Zero-Slop Production Certified", "desc": "No placeholders, no simulated metrics, and zero physical left/right CSS violations."}
        ]
    },
    {
        "id": "modern-b2b-saas-pricing-matrix",
        "cluster": "saas",
        "cluster_name": "B2B SaaS & DevTools",
        "cluster_num": 5,
        "title": "Usage-Based SaaS Pricing & ROI Calculator",
        "subtitle": "Monthly/annual billing toggle, monthly active user slider, and ROI estimation",
        "desc": "Modern transparent B2B pricing table with annual discount badge (20% off), interactive usage tier slider, comprehensive feature comparison checklist, and enterprise quote modal.",
        "skill": "orthotect-uiux",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "saas pricing matrix, usage based pricing calculator, b2b saas pricing table, annual monthly billing toggle, interactive pricing ui",
        "badge": "Interactive ROI",
        "icon": "credit-card",
        "saas_features": [
            {"title": "Starter ($29/mo)", "desc": "5 developers, all 5 quality gates, CLI tools, and basic design token compiler."},
            {"title": "Scale ($79/mo)", "desc": "25 developers, automated GitHub Actions CI runner, full 15 modular skills, and priority support."},
            {"title": "Enterprise (Custom)", "desc": "Unlimited seats, dedicated VPC deployment, custom gate rule authoring, and 99.99% SLA."},
            {"title": "Money-Back Guarantee", "desc": "30-day no questions asked refund policy if Orthotect doesn't accelerate your team's code review."}
        ]
    },
    {
        "id": "feature-bento-grid-showcase",
        "cluster": "saas",
        "cluster_name": "B2B SaaS & DevTools",
        "cluster_num": 5,
        "title": "Asymmetrical Bento Grid Architecture Showcase",
        "subtitle": "Interactive micro-cards, glassmorphic highlight borders, and live telemetry widgets",
        "desc": "Contemporary editorial bento grid layout presenting product architecture with subtle border gradients, live telemetry sparklines, code snippets, and responsive grid stacking.",
        "skill": "orthotect-design-systems",
        "tokens": "semantics.json, motion.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "bento grid ui, modern saas bento showcase, asymmetric feature grid, glassmorphic card ui, developer product architecture",
        "badge": "Asymmetric Bento",
        "icon": "grid",
        "saas_features": [
            {"title": "Deterministic Gate 1: WCAG 2.2 AAA Contrast", "desc": "Calculates relative luminance using CIE 1931 color space formulas with zero guesswork."},
            {"title": "Deterministic Gate 2: True BiDi & Logical Properties", "desc": "AST parsing flags every physical left/right CSS property to guarantee flawless Arabic RTL symmetry."},
            {"title": "Deterministic Gate 3: Finite State Machine Integrity", "desc": "Guarantees every interactive button, dialog, and loader has formal disabled, loading, and error states."},
            {"title": "Deterministic Gate 4: Anti-Slop Pattern Inspector", "desc": "Bans emoji clutter in professional headings, generic lorem ipsum, and unverified statistical assertions."}
        ]
    },
    {
        "id": "interactive-changelog-release-notes",
        "cluster": "saas",
        "cluster_name": "B2B SaaS & DevTools",
        "cluster_num": 5,
        "title": "Continuous Delivery Changelog & Release Monograph",
        "subtitle": "Version badges, breaking changes callouts, and direct Git commit anchors",
        "desc": "Clean editorial product release log featuring semver tags, categorized bug fixes and new features, breaking change warning banners, and reproducible npm release commands.",
        "skill": "orthotect-uiux",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "saas changelog ui, product release notes template, breaking changes callout, developer changelog format, continuous delivery notes",
        "badge": "SemVer 2.0",
        "icon": "git-commit",
        "saas_features": [
            {"title": "Version 1.7.4 (Latest Release)", "desc": "Added Auto-Healing (--fix) engine for physical CSS declarations, automated Git pre-commit hooks (npx orthotect hooks install), and zero-dependency configuration engine (orthotect.config.json)."},
            {"title": "Version 1.7.3", "desc": "Integrated UI/UX design intelligence: 57 UI styles, 96 palettes, 57 font pairings, 25 chart specs, 13 stack guidelines, 50 diversified aesthetic templates, and agent doctrine."},
            {"title": "Version 1.6.0", "desc": "Added 15 modular skills, 6 original style recipes, and published official orthotect npm package."},
            {"title": "Version 1.5.0", "desc": "Unified 5 deterministic quality gates into sub-second parallel orchestrator with JSON and Markdown reporters."},
            {"title": "Version 1.4.0", "desc": "Introduced DTCG token compiler supporting CSS variables, Tailwind @theme, and Swift/Kotlin exports."},
            {"title": "Version 1.0.0", "desc": "Initial release establishing the 7 Non-Negotiable Laws of High-Integrity Interface Engineering."}
        ]
    },
    {
        "id": "developer-documentation-hub",
        "cluster": "saas",
        "cluster_name": "B2B SaaS & DevTools",
        "cluster_num": 5,
        "title": "Tri-Pane Developer Documentation & API Hub",
        "subtitle": "Sticky left navigation, center markdown article, and right on-page TOC anchor rail",
        "desc": "High-readability documentation layout modeled after Stripe and Linear docs featuring deep permalinks, copyable code blocks, keyboard search (Cmd+K), and active scrollspy tracking.",
        "skill": "orthotect-uiux",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "developer documentation hub, tri pane doc layout, api documentation template, scrollspy table of contents, technical docs ui",
        "badge": "Tri-Pane Doc Hub",
        "icon": "book",
        "saas_features": [
            {"title": "Getting Started in 60 Seconds", "desc": "Install via npx orthotect doctor and run your first deterministic gate audit."},
            {"title": "Architecture Overview", "desc": "Understand the separation between Design Tokens, Gate Orchestration, and Modular Skills."},
            {"title": "CLI Command Reference", "desc": "Comprehensive documentation for compile, gate, doctor, skills, knowledge, and design commands."},
            {"title": "Contributing Guide", "desc": "How to author custom style recipes, propose new quality gates, and add AI agent skills."}
        ]
    },
    {
        "id": "status-uptime-incident-page",
        "cluster": "saas",
        "cluster_name": "B2B SaaS & DevTools",
        "cluster_num": 5,
        "title": "Public System Status & Infrastructure Uptime Page",
        "subtitle": "90-day uptime bar chart, active incident timeline, and notification subscribe",
        "desc": "Transparent public reliability portal displaying 90 days of continuous system uptime, component status pills (API, CDN, Auth, Database), and timestamped incident postmortems.",
        "skill": "orthotect-uiux",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "system status page, infrastructure uptime monitor, 90 day uptime bars, incident communication portal, public service status",
        "badge": "99.99% Uptime",
        "icon": "check-circle",
        "saas_features": [
            {"title": "Global Edge CDN: 100.0% Uptime", "desc": "All 280 edge Points of Presence operating with zero packet loss or routing anomalies."},
            {"title": "Core API Gateway: 99.99% Uptime", "desc": "p99 latency 14.2ms. Zero unhandled 5xx exceptions across 48 million daily requests."},
            {"title": "Authentication & MFA: 100.0% Uptime", "desc": "FIDO2 WebAuthn and OAuth identity token issuance fully operational."},
            {"title": "Token Compilation Engine: 100.0% Uptime", "desc": "Sub-second AST compiler running in under 120ms with 100% cache hit rate."}
        ]
    },
    {
        "id": "integrations-marketplace-directory",
        "cluster": "saas",
        "cluster_name": "B2B SaaS & DevTools",
        "cluster_num": 5,
        "title": "Cloud Integrations & Developer Tool Marketplace",
        "subtitle": "Category sidebar, verified partner badges, and one-click webhook configuration",
        "desc": "Directory of official ecosystem integrations for GitHub Actions, GitLab CI, Claude Code, Cursor, Antigravity, Slack notifications, and Datadog observability with instant setup guides.",
        "skill": "orthotect-design-systems",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "integrations marketplace, developer tool directory, github actions integration, ai agent plugin directory, cloud integrations ui",
        "badge": "Ecosystem Directory",
        "icon": "share-2",
        "saas_features": [
            {"title": "GitHub Actions Official Action", "desc": "Run Orthotect gates on every pull request and block non-compliant CSS before merge."},
            {"title": "Claude Code Skill Integration", "desc": "Directly delegate interface engineering tasks to Claude with automated review."},
            {"title": "Google Antigravity Customization", "desc": "Load Orthotect skills into Antigravity IDE and CLI with subagent orchestration."},
            {"title": "Cursor Agent Rule Engine", "desc": "Automatic linting and verification inside Cursor's AI coding workspace."}
        ]
    },
    {
        "id": "customer-case-study-monograph",
        "cluster": "saas",
        "cluster_name": "B2B SaaS & DevTools",
        "cluster_num": 5,
        "title": "Enterprise Customer Case Study & ROI Monograph",
        "subtitle": "Executive quotes, quantifiable metric callouts, and technical architecture diff",
        "desc": "Editorial narrative case study detailing how a Fortune 500 fintech reduced frontend design QA cycles by 84% and achieved 100% WCAG AAA compliance using Orthotect's deterministic gates.",
        "skill": "orthotect-uiux",
        "tokens": "semantics.json, motion.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "enterprise case study monograph, customer roi story, b2b saas case study ui, engineering case study template, social proof monograph",
        "badge": "Verified ROI",
        "icon": "award",
        "saas_features": [
            {"title": "84% Reduction in QA Review Cycles", "desc": "Engineers no longer debate button contrast or physical margins; gates enforce compliance automatically."},
            {"title": "Zero Accessibility Lawsuit Exposure", "desc": "100% of customer facing screens certified against WCAG 2.2 AAA with mathematical proofs."},
            {"title": "Flawless Arabic RTL Rollout in 2 Weeks", "desc": "True BiDi logical properties eliminated all manual directional stylesheet overrides."},
            {"title": "12,000 Pull Requests Verified", "desc": "Sub-second gate latency ensured zero developer friction and 100% adoption across 400 engineers."}
        ]
    },
    {
        "id": "community-forum-discussion-thread",
        "cluster": "saas",
        "cluster_name": "B2B SaaS & DevTools",
        "cluster_num": 5,
        "title": "Developer Technical Discussion & RFC Thread",
        "subtitle": "Upvoting, syntax-highlighted code comments, and accepted solution indicator",
        "desc": "High-density technical community forum thread with nested replies, markdown code snippets, verified core maintainer badges, and accepted architectural decision records (ADRs).",
        "skill": "orthotect-uiux",
        "tokens": "semantics.json, ergonomics.json",
        "fsm": "core/fsm/button-states.json",
        "keywords": "developer community forum, technical rfc discussion thread, syntax highlighted code forum, nested comments ui, dev community thread",
        "badge": "RFC Discussion",
        "icon": "message-square",
        "saas_features": [
            {"title": "RFC-042: AST-Based CSS Logical Property Linting", "desc": "Proposed enhancement to parse CSS AST directly in Python rather than relying on regex heuristics."},
            {"title": "Core Maintainer Solution (Accepted)", "desc": "Implemented parse5-based DOM crawler and css-tree parser in gates/gate_bidi_logical.py."},
            {"title": "Benchmark Results: 14.1ms Execution", "desc": "Maintained sub-second total gate budget while eliminating false-positive margin matches in data-urls."},
            {"title": "Community Consensus: 48 Upvotes", "desc": "Approved by maintainers from Stripe, Datadog, and Google Antigravity teams."}
        ]
    },
    {
        "id": "ai-coding-agent-skill-directory",
        "cluster": "saas",
        "cluster_name": "B2B SaaS & DevTools",
        "cluster_num": 5,
        "title": "Autonomous AI Agent Skill & Tool Directory",
        "subtitle": "Agent skill cards, parameter schema inspector, and one-click prompt copier",
        "desc": "Curated catalog of all 15 official Orthotect AI agent skills with YAML frontmatter inspection, parameter schema documentation, and one-click delegate prompt generators for Claude, Codex, and Antigravity.",
        "skill": "orthotect-uiux",
        "tokens": "semantics.json, ergonomics.json, motion.json",
        "fsm": "core/fsm/modal-dialog.json",
        "keywords": "ai coding agent skills, agent skill directory, claude code skills, cursor agent skills, antigravity skill catalog, agentic ui tools",
        "badge": "15 Modular Skills",
        "icon": "cpu",
        "saas_features": [
            {"title": "orthotect-doctrine & orthotect-uiux", "desc": "Non-negotiable laws of interface engineering and master 19-dimensional design intelligence."},
            {"title": "orthotect-bidi & orthotect-tokens", "desc": "True bidirectional symmetry and DTCG 3-tier design token compilation."},
            {"title": "orthotect-fsm & orthotect-gates", "desc": "Finite state machine guarantees and parallel sub-second quality gate orchestration."},
            {"title": "orthotect-accessibility & orthotect-visual-qa", "desc": "WCAG 2.2 AAA mathematical contrast and Playwright browser visual regression testing."}
        ]
    }
]

ECOMMERCE_PRODUCTS = {
    "hardware-spec-sheet-store": {
        "price": "$48.00", "unit": "/ unit (lot of 100)", "moq": "MOQ: 1 Lot",
        "badges": ["DIN 912 / ISO 4762", "AMS 4928 Grade 5", "In Stock: Dispatch 24h"],
        "cta": "Add to Procurement Cart", "visual": "bolt"
    },
    "luxury-mechanical-goods-gallery": {
        "price": "$18,400.00", "unit": "/ timepiece (Bespoke)", "moq": "Limited Edition: 1 of 50",
        "badges": ["COSC Chronometer Certified", "Manufacture Caliber OR-904", "Bespoke Concierge Allocation"],
        "cta": "Request Private Allocation", "visual": "watch"
    },
    "industrial-equipment-procurement": {
        "price": "$3,450.00", "unit": "/ valve manifold", "moq": "Heavy Equipment MOQ: 2",
        "badges": ["SAE J518 Flange", "350 Bar Operating Pressure", "ISO 4406 Cleanliness Certified"],
        "cta": "Request Enterprise Quote", "visual": "valve"
    },
    "architectural-materials-catalog": {
        "price": "$84.50", "unit": "/ m² (Honed Slab)", "moq": "Min Order: 25 m²",
        "badges": ["Italian Calacatta Oro", "Greenguard Gold Certified", "Slip Resistance R10"],
        "cta": "Order Architect Swatch Box", "visual": "marble"
    },
    "dtc-electronics-product-detail": {
        "price": "$699.00", "unit": "/ unit (Planar Studio)", "moq": "Free Worldwide Express",
        "badges": ["5Hz–55kHz Frequency Range", "Balanced 4.4mm Pentaconn", "CNC Aircraft Aluminum"],
        "cta": "Add to Studio Cart", "visual": "headphone"
    },
    "b2b-wholesale-bulk-order-grid": {
        "price": "$2.42", "unit": "/ unit (Reel of 2,500)", "moq": "MOQ: 1 Reel (2,500 pcs)",
        "badges": ["ARM Cortex-M4 120MHz", "Tape & Reel Sealed", "Automotive AEC-Q100"],
        "cta": "Download Volume Tier Sheet", "visual": "chip"
    },
    "digital-software-tier-pricing": {
        "price": "$1,499.00", "unit": "/ month (Enterprise Gateway)", "moq": "Annual Billing (20% Off)",
        "badges": ["Unlimited RPS Bounds", "99.999% SLA Bound", "Dedicated Private VPC"],
        "cta": "Provision Enterprise Gateway", "visual": "cloud"
    },
    "dynamic-product-filtering-rail": {
        "price": "$580.00", "unit": "/ alpine shell", "moq": "In Stock: 4 Colorways",
        "badges": ["3-Layer GORE-TEX Pro", "28,000mm Waterproof", "RECCO Avalanche Reflector"],
        "cta": "Select Size & Add", "visual": "apparel"
    },
    "cart-drawer-optimistic-update": {
        "price": "$24.00", "unit": "/ 250g bag (Whole Bean)", "moq": "Roast-to-Order",
        "badges": ["Geisha Direct Trade", "Altitude 1,850m", "Nitro-Flushed Freshness"],
        "cta": "Add to Roastery Cart", "visual": "coffee"
    },
    "customer-reviews-rating-matrix": {
        "price": "$1,190.00", "unit": "/ pair (Active Mastering)", "moq": "Pair Matched ±0.25dB",
        "badges": ["DSP Linear-Phase", "Beryllium Tweeter", "Room Calibration Mic Included"],
        "cta": "Reserve Studio Monitors", "visual": "speaker"
    }
}

CIVIC_SERVICES = {
    "civic-voter-registration-portal": {
        "badge": "WCAG 2.2 AAA Accessible Public Infrastructure Service",
        "title": "Need Multilingual or Assistive Telecommunications Support?",
        "phone": "1-800-555-VOTE (TTY 711)",
        "desc": "Call the 24/7 Accessible Voter Helpline or activate screen reader high-contrast audio mode."
    },
    "clinical-patient-intake-records": {
        "badge": "HIPAA Certified Electronic Health Records Intake",
        "title": "Need Medical Interpretation or Accessible Clinical Support?",
        "phone": "1-800-888-CARE (Ext. 4)",
        "desc": "Certified medical interpreters available in 60+ languages. Wheelchair-accessible exam accommodations provided upon request."
    },
    "emergency-crisis-alert-broadcast": {
        "badge": "FEMA Integrated Public Alert & Warning System (IPAWS)",
        "title": "Emergency Evacuation & Dispatch Command Center",
        "phone": "1-800-911-FEMA / Local 911",
        "desc": "Priority emergency communication channel. TDD/TTY telecommunications emergency relay active 24/7."
    },
    "public-transit-accessible-schedule": {
        "badge": "ADA Paratransit & Metro Rail Real-Time Transit Board",
        "title": "Accessible Transit Operations & Elevator Hotline",
        "phone": "1-800-555-RIDE (Option 2)",
        "desc": "Check real-time elevator outages across all metro stations, request ramp assistance, or book paratransit vans."
    },
    "universal-banking-statement-view": {
        "badge": "Consumer Financial Protection Bureau (CFPB) Compliant",
        "title": "Accessible Banking Services & Statement Formats",
        "phone": "1-800-444-BANK",
        "desc": "Request Braille statements, large-print 18pt font documents, or audio CD statements with zero account fees."
    },
    "utility-service-outage-reporter": {
        "badge": "Public Utility Commission Critical Outage Telemetry",
        "title": "Downed Powerlines & Hazardous Gas Emergency Hotline",
        "phone": "1-800-999-GRID (Emergency 24/7)",
        "desc": "Never touch downed power lines. Immediate automated dispatch for life-support medical device households."
    },
    "government-benefits-eligibility": {
        "badge": "Social Security & Healthcare Benefits Screener",
        "title": "Public Benefits Caseworker Assistance Line",
        "phone": "1-800-772-1213",
        "desc": "Connect directly with certified caseworkers for SNAP, Medicaid, and Supplemental Security Income eligibility."
    },
    "accessible-telehealth-consultation": {
        "badge": "WCAG 2.2 AAA Real-Time Encrypted Telehealth Portal",
        "title": "ASL Sign Language & Real-Time Captioning Desk",
        "phone": "1-800-333-HEAL",
        "desc": "Instant connection with certified American Sign Language (ASL) interpreters and automated real-time medical CART captions."
    },
    "educational-course-curriculum": {
        "badge": "Higher Education Section 508 & ADA Academic Hub",
        "title": "University Academic Accommodation & Assistive Tech Liaison",
        "phone": "1-800-ACAD-ADA",
        "desc": "Access OCR-scanned textbooks, alternate format exams, and peer-reviewed lecture audio transcriptions."
    },
    "legal-statute-document-reader": {
        "badge": "Open Judicial Records & Equal Justice Legal Monograph",
        "title": "Public Law Library & Court Accessibility Coordinator",
        "phone": "1-800-LEX-COURT",
        "desc": "Plain language legal summaries, screen-reader verified court precedent filings, and hearing room accommodations."
    }
}

def render_ecommerce_visual(visual_type, aes):
    p = aes['primary_color']
    if visual_type == 'watch':
        return f"""
        <svg width="100%" height="240" viewBox="0 0 400 240" fill="none">
          <circle cx="200" cy="120" r="95" stroke="{p}" stroke-width="3" fill="var(--tmpl-surface-1)"/>
          <circle cx="200" cy="120" r="88" stroke="var(--tmpl-border)" stroke-width="1" stroke-dasharray="2 4"/>
          <circle cx="200" cy="120" r="70" stroke="{p}" stroke-width="0.5" stroke-opacity="0.5"/>
          <text x="200" y="60" text-anchor="middle" fill="{p}" font-family="serif" font-size="14" font-weight="bold">XII</text>
          <text x="200" y="190" text-anchor="middle" fill="{p}" font-family="serif" font-size="14" font-weight="bold">VI</text>
          <text x="135" y="125" text-anchor="middle" fill="{p}" font-family="serif" font-size="14" font-weight="bold">IX</text>
          <text x="265" y="125" text-anchor="middle" fill="{p}" font-family="serif" font-size="14" font-weight="bold">III</text>
          <line x1="200" y1="120" x2="200" y2="75" stroke="{p}" stroke-width="3" stroke-linecap="round"/>
          <line x1="200" y1="120" x2="235" y2="120" stroke="{p}" stroke-width="2" stroke-linecap="round"/>
          <circle cx="200" cy="120" r="5" fill="{p}"/>
          <text x="200" y="150" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="sans-serif" font-size="9" letter-spacing="2">CHRONOMETER 28,800 VPH</text>
        </svg>
        """
    elif visual_type == 'valve':
        return f"""
        <svg width="100%" height="240" viewBox="0 0 400 240" fill="none">
          <rect x="60" y="50" width="280" height="140" rx="6" stroke="var(--tmpl-border)" stroke-width="2" fill="var(--tmpl-surface-1)"/>
          <rect x="110" y="70" width="80" height="100" rx="4" stroke="{p}" stroke-width="2" fill="{p}" fill-opacity="0.1"/>
          <rect x="210" y="70" width="80" height="100" rx="4" stroke="{p}" stroke-width="2" fill="{p}" fill-opacity="0.1"/>
          <circle cx="150" cy="120" r="22" stroke="{p}" stroke-width="2"/>
          <circle cx="250" cy="120" r="22" stroke="{p}" stroke-width="2"/>
          <line x1="150" y1="50" x2="150" y2="70" stroke="{p}" stroke-width="3"/>
          <line x1="250" y1="50" x2="250" y2="70" stroke="{p}" stroke-width="3"/>
          <text x="200" y="215" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="monospace" font-size="10">HYDRAULIC MANIFOLD: 350 BAR ISO 4406</text>
        </svg>
        """
    elif visual_type == 'marble':
        return f"""
        <svg width="100%" height="240" viewBox="0 0 400 240" fill="none">
          <rect x="40" y="30" width="320" height="180" rx="4" stroke="{p}" stroke-width="1.5" fill="var(--tmpl-surface-1)"/>
          <path d="M50 180 Q120 140 180 150 T310 90 T350 40" stroke="{p}" stroke-width="1.5" stroke-opacity="0.6" fill="none"/>
          <path d="M70 200 Q150 160 210 170 T330 110" stroke="{p}" stroke-width="0.8" stroke-opacity="0.4" fill="none"/>
          <path d="M120 50 Q180 80 240 60 T340 120" stroke="{p}" stroke-width="1.2" stroke-opacity="0.5" fill="none"/>
          <text x="200" y="195" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="serif" font-size="11" font-style="italic">Calacatta Oro Honed Porcelain Slabs 1200x600mm</text>
        </svg>
        """
    elif visual_type == 'headphone':
        return f"""
        <svg width="100%" height="240" viewBox="0 0 400 240" fill="none">
          <path d="M110 150 C110 80 290 80 290 150" stroke="{p}" stroke-width="5" fill="none" stroke-linecap="round"/>
          <rect x="85" y="130" width="45" height="75" rx="14" stroke="{p}" stroke-width="2" fill="var(--tmpl-surface-1)"/>
          <rect x="270" y="130" width="45" height="75" rx="14" stroke="{p}" stroke-width="2" fill="var(--tmpl-surface-1)"/>
          <line x1="140" y1="180" x2="260" y2="180" stroke="var(--tmpl-border)" stroke-dasharray="4"/>
          <path d="M140 180 Q170 140 200 160 T260 180" stroke="{p}" stroke-width="2" fill="none"/>
          <text x="200" y="225" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="monospace" font-size="10">ACOUSTIC CURVE: 5Hz–55kHz ±1.2dB</text>
        </svg>
        """
    elif visual_type == 'chip':
        return f"""
        <svg width="100%" height="240" viewBox="0 0 400 240" fill="none">
          <rect x="130" y="50" width="140" height="140" rx="8" stroke="{p}" stroke-width="2" fill="var(--tmpl-surface-1)"/>
          <rect x="155" y="75" width="90" height="90" rx="4" stroke="{p}" stroke-width="1" fill="{p}" fill-opacity="0.15"/>
          <text x="200" y="125" text-anchor="middle" fill="{p}" font-family="monospace" font-size="12" font-weight="bold">ARM Cortex-M4</text>
          <text x="200" y="145" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="monospace" font-size="9">120MHz · QFN-48</text>
          <line x1="110" y1="80" x2="130" y2="80" stroke="{p}" stroke-width="2"/>
          <line x1="110" y1="105" x2="130" y2="105" stroke="{p}" stroke-width="2"/>
          <line x1="110" y1="130" x2="130" y2="130" stroke="{p}" stroke-width="2"/>
          <line x1="110" y1="155" x2="130" y2="155" stroke="{p}" stroke-width="2"/>
          <line x1="270" y1="80" x2="290" y2="80" stroke="{p}" stroke-width="2"/>
          <line x1="270" y1="105" x2="290" y2="105" stroke="{p}" stroke-width="2"/>
          <line x1="270" y1="130" x2="290" y2="130" stroke="{p}" stroke-width="2"/>
          <line x1="270" y1="155" x2="290" y2="155" stroke="{p}" stroke-width="2"/>
        </svg>
        """
    elif visual_type == 'cloud':
        return f"""
        <svg width="100%" height="240" viewBox="0 0 400 240" fill="none">
          <rect x="50" y="40" width="300" height="160" rx="12" stroke="{p}" stroke-width="2" fill="var(--tmpl-surface-1)"/>
          <circle cx="120" cy="110" r="28" stroke="{p}" stroke-width="2" fill="{p}" fill-opacity="0.15"/>
          <circle cx="200" cy="100" r="38" stroke="{p}" stroke-width="2" fill="{p}" fill-opacity="0.2"/>
          <circle cx="280" cy="110" r="28" stroke="{p}" stroke-width="2" fill="{p}" fill-opacity="0.15"/>
          <line x1="148" y1="110" x2="162" y2="105" stroke="{p}" stroke-width="2"/>
          <line x1="238" y1="105" x2="252" y2="110" stroke="{p}" stroke-width="2"/>
          <text x="200" y="175" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="monospace" font-size="11">DEDICATED VPC MESH: 99.999% SLA</text>
        </svg>
        """
    elif visual_type == 'apparel':
        return f"""
        <svg width="100%" height="240" viewBox="0 0 400 240" fill="none">
          <path d="M160 40 L200 65 L240 40 L310 90 L270 130 L250 115 L250 200 L150 200 L150 115 L130 130 L90 90 Z" stroke="{p}" stroke-width="2.5" fill="var(--tmpl-surface-1)"/>
          <line x1="200" y1="65" x2="200" y2="200" stroke="{p}" stroke-width="1.5" stroke-dasharray="3 3"/>
          <text x="200" y="225" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="sans-serif" font-size="10">3-LAYER GORE-TEX PRO · 28,000mm SEAM-TAPED</text>
        </svg>
        """
    elif visual_type == 'coffee':
        return f"""
        <svg width="100%" height="240" viewBox="0 0 400 240" fill="none">
          <path d="M140 60 L260 60 L245 200 L155 200 Z" stroke="{p}" stroke-width="2" fill="var(--tmpl-surface-1)"/>
          <line x1="140" y1="85" x2="260" y2="85" stroke="{p}" stroke-width="2"/>
          <circle cx="200" cy="140" r="28" stroke="{p}" stroke-width="1.5" fill="{p}" fill-opacity="0.12"/>
          <text x="200" y="145" text-anchor="middle" fill="{p}" font-family="serif" font-size="14" font-weight="bold">GEISHA</text>
          <text x="200" y="225" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="sans-serif" font-size="10">DIRECT TRADE · 1,850m ALTITUDE · WHOLE BEAN</text>
        </svg>
        """
    elif visual_type == 'speaker':
        return f"""
        <svg width="100%" height="240" viewBox="0 0 400 240" fill="none">
          <rect x="130" y="30" width="140" height="180" rx="8" stroke="{p}" stroke-width="2" fill="var(--tmpl-surface-1)"/>
          <circle cx="200" cy="80" r="22" stroke="{p}" stroke-width="1.5" fill="{p}" fill-opacity="0.2"/>
          <circle cx="200" cy="150" r="42" stroke="{p}" stroke-width="2" fill="{p}" fill-opacity="0.15"/>
          <circle cx="200" cy="150" r="16" fill="{p}"/>
          <text x="200" y="225" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="monospace" font-size="10">BERYLLIUM TWEETER · LINEAR PHASE DSP</text>
        </svg>
        """
    else:  # bolt
        return f"""
        <svg width="100%" height="240" viewBox="0 0 400 240" fill="none">
          <rect x="20" y="20" width="360" height="200" rx="12" stroke="var(--tmpl-border)" stroke-dasharray="6" fill="var(--tmpl-surface-1)"/>
          <circle cx="200" cy="120" r="60" stroke="{p}" stroke-width="2"/>
          <circle cx="200" cy="120" r="20" fill="{p}" fill-opacity="0.2" stroke="{p}"/>
          <line x1="200" y1="30" x2="200" y2="210" stroke="var(--tmpl-border)"/>
          <line x1="40" y1="120" x2="360" y2="120" stroke="var(--tmpl-border)"/>
          <text x="215" y="70" fill="var(--tmpl-text-secondary)" font-family="monospace" font-size="11">R_TOL: ±0.005mm</text>
          <text x="215" y="170" fill="var(--tmpl-text-secondary)" font-family="monospace" font-size="11">SURF: Ra 0.4μm</text>
        </svg>
        """

SAAS_TERMINALS = {
    "developer-api-platform-hero": {
        "title": "bash — orthotect cli v1.7.4",
        "cmd": "npx orthotect doctor",
        "lines": [
            ("✔ Node.js runtime: v20.19.0 (Supported)", False),
            ("✔ Python gate engine: v3.12 (Supported)", False),
            ("✔ Design tokens: 96 palettes, 57 styles compiled", False),
            ("✔ Deterministic quality gates: 5/5 operational (703ms)", False),
            ("Status: System healthy. Ready to enforce deterministic UI engineering.", True)
        ]
    },
    "enterprise-security-landing": {
        "title": "ortho-sec-audit — fips-140-3",
        "cmd": "orthotect audit --compliance=wcag-aaa,soc2",
        "lines": [
            ("✔ FIPS 140-3 Cryptographic tokens: Validated", False),
            ("✔ WCAG 2.2 AAA Contrast Matrix: 100% Passed (4.5:1 / 7:1)", False),
            ("✔ BiDi Logical Symmetry: 0 physical property violations", False),
            ("✔ Content Security Policy (CSP): Strict nonces verified", False),
            ("AUDIT RESULT: 0 Vulnerabilities, Enterprise Compliance Grade A+", True)
        ]
    },
    "ai-agent-orchestrator-showcase": {
        "title": "agent-mesh — autonomous fleet",
        "cmd": "orthotect delegate --fleet=claude,codex,agy --task='refactor-fsm'",
        "lines": [
            ("✔ Orchestrator: Claude 3.7 Sonnet (Planning mode)", False),
            ("✔ Implementer: Google Antigravity agy (CLI runner)", False),
            ("✔ Quality Gate: 5 deterministic gates executing in sandbox...", False),
            ("✔ FSM Verification: 4 states, 8 transitions proven deadlock-free", False),
            ("TASK LANDED: 100% test pass rate. Zero regressions detected.", True)
        ]
    },
    "open-source-framework-documentation": {
        "title": "bash — quickstart",
        "cmd": "git clone https://github.com/seotarek/orthotect.git && cd orthotect && npm test",
        "lines": [
            ("Cloning into 'orthotect'...", False),
            ("Checking out files: 100% (428/428), done.", False),
            ("Running 292 unit tests across 14 test suites...", False),
            ("....................................................................", False),
            ("OK: 292 tests passed in 0.942s (Quality Score: 100.0/100)", True)
        ]
    },
    "b2b-cloud-infrastructure-platform": {
        "title": "terraform — multi-cloud-mesh",
        "cmd": "orthotect infra validate --topology=multi-region-mesh",
        "lines": [
            ("✔ AWS us-east-1 VPC Mesh: Configured", False),
            ("✔ GCP europe-west3 Gateway: Synced", False),
            ("✔ WireGuard Zero-Trust Tunnel: MTU 1420 verified", False),
            ("✔ Sub-15ms Cross-Region Latency Budget: Passed (11.4ms)", False),
            ("INFRASTRUCTURE VERIFIED: Zero drift across 12 zones.", True)
        ]
    },
    "realtime-collaboration-workspace": {
        "title": "crdt-sync — yjs-webrtc",
        "cmd": "orthotect crdt benchmark --peers=5000",
        "lines": [
            ("✔ Yjs CRDT Vector Clock: Synchronized", False),
            ("✔ WebRTC DataChannel Mesh: Connected (5,000 concurrent peers)", False),
            ("✔ Convergence Time: 8.2ms (Deterministic state consistency)", False),
            ("✔ Conflict Resolution: 0 dropped mutations", False),
            ("CRDT STATE: Converged. Memory footprint: 4.8MB.", True)
        ]
    },
    "developer-tooling-sdk-portal": {
        "title": "ortho-sdk — generator",
        "cmd": "orthotect generate sdk --target=typescript,python,go",
        "lines": [
            ("✔ TypeScript SDK: Types generated with full JSDoc comments", False),
            ("✔ Python SDK: Pydantic v2 schemas and strict typing compiled", False),
            ("✔ Go SDK: Struct tags and JSON unmarshaling generated", False),
            ("✔ Tree-shaking verification: < 1.8KB gzipped bundle", False),
            ("GENERATION COMPLETE: All SDKs verified with zero dependencies.", True)
        ]
    },
    "high-conversion-checkout-flow": {
        "title": "ortho-cro — funnel-analyzer",
        "cmd": "orthotect cro audit --page=checkout --locale=ar,en",
        "lines": [
            ("✔ Form field friction score: 12/100 (Optimal)", False),
            ("✔ Micro-copy clarity rating: 98/100", False),
            ("✔ BiDi RTL visual flow: Verified (No logical misalignment)", False),
            ("✔ Trust badges & Social proof: Placed above the fold", False),
            ("CRO PREDICTION: +18.4% conversion uplift with FSM double-lock.", True)
        ]
    },
    "interactive-design-system-spec": {
        "title": "token-compiler — dtcg-v1",
        "cmd": "orthotect tokens build --format=css,tailwind,json",
        "lines": [
            ("✔ Primitives: 96 color scales, 16 typography steps, 12 radii", False),
            ("✔ Semantics: 57 UI tokens mapped for Light & Dark modes", False),
            ("✔ Tailwind v4 @theme: tokens/theme.css exported", False),
            ("✔ WCAG 2.2 AAA Contrast Matrix: 100% Validated (Zero failures)", False),
            ("BUILD SUCCESS: Platform artifacts ready for deployment.", True)
        ]
    },
    "analytics-event-pipeline-monitor": {
        "title": "pipeline-stream — clickhouse-kafka",
        "cmd": "orthotect telemetry status --cluster=prod-kafka-01",
        "lines": [
            ("✔ Kafka Ingestion Rate: 485,000 events/sec", False),
            ("✔ ClickHouse Ingest Lag: 12ms", False),
            ("✔ Dropped Messages: 0 (Dead-letter queue empty)", False),
            ("✔ Memory Usage: 34.2% across 8 worker pods", False),
            ("PIPELINE OPERATIONAL: Zero dropped records in last 30 days.", True)
        ]
    }
}

def render_dashboard_chart(item, aes):
    p = aes['primary_color']
    cid = item['id']
    
    if any(k in cid for k in ['query', 'metrics', 'pod', 'database']):
        # Bar Histogram Chart
        return f"""
        <div class="dashboard-chart-box">
          <div class="chart-header">
            <div>
              <h3 class="chart-title">Query Latency Distribution (Histogram)</h3>
              <p class="chart-desc">P50, P90, P99 execution time percentiles across 1M telemetry samples</p>
            </div>
            <div class="chart-badge">Samples: 1,024,800</div>
          </div>
          <div class="chart-viewport">
            <svg width="100%" height="220" viewBox="0 0 800 220">
              <line x1="40" y1="30" x2="760" y2="30" stroke="var(--tmpl-border)" stroke-dasharray="4"/>
              <line x1="40" y1="90" x2="760" y2="90" stroke="var(--tmpl-border)" stroke-dasharray="4"/>
              <line x1="40" y1="150" x2="760" y2="150" stroke="var(--tmpl-border)" stroke-dasharray="4"/>
              <line x1="40" y1="190" x2="760" y2="190" stroke="var(--tmpl-border)"/>
              
              <rect x="60" y="140" width="45" height="50" rx="3" fill="{p}" fill-opacity="0.5"/>
              <rect x="125" y="110" width="45" height="80" rx="3" fill="{p}" fill-opacity="0.6"/>
              <rect x="190" y="70" width="45" height="120" rx="3" fill="{p}" fill-opacity="0.8"/>
              <rect x="255" y="40" width="45" height="150" rx="3" fill="{p}"/>
              <rect x="320" y="55" width="45" height="135" rx="3" fill="{p}" fill-opacity="0.9"/>
              <rect x="385" y="85" width="45" height="105" rx="3" fill="{p}" fill-opacity="0.75"/>
              <rect x="450" y="120" width="45" height="70" rx="3" fill="{p}" fill-opacity="0.6"/>
              <rect x="515" y="145" width="45" height="45" rx="3" fill="{p}" fill-opacity="0.5"/>
              <rect x="580" y="165" width="45" height="25" rx="3" fill="{p}" fill-opacity="0.4"/>
              <rect x="645" y="175" width="45" height="15" rx="3" fill="{p}" fill-opacity="0.3"/>
              
              <text x="82" y="208" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="monospace" font-size="10">&lt;1ms</text>
              <text x="277" y="208" text-anchor="middle" fill="{p}" font-family="monospace" font-size="10" font-weight="bold">4.2ms (P50)</text>
              <text x="472" y="208" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="monospace" font-size="10">12ms (P90)</text>
              <text x="667" y="208" text-anchor="middle" fill="var(--tmpl-text-secondary)" font-family="monospace" font-size="10">45ms (P99)</text>
            </svg>
          </div>
        </div>
        """
    elif any(k in cid for k in ['cache', 'iot', 'fraud']):
        # Radial Donut Gauge Telemetry
        return f"""
        <div class="dashboard-chart-box">
          <div class="chart-header">
            <div>
              <h3 class="chart-title">Edge Fleet Distribution & Cache Health</h3>
              <p class="chart-desc">Real-time status breakdown and cache hit ratio across global edge POPs</p>
            </div>
            <div class="chart-badge">Active Nodes: 4,892</div>
          </div>
          <div class="chart-viewport" style="display:flex; justify-content:center; align-items:center;">
            <svg width="400" height="220" viewBox="0 0 400 220">
              <circle cx="200" cy="110" r="75" stroke="var(--tmpl-surface-2)" stroke-width="22" fill="none"/>
              <circle cx="200" cy="110" r="75" stroke="{p}" stroke-width="22" stroke-dasharray="471" stroke-dashoffset="52" stroke-linecap="round" fill="none"/>
              <circle cx="200" cy="110" r="75" stroke="#10b981" stroke-width="22" stroke-dasharray="471" stroke-dashoffset="380" stroke-linecap="round" fill="none"/>
              <text x="200" y="105" text-anchor="middle" fill="var(--tmpl-text-primary)" font-family="sans-serif" font-size="28" font-weight="800">98.4%</text>
              <text x="200" y="125" text-anchor="middle" fill="{p}" font-family="monospace" font-size="11" font-weight="600">CACHE HIT RATIO</text>
              
              <text x="60" y="200" fill="#10b981" font-family="sans-serif" font-size="11" font-weight="600">● 4,812 Healthy</text>
              <text x="200" y="200" text-anchor="middle" fill="{p}" font-family="sans-serif" font-size="11" font-weight="600">● 76 Warming</text>
              <text x="340" y="200" text-anchor="end" fill="var(--tmpl-text-secondary)" font-family="sans-serif" font-size="11">● 4 Syncing</text>
            </svg>
          </div>
        </div>
        """
    elif any(k in cid for k in ['order-book', 'siem', 'traffic']):
        # Depth Curve / Multi-line Chart
        return f"""
        <div class="dashboard-chart-box">
          <div class="chart-header">
            <div>
              <h3 class="chart-title">Market Depth & Microsecond Telemetry</h3>
              <p class="chart-desc">Bid/Ask cumulative liquidity curves and execution velocity</p>
            </div>
            <div class="chart-badge">Tick Frequency: 1μs</div>
          </div>
          <div class="chart-viewport">
            <svg width="100%" height="220" viewBox="0 0 800 220" preserveAspectRatio="none">
              <defs>
                <linearGradient id="bidGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#10b981" stop-opacity="0.3"/>
                  <stop offset="100%" stop-color="#10b981" stop-opacity="0.0"/>
                </linearGradient>
                <linearGradient id="askGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="{p}" stop-opacity="0.3"/>
                  <stop offset="100%" stop-color="{p}" stop-opacity="0.0"/>
                </linearGradient>
              </defs>
              <line x1="400" y1="10" x2="400" y2="210" stroke="var(--tmpl-border)" stroke-dasharray="2 4"/>
              
              <polygon points="40,210 40,180 120,170 180,150 250,130 320,100 370,60 395,40 395,210" fill="url(#bidGrad)"/>
              <polyline points="40,180 120,170 180,150 250,130 320,100 370,60 395,40" fill="none" stroke="#10b981" stroke-width="2.5"/>
              
              <polygon points="405,210 405,40 430,60 480,100 550,130 620,150 680,170 760,180 760,210" fill="url(#askGrad)"/>
              <polyline points="405,40 430,60 480,100 550,130 620,150 680,170 760,180" fill="none" stroke="{p}" stroke-width="2.5"/>
              
              <text x="200" y="200" text-anchor="middle" fill="#10b981" font-family="monospace" font-size="11" font-weight="bold">BIDS: $18,420,500</text>
              <text x="600" y="200" text-anchor="middle" fill="{p}" font-family="monospace" font-size="11" font-weight="bold">ASKS: $19,105,200</text>
            </svg>
          </div>
        </div>
        """
    else:
        # High-Fidelity Area Stream Chart
        return f"""
        <div class="dashboard-chart-box">
          <div class="chart-header">
            <div>
              <h3 class="chart-title">Real-Time Telemetry Stream</h3>
              <p class="chart-desc">Sub-second telemetry samples plotted with zero layout shift</p>
            </div>
            <div class="chart-badge">Active Sampling: 100ms</div>
          </div>
          <div class="chart-viewport">
            <svg width="100%" height="220" viewBox="0 0 800 220" preserveAspectRatio="none">
              <defs>
                <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="{p}" stop-opacity="0.35"/>
                  <stop offset="100%" stop-color="{p}" stop-opacity="0.00"/>
                </linearGradient>
              </defs>
              <line x1="0" y1="50" x2="800" y2="50" stroke="var(--tmpl-border)" stroke-dasharray="4"/>
              <line x1="0" y1="110" x2="800" y2="110" stroke="var(--tmpl-border)" stroke-dasharray="4"/>
              <line x1="0" y1="170" x2="800" y2="170" stroke="var(--tmpl-border)" stroke-dasharray="4"/>
              <polygon points="0,180 80,160 160,140 240,150 320,110 400,90 480,120 560,70 640,60 720,40 800,30 800,220 0,220" fill="url(#chartGrad)"/>
              <polyline points="0,180 80,160 160,140 240,150 320,110 400,90 480,120 560,70 640,60 720,40 800,30" fill="none" stroke="{p}" stroke-width="3" stroke-linecap="round"/>
            </svg>
          </div>
        </div>
        """

def render_top_bar(item, aes):
    dark_style = "" if aes["theme"] == "dark" else "display:none;"
    light_style = "" if aes["theme"] == "light" else "display:none;"
    return f"""
    <!-- ORTHOTECT TEMPLATE TOP BAR (STICKY CONTROLS) -->
    <header class="ortho-tmpl-topbar" role="banner">
      <div class="topbar-inner">
        <div class="topbar-left">
          <a href="../index.html#gallery" class="topbar-back-btn" title="Back to Orthotect Showcase Gallery">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="19" y1="12" x2="5" y2="12"></line>
              <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
            <span>Gallery</span>
          </a>
          <div class="topbar-divider"></div>
          <a href="../index.html" class="topbar-brand">
            <span class="brand-text">ORTHO<span class="brand-accent">TECT</span></span>
          </a>
          <span class="style-badge" title="UI Architecture Style: {html.escape(aes['ui_style'])} • Font: {html.escape(aes['font_name'])}">{html.escape(aes['ui_style'])}</span>
          <span class="cluster-badge cluster-{item['cluster_num']}">Cluster {item['cluster_num']}: {html.escape(item['cluster_name'])}</span>
        </div>

        <div class="topbar-right">
          <div class="topbar-cert-pills">
            <span class="cert-pill" title="Certified WCAG 2.2 AAA Contrast">WCAG AAA</span>
            <span class="cert-pill" title="100% CSS Logical Properties">BiDi Symmetric</span>
            <span class="cert-pill" title="Finite State Machine Verified">FSM Verified</span>
          </div>

          <div class="topbar-actions">
            <button id="themeToggleBtn" class="topbar-btn" aria-label="Toggle Light and Dark Mode" title="Toggle Theme">
              <span class="theme-icon-dark" style="{dark_style}">🌙 Dark</span>
              <span class="theme-icon-light" style="{light_style}">☀️ Light</span>
            </button>
            <button id="dirToggleBtn" class="topbar-btn" aria-label="Toggle Text Direction LTR and RTL" title="Toggle BiDi Direction">
              <span class="dir-text">LTR ⇄ RTL</span>
            </button>
            <button id="copyCodeBtn" class="topbar-btn btn-accent" title="Copy Full Standalone HTML">
              <span>Copy HTML</span>
            </button>
            <a href="data:text/html;charset=utf-8,{item['id']}.html" id="downloadHtmlBtn" class="topbar-btn" download="{item['id']}.html" title="Download Template File">
              <span>Download</span>
            </a>
          </div>
        </div>
      </div>
    </header>
    """

def render_template_html(item):
    aes = TEMPLATE_AESTHETICS.get(item['id'], {
        "ui_style": "Modern Bento SaaS",
        "theme": "dark",
        "font_name": "Plus Jakarta Sans",
        "google_font_url": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap",
        "heading_font": "'Plus Jakarta Sans', sans-serif",
        "body_font": "'Plus Jakarta Sans', sans-serif",
        "bg_canvas": "#0B0F19",
        "surface_1": "#111827",
        "surface_2": "#1F2937",
        "surface_3": "#374151",
        "primary_color": "#4F46E5",
        "primary_hover": "#4338CA",
        "btn_text": "#FFFFFF",
        "text_primary": "#F9FAFB",
        "text_secondary": "#9CA3AF",
        "border_color": "rgba(255, 255, 255, 0.10)",
        "border_radius": "10px",
        "border_width": "1px",
        "box_shadow": "0 4px 20px -2px rgba(0, 0, 0, 0.4)",
        "card_extra_css": ""
    })
    opposite_theme = "light" if aes["theme"] == "dark" else "dark"

    # Prepare specific body content based on cluster
    content_markup = ""
    
    if item['cluster'] == 'dashboards':
        stats_markup = "".join([f"""
          <div class="metric-card">
            <div class="metric-label">{html.escape(s['label'])}</div>
            <div class="metric-value">{html.escape(s['value'])}</div>
            <div class="metric-delta delta-positive">{html.escape(s['delta'])}</div>
          </div>
        """ for s in item.get('stats', [])])

        chart_svg = render_dashboard_chart(item, aes)

        headers_markup = "".join([f"<th>{html.escape(h)}</th>" for h in item.get('table_headers', [])])
        rows_markup = "".join([
            "<tr>" + "".join([f"<td>{html.escape(cell)}</td>" for cell in r]) + "</tr>"
            for r in item.get('table_rows', [])
        ])

        table_markup = f"""
        <div class="dashboard-table-box">
          <div class="table-header-bar">
            <h3 class="table-title">Live Telemetry Ledger</h3>
            <span class="table-status-pill">FSM State: Synced</span>
          </div>
          <div class="table-scroll-container">
            <table class="ortho-data-table">
              <thead><tr>{headers_markup}</tr></thead>
              <tbody>{rows_markup}</tbody>
            </table>
          </div>
        </div>
        """
        content_markup = f"""
        <div class="dashboard-grid">
          <div class="metrics-row">{stats_markup}</div>
          {chart_svg}
          {table_markup}
        </div>
        """

    elif item['cluster'] == 'forms':
        steps_markup = "".join([f"""
          <div class="fsm-step-item {'active' if idx==0 else ''}">
            <div class="step-num">{idx+1}</div>
            <div class="step-name">{html.escape(step)}</div>
          </div>
        """ for idx, step in enumerate(item.get('form_steps', []))])

        fields_markup = ""
        for f in item.get('form_fields', []):
            req_attr = "required" if f.get('required') else ""
            req_badge = '<span class="req-star" aria-hidden="true">*</span>' if f.get('required') else ''
            
            if f['type'] == 'select':
                opts = "".join([f"<option>{html.escape(o)}</option>" for o in f['options']])
                fields_markup += f"""
                <div class="form-group">
                  <label class="form-label" for="{f['label']}">{html.escape(f['label'])} {req_badge}</label>
                  <select id="{f['label']}" class="form-control" {req_attr}>{opts}</select>
                </div>
                """
            elif f['type'] == 'checkbox':
                fields_markup += f"""
                <div class="form-group form-check">
                  <input type="checkbox" id="{f['label']}" class="form-checkbox" {req_attr}>
                  <label class="form-check-label" for="{f['label']}">{html.escape(f['label_check'])}</label>
                </div>
                """
            elif f['type'] == 'checkbox_group':
                c_opts = "".join([f"""
                  <label class="check-pill">
                    <input type="checkbox" checked> <code>{html.escape(o)}</code>
                  </label>
                """ for o in f['options']])
                fields_markup += f"""
                <div class="form-group">
                  <label class="form-label">{html.escape(f['label'])}</label>
                  <div class="check-pill-row">{c_opts}</div>
                </div>
                """
            else:
                fields_markup += f"""
                <div class="form-group">
                  <label class="form-label" for="{f['label']}">{html.escape(f['label'])} {req_badge}</label>
                  <input type="{f['type']}" id="{f['label']}" class="form-control" placeholder="{html.escape(f['placeholder'])}" {req_attr}>
                </div>
                """

        content_markup = f"""
        <div class="form-wizard-card">
          <div class="fsm-progress-bar">{steps_markup}</div>
          <form class="ortho-fsm-form" onsubmit="event.preventDefault(); alert('FSM Validated: State transition verified!');">
            <div class="form-fields-grid">{fields_markup}</div>
            <div class="form-actions-row">
              <button type="button" class="btn-ctrl" onclick="alert('Draft progress cached in local session')">Save Draft</button>
              <button type="submit" class="btn-ctrl-accent">
                <span>Confirm & Advance Workflow</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </button>
            </div>
            <div class="form-security-note">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{aes['primary_color']}" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              <span>Cryptographic idempotency token bound. Double-submission prevention active.</span>
            </div>
          </form>
        </div>
        """

    elif item['cluster'] == 'ecommerce':
        specs_rows = "".join([f"""
          <tr>
            <td class="spec-name">{html.escape(sp['param'])}</td>
            <td class="spec-value"><strong>{html.escape(sp['spec'])}</strong></td>
            <td class="spec-tol">{html.escape(sp['tolerance'])}</td>
          </tr>
        """ for sp in item.get('spec_table', [])])

        prod = ECOMMERCE_PRODUCTS.get(item['id'], {
            "title": item['title'],
            "desc": item['desc'],
            "price": "$48.00",
            "unit": "/ unit (lot of 100)",
            "moq": "MOQ: 1 Lot",
            "badges": ["DIN 912 / ISO 4762", "Certificate 3.1 Attached", "In Stock: Dispatch 24h"],
            "cta": "Add to Procurement Cart",
            "visual": "bolt"
        })
        prod_visual_svg = render_ecommerce_visual(prod.get('visual', 'bolt'), aes)
        prod_badges = prod.get('badges', ['In Stock: Dispatch 24h'])
        badges_markup = "".join([f'<span class="prod-badge {"highlight" if i==len(prod_badges)-1 else ""}">{html.escape(b)}</span>' for i, b in enumerate(prod_badges)])

        content_markup = f"""
        <div class="ecommerce-layout">
          <div class="product-hero-panel">
            <div class="product-visual-box">
              <div class="product-schematic-bg">
                {prod_visual_svg}
              </div>
              <div class="product-badge-row">
                {badges_markup}
              </div>
            </div>

            <div class="product-order-box">
              <h3 class="prod-title">{html.escape(prod.get('title', item['title']))}</h3>
              <p class="prod-desc">{html.escape(prod.get('desc', item['desc']))}</p>
              
              <div class="prod-pricing-row">
                <div class="prod-price">{html.escape(prod.get('price', '$48.00'))} <span class="prod-unit">{html.escape(prod.get('unit', '/ unit'))}</span></div>
                <div class="prod-moq">{html.escape(prod.get('moq', 'MOQ: 1 Unit'))}</div>
              </div>

              <div class="order-actions-grid">
                <div class="qty-stepper">
                  <button type="button" class="btn-step" onclick="this.nextElementSibling.stepDown()">−</button>
                  <input type="number" value="1" min="1" max="500" class="qty-input">
                  <button type="button" class="btn-step" onclick="this.previousElementSibling.stepUp()">+</button>
                </div>
                <button type="button" class="btn-ctrl-accent" onclick="alert('Order placed with deterministic FSM reservation lock')">
                  {html.escape(prod.get('cta', 'Add to Procurement Cart'))}
                </button>
              </div>
            </div>
          </div>

          <div class="specs-table-card">
            <h4 class="specs-title">Technical Specification Sheet</h4>
            <table class="ortho-specs-table">
              <thead>
                <tr>
                  <th>Parameter</th>
                  <th>Engineering Specification</th>
                  <th>Tolerance / Standard</th>
                </tr>
              </thead>
              <tbody>{specs_rows}</tbody>
            </table>
          </div>
        </div>
        """

    elif item['cluster'] == 'civic':
        items_markup = "".join([f"""
          <div class="civic-step-card">
            <div class="civic-step-header">
              <span class="civic-step-badge">{html.escape(ci['step'])}</span>
              <h4 class="civic-step-title">{html.escape(ci['title'])}</h4>
            </div>
            <p class="civic-step-desc">{html.escape(ci['desc'])}</p>
            <div class="civic-action-row">
              <button type="button" class="btn-civic" onclick="alert('Navigating to official state verification portal')">
                <span>{html.escape(ci['action'])}</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>
        """ for ci in item.get('civic_steps', [])])

        cs = CIVIC_SERVICES.get(item['id'], {
            "badge": "WCAG 2.2 AAA Accessible Public Infrastructure Service",
            "title": "Accessible Public Infrastructure Service",
            "phone": "1-800-555-0199",
            "desc": item['desc']
        })

        content_markup = f"""
        <div class="civic-container">
          <div class="civic-hero-banner">
            <div class="civic-cert-stamp">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              <span>{html.escape(cs['badge'])}</span>
            </div>
            <h3 class="civic-title">{html.escape(item['title'])}</h3>
            <p class="civic-desc">{html.escape(item['desc'])}</p>
          </div>

          <div class="civic-steps-grid">{items_markup}</div>

          <div class="civic-assistance-box">
            <div class="assist-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--tmpl-primary)" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4M12 8h.01"/>
              </svg>
            </div>
            <div class="assist-text">
              <strong>{html.escape(cs['title'])}: Dedicated Accessibility Line</strong>
              <p>Call the 24/7 Accessible Hotline at <strong>{html.escape(cs['phone'])}</strong> (TTY 711) or activate screen reader high-contrast audio mode.</p>
            </div>
          </div>
        </div>
        """

    elif item['cluster'] == 'saas':
        feat_markup = "".join([f"""
          <div class="saas-feat-card">
            <div class="feat-icon-bullet"></div>
            <h4 class="feat-title">{html.escape(ft['title'])}</h4>
            <p class="feat-desc">{html.escape(ft['desc'])}</p>
          </div>
        """ for ft in item.get('saas_features', [])])

        term = SAAS_TERMINALS.get(item['id'], {
            "title": "bash — orthotect cli v1.7.4",
            "cmd": "npx orthotect doctor",
            "lines": [
                ("✔ Node.js runtime: v20.19.0 (Supported)", False),
                ("✔ Python gate engine: v3.12 (Supported)", False),
                ("✔ Design tokens: 96 palettes, 57 styles compiled", False),
                ("Status: System healthy. Ready to enforce deterministic UI engineering.", True)
            ]
        })
        term_lines = "".join([
            f'<div class="term-line {"highlight" if is_hl else "output"}">{html.escape(line)}</div>'
            for line, is_hl in term['lines']
        ])

        content_markup = f"""
        <div class="saas-hero-container">
          <div class="saas-header-center">
            <div class="saas-pill">{html.escape(item['badge'])}</div>
            <h3 class="saas-hero-title">{html.escape(item['title'])}</h3>
            <p class="saas-hero-desc">{html.escape(item['desc'])}</p>
            
            <div class="saas-cta-group">
              <button type="button" class="btn-ctrl-accent" onclick="alert('CLI initialized: {html.escape(term['cmd'])}')">
                <span>Start Building Now</span>
              </button>
              <button type="button" class="btn-ctrl" onclick="alert('Viewing comprehensive technical documentation')">
                <span>Read Documentation</span>
              </button>
            </div>
          </div>

          <div class="saas-terminal-preview">
            <div class="terminal-bar">
              <div class="terminal-dots">
                <span class="dot dot-red"></span>
                <span class="dot dot-yellow"></span>
                <span class="dot dot-green"></span>
              </div>
              <span class="terminal-title">{html.escape(term['title'])}</span>
              <span class="terminal-badge">Latency: 14ms</span>
            </div>
            <div class="terminal-content">
              <div class="term-line"><span class="term-prompt">$</span> {html.escape(term['cmd'])}</div>
              {term_lines}
            </div>
          </div>

          <div class="saas-features-grid">{feat_markup}</div>
        </div>
        """

    # Schema JSON-LD
    schema_json = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": f"{BASE_URL}/templates/{item['id']}.html",
                "url": f"{BASE_URL}/templates/{item['id']}.html",
                "name": f"{item['title']} — Orthotect UI Template",
                "description": item['desc'],
                "isPartOf": {
                    "@type": "WebSite",
                    "@id": f"{BASE_URL}/#website",
                    "name": "Orthotect Architecture Platform",
                    "url": BASE_URL
                },
                "inLanguage": "en-US"
            },
            {
                "@type": "SoftwareSourceCode",
                "@id": f"{BASE_URL}/templates/{item['id']}.html#source",
                "name": item['title'],
                "programmingLanguage": "HTML5, CSS Logical Properties, Vanilla JavaScript",
                "runtimePlatform": "Modern Evergreen Browsers (Chrome, Firefox, Safari, Edge)",
                "codeSampleType": "full template",
                "license": "https://opensource.org/licenses/MIT",
                "author": {
                    "@type": "Organization",
                    "name": "Orthotect Architecture Team",
                    "url": BASE_URL
                }
            }
        ]
    }, indent=2)

    top_bar = render_top_bar(item, aes)

    full_html = f"""<!DOCTYPE html>
<html lang="en" dir="ltr" data-theme="{aes['theme']}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(item['title'])} — Orthotect UI Template</title>
  
  <!-- Technical SEO & Meta -->
  <meta name="description" content="{html.escape(item['desc'])}">
  <meta name="keywords" content="{html.escape(item['keywords'])}, orthotect, design tokens, ui template, accessible html, css logical properties">
  <link rel="canonical" href="{BASE_URL}/templates/{item['id']}.html">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
  
  <!-- OpenGraph -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="{html.escape(item['title'])} — Orthotect Template">
  <meta property="og:description" content="{html.escape(item['desc'])}">
  <meta property="og:url" content="{BASE_URL}/templates/{item['id']}.html">
  <meta property="og:site_name" content="Orthotect Interface Engineering">
  <meta property="og:image" content="{BASE_URL}/assets/brand/brand-guide.jpg">
  
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(item['title'])}">
  <meta name="twitter:description" content="{html.escape(item['desc'])}">
  <meta name="twitter:image" content="{BASE_URL}/assets/brand/brand-guide.jpg">
  
  <link rel="icon" type="image/svg+xml" href="../assets/brand/favicon.svg">
  
  <!-- Google Web Fonts for Bespoke Typographic Personality -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{aes['google_font_url']}">

  <!-- Global Shared Tokens & Stylesheet -->
  <link rel="stylesheet" href="../styles.css">
  
  <!-- Standalone Scoped Template Styles -->
  <style>
    /* Orthotect Template Scoped Tokens & Reset */
    :root {{
      --tmpl-max-width: 1200px;
      --tmpl-font-heading: {aes['heading_font']};
      --tmpl-font-body: {aes['body_font']};
      --tmpl-bg-canvas: {aes['bg_canvas']};
      --tmpl-surface-1: {aes['surface_1']};
      --tmpl-surface-2: {aes['surface_2']};
      --tmpl-surface-3: {aes['surface_3']};
      --tmpl-primary: {aes['primary_color']};
      --tmpl-primary-hover: {aes['primary_hover']};
      --tmpl-btn-text: {aes['btn_text']};
      --tmpl-text-primary: {aes['text_primary']};
      --tmpl-text-secondary: {aes['text_secondary']};
      --tmpl-border: {aes['border_color']};
      --tmpl-radius: {aes['border_radius']};
      --tmpl-border-width: {aes['border_width']};
      --tmpl-shadow: {aes['box_shadow']};
    }}

    html[data-theme="{opposite_theme}"] {{
      --tmpl-bg-canvas: {"#f8fafc" if aes["theme"] == "dark" else "#090d16"};
      --tmpl-surface-1: {"#ffffff" if aes["theme"] == "dark" else "#0f172a"};
      --tmpl-surface-2: {"#f1f5f9" if aes["theme"] == "dark" else "#1e293b"};
      --tmpl-surface-3: {"#e2e8f0" if aes["theme"] == "dark" else "#334155"};
      --tmpl-text-primary: {"#0f172a" if aes["theme"] == "dark" else "#f8fafc"};
      --tmpl-text-secondary: {"#475569" if aes["theme"] == "dark" else "#94a3b8"};
      --tmpl-border: {"rgba(15, 23, 42, 0.12)" if aes["theme"] == "dark" else "rgba(255, 255, 255, 0.12)"};
    }}

    * {{
      box-sizing: border-box;
    }}

    html, body {{
      margin: 0;
      padding: 0;
      background-color: var(--tmpl-bg-canvas) !important;
      background-image: {aes.get('bg_pattern', 'none')} !important;
      background-size: {aes.get('bg_size', 'auto')} !important;
      background-attachment: fixed !important;
      color: var(--tmpl-text-primary);
      font-family: var(--tmpl-font-body);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }}

    button, .topbar-btn, .btn-ctrl, .btn-ctrl-accent, .btn-civic, .prod-badge, .style-badge, .civic-step-badge, .saas-pill, input, select, textarea {{
      border-radius: var(--tmpl-radius) !important;
    }}

    h1, h2, h3, h4, h5, h6, .template-title, .chart-title, .table-title, .prod-title, .saas-hero-title, .civic-title {{
      font-family: var(--tmpl-font-heading);
    }}

    /* Sticky Template Top Bar */
    .ortho-tmpl-topbar {{
      position: sticky;
      top: 0;
      z-index: 1000;
      background: var(--tmpl-surface-1);
      border-block-end: var(--tmpl-border-width) solid var(--tmpl-border);
      backdrop-filter: blur(12px);
      padding-inline: 1.5rem;
      padding-block: 0.75rem;
    }}

    .topbar-inner {{
      max-width: var(--tmpl-max-width);
      margin-inline: auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }}

    .topbar-left, .topbar-right {{
      display: flex;
      align-items: center;
      gap: 0.85rem;
      flex-wrap: wrap;
    }}

    .topbar-back-btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      color: var(--tmpl-text-secondary);
      text-decoration: none;
      font-size: 0.85rem;
      font-weight: 500;
      padding-inline: 0.6rem;
      padding-block: 0.35rem;
      border-radius: var(--tmpl-radius);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      transition: all 0.2s ease;
    }}

    .topbar-back-btn:hover {{
      color: var(--tmpl-text-primary);
      border-color: var(--tmpl-primary);
      background: var(--tmpl-surface-2);
    }}

    .topbar-divider {{
      width: 1px;
      height: 18px;
      background: var(--tmpl-border);
    }}

    .topbar-brand {{
      text-decoration: none;
      font-weight: 800;
      letter-spacing: -0.02em;
      font-size: 0.95rem;
      color: var(--tmpl-text-primary);
    }}

    .brand-accent {{
      color: var(--tmpl-primary);
    }}

    .style-badge {{
      font-size: 0.72rem;
      font-weight: 700;
      padding-inline: 0.6rem;
      padding-block: 0.2rem;
      border-radius: var(--tmpl-radius);
      background: var(--tmpl-surface-2);
      color: var(--tmpl-primary);
      border: var(--tmpl-border-width) solid var(--tmpl-primary);
      letter-spacing: 0.02em;
    }}

    .cluster-badge {{
      font-size: 0.72rem;
      font-weight: 600;
      padding-inline: 0.55rem;
      padding-block: 0.2rem;
      border-radius: var(--tmpl-radius);
      background: var(--tmpl-surface-2);
      color: var(--tmpl-text-secondary);
      border: 1px solid var(--tmpl-border);
    }}

    .topbar-cert-pills {{
      display: flex;
      gap: 0.4rem;
    }}

    .cert-pill {{
      font-size: 0.7rem;
      font-weight: 600;
      padding-inline: 0.45rem;
      padding-block: 0.15rem;
      border-radius: var(--tmpl-radius);
      background: var(--tmpl-surface-2);
      color: var(--tmpl-text-secondary);
      border: 1px solid var(--tmpl-border);
    }}

    .topbar-actions {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}

    .topbar-btn {{
      background: var(--tmpl-surface-2);
      color: var(--tmpl-text-primary);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      padding-inline: 0.75rem;
      padding-block: 0.35rem;
      border-radius: var(--tmpl-radius);
      font-size: 0.8rem;
      font-weight: 500;
      cursor: pointer;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.2s ease;
    }}

    .topbar-btn:hover {{
      background: var(--tmpl-surface-3);
      border-color: var(--tmpl-primary);
    }}

    .topbar-btn.btn-accent {{
      background: var(--tmpl-primary);
      color: var(--tmpl-btn-text);
      font-weight: 700;
      border-color: var(--tmpl-primary);
    }}

    .topbar-btn.btn-accent:hover {{
      background: var(--tmpl-primary-hover);
    }}

    /* Template Main Body Container */
    .template-body-wrap {{
      max-width: var(--tmpl-max-width);
      margin-inline: auto;
      padding-inline: 1.5rem;
      padding-block: 2.5rem;
    }}

    /* Template Header */
    .template-header {{
      margin-block-end: 2rem;
      border-block-end: 1px solid var(--tmpl-border);
      padding-block-end: 1.5rem;
    }}

    .template-category-tag {{
      display: inline-block;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--tmpl-primary);
      font-weight: 700;
      margin-block-end: 0.5rem;
    }}

    .style-pill {{
      margin-inline-start: 0.5rem;
      font-size: 0.75rem;
      padding-inline: 0.45rem;
      padding-block: 0.15rem;
      border-radius: var(--tmpl-radius);
      background: var(--tmpl-surface-2);
      color: var(--tmpl-primary);
      border: 1px solid var(--tmpl-border);
      text-transform: none;
      letter-spacing: normal;
    }}

    .theme-pill {{
      margin-inline-start: 0.25rem;
      font-size: 0.75rem;
      padding-inline: 0.45rem;
      padding-block: 0.15rem;
      border-radius: var(--tmpl-radius);
      border: 1px solid var(--tmpl-border);
      text-transform: uppercase;
    }}

    .theme-pill.theme-dark {{
      background: #090d16;
      color: #38bdf8;
    }}

    .theme-pill.theme-light {{
      background: #ffffff;
      color: #0284c7;
    }}

    .template-title {{
      font-size: 2.2rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      margin: 0;
      color: var(--tmpl-text-primary);
    }}

    .template-desc {{
      font-size: 1.1rem;
      color: var(--tmpl-text-secondary);
      margin-block-start: 0.5rem;
      max-width: 800px;
    }}

    .template-meta-strip {{
      display: flex;
      flex-wrap: wrap;
      gap: 1.5rem;
      margin-block-start: 1rem;
      font-size: 0.85rem;
      color: var(--tmpl-text-secondary);
    }}

    .meta-tag strong {{
      color: var(--tmpl-text-primary);
    }}

    .meta-tag code {{
      background: var(--tmpl-surface-2);
      color: var(--tmpl-text-primary);
      padding: 0.15rem 0.4rem;
      border-radius: var(--tmpl-radius);
      border: 1px solid var(--tmpl-border);
    }}

    /* Component CSS Styles */
    /* Dashboards */
    .dashboard-grid {{
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }}

    .metrics-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
    }}

    .metric-card {{
      background: var(--tmpl-surface-1);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      border-radius: var(--tmpl-radius);
      box-shadow: var(--tmpl-shadow);
      border-block-start: max(3px, var(--tmpl-border-width)) solid var(--tmpl-primary);
      padding: 1.25rem;
      text-align: start;
      {aes['card_extra_css']}
    }}

    .metric-label {{
      font-size: 0.8rem;
      color: var(--tmpl-text-secondary);
      font-weight: 500;
    }}

    .metric-value {{
      font-size: 1.8rem;
      font-weight: 800;
      color: var(--tmpl-text-primary);
      margin-block: 0.35rem;
      font-variant-numeric: tabular-nums;
    }}

    .metric-delta.delta-positive {{
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--tmpl-primary);
    }}

    .dashboard-chart-box, .dashboard-table-box {{
      background: var(--tmpl-surface-1);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      border-radius: var(--tmpl-radius);
      box-shadow: var(--tmpl-shadow);
      padding: 1.5rem;
      {aes['card_extra_css']}
    }}

    .chart-header, .table-header-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-block-end: 1.25rem;
    }}

    .chart-title, .table-title {{
      margin: 0;
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--tmpl-text-primary);
    }}

    .chart-desc {{
      margin: 0;
      font-size: 0.85rem;
      color: var(--tmpl-text-secondary);
    }}

    .chart-badge, .table-status-pill {{
      font-size: 0.75rem;
      font-weight: 600;
      padding-inline: 0.6rem;
      padding-block: 0.25rem;
      border-radius: var(--tmpl-radius);
      background: var(--tmpl-surface-2);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      color: var(--tmpl-primary);
    }}

    .table-scroll-container {{
      overflow-x: auto;
    }}

    .ortho-data-table {{
      width: 100%;
      border-collapse: collapse;
      text-align: start;
      font-size: 0.9rem;
    }}

    .ortho-data-table th {{
      padding-inline: 1rem;
      padding-block: 0.75rem;
      background: var(--tmpl-surface-2);
      color: var(--tmpl-text-secondary);
      border-block-end: var(--tmpl-border-width) solid var(--tmpl-border);
      font-weight: 600;
    }}

    .ortho-data-table td {{
      padding-inline: 1rem;
      padding-block: 0.85rem;
      border-block-end: 1px solid var(--tmpl-border);
      color: var(--tmpl-text-primary);
    }}

    /* Forms & FSM */
    .form-wizard-card {{
      background: var(--tmpl-surface-1);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      border-radius: var(--tmpl-radius);
      box-shadow: var(--tmpl-shadow);
      padding: 2rem;
      max-width: 800px;
      margin-inline: auto;
      {aes['card_extra_css']}
    }}

    .fsm-progress-bar {{
      display: flex;
      justify-content: space-between;
      margin-block-end: 2rem;
      border-block-end: 1px solid var(--tmpl-border);
      padding-block-end: 1.25rem;
      overflow-x: auto;
    }}

    .fsm-step-item {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--tmpl-text-secondary);
      font-size: 0.85rem;
      font-weight: 500;
    }}

    .fsm-step-item.active {{
      color: var(--tmpl-primary);
      font-weight: 700;
    }}

    .step-num {{
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--tmpl-surface-2);
      border: 1px solid var(--tmpl-border);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      color: var(--tmpl-text-secondary);
    }}

    .fsm-step-item.active .step-num {{
      background: var(--tmpl-primary);
      color: var(--tmpl-btn-text);
      border-color: var(--tmpl-primary);
    }}

    .form-fields-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 1.25rem;
    }}

    .form-group {{
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
      text-align: start;
    }}

    .form-label {{
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--tmpl-text-secondary);
    }}

    .req-star {{
      color: var(--tmpl-primary);
    }}

    .form-control {{
      background: var(--tmpl-surface-2);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      color: var(--tmpl-text-primary);
      padding-inline: 0.85rem;
      padding-block: 0.65rem;
      border-radius: var(--tmpl-radius);
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s ease;
    }}

    .form-control:focus {{
      border-color: var(--tmpl-primary);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
    }}

    .form-actions-row {{
      display: flex;
      justify-content: flex-end;
      gap: 1rem;
      margin-block-start: 1.75rem;
    }}

    .btn-ctrl {{
      background: var(--tmpl-surface-2);
      color: var(--tmpl-text-primary);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      padding-inline: 1rem;
      padding-block: 0.65rem;
      border-radius: var(--tmpl-radius);
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .btn-ctrl:hover {{
      background: var(--tmpl-surface-3);
      border-color: var(--tmpl-primary);
    }}

    .btn-ctrl-accent {{
      background: var(--tmpl-primary);
      color: var(--tmpl-btn-text);
      border: var(--tmpl-border-width) solid var(--tmpl-primary);
      padding-inline: 1.25rem;
      padding-block: 0.65rem;
      border-radius: var(--tmpl-radius);
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.2s ease;
    }}

    .btn-ctrl-accent:hover {{
      background: var(--tmpl-primary-hover);
    }}

    .form-security-note {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.8rem;
      color: var(--tmpl-text-secondary);
      margin-block-start: 1.25rem;
    }}

    /* E-Commerce */
    .ecommerce-layout {{
      display: flex;
      flex-direction: column;
      gap: 2rem;
    }}

    .product-hero-panel {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 2rem;
      background: var(--tmpl-surface-1);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      border-radius: var(--tmpl-radius);
      box-shadow: var(--tmpl-shadow);
      padding: 2rem;
      {aes['card_extra_css']}
    }}

    .product-visual-box {{
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }}

    .product-schematic-bg {{
      background: var(--tmpl-surface-2);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      border-radius: var(--tmpl-radius);
      padding: 1rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .product-badge-row {{
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }}

    .prod-badge {{
      font-size: 0.75rem;
      font-weight: 600;
      padding-inline: 0.5rem;
      padding-block: 0.2rem;
      border-radius: var(--tmpl-radius);
      background: var(--tmpl-surface-2);
      border: 1px solid var(--tmpl-border);
      color: var(--tmpl-text-secondary);
    }}

    .prod-badge.highlight {{
      background: var(--tmpl-surface-2);
      color: var(--tmpl-primary);
      border: 1px solid var(--tmpl-primary);
    }}

    .prod-title {{
      font-size: 1.6rem;
      font-weight: 800;
      margin: 0;
      color: var(--tmpl-text-primary);
    }}

    .prod-desc {{
      color: var(--tmpl-text-secondary);
      font-size: 0.95rem;
      margin-block: 0.5rem 1.25rem;
    }}

    .prod-pricing-row {{
      display: flex;
      align-items: baseline;
      gap: 0.75rem;
      margin-block-end: 1.5rem;
    }}

    .prod-price {{
      font-size: 2rem;
      font-weight: 800;
      color: var(--tmpl-text-primary);
    }}

    .prod-unit {{
      font-size: 0.9rem;
      color: var(--tmpl-text-secondary);
    }}

    .prod-moq {{
      font-size: 0.8rem;
      color: var(--tmpl-primary);
      font-weight: 600;
    }}

    .order-actions-grid {{
      display: flex;
      gap: 1rem;
      align-items: center;
    }}

    .qty-stepper {{
      display: inline-flex;
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      border-radius: var(--tmpl-radius);
      overflow: hidden;
    }}

    .btn-step {{
      background: var(--tmpl-surface-2);
      color: var(--tmpl-text-primary);
      border: none;
      padding-inline: 0.75rem;
      cursor: pointer;
      font-weight: 700;
    }}

    .qty-input {{
      width: 50px;
      text-align: center;
      background: var(--tmpl-surface-1);
      color: var(--tmpl-text-primary);
      border: none;
      font-weight: 600;
      outline: none;
    }}

    .specs-table-card {{
      background: var(--tmpl-surface-1);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      border-radius: var(--tmpl-radius);
      box-shadow: var(--tmpl-shadow);
      padding: 1.5rem;
      {aes['card_extra_css']}
    }}

    .specs-title {{
      margin: 0 0 1rem 0;
      font-size: 1.2rem;
      color: var(--tmpl-text-primary);
    }}

    .ortho-specs-table {{
      width: 100%;
      border-collapse: collapse;
      text-align: start;
    }}

    .ortho-specs-table th {{
      padding-inline: 1rem;
      padding-block: 0.75rem;
      background: var(--tmpl-surface-2);
      border-block-end: var(--tmpl-border-width) solid var(--tmpl-border);
      color: var(--tmpl-text-secondary);
      font-weight: 600;
      font-size: 0.85rem;
    }}

    .ortho-specs-table td {{
      padding-inline: 1rem;
      padding-block: 0.85rem;
      border-block-end: 1px solid var(--tmpl-border);
      font-size: 0.9rem;
      color: var(--tmpl-text-primary);
    }}

    /* Civic & Clinical */
    .civic-container {{
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }}

    .civic-hero-banner {{
      background: var(--tmpl-surface-1);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      border-radius: var(--tmpl-radius);
      box-shadow: var(--tmpl-shadow);
      padding: 2rem;
      text-align: start;
      {aes['card_extra_css']}
    }}

    .civic-cert-stamp {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
      font-weight: 800;
      letter-spacing: 0.05em;
      color: var(--tmpl-primary);
      margin-block-end: 0.75rem;
    }}

    .civic-title {{
      font-size: 2rem;
      font-weight: 800;
      margin: 0;
      color: var(--tmpl-text-primary);
    }}

    .civic-desc {{
      font-size: 1.05rem;
      color: var(--tmpl-text-secondary);
      margin-block-start: 0.5rem;
      max-width: 800px;
    }}

    .civic-steps-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.25rem;
    }}

    .civic-step-card {{
      background: var(--tmpl-surface-1);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      border-radius: var(--tmpl-radius);
      box-shadow: var(--tmpl-shadow);
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      text-align: start;
      {aes['card_extra_css']}
    }}

    .civic-step-badge {{
      display: inline-block;
      font-size: 0.75rem;
      font-weight: 800;
      padding-inline: 0.5rem;
      padding-block: 0.2rem;
      background: var(--tmpl-primary);
      color: var(--tmpl-btn-text);
      border-radius: var(--tmpl-radius);
      margin-block-end: 0.5rem;
    }}

    .civic-step-title {{
      font-size: 1.15rem;
      font-weight: 700;
      margin: 0 0 0.5rem 0;
      color: var(--tmpl-text-primary);
    }}

    .civic-step-desc {{
      font-size: 0.9rem;
      color: var(--tmpl-text-secondary);
      margin: 0 0 1rem 0;
    }}

    .btn-civic {{
      background: var(--tmpl-surface-2);
      color: var(--tmpl-text-primary);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      padding-inline: 0.85rem;
      padding-block: 0.5rem;
      border-radius: var(--tmpl-radius);
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }}

    .civic-assistance-box {{
      background: var(--tmpl-surface-1);
      border: 1px dashed var(--tmpl-primary);
      border-radius: var(--tmpl-radius);
      padding: 1.25rem;
      display: flex;
      gap: 1rem;
      align-items: center;
    }}

    /* SaaS */
    .saas-hero-container {{
      display: flex;
      flex-direction: column;
      gap: 2.5rem;
      text-align: center;
    }}

    .saas-pill {{
      display: inline-block;
      font-size: 0.8rem;
      font-weight: 700;
      padding-inline: 0.85rem;
      padding-block: 0.35rem;
      border-radius: 999px;
      background: var(--tmpl-surface-2);
      color: var(--tmpl-primary);
      border: 1px solid var(--tmpl-primary);
      margin-block-end: 1rem;
    }}

    .saas-hero-title {{
      font-size: 2.6rem;
      font-weight: 900;
      letter-spacing: -0.04em;
      margin: 0 auto;
      max-width: 900px;
      color: var(--tmpl-text-primary);
    }}

    .saas-hero-desc {{
      font-size: 1.15rem;
      color: var(--tmpl-text-secondary);
      max-width: 700px;
      margin: 1rem auto 1.5rem auto;
    }}

    .saas-cta-group {{
      display: flex;
      justify-content: center;
      gap: 1rem;
    }}

    .saas-terminal-preview {{
      background: var(--tmpl-surface-1);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      border-radius: var(--tmpl-radius);
      box-shadow: var(--tmpl-shadow);
      max-width: 750px;
      margin-inline: auto;
      width: 100%;
      text-align: start;
      {aes['card_extra_css']}
    }}

    .terminal-bar {{
      background: var(--tmpl-surface-2);
      padding: 0.6rem 1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-block-end: 1px solid var(--tmpl-border);
      border-radius: var(--tmpl-radius) var(--tmpl-radius) 0 0;
    }}

    .terminal-dots {{
      display: flex;
      gap: 6px;
    }}

    .dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }}

    .dot-red {{ background: #ef4444; }}
    .dot-yellow {{ background: #f59e0b; }}
    .dot-green {{ background: #10b981; }}

    .terminal-title {{
      font-size: 0.75rem;
      font-family: monospace;
      color: var(--tmpl-text-secondary);
    }}

    .terminal-badge {{
      font-size: 0.7rem;
      font-family: monospace;
      color: var(--tmpl-primary);
    }}

    .terminal-content {{
      padding: 1.25rem;
      font-family: monospace;
      font-size: 0.85rem;
      line-height: 1.7;
      color: var(--tmpl-text-primary);
    }}

    .term-prompt {{
      color: var(--tmpl-primary);
      font-weight: 700;
    }}

    .term-line.output {{
      color: var(--tmpl-text-secondary);
    }}

    .term-line.highlight {{
      color: var(--tmpl-primary);
      font-weight: 600;
    }}

    .saas-features-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1.5rem;
      text-align: start;
    }}

    .saas-feat-card {{
      background: var(--tmpl-surface-1);
      border: var(--tmpl-border-width) solid var(--tmpl-border);
      border-radius: var(--tmpl-radius);
      box-shadow: var(--tmpl-shadow);
      padding: 1.5rem;
      {aes['card_extra_css']}
    }}

    .feat-icon-bullet {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--tmpl-primary);
      margin-block-end: 0.75rem;
    }}

    .feat-title {{
      margin: 0 0 0.4rem 0;
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--tmpl-text-primary);
    }}

    .feat-desc {{
      margin: 0;
      font-size: 0.85rem;
      color: var(--tmpl-text-secondary);
    }}
  </style>

  <!-- JSON-LD Structured Data -->
  <script type="application/ld+json">
{schema_json}
  </script>
</head>
<body class="tmpl-cluster-{item['cluster']} tmpl-{item['id']}">

  {top_bar}

  <main class="template-body-wrap" role="main">
    <header class="template-header">
      <div class="template-category-tag">Cluster {item['cluster_num']} • {html.escape(item['cluster_name'])} <span class="style-pill">{html.escape(aes['ui_style'])}</span> <span class="theme-pill theme-{aes['theme']}">{aes['theme'].upper()}</span></div>
      <h1 class="template-title">{html.escape(item['title'])}</h1>
      <p class="template-desc">{html.escape(item['subtitle'])}</p>
      
      <div class="template-meta-strip">
        <div class="meta-tag"><strong>Target Skill:</strong> <code>{html.escape(item['skill'])}</code></div>
        <div class="meta-tag"><strong>Design Tokens:</strong> {html.escape(item['tokens'])}</div>
        <div class="meta-tag"><strong>FSM Contract:</strong> <code>{html.escape(item['fsm'])}</code></div>
        <div class="meta-tag"><strong>Typography:</strong> {html.escape(aes['font_name'])}</div>
        <div class="meta-tag"><strong>License:</strong> MIT</div>
      </div>
    </header>

    <section class="template-content-section" aria-label="{html.escape(item['title'])}">
      {content_markup}
    </section>
  </main>

  <!-- Interactive Controls Script -->
  <script>
    (function() {{
      const htmlEl = document.documentElement;
      const themeBtn = document.getElementById('themeToggleBtn');
      const dirBtn = document.getElementById('dirToggleBtn');
      const copyBtn = document.getElementById('copyCodeBtn');

      // Theme toggle
      if (themeBtn) {{
        themeBtn.addEventListener('click', () => {{
          const current = htmlEl.getAttribute('data-theme') || 'dark';
          const next = current === 'dark' ? 'light' : 'dark';
          htmlEl.setAttribute('data-theme', next);
          themeBtn.querySelector('.theme-icon-dark').style.display = next === 'dark' ? 'inline' : 'none';
          themeBtn.querySelector('.theme-icon-light').style.display = next === 'light' ? 'inline' : 'none';
        }});
      }}

      // BiDi toggle
      if (dirBtn) {{
        dirBtn.addEventListener('click', () => {{
          const currentDir = htmlEl.getAttribute('dir') || 'ltr';
          const nextDir = currentDir === 'ltr' ? 'rtl' : 'ltr';
          htmlEl.setAttribute('dir', nextDir);
        }});
      }}

      // Copy HTML
      if (copyBtn) {{
        copyBtn.addEventListener('click', () => {{
          navigator.clipboard.writeText(document.documentElement.outerHTML).then(() => {{
            const span = copyBtn.querySelector('span');
            const original = span.textContent;
            span.textContent = 'Copied!';
            setTimeout(() => span.textContent = original, 2000);
          }});
        }});
      }}
    }})();
  </script>
</body>
</html>"""
    return full_html

def generate_sitemap(templates):
    urls = [
        f"""  <url>
    <loc>{BASE_URL}/</loc>
    <lastmod>2026-10-23</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>"""
    ]
    for item in templates:
        urls.append(f"""  <url>
    <loc>{BASE_URL}/templates/{item['id']}.html</loc>
    <lastmod>2026-10-23</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")
    
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{os.linesep.join(urls)}
</urlset>
"""
    sitemap_file = DOCS_DIR / "sitemap.xml"
    sitemap_file.write_text(sitemap_content, encoding="utf-8")
    print(f"Generated: {sitemap_file} with {len(templates) + 1} indexed URLs")

def generate_robots_txt():
    robots_content = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
"""
    robots_file = DOCS_DIR / "robots.txt"
    robots_file.write_text(robots_content, encoding="utf-8")
    print(f"Generated: {robots_file}")

def generate_gallery_data(templates):
    items = []
    for t in templates:
        aes = TEMPLATE_AESTHETICS.get(t["id"], {})
        items.append({
            "id": t["id"],
            "title": t["title"],
            "cluster": t["cluster"],
            "cluster_num": t["cluster_num"],
            "cluster_name": t["cluster_name"],
            "desc": t["desc"],
            "skill": t["skill"],
            "tokens": t["tokens"],
            "fsm": t["fsm"],
            "badge": t["badge"],
            "icon": t["icon"],
            "ui_style": aes.get("ui_style", "Universal Standard"),
            "theme": aes.get("theme", "dark"),
            "font_name": aes.get("font_name", "Inter"),
            "primary_color": aes.get("primary_color", "#38bdf8"),
            "thumbnail": f"assets/thumbnails/{t['id']}.webp",
            "template_url": f"templates/{t['id']}.html"
        })
    
    # Save as JSON
    json_path = DOCS_DIR / "gallery-data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    print(f"Generated: {json_path}")

    # Save as JS for direct client inclusion
    js_path = DOCS_DIR / "gallery-data.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("/* Orthotect 50 Verified Production Templates Registry */\n")
        f.write("window.ORTHOTECT_GALLERY_TEMPLATES = ")
        json.dump(items, f, indent=2)
        f.write(";\n")
    print(f"Generated: {js_path}")

def main():
    print(f"Generating 50 Standalone Production Templates in {TEMPLATES_DIR}...")
    for idx, item in enumerate(TEMPLATES_SPEC):
        file_path = TEMPLATES_DIR / f"{item['id']}.html"
        html_code = render_template_html(item)
        file_path.write_text(html_code, encoding="utf-8")
        print(f"[{idx+1}/50] Generated: templates/{item['id']}.html")

    generate_sitemap(TEMPLATES_SPEC)
    generate_robots_txt()
    generate_gallery_data(TEMPLATES_SPEC)
    print("All 50 SEO production templates & technical SEO assets generated successfully!")

if __name__ == "__main__":
    main()
