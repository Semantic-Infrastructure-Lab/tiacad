# TiaCAD Backlog

Open action items migrated to `tt` (project-embedded task tracker) on 2026-07-17.
See `TASKS.md` for the live list, or run:

```
tt list                # open items
tt list --area VAL     # validation/testing infrastructure
tt list --area UX      # model-validation UX (docs/developer/MODEL_VALIDATION.md items 2-7)
tt list --area API     # API / language surface
tt list --area ARCH    # architecture debt
```

`ROADMAP.md` still owns the headline strategic track (Constraint Solver Q4 2026,
CGA v5.0 2027+) — `tt` is for everything else. Items move to `CHANGELOG.md` when
shipped (`tt status <id> done --commit <hash>`), not the other way around.
