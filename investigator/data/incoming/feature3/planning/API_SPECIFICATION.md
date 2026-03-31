# API Specification: Advanced Resource Reservation System

## Base URL
```
Production: https://api.communityshare.io/v1
Staging: https://api-staging.communityshare.io/v1
Development: http://localhost:3000/api/v1
```

## Authentication
All endpoints require authentication via JWT bearer token.

```http
Authorization: Bearer <jwt_token>
```

## Common Headers
```http
Content-Type: application/json
Accept: application/json
X-Request-ID: <uuid>  (optional, for tracking)
```

## Datetime Format
All datetime values use ISO 8601 format with timezone information:
```
2025-10-17T14:00:00-07:00  (Pacific Daylight Time)
2025-10-17T21:00:00Z        (UTC)
```

## API Endpoints

### 1. Create Reservation

Create a new resource reservation.

```http
POST /api/reservations
```

**Request Body:**
```json
{
  "resourceId": 42,
  "startTime": "2025-10-17T14:00:00-07:00",
  "endTime": "2025-10-17T16:00:00-07:00",
  "purpose": "Weekly pottery class",
  "specialRequirements": "Need 10 chairs set up"
}
```

**Field Validation:**
- `resourceId` (required): Integer, must reference valid resource
- `startTime` (required): ISO 8601 datetime, must be in future, max 30 days ahead
- `endTime` (required): ISO 8601 datetime, must be after startTime
- `purpose` (required): String, 10-500 characters
- `specialRequirements` (optional): String, max 1000 characters

**Success Response (201 Created):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "resourceId": 42,
  "resourceName": "Workshop Space",
  "userId": 789,
  "userName": "Jane Smith",
  "startTime": "2025-10-17T14:00:00-07:00",
  "endTime": "2025-10-17T16:00:00-07:00",
  "status": "CONFIRMED",
  "purpose": "Weekly pottery class",
  "specialRequirements": "Need 10 chairs set up",
  "priority": false,
  "createdAt": "2025-10-16T10:30:00-07:00",
  "updatedAt": "2025-10-16T10:30:00-07:00"
}
```

**Error Responses:**

*400 Bad Request - Validation Error*
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid request data",
  "details": [
    {
      "field": "startTime",
      "message": "Start time must be in the future"
    },
    {
      "field": "purpose",
      "message": "Purpose must be between 10 and 500 characters"
    }
  ]
}
```

*409 Conflict - Time Slot Unavailable*
```json
{
  "error": "TIME_SLOT_UNAVAILABLE",
  "message": "The requested time conflicts with an existing reservation",
  "conflictingReservation": {
    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "startTime": "2025-10-17T13:00:00-07:00",
    "endTime": "2025-10-17T17:00:00-07:00"
  },
  "alternatives": [
    {
      "startTime": "2025-10-17T11:00:00-07:00",
      "endTime": "2025-10-17T13:00:00-07:00"
    },
    {
      "startTime": "2025-10-17T17:00:00-07:00",
      "endTime": "2025-10-17T19:00:00-07:00"
    }
  ],
  "waitlistAvailable": true
}
```

*403 Forbidden - Max Concurrent Reservations*
```json
{
  "error": "MAX_RESERVATIONS_EXCEEDED",
  "message": "You have reached the maximum number of concurrent reservations (5)",
  "currentReservations": 5
}
```

*404 Not Found - Resource Not Found*
```json
{
  "error": "RESOURCE_NOT_FOUND",
  "message": "Resource with ID 42 does not exist",
  "resourceId": 42
}
```

### 2. Get Reservations

Retrieve reservations for the authenticated user.

```http
GET /api/reservations
```

**Query Parameters:**
- `status` (optional): Filter by status (PENDING, CONFIRMED, ACTIVE, COMPLETED, NO_SHOW, CANCELLED)
- `startDate` (optional): ISO 8601 date, filter reservations starting on or after this date
- `endDate` (optional): ISO 8601 date, filter reservations ending on or before this date
- `resourceId` (optional): Filter by specific resource
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Results per page (default: 20, max: 100)
- `sort` (optional): Sort field (startTime, createdAt), prefix with - for descending (default: startTime)

**Example Request:**
```http
GET /api/reservations?status=CONFIRMED&startDate=2025-10-15&sort=-startTime&limit=50
```

**Success Response (200 OK):**
```json
{
  "reservations": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "resourceId": 42,
      "resourceName": "Workshop Space",
      "startTime": "2025-10-17T14:00:00-07:00",
      "endTime": "2025-10-17T16:00:00-07:00",
      "status": "CONFIRMED",
      "purpose": "Weekly pottery class",
      "createdAt": "2025-10-16T10:30:00-07:00"
    },
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "resourceId": 15,
      "resourceName": "3D Printer",
      "startTime": "2025-10-18T09:00:00-07:00",
      "endTime": "2025-10-18T13:00:00-07:00",
      "status": "CONFIRMED",
      "purpose": "Print prototype parts",
      "createdAt": "2025-10-14T15:22:00-07:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 2,
    "totalPages": 1
  }
}
```

### 3. Get Reservation Details

Retrieve details for a specific reservation.

```http
GET /api/reservations/:id
```

**Success Response (200 OK):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "resourceId": 42,
  "resourceName": "Workshop Space",
  "resourceDescription": "Main community workshop area",
  "userId": 789,
  "userName": "Jane Smith",
  "userEmail": "jane.smith@example.com",
  "startTime": "2025-10-17T14:00:00-07:00",
  "endTime": "2025-10-17T16:00:00-07:00",
  "status": "CONFIRMED",
  "purpose": "Weekly pottery class",
  "specialRequirements": "Need 10 chairs set up",
  "priority": false,
  "createdAt": "2025-10-16T10:30:00-07:00",
  "updatedAt": "2025-10-16T10:30:00-07:00",
  "checkedInAt": null,
  "checkedOutAt": null
}
```

**Error Response:**

*404 Not Found*
```json
{
  "error": "RESERVATION_NOT_FOUND",
  "message": "Reservation with ID a1b2c3d4-e5f6-7890-abcd-ef1234567890 does not exist",
  "reservationId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

*403 Forbidden - Not Owner*
```json
{
  "error": "FORBIDDEN",
  "message": "You do not have permission to view this reservation"
}
```

### 4. Modify Reservation

Update an existing reservation.

```http
PATCH /api/reservations/:id
```

**Request Body:**
```json
{
  "startTime": "2025-10-17T15:00:00-07:00",
  "endTime": "2025-10-17T17:00:00-07:00",
  "purpose": "Updated: Pottery class with demo",
  "specialRequirements": "Need 10 chairs and 1 table"
}
```

**Field Rules:**
- Can only modify reservations in PENDING or CONFIRMED status
- Cannot modify within 24 hours of start time
- All fields optional, only provided fields are updated
- Modification triggers new conflict check

**Success Response (200 OK):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "resourceId": 42,
  "startTime": "2025-10-17T15:00:00-07:00",
  "endTime": "2025-10-17T17:00:00-07:00",
  "status": "CONFIRMED",
  "purpose": "Updated: Pottery class with demo",
  "specialRequirements": "Need 10 chairs and 1 table",
  "updatedAt": "2025-10-16T14:22:00-07:00"
}
```

**Error Responses:**

*409 Conflict - New Time Conflicts*
```json
{
  "error": "TIME_SLOT_UNAVAILABLE",
  "message": "The updated time conflicts with an existing reservation"
}
```

*400 Bad Request - Too Late to Modify*
```json
{
  "error": "MODIFICATION_DEADLINE_PASSED",
  "message": "Reservations cannot be modified within 24 hours of start time",
  "startTime": "2025-10-17T15:00:00-07:00",
  "currentTime": "2025-10-17T10:00:00-07:00"
}
```

### 5. Cancel Reservation

Cancel an existing reservation.

```http
DELETE /api/reservations/:id
```

**Success Response (200 OK):**
```json
{
  "message": "Reservation cancelled successfully",
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "CANCELLED",
  "waitlistNotified": true,
  "nextUserNotified": {
    "userId": 845,
    "userName": "Bob Johnson"
  }
}
```

**Error Response:**

*400 Bad Request - Already Active*
```json
{
  "error": "CANNOT_CANCEL_ACTIVE",
  "message": "Cannot cancel a reservation that is currently active. Please check out first.",
  "status": "ACTIVE"
}
```

### 6. Check for Conflicts

Check if a proposed time slot has conflicts.

```http
GET /api/reservations/conflicts
```

**Query Parameters:**
- `resourceId` (required): Resource to check
- `startTime` (required): ISO 8601 datetime
- `endTime` (required): ISO 8601 datetime
- `excludeReservationId` (optional): Exclude specific reservation (for updates)

**Example Request:**
```http
GET /api/reservations/conflicts?resourceId=42&startTime=2025-10-17T14:00:00-07:00&endTime=2025-10-17T16:00:00-07:00
```

**Success Response (200 OK):**

*No Conflicts:*
```json
{
  "hasConflict": false,
  "available": true
}
```

*With Conflicts:*
```json
{
  "hasConflict": true,
  "available": false,
  "conflicts": [
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "startTime": "2025-10-17T13:00:00-07:00",
      "endTime": "2025-10-17T17:00:00-07:00",
      "overlapType": "CONTAINS"
    }
  ],
  "alternatives": [
    {
      "startTime": "2025-10-17T11:00:00-07:00",
      "endTime": "2025-10-17T13:00:00-07:00"
    },
    {
      "startTime": "2025-10-17T17:00:00-07:00",
      "endTime": "2025-10-17T19:00:00-07:00"
    }
  ]
}
```

### 7. Get Resource Availability

Get calendar availability for a specific resource.

```http
GET /api/resources/:id/availability
```

**Query Parameters:**
- `startDate` (required): ISO 8601 date
- `endDate` (required): ISO 8601 date (max 30 days from startDate)
- `timeSlotMinutes` (optional): Time slot granularity in minutes (default: 30)

**Example Request:**
```http
GET /api/resources/42/availability?startDate=2025-10-17&endDate=2025-10-18&timeSlotMinutes=60
```

**Success Response (200 OK):**
```json
{
  "resourceId": 42,
  "resourceName": "Workshop Space",
  "startDate": "2025-10-17",
  "endDate": "2025-10-18",
  "timeSlotMinutes": 60,
  "availability": [
    {
      "date": "2025-10-17",
      "slots": [
        {
          "startTime": "2025-10-17T09:00:00-07:00",
          "endTime": "2025-10-17T10:00:00-07:00",
          "available": true
        },
        {
          "startTime": "2025-10-17T10:00:00-07:00",
          "endTime": "2025-10-17T11:00:00-07:00",
          "available": true
        },
        {
          "startTime": "2025-10-17T11:00:00-07:00",
          "endTime": "2025-10-17T12:00:00-07:00",
          "available": false,
          "reservationId": "b2c3d4e5-f6a7-8901-bcde-f12345678901"
        }
      ]
    },
    {
      "date": "2025-10-18",
      "slots": [
        // Similar structure for next day
      ]
    }
  ]
}
```

### 8. Join Waitlist

Add user to waitlist for unavailable time slot.

```http
POST /api/reservations/:id/waitlist
```

OR

```http
POST /api/waitlist
```

**Request Body (for POST /api/waitlist):**
```json
{
  "resourceId": 42,
  "requestedStartTime": "2025-10-17T14:00:00-07:00",
  "requestedEndTime": "2025-10-17T16:00:00-07:00"
}
```

**Success Response (201 Created):**
```json
{
  "id": 123,
  "resourceId": 42,
  "resourceName": "Workshop Space",
  "requestedStartTime": "2025-10-17T14:00:00-07:00",
  "requestedEndTime": "2025-10-17T16:00:00-07:00",
  "position": 3,
  "status": "WAITING",
  "estimatedNotificationTime": "2025-10-17T12:00:00-07:00",
  "createdAt": "2025-10-16T10:30:00-07:00"
}
```

**Error Response:**

*400 Bad Request - Already on Waitlist*
```json
{
  "error": "ALREADY_ON_WAITLIST",
  "message": "You are already on the waitlist for this time slot",
  "existingWaitlistId": 122
}
```

### 9. Leave Waitlist

Remove user from waitlist.

```http
DELETE /api/waitlist/:id
```

**Success Response (200 OK):**
```json
{
  "message": "Successfully removed from waitlist",
  "id": 123
}
```

### 10. Get User's Waitlist Positions

Get all waitlist entries for authenticated user.

```http
GET /api/waitlist/my-queue
```

**Success Response (200 OK):**
```json
{
  "waitlistEntries": [
    {
      "id": 123,
      "resourceId": 42,
      "resourceName": "Workshop Space",
      "requestedStartTime": "2025-10-17T14:00:00-07:00",
      "requestedEndTime": "2025-10-17T16:00:00-07:00",
      "position": 3,
      "status": "WAITING",
      "createdAt": "2025-10-16T10:30:00-07:00"
    },
    {
      "id": 124,
      "resourceId": 15,
      "resourceName": "3D Printer",
      "requestedStartTime": "2025-10-18T09:00:00-07:00",
      "requestedEndTime": "2025-10-18T13:00:00-07:00",
      "position": 1,
      "status": "NOTIFIED",
      "notifiedAt": "2025-10-17T08:00:00-07:00",
      "expiresAt": "2025-10-17T10:00:00-07:00",
      "createdAt": "2025-10-15T14:20:00-07:00"
    }
  ]
}
```

## Error Codes

### Standard HTTP Status Codes
- `200 OK`: Successful GET, PATCH, DELETE
- `201 Created`: Successful POST
- `400 Bad Request`: Validation error, business logic violation
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Authenticated but not authorized for this action
- `404 Not Found`: Resource or reservation not found
- `409 Conflict`: Time slot conflict
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Application Error Codes
- `VALIDATION_ERROR`: Invalid request data
- `TIME_SLOT_UNAVAILABLE`: Requested time conflicts with existing reservation
- `MAX_RESERVATIONS_EXCEEDED`: User has too many concurrent reservations
- `RESOURCE_NOT_FOUND`: Resource does not exist
- `RESERVATION_NOT_FOUND`: Reservation does not exist
- `FORBIDDEN`: User not authorized
- `MODIFICATION_DEADLINE_PASSED`: Too late to modify reservation
- `CANNOT_CANCEL_ACTIVE`: Cannot cancel active reservation
- `ALREADY_ON_WAITLIST`: User already on waitlist for this slot
- `INVALID_DATETIME`: Datetime format or timezone error
- `PAST_DATE_ERROR`: Start time is in the past
- `MAX_ADVANCE_EXCEEDED`: Reservation too far in advance (>30 days)
- `INVALID_DURATION`: Duration too short (<30 min) or too long (>8 hours)

## Rate Limits

- **Standard Users**: 100 requests per minute
- **Admin Users**: 500 requests per minute
- **Booking Endpoints**: 10 reservation attempts per hour per user

Rate limit headers included in all responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567890
```

## Webhooks (Future Enhancement)

Webhook support planned for:
- Reservation confirmed
- Reservation cancelled
- Waitlist notification sent
- No-show detected

## API Versioning

Current version: `v1`

Version included in URL path: `/api/v1/reservations`

Breaking changes will result in new version: `/api/v2/reservations`

## API Documentation

Interactive API documentation available at:
- Swagger UI: `https://api.communityshare.io/docs`
- Postman Collection: `https://documenter.getpostman.com/...`

## Changelog

### v1.0.0 (2025-10-09)
- Initial release
- All endpoints documented above

## Support

For API support, contact: api-support@communityshare.io
