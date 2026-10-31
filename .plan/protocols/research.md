---
name: research
description: Research protocol with companion task file and auto isolation in automated runs.
worktree: auto
branch: auto
task_file: true
integration: squash
commit: auto
push: none
cleanup: auto
review: different-agent
preview: none
review_guidance: |
  Audit the research adversarially and reject the work when any check fails:
  - Every [V:<tier>] claim cites a source you opened, and the tier matches the source type.
  - Every [D] figure shows its derivation; recompute the figures behind each conclusion.
  - No [E] figure bears a core conclusion or recommendation, and [E] inputs yield [E] results.
  - Every link resolves; list dead or unverifiable links as defects.
  - Unconfirmed data is recorded as `not found` with the queries tried.
  - The Phase 0 capability declaration is present.
---

# Research Task Execution Protocol

You are executing research task **{{task-id}}**: {{description}}

## Environment
- Working Directory: {{work-dir}}
- Task File: {{task-file}}
- Target Branch: {{branch}}
- Target Worktree: {{worktree}}

## Workflow
1. {{isolation-instructions}}
2. Create and maintain the companion task file at {{task-file}} for progress and findings.
3. Emit a Phase 0 capability declaration disclosing web access, consultable formats, and cutoff dates.
4. Execute research following the bundled `research-guidelines` skill, using standard evidence labels:
   - `[V:<tier>]` **Verified**: Transcribed directly from an opened source, qualified by authority tier:
     - `[V:A]` Tier A: Peer-reviewed papers, regulatory filings, official benchmark releases.
     - `[V:B]` Tier B: Academic preprints, institutional research, formal technical whitepapers.
     - `[V:C]` Tier C: First-party engineering documentation, reputable technical and financial journalism.
     - `[V:D]` Tier D: Commercial vendor blogs, opinion posts, forums, secondary aggregators.
   - `[D]` **Derived**: Mathematically or logically derived from verified inputs, showing intermediate steps.
   - `[E]` **Estimated**: Projections, heuristics, or sources blocked by paywalls or HTTP 403.
   - **Inheritance Rule**: Any derivation containing an `[E]` input yields an `[E]` result.
   - **Decision Rule**: An `[E]` figure must never bear a core conclusion or recommendation.
   - **Explicit Gaps**: Record `not found` with attempted search queries when data cannot be confirmed.
5. Validate all external and internal links to ensure zero dead references or hallucinated URLs.
6. Require at least one critical adversarial review by another agent, preferably from another vendor.
7. Resolve all review remarks and re-audit findings across at most 5 review iterations.
8. If disagreements remain after 5 iterations, summarize contention points and suspend task for human review.
9. {{completion-instruction}}
