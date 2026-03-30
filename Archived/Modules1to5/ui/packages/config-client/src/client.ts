import {
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    ConfigurationCreate,
    ConfigurationResponse,
    ConfigurationUpdate,
} from './types';
import {
    ConfigApiError,
    ConfigConflictError,
    ConfigNotFoundError,
    ConfigValidationError,
} from './errors';

export class ConfigClient {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
    }

    /**
     * Internal helper to handle fetch requests and error mapping.
     */
    private async request<T>(
        path: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${path}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const message = errorData.detail || response.statusText;

            switch (response.status) {
                case 404:
                    throw new ConfigNotFoundError(path.split('/').pop() || '', 'Resource');
                case 409:
                    throw new ConfigConflictError(message);
                case 422:
                    throw new ConfigValidationError(errorData.detail);
                default:
                    throw new ConfigApiError(message, response.status, errorData);
            }
        }

        if (response.status === 204) {
            return {} as T;
        }

        return response.json();
    }

    // --- Applications ---

    async listApplications(): Promise<ApplicationResponse[]> {
        return this.request<ApplicationResponse[]>('/api/v1/applications');
    }

    async getApplication(id: string): Promise<ApplicationResponse> {
        return this.request<ApplicationResponse>(`/api/v1/applications/${id}`);
    }

    async createApplication(data: ApplicationCreate): Promise<ApplicationResponse> {
        return this.request<ApplicationResponse>('/api/v1/applications', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateApplication(
        id: string,
        data: ApplicationUpdate
    ): Promise<ApplicationResponse> {
        return this.request<ApplicationResponse>(`/api/v1/applications/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    // --- Configurations ---

    async getConfiguration(id: string): Promise<ConfigurationResponse> {
        return this.request<ConfigurationResponse>(`/api/v1/configurations/${id}`);
    }

    async createConfiguration(
        data: ConfigurationCreate
    ): Promise<ConfigurationResponse> {
        return this.request<ConfigurationResponse>('/api/v1/configurations', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateConfiguration(
        id: string,
        data: ConfigurationUpdate
    ): Promise<ConfigurationResponse> {
        return this.request<ConfigurationResponse>(`/api/v1/configurations/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }
}
