# Retrieving Original Agent Instructions

To retrieve the original instructions (componenttype 15) for a deployed Copilot Studio agent:

1. Ensure Google Chrome is running with remote debugging enabled on port 9223:
   ```bash
   start chrome --remote-debugging-port=9223 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data"
   ```

2. Run the live agent dump script to extract the agent's components:
   ```bash
   node "D:/my agents copilot studio/pipeline/scripts/dump_live_components.cjs"
   ```
   This will create JSON files in `D:/my agents copilot studio/pipeline/live_agent_dump/`.

3. Locate the file for the target agent (e.g., `TDA_components_response.json`) and extract the `data` field from the component with `componenttype` 15. This contains the original instructions in YAML format.

4. To restore the original instructions, use a similar PATCH script (see `scripts/restore_tda_original.js` as an example) that sends a PATCH request to the Dataverse API to set the `data` field back to the original value.

Note: Always backup the current state before making changes.