# Tier 1 live-ready without external integrations

Use when Kevin wants an agent "as live as possible" **without** SimpleLTC/API, Power BI, login redesign, or further bot rewrites.

## Definition

| Tier | Meaning | Needs |
|------|---------|-------|
| **1 — Coaching live** | Users chat; paste rates/notes; get structured advisory output | Publish clean + channels + Pattern L brain + paste SOP + audience |
| **2 — Operational live** | Auto data + dashboard + real handoff | SimpleLTC/export path, PBI surface, escalate queue, optional Prod ALM |
| **3 — Fleet product** | Multi-agent record_id routing + audit log | Connected agents healthy, shared contracts |

Do **not** block Tier 1 on Tier 2/3 work.

## Read-only gates (no agent PATCH)

1. `statecode=0`, last publish `Succeeded`, `diagnosticDetails` empty  
2. `provisioningStatus=Provisioned`, sync state healthy  
3. Channels present for intended entry (Teams and/or M365 Copilot)  
4. Auth mode understood (Integrated=2 common) — app registration in tenant if Integrated  
5. Core leaves: SASC + FullResponse + SendActivity `=Topic.Answer` + EndDialog  
6. Conversation Start: welcome + EndDialog when customized  
7. Fallback not apology-only  
8. Eval baseline recorded if available (SR/Conv averages)

## Operator checklist (distribution only)

- Pilot security group / who can open the agent  
- Pin in correct Teams  
- One-page paste format + PHI rules (no DOB/MRN)  
- Channel blurb: Dashboard/PBI is separate if not in-bot  

## QM Coach example (2026-07-17)

- Bot `ea52ad9c…` — Teams + M365 Copilot; SR ~94.5% / Conv ~94.8%  
- Pack: `Pacific-Coast-Therapy-Hub/QMCOACH_LIVE_READY_NO_INTEGRATIONS.md`  
- Skill: `copilot-studio-qm-coach-v2` §Tier 1  

## Anti-patterns

- Rewriting topics "for live" when only distribution is missing  
- Claiming not live solely because SimpleLTC/PBI are unwired when coaching mode works  
