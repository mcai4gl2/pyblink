import { expect, test } from '@playwright/test';

// List of examples to test - mirroring src/data/examples.ts logic
const EXAMPLES = [
    'Simple Person',
    'Nested Company (Default)',
    'Trading Order',
    'Dynamic Group',
    'Sequence Example',
    'Optional Fields',
    'Enum Usage'
];

test.describe('Example Library', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await expect(page.getByText('Blink Message Playground')).toBeVisible();
    });

    for (const exampleTitle of EXAMPLES) {
        test(`can render example: ${exampleTitle}`, async ({ page }) => {
            // Select Example from Dropdown
            // Scoped to banner as there are multiple comboboxes on page
            const dropdown = page.getByRole('banner').getByRole('combobox');
            await dropdown.selectOption({ label: exampleTitle });

            // Verify Loaded Toast
            // "Loaded example: X" or "Loaded playground: X" (if from URL)
            // App.tsx: showInfo(`Loaded example: ${example.title}`);
            const loadedToast = page.getByText(`Loaded example: ${exampleTitle}`);
            await expect(loadedToast).toBeVisible();

            // Click Convert
            await page.getByRole('button', { name: 'Convert' }).click();

            // Verify Conversion Success
            const successToast = page.getByText('Message converted successfully!');
            await expect(successToast).toBeVisible();

            // Verify Native Binary Output (check for any byte content, e.g. "00" or just non-empty)
            // The hex pane uses mono-block. Just check output panel is active.
            // Look for "Native Binary" header.
            await expect(page.getByRole('heading', { name: 'Native Binary' })).toBeVisible();

            // Optional: Check specific content logic
            // E.g. "Simple Person" -> should have "Alice" in output view
            if (exampleTitle.includes('Simple Person')) {
                // "Alice" ASCII
                await expect(page.locator('body')).toContainText('Alice');
            }
        });
    }
});
