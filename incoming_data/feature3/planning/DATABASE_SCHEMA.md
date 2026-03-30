# Database Schema: Advanced Resource Reservation System

## Overview

This document describes the database schema for the Advanced Resource Reservation System, including tables, indexes, constraints, and relationships.

## Database Technology

- **Engine**: PostgreSQL 14+
- **Timezone Handling**: All timestamps stored with timezone (TIMESTAMP WITH TIME ZONE)
- **UUID Generation**: Uses `gen_random_uuid()` for primary keys

## Entity Relationship Diagram

```
┌─────────────────┐         ┌──────────────────────┐
│   users         │         │   resources          │
│─────────────────│         │──────────────────────│
│ id (PK)         │         │ id (PK)              │
│ name            │         │ name                 │
│ email           │         │ description          │
│ ...             │         │ bookable             │
└────────┬────────┘         └──────────┬───────────┘
         │                              │
         │                              │
         │    ┌─────────────────────────┘
         │    │
         │    │
         ▼    ▼
┌─────────────────────────────────────────────────┐
│            reservations                         │
│─────────────────────────────────────────────────│
│ id (PK)                    UUID                 │
│ resource_id (FK)           INTEGER              │
│ user_id (FK)               INTEGER              │
│ start_time                 TIMESTAMP WITH TZ    │
│ end_time                   TIMESTAMP WITH TZ    │
│ status                     VARCHAR(20)          │
│ purpose                    TEXT                 │
│ special_requirements       TEXT                 │
│ priority                   BOOLEAN              │
│ created_at                 TIMESTAMP WITH TZ    │
│ updated_at                 TIMESTAMP WITH TZ    │
└────────┬────────────────────────────────────────┘
         │
         │
         ▼
┌─────────────────────────────────────────────────┐
│         reservation_waitlist                    │
│─────────────────────────────────────────────────│
│ id (PK)                    SERIAL               │
│ reservation_request_id     UUID                 │
│ resource_id (FK)           INTEGER              │
│ user_id (FK)               INTEGER              │
│ requested_start_time       TIMESTAMP WITH TZ    │
│ requested_end_time         TIMESTAMP WITH TZ    │
│ position                   INTEGER              │
│ notified_at                TIMESTAMP WITH TZ    │
│ expires_at                 TIMESTAMP WITH TZ    │
│ status                     VARCHAR(20)          │
│ created_at                 TIMESTAMP WITH TZ    │
└─────────────────────────────────────────────────┘
```

## Table Definitions

### reservations

Main table storing all resource reservations.

```sql
CREATE TABLE reservations (
  -- Primary identifier
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Foreign keys
  resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Time information (stored in UTC)
  start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  end_time TIMESTAMP WITH TIME ZONE NOT NULL,
  
  -- Status tracking
  status VARCHAR(20) NOT NULL CHECK (status IN (
    'PENDING',      -- Initial state, awaiting confirmation
    'CONFIRMED',    -- Booking finalized
    'ACTIVE',       -- User checked in
    'COMPLETED',    -- User checked out or time expired
    'NO_SHOW',      -- User didn't check in
    'CANCELLED'     -- User or admin cancelled
  )),
  
  -- Booking details
  purpose TEXT NOT NULL CHECK (length(purpose) >= 10 AND length(purpose) <= 500),
  special_requirements TEXT CHECK (length(special_requirements) <= 1000),
  
  -- Priority flag (admin override capability)
  priority BOOLEAN DEFAULT FALSE,
  
  -- Audit timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT valid_time_range CHECK (start_time < end_time),
  CONSTRAINT future_start_time CHECK (start_time > created_at),
  CONSTRAINT max_advance_booking CHECK (
    start_time <= created_at + INTERVAL '30 days'
  ),
  CONSTRAINT reasonable_duration CHECK (
    end_time - start_time >= INTERVAL '30 minutes' AND
    end_time - start_time <= INTERVAL '8 hours'
  )
);

-- Comments for documentation
COMMENT ON TABLE reservations IS 'Resource reservations with conflict detection and state management';
COMMENT ON COLUMN reservations.start_time IS 'Reservation start time in UTC';
COMMENT ON COLUMN reservations.end_time IS 'Reservation end time in UTC (exclusive)';
COMMENT ON COLUMN reservations.status IS 'Current state in reservation lifecycle';
COMMENT ON COLUMN reservations.priority IS 'Admin priority booking (can override conflicts)';
```

**Field Details:**

- **id**: UUID primary key for global uniqueness
- **resource_id**: Reference to resources table (what is being reserved)
- **user_id**: Reference to users table (who made the reservation)
- **start_time**: When reservation begins (inclusive)
- **end_time**: When reservation ends (exclusive, following [start, end) convention)
- **status**: Current state in the reservation lifecycle
- **purpose**: Why the resource is needed (required for accountability)
- **special_requirements**: Additional setup needs (optional)
- **priority**: True for admin override bookings
- **created_at**: When reservation was initially created
- **updated_at**: Last modification timestamp

**Business Rules Enforced:**

1. Start time must be before end time
2. Start time must be in the future (relative to creation)
3. Cannot book more than 30 days in advance
4. Minimum duration: 30 minutes
5. Maximum duration: 8 hours
6. Purpose must be 10-500 characters

### reservation_waitlist

Queue management for unavailable time slots.

```sql
CREATE TABLE reservation_waitlist (
  -- Primary identifier
  id SERIAL PRIMARY KEY,
  
  -- Original reservation request (for reference)
  reservation_request_id UUID,
  
  -- Foreign keys
  resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Requested time slot
  requested_start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  requested_end_time TIMESTAMP WITH TIME ZONE NOT NULL,
  
  -- Queue management
  position INTEGER NOT NULL CHECK (position > 0),
  
  -- Notification tracking
  notified_at TIMESTAMP WITH TIME ZONE,
  expires_at TIMESTAMP WITH TIME ZONE,
  
  -- Waitlist status
  status VARCHAR(20) NOT NULL CHECK (status IN (
    'WAITING',      -- In queue, not yet notified
    'NOTIFIED',     -- User notified of availability
    'BOOKED',       -- User successfully booked after notification
    'EXPIRED',      -- Notification expired, moved to next person
    'CANCELLED'     -- User left waitlist
  )),
  
  -- Audit
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT valid_waitlist_time_range CHECK (requested_start_time < requested_end_time),
  CONSTRAINT notification_logic CHECK (
    (status = 'NOTIFIED' AND notified_at IS NOT NULL AND expires_at IS NOT NULL) OR
    (status != 'NOTIFIED')
  )
);

-- Comments
COMMENT ON TABLE reservation_waitlist IS 'FIFO queue for unavailable time slots';
COMMENT ON COLUMN reservation_waitlist.position IS 'Queue position (1 = next in line)';
COMMENT ON COLUMN reservation_waitlist.expires_at IS 'Notification expires 2 hours after notified_at';
```

**Field Details:**

- **id**: Serial integer primary key
- **reservation_request_id**: UUID linking to original failed booking attempt (optional)
- **resource_id**: Which resource the user wants
- **user_id**: Who is waiting
- **requested_start_time**: Desired start time
- **requested_end_time**: Desired end time
- **position**: Queue position (1 = next, 2 = second, etc.)
- **notified_at**: When user was notified of availability
- **expires_at**: When notification expires (notified_at + 2 hours)
- **status**: Current waitlist state
- **created_at**: When user joined waitlist

**Queue Logic:**

1. FIFO ordering by position
2. Position numbers are sequential (no gaps)
3. When notified, user has 2 hours to book
4. If notification expires, position recalculated for remaining users

## Indexes

Indexes optimized for common query patterns.

### Primary Indexes (Conflict Detection)

```sql
-- Most critical index: conflict detection
-- Enables fast interval overlap queries
CREATE INDEX idx_reservations_conflict ON reservations (
  resource_id,
  start_time,
  end_time
) WHERE status IN ('CONFIRMED', 'ACTIVE');

COMMENT ON INDEX idx_reservations_conflict IS 
  'Critical for conflict detection. Partial index only includes bookable states.';
```

**Query Patterns Supported:**
```sql
-- Conflict detection query
SELECT * FROM reservations 
WHERE resource_id = $1 
  AND status IN ('CONFIRMED', 'ACTIVE')
  AND (start_time, end_time) OVERLAPS ($2, $3);
```

**Performance Characteristics:**
- Query time: ~5ms for 100k reservations
- Index size: ~50MB for 100k rows
- B-tree structure enables range scans

### User Reservation Lookup

```sql
-- User's reservation history and upcoming bookings
CREATE INDEX idx_reservations_user ON reservations (
  user_id,
  start_time DESC
);

COMMENT ON INDEX idx_reservations_user IS 
  'Lookup user reservations sorted by most recent first';
```

**Query Patterns Supported:**
```sql
-- Get user's upcoming reservations
SELECT * FROM reservations 
WHERE user_id = $1 
  AND start_time > NOW()
ORDER BY start_time;
```

### Waitlist Queue Ordering

```sql
-- Waitlist queue lookup by resource
CREATE INDEX idx_waitlist_queue ON reservation_waitlist (
  resource_id,
  position,
  status
) WHERE status IN ('WAITING', 'NOTIFIED');

COMMENT ON INDEX idx_waitlist_queue IS 
  'Fast lookup of next person in queue when slot becomes available';
```

**Query Patterns Supported:**
```sql
-- Find next person in waitlist
SELECT * FROM reservation_waitlist 
WHERE resource_id = $1 
  AND status = 'WAITING'
ORDER BY position 
LIMIT 1;
```

### No-Show Detection (Cron Job)

```sql
-- Efficient lookup for no-show detection cron job
CREATE INDEX idx_reservations_no_show ON reservations (
  start_time,
  status
) WHERE status = 'CONFIRMED';

COMMENT ON INDEX idx_reservations_no_show IS 
  'Cron job uses this to find reservations that should have started but no check-in occurred';
```

**Query Patterns Supported:**
```sql
-- Find reservations that started >30 min ago without check-in
SELECT r.* FROM reservations r
WHERE r.status = 'CONFIRMED'
  AND r.start_time < NOW() - INTERVAL '30 minutes'
  AND NOT EXISTS (
    SELECT 1 FROM check_ins c 
    WHERE c.reservation_id = r.id
  );
```

### Resource Availability Lookup

```sql
-- Calendar availability queries
CREATE INDEX idx_reservations_calendar ON reservations (
  resource_id,
  start_time,
  status
) WHERE status IN ('CONFIRMED', 'ACTIVE');

COMMENT ON INDEX idx_reservations_calendar IS 
  'Calendar view queries for date range availability';
```

**Query Patterns Supported:**
```sql
-- Get all reservations for a resource in a date range
SELECT * FROM reservations 
WHERE resource_id = $1 
  AND start_time >= $2 
  AND start_time < $3
  AND status IN ('CONFIRMED', 'ACTIVE')
ORDER BY start_time;
```

## Database Functions

### Trigger: Update Timestamp

```sql
-- Automatically update updated_at on row modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_reservations_updated_at
  BEFORE UPDATE ON reservations
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
```

### Function: Check Conflicts

```sql
-- Function to check for reservation conflicts
CREATE OR REPLACE FUNCTION has_reservation_conflict(
  p_resource_id INTEGER,
  p_start_time TIMESTAMP WITH TIME ZONE,
  p_end_time TIMESTAMP WITH TIME ZONE,
  p_exclude_reservation_id UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
  conflict_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO conflict_count
  FROM reservations
  WHERE resource_id = p_resource_id
    AND status IN ('CONFIRMED', 'ACTIVE')
    AND (id != p_exclude_reservation_id OR p_exclude_reservation_id IS NULL)
    AND (start_time, end_time) OVERLAPS (p_start_time, p_end_time);
  
  RETURN conflict_count > 0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION has_reservation_conflict IS 
  'Check if proposed time slot conflicts with existing reservations';
```

**Usage Example:**
```sql
-- Check if time slot is available
SELECT has_reservation_conflict(
  42,  -- resource_id
  '2025-10-17 14:00:00-07'::TIMESTAMPTZ,
  '2025-10-17 16:00:00-07'::TIMESTAMPTZ
);
-- Returns: true (conflict) or false (available)
```

### Function: Get Next Waitlist Position

```sql
-- Calculate next position in waitlist queue
CREATE OR REPLACE FUNCTION get_next_waitlist_position(
  p_resource_id INTEGER
)
RETURNS INTEGER AS $$
DECLARE
  max_pos INTEGER;
BEGIN
  SELECT COALESCE(MAX(position), 0) INTO max_pos
  FROM reservation_waitlist
  WHERE resource_id = p_resource_id
    AND status IN ('WAITING', 'NOTIFIED');
  
  RETURN max_pos + 1;
END;
$$ LANGUAGE plpgsql;
```

## Constraints Summary

### Foreign Key Constraints

```sql
-- Reservation foreign keys
ALTER TABLE reservations
  ADD CONSTRAINT fk_reservations_resource
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE;

ALTER TABLE reservations
  ADD CONSTRAINT fk_reservations_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Waitlist foreign keys
ALTER TABLE reservation_waitlist
  ADD CONSTRAINT fk_waitlist_resource
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE;

ALTER TABLE reservation_waitlist
  ADD CONSTRAINT fk_waitlist_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

### Check Constraints

All check constraints summarized:

**reservations table:**
- `valid_time_range`: start_time < end_time
- `future_start_time`: start_time > created_at
- `max_advance_booking`: start_time <= created_at + 30 days
- `reasonable_duration`: 30 minutes <= duration <= 8 hours
- `valid_status`: Status must be in predefined list
- `purpose_length`: Purpose must be 10-500 characters

**reservation_waitlist table:**
- `valid_waitlist_time_range`: requested_start_time < requested_end_time
- `positive_position`: position > 0
- `notification_logic`: If NOTIFIED, must have notified_at and expires_at
- `valid_status`: Status must be in predefined list

## Unique Constraints

```sql
-- Prevent duplicate waitlist entries for same user/resource/time
CREATE UNIQUE INDEX idx_waitlist_unique_request ON reservation_waitlist (
  user_id,
  resource_id,
  requested_start_time,
  requested_end_time
) WHERE status IN ('WAITING', 'NOTIFIED');
```

## Data Retention

### Reservation Archival Policy

- Active reservations (CONFIRMED, ACTIVE): Kept indefinitely
- Completed reservations: Retained for 2 years
- Cancelled reservations: Retained for 6 months
- No-show reservations: Retained for 1 year (for pattern analysis)

### Partitioning Strategy (Future)

For scaling beyond 1M reservations, consider partitioning by date:

```sql
-- Future partitioning example
CREATE TABLE reservations_2025_q4 PARTITION OF reservations
  FOR VALUES FROM ('2025-10-01') TO ('2026-01-01');
```

## Performance Tuning

### Query Performance Targets

- Conflict detection: <10ms
- Calendar availability: <50ms for 30-day range
- User reservation lookup: <20ms
- Waitlist queue operations: <15ms

### Vacuum and Analyze

```sql
-- Regular maintenance
VACUUM ANALYZE reservations;
VACUUM ANALYZE reservation_waitlist;

-- Auto-vacuum settings (postgresql.conf)
autovacuum = on
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_scale_factor = 0.05
```

### Connection Pooling

- Use PgBouncer or similar
- Pool size: 20-50 connections
- Transaction mode recommended

## Migration Scripts

### Initial Schema Creation

```sql
-- Create tables
\i create_reservations_table.sql
\i create_waitlist_table.sql

-- Create indexes
\i create_indexes.sql

-- Create functions
\i create_functions.sql

-- Add constraints
\i add_constraints.sql
```

### Rollback Strategy

All migrations include rollback scripts:

```sql
-- Rollback example
DROP INDEX IF EXISTS idx_reservations_conflict;
DROP FUNCTION IF EXISTS has_reservation_conflict(INTEGER, TIMESTAMPTZ, TIMESTAMPTZ, UUID);
DROP TABLE IF EXISTS reservation_waitlist;
DROP TABLE IF EXISTS reservations;
```

## Testing Database

### Test Data Generation

```sql
-- Generate test reservations
INSERT INTO reservations (
  resource_id, user_id, start_time, end_time, status, purpose
)
SELECT
  (random() * 50 + 1)::INTEGER,  -- Random resource
  (random() * 100 + 1)::INTEGER,  -- Random user
  NOW() + (random() * 30 || ' days')::INTERVAL,  -- Random future date
  NOW() + (random() * 30 || ' days')::INTERVAL + '2 hours'::INTERVAL,
  'CONFIRMED',
  'Test reservation ' || generate_series
FROM generate_series(1, 10000);
```

## Security Considerations

### Row-Level Security

```sql
-- Enable RLS
ALTER TABLE reservations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can see their own reservations
CREATE POLICY reservations_user_access ON reservations
  FOR ALL
  TO authenticated_user
  USING (user_id = current_user_id());

-- Policy: Admins can see all reservations
CREATE POLICY reservations_admin_access ON reservations
  FOR ALL
  TO admin_user
  USING (true);
```

### Sensitive Data

- User IDs linked to users table (separate permissions)
- No PII stored in reservations table
- purpose and special_requirements may contain sensitive info → access restricted

## Monitoring

### Key Metrics to Track

```sql
-- Active reservations count
SELECT COUNT(*) FROM reservations 
WHERE status IN ('CONFIRMED', 'ACTIVE');

-- Waitlist depth by resource
SELECT resource_id, COUNT(*) as waitlist_depth
FROM reservation_waitlist 
WHERE status = 'WAITING'
GROUP BY resource_id
ORDER BY waitlist_depth DESC;

-- No-show rate
SELECT 
  COUNT(*) FILTER (WHERE status = 'NO_SHOW')::FLOAT / COUNT(*) * 100 as no_show_rate
FROM reservations
WHERE created_at > NOW() - INTERVAL '30 days';

-- Average reservation duration
SELECT AVG(end_time - start_time) as avg_duration
FROM reservations
WHERE status = 'COMPLETED';
```

## Schema Versioning

Current version: **1.0.0**

Schema changes tracked in `schema_migrations` table (managed by migration tool).

## Documentation Updates

Last updated: 2025-10-09
Author: Sarah Chen (Engineering Lead)
Review: Approved by James Wilson (Database Architect)
