/* --------------------------------------------------------------
   Office Script: generic-retry-http
   --------------------------------------------------------------
   Purpose:
   • Accept a JSON payload describing an HTTP request.
   • Execute the request with exponential-back-off retries.
   • Return the successful JSON response (or throw after max attempts).

   Expected payload shape (stringified JSON passed to `payload`):
   {
     "url": "https://api.example.com/endpoint",
     "method": "POST",                 // optional – defaults to POST
     "headers": { "Authorization": "..." },
     "body": { "foo": "bar" },         // any JSON-serialisable object
     "maxAttempts": 4,                 // optional – defaults to 4
     "initialDelayMs": 1500            // optional – defaults to 1500
   }

   NOTE: Office Scripts do NOT support `import`. The retry helper is
   embedded below so this script is fully self-contained.
   -------------------------------------------------------------- */

export async function main(
    workbook: ExcelScript.Workbook,
    payload: string
): Promise<string> {

    // ---------- 1️⃣ Parse the incoming payload ----------
    const cfg = JSON.parse(payload);
    const url           = cfg.url;
    const method        = cfg.method ?? "POST";
    const headers       = cfg.headers ?? {};
    const body          = cfg.body ?? {};
    const maxAttempts    = cfg.maxAttempts ?? 4;
    const initialDelayMs = cfg.initialDelayMs ?? 1500;

    // ---------- 2️⃣ Embedded retry helper (self-contained) ----------
    async function retry<T>(
        action: () => Promise<T>,
        maxAttempts: number = 3,
        delayMs: number = 2000
    ): Promise<T> {
        let attempt = 0;
        while (true) {
            try {
                return await action();
            } catch (e) {
                attempt++;
                if (attempt >= maxAttempts) {
                    console.log(`❌ Failed after ${attempt} attempts`);
                    throw e;
                }
                console.log(`🔄 Attempt ${attempt} failed – retrying in ${delayMs} ms`);
                await new Promise(r => setTimeout(r, delayMs));
                delayMs *= 2; // exponential back-off
            }
        }
    }

    // ---------- 3️⃣ Run the HTTP request with retry ----------
    const result = await retry<string>(async () => {
        const response = await fetch(url, {
            method,
            headers: {
                "Content-Type": "application/json",
                ...headers,
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const json = await response.json();
        return JSON.stringify({ result: json });
    }, maxAttempts, initialDelayMs);

    // ---------- 4️⃣ Return to the flow ----------
    return result;
}
