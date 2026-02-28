/**
 * tests/e2e/configurations.spec.ts
 * ----------------------------------
 * Playwright integration tests: full CRUD flow for Configurations.
 * Creates a parent application first, then tests configuration operations.
 */

import { test, expect } from '@playwright/test';

const uid = (): string => `${Date.now()}`;

test.describe('Configurations CRUD', () => {
    test('creates a configuration under an application', async ({ page }) => {
        await page.goto('/');
        const appName = `e2e-app-${uid()}`;
        const cfgName = `e2e-cfg-${uid()}`;

        // Step 1: Create an application
        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            shell.shadowRoot.getElementById('addAppBtn')?.click();
            const form = shell.shadowRoot.getElementById('appForm') as any;
            (form.shadowRoot.getElementById('name') as HTMLInputElement).value = n;
            form.shadowRoot.getElementById('submitBtn')?.click();
        }, appName);
        await page.waitForTimeout(700);

        // Step 2: Select the application
        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            const list = shell.shadowRoot.getElementById('appList') as any;
            const items = list.shadowRoot.querySelectorAll('.item') as NodeListOf<HTMLElement>;
            for (const item of items) {
                if (item.textContent?.includes(n)) {
                    item.click();
                    break;
                }
            }
        }, appName);
        await page.waitForTimeout(400);

        // Step 3: Create a configuration
        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            shell.shadowRoot.getElementById('addConfigBtn')?.click();
            const form = shell.shadowRoot.getElementById('configForm') as any;
            (form.shadowRoot.getElementById('name') as HTMLInputElement).value = n;
            (form.shadowRoot.getElementById('configJson') as HTMLTextAreaElement).value =
                JSON.stringify({ env: 'production', debug: false });
            form.shadowRoot.getElementById('submitBtn')?.click();
        }, cfgName);
        await page.waitForTimeout(700);

        // Step 4: Verify the config appears in the list
        const gridText = await page.evaluate(() => {
            const shell = document.querySelector('app-shell') as any;
            const cList = shell.shadowRoot.getElementById('configList') as any;
            return cList.shadowRoot.getElementById('content')?.textContent ?? '';
        });
        expect(gridText).toContain(cfgName);
        expect(gridText).toContain('2 keys');
    });

    test('edits a configuration', async ({ page }) => {
        await page.goto('/');
        const appName = `e2e-app-edit-${uid()}`;
        const cfgName = `e2e-cfg-edit-${uid()}`;
        const cfgNameUpdated = `${cfgName}-v2`;

        // Create app + config
        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            shell.shadowRoot.getElementById('addAppBtn')?.click();
            const form = shell.shadowRoot.getElementById('appForm') as any;
            (form.shadowRoot.getElementById('name') as HTMLInputElement).value = n;
            form.shadowRoot.getElementById('submitBtn')?.click();
        }, appName);
        await page.waitForTimeout(700);

        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            const list = shell.shadowRoot.getElementById('appList') as any;
            for (const item of list.shadowRoot.querySelectorAll('.item') as NodeListOf<HTMLElement>) {
                if (item.textContent?.includes(n)) { item.click(); break; }
            }
        }, appName);
        await page.waitForTimeout(400);

        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            shell.shadowRoot.getElementById('addConfigBtn')?.click();
            const form = shell.shadowRoot.getElementById('configForm') as any;
            (form.shadowRoot.getElementById('name') as HTMLInputElement).value = n;
            form.shadowRoot.getElementById('submitBtn')?.click();
        }, cfgName);
        await page.waitForTimeout(700);

        // Edit the configuration
        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            const cList = shell.shadowRoot.getElementById('configList') as any;
            for (const btn of cList.shadowRoot.querySelectorAll('.edit-btn') as NodeListOf<HTMLButtonElement>) {
                if (btn.closest('.card')?.querySelector('.card-name')?.textContent?.includes(n)) {
                    btn.click(); break;
                }
            }
        }, cfgName);
        await page.waitForTimeout(300);

        await page.evaluate((n) => {
            const shell = document.querySelector('app-shell') as any;
            const form = shell.shadowRoot.getElementById('configForm') as any;
            (form.shadowRoot.getElementById('name') as HTMLInputElement).value = n;
            form.shadowRoot.getElementById('submitBtn')?.click();
        }, cfgNameUpdated);
        await page.waitForTimeout(700);

        const gridText = await page.evaluate(() => {
            const shell = document.querySelector('app-shell') as any;
            return shell.shadowRoot.getElementById('configList')?.shadowRoot.getElementById('content')?.textContent ?? '';
        });
        expect(gridText).toContain(cfgNameUpdated);
    });
});
