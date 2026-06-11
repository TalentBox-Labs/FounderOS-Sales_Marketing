---
tags: [qa, reference, patterns]
created: 2026-06-11
---

# 🚨 QA Failure Patterns

> Running log of recurring validator failures and fixes. Update this whenever a new pattern appears.

## Pattern 1: Missing YAML Front Matter
**Validator**: metadata_checker  
**Symptom**: "No YAML front matter block"  
**Cause**: Editor agent produced final without `---` block  
**Fix**: Re-run editor with explicit YAML FM instruction; check `agents_editor.yaml`

## Pattern 2: FAQ Section Missing
**Validator**: structure_checker / draft_validator  
**Symptom**: "Missing FAQ section"  
**Cause**: Writer skipped or renamed FAQ heading  
**Fix**: Ensure `## Frequently Asked Questions` heading is exact (case-insensitive match)

## Pattern 3: Research Terms Missing
**Validator**: research_mapper  
**Symptom**: "Research missing: ziprecruiter" etc.  
**Cause**: Research file too thin or platform section absent  
**Fix**: Check `03_Research.md` — ensure all required terms appear per research gate config

## Pattern 4: Bracket Placeholders in Final
**Validator**: metadata_checker  
**Symptom**: "Bracket placeholder in `canonical_url`"  
**Cause**: Editor left `[CANONICAL_URL]` unfilled  
**Fix**: Set `WORKCREW_CREWAI_MODEL` to a capable model; check SEO plan has parseable canonical URL

## Pattern 5: Word Count Below Minimum
**Validator**: draft_validator (article mode)  
**Symptom**: "Word count below minimum"  
**Cause**: Draft too short; usually < 900 words  
**Fix**: Increase Writer instructions or re-run with `draft_article_min_words` override

## Related
- [[Validator Rules Reference]]
- [[Content Pipeline Overview]]
