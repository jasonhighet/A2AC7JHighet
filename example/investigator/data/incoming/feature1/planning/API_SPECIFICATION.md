# API Specification: Maintenance Scheduling & Alert System

## Base URL
```
https://api.communityshare.io/api/maintenance
```

## Authentication
All endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Rate Limiting
- 100 requests per minute per user
- Rate limit headers included in all responses:
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

## Common Response Codes
- `200 OK`: Successful GET/PATCH request
- `201 Created`: Successful POST request
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

## Endpoints

### 1. Create Maintenance Schedule

**POST** `/schedules`

Create a new maintenance schedule for a resource.

**Authorization**: Requires `admin` or `maintenance_coordinator` role

**Request Body**:
```json
{
  "resource_id": "550e8400-e29b-41d4-a716-446655440000",
  "schedule_type": "inspection",
  "frequency": "monthly",
  "start_date": "2025-10-15T00:00:00Z",
  "description": "Monthly safety inspection of basketball court",
  "assigned_to": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

**Request Schema**:
- `resource_id` (string, required): UUID of the resource
- `schedule_type` (string, required): Type of maintenance. One of: `inspection`, `cleaning`, `repair`, `replacement`, `other`
- `frequency` (string, required): How often maintenance occurs. One of: `one-time`, `daily`, `weekly`, `monthly`, `quarterly`, `annually`
- `start_date` (string, required): ISO 8601 datetime for first occurrence
- `description` (string, optional): Detailed description of maintenance tasks (max 1000 chars)
- `assigned_to` (string, optional): UUID of user assigned to perform maintenance

**Success Response (201 Created)**:
```json
{
  "id": "a3d8f6c9-42b1-4e8f-9a2c-1d5e7f8b9c0d",
  "resource_id": "550e8400-e29b-41d4-a716-446655440000",
  "schedule_type": "inspection",
  "frequency": "monthly",
  "start_date": "2025-10-15T00:00:00Z",
  "next_due_date": "2025-11-15T00:00:00Z",
  "description": "Monthly safety inspection of basketball court",
  "assigned_to": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "created_at": "2025-10-16T10:30:00Z",
  "updated_at": "2025-10-16T10:30:00Z",
  "deleted_at": null
}
```

**Error Responses**:
```json
// 400 Bad Request - Invalid frequency
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid frequency value. Must be one of: one-time, daily, weekly, monthly, quarterly, annually",
  "field": "frequency"
}

// 403 Forbidden - User doesn't own resource
{
  "error": "FORBIDDEN",
  "message": "You do not have permission to create schedules for this resource"
}

// 404 Not Found - Resource doesn't exist
{
  "error": "RESOURCE_NOT_FOUND",
  "message": "Resource with id 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

---

### 2. Get Maintenance Schedules

**GET** `/schedules`

Retrieve a list of maintenance schedules with optional filtering.

**Authorization**: Requires authentication. Returns schedules for resources user has access to.

**Query Parameters**:
- `resource_id` (string, optional): Filter by resource UUID
- `assigned_to` (string, optional): Filter by assigned user UUID
- `status` (string, optional): Filter by status. One of: `active`, `overdue`, `completed`, `deleted`
- `frequency` (string, optional): Filter by frequency
- `limit` (integer, optional): Number of results per page (default: 50, max: 100)
- `offset` (integer, optional): Number of results to skip (default: 0)
- `sort_by` (string, optional): Field to sort by (default: `next_due_date`)
- `sort_order` (string, optional): `asc` or `desc` (default: `asc`)

**Example Request**:
```
GET /schedules?resource_id=550e8400-e29b-41d4-a716-446655440000&status=active&limit=20
```

**Success Response (200 OK)**:
```json
{
  "data": [
    {
      "id": "a3d8f6c9-42b1-4e8f-9a2c-1d5e7f8b9c0d",
      "resource_id": "550e8400-e29b-41d4-a716-446655440000",
      "schedule_type": "inspection",
      "frequency": "monthly",
      "start_date": "2025-10-15T00:00:00Z",
      "next_due_date": "2025-11-15T00:00:00Z",
      "description": "Monthly safety inspection",
      "assigned_to": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "assigned_to_name": "Bob Martinez",
      "resource_name": "Basketball Court #3",
      "created_at": "2025-10-16T10:30:00Z",
      "updated_at": "2025-10-16T10:30:00Z",
      "deleted_at": null
    }
  ],
  "pagination": {
    "total": 42,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

---

### 3. Get Single Maintenance Schedule

**GET** `/schedules/:id`

Retrieve a specific maintenance schedule by ID.

**Authorization**: Requires authentication. User must have access to the associated resource.

**Path Parameters**:
- `id` (string, required): UUID of the maintenance schedule

**Success Response (200 OK)**:
```json
{
  "id": "a3d8f6c9-42b1-4e8f-9a2c-1d5e7f8b9c0d",
  "resource_id": "550e8400-e29b-41d4-a716-446655440000",
  "schedule_type": "inspection",
  "frequency": "monthly",
  "start_date": "2025-10-15T00:00:00Z",
  "next_due_date": "2025-11-15T00:00:00Z",
  "description": "Monthly safety inspection of basketball court including: check court surface for cracks, inspect safety equipment, test lighting",
  "assigned_to": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "assigned_to_name": "Bob Martinez",
  "assigned_to_email": "bob.martinez@example.com",
  "resource_name": "Basketball Court #3",
  "resource_location": "Main Facility, Building A",
  "created_at": "2025-10-16T10:30:00Z",
  "updated_at": "2025-10-16T10:30:00Z",
  "deleted_at": null,
  "recent_logs": [
    {
      "id": "f8e3d2c1-9b0a-4f5e-8d7c-6b5a4f3e2d1c",
      "performed_at": "2025-10-15T14:30:00Z",
      "performed_by_name": "Bob Martinez",
      "issues_found": "none"
    }
  ]
}
```

**Error Response**:
```json
// 404 Not Found
{
  "error": "SCHEDULE_NOT_FOUND",
  "message": "Maintenance schedule with id a3d8f6c9-42b1-4e8f-9a2c-1d5e7f8b9c0d not found"
}
```

---

### 4. Update Maintenance Schedule

**PATCH** `/schedules/:id`

Update an existing maintenance schedule. Only provided fields will be updated.

**Authorization**: Requires `admin` role or must be the schedule creator

**Path Parameters**:
- `id` (string, required): UUID of the maintenance schedule

**Request Body** (all fields optional):
```json
{
  "schedule_type": "repair",
  "frequency": "quarterly",
  "description": "Quarterly deep cleaning and repairs",
  "assigned_to": "8d7c6b5a-4f3e-2d1c-0b9a-8f7e6d5c4b3a"
}
```

**Success Response (200 OK)**:
```json
{
  "id": "a3d8f6c9-42b1-4e8f-9a2c-1d5e7f8b9c0d",
  "resource_id": "550e8400-e29b-41d4-a716-446655440000",
  "schedule_type": "repair",
  "frequency": "quarterly",
  "start_date": "2025-10-15T00:00:00Z",
  "next_due_date": "2026-01-15T00:00:00Z",
  "description": "Quarterly deep cleaning and repairs",
  "assigned_to": "8d7c6b5a-4f3e-2d1c-0b9a-8f7e6d5c4b3a",
  "created_at": "2025-10-16T10:30:00Z",
  "updated_at": "2025-10-16T11:45:00Z",
  "deleted_at": null
}
```

**Error Response**:
```json
// 403 Forbidden
{
  "error": "FORBIDDEN",
  "message": "You do not have permission to update this schedule"
}
```

---

### 5. Delete Maintenance Schedule

**DELETE** `/schedules/:id`

Soft delete a maintenance schedule. Schedule is marked as deleted but retained for audit purposes.

**Authorization**: Requires `admin` role or must be the schedule creator

**Path Parameters**:
- `id` (string, required): UUID of the maintenance schedule

**Success Response (204 No Content)**:
No response body

**Error Response**:
```json
// 404 Not Found
{
  "error": "SCHEDULE_NOT_FOUND",
  "message": "Maintenance schedule with id a3d8f6c9-42b1-4e8f-9a2c-1d5e7f8b9c0d not found"
}
```

---

### 6. Create Maintenance Log

**POST** `/logs`

Log completion of a maintenance task.

**Authorization**: Requires `admin` or `maintenance_coordinator` role

**Request Body**:
```json
{
  "schedule_id": "a3d8f6c9-42b1-4e8f-9a2c-1d5e7f8b9c0d",
  "resource_id": "550e8400-e29b-41d4-a716-446655440000",
  "performed_at": "2025-10-15T14:30:00Z",
  "notes": "Completed monthly inspection. Found minor crack in southeast corner that needs monitoring. All safety equipment functional.",
  "photos": [
    "https://s3.amazonaws.com/communityshare/maintenance/photo1.jpg",
    "https://s3.amazonaws.com/communityshare/maintenance/photo2.jpg"
  ],
  "issues_found": "minor"
}
```

**Request Schema**:
- `schedule_id` (string, required): UUID of the maintenance schedule (if completing scheduled maintenance)
- `resource_id` (string, required): UUID of the resource
- `performed_at` (string, required): ISO 8601 datetime when maintenance was performed
- `notes` (string, required): Detailed notes about the maintenance performed (max 5000 chars)
- `photos` (array of strings, optional): Array of S3 URLs for uploaded photos
- `issues_found` (string, required): One of: `none`, `minor`, `major`

**Success Response (201 Created)**:
```json
{
  "id": "f8e3d2c1-9b0a-4f5e-8d7c-6b5a4f3e2d1c",
  "schedule_id": "a3d8f6c9-42b1-4e8f-9a2c-1d5e7f8b9c0d",
  "resource_id": "550e8400-e29b-41d4-a716-446655440000",
  "performed_by": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "performed_at": "2025-10-15T14:30:00Z",
  "notes": "Completed monthly inspection. Found minor crack in southeast corner that needs monitoring.",
  "photos": [
    "https://s3.amazonaws.com/communityshare/maintenance/photo1.jpg",
    "https://s3.amazonaws.com/communityshare/maintenance/photo2.jpg"
  ],
  "issues_found": "minor",
  "created_at": "2025-10-15T14:35:00Z",
  "updated_at": "2025-10-15T14:35:00Z"
}
```

**Note**: When a log is created for a schedule, the schedule's `next_due_date` is automatically updated based on the frequency.

---

### 7. Get Maintenance Logs

**GET** `/logs`

Retrieve maintenance logs with optional filtering.

**Authorization**: Requires authentication. Returns logs for resources user has access to.

**Query Parameters**:
- `resource_id` (string, optional): Filter by resource UUID
- `schedule_id` (string, optional): Filter by schedule UUID
- `performed_by` (string, optional): Filter by user UUID who performed maintenance
- `date_from` (string, optional): ISO 8601 date to filter logs from
- `date_to` (string, optional): ISO 8601 date to filter logs to
- `issues_found` (string, optional): Filter by issues found: `none`, `minor`, `major`
- `limit` (integer, optional): Number of results per page (default: 50, max: 100)
- `offset` (integer, optional): Number of results to skip (default: 0)
- `sort_by` (string, optional): Field to sort by (default: `performed_at`)
- `sort_order` (string, optional): `asc` or `desc` (default: `desc`)

**Example Request**:
```
GET /logs?resource_id=550e8400-e29b-41d4-a716-446655440000&date_from=2025-09-01&limit=10
```

**Success Response (200 OK)**:
```json
{
  "data": [
    {
      "id": "f8e3d2c1-9b0a-4f5e-8d7c-6b5a4f3e2d1c",
      "schedule_id": "a3d8f6c9-42b1-4e8f-9a2c-1d5e7f8b9c0d",
      "resource_id": "550e8400-e29b-41d4-a716-446655440000",
      "resource_name": "Basketball Court #3",
      "performed_by": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "performed_by_name": "Bob Martinez",
      "performed_at": "2025-10-15T14:30:00Z",
      "notes": "Completed monthly inspection. Found minor crack in southeast corner.",
      "photos": [
        "https://s3.amazonaws.com/communityshare/maintenance/photo1.jpg",
        "https://s3.amazonaws.com/communityshare/maintenance/photo2.jpg"
      ],
      "issues_found": "minor",
      "created_at": "2025-10-15T14:35:00Z"
    }
  ],
  "pagination": {
    "total": 156,
    "limit": 10,
    "offset": 0,
    "has_more": true
  }
}
```

---

### 8. Get Single Maintenance Log

**GET** `/logs/:id`

Retrieve a specific maintenance log by ID.

**Authorization**: Requires authentication. User must have access to the associated resource.

**Path Parameters**:
- `id` (string, required): UUID of the maintenance log

**Success Response (200 OK)**:
```json
{
  "id": "f8e3d2c1-9b0a-4f5e-8d7c-6b5a4f3e2d1c",
  "schedule_id": "a3d8f6c9-42b1-4e8f-9a2c-1d5e7f8b9c0d",
  "schedule_type": "inspection",
  "resource_id": "550e8400-e29b-41d4-a716-446655440000",
  "resource_name": "Basketball Court #3",
  "resource_location": "Main Facility, Building A",
  "performed_by": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "performed_by_name": "Bob Martinez",
  "performed_by_email": "bob.martinez@example.com",
  "performed_at": "2025-10-15T14:30:00Z",
  "notes": "Completed monthly inspection. Found minor crack in southeast corner that needs monitoring. All safety equipment functional. Lighting systems tested and working properly.",
  "photos": [
    {
      "url": "https://s3.amazonaws.com/communityshare/maintenance/photo1.jpg",
      "uploaded_at": "2025-10-15T14:32:00Z",
      "size_bytes": 2458234
    },
    {
      "url": "https://s3.amazonaws.com/communityshare/maintenance/photo2.jpg",
      "uploaded_at": "2025-10-15T14:33:00Z",
      "size_bytes": 1932847
    }
  ],
  "issues_found": "minor",
  "created_at": "2025-10-15T14:35:00Z",
  "updated_at": "2025-10-15T14:35:00Z"
}
```

---

## Error Handling

### Standard Error Response Format
All errors follow this structure:
```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "field": "field_name",  // Optional: included for validation errors
  "details": {}  // Optional: additional error context
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Request data failed validation
- `AUTHENTICATION_REQUIRED`: Missing or invalid JWT token
- `FORBIDDEN`: User lacks required permissions
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `SCHEDULE_NOT_FOUND`: Maintenance schedule not found
- `LOG_NOT_FOUND`: Maintenance log not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_SERVER_ERROR`: Unexpected server error

---

## Webhooks (Future Enhancement)

*Not implemented in v1.0. Planned for future release.*

Webhooks will allow external systems to receive real-time notifications when maintenance events occur:
- Schedule created/updated/deleted
- Maintenance logged
- Alert generated

---

## Versioning

API version is included in the URL path:
```
https://api.communityshare.io/v1/maintenance/schedules
```

Current version: `v1`

Breaking changes will result in a new API version. Non-breaking changes (new optional fields, new endpoints) will be added to existing versions.

---

## SDK Examples

### JavaScript/Node.js
```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'https://api.communityshare.io/api/maintenance',
  headers: {
    'Authorization': `Bearer ${process.env.JWT_TOKEN}`,
    'Content-Type': 'application/json'
  }
});

// Create maintenance schedule
const schedule = await api.post('/schedules', {
  resource_id: '550e8400-e29b-41d4-a716-446655440000',
  schedule_type: 'inspection',
  frequency: 'monthly',
  start_date: '2025-10-15T00:00:00Z',
  description: 'Monthly safety inspection'
});

// Get schedules for a resource
const schedules = await api.get('/schedules', {
  params: { resource_id: '550e8400-e29b-41d4-a716-446655440000' }
});

// Log completed maintenance
const log = await api.post('/logs', {
  schedule_id: schedule.data.id,
  resource_id: '550e8400-e29b-41d4-a716-446655440000',
  performed_at: new Date().toISOString(),
  notes: 'Inspection completed successfully',
  issues_found: 'none'
});
```

### Python
```python
import requests
from datetime import datetime

BASE_URL = 'https://api.communityshare.io/api/maintenance'
headers = {
    'Authorization': f'Bearer {os.getenv("JWT_TOKEN")}',
    'Content-Type': 'application/json'
}

# Create maintenance schedule
schedule = requests.post(
    f'{BASE_URL}/schedules',
    headers=headers,
    json={
        'resource_id': '550e8400-e29b-41d4-a716-446655440000',
        'schedule_type': 'inspection',
        'frequency': 'monthly',
        'start_date': '2025-10-15T00:00:00Z',
        'description': 'Monthly safety inspection'
    }
)

# Get schedules
schedules = requests.get(
    f'{BASE_URL}/schedules',
    headers=headers,
    params={'resource_id': '550e8400-e29b-41d4-a716-446655440000'}
)

# Log maintenance
log = requests.post(
    f'{BASE_URL}/logs',
    headers=headers,
    json={
        'schedule_id': schedule.json()['id'],
        'resource_id': '550e8400-e29b-41d4-a716-446655440000',
        'performed_at': datetime.utcnow().isoformat(),
        'notes': 'Inspection completed successfully',
        'issues_found': 'none'
    }
)
```
