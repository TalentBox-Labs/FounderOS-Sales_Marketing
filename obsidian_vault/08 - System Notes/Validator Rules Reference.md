---
tags: [system, validators, reference]
created: 2026-06-11
---

# ✅ Validator Rules Reference

Full spec of every gate the CMS pipeline runs automatically.

## research_mapper
**File**: `src/tools/research_mapper.py`  
**Reads**: `research_path`, `seo_plan_path`  
Checks research file contains required platform terms.  
Checks SEO plan contains required keyword terms and at least one approved CTA.  
→ See: [[SEO Framework]]

## draft_validator
**File**: `src/tools/draft_validator.py`  
**Reads**: `draft_path`  
**Modes**:
- `template` — checks for required heading sections in the CMS template shell
- `article` — checks H1, FAQ, word count ≥ `draft_article_min_words`
→ See: [[Brand Voice Guide]] for banned phrases list

## structure_checker
**File**: `src/tools/structure_checker.py`  
**Reads**: `final_path`  
Checks final article for: H1, H2s, FAQ section, no banned phrases.

## metadata_checker
**File**: `src/tools/metadata_checker.py`  
**Reads**: `final_path`  
Validates YAML front matter keys:
→ See: [[Final Front Matter Schema]]

## publish_checklist_checker
**File**: `src/tools/publish_checklist_checker.py`  
**Reads**: `09_Publish_Checklist.md`  
Required sections: `# Content QA`, `# SEO QA`, `# Brand QA`, `# Technical QA`, `# Final Approval`

## Related
- [[QA Failure Patterns]]
- [[Content Pipeline Overview]]
