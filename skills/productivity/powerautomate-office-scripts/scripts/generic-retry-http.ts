import { retry } from '../../../../../OneDrive/OfficeScripts/snippets/retry';

/**
 * Example generic Office Script that performs an HTTP POST with retry logic.
 * The script expects a JSON payload string as the `payload` parameter.
 */
export async function main(workbook: ExcelScript.Workbook, payload: string): Promise<string> {
    const data = JSON.parse(payload);
    const result = await retry(async () => {
        const response = await fetch(data.url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(data.headers || {}),
            },
            body: JSON.stringify(data.body),
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const json = await response.json();
        return JSON.stringify({ result: json });
    }, data.maxAttempts ?? 4, data.initialDelayMs ?? 1500);
    return result;
}
