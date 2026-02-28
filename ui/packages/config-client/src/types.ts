/**
 * Applications Management Types
 */

export interface ApplicationCreate {
    name: string;
    comments?: string;
}

export interface ApplicationUpdate {
    name?: string;
    comments?: string;
}

export interface ApplicationResponse {
    id: string;
    name: string;
    comments: string | null;
}

/**
 * Configurations Management Types
 */

export interface ConfigurationCreate {
    application_id: string;
    name: string;
    comments?: string;
    config?: Record<string, any>;
}

export interface ConfigurationUpdate {
    name?: string;
    comments?: string;
    config?: Record<string, any>;
}

export interface ConfigurationResponse {
    id: string;
    application_id: string;
    name: string;
    comments: string | null;
    config: Record<string, any>;
}
