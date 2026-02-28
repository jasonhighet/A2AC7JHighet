/**
 * src/store/app-store.ts
 * ----------------------
 * Centralised application state, implemented as a singleton class that
 * extends EventTarget to act as both a state container and an event bus.
 *
 * Pattern:
 *  1. Components call store methods to trigger mutations.
 *  2. The store mutates its private state, then dispatches a CustomEvent.
 *  3. Components subscribe to those events in connectedCallback() and
 *     unsubscribe in disconnectedCallback() to avoid memory leaks.
 *
 * Events dispatched:
 *  - 'applications-changed'  → detail: ApplicationResponse[]
 *  - 'app-selected'          → detail: string | null  (the selected app id)
 *  - 'configs-changed'       → detail: ConfigurationResponse[]
 *  - 'loading-changed'       → detail: boolean
 *  - 'error-changed'         → detail: string | null
 *
 * @see src/api/client.ts    — API calls
 * @see src/api/types.ts     — type definitions
 */

import {
    applicationsApi,
    configurationsApi,
    ApiClientError,
} from '../api/client.js';
import type {
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    ConfigurationCreate,
    ConfigurationResponse,
    ConfigurationUpdate,
} from '../api/types.js';

// ---------------------------------------------------------------------------
// Typed event map for better DX when subscribing to the store
// ---------------------------------------------------------------------------

export interface StoreEventMap {
    'applications-changed': CustomEvent<ApplicationResponse[]>;
    'app-selected': CustomEvent<string | null>;
    'configs-changed': CustomEvent<ConfigurationResponse[]>;
    'loading-changed': CustomEvent<boolean>;
    'error-changed': CustomEvent<string | null>;
}

// ---------------------------------------------------------------------------
// AppStore
// ---------------------------------------------------------------------------

class AppStore extends EventTarget {
    // Private state using class field privates (#) for true encapsulation.
    #applications: ApplicationResponse[] = [];
    #selectedAppId: string | null = null;
    #configs: ConfigurationResponse[] = [];
    #loading = false;
    #error: string | null = null;

    // ---- Accessors -----------------------------------------------------------

    get applications(): readonly ApplicationResponse[] { return this.#applications; }
    get selectedAppId(): string | null { return this.#selectedAppId; }
    get configs(): readonly ConfigurationResponse[] { return this.#configs; }
    get loading(): boolean { return this.#loading; }
    get error(): string | null { return this.#error; }

    get selectedApp(): ApplicationResponse | undefined {
        return this.#applications.find((a) => a.id === this.#selectedAppId);
    }

    // ---- Private helpers -----------------------------------------------------

    #emit<K extends keyof StoreEventMap>(
        type: K,
        detail: StoreEventMap[K]['detail'],
    ): void {
        this.dispatchEvent(new CustomEvent(type, { detail }));
    }

    #setLoading(value: boolean): void {
        this.#loading = value;
        this.#emit('loading-changed', value);
    }

    #setError(message: string | null): void {
        this.#error = message;
        this.#emit('error-changed', message);
    }

    #handleError(err: unknown): void {
        // Use duck-typing instead of instanceof so this works correctly
        // when ApiClientError is mocked in tests (vi.mock breaks instanceof).
        if (
            err !== null &&
            typeof err === 'object' &&
            'detail' in err &&
            typeof (err as { detail: unknown }).detail === 'string'
        ) {
            this.#setError((err as { detail: string }).detail);
        } else if (err instanceof Error) {
            this.#setError(err.message);
        } else {
            this.#setError('An unexpected error occurred.');
        }
    }


    // ---- Application actions -------------------------------------------------

    async loadApplications(): Promise<void> {
        this.#setLoading(true);
        this.#setError(null);
        try {
            const apps = await applicationsApi.list();
            this.#applications = apps;
            this.#emit('applications-changed', apps);
        } catch (err) {
            this.#handleError(err);
        } finally {
            this.#setLoading(false);
        }
    }

    async createApplication(body: ApplicationCreate): Promise<ApplicationResponse | null> {
        this.#setLoading(true);
        this.#setError(null);
        try {
            const app = await applicationsApi.create(body);
            this.#applications = [...this.#applications, app];
            this.#emit('applications-changed', this.#applications);
            return app;
        } catch (err) {
            this.#handleError(err);
            return null;
        } finally {
            this.#setLoading(false);
        }
    }

    async updateApplication(id: string, body: ApplicationUpdate): Promise<ApplicationResponse | null> {
        this.#setLoading(true);
        this.#setError(null);
        try {
            const updated = await applicationsApi.update(id, body);
            this.#applications = this.#applications.map((a) => (a.id === id ? updated : a));
            this.#emit('applications-changed', this.#applications);
            return updated;
        } catch (err) {
            this.#handleError(err);
            return null;
        } finally {
            this.#setLoading(false);
        }
    }

    selectApplication(id: string | null): void {
        this.#selectedAppId = id;
        this.#configs = [];
        this.#emit('app-selected', id);
        this.#emit('configs-changed', []);
        if (id !== null) {
            void this.#loadConfigsForApp(id);
        }
    }

    // ---- Configuration actions -----------------------------------------------

    /**
     * Waterfall fetch: loads an app by ID to get its configuration_ids,
     * then resolves each ID in parallel.
     *
     * NOTE: This approach is intentionally a workaround for the missing
     * GET /configurations?application_id=X endpoint. See Implementation Plan.
     */
    async #loadConfigsForApp(appId: string): Promise<void> {
        this.#setLoading(true);
        this.#setError(null);
        try {
            const app = await applicationsApi.get(appId);
            const ids = app.configuration_ids ?? [];
            const configs = await configurationsApi.getMany(ids);
            this.#configs = configs;
            this.#emit('configs-changed', configs);
        } catch (err) {
            this.#handleError(err);
        } finally {
            this.#setLoading(false);
        }
    }

    async createConfiguration(body: ConfigurationCreate): Promise<ConfigurationResponse | null> {
        this.#setLoading(true);
        this.#setError(null);
        try {
            const config = await configurationsApi.create(body);
            this.#configs = [...this.#configs, config];
            // Track the new ID on the in-memory application object.
            this.#applications = this.#applications.map((a) => {
                if (a.id !== body.application_id) return a;
                return {
                    ...a,
                    configuration_ids: [...(a.configuration_ids ?? []), config.id],
                };
            });
            this.#emit('configs-changed', this.#configs);
            return config;
        } catch (err) {
            this.#handleError(err);
            return null;
        } finally {
            this.#setLoading(false);
        }
    }

    async updateConfiguration(id: string, body: ConfigurationUpdate): Promise<ConfigurationResponse | null> {
        this.#setLoading(true);
        this.#setError(null);
        try {
            const updated = await configurationsApi.update(id, body);
            this.#configs = this.#configs.map((c) => (c.id === id ? updated : c));
            this.#emit('configs-changed', this.#configs);
            return updated;
        } catch (err) {
            this.#handleError(err);
            return null;
        } finally {
            this.#setLoading(false);
        }
    }
}

// Module-level singleton — import `store` anywhere to access shared state.
export const store = new AppStore();
