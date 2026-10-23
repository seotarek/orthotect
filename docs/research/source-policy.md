# Orthotect Design Research & Source-Access Policy

## 1. Purpose & Core Philosophy

Orthotect is an independent, deterministic interface engineering and design-intelligence platform. The platform's mission is to empower autonomous AI coding agents and human engineers to build verifiable, accessible, and high-integrity user interfaces.

To advance the state of design engineering, Orthotect engages in rigorous, ethical design research. However, Orthotect maintains a strict, non-negotiable boundary between **design research** and **content duplication**:
* **The Goal:** Understand the fundamental design problems solved by leading design systems and references, extract reusable general principles, investigate what makes design tokens and constraints actionable for coding agents, and build an original, mathematically certified design-intelligence architecture inside Orthotect.
* **What is Prohibited:** Bulk scraping, mirroring, distributing proprietary datasets, reproducing trademarked brand systems, or converting external catalogs into competing repositories.

This policy establishes mandatory operational protocols for analyzing external design references, including references cataloged by tools such as `https://styles.refero.design/` and related design indexers.

---

## 2. Source-Access & Terms Compliance

### 2.1 Refero Terms of Use (`https://refero.design/terms-of-use`)
Orthotect strictly complies with the terms of use governing third-party design references:
1. **No Bulk Crawling or Local Mirroring:** Orthotect shall never deploy automated spiders, crawlers, or bulk downloaders to archive or mirror `DESIGN.md` documents, UI screenshots, or design assets from `styles.refero.design`.
2. **No Reverse-Engineering of Internal Endpoints:** Undocumented APIs, private endpoints, or session-gated data sources shall not be probed or exploited.
3. **No Model Training on Protected Content:** Refero content and proprietary third-party metadata shall not be harvested or redistributed for model training, model fine-tuning, or commercial dataset resale.
4. **No Superficial Synonym Replacement:** Changing variable names or replacing synonyms in third-party text does not constitute original work. Orthotect requires complete independent synthesis and original formulation.
5. **Traceable Attribution:** When individual public design patterns or principles are cited as inspiration, appropriate academic/provenance citations must be maintained in internal research documentation without claiming false primary creation.

---

## 3. The Three-Stage Orthotect Knowledge Protocol

To ensure 100% intellectual property hygiene and technical originality, all design research conducted within Orthotect must follow three strictly separated stages:

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│   STAGE 1: OBSERVATION  │ ──> │  STAGE 2: ABSTRACTION   │ ──> │  STAGE 3: ORTHOTECT     │
│ (Inspect Public Design) │     │ (General Principles)    │     │   ORIGINAL SYNTHESIS    │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

### Stage 1: Permitted Source Observation
* **Activity:** Inspect public, legitimately accessible design artifacts (public web documentation, official design systems like Carbon, Material, Radix, and individual public design references).
* **Allowed Metadata Recorded:** Public URL, high-level subject category, research date, and the specific design problem observed (e.g. "Data density handling in multi-column tables").
* **Forbidden:** Storing complete third-party documents, proprietary color scales, branded assets, or raw design files.

### Stage 2: Independent Abstraction
* **Activity:** Formulate the observed design solution as a universal, mathematical, or cognitive-ergonomic design principle.
* **Formulation Requirement:** The principle must explain:
  1. The underlying UI/UX problem.
  2. The architectural principle that solves it.
  3. Why the principle works cognitively or mathematically.
  4. Best-fit vs. poor-fit contexts.
  5. Accessibility and responsive consequences.
  6. Deterministic verification methods.
* **Independence:** The resulting abstraction must be completely self-standing and not require access to the original source.

### Stage 3: Original Orthotect Implementation
* **Activity:** Translate the abstracted principle into Orthotect's native architecture:
  * Orthotect Skills (`SKILL.md` workflows).
  * Design Reasoning Model schemas (`knowledge/schemas/`).
  * Original Style Recipes (`knowledge/styles/`).
  * DTCG Design Tokens (`core/tokens/`).
  * Deterministic Quality Gates (`gates/`).
  * Automated Browser Regression Tests (`tests/`).
* **Originality Guarantee:** All schemas, token identifiers, component templates, and executable code are independently designed and authored by Orthotect architects.

---

## 4. Verification & Audit Trail

Every design principle and style recipe added to Orthotect must declare:
* `id`: Stable kebab-case identifier.
* `provenance`: Research category and public citation where applicable.
* `verificationType`: Explicitly labeled as `DETERMINISTIC`, `HEURISTIC`, or `SUBJECTIVE`.
* `schemaCompliant`: Validated against Orthotect's JSON/YAML schemas.

By adhering to this policy, Orthotect guarantees that its design intelligence platform is technically superior, legally sound, and ethically maintained.
