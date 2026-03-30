# API Specification: QR Code Check-in/out

## Feature ID
FEAT-QR-002

## Base URL
```
Production: https://api.communityshare.io/v1
Staging: https://api-staging.communityshare.io/v1
Development: http://localhost:3000/api/v1
```

## Authentication
All API endpoints require JWT authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## New REST Endpoints

### 1. Generate QR Code

**Endpoint**: `POST /api/resources/:id/qr-code`

**Description**: Generates a unique, time-limited QR code for a resource.

**Path Parameters**:
- `id` (UUID, required): Resource ID

**Request Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body**: None

**Success Response (201 Created)**:
```json
{
  "success": true,
  "data": {
    "qr_code_id": "550e8400-e29b-41d4-a716-446655440000",
    "resource_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "token": "eyJyZXNvdXJjZV9pZCI6Ijdj...",
    "qr_image_url": "https://api.communityshare.io/qr/550e8400...",
    "qr_data_url": "data:image/png;base64,iVBORw0KGgo...",
    "expires_at": "2025-10-16T15:30:00Z",
    "created_at": "2025-10-16T15:15:00Z"
  }
}
```

**Error Responses**:

*401 Unauthorized*:
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired authentication token"
  }
}
```

*403 Forbidden*:
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to generate QR codes for this resource"
  }
}
```

*404 Not Found*:
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Resource with ID 7c9e6679-7425-40de-944b-e07fc1f90ae7 not found"
  }
}
```

*429 Too Many Requests*:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Maximum 10 QR code generations per minute exceeded",
    "retry_after": 45
  }
}
```

**Rate Limit**: 10 requests per minute per user

**Example Request**:
```bash
curl -X POST \
  https://api.communityshare.io/v1/resources/7c9e6679-7425-40de-944b-e07fc1f90ae7/qr-code \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json'
```

---

### 2. Validate and Scan QR Code

**Endpoint**: `POST /api/checkin/scan`

**Description**: Validates a QR token and initiates a check-in or check-out operation.

**Request Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "token": "eyJyZXNvdXJjZV9pZCI6Ijdj...",
  "action": "checkout",  // "checkout" or "checkin"
  "device_info": {
    "device_id": "550e8400-e29b-41d4-a716-446655440001",
    "platform": "ios",  // "ios" or "android"
    "app_version": "1.0.0"
  }
}
```

**Request Schema**:
```typescript
interface ScanRequest {
  token: string;                    // Required: Base64-encoded QR token
  action: 'checkout' | 'checkin';   // Required: Desired action
  device_info?: {                   // Optional: Device information
    device_id?: string;             // Device UUID
    platform?: 'ios' | 'android';   // Platform
    app_version?: string;           // App version
  };
}
```

**Success Response (200 OK)**:

*Checkout Success*:
```json
{
  "success": true,
  "data": {
    "checkout_id": "9a8e7890-e29b-41d4-a716-446655440002",
    "resource": {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "name": "Milwaukee Drill Press",
      "model": "DP-4550",
      "image_url": "https://cdn.communityshare.io/resources/drill-press.jpg"
    },
    "checked_out_by": {
      "id": "1234567890",
      "name": "John Doe",
      "email": "john.doe@example.com"
    },
    "checked_out_at": "2025-10-16T15:20:00Z",
    "due_at": "2025-10-23T15:20:00Z",
    "checkout_method": "qr"
  }
}
```

*Check-in Success*:
```json
{
  "success": true,
  "data": {
    "checkout_id": "9a8e7890-e29b-41d4-a716-446655440002",
    "resource": {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "name": "Milwaukee Drill Press",
      "model": "DP-4550"
    },
    "checked_in_at": "2025-10-18T10:30:00Z",
    "duration_hours": 42.5
  }
}
```

**Error Responses**:

*400 Bad Request*:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid request body",
    "details": [
      {
        "field": "token",
        "message": "Token is required"
      }
    ]
  }
}
```

*401 Unauthorized*:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_TOKEN",
    "message": "QR token is invalid or has been tampered with"
  }
}
```

*403 Forbidden*:
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_UNAVAILABLE",
    "message": "Resource is already checked out by another member"
  }
}
```

*410 Gone*:
```json
{
  "success": false,
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "QR token has expired. Please generate a new QR code.",
    "expired_at": "2025-10-16T15:00:00Z"
  }
}
```

*409 Conflict*:
```json
{
  "success": false,
  "error": {
    "code": "TOKEN_ALREADY_USED",
    "message": "This QR code has already been scanned and cannot be reused"
  }
}
```

*429 Too Many Requests*:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Maximum 10 scans per minute exceeded",
    "retry_after": 30
  }
}
```

**Rate Limit**: 10 requests per minute per user

**Example Request**:
```bash
curl -X POST \
  https://api.communityshare.io/v1/checkin/scan \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'Content-Type: application/json' \
  -d '{
    "token": "eyJyZXNvdXJjZV9pZCI6Ijdj...",
    "action": "checkout",
    "device_info": {
      "device_id": "550e8400-e29b-41d4-a716-446655440001",
      "platform": "ios",
      "app_version": "1.0.0"
    }
  }'
```

---

### 3. Get Checkout Status (Real-time)

**Endpoint**: `GET /api/checkin/status/:checkout_id`

**Description**: Retrieves the current status of a checkout operation. Used for polling when WebSocket is unavailable.

**Path Parameters**:
- `checkout_id` (UUID, required): Checkout ID

**Request Headers**:
```
Authorization: Bearer <jwt_token>
```

**Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "checkout_id": "9a8e7890-e29b-41d4-a716-446655440002",
    "status": "active",  // "active", "completed", "overdue"
    "resource": {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "name": "Milwaukee Drill Press",
      "availability": "checked_out"
    },
    "checked_out_at": "2025-10-16T15:20:00Z",
    "due_at": "2025-10-23T15:20:00Z",
    "checked_in_at": null
  }
}
```

**Error Responses**:

*404 Not Found*:
```json
{
  "success": false,
  "error": {
    "code": "CHECKOUT_NOT_FOUND",
    "message": "Checkout with ID 9a8e7890-e29b-41d4-a716-446655440002 not found"
  }
}
```

**Rate Limit**: 60 requests per minute per user (higher limit for polling)

---

## WebSocket Events

### Connection

**Connection URL**: `wss://api.communityshare.io/v1/ws`

**Authentication**: JWT token passed in handshake
```javascript
const socket = io('wss://api.communityshare.io/v1/ws', {
  auth: {
    token: '<jwt_token>'
  }
});
```

**Connection Events**:

*Client → Server*:
- `connection`: Initial connection (automatic)
- `disconnect`: Disconnection (automatic)
- `ping`: Keepalive heartbeat (automatic, every 25s)

*Server → Client*:
- `authenticated`: Connection authenticated successfully
- `auth_error`: Authentication failed
- `pong`: Keepalive response (automatic)

---

### Subscribe to Resource Updates

**Event**: `subscribe_resource`

**Client → Server**:
```javascript
socket.emit('subscribe_resource', {
  resource_id: '7c9e6679-7425-40de-944b-e07fc1f90ae7'
});
```

**Server → Client (Acknowledgment)**:
```javascript
{
  "success": true,
  "resource_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "current_availability": "available"
}
```

---

### Resource Availability Changed

**Event**: `resource_availability_changed`

**Server → Client** (broadcast to all subscribers):
```javascript
{
  "event": "resource_availability_changed",
  "data": {
    "resource_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "previous_availability": "available",
    "current_availability": "checked_out",
    "changed_at": "2025-10-16T15:20:00Z",
    "changed_by": {
      "id": "1234567890",
      "name": "John Doe"
    }
  }
}
```

---

### Checkout Completed

**Event**: `checkout_completed`

**Server → Client** (to user who performed checkout):
```javascript
{
  "event": "checkout_completed",
  "data": {
    "checkout_id": "9a8e7890-e29b-41d4-a716-446655440002",
    "resource": {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "name": "Milwaukee Drill Press"
    },
    "checked_out_at": "2025-10-16T15:20:00Z",
    "due_at": "2025-10-23T15:20:00Z"
  }
}
```

---

### Check-in Completed

**Event**: `checkin_completed`

**Server → Client** (to user who performed check-in):
```javascript
{
  "event": "checkin_completed",
  "data": {
    "checkout_id": "9a8e7890-e29b-41d4-a716-446655440002",
    "resource": {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "name": "Milwaukee Drill Press"
    },
    "checked_in_at": "2025-10-18T10:30:00Z",
    "duration_hours": 42.5
  }
}
```

---

### Error Event

**Event**: `error`

**Server → Client**:
```javascript
{
  "event": "error",
  "data": {
    "code": "WEBSOCKET_ERROR",
    "message": "Failed to subscribe to resource updates",
    "details": {
      "resource_id": "invalid-uuid"
    }
  }
}
```

---

## Request/Response Schemas

### QR Token Structure (Internal)
```typescript
interface QRToken {
  resource_id: string;        // UUID
  nonce: string;              // Random 16-byte hex string
  expires_at: string;         // ISO 8601 timestamp
  signature: string;          // HMAC-SHA256 signature
}
```

### Device Info Schema
```typescript
interface DeviceInfo {
  device_id?: string;         // Device UUID
  platform?: 'ios' | 'android';
  app_version?: string;       // Semantic version (e.g., "1.0.0")
}
```

---

## Error Codes Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing authentication token |
| `FORBIDDEN` | 403 | User lacks permission for this operation |
| `RESOURCE_NOT_FOUND` | 404 | Resource does not exist |
| `CHECKOUT_NOT_FOUND` | 404 | Checkout does not exist |
| `INVALID_TOKEN` | 401 | QR token is invalid or tampered |
| `TOKEN_EXPIRED` | 410 | QR token has expired |
| `TOKEN_ALREADY_USED` | 409 | QR token has already been used |
| `RESOURCE_UNAVAILABLE` | 403 | Resource is checked out by another user |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INVALID_REQUEST` | 400 | Malformed request body |
| `WEBSOCKET_ERROR` | N/A | WebSocket operation failed |

---

## API Versioning

**Current Version**: v1

**Deprecation Policy**: Endpoints deprecated with 6-month notice. Breaking changes introduce new versions.

**Version Header** (optional):
```
X-API-Version: 1
```

---

## Rate Limiting

**Default Limits**:
- General API: 100 requests per minute per user
- QR Generation: 10 requests per minute per user
- QR Scanning: 10 requests per minute per user
- Status Polling: 60 requests per minute per user

**Rate Limit Headers** (included in all responses):
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1697462400
```

---

## Testing Endpoints

**Staging Environment**:
```
https://api-staging.communityshare.io/v1
```

**Test Credentials**: Available in staging documentation

**Test QR Code Generation**: Use test resource IDs:
- `test-resource-001`: Always succeeds
- `test-resource-002`: Simulates expired token
- `test-resource-003`: Simulates already used token
