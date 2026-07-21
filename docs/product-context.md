# Open ACP — Canonical Product Context (All Products)

> **Standalone handoff document.** Everything needed is inlined — no repo access required.
> Derived from the `open_acp` repo's product manifests, structure profiles, packaging manifests,
> the NIAT target-audience source, and the product catalog doc. Dates are internal working
> context (baseline snapshot **April 16, 2026**), not finalized launch metadata.
> Generated 2026-07-06.

---

## 1. The layering model (read this first)

Products do **not** replace curriculum. The system composes a delivered learning experience in layers:

```
stack/domain curriculum          (e.g. genai, fullstack, dsa — the actual content)
  + structure profile            (the container hierarchy — see §3)
  + product family / version     (delivery + packaging + pedagogy overlays)
  + packaging profile            (module/topic counts, unit mix, assessment cadence — see §4)
  = delivered learning experience
```

Rules:
- The same stack curriculum (e.g. `genai`) can be packaged differently by different products.
- Product overlays adjust delivery mode, packaging, pedagogy emphasis, assessment cadence, and end-of-course outputs.
- Some products may require **course variants**, not just packaging variants (Launchpad is the flagged case: the same course name — e.g. Operating Systems, Computer Networks — may not imply the same course variant across Launchpad and NIAT).
- `default` is the stack-only fallback when no explicit product is selected; every product manifest is deep-merged **over** it.

### How resolution actually works (runtime semantics)

The loader (`curriculum_context.py`) resolves product context deterministically:

1. **Product merge:** load `default` manifest → deep-merge the named product manifest over it.
2. **Version overlay:** if a version is requested (or the product has `default_version`), deep-merge `versions.<V>` over the merged manifest (this is how e.g. Intensive `Offline` flips `live_sessions_included` to true).
3. **Packaging layer precedence** (later layers override earlier; field-level provenance is tracked):
   `global default → stack fallback (per-domain packaging manifest) → product default → product domain → product version → product version-domain → legacy overrides`
4. **Pedagogy layers** resolve the same way: product default → domain → version → version-domain.
5. Legacy unit type `ppt_video_unit` is normalized to `video_session_unit` everywhere.
6. If no product is selected, the label is "Stack-only default" — kept only for tests/back-compat; real curriculum runs should pass an explicit product.

### Product category taxonomy

- `degree_program_product` → **NIAT** (and future: BITS Product)
- `certification_or_upskilling_product` → **Academy**, **Intensive**, **GRIT** (and future: MINT, Launchpad)
- `event_or_workshop_product` (future) → Makers Conclave, Partnership Workshops, Govt Workshops, Master Classes, Employee Workshops
- `media_or_brand_product` (future) → Youtube Series, Content Branding Pipeline
- `standard_product` → `default` fallback only

### At-a-glance matrix (post-merge values, i.e. what runtime resolves)

| product | category | structure profile | default ver | focus | recorded | live | AI tutor | cheatsheet | offline req |
|---|---|---|---|---|---|---|---|---|---|
| **NIAT** | degree program | `niat_university_structure` | B3 | active | ✅ | ❌ | ✅¹ᵃ | ❌ | ✅ |
| **Academy** | cert/upskilling | `academy_certification_structure` | 1.5 | active | ✅ | ✅ | ❌ | ✅ | — |
| **Intensive** | cert/upskilling | `standard_product_structure` | Offline | active | ✅ | ✅¹ | ❌ | ✅ | — |
| **GRIT** | cert/upskilling | `standard_product_structure` | — | future | ✅ | ❌ | ❌ | ❌ | — |
| **Launchpad** | cert/upskilling | `standard_product_structure` | — | deferred | ✅ | ✅ | ❌ | ✅ | — |
| **default** | standard (fallback) | `standard_product_structure` | — | default | ❌ | ❌ | ❌ | ❌ | — |

¹ Intensive live sessions are **off** at the product default but **on** in the `Offline` version overlay.
¹ᵃ NIAT AI tutor confirmed **live for all questions, enabled at course level** (platform owner, 2026-07-07); the manifest previously said false and has been corrected.

---

## 2. Product-by-product context

### 2.1 NIAT

**Meaning:** NxtWave Innovation of Advanced Technologies — the **university-collaboration** product.
**Category:** `degree_program_product` · **Structure:** `niat_university_structure` · **Container:** `academic_degree_curriculum`
**Default version:** `B3` · **Focus:** active

**Feature flags:** recorded ✅ · live ❌ · **ai_tutor ✅ (course-level, all questions — corrected 2026-07-07)** · summary_cheatsheet ❌ · **offline_delivery_required ✅**

**Delivery:** offline-only, full-time, college-style (smart classrooms, hostel/campus, college timetable). A learning portal still provides recorded assets and materials per course.

**Target audience (summary — full profile in Appendix A):** post-12th students enrolled in partner universities. An academic-degree audience, NOT generic upskilling: expects a full-time college-like experience, is early in its technical journey, needs multi-year structured progression, requires both degree-oriented and industry-readiness outcomes.

**Academic progression roadmap:**
- Years 1–2: foundations, MERN/full-stack build work, early projects
- Year 2: DSA + competitive coding emphasis increases
- Year 3: specialization (software engineering or AI/ML tracks)
- Year 4: capstone projects + interview preparation

**Pedagogy manifest content:**
- Default rationale: bias toward industry-aligned, project-based learning while respecting academic sequencing, campus delivery, and degree-program constraints.
- Domain `genai`: pedagogy_profile `project_build_along` — learners repeatedly connect models, system architecture, and deployable workflows instead of treating GenAI as isolated theory.
- Version `B3`: pedagogy must scale across many partner universities while keeping milestone-based implementation, assessment checkpoints, and placement-oriented outcomes consistent.
- B3×genai: `project_build_along` baseline — academic progression + industry-facing implementation practice + checkpointed readiness for IRC and placement pathways simultaneously.

**Packaging (product manifest values):**
- Default (`niat_default_packaging`): 3 modules/course (2–5, ~8h each) · 4 topics/module (2–6) · 3 learning units/topic · allowed units: video_session, reading_material, mcq_practice, coding_practice · preferred mix: video, reading, mcq · classroom quiz every 20 min · module quiz required · skill assessment every 8 topics (mcq/coding/fib/project; easy/medium/hard)
- Domain `genai` (`niat_genai_packaging`): preferred mix swaps mcq→coding_practice; topic phase labels: Problem framing → Architecture and concepts → Guided build → Checkpoint and quiz
- Version B3 (`niat_b3_packaging`), B3×genai (`niat_b3_genai_packaging`): **total 120h ±5%**, 3 modules (2–4, ~8h), 4 topics (3–5)

**Versions / batches:**

| batch | year | focus | delivery | notes |
|---|---|---|---|---|
| B1 | 2023 | legacy | hybrid | low-volume legacy batch |
| B2 | 2024 | active | hybrid | 2 universities, ~1000 students; BITS BSc + Chaitanya Deemed Univ BTech |
| B3 | 2025 | active | mixed partner | ~17 universities, ~6500 students; broad expansion |
| B4 | 2026 | active | mixed partner | 34+ more universities, ongoing |
| B5 | — | future | mixed partner | — |

Architecture focus: **B2, B3, B4** (B1 supported but must not drive design).

**Branch complexity:** branch names vary by university; not all universities have all branches; different branches can require different container structures. Captured examples: B.Tech CSE · CSE (Full Stack Development) · CSE (AI & ML) · CSE (Data Science) · CSE (Generative AI) · B.Tech AI & Agentic AI · AI & Data Engineering · Computer Science & Quantum Engineering.

**Delivery modes (who teaches BOS-approved curriculum at each partner):**
- **Co-Delivery:** NIAT teaches most, university a smaller portion (e.g. NIAT ~141 of 161 credits). Examples: SGU, CDU, Annamacharya University (B3).
- **Full Delivery:** NIAT teaches all approved courses. Examples: MRV University, Aurora University.
- **Hybrid Delivery:** university runs its own curriculum, NIAT runs a parallel one (university ~1–1.5 days/week, NIAT ~4–4.5 days/week). Examples: NSRIT, Chalapathy University.

**Outcomes:** partner-university B.Tech/B.Sc degree + **Industry-Ready Certificate (IRC)** + placement-readiness support. Skill assessments align to the IRC/placement layer.

**Canonical intake for batch sources** (BOS curriculum + grid-template CSVs are canonical inputs, not runtime state):
```
knowledge/catalog/niat/batches/<batch_id>/
  bos_curriculum_references.csv
  grid_template_references.csv
  README.md
```
Staged in-repo examples: B3 university program-design/package implementation references; B4 grid-template structure references; B4 summary pivots; AICTE category-minimum reference data (`knowledge/catalog/regulations/aicte/`).

### 2.2 Academy

**Category:** `certification_or_upskilling_product` · **Structure:** `academy_certification_structure` · **Container:** `certification_curriculum`
**Default version:** `1.5` · **Focus:** active

**Feature flags:** recorded ✅ · **live ✅** · ai_tutor ❌ · **summary_cheatsheet ✅**

**Delivery:** live session delivery is core to the value proposition (live + recorded).

**Audience:** mature upskilling audience (no dedicated audience source file yet).

**Packaging:** standard `default_learning_packaging` (see §4) — no product-specific overrides.

**Versions:**

| version | timeline | focus | delivery |
|---|---|---|---|
| 1.0 | ~2020 | legacy | (recorded) |
| **1.5** | learners from Nov 2025 onward | active | live_plus_recorded |
| 2.0 | planned, NOT launched in this snapshot | planned | live_plus_recorded |

Architecture focus: 1.5 and 2.0; 1.0 legacy-supported.

### 2.3 Intensive

**Category:** `certification_or_upskilling_product` · **Structure:** `standard_product_structure` · **Container:** `standard_curriculum`
**Default version:** `Offline` · **Focus:** active

**Feature flags:**

| flag | product default | Offline version overlay |
|---|---|---|
| recorded_videos_included | ✅ | ✅ |
| live_sessions_included | ❌ | ✅ **true** |
| ai_tutor_enabled | ❌ | ❌ |
| summary_cheatsheet_required | ✅ | ✅ |

**Delivery:** exists in online and offline forms. **Offline = `offline_plus_recorded`** — the primary current design focus (associated with Nov 2025). Structure must still support the earlier online versions.

**Audience:** mature upskilling audience (no dedicated audience source file yet).

**Packaging:** standard `default_learning_packaging` — no product overrides.

**Versions:** 1.0 (2019, legacy, online) · 2.0 (2021, legacy, online) · 3.0 (2023, legacy, online) · **Offline (Nov 2025, active, offline_plus_recorded + live)**.

### 2.4 GRIT

**Category:** `certification_or_upskilling_product` · **Structure:** `standard_product_structure` · **Container:** `standard_curriculum`
**Focus:** future · no versions modeled yet

**Feature flags:** recorded ✅ · live ❌ · ai_tutor ❌ · summary_cheatsheet ❌

**Status:** known product family; detailed versioning and delivery metadata still pending.

### 2.5 Launchpad

**Category:** `certification_or_upskilling_product` · **Structure:** `standard_product_structure` · **Container:** `standard_curriculum`
**Focus:** deferred · **Variant strategy:** `audience_specific_course_variants`

**Feature flags:** recorded ✅ · live ✅ · ai_tutor ❌ · summary_cheatsheet ✅

**Status:** intentionally deferred from the first implementation slice.
**Key modeling note:** Launchpad likely needs true **product-specific course variants**, not just packaging changes — its (top-tier) target audience differs enough that the same broad course name may need a different course variant than NIAT's.

### 2.6 default (fallback)

**Category:** `standard_product` · **Structure:** `standard_product_structure` · **Container:** `standard_curriculum` · **Focus:** default

**Feature flags:** all ❌ (recorded, live, ai_tutor, cheatsheet)

**Purpose:** stack-only fallback when no explicit product is selected. Every real product manifest deep-merges over this. Keep for back-compat, tests, and generic exploration; real curriculum-design runs should pass an explicit product.

### 2.7 Future product families (accounted for in architecture, not yet modeled)

Launchpad · MINT · Makers Conclave · Partnership Workshops · Govt Workshops · Master Classes · Youtube Series · Content Branding Pipeline · BITS Product · Employee Workshops.

---

## 3. Structure profiles (inlined)

### 3.1 `standard_product_structure` (Academy-style default for Intensive/GRIT/Launchpad/default)

- Container kind: `standard_curriculum`
- Hierarchy: `curriculum_container → courses → modules → topics → learning_units`
- Design-priority dimensions: job_placement_outcomes · student_learning_outcomes · cross_product_alignment · market_and_community_signals · internal_expertise
- Note: default structure for standard upskilling and product-led curriculum containers.

### 3.2 `academy_certification_structure` (Academy)

- Container kind: `certification_curriculum`
- Hierarchy: `certification_curriculum → course_requirements → course_package_parts → modules → topics → learning_units`
- Design-priority dimensions: job_placement_outcomes · student_learning_outcomes · cross_product_alignment · industry_partnerships_and_certifications · customer_and_sales_intelligence · internal_expertise
- Notes: supports mandatory and optional course requirements inside certification-linked curricula; course completion and certification attempt remain separate policies.

### 3.3 `niat_university_structure` (NIAT)

- Container kind: `academic_degree_curriculum`
- Hierarchy: `batch_curriculum_grid_template → university → branch → bos_curriculum_reference → implementation_curriculum → courses → modules → topics → learning_units`
- Design-priority dimensions: regulatory_compliance · university_policy_and_infra_constraints · degree_and_higher_ed_outcomes · job_placement_outcomes · student_learning_outcomes · operational_efficiency · cross_product_alignment · internal_expertise
- Notes: supports batch/university/branch overlays above the implementation curriculum; BOS alignment and implementation drift must remain visible during curriculum design.

---

## 4. Packaging manifests (inlined)

### 4.1 Global default (`default_learning_packaging`)

- Modules/course: default 3 (min 2, max 5), target ~8h/module
- Topics/module: default 4 (min 2, max 6)
- Learning units/topic: 3
- Allowed unit types: video_session_unit, reading_material_unit, mcq_practice_unit, coding_practice_unit
- Preferred mix: video_session_unit, reading_material_unit, mcq_practice_unit
- Module phase labels: Foundations → Core workflow → Practice and integration → Assessment readiness
- Topic phase labels: Motivation and framing → Core concepts → Worked practice → Checkpoint and recap
- Classroom quiz every **20 minutes** · module quiz **required**
- Skill assessment every **8 topics**; question types mcq/coding/fib/project; difficulty easy/medium/hard

### 4.2 GenAI stack fallback (`genai_stack_packaging`)

- Modules/course: default 3 (min 2, max 4, ~8h) · Topics/module: default 4 (min 3, max 5)
- Preferred mix: video_session_unit, reading_material_unit, **coding_practice_unit**
- Topic phase labels: **Problem framing → Architecture and concepts → Guided build → Checkpoint and quiz**
- Skill assessment types: mcq/coding/fib/project
- Notes: GenAI delivery retains concept framing, architecture reasoning, and build checkpoints in the same course flow; external GenAI skill assessments should expect project and coding evidence alongside conceptual checks.

(NIAT layers its own packaging on top of these — see §2.1.)

---

## Appendix A — NIAT Target Audience Profile (full source content, inlined)

**Product:** family NIAT ("NxtWave Innovation of Advanced Technologies"); current operational focus B2, B3, B4.

**Primary target audience:** post-12th students enrolled in partner universities through the NIAT model. This is not a generic upskilling audience. It is an academic-degree audience that: expects a full-time college-like experience; is early in its formal technical journey; needs structured progression over multiple academic years; requires both degree-oriented and industry-readiness outcomes.

**Delivery context:** primary mode is offline campus delivery; a learning portal still provides recorded assets and learning materials digitally; learning environment is smart classrooms, hostel and campus setting, college-style timetable.

**Learning orientation:** industry-aligned, project-based learning journey. Expectation is not only concept coverage but strong hands-on practice, project-based progression, readiness for degree assessments, and readiness for industry certification and placement preparation.

**Broad academic progression:** Years 1–2 foundations, MERN/full-stack build work, early projects; Year 2 DSA and competitive coding emphasis increases; Year 3 specialization depth (software engineering or AI/ML tracks); Year 4 capstone projects and interview preparation become central.

**Program characteristics:** branch structure varies by university; university naming and branch naming can differ; not all universities have all branches; curriculum structure can differ by branch and university.

**Branch examples captured so far:** B.Tech CSE; CSE (Full Stack Development); CSE (AI & ML); CSE (Data Science); CSE (Generative AI); B.Tech AI & Agentic AI; B.Tech AI & Data Engineering; B.Tech Computer Science & Quantum Engineering.

**Outcome expectations:** university degree outcome; industry-readiness orientation; support toward placement preparation; exposure to modern AI, cloud, automation, and software engineering workflows.

**Audience notes:** materially different from mature upskilling audiences (Academy, Intensive) and from top-tier Launchpad-style audiences (where some courses may need different variants). NIAT target-audience modeling should later become batch-aware, university-aware, and branch-aware.

---

## Provenance (for maintainers; all content above is inlined)

Repo sources this document was derived from: `knowledge/manifests/products/{default,niat,academy,intensive,grit,launchpad}.yaml`, `knowledge/manifests/structure_profiles/*.yaml`, `knowledge/manifests/packaging/{default,genai}.yaml`, `knowledge/sources/products/niat/target_audience/niat_target_audience_profile.md`, `docs/architecture/product_catalog.md`, `src/open_acp/config/curriculum_context.py`.
