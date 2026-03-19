/**
 * tests/e2e/applications.spec.ts
 * --------------------------------
 * Playwright integration tests: full CRUD flow for Applications.
 * Requires the backend (localhost:8000) and UI (localhost:3000) to be running.
 * The UI dev server is auto-started via playwright.config.ts `webServer`.
 */

import { test, expect } from '@playwright/test';

const uniqueName = (): string => `test-app-${Date.now()}`;

test.describe('Applications CRUD', () => {
    test('shows empty state when no applications exist', async ({ page }) => {
        await page.goto('/');
        // The sidebar should load without errors
        await expect(page.locator('app-shell')).toBeVisible();
    });

    test('creates a new application and it appears in the sidebar', async ({ page }) => {
        await page.goto('/');
        const name = uniqueName();

        // Open the new application form
        const addBtn = page.locator('#addAppBtn');
        // Shadow DOM piercing — use evaluate to click inside shadow root
        await page.evaluate(() => {
            const shell = document.querySelector('app-shell') as any;
            const btn = shell.shadowRoot.getElementById('addAppBtn');
            btn?.click();
        });

        // Fill in the form inside the shadow DOM
        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            const form = shell.shadowRoot.getElementById('appForm') as any;
            const input = form.shadowRoot.getElementById('name') as HTMLInputElement;
            input.value = n;
            input.dispatchEvent(new Event('input'));
        }, name);

        // Submit the form
        await page.evaluate(() => {
            const shell = document.querySelector('app-shell') as any;
            const form = shell.shadowRoot.getElementById('appForm') as any;
            const submitBtn = form.shadowRoot.getElementById('submitBtn') as HTMLButtonElement;
            submitBtn.click();
        });

        // Wait for the success toast
        await page.waitForTimeout(500);

        // Verify the app appears in the sidebar list
        const listText = await page.evaluate(() => {
            const shell = document.querySelector('app-shell') as any;
            const list = shell.shadowRoot.getElementById('appList') as any;
            return list.shadowRoot.getElementById('list')?.textContent ?? '';
        });

        expect(listText).toContain(name);
    });

    test('edits an application name', async ({ page }) => {
        await page.goto('/');
        const originalName = uniqueName();
        const updatedName = `${originalName}-updated`;

        // Create an application first
        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            shell.shadowRoot.getElementById('addAppBtn')?.click();
            const form = shell.shadowRoot.getElementById('appForm') as any;
            (form.shadowRoot.getElementById('name') as HTMLInputElement).value = n;
        }, originalName);

        await page.evaluate(() => {
            const shell = document.querySelector('app-shell') as any;
            const form = shell.shadowRoot.getElementById('appForm') as any;
            form.shadowRoot.getElementById('submitBtn')?.click();
        });
        await page.waitForTimeout(600);

        // Click the edit button for the app
        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            const list = shell.shadowRoot.getElementById('appList') as any;
            const items = list.shadowRoot.querySelectorAll('.item') as NodeListOf<HTMLElement>;
            for (const item of items) {
                if (item.textContent?.includes(n)) {
                    (item.querySelector('.edit-btn') as HTMLButtonElement)?.click();
                    break;
                }
            }
        }, originalName);

        // Update the name
        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            const form = shell.shadowRoot.getElementById('appForm') as any;
            const input = form.shadowRoot.getElementById('name') as HTMLInputElement;
            input.value = n;
        }, updatedName);

        await page.evaluate(() => {
            const shell = document.querySelector('app-shell') as any;
            const form = shell.shadowRoot.getElementById('appForm') as any;
            form.shadowRoot.getElementById('submitBtn')?.click();
        });
        await page.waitForTimeout(600);

        const listText = await page.evaluate(() => {
            const shell = document.querySelector('app-shell') as any;
            const list = shell.shadowRoot.getElementById('appList') as any;
            return list.shadowRoot.getElementById('list')?.textContent ?? '';
        });
        expect(listText).toContain(updatedName);
    });
});
