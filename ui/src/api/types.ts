/**
 * src/api/types.ts
 * ----------------
 * TypeScript interfaces that mirror the Pydantic models in the
 * config-service backend. Keep in sync with:
 *   - config-service/app/applications/models.py
 *   - config-service/app/configurations/models.py
 */

// ---------------------------------------------------------------------------
// Applications
// ---------------------------------------------------------------------------

/** POST /api/v1/applications */
export interface ApplicationCreate {
    name: string;
    comments?: string;
}

/** PUT /api/v1/applications/{id} */
export interface ApplicationUpdate {
    name?: string;
    comments?: string;
}

/** GET /api/v1/applications, GET /api/v1/applications/{id} */
export interface ApplicationResponse {
    id: string;
    name: string;
    comments?: string;
    /**
     * NOTE: The backend does not yet expose a list endpoint for
     * configurations. This field is populated client-side by the store
     * after each create/update call so that config-list can resolve IDs.
     *
     * @see src/store/app-store.ts
     * @see Implementation Plan — Collaborative Improvement section
     */
    configuration_ids?: string[];
}

// ---------------------------------------------------------------------------
// Configurations
// ---------------------------------------------------------------------------

/** POST /api/v1/configurations */
export interface ConfigurationCreate {
    application_id: string;
    name: string;
    comments?: string;
    config?: Record<string, unknown>;
}

/** PUT /api/v1/configurations/{id} */
export interface ConfigurationUpdate {
    name?: string;
    comments?: string;
    config?: Record<string, unknown>;
}

/** GET /api/v1/configurations/{id} */
export interface ConfigurationResponse {
    id: string;
    application_id: string;
    name: string;
    comments?: string;
    config: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Error shapes
// ---------------------------------------------------------------------------

/** 404 and 409 responses from FastAPI exception handlers */
export interface ApiError {
    detail: string;
}
