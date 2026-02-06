import { defineConfig, devices } from '@playwright/test';

// In CI with USE_BUILD=true, use production build with 'serve' (fast static server)
// Locally, use 'npm start' (dev server with hot reload)
const useBuild = process.env.USE_BUILD === 'true';
const isCI = !!process.env.CI;

export default defineConfig({
    testDir: './e2e',
    fullyParallel: true,
    forbidOnly: isCI,
    retries: 0,  // No retries - fail fast and check traces for debugging
    workers: isCI ? 1 : undefined,
    // Per-test timeout: 30s in CI, 60s locally
    timeout: isCI ? 30 * 1000 : 60 * 1000,
    // Global timeout: 4 minutes in CI (leaves 1 min buffer for 5 min job timeout)
    globalTimeout: isCI ? 4 * 60 * 1000 : undefined,
    // Expect timeout: 10s for assertions
    expect: {
        timeout: 10 * 1000,
    },
    reporter: isCI
        ? [['list'], ['html'], ['github']]  // GitHub annotations for CI
        : [['list'], ['html']],
    use: {
        baseURL: 'http://127.0.0.1:3000',
        // Enhanced debugging: always capture trace in CI
        trace: isCI ? 'on' : 'on-first-retry',
        // Capture screenshot on failure
        screenshot: 'only-on-failure',
        // Capture video on failure (helps debug timing issues)
        video: isCI ? 'retain-on-failure' : 'off',
        // Slow down actions for debugging (50ms between actions)
        actionTimeout: 10 * 1000,
    },

    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],

    webServer: [
        {
            // In CI: use 'serve' to host pre-built static files (fast startup)
            // Locally: use 'npm start' for dev server with hot reload
            command: useBuild
                ? 'npx serve -s build -l 3000'
                : 'npm start',
            url: 'http://127.0.0.1:3000',
            reuseExistingServer: !isCI,
            // serve starts in <5s, npm start can take 60s+
            timeout: useBuild ? 30 * 1000 : 120 * 1000,
            stdout: 'pipe',  // Capture server output for debugging
            stderr: 'pipe',
            env: {
                PORT: '3000',
                REACT_APP_API_URL: 'http://127.0.0.1:8000',
                BROWSER: 'none',
            },
        },
        {
            // Backend server command - works on both Windows and Linux
            // Windows: uses .venv\Scripts\python.exe
            // Linux/CI: uses .venv/bin/python or system python
            command: process.platform === 'win32'
                ? 'cd ../backend && .venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000'
                : 'cd ../backend && (test -f .venv/bin/python && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 || python -m uvicorn app.main:app --host 127.0.0.1 --port 8000)',
            url: 'http://127.0.0.1:8000/docs',
            reuseExistingServer: !isCI,
            timeout: 30 * 1000,
            stdout: 'pipe',
            stderr: 'pipe',
        }
    ],
});
