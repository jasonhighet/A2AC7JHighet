/**
 * tests/unit/store/app-store.test.ts
 * ------------------------------------
 * Unit tests for AppStore state management and event emissions.
 * Mocks the API client so no real HTTP calls are made.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// ---------------------------------------------------------------------------
// Mock the API client module before importing the store
// ---------------------------------------------------------------------------

vi.mock('../../../src/api/client.js', () => ({
    applicationsApi: {
        list: vi.fn(),
        get: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
    },
    configurationsApi: {
        get: vi.fn(),
        getMany: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
    },
}));

import { store } from '../../../src/store/app-store.js';
import { applicationsApi, configurationsApi } from '../../../src/api/client.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function listenOnce<T>(eventName: string): Promise<T> {
    return new Promise((resolve) => {
        store.addEventListener(eventName, (e) => {
            resolve((e as CustomEvent<T>).detail);
        }, { once: true });
    });
}

beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state between tests by selecting null
    store.selectApplication(null);
});

// ---------------------------------------------------------------------------
// loadApplications
// ---------------------------------------------------------------------------

describe('store.loadApplications', () => {
    it('sets applications and dispatches applications-changed', async () => {
        const apps = [{ id: '1', name: 'app-one' }];
        vi.mocked(applicationsApi.list).mockResolvedValue(apps as any);

        const changeEvent = listenOnce<typeof apps>('applications-changed');
        await store.loadApplications();

        expect(store.applications).toEqual(apps);
        expect(await changeEvent).toEqual(apps);
    });

    it('dispatches loading-changed true then false', async () => {
        vi.mocked(applicationsApi.list).mockResolvedValue([]);
        const loadingValues: boolean[] = [];

        store.addEventListener('loading-changed', (e) => {
            loadingValues.push((e as CustomEvent<boolean>).detail);
        });

        await store.loadApplications();

        expect(loadingValues).toContain(true);
        expect(loadingValues.at(-1)).toBe(false);
    });

    it('dispatches error-changed when API throws', async () => {
        // Throw a plain object with {detail} — matches the store's duck-typing check.
        vi.mocked(applicationsApi.list).mockRejectedValue({ detail: 'Server error', status: 500 });

        // Collect every error-changed event into an array.
        const errors: Array<string | null> = [];
        const handler = (e: Event) => errors.push((e as CustomEvent<string | null>).detail);
        store.addEventListener('error-changed', handler);

        await store.loadApplications();

        store.removeEventListener('error-changed', handler);

        // The store fires error-changed(null) to reset, then error-changed('Server error').
        expect(errors).toContain('Server error');
        expect(store.error).toBe('Server error');
    });

});

// ---------------------------------------------------------------------------
// createApplication
// ---------------------------------------------------------------------------

describe('store.createApplication', () => {
    it('appends the new app and dispatches applications-changed', async () => {
        const newApp = { id: '99', name: 'new-app' };
        vi.mocked(applicationsApi.list).mockResolvedValue([]);
        vi.mocked(applicationsApi.create).mockResolvedValue(newApp as any);

        await store.loadApplications();
        const changeEvent = listenOnce<any[]>('applications-changed');
        const result = await store.createApplication({ name: 'new-app' });

        expect(result).toEqual(newApp);
        const updated = await changeEvent;
        expect(updated).toContainEqual(newApp);
        expect(store.applications).toContainEqual(newApp);
    });

    it('returns null and sets error when API throws', async () => {
        vi.mocked(applicationsApi.create).mockRejectedValue({ detail: 'Name already exists', status: 409 });

        const result = await store.createApplication({ name: 'dupe' });
        expect(result).toBeNull();
        expect(store.error).toBe('Name already exists');
    });
});

// ---------------------------------------------------------------------------
// selectApplication
// ---------------------------------------------------------------------------

describe('store.selectApplication', () => {
    it('dispatches app-selected with the given id', async () => {
        vi.mocked(applicationsApi.get).mockResolvedValue({ id: 'x', name: 'x', configuration_ids: [] } as any);
        vi.mocked(configurationsApi.getMany).mockResolvedValue([]);

        const selectEvent = listenOnce<string>('app-selected');
        store.selectApplication('x');

        expect(await selectEvent).toBe('x');
        expect(store.selectedAppId).toBe('x');
    });

    it('clears configs when null is passed', () => {
        store.selectApplication(null);
        expect(store.selectedAppId).toBeNull();
        expect(store.configs).toHaveLength(0);
    });
});

// ---------------------------------------------------------------------------
// createConfiguration
// ---------------------------------------------------------------------------

describe('store.createConfiguration', () => {
    it('appends the new config and dispatches configs-changed', async () => {
        const newCfg = { id: 'cfg-1', application_id: 'app-1', name: 'prod', config: {} };
        vi.mocked(configurationsApi.create).mockResolvedValue(newCfg as any);
        vi.mocked(applicationsApi.list).mockResolvedValue([{ id: 'app-1', name: 'a' }] as any);
        await store.loadApplications();

        const changeEvent = listenOnce<any[]>('configs-changed');
        const result = await store.createConfiguration({ application_id: 'app-1', name: 'prod', config: {} });

        expect(result).toEqual(newCfg);
        const updated = await changeEvent;
        expect(updated).toContainEqual(newCfg);
    });
});
