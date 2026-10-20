---
name: linkedin-profile-optimization
description: Build and optimize LinkedIn profiles for personal branding — fresh graduates, career changers, and professionals. Covers headline, about, experience, skills, and positioning strategy.
triggers:
  - user asks about LinkedIn profile
  - user wants to improve personal branding
  - user asks how to write headline/about/experience on LinkedIn
  - user is a fresh graduate building professional presence
---

# LinkedIn Profile Optimization

## Core Philosophy

LinkedIn is a **positioning tool**, not a resume mirror. Every section should answer: *"Why should someone care about this person?"*

For fresh graduates: lead with **what you can do**, not just what you studied.

---

## Section-by-Section Guide

### 1. Headline
- Appears under name everywhere — search, comments, connection requests
- NOT a motto or inspirational quote — it's a **professional positioning statement**
- Format: `[Role/Background] | [Key Skills] | [Value Proposition]`
- Example: `Agroindustrial Technology Graduate | Data Analysis · Next.js · UI/UX | Bridging Food Industry & Digital Solutions`
- Keep under 220 characters

### 2. About / Summary
Structure (3–4 paragraphs):
1. Who you are + field
2. Key skills / hands-on experience (mention specific tools/projects)
3. What you're looking for / career direction
4. CTA — invite to connect or collaborate

Write in first person, conversational but professional. Avoid generic phrases like "hardworking" or "passionate learner."

### 3. Industry Field
Pick the field closest to your **domain knowledge**, not your tech stack:
- Food & Beverages → for Agroindustry, Food Tech, FMCG
- Agriculture → for agribusiness, farming tech
- Information Technology & Services → if pivoting fully to tech
- Education → if targeting teaching/training roles

Can be changed anytime as career direction shifts.

### 4. Experience / Projects
- Include internships, final year projects, freelance, org roles — everything counts
- Write results, not tasks:
  - ❌ "Membuat website untuk klien"
  - ✅ "Developed marketing website using Next.js, increasing brand visibility for Teaching Factory product"
- Ongoing projects (e.g. skripsi): set end date as "Present"

### 5. Education
- Full institution name, degree, years
- Add relevant activities, organizations, achievements

### 6. Skills
- Add all relevant technical + domain skills
- Request endorsements from classmates, lecturers, colleagues
- LinkedIn surfaces top 3 most endorsed — make sure those are your strongest

### 7. Featured Section
- Best place for portfolio links, GitHub, live projects, publications
- Add after project/website is live — don't leave it empty with placeholder

---

## Positioning Strategies

### The "Niche + Tech" Angle
When a user has domain expertise (food, agriculture, law, medicine) PLUS technical skills (coding, data, design) — this is a **rare combination**. Position it as a bridge:
> "I bring [domain] knowledge AND [tech skill] — I can solve problems others can't even see."

This works especially well for:
- Agroindustry + web dev / data analysis
- Biology + bioinformatics
- Business + automation/coding

### Fresh Graduate Differentiators
- Final year project = valid work experience entry
- Certifications (Google, Coursera, etc.) fill experience gaps
- Content creation about your field builds authority fast

---

## Cicil / Incremental Build Order
When user is still in progress (e.g. still writing skripsi), recommend this order:

1. **Profile photo** — professional, clear face, neutral background
2. **Headline** — update immediately, high visibility
3. **About section** — draft now, refine later
4. **Education** — fill completely
5. **Skills** — add all now, get endorsements
6. **Project/Experience** — add as "Present" / ongoing
7. **Featured section** — wait until project is live/published
8. **Recommendations** — request from supervisor after graduation

---

## Indonesian Context Notes
- Many Indonesian recruiters still use LinkedIn in English — default to English for broader reach
- Bilingual profiles (English about + Indonesian experience descriptions) are acceptable
- SMKN/vocational school collaborations are valid and impressive project entries
- Teaching Factory projects show real-world application — highlight them

---

## LinkedIn Banner Generation (PIL)

LinkedIn banner size: **1584 x 396 px**.

Generate with Pillow (`pip install Pillow`). Proven dark-theme approach:
- Manual horizontal gradient loop (`for x in range(W)`) for smooth bg
- Accent line top (4px, brand color)
- Decorative circles + dot grid on right side for depth
- Name in large bold font (~58pt), subtitle ~26pt, skill tags ~18pt
- Rounded rectangle skill tags with border + fill
- Bottom tagline in muted color
- Save as PNG to `/tmp/linkedin_banner.png`, deliver via MEDIA:

**Pitfall:** `draw.textbbox()` returns `(x0, y0, x2, y2)` — don't use `name_bbox[3]-200` as rect right edge (it goes negative for short names). Use a fixed pixel value like `500` instead.


---

## Skills Field Notes
- Use **`SPSS Statistics`** (not just "SPSS") — more specific and recognized
- All skills should be in **English** — LinkedIn search algorithm is English-first; Indonesian skill names won't surface in recruiter searches
- For org involvement (BEM, DPM): add as **Experience entries**, not just Education description

---

## Skill Honesty & AI-Assisted Work

A common question: *"Can I list skills that AI helped me build?"*

**Rule:** Only list skills you can defend in an interview. If you can't explain what the code does or answer a technical question about it, don't list it as a skill.

**What you CAN claim honestly when AI did the implementation:**
- `AI-Assisted Development` — valid, in-demand skill right now
- `Prompt Engineering` — if you directed the AI effectively
- `Project Management` — you managed the scope, requirements, and direction

**In About section:** Write *"Currently building X using Next.js with AI-assisted development"* — honest and shows growth mindset.

**Bottom line:** Recruiters who discover inflated skills during interviews will reject immediately. A smaller honest skill set + clear growth trajectory beats a padded list every time.

---

## Templates
See `templates/linkedin-sections.md` for ready-to-copy section drafts.
