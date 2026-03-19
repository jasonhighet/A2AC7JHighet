import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ConfigClient } from './client';
import { ConfigNotFoundError, ConfigConflictError } from './errors';

describe('ConfigClient', () => {
    const baseUrl = 'http://api.example.com';
    let client: ConfigClient;

    beforeEach(() => {
        client = new ConfigClient(baseUrl);
        vi.stubGlobal('fetch', vi.fn());
    });

    describe('listApplications', () => {
        it('should fetch applications and return them', async () => {
            const mockApps = [{ id: '1', name: 'App 1', comments: null }];
            vi.mocked(fetch).mockResolvedValue({
                ok: true,
                json: async () => mockApps,
            } as Response);

            const result = await client.listApplications();

            expect(fetch).toHaveBeenCalledWith(`${baseUrl}/api/v1/applications`, expect.any(Object));
            expect(result).toEqual(mockApps);
        });

        it('should throw ConfigNotFoundError on 404', async () => {
            vi.mocked(fetch).mockResolvedValue({
                ok: false,
                status: 404,
                json: async () => ({ detail: 'Not Found' }),
            } as Response);

            await expect(client.listApplications()).rejects.toThrow(ConfigNotFoundError);
        });
    });

    describe('createApplication', () => {
        it('should send a POST request with the correct body', async () => {
            const newApp = { name: 'New App' };
            const responseApp = { id: '2', ...newApp, comments: null };

            vi.mocked(fetch).mockResolvedValue({
                ok: true,
                status: 201,
                json: async () => responseApp,
            } as Response);

            const result = await client.createApplication(newApp);

            expect(fetch).toHaveBeenCalledWith(
                `${baseUrl}/api/v1/applications`,
                expect.objectContaining({
                    method: 'POST',
                    body: JSON.stringify(newApp),
                })
            );
            expect(result).toEqual(responseApp);
        });

        it('should throw ConfigConflictError on 409', async () => {
            vi.mocked(fetch).mockResolvedValue({
                ok: false,
                status: 409,
                json: async () => ({ detail: 'Already exists' }),
            } as Response);

            await expect(client.createApplication({ name: 'Dup' })).rejects.toThrow(ConfigConflictError);
        });
    });
});
