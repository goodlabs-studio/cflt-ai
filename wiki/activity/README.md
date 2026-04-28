# Activity Log

Append-only audit trail of skill invocations.
One file per calendar month: `YYYY-MM.md`.
Each entry records: skill invoked, overlay active, inputs, outputs, timestamp.

Never edit entries retroactively. Archive (do not delete) files older than 12 months.

## Entry Format

```
## YYYY-MM-DDTHH:MM:SSZ
**Skill:** /{skill-name}
**Overlay:** {base | fsi | customer/{name} | engagement/{name}}
**Input:** {path or description}
**Output:** {path or "none"}
**Canon stack:** {layers active, e.g., "base + fsi"}
```

## Rules

1. Entries are append-only — never modify a past entry
2. The `Overlay` field records which canon overlay layer was active during the invocation
3. One file per calendar month; create `YYYY-MM.md` when the first entry in a new month occurs
4. Files older than 12 months should be archived to `wiki/activity/archive/`, not deleted
5. The `Canon stack` field records all active layers (e.g., "base + fsi + customer/acme")
