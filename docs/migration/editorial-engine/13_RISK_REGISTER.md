# E6A — Risk Register

| ID | Risk | Evidence | Impact | Likelihood | Severity | Mitigation | Rollback |
|----|------|----------|--------|------------|----------|------------|----------|
| R1 | Re-migrate CMS `reference-design` crews → duplicate Editorial Engine | CMS ref ≈ Founder `editor_crew`/`qa_crew`/validators | Dual prompts, drift | Medium if ignored | **BLOCKER** (if attempted) | Classify SUPERSEDED; KEEP FOUNDER | Delete mistaken ports |
| R2 | Adopt OpenClaw as Founder editorial runtime | CMS SOUL agents depend on OpenClaw | Platform coupling, non-canonical | Medium historically | **BLOCKER** (if attempted) | OUT OF SCOPE; ADAPT prompts only | Remove OpenClaw wiring |
| R3 | Sheets as editorial SoT | CMS Sheets stages/QA columns | Second SoT vs tracker | High if CMS UX copied blindly | **BLOCKER** (if attempted) | RETIRE Sheets SoT; tracker canonical | Revert Sheets writes |
| R4 | Broken `/edit` `/generate` treated as working Editorial API | `pipeline.py` omits staging args | Operator false confidence; failed runs | High | HIGH | Fix in later unit or document; prefer readiness read first | Revert API change |
| R5 | Prompt conflict merging SOUL + YAML blindly | Different agent systems | Tone/contract breakage | Medium | HIGH | ADAPT via ADR; no prompt edit in E6A | Restore YAML |
| R6 | Automatic mutation / publish leakage | `/run` updates tracker; go-live separate | Premature “approved” semantics | Medium | HIGH | Approval ADR; first unit read-only | Revert mutations |
| R7 | Brand ownership duplication | Vault guide + CMS voice.md + validators | Conflicting brand SoT | Medium | MEDIUM | Brand Engine owns definition | Revert merge |
| R8 | SEO ownership duplication | SEO agent vs editorial validators | Strategy vs validate confusion | Low | MEDIUM | Keep boundary doc | — |
| R9 | Dead UI `/qa` `/sheet-sync` | templates reference missing routes | UX lies | High | MEDIUM | Fix/remove in UI hygiene sprint | Revert template |
| R10 | content_quality not in default/promote | 2c-only | Quality gap vs CMS scorecards | Medium | MEDIUM | DEFER wiring with tests | Revert validator list |
| R11 | Approval semantics undefined across promote vs CMS stages | E6A §09 | Wrong lifecycle if merged | Medium | HIGH → **ADR REQUIRED** | ADR before stage import | — |
| R12 | Legacy `src/crew.py` confusion | Parallel QA entry | Wrong module called | Low | LOW | DEFER retire | — |

### Blocking risks (severity BLOCKER if path attempted)

**Count: 3** — R1, R2, R3.

These block **wrong** migration approaches; they do **not** block a Founder-native read-only first unit that avoids CMS runtime/Sheets/ref-design copy.
