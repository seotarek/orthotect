---
name: orthotect-schema
description: Semantic structured data and Schema.org JSON-LD engineering for accessible, search-engine-crawlable interfaces. Use when adding or validating JSON-LD, WebSite, SoftwareApplication, Organization, FAQPage, or BreadcrumbList rich snippets.
metadata:
  version: 1.0.0
---

# Skill: Orthotect Semantic Structured Data & Schema.org

Engineer deterministic, valid Schema.org structured data in JSON-LD format. Orthotect treats structured data as an essential facet of interface architecture: machine-readable semantic graphs empower search crawlers, AI agents, and accessibility parsers to understand UI content accurately.

## Reference Routing

Load the matching reference before generating or auditing JSON-LD markup:

| Intent | Reference File | Covers |
|---|---|---|
| Complete JSON-LD templates for WebSite, SoftwareApplication, Organization, FAQ, Breadcrumbs | [jsonld-templates.md](references/jsonld-templates.md) | Copy-pasteable, verified Schema.org snippets with multi-entity `@graph` support |

---

## The 4 Core Principles of Schema Engineering

### 1. Visible Content Parity (Prevent Phantom Data)
- Every property declared in JSON-LD should correspond to content visibly rendered on the page. Declaring pricing, reviews, or FAQs absent from the rendered DOM risks Google rich-result penalties and misleads user agents.

### 2. Native JSON-LD Script Injection
- Embed structured data exclusively within `<script type="application/ld+json">` elements placed inside `<head>` or at the close of `<body>`. Avoid legacy Microdata or RDFa attributes embedded in HTML tags.

### 3. Unified `@graph` Architecture
- On multi-faceted pages (e.g. SaaS homepage with Organization, WebSite, and SoftwareApplication), unify entities into a single `@graph` array connected via `@id` URIs rather than scattering multiple disconnected script tags.

### 4. Deterministic Type Contracts
- Provide structured data properties aligned with Google Search Central guidelines:

| Schema Entity | Target Surface | Google Requirements | Recommended Enhancements |
|---|---|---|---|
| `WebSite` | Homepage / Site Search | Required: `name`, `url` | `potentialAction` (SearchAction) |
| `Organization` | Company / Brand Identity | Recommended: `name`, `url`, `logo` *(No mandatory properties required by Google for general organizations)* | `sameAs` (social profiles), `contactPoint` |
| `SoftwareApplication` | SaaS / Web Tools | Required: `name`, `offers` (`price`, `priceCurrency`), AND either `aggregateRating` or `review` *(only when genuine ratings/reviews are visibly displayed on the page)* | `applicationCategory`, `operatingSystem`, `description` |
| `FAQPage` | Documentation / FAQ | Required: `mainEntity` *(Note: Since August 2023, Google SERP rich snippet accordions are restricted to authoritative health & government domains; general sites retain LLM/crawler understanding)* | `acceptedAnswer` with plain text or valid HTML |
| `BreadcrumbList` | Navigation Trees | Required: `itemListElement` (`position`, `name`, `item`) | Nested item hierarchies |

---

## Attribution & Licensing

Portions of the schema markup guidance adapted from [marketingskills](https://github.com/coreyhaines31/marketingskills) by Corey Haines under the MIT License (Copyright 2025 Corey Haines).
