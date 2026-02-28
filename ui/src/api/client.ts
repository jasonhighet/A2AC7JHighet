/**
 * src/api/client.ts
 * -----------------
 * Typed fetch wrapper over the Config Service REST API.
 *
 * All HTTP calls go through the single `request()` method, which:
 *  - Sets JSON content-type headers
 *  - Runs the auth hook (currently a no-op stub — see NOTE below)
 *  - Parses JSON responses
 *  - Throws ApiClientError on non-2xx status codes
 *
 * Base URL Resolution:
 *  In development the Vite dev server proxies `/api` → `http://localhost:8000`
 *  via vite.config.ts `server.proxy`, so the base URL is left as an empty string.
 *  In production the UI must be served from the same origin as the API, or the
 *  BASE_URL must be updated to the deployed API origin.
 *
 * @see src/api/types.ts   — request/response type definitions
 * @see vite.config.ts     — /api proxy configuration
 */

import type {
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    ConfigurationCreate,
    ConfigurationResponse,
    ConfigurationUpdate,
    ApiError,
} from './types.js';

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ApiClientError extends Error {
    constructor(
        public readonly status: number,
        public readonly detail: string,
    ) {
        super(`API error ${status}: ${detail}`);
        this.name = 'ApiClientError';
    }
}

// ---------------------------------------------------------------------------
// Auth hook stub
// NOTE: Authentication is not required in this phase.
// When auth is introduced, update this function to return the required headers
// (e.g. { Authorization: `Bearer ${getToken()}` }).
// ---------------------------------------------------------------------------

function getAuthHeaders(): Record<string, string> {
    // TODO(auth): return auth headers here when authentication is implemented.
    return {};
}

// ---------------------------------------------------------------------------
// Core request helper
// ---------------------------------------------------------------------------

const BASE_URL = '/api/v1';

async function request<T>(
    method: string,
    path: string,
    body?: unknown,
): Promise<T> {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...getAuthHeaders(),
    };

    const response = await fetch(`${BASE_URL}${path}`, {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
        let detail = response.statusText;
        try {
            const err = (await response.json()) as ApiError;
            detail = err.detail ?? detail;
        } catch {
            // Response body was not valid JSON — use statusText as fallback.
        }
        throw new ApiClientError(response.status, detail);
    }

    // 204 No Content — return empty object cast to T.
    if (response.status === 204) {
        return {} as T;
    }

    return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Applications API
// ---------------------------------------------------------------------------

export const applicationsApi = {
    /** GET /api/v1/applications → ApplicationResponse[] */
    list(): Promise<ApplicationResponse[]> {
        return request<ApplicationResponse[]>('GET', '/applications');
    },

    /** GET /api/v1/applications/{id} → ApplicationResponse */
    get(id: string): Promise<ApplicationResponse> {
        return request<ApplicationResponse>('GET', `/applications/${id}`);
    },

    /** POST /api/v1/applications → ApplicationResponse (201) */
    create(body: ApplicationCreate): Promise<ApplicationResponse> {
        return request<ApplicationResponse>('POST', '/applications', body);
    },

    /** PUT /api/v1/applications/{id} → ApplicationResponse */
    update(id: string, body: ApplicationUpdate): Promise<ApplicationResponse> {
        return request<ApplicationResponse>('PUT', `/applications/${id}`, body);
    },
};

// ---------------------------------------------------------------------------
// Configurations API
// ---------------------------------------------------------------------------

export const configurationsApi = {
    /** GET /api/v1/configurations/{id} → ConfigurationResponse */
    get(id: string): Promise<ConfigurationResponse> {
        return request<ConfigurationResponse>('GET', `/configurations/${id}`);
    },

    /**
     * Waterfall fetch: resolves a list of configuration IDs to full objects.
     * Calls GET /configurations/{id} for each ID concurrently via Promise.all.
     *
     * NOTE: This is intentionally inefficient. A future Collaborative Improvement
     * will add GET /configurations?application_id=X to replace this.
     */
    async getMany(ids: string[]): Promise<ConfigurationResponse[]> {
        return Promise.all(ids.map((id) => configurationsApi.get(id)));
    },

    /** POST /api/v1/configurations → ConfigurationResponse (201) */
    create(body: ConfigurationCreate): Promise<ConfigurationResponse> {
        return request<ConfigurationResponse>('POST', '/configurations', body);
    },

    /** PUT /api/v1/configurations/{id} → ConfigurationResponse */
    update(id: string, body: ConfigurationUpdate): Promise<ConfigurationResponse> {
        return request<ConfigurationResponse>('PUT', `/configurations/${id}`, body);
    },
};
