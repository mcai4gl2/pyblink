import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './e2e',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: 'html',
    use: {
        baseURL: 'http://localhost:3000',
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
            url: 'http://localhost:3000',
            reuseExistingServer: !process.env.CI,
            timeout: 120 * 1000,
        },
        {
            // Start backend from project root to ensure imports work (assuming PYTHONPATH setup or venv)
            // We run from frontend dir, so cd .. to project root.
            // Then set PYTHONPATH to include current dir (.) so 'blink' and 'backend' are visible?
            // Or just rely on standard structure.
            // Assuming 'python' is in path and has dependencies installed.
            command: 'cd .. && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000',
            url: 'http://127.0.0.1:8000/docs',
            reuseExistingServer: !process.env.CI,
            timeout: 120 * 1000,
        }
    ],
});
