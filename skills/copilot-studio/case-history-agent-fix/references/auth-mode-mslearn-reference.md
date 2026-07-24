# Auth Mode Investigation — MS Learn References

## Key MS Learn Links
- Configure user authentication: https://learn.microsoft.com/microsoft-copilot-studio/configuration-end-user-authentication
- Authenticate with Azure AD: https://learn.microsoft.com/microsoft-copilot-studio/configuration-authentication-azure-ad
- Add auth to topics: https://learn.microsoft.com/microsoft-copilot-studio/advanced-end-user-authentication
- Admin auth controls: https://learn.microsoft.com/power-platform/admin/security/configure-authentication-controls-for-agents

## ManualAuthenticationInputNotEnabled Error

**Root Cause:** Topics using `SearchSpecificFiles`, `FilePrebuiltEntity`, or SharePoint-based knowledge sources require ManualAuth at the agent level. When `authenticationmode` is set to `None` (0), these features can't authenticate against the backend (SharePoint, OneDrive, etc.) and the publish validator blocks with `ManualAuthenticationInputNotEnabled`.

**MS Learn Documentation States:**
> "When you use SharePoint as the data source in generative answers, you need to configure Manual authentication. Manual authentication is required because it's using the connected end-user's context to run the search (so that it only returns content they have access to)."

> "If a topic uses authentication variables, they become Unknown variables when auth is turned off. Go to the Topics page to see which topics have errors and fix them before publishing."

> "If your agent has tools configured to require user credentials, don't turn off authentication at the agent level. This action prevents these tools from working."

**Resolution Options (in preference order):**
1. **Keep auth at Integrated (2), deactivate Sign-in topic** — if the Sign-in topic is already inactive (statecode=1), the auth gate is mitigated. The platform-level auth mode doesn't block queries in eval.
2. **Remove auth-dependent features from topics** — replace `SearchSpecificFiles` with `SearchAllKnowledgeSources`, remove `FilePrebuiltEntity` nodes, remove SharePoint knowledge sources. Then flip auth to None.
3. **Live with Integrated auth** — eval still works; the auth gate only matters for production users who haven't signed in.

## Practical Impact on Eval Scores
- Auth at Integrated (2) with inactive Sign-in topic: ~0pp impact on SR evals
- Auth at None (0) with no auth-dependent features: theoretical benefit but requires topic surgery
- Auth at Integrated (2) with ACTIVE Sign-in topic: -40+ pp on SR (all queries intercepted by sign-in gate)
