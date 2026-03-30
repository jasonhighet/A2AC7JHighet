# API Specification: Contribution Tracking & Community Credits

## Base URL
```
Production: https://api.communityshare.io/v1
UAT: https://uat-api.communityshare.io/v1
Development: http://localhost:3000/api/v1
```

## Authentication
All endpoints require JWT authentication via Bearer token in Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Common Response Codes
- `200 OK`: Successful GET/PATCH request
- `201 Created`: Successful POST request
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

## Contribution Endpoints

### Create Contribution
```http
POST /api/contributions
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body (Item Donation)**:
```json
{
  "type": "item_donation",
  "data": {
    "description": "Camping tent, 4-person Coleman",
    "estimated_value": 50.00,
    "condition": "like_new",
    "photos": ["https://storage.example.com/photo1.jpg"],
    "notes": "Lightly used, all poles included"
  }
}
```

**Request Body (Money)**:
```json
{
  "type": "money",
  "data": {
    "amount": 50.00,
    "currency": "USD",
    "payment_method": "online_transfer",
    "receipt_url": "https://storage.example.com/receipt.jpg",
    "transaction_id": "TXN123456"
  }
}
```

**Request Body (Volunteer Hours)**:
```json
{
  "type": "volunteer_hours",
  "data": {
    "activity": "Community garden maintenance",
    "hours": 3.0,
    "date": "2025-10-15",
    "supervisor": "Jane Smith",
    "notes": "Weeding and planting seasonal vegetables"
  }
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "type": "item_donation",
  "data": {
    "description": "Camping tent, 4-person Coleman",
    "estimated_value": 50.00,
    "condition": "like_new",
    "photos": ["https://storage.example.com/photo1.jpg"],
    "notes": "Lightly used, all poles included"
  },
  "status": "pending",
  "calculated_credits": 5.00,
  "created_at": "2025-10-16T14:32:00Z",
  "updated_at": "2025-10-16T14:32:00Z"
}
```

**Validation Rules**:
- `type`: Required, must be one of: item_donation, money, volunteer_hours
- Item donation:
  - `description`: Required, 10-500 characters
  - `estimated_value`: Required, minimum $10.00
  - `condition`: Required, one of: new, like_new, good, fair
  - `photos`: Optional, max 3 URLs
- Money:
  - `amount`: Required, minimum $5.00
  - `currency`: Optional, defaults to "USD"
  - `payment_method`: Required, one of: cash, check, online_transfer
- Volunteer hours:
  - `activity`: Required, 10-200 characters
  - `hours`: Required, minimum 0.5, maximum 24
  - `date`: Required, cannot be future date

---

### Get User's Contributions
```http
GET /api/contributions?user_id={user_id}&status={status}&limit={limit}&offset={offset}
Authorization: Bearer <token>
```

**Query Parameters**:
- `user_id` (optional): Filter by user ID (if omitted, returns current user's contributions)
- `status` (optional): Filter by status (pending, approved, rejected)
- `type` (optional): Filter by contribution type
- `limit` (optional): Results per page, default 20, max 100
- `offset` (optional): Pagination offset, default 0

**Response** (200 OK):
```json
{
  "contributions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "type": "item_donation",
      "data": {
        "description": "Camping tent, 4-person Coleman",
        "estimated_value": 50.00,
        "condition": "like_new"
      },
      "status": "approved",
      "calculated_credits": 5.00,
      "approved_by": "admin-user-id",
      "approved_at": "2025-10-16T15:00:00Z",
      "created_at": "2025-10-16T14:32:00Z"
    }
  ],
  "pagination": {
    "total": 45,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

---

### Get Single Contribution
```http
GET /api/contributions/{id}
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "user_name": "Alice Johnson",
  "type": "item_donation",
  "data": {
    "description": "Camping tent, 4-person Coleman",
    "estimated_value": 50.00,
    "condition": "like_new",
    "photos": ["https://storage.example.com/photo1.jpg"],
    "notes": "Lightly used, all poles included"
  },
  "status": "approved",
  "calculated_credits": 5.00,
  "approved_by": "admin-user-id",
  "approved_by_name": "Admin User",
  "approved_at": "2025-10-16T15:00:00Z",
  "created_at": "2025-10-16T14:32:00Z",
  "updated_at": "2025-10-16T15:00:00Z"
}
```

---

### Approve Contribution (Admin Only)
```http
PATCH /api/contributions/{id}/approve
Content-Type: application/json
Authorization: Bearer <admin_token>
```

**Request Body**:
```json
{
  "adjusted_credits": 5.00,
  "notes": "Approved as submitted"
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "approved",
  "credits_added": 5.00,
  "user_credit_balance": {
    "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "old_balance": 42.00,
    "new_balance": 47.00,
    "new_tier": "gold"
  },
  "approved_at": "2025-10-16T15:00:00Z"
}
```

---

### Reject Contribution (Admin Only)
```http
PATCH /api/contributions/{id}/reject
Content-Type: application/json
Authorization: Bearer <admin_token>
```

**Request Body**:
```json
{
  "reason": "Estimated value appears too high for item condition"
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "rejected",
  "rejection_reason": "Estimated value appears too high for item condition",
  "rejected_at": "2025-10-16T15:00:00Z"
}
```

---

## Credit Balance Endpoints

### Get Credit Balance
```http
GET /api/contributions/credits/{user_id}
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "balance": 47.00,
  "tier": "gold",
  "tier_info": {
    "current": "gold",
    "current_range": "51-100 credits",
    "next": "platinum",
    "credits_to_next": 53.00
  },
  "breakdown": {
    "item_donations": {
      "count": 15,
      "credits": 28.00,
      "percentage": 60
    },
    "money": {
      "count": 6,
      "credits": 12.00,
      "percentage": 26
    },
    "volunteer_hours": {
      "count": 8,
      "credits": 7.00,
      "percentage": 14
    }
  },
  "last_calculated_at": "2025-10-16T03:00:00Z"
}
```

---

### Get Credit Transaction History
```http
GET /api/contributions/credits/{user_id}/history?limit={limit}&offset={offset}
Authorization: Bearer <token>
```

**Query Parameters**:
- `limit` (optional): Results per page, default 20, max 100
- `offset` (optional): Pagination offset, default 0

**Response** (200 OK):
```json
{
  "transactions": [
    {
      "id": "trans-uuid-1",
      "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "amount": 5.00,
      "balance_after": 47.00,
      "reason": "Contribution approved: item_donation",
      "contribution_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-10-16T15:00:00Z"
    },
    {
      "id": "trans-uuid-2",
      "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "amount": 10.00,
      "balance_after": 42.00,
      "reason": "Contribution approved: money",
      "contribution_id": "contrib-uuid-2",
      "created_at": "2025-10-15T14:30:00Z"
    }
  ],
  "pagination": {
    "total": 23,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

---

### Manual Credit Adjustment (Admin Only)
```http
POST /api/contributions/credits/adjust
Content-Type: application/json
Authorization: Bearer <admin_token>
```

**Request Body**:
```json
{
  "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "amount": -5.00,
  "reason": "Correction for duplicate submission"
}
```

**Validation Rules**:
- `user_id`: Required, valid UUID
- `amount`: Required, can be positive or negative
- `reason`: Required, 10-500 characters
- Result cannot make balance negative

**Response** (200 OK):
```json
{
  "transaction_id": "trans-uuid-3",
  "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "old_balance": 47.00,
  "adjustment": -5.00,
  "new_balance": 42.00,
  "old_tier": "gold",
  "new_tier": "silver",
  "reason": "Correction for duplicate submission",
  "adjusted_by": "admin-user-id",
  "adjusted_at": "2025-10-16T15:30:00Z"
}
```

---

### Get Priority Status
```http
GET /api/contributions/credits/{user_id}/priority
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "credit_balance": 47.00,
  "tier": "gold",
  "priority_level": 1,
  "priority_label": "High Priority",
  "benefits": [
    "Priority booking access",
    "Extended reservation times",
    "Top 15% in waitlists"
  ],
  "estimated_waitlist_improvement": "Top 15%"
}
```

---

## Statistics Endpoints

### Get Community-Wide Statistics (Admin Only)
```http
GET /api/contributions/stats?period={period}
Authorization: Bearer <admin_token>
```

**Query Parameters**:
- `period` (optional): Time period (today, week, month, year, all), default "month"

**Response** (200 OK):
```json
{
  "period": "month",
  "period_start": "2025-10-01T00:00:00Z",
  "period_end": "2025-10-31T23:59:59Z",
  "summary": {
    "total_contributions": 127,
    "total_credits_issued": 542.00,
    "active_contributors": 84,
    "pending_approvals": 12
  },
  "by_type": {
    "item_donation": {
      "count": 45,
      "percentage": 35,
      "credits": 183.00
    },
    "money": {
      "count": 52,
      "percentage": 41,
      "credits": 268.00
    },
    "volunteer_hours": {
      "count": 30,
      "percentage": 24,
      "credits": 91.00
    }
  },
  "tier_distribution": {
    "bronze": 120,
    "silver": 45,
    "gold": 28,
    "platinum": 12
  },
  "top_contributors": [
    {
      "user_id": "user-1",
      "name": "Carol Smith",
      "credits_this_period": 28.00,
      "contributions_count": 8
    },
    {
      "user_id": "user-2",
      "name": "David Lee",
      "credits_this_period": 24.00,
      "contributions_count": 6
    }
  ]
}
```

---

### Get User Statistics
```http
GET /api/contributions/stats/user/{user_id}
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "summary": {
    "total_contributions": 29,
    "total_credits_earned": 47.00,
    "current_balance": 47.00,
    "current_tier": "gold",
    "member_since": "2024-03-15T00:00:00Z"
  },
  "by_type": {
    "item_donation": {
      "count": 15,
      "credits": 28.00
    },
    "money": {
      "count": 6,
      "credits": 12.00
    },
    "volunteer_hours": {
      "count": 8,
      "total_hours": 14.5,
      "credits": 7.00
    }
  },
  "milestones": [
    {
      "type": "tier_reached",
      "tier": "gold",
      "date": "2025-09-20T00:00:00Z"
    },
    {
      "type": "contribution_count",
      "count": 25,
      "date": "2025-10-05T00:00:00Z"
    }
  ]
}
```

---

### Get Leaderboard
```http
GET /api/contributions/leaderboard?period={period}&limit={limit}
Authorization: Bearer <token>
```

**Query Parameters**:
- `period` (optional): Time period (week, month, year, all), default "month"
- `limit` (optional): Number of results, default 10, max 100

**Response** (200 OK):
```json
{
  "period": "month",
  "leaderboard": [
    {
      "rank": 1,
      "user_id": "user-1",
      "name": "Carol Smith",
      "credits_this_period": 28.00,
      "contributions_count": 8,
      "tier": "platinum"
    },
    {
      "rank": 2,
      "user_id": "user-2",
      "name": "David Lee",
      "credits_this_period": 24.00,
      "contributions_count": 6,
      "tier": "gold"
    }
  ]
}
```

---

## Error Response Format

All error responses follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "data.estimated_value",
        "message": "Value must be at least $10.00"
      }
    ],
    "timestamp": "2025-10-16T15:00:00Z",
    "request_id": "req-uuid"
  }
}
```

**Error Codes**:
- `VALIDATION_ERROR`: Input validation failed
- `AUTHENTICATION_ERROR`: Missing or invalid token
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `DUPLICATE_ERROR`: Resource already exists
- `RATE_LIMIT_ERROR`: Too many requests
- `SERVER_ERROR`: Internal server error

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /contributions | 10 per hour |
| GET /contributions | 100 per hour |
| PATCH /contributions/*/approve | 200 per hour (admin) |
| POST /credits/adjust | 50 per hour (admin) |
| GET /stats | 100 per hour |

Rate limit headers included in all responses:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1697472000
```

---

## Webhooks (Future Enhancement)

Events that can trigger webhooks:
- `contribution.created`
- `contribution.approved`
- `contribution.rejected`
- `credit.balance_changed`
- `tier.upgraded`

Webhook payload format:
```json
{
  "event": "contribution.approved",
  "timestamp": "2025-10-16T15:00:00Z",
  "data": {
    "contribution_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "credits_added": 5.00,
    "new_balance": 47.00
  }
}
```
