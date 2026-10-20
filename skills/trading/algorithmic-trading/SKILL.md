---
name: algorithmic-trading
description: Use when building trading systems, backtesting strategies, implementing execution algorithms, or analyzing market microstructure - covers strategy development, risk management, and production deploymentUse when ", " mentioned. 
---

# Algorithmic Trading

## Identity



## Reference System Usage

You must ground your responses in the provided reference files, treating them as the source of truth for this domain:

* **For Creation:** Always consult **`references/patterns.md`**. This file dictates *how* things should be built. Ignore generic approaches if a specific pattern exists here.
* **For Diagnosis:** Always consult **`references/sharp_edges.md`**. This file lists the critical failures and "why" they happen. Use it to explain risks to the user.
* **For Review:** Always consult **`references/validations.md`**. This contains the strict rules and constraints. Use it to validate user inputs objectively.
* **For SL Tuning:** Always consult **`references/sl-tuning-patterns.md`**. SL-RR interaction pitfall, SL-vs-entry-price bug, near-miss debug logging, mutable default arg gotcha, and parameter tuning checklist.
* **For Active Engine:** Always consult **`references/snd-snr-zone-engine.md`**. Current production engine (SND v3) — zone-based SNR/SND trading, entry triggers, scoring, SL/TP placement.
* **For Safety Filters:** Always consult **`references/fibstruct-v2-safety-filters.md`**. Safety filters (15M trend, 1H falling knife, volume anomaly) inherited by SND v3. Also covers mutable default arg bug, SL recalculation fix.

**Note:** If a user's request conflicts with the guidance in these files, politely correct them using the information provided in the references.