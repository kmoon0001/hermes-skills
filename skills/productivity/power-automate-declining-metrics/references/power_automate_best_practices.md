# Power Automate Best Practices (Weekly Decline Flow)

* **Use a Recurrence trigger with a Fixed time zone** – prevents daylight‑saving surprises.
* **Add a timeout** on long‑running actions (e.g., Get file content) to avoid hanging flows.
* **Configure Run After** on each action to capture failures and send a diagnostic email.
* **Limit data size** – keep the weekly export under 1 MB; otherwise split per‑facility.
* **Idempotent design** – the flow should be safe to re‑run manually without duplicate notifications. Include a *Check if notification already sent* step (store a flag in a SharePoint list).
* **Logging** – write a simple log entry to another SharePoint list (`FlowLogs`) with columns: `RunDate`, `Facility`, `Status`.
* **Testing** – use the *Run flow* button with a test file before scheduling.
