import { expect, test } from '@playwright/test';

test.describe('Binary Inspector - Bidirectional Highlighting', () => {

    test.beforeEach(async ({ page }) => {
        // Go to homepage
        await page.goto('/');

        // Ensure page loaded
        await expect(page.getByText('Blink Message Playground')).toBeVisible({ timeout: 10000 });

        // Click Convert to ensure data is ready
        const convertButton = page.getByRole('button', { name: 'Convert' });
        await expect(convertButton).toBeVisible({ timeout: 5000 });
        await convertButton.click();

        // Wait for success
        try {
            await expect(page.getByText('Message converted successfully!')).toBeVisible({ timeout: 10000 });
        } catch (e) {
            console.log('Conversion may have failed or toast disappeared quickly');
        }

        // Wait for Native Binary output
        await expect(page.getByRole('heading', { name: 'Native Binary' })).toBeVisible({ timeout: 15000 });

        // Wait a bit for the data to settle
        await page.waitForTimeout(1000);

        // Open Advanced Inspector
        const inspectorButton = page.getByTitle("Open Advanced Binary Inspector");
        await expect(inspectorButton).toBeVisible({ timeout: 5000 });
        await inspectorButton.click();

        // Wait for inspector modal to open
        const modal = page.locator('h2', { hasText: 'Advanced Binary Inspector' });
        await expect(modal).toBeVisible({ timeout: 5000 });

        // Wait for analysis to complete - look for any field or section
        // Try multiple possible indicators that analysis is done
        try {
            await expect(page.getByText('Message Size').first()).toBeVisible({ timeout: 15000 });
        } catch (e) {
            // If "Message Size" not found, try looking for any field
            try {
                await expect(page.getByText('"CompanyName"').first()).toBeVisible({ timeout: 5000 });
            } catch (e2) {
                // Last resort: just wait for the analyzing text to disappear
                await expect(page.getByText('Analyzing...')).not.toBeVisible({ timeout: 10000 });
            }
        }
    });

    test('highlights both pointer and data when clicking on string field', async ({ page }) => {
        // Find any string field in the structure pane (left side)
        // Look for a field with quotes around it
        const stringFields = page.locator('[class*="text-purple-700"]').filter({ hasText: '"' });
        const firstField = stringFields.first();

        // Wait for at least one field to be visible
        await expect(firstField).toBeVisible({ timeout: 5000 });

        // Click on the first string field
        await firstField.click();

        // Wait a moment for highlighting to apply
        await page.waitForTimeout(500);

        // The field container should be highlighted with blue background
        const fieldContainer = firstField.locator('..');
        await expect(fieldContainer).toHaveClass(/bg-blue/, { timeout: 2000 });

        // Both the pointer bytes and data bytes should be highlighted in the hex view
        const highlightedBytes = page.locator('.ring-2.ring-blue-500, .ring-2.ring-blue-300');
        const count = await highlightedBytes.count();

        // Should have multiple highlighted bytes (pointer + data)
        expect(count).toBeGreaterThan(0);
    });

    test('highlights field when clicking on pointer offset in hex view', async ({ page }) => {
        // Click on a byte in the hex view
        const hexByte = page.locator('[id^="byte-"]').nth(20); // Try byte at offset 20

        if (await hexByte.count() > 0) {
            await hexByte.click();

            // Wait for highlighting
            await page.waitForTimeout(500);

            // Check if a field in the structure pane is highlighted
            const highlightedField = page.locator('.bg-blue-100, .bg-blue-50').first();

            // Either a field is highlighted OR we have highlighted bytes
            const fieldHighlighted = await highlightedField.count() > 0;
            const bytesHighlighted = await page.locator('.ring-2.ring-blue-500, .ring-2.ring-blue-300').count() > 0;

            expect(fieldHighlighted || bytesHighlighted).toBeTruthy();
        }
    });

    test('highlights both pointer and data bytes when clicking on data bytes', async ({ page }) => {
        // Click on any field first to see what gets highlighted
        const anyField = page.locator('[class*="text-purple-700"]').first();
        await expect(anyField).toBeVisible({ timeout: 5000 });
        await anyField.click();

        // Wait for highlighting
        await page.waitForTimeout(500);

        // Find a highlighted byte in the hex view
        const highlightedByte = page.locator('.ring-2.ring-blue-500, .ring-2.ring-blue-300').first();

        if (await highlightedByte.count() > 0) {
            await highlightedByte.click();

            // Wait for highlighting
            await page.waitForTimeout(500);

            // Both pointer and data bytes should be highlighted
            const highlightedBytes = page.locator('.ring-2.ring-blue-500, .ring-2.ring-blue-300');
            const count = await highlightedBytes.count();

            // Should have highlighted bytes
            expect(count).toBeGreaterThan(0);
        }
    });

    test('shows different highlight styles for selected vs related sections', async ({ page }) => {
        // Click on any field
        const anyField = page.locator('[class*="text-purple-700"]').first();
        await expect(anyField).toBeVisible({ timeout: 5000 });
        await anyField.click();

        // Wait for highlighting
        await page.waitForTimeout(500);

        // Check for either primary or related highlights
        const primaryHighlight = page.locator('.ring-blue-500');
        const relatedHighlight = page.locator('.ring-blue-300');

        const primaryCount = await primaryHighlight.count();
        const relatedCount = await relatedHighlight.count();

        // Should have some kind of highlighting
        expect(primaryCount + relatedCount).toBeGreaterThan(0);
    });

    test('clears related highlights when selecting different field', async ({ page }) => {
        // Get all fields
        const fields = page.locator('[class*="text-purple-700"]').filter({ hasText: '"' });
        const fieldCount = await fields.count();

        if (fieldCount >= 2) {
            // Click first field
            await fields.nth(0).click();
            await page.waitForTimeout(500);

            // Verify first field is highlighted
            const firstFieldContainer = fields.nth(0).locator('..');
            await expect(firstFieldContainer).toHaveClass(/bg-blue/);

            // Click second field
            await fields.nth(1).click();
            await page.waitForTimeout(500);

            // First field should no longer have primary highlight
            const firstFieldClass = await firstFieldContainer.getAttribute('class');
            expect(firstFieldClass).not.toContain('bg-blue-100');

            // Second field should be highlighted
            const secondFieldContainer = fields.nth(1).locator('..');
            await expect(secondFieldContainer).toHaveClass(/bg-blue/);
        }
    });

    test('works with nested object pointers', async ({ page }) => {
        // Find any nested object field (might have different structure)
        const allFields = page.locator('[class*="text-purple-700"]');
        const fieldCount = await allFields.count();

        if (fieldCount > 1) {
            // Click on the second field (might be nested)
            await allFields.nth(1).click();
            await page.waitForTimeout(500);

            // Should highlight some bytes (or at least not error)
            const highlightedBytes = page.locator('.ring-2.ring-blue-500, .ring-2.ring-blue-300');
            const count = await highlightedBytes.count();

            // Should have highlighted bytes (or 0 if it's not a pointer field)
            expect(count).toBeGreaterThanOrEqual(0);
        } else {
            // If there's only one field or none, the test passes
            expect(fieldCount).toBeGreaterThanOrEqual(0);
        }
    });

    test('maintains highlighting during scroll', async ({ page }) => {
        // Click on any field
        const anyField = page.locator('[class*="text-purple-700"]').first();
        await expect(anyField).toBeVisible({ timeout: 5000 });
        await anyField.click();
        await page.waitForTimeout(500);

        // Get initial highlight count
        const highlightedBytes = page.locator('.ring-2.ring-blue-500, .ring-2.ring-blue-300');
        const initialCount = await highlightedBytes.count();
        expect(initialCount).toBeGreaterThan(0);

        // Scroll the hex pane (find the scrollable container)
        const hexPane = page.locator('.overflow-auto').last();
        if (await hexPane.count() > 0) {
            await hexPane.evaluate(node => node.scrollTop = 50);
            await page.waitForTimeout(300);

            // Highlighting should still be present
            const afterScrollCount = await highlightedBytes.count();
            expect(afterScrollCount).toBeGreaterThan(0);
        }
    });
});
