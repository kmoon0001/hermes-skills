/**
 * Test script for the generic‑retry‑http helper.
 * This script is NOT meant to be run in a flow – it simply demonstrates the
 * payload shape you would pass from Power Automate.
 */

export async function main(workbook: ExcelScript.Workbook, _: string): Promise<string> {
    // Example payload – a real flow would supply this as the third parameter.
    const payload = {
        url: "https://httpstat.us/503", // will fail → retries then throw
        method: "GET",
        headers: {},
        body: {},
        maxAttempts: 3,
        initialDelayMs: 1000
    };
    // Call the reusable script (import style not supported in Office Scripts).
    // Instead we inline the retry logic – see generic-retry-http.ts for the real impl.
    // For a quick demo we just return the JSON string so you can see it in the flow.
    return JSON.stringify(payload);
}
