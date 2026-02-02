import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './e2e',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    timeout: 60 * 1000,
    reporter: [['list'], ['html']],
    use: {
        baseURL: 'http://127.0.0.1:3000',
        trace: 'on-first-retry',
    },

    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],

    webServer: [
        {
            command: 'npm start',
            url: 'http://127.0.0.1:3000',
            reuseExistingServer: !process.env.CI,
            timeout: 120 * 1000,
            env: {
                PORT: '3000',
                REACT_APP_API_URL: 'http://127.0.0.1:8000',
                BROWSER: 'none',
            },
        },
        {
            command: 'cd ../backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000',
            url: 'http://127.0.0.1:8000/docs',
            reuseExistingServer: !process.env.CI,
            timeout: 120 * 1000,
        }
    ],
});
