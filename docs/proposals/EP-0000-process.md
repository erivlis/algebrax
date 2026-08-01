---
title: "EP-0000: Enhancement Proposals"
description: "The process for creating, reviewing, and implementing Enhancement Proposals (EPs)."
icon: lucide/file-text
status: active
---

# EP-0000: Tur Enhancement Proposals

| Field       | Value                    |
|:------------|:-------------------------|
| **EP**      | 0000                     |
| **Title**   | Enhancement Proposals    |
| **Author**  | Eran Rivlis              |
| **Status**  | Active                   |
| **Type**    | Process                  |
| **Created** | 2026-02-19               |
| **Updated** | 2026-04-12               |

## Abstract

This document describes the process for creating, reviewing, and implementing Enhancement Proposals (EPs).
EPs are the primary mechanism for proposing major new features, collecting community input, and documenting design
decisions.

## Rationale

To maintain the architectural integrity of the system and adhere to the **Council Framework**, major changes require
careful consideration. EPs provide a structured way to:

1. **Falsify** ideas before implementation (Popper).
2. Ensure **Clarity** in design (Feynman).
3. Maintain a history of decisions (**Harmony**).

## The EP Workflow

1. **Draft:** The author creates a new file in `design/proposals/` using the template.
2. **Review:** The proposal is reviewed by the maintainers (The Council).
3. **Status Change:**
    * **Accepted:** The design is approved.
    * **Rejected:** The design is flawed or misaligned.
    * **Deferred:** Good idea, but not now.
    * **Superseded:** Replaced by a newer EP.
    * **Withdrawn:** The author withdrew the proposal.
4. **Implementation:** The code is written.
5. **Final:** The feature is released.

## EP Types

* **Standards Track:** New features or behavioral changes.
* **Process:** Meta-EPs (like this one) describing procedures.
* **Informational:** Design issues or general guidelines.

## Template

```markdown
---
title: "EP-XXXX: Title"
description: "One-sentence summary of the proposal — used in navigation and search."
icon: lucide/<icon-name>
status: draft
---

# EP-XXXX: Title

| Field       | Value           |
|:------------|:----------------|
| **EP**      | XXXX            |
| **Title**   | Title           |
| **Author**  | Name            |
| **Status**  | Draft           |
| **Type**    | Standards Track |
| **Created** | YYYY-MM-DD      |
| **Updated** | YYYY-MM-DD      |

## Abstract

Short summary of the proposal.

## Motivation

Why is this change needed? What problem does it solve?

## Rationale

Why this specific design? How does it align with the Council Framework?

## Specification

Technical details of the implementation.

## Backwards Compatibility

Does this break existing code? How will the transition be handled?

## Reference Implementation

Link to code or pseudo-code.

## Change Log

* **YYYY-MM-DD:**
    * Initial Draft.
    * Another change made on the same day.
```
