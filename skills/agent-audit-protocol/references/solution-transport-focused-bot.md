# Focused bot transport (PCCA → Therapy AI Dev)

`copilot-studio-agent-solution-migration` is **pinned** — keep operational detail here until unpinned.

## Doc Defense validated 2026-07-16 (Pacific)
| | |
|--|--|
| Source | `https://pccapackage.crm.dynamics.com/` bot `9e7b871d-1d80-f111-ab0f-000d3a5b0d6c` |
| Target | `https://orgbd048f00.crm.dynamics.com/` bot **`2e08ac68-bdef-481e-9c04-6a349c79d6c0`** (new id) |
| Solution | `DocDefenseTransport` unmanaged + required components |
| Zip | `C:/Users/kevin/Desktop/docdef_migrate/DocDefenseTransport.zip` |

```bash
pac solution add-solution-component -env https://pccapackage.crm.dynamics.com/ \
  -sn DocDefenseTransport -c 9e7b871d-1d80-f111-ab0f-000d3a5b0d6c -ct bot -arc
pac solution export -env https://pccapackage.crm.dynamics.com/ \
  -n DocDefenseTransport -p C:/Users/kevin/Desktop/docdef_migrate/DocDefenseTransport.zip --overwrite --managed false
pac solution import -env https://orgbd048f00.crm.dynamics.com/ \
  -p C:/Users/kevin/Desktop/docdef_migrate/DocDefenseTransport.zip --publish-changes --force-overwrite
# fetch NEW botid on target, then:
pac copilot publish -env https://orgbd048f00.crm.dynamics.com/ -b 2e08ac68-bdef-481e-9c04-6a349c79d6c0
```

Import does not heal defects. Run agent-audit-protocol next (expect Fallback no SASC, missing RCT, GPT55Chat, empty RI). Use Pattern J for Fallback. Report times in Pacific local.