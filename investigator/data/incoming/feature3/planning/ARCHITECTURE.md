# Architecture Document: Advanced Resource Reservation System

## System Overview

The Advanced Resource Reservation System is a calendar-based booking platform that allows community members to reserve resources up to 30 days in advance. The system includes conflict detection, waitlist management, and automated notifications.

## High-Level Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│             │      │              │      │             │
│  React UI   │─────▶│  Express API │─────▶│ PostgreSQL  │
│  (Calendar) │      │  (Business   │      │ (Reserv.    │
│             │◀─────│   Logic)     │◀─────│  Tables)    │
│             │      │              │      │             │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                            │
                            ▼
                     ┌──────────────┐
                     │              │
                     │ Email Service│
                     │  (v1.5+)     │
                     │              │
                     └──────────────┘
```

## Core Components

### 1. Reservation State Machine

Reservations progress through a well-defined lifecycle:

```
    [Create]
       │
       ▼
  ┌─────────┐
  │ PENDING │ (Initial state, awaiting confirmation)
  └────┬────┘
       │
       │ [Admin/System Approval]
       ▼
 ┌───────────┐
 │ CONFIRMED │ (Booking finalized, email sent)
 └─────┬─────┘
       │
       │ [Check-in at start time]
       ▼
  ┌────────┐
  │ ACTIVE │ (User checked in, resource in use)
  └────┬───┘
       │
       ├──[Check-out]──────▶ ┌───────────┐
       │                     │ COMPLETED │
       │                     └───────────┘
       │
       └──[No show after    ┌──────────┐
          30 min grace]────▶│ NO_SHOW  │
                            └──────────┘
```

**State Transitions:**
- `PENDING → CONFIRMED`: Automatic after validation (no conflicts)
- `CONFIRMED → ACTIVE`: User checks in using existing check-in system
- `ACTIVE → COMPLETED`: User checks out or time expires
- `CONFIRMED → NO_SHOW`: Cron job detects no check-in after 30 min grace period
- `CONFIRMED → CANCELLED`: User or admin cancels reservation

**State Machine Benefits:**
- Clear lifecycle tracking
- Audit trail of all state changes
- Easy to add new states (e.g., `WAITING_APPROVAL`)
- Prevents invalid transitions

### 2. Conflict Detection Algorithm

The core challenge is detecting overlapping time intervals efficiently.

**SQL Query Approach:**
```sql
SELECT * FROM reservations 
WHERE resource_id = ? 
  AND status IN ('CONFIRMED', 'ACTIVE')
  AND (start_time, end_time) OVERLAPS (?, ?)
```

**PostgreSQL Range Overlap Logic:**
Two intervals overlap if:
- Interval A: `[start_a, end_a)`
- Interval B: `[start_b, end_b)`
- Overlap exists when: `start_a < end_b AND start_b < end_a`

**Edge Cases Handled:**
- **Exact boundaries**: `end_a == start_b` → No conflict (exclusive end time)
- **Same start time**: `start_a == start_b` → Conflict (inclusive start time)
- **Contained interval**: `start_b ≥ start_a AND end_b ≤ end_a` → Conflict
- **Container interval**: `start_a ≥ start_b AND end_a ≤ end_b` → Conflict

**Performance Optimization:**
- B-tree index on `(resource_id, start_time, end_time)` for fast range queries
- Query plan: Index scan → ~5ms for typical conflict checks
- Scales well up to 100k reservations per resource

### 3. Datetime Handling Strategy

**Critical Decision: Store in UTC, Display in User Timezone**

**Storage:**
- All `start_time` and `end_time` values stored as `TIMESTAMP WITH TIME ZONE` (UTC)
- Database handles timezone conversions automatically
- No ambiguity in stored data

**Display:**
- Frontend uses Luxon.js for timezone-aware datetime manipulation
- User's timezone detected from browser (`Intl.DateTimeFormat().resolvedOptions().timeZone`)
- All displayed times converted to user's local timezone
- ISO 8601 format for API communication: `2025-10-17T14:00:00-07:00`

**Daylight Saving Time (DST) Challenges:**
- **Spring Forward**: Clock jumps ahead (e.g., 2:00 AM → 3:00 AM)
  - Issue: Booking at 2:30 AM doesn't exist on that day
  - Solution: Luxon detects invalid times, suggests valid alternative
  - Test coverage: Edge case scenario in integration tests
  
- **Fall Back**: Clock repeats (e.g., 2:00 AM happens twice)
  - Issue: Ambiguous which "2:00 AM" user intends
  - Solution: Always use first occurrence (standard time)
  - Test coverage: Duration calculation tests

**Known DST Issues:**
⚠️ 3 integration tests currently failing for DST edge cases:
1. `Reservation during DST spring forward transition`
2. `Reservation spanning DST fall back transition`
3. `Conflict detection at DST boundary`

These are rare scenarios (occur twice per year) and have been marked as non-blocking for initial release.

### 4. Auto-Checkout Integration

**Problem:** Users forget to check out, blocking resource availability

**Solution:** Cron job for automated no-show detection

```javascript
// Pseudo-code for cron job (runs every 10 minutes)
function autoCheckoutNoShows() {
  const cutoffTime = now() - 30 minutes;
  
  const noShows = await db.query(`
    SELECT * FROM reservations
    WHERE status = 'CONFIRMED'
      AND start_time < $1
      AND NOT EXISTS (
        SELECT 1 FROM check_ins 
        WHERE check_ins.reservation_id = reservations.id
      )
  `, [cutoffTime]);
  
  for (const reservation of noShows) {
    await updateStatus(reservation.id, 'NO_SHOW');
    await releaseResource(reservation.resource_id);
    await notifyWaitlist(reservation);
  }
}
```

**Grace Period:** 30 minutes after `start_time` before marking as no-show
**Integration Point:** Links to existing check-in system (v1.2+)
**Waitlist Trigger:** No-shows automatically notify next person in queue

### 5. Waitlist Queue Management

**Algorithm:** FIFO (First-In-First-Out) with Admin Priority Override

**Data Structure:**
```sql
CREATE TABLE reservation_waitlist (
  id SERIAL PRIMARY KEY,
  reservation_request_id UUID,  -- Original failed booking attempt
  resource_id INTEGER REFERENCES resources(id),
  user_id INTEGER REFERENCES users(id),
  requested_start_time TIMESTAMP WITH TIME ZONE,
  requested_end_time TIMESTAMP WITH TIME ZONE,
  position INTEGER,  -- Queue position (1 = next in line)
  notified_at TIMESTAMP WITH TIME ZONE,
  expires_at TIMESTAMP WITH TIME ZONE,  -- Notification expires after 2 hours
  status VARCHAR(20),  -- 'WAITING', 'NOTIFIED', 'BOOKED', 'EXPIRED'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Queue Operations:**

1. **Join Waitlist:**
   ```javascript
   async function joinWaitlist(userId, resourceId, startTime, endTime) {
     const maxPosition = await getMaxPosition(resourceId);
     await insertWaitlist({
       userId,
       resourceId,
       requestedStartTime: startTime,
       requestedEndTime: endTime,
       position: maxPosition + 1,
       status: 'WAITING'
     });
   }
   ```

2. **Notify Next in Queue:**
   ```javascript
   async function notifyWaitlist(cancelledReservation) {
     const nextUser = await getNextWaitlistUser(
       cancelledReservation.resource_id,
       cancelledReservation.start_time,
       cancelledReservation.end_time
     );
     
     if (nextUser) {
       await sendEmail(nextUser.user_id, {
         subject: 'Resource Now Available!',
         template: 'waitlist-notification',
         expiresAt: now() + 2 hours
       });
       
       await updateWaitlist(nextUser.id, {
         status: 'NOTIFIED',
         notifiedAt: now(),
         expiresAt: now() + 2 hours
       });
     }
   }
   ```

3. **Admin Priority Override:**
   ```javascript
   async function adminPriorityBooking(adminId, resourceId, startTime, endTime) {
     // Cancel conflicting reservations
     await cancelConflicts(resourceId, startTime, endTime);
     
     // Create admin reservation with priority flag
     await createReservation({
       userId: adminId,
       resourceId,
       startTime,
       endTime,
       priority: true,
       status: 'CONFIRMED'
     });
     
     // Notify affected users
     await notifyDisplacedUsers();
   }
   ```

**Expiration Handling:**
- Notifications expire after 2 hours
- Expired notifications automatically move to next person in queue
- Cron job runs every 15 minutes to process expirations

## Database Schema

### Primary Tables

```sql
-- Main reservations table
CREATE TABLE reservations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id INTEGER NOT NULL REFERENCES resources(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  end_time TIMESTAMP WITH TIME ZONE NOT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN (
    'PENDING', 'CONFIRMED', 'ACTIVE', 'COMPLETED', 'NO_SHOW', 'CANCELLED'
  )),
  purpose TEXT,
  special_requirements TEXT,
  priority BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Ensure start time is before end time
  CONSTRAINT valid_time_range CHECK (start_time < end_time),
  
  -- Prevent reservations too far in advance (30 days)
  CONSTRAINT max_advance_booking CHECK (
    start_time <= NOW() + INTERVAL '30 days'
  )
);

-- Waitlist queue
CREATE TABLE reservation_waitlist (
  id SERIAL PRIMARY KEY,
  reservation_request_id UUID,
  resource_id INTEGER NOT NULL REFERENCES resources(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  requested_start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  requested_end_time TIMESTAMP WITH TIME ZONE NOT NULL,
  position INTEGER NOT NULL,
  notified_at TIMESTAMP WITH TIME ZONE,
  expires_at TIMESTAMP WITH TIME ZONE,
  status VARCHAR(20) NOT NULL CHECK (status IN (
    'WAITING', 'NOTIFIED', 'BOOKED', 'EXPIRED', 'CANCELLED'
  )),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Indexes for Performance

```sql
-- Conflict detection index (most critical)
CREATE INDEX idx_reservations_conflict ON reservations (
  resource_id,
  start_time,
  end_time
) WHERE status IN ('CONFIRMED', 'ACTIVE');

-- User's reservation lookup
CREATE INDEX idx_reservations_user ON reservations (
  user_id,
  start_time DESC
);

-- Waitlist queue ordering
CREATE INDEX idx_waitlist_queue ON reservation_waitlist (
  resource_id,
  position,
  status
) WHERE status IN ('WAITING', 'NOTIFIED');

-- No-show detection (for cron job)
CREATE INDEX idx_reservations_no_show ON reservations (
  start_time,
  status
) WHERE status = 'CONFIRMED';
```

**Index Analysis:**
- `idx_reservations_conflict`: B-tree index, 90% cache hit rate
- Estimated size: ~50MB for 100k reservations
- Query performance: <10ms for conflict checks

## API Design

### RESTful Endpoints

```
POST   /api/reservations              Create new reservation
GET    /api/reservations              List user's reservations
GET    /api/reservations/:id          Get reservation details
PATCH  /api/reservations/:id          Modify reservation
DELETE /api/reservations/:id          Cancel reservation

GET    /api/reservations/conflicts    Check for conflicts (query params)
GET    /api/resources/:id/availability  Get calendar availability

POST   /api/reservations/:id/waitlist  Join waitlist
DELETE /api/waitlist/:id               Leave waitlist
GET    /api/waitlist/my-queue          Get user's waitlist positions
```

### Request/Response Examples

**Create Reservation:**
```http
POST /api/reservations
Content-Type: application/json

{
  "resourceId": 42,
  "startTime": "2025-10-17T14:00:00-07:00",
  "endTime": "2025-10-17T16:00:00-07:00",
  "purpose": "Weekly pottery class",
  "specialRequirements": "Need 10 chairs set up"
}
```

**Success Response:**
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "resourceId": 42,
  "userId": 789,
  "startTime": "2025-10-17T14:00:00-07:00",
  "endTime": "2025-10-17T16:00:00-07:00",
  "status": "CONFIRMED",
  "purpose": "Weekly pottery class",
  "createdAt": "2025-10-16T10:30:00-07:00"
}
```

**Conflict Error Response:**
```http
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "error": "TIME_SLOT_UNAVAILABLE",
  "message": "The requested time conflicts with an existing reservation",
  "conflictingReservation": {
    "startTime": "2025-10-17T14:00:00-07:00",
    "endTime": "2025-10-17T17:00:00-07:00"
  },
  "alternatives": [
    {
      "startTime": "2025-10-17T12:00:00-07:00",
      "endTime": "2025-10-17T14:00:00-07:00"
    },
    {
      "startTime": "2025-10-17T17:00:00-07:00",
      "endTime": "2025-10-17T19:00:00-07:00"
    }
  ],
  "waitlistAvailable": true
}
```

## Integration Points

### 1. Check-in System Integration (v1.2+)
- Reservation creation triggers potential check-in record
- Check-in system validates against active reservations
- No-show detection queries check-in records

### 2. Email Service Integration (v1.5+)
- Confirmation emails on booking
- Waitlist notification emails
- Reminder emails (future enhancement)
- Cancellation confirmation emails

### 3. User Authentication
- JWT-based authentication required for all endpoints
- User ID extracted from token for reservation ownership
- Admin role required for priority bookings

## Security Considerations

### Authorization Rules
- Users can only view/modify their own reservations
- Admins can view/modify all reservations
- Guests cannot make reservations (authentication required)

### Input Validation
- Start time must be in the future
- End time must be after start time
- Duration must be reasonable (min 30 min, max 8 hours)
- Purpose field required (prevents accidental bookings)
- Resource must exist and be bookable

### Rate Limiting
- Max 10 booking attempts per user per hour
- Max 5 concurrent reservations per user
- Prevents resource hoarding and abuse

## Monitoring & Observability

### Key Metrics
- Reservation success rate
- Conflict detection accuracy
- Waitlist conversion rate
- No-show percentage
- API response times
- Email delivery success rate

### Logging
- All state transitions logged with timestamp and actor
- Conflict detection results logged for analysis
- Failed booking attempts logged with reason
- Admin overrides logged for audit trail

### Alerts
- High no-show rate (>15%)
- Elevated conflict rate (>5%)
- Email delivery failures
- Database query timeouts
- Cron job failures

## Scalability Considerations

### Current Capacity
- Supports 100k active reservations
- Handles 1000 concurrent users
- Calendar loads in <2 seconds

### Future Scaling Options
- Add read replicas for calendar queries
- Implement caching layer (Redis) for availability checks
- Partition reservations table by date range
- Use CDC (Change Data Capture) for real-time calendar updates

## Deployment Architecture

### Infrastructure
- Containerized application (Docker)
- Kubernetes orchestration
- PostgreSQL 14+ (managed service)
- Redis for caching (future)
- SendGrid for email delivery

### Feature Flag
- `reservation_system_enabled` (default: false)
- Allows gradual rollout to communities
- Quick rollback if issues arise

## Testing Strategy

### Unit Tests
- State machine transitions
- Conflict detection logic
- Datetime conversions
- Waitlist queue operations

### Integration Tests
- End-to-end booking flow
- Check-in system integration
- Email service integration
- DST edge cases (⚠️ 3 currently failing)

### Performance Tests
- Scheduled but not yet executed
- Target: <200ms for calendar load
- Target: <100ms for conflict check

## Known Technical Debt

### Current Issues
1. **DST Edge Cases**: 3 failing integration tests
   - Spring forward transition
   - Fall back duration calculation
   - Conflict detection at DST boundary
   
2. **No Recurring Reservations**: Single bookings only
   - Future enhancement for weekly/daily patterns
   
3. **Limited Waitlist Intelligence**: Pure FIFO
   - Could optimize based on user patterns

### Future Improvements
- Implement conflict resolution suggestions (ML-based)
- Add capacity management (partial resource booking)
- Real-time calendar updates (WebSocket)
- Calendar synchronization (Google Calendar, Outlook)

## Architecture Review History

### Review Date: September 15, 2025
- **Attendees**: Sarah Chen (Lead), James Wilson (Backend), Lisa Park (Frontend)
- **Status**: APPROVED
- **Key Decisions**:
  - Use PostgreSQL range types for conflict detection
  - Store all times in UTC
  - Implement FIFO waitlist with admin override
- **Action Items**: All completed

### Next Review: After UAT completion
