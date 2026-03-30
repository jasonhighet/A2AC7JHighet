export class ConfigApiError extends Error {
    constructor(
        public message: string,
        public statusCode?: number,
        public detail?: any
    ) {
        super(message);
        this.name = 'ConfigApiError';
    }
}

export class ConfigNotFoundError extends ConfigApiError {
    constructor(id: string, resource: string) {
        super(`${resource} with ID ${id} not found`, 404);
        this.name = 'ConfigNotFoundError';
    }
}

export class ConfigValidationError extends ConfigApiError {
    constructor(detail: any) {
        super('Validation error', 422, detail);
        this.name = 'ConfigValidationError';
    }
}

export class ConfigConflictError extends ConfigApiError {
    constructor(message: string) {
        super(message, 409);
        this.name = 'ConfigConflictError';
    }
}
