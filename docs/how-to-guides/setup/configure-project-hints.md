---
title: Configure project hints
parent: Setup
grand_parent: How-to guides
nav_order: 6
---

# Configure project hints

Project hints are not part of the alpha.15 standalone runtime. The current
template does not ship `.memoria/project-hints.yaml.example`, and ingest does not
read a workspace project-hints file.

Use the implemented path instead:

```bash
memoria work update --workspace <vault> <work-id> --research-area <term>
memoria work update --workspace <vault> <work-id> --topic <term>
```

## Related

- Where source metadata is corrected: [Classify a source](../library/classify-a-source.md)
- Topic vocabulary discipline: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
