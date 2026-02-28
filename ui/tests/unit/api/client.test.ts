/**
 * tests/unit/api/client.test.ts
 * --------------------------------
 * Unit tests for ApiClient fetch wrapper.
 * Uses vi.stubGlobal to mock the global fetch function — no real HTTP calls.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { applicationsApi, configurationsApi, ApiClientError } from '../../../src/api/client.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function mockFetch(status: number, body: unknown): void {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: status >= 200 && status < 300,
        status,
        statusText: 'OK',
        json: () => Promise.resolve(body),
    }));
}

function mockFetchReject(error: Error): void {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(error));
}

beforeEach(() => { vi.clearAllMocks(); });
afterEach(() => { vi.unstubAllGlobals(); });

// ---------------------------------------------------------------------------
// applicationsApi
// ---------------------------------------------------------------------------

describe('applicationsApi.list', () => {
    it('calls GET /api/v1/applications and returns the response', async () => {
        const apps = [{ id: '1', name: 'my-app', comments: null }];
        mockFetch(200, apps);

        const result = await applicationsApi.list();

        expect(fetch).toHaveBeenCalledWith('/api/v1/applications', expect.objectContaining({ method: 'GET' }));
        expect(result).toEqual(apps);
    });
});

describe('applicationsApi.get', () => {
    it('calls GET /api/v1/applications/{id}', async () => {
        const app = { id: 'abc', name: 'payments', configuration_ids: [] };
        mockFetch(200, app);

        const result = await applicationsApi.get('abc');

        expect(fetch).toHaveBeenCalledWith('/api/v1/applications/abc', expect.objectContaining({ method: 'GET' }));
        expect(result).toEqual(app);
    });
});

describe('applicationsApi.create', () => {
    it('calls POST /api/v1/applications with the correct body', async () => {
        const created = { id: 'new-id', name: 'billing', comments: undefined };
        mockFetch(201, created);

        const result = await applicationsApi.create({ name: 'billing' });

        const fetchCall = vi.mocked(fetch).mock.calls[0]!;
        expect(fetchCall[1]?.method).toBe('POST');
        expect(JSON.parse(fetchCall[1]?.body as string)).toEqual({ name: 'billing' });
        expect(result).toEqual(created);
    });
});

describe('applicationsApi.update', () => {
    it('calls PUT /api/v1/applications/{id}', async () => {
        const updated = { id: 'old-id', name: 'billing-v2' };
        mockFetch(200, updated);

        const result = await applicationsApi.update('old-id', { name: 'billing-v2' });

        expect(fetch).toHaveBeenCalledWith('/api/v1/applications/old-id', expect.objectContaining({ method: 'PUT' }));
        expect(result).toEqual(updated);
    });
});

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

describe('ApiClientError', () => {
    it('throws ApiClientError with status and detail on 404', async () => {
        mockFetch(404, { detail: 'Application not found' });

        await expect(applicationsApi.get('missing')).rejects.toThrow(ApiClientError);
        await expect(applicationsApi.get('missing')).rejects.toMatchObject({
            status: 404,
            detail: 'Application not found',
        });
    });

    it('throws ApiClientError with detail on 409 conflict', async () => {
        mockFetch(409, { detail: 'Name already exists' });

        await expect(applicationsApi.create({ name: 'dupe' })).rejects.toMatchObject({
            status: 409,
            detail: 'Name already exists',
        });
    });

    it('falls back to statusText if response body is not valid JSON', async () => {
        vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
            ok: false,
            status: 500,
            statusText: 'Internal Server Error',
            json: () => Promise.reject(new SyntaxError('invalid json')),
        }));

        await expect(applicationsApi.list()).rejects.toMatchObject({
            status: 500,
            detail: 'Internal Server Error',
        });
    });

    it('propagates network errors', async () => {
        mockFetchReject(new TypeError('Failed to fetch'));

        await expect(applicationsApi.list()).rejects.toThrow(TypeError);
    });
});

// ---------------------------------------------------------------------------
// configurationsApi
// ---------------------------------------------------------------------------

describe('configurationsApi.get', () => {
    it('calls GET /api/v1/configurations/{id}', async () => {
        const cfg = { id: 'cfg-1', application_id: 'app-1', name: 'prod', config: {} };
        mockFetch(200, cfg);

        const result = await configurationsApi.get('cfg-1');

        expect(fetch).toHaveBeenCalledWith('/api/v1/configurations/cfg-1', expect.objectContaining({ method: 'GET' }));
        expect(result).toEqual(cfg);
    });
});

describe('configurationsApi.getMany', () => {
    it('fetches all IDs in parallel via Promise.all', async () => {
        const configs = [
            { id: 'a', application_id: 'app', name: 'dev', config: {} },
            { id: 'b', application_id: 'app', name: 'prod', config: { key: 'val' } },
        ];
        let callCount = 0;
        vi.stubGlobal('fetch', vi.fn().mockImplementation(() => {
            const c = configs[callCount++]!;
            return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(c) });
        }));

        const result = await configurationsApi.getMany(['a', 'b']);

        expect(fetch).toHaveBeenCalledTimes(2);
        expect(result).toHaveLength(2);
    });
});

describe('configurationsApi.create', () => {
    it('calls POST /api/v1/configurations with correct body', async () => {
        const created = { id: 'new', application_id: 'app', name: 'staging', config: { host: 'x' } };
        mockFetch(201, created);

        await configurationsApi.create({ application_id: 'app', name: 'staging', config: { host: 'x' } });

        const fetchCall = vi.mocked(fetch).mock.calls[0]!;
        expect(fetchCall[1]?.method).toBe('POST');
        expect(JSON.parse(fetchCall[1]?.body as string).config).toEqual({ host: 'x' });
    });
});
