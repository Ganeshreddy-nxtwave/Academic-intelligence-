# Open ACP — Platform Student Experience & Data↔UI Mapping (Python Course)

> **Living handoff document.** Captures how the NIAT learning platform actually presents the
> "Computer Programming using Python" course to students (from product screenshots,
> 2026-07-06/07) and how the question/content export maps onto that UI. Purpose, per the
> Forge program: (1) ground Forge's **reviewer UI/UX** proposals, (2) design the **student
> adaptivity experience** that replaces static practice units, (3) serve as the baseline for
> **learner-behaviour analysis** when student-facing stats arrive (→ product-context updates).
>
> **Status:** UX fully captured; ALL 16 open questions answered by the platform owner
> (2026-07-07) — answers folded in below. PENDING: re-export of all questions WITH difficulty
> tags + tutorials + explanations; learner stats. Version 4 — 2026-07-07.

---

## 1. Naming map (one thing, three names)

| context | name |
|---|---|
| Student UI + export `course_title` | **Programming Foundations** |
| Course Outline CSV | Computer Programming Using Python |
| Central Stack Catalogue | Computer Programming using Python (stack: Programming & Algorithms) |

UI vocabulary: a **Topic = a session** (the outline's Session No./Name). The export's
`topic_id`/`topic_name` confirm this (e.g. topic_name "Sequence of Instructions").

## 2. Curriculum hierarchy as the student sees it (NIAT product)

```
Year (Year 1 unlocked: 19 subjects · Year 2 locked, 0 subjects)
  └─ Subject (e.g. "Computer Programming", "Web Application Development -2", "Probability & Statistics")
       └─ Course (subject card shows count, e.g. Computer Programming → Course: 1 → "Programming Foundations")
            └─ Topic (= session; course panel shows "Topics: 32", per-topic progress ring %)
                 └─ Units (ordered, each with a completion tick)
```

- Course panel shows overall course progress % (e.g. 7%) and per-topic progress (22%, 15%).
- Observed subject list (Year 1) includes: Web Application Development -2, Introduction to
  NIAT, Introduction to Computing Systems, Probability & Statistics, Communicative English
  Advanced/Foundation, Computer Programming, Numerical Ability, Quantitative Aptitude.
- Sidebar module groupings in the course differ slightly from the outline CSV's module names
  (e.g. UI "Logical Operators & Conditional Statements" spans CSV modules "Operators" +
  "Conditional Statements").
- Topics count: **32 sessions is authoritative** (owner-confirmed); the portal's "34" is a
  different grouping — treat the JSON/outline as truth.

## 3. Unit sequence within a topic (observed)

```
Video Session  →  Reading Material (labeled "Cheat Sheet")  →  Classroom Quiz A  →
Classroom Quiz B  →  [Classroom Quiz C when present]  →  MCQ Practice  →  Coding Practice
…and at module end: Module Quiz - N
```

- Every unit has a completion tick; Reading Material shows a green filled tick when done.
- **Module Quiz units** are absent from the question export; CONFIRMED they are a
  **repurposed mix of existing classroom-quiz + coding questions** (not an authored separate
  bank) — do not mine them; JSON arriving for context only.

## 4. Coding Practice unit — list view

Table columns: **QUESTION | DIFFICULTY | TESTCASES PASSED | SCORE | STATUS** (+ open arrow).
- Question shows `short_text` (e.g. "Product of 37, 61 and 391").
- DIFFICULTY chip (Easy/…) — not in the current export; **a re-export with difficulty tags (+ tutorials + explanations) is incoming**.
- SCORE denominator = sum of the item's test-case `weightage` (e.g. –/5).
- STATUS: NOT ATTEMPTED / In Progress / etc.
- Current unit size: 2 questions in the observed session (Sequence of Instructions) — the
  static units Forge's adaptive unit replaces.

## 5. Coding workspace (per question)

Layout: left panel (tabs **Description | Submissions | Tutorial**) · center editor
(**Python 3.10**, timer icon, save/settings/format/reset/fullscreen) with **Run** / **Submit**
and a bug-icon **visual debugger** · bottom **Testcase panel** · right **AI Tutor** panel.

- **Description tab:** title + status chip (In Progress) + difficulty chip + stem; **Sample
  Input / Sample Output are rendered from the visible test case(s)** (input "" → empty Sample
  Input; output 882487). Bookmark, Helpful, Give Feedback affordances.
- **Testcase panel:** shows Case 1…n (the visible cases); students can **add custom cases**
  (+, Input/Output fields, UPDATE). After a run: per-case verdict ("Wrong Answer"), **Your
  Output vs Expected side-by-side with a Diff toggle**.
- **Submissions tab:** *Your Submissions* and **Public Submissions** toggles; per submission:
  status, N/M testcases passed, language ("Python 3.10"), runtime, timestamp, view/open
  actions; failed-case detail with Input / Output (red) / Expected Output (green) and "Use
  Testcase" (copies the case into the panel).
- **Tutorial tab (per question):** a step-by-step worked solution ("Step 1: Understand the
  problem → Step 2: Write the program (PYTHON-pill code block, built incrementally) → Step 3:
  Show the result"), with a **Completed** tick. Coming in the re-export; **CONFIRMED: Forge
  must emit a tutorial with every coding item** (part of the item contract).
- **Visual debugger:** step-through execution — "Line that just executed" / "Next line to
  execute" arrows, step slider, FIRST/PREV/NEXT/LAST, **Scopes / Objects** inspector panes,
  custom Input/Output, "EDIT THIS CODE", "Learn How To Debug" video link. (Pairs with the
  course's s7 "How to debug your code?" session.)
- **AI Tutor:** right-side chat panel, greets the student by name, **Chat + Voice** modes,
  "Set as default" toggle, floating "Do you need any help?" nudge.
  ✅ CONFIRMED: AI Tutor is live for ALL questions, enabled at course level; the manifest was
  stale and has been updated (`ai_tutor_enabled: true` in niat.yaml + products handoff doc).

## 6. Objective practice player (MCQ Practice unit)

Full-screen player, one question at a time. Header: back arrow + "MCQ PRACTICE" + PRACTICE
INSTRUCTIONS link · center **SCORE: N** · right **QUESTIONS ATTEMPTED: N/15** + **END
PRACTICE** (always available).

- **Layout:** question panel LEFT (stem + response control + SUBMIT/SKIP), **read-only code
  pane RIGHT** (the same dark editor component as the coding workspace).
- **Response modes observed:** TEXTUAL = free-text "Enter your answer" box (typed production);
  MCQ = radio-button option list (3 options observed — option count varies by item).
- **Flow per question:** SUBMIT → immediate verdict. Correct: green tick on the answer +
  **"+1"** feedback card. Wrong: red ✗ + **"0"** card **and the correct answer is revealed**
  (student's wrong answer shown red, correct shown green beneath). Then **Show Explanation**
  (optional) → **NEXT**. No retry of the same item once answered.
- **Explanation modal** ("EXPLANATION FOR ANSWER", draggable): PYTHON-pill code block with
  **inline `#` comments** + bullet-point walkthrough of the logic and outcome. Every objective
  item appears to have one. Coming in the re-export (**not all items may have one**);
  **CONFIRMED: Forge must emit an explanation with every objective item**.
- **SKIP** is gated by a countdown ("You can skip this question after 1/3 Seconds") and —
  per the on-screen note on conceptual items — **"If you skip, you can attempt this question
  again after finishing all questions"**: skipped items REQUEUE at the end of the run. Skip is
  deferral, not abandonment (a run can still end with Unanswered > 0 via END PRACTICE).
- **Run length:** the player samples 15 from the unit pool based on **legacy tagging
  implemented years back — owner says NEGLECT it**; the adaptive delivery replaces this
  sampler entirely.
- **TEXTUAL grading exactness visible in-product:** the revealed correct answer for
  `print(10 / (2 + 3))` is **`2.0`** — float `.0` precision is answer-bearing, matching the
  corpus finding that format precision is itself a tested fact.
- ⚠ **Lint-marker leak:** the read-only code pane shows editor error markers (red ✗ gutter on
  `print(age)` before `age = 10`) — for error-prediction items the editor itself hints the
  answer. Forge/delivery should render error-item code with linting disabled.

- **Difference checker (TEXTUAL wrong answers):** bottom panel "Difference checker" with
  On/Off toggle — Your Answer (strikethrough) vs Actual Answer side-by-side, same diff
  affordance as the coding workspace.
- **Two layouts:** code-based items render split-pane (question left, read-only code pane
  right); **conceptual no-code items render as a centered full-width card** (BODMAS-style
  text questions) — the player adapts layout per item.
- **Lint-marker leak confirmed twice:** `c = b + c` (NameError line) also shows the red ✗
  gutter marker — on an item whose correct option is literally that NameError.
- **Run summary modal (after 15/15):** date + duration (e.g. 3MIN20SECS), score gauge
  **N/15** with **PASS SCORE = 11** (≈73%) and **FAILED/PASSED** state, breakdown (✓ correct,
  ✗ wrong, • unanswered), **REVIEW ATTEMPT** (post-run review), **PRACTICE AGAIN** (full
  retake) and **PROCEED TO NEXT** (available even on FAILED), plus a motivational nudge
  ("You can do way better! Why don't you revise the concepts and practice once again?").
- ⚠ **Production evidence for the verdict layer:** the live run served the BODMAS
  letter-mapping item (a/b/c → "b, a, c" orderings) — an item the question-intelligence doc's
  DROP list flags as conflating the mnemonic with Python precedence in a confusing format.
  The old bank's defects are in front of students today.

Three design consequences for the adaptive bank:
1. **Answer-reveal burns items** — once a student answers (right or wrong) the item is spent;
   retry/step-down needs *fresh variants*, which sets the ≥3-variants-per-cell pool depth.
2. **Per-item explanations are part of the item contract** — Forge should generate the
   explanation (code-with-comments + bullets) alongside each objective item, in this format.
3. **Skip is a first-class outcome** — the adaptive walk needs a policy for skipped items
   (no evidence ≠ wrong).

## 7. Completion rules (the rules adaptivity replaces)

- Unit-level `instructions` (export) carry student-facing rules. Observed MCQ Practice:
  "Number of Questions: 30 · Types: MCQs · Marking: equal weightage, +1 per correct, no
  negative marking · **You must answer all the MCQs correctly in order to mark your practice
  as completed.**"
- **CONFIRMED completion rules (platform owner):** MCQ Practice unit = **80% of questions
  answered correctly** marks complete; Coding Practice unit = **80% of questions with all
  test cases passed** marks complete. (One observed run showed PASS SCORE 11/15 ≈ 73% —
  per-unit rounding/legacy variance; treat 80% as the policy.) The instructions text
  ("answer all correctly") overstates the actual bar.
- The Forge thread's note stands: the "answer all correctly" completion rule has **no adaptive
  analog yet**; the adaptive unit needs its own completion/mastery rule, owned by the
  delivery scope.

## 8. Export ↔ UI mapping (what the JSON actually is)

The export (`question_details_json_with_coding_question_content.json`) = **188 units**:
127 question units + **61 learning-resource units** (Reading Material + Video Session):

| export structure | UI meaning |
|---|---|
| `content_data.title` / `description` | unit name shown in the topic's unit list |
| `content_data.instructions` (JSON string) | the unit's student-facing rules dialog (counts, marking, completion rule) |
| `content_data.total_max_score` | unit score cap (e.g. Coding Practice 10.0 = 2 × 5) |
| `content_data.content_type: 'CODING'` (38 units) | Coding Practice units |
| `content_data.question_set_id` | = unit_id for question units |
| `question_details[].short_text` | question title in the unit's list view (CODING only) |
| `question_details[].test_cases` (is_hidden=false) | Description tab's Sample Input/Output + Testcase panel visible cases |
| `test_cases[].weightage` | per-case marks; sum = SCORE denominator |
| `question_guiding_questions` (rounds of TEXTUAL predict-output Qs with answers + explanations) | pre/while-coding comprehension scaffold (51 CODING items; placement in UI TBC) |
| `learning_resource_details[].content` (MARKDOWN) | Reading Material page content |
| `learning_resource_details[].tutorials_data[]` (content + `order`) | Reading Material **sections**, ordered — this is the `order` key's home in this export |
| `learning_resource_details[].learning_resource_type: 'INTERACTIVE_VIDEO'` + `multimedia_details[]` (video url, `transcript_url`, language 'en') | Video Session units (+ transcripts; `question_set_ids` mostly empty in export) |

**Confirmed absent from this export** (live elsewhere): per-question **difficulty**, coding
question **display order**, **Module Quiz** banks, the per-question **Tutorial** content,
public-submission data, objective answer-**explanations**, any learner telemetry. Question-level `multimedia` and unit
`extra_details` are present as keys but empty corpus-wide.

## 9. Questions — ANSWERED (platform owner, 2026-07-07)

| # | question | answer |
|---|---|---|
| 1 | Difficulty source | Re-export incoming with difficulty tagged on all questions |
| 2 | Coding-question order | **Array position** in the export |
| 3 | Tutorial tab content | In the re-export; **Forge must generate tutorials too** |
| 4 | Module Quiz bank | **Repurposed mix of classroom-quiz + coding questions** — do NOT treat as a separate bank; JSON will be provided but is repurposed content |
| 5 | Runtime | **Emit everything as Python 3.10** |
| 6 | Classroom Quiz A/B/C | **Delivered live in class when the quiz slide pops up** (maps to the decks' "Quiz Time!" slides) |
| 7 | Grading | CODING: **trailing-whitespace/newline tolerant confirmed** · FIB: **exact string match** · TEXTUAL: **not exact-match** (normalization applied; details unspecified) |
| 8 | Coding completion | **80% of questions with all test cases passed** |
| 9 | Public Submissions | **Yes** — students can browse others' solutions (novelty/rebuild cadence is a real constraint) |
| 10 | Run vs Submit | Confirmed: Run = visible + custom; Submit = full suite incl. hidden |
| 11 | Topics 34 vs 32 | **32 sessions is the truth**; the portal groups differently; treat the JSON as authoritative |
| 12 | AI Tutor | **Live for all questions, enabled at course level**; manifest was stale (now fixed) |
| 13 | Objective explanations | In the re-export (**not all items have one**); Forge must emit them |
| 14 | 15-of-30 sampling | Legacy tagging from years back — **neglect**; adaptive delivery replaces the sampler |
| 15 | Lint markers | Ideally yes but **the editor doesn't support disabling lint** (long-standing ask to the portal team) — treat as a delivery constraint |
| 16 | Completion tick | **80% correct** marks complete |

**Design consequences locked by these answers:**
- FIB **exact string match** makes the uniqueness/canonicalization gate (C04) non-negotiable:
  ~1 in 4 legacy blanks would mark a *correct* student answer wrong. New FIB items must be
  closed-vocabulary-token blanks or ship a canonical single-string answer by construction.
- **Public submissions leak solutions** → fresh-bank novelty constraint is real; variant
  generation + periodic rebuild is the mitigation (as the Forge thread assumed).
- **Lint leak cannot be fixed platform-side for now** → generation-side mitigation: avoid
  statically-lintable bugs (undefined-name style) as the ANSWER of error-prediction items
  delivered in the current player; prefer runtime-only errors (type errors on valid names,
  value errors) until the editor supports per-item lint control.
- The legacy 15-question sampler and the 80% rule are exactly what the adaptive walk replaces.

## 10. Pending additions

- Re-export: all questions with difficulty tags + tutorials + explanations (incoming).
- Module-quiz JSON (repurposed content — context only, not a bank to mine).
- Forge reviewer UI/UX proposal + student adaptivity experience proposal (to be drafted once
  the objective UX and the open questions above are settled).
- Learner-behaviour stats → per-product analysis → product-context updates.
