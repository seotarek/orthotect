# Orthotect Evidence-Based Benchmark Methodology

## 1. Executive Summary

This document defines the transparent, reproducible evaluation framework used by Orthotect to assess interface engineering quality, design intelligence, and verification rigor across 10 objective dimensions.

Orthotect rejects unverified marketing claims such as "100% WCAG certified", "zero CLS", or "best in class" unless backed by reproducible code, automated test output, and documented limitations.

---

## 2. Evaluation Dimensions & Scoring Rubric

Every evaluated component or interface is scored against 10 objective dimensions on a 0 to 10 scale:

| Dimension | Verification Mechanism | Evaluation Criteria |
| :--- | :--- | :--- |
| **1. Functional Correctness** | Automated Unit Tests | All controls, forms, and transitions operate without console errors or runtime exceptions. |
| **2. Mathematical Contrast** | WCAG 2.2 Relative Luminance | Text meets $\ge 4.5:1$ (AA) or $\ge 7.0:1$ (AAA); UI controls meet $\ge 3.0:1$. |
| **3. Bidirectional Symmetry** | AST Logical Property Check | 100% CSS logical property adoption; 0 physical directional coordinates (`left`, `right`). |
| **4. State Machine Rigor** | Graph Reachability & Locks | 0 reachable deadlocks; loading transition locks prevent double-clicks; explicit error state. |
| **5. Layout Stability (CLS)** | Media Bounding Check | 100% of media elements have explicit width/height or valid `aspect-ratio` reserving bounding box. |
| **6. Anti-Slop Discipline** | Pattern Inspector | 0 uncalibrated generic purple gradients; 0 raw emojis used as icons; 0 hardcoded styling. |
| **7. Multi-Viewport Responsiveness** | Real-Browser Viewport Scan | Evaluated at 320px, 360px, 390px, 768px, 1024px, 1280px, 1440px with 0 horizontal overflow. |
| **8. Accessibility Conformance** | Keyboard & ARIA Review | Focus trap in modals; visible focus rings; proper ARIA roles and accessible names. |
| **9. Performance Footprint** | Dependency & Latency Scan | 0 runtime client bloat; parallel verification latency $< 1000\text{ms}$. |
| **10. Proof Integrity** | Honest Result Semantics | Missing or unverified inputs yield `NOT_EVALUATED`, never a false `PASS`. |

---

## 3. Result Classification Semantics

To ensure complete honesty and prevent false confidence:
* **`PASS`**: The check was executed against actual input, met the mathematical/AST criteria, and verified.
* **`FAIL`**: The check was executed and detected one or more verified violations.
* **`NOT_EVALUATED`**: The input or environment required to evaluate the check was missing or unsupported (e.g. contrast evaluation when no foreground/background pairs were declared).
* **`SKIPPED`**: Explicitly bypassed by configuration with a documented rationale.
