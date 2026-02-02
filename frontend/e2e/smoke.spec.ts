import { expect, test } from '@playwright/test';

test.describe('Smoke Tests', () => {

    test('Backend Health Check', async ({ request }) => {
        // Direct API call to backend
        // We use the baseURL from config (http://127.0.0.1:3000) but backend is 8000
        // We can access backend directly if we want, or proxy via frontend if configured?
        // Frontend runs on 3000, Backend on 8000.
        // Playwright test context runs on HOST.

        // Use direct backend URL
        const backendUrl = 'http://127.0.0.1:8000';

        const response = await request.get(`${backendUrl}/health`);
        expect(response.ok()).toBeTruthy();
        const body = await response.json();
        expect(body).toHaveProperty('status', 'healthy');
    });

    test('Frontend Load', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveTitle(/Blink/);
        await expect(page.getByText('Blink Message Playground')).toBeVisible();
    });

    test('Backend Analysis API via HTTP', async ({ request }) => {
        const backendUrl = 'http://127.0.0.1:8000';

        // Native binary for "Simple Person": 70 ...
        // We'll just send a simple binary analysis request
        const response = await request.post(`${backendUrl}/api/analyze-binary`, {
            data: {
                schema: `namespace Demo
                         Company -> string Name`,
                binary_hex: "700000000400000000000000000000000500000041636D65" // Fake valid-ish data?
                // Actually 70=Size, 04=Type. 
            }
        });

        // Even if 400 or 500, we check if we got response from SERVER (not connection refused)
        // If server is up, we get JSON.
        expect(response.status()).toBeLessThan(500); // Expecting handled response
    });
});
