// retry.ts – reusable retry helper for Office Scripts
/**
 * Retry‑and‑continue helper for Office Scripts.
 * Wrap any async operation that may fail transiently.
 *
 * @param action      A function returning a Promise – the risky code.
 * @param maxAttempts Maximum attempts (default 3).
 * @param delayMs     Initial back‑off delay in ms (default 2000). Doubles each retry.
 * @returns Resolved value of `action` on success.
 * @throws Last error after exhausting retries.
 */
export async function retry<T>(
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
            console.log(`🔄 Attempt ${attempt} failed – retrying in ${delayMs} ms`);
            await new Promise(r => setTimeout(r, delayMs));
            delayMs *= 2; // exponential back‑off
        }
    }
}
