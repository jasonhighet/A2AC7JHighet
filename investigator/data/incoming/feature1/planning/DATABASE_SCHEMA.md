# Database Schema: Maintenance Scheduling & Alert System

## Overview
This document defines the database schema for the Maintenance Scheduling & Alert System. The schema uses PostgreSQL 14+ and integrates with existing CommunityShare platform tables.

## Schema Diagram

```
┌─────────────────────────────────────┐
│         resources (existing)         │
├─────────────────────────────────────┤
│ • id (UUID, PK)                     │
│ • name (VARCHAR)                    │
│ • type (VARCHAR)                    │
│ • owner_id (UUID, FK → users)       │
│ • created_at (TIMESTAMP)            │
│ • ...                                │
└──────────────┬──────────────────────┘
               │
               │ 1:N
               │
┌──────────────┴──────────────────────┐
│      maintenance_schedules          │
├─────────────────────────────────────┤
│ • id (UUID, PK)                     │
│ • resource_id (UUID, FK)            │◄─┐
│ • schedule_type (VARCHAR)           │  │
│ • frequency (ENUM)                  │  │ 1:N
│ • start_date (TIMESTAMP)            │  │
│ • next_due_date (TIMESTAMP)         │  │
│ • description (TEXT)                │  │
│ • assigned_to (UUID, FK → users)    │  │
│ • created_at (TIMESTAMP)            │  │
│ • updated_at (TIMESTAMP)            │  │
│ • deleted_at (TIMESTAMP)            │  │
└──────────────┬──────────────────────┘  │
               │                          │
               │ 1:N                      │
               │                          │
┌──────────────┴──────────────────────┐  │
│        maintenance_logs             │  │
├─────────────────────────────────────┤  │
│ • id (UUID, PK)                     │  │
│ • schedule_id (UUID, FK)            │──┘
│ • resource_id (UUID, FK)            │
│ • performed_by (UUID, FK → users)   │
│ • performed_at (TIMESTAMP)          │
│ • notes (TEXT)                      │
│ • photos (JSONB)                    │
│ • issues_found (ENUM)               │
│ • created_at (TIMESTAMP)            │
│ • updated_at (TIMESTAMP)            │
└─────────────────────────────────────┘
```

## Table Definitions

### maintenance_schedules

Stores maintenance schedules for resources with configurable frequencies.

```sql
CREATE TABLE maintenance_schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id UUID NOT NULL,
  schedule_type VARCHAR(50) NOT NULL,
  frequency maintenance_frequency NOT NULL,
  start_date TIMESTAMP WITH TIME ZONE NOT NULL,
  next_due_date TIMESTAMP WITH TIME ZONE NOT NULL,
  description TEXT,
  assigned_to UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP WITH TIME ZONE,
  
  CONSTRAINT fk_resource
    FOREIGN KEY (resource_id)
    REFERENCES resources(id)
    ON DELETE CASCADE,
    
  CONSTRAINT fk_assigned_user
    FOREIGN KEY (assigned_to)
    REFERENCES users(id)
    ON DELETE SET NULL,
    
  CONSTRAINT check_dates
    CHECK (next_due_date >= start_date)
);
```

**Column Descriptions**:
- `id`: Unique identifier for the schedule (UUID v4)
- `resource_id`: Foreign key to the resources table
- `schedule_type`: Type of maintenance (inspection, cleaning, repair, replacement, other)
- `frequency`: How often maintenance occurs (see ENUM below)
- `start_date`: When the maintenance schedule begins
- `next_due_date`: When the next maintenance is due (calculated based on frequency)
- `description`: Optional detailed description of maintenance tasks
- `assigned_to`: Optional user assigned to perform the maintenance
- `created_at`: Timestamp when schedule was created
- `updated_at`: Timestamp when schedule was last updated
- `deleted_at`: Soft delete timestamp (NULL if not deleted)

**Indexes**:
```sql
-- Optimize queries for resource schedules
CREATE INDEX idx_maintenance_schedules_resource_id 
  ON maintenance_schedules(resource_id)
  WHERE deleted_at IS NULL;

-- Optimize queries for due date checks (background job)
CREATE INDEX idx_maintenance_schedules_next_due_date 
  ON maintenance_schedules(next_due_date)
  WHERE deleted_at IS NULL;

-- Optimize queries for assigned user
CREATE INDEX idx_maintenance_schedules_assigned_to 
  ON maintenance_schedules(assigned_to)
  WHERE deleted_at IS NULL;

-- Composite index for common query pattern
CREATE INDEX idx_maintenance_schedules_resource_due 
  ON maintenance_schedules(resource_id, next_due_date)
  WHERE deleted_at IS NULL;
```

---

### maintenance_logs

Immutable records of completed maintenance activities.

```sql
CREATE TABLE maintenance_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id UUID,
  resource_id UUID NOT NULL,
  performed_by UUID NOT NULL,
  performed_at TIMESTAMP WITH TIME ZONE NOT NULL,
  notes TEXT NOT NULL,
  photos JSONB DEFAULT '[]'::jsonb,
  issues_found maintenance_issue_level NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT fk_schedule
    FOREIGN KEY (schedule_id)
    REFERENCES maintenance_schedules(id)
    ON DELETE SET NULL,
    
  CONSTRAINT fk_resource
    FOREIGN KEY (resource_id)
    REFERENCES resources(id)
    ON DELETE CASCADE,
    
  CONSTRAINT fk_performed_by_user
    FOREIGN KEY (performed_by)
    REFERENCES users(id)
    ON DELETE RESTRICT,
    
  CONSTRAINT check_performed_at
    CHECK (performed_at <= CURRENT_TIMESTAMP)
);
```

**Column Descriptions**:
- `id`: Unique identifier for the log entry (UUID v4)
- `schedule_id`: Optional foreign key to the maintenance schedule (NULL for ad-hoc maintenance)
- `resource_id`: Foreign key to the resources table
- `performed_by`: User who performed the maintenance
- `performed_at`: Timestamp when maintenance was performed
- `notes`: Detailed notes about the maintenance work performed (required)
- `photos`: JSONB array of photo metadata (URLs, sizes, timestamps)
- `issues_found`: Severity of issues found (none, minor, major)
- `created_at`: Timestamp when log was created (immutable)
- `updated_at`: Timestamp when log was last updated

**Photos JSONB Structure**:
```json
[
  {
    "url": "https://s3.amazonaws.com/communityshare/maintenance/abc123.jpg",
    "size_bytes": 2458234,
    "uploaded_at": "2025-10-15T14:32:00Z",
    "content_type": "image/jpeg"
  }
]
```

**Indexes**:
```sql
-- Optimize queries for schedule history
CREATE INDEX idx_maintenance_logs_schedule_id 
  ON maintenance_logs(schedule_id);

-- Optimize queries for resource history
CREATE INDEX idx_maintenance_logs_resource_id 
  ON maintenance_logs(resource_id);

-- Optimize queries by date range
CREATE INDEX idx_maintenance_logs_performed_at 
  ON maintenance_logs(performed_at DESC);

-- Optimize queries for user's performed maintenance
CREATE INDEX idx_maintenance_logs_performed_by 
  ON maintenance_logs(performed_by);

-- GIN index for JSONB photos queries (if needed in future)
CREATE INDEX idx_maintenance_logs_photos 
  ON maintenance_logs USING GIN (photos);
```

---

## ENUM Types

### maintenance_frequency

```sql
CREATE TYPE maintenance_frequency AS ENUM (
  'one-time',
  'daily',
  'weekly',
  'monthly',
  'quarterly',
  'annually'
);
```

### maintenance_issue_level

```sql
CREATE TYPE maintenance_issue_level AS ENUM (
  'none',
  'minor',
  'major'
);
```

---

## Triggers

### Update Timestamp Trigger

Automatically updates the `updated_at` timestamp when a record is modified.

```sql
-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for maintenance_schedules
CREATE TRIGGER update_maintenance_schedules_updated_at
  BEFORE UPDATE ON maintenance_schedules
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Trigger for maintenance_logs (though logs should be immutable after 30 days)
CREATE TRIGGER update_maintenance_logs_updated_at
  BEFORE UPDATE ON maintenance_logs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
```

### Prevent Log Modification After 30 Days

Maintenance logs become read-only after 30 days for audit trail integrity.

```sql
CREATE OR REPLACE FUNCTION prevent_old_log_modification()
RETURNS TRIGGER AS $$
BEGIN
  IF (CURRENT_TIMESTAMP - OLD.created_at) > INTERVAL '30 days' THEN
    RAISE EXCEPTION 'Cannot modify maintenance logs older than 30 days';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_old_log_updates
  BEFORE UPDATE ON maintenance_logs
  FOR EACH ROW
  EXECUTE FUNCTION prevent_old_log_modification();

CREATE TRIGGER prevent_old_log_deletes
  BEFORE DELETE ON maintenance_logs
  FOR EACH ROW
  EXECUTE FUNCTION prevent_old_log_modification();
```

---

## Migration Scripts

### Migration: 20250915_001_create_maintenance_tables.sql

```sql
-- Migration: Create maintenance scheduling tables
-- Version: 20250915_001
-- Description: Initial schema for maintenance scheduling and logging

BEGIN;

-- Create ENUM types
CREATE TYPE maintenance_frequency AS ENUM (
  'one-time',
  'daily',
  'weekly',
  'monthly',
  'quarterly',
  'annually'
);

CREATE TYPE maintenance_issue_level AS ENUM (
  'none',
  'minor',
  'major'
);

-- Create maintenance_schedules table
CREATE TABLE maintenance_schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id UUID NOT NULL,
  schedule_type VARCHAR(50) NOT NULL,
  frequency maintenance_frequency NOT NULL,
  start_date TIMESTAMP WITH TIME ZONE NOT NULL,
  next_due_date TIMESTAMP WITH TIME ZONE NOT NULL,
  description TEXT,
  assigned_to UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP WITH TIME ZONE,
  
  CONSTRAINT fk_resource
    FOREIGN KEY (resource_id)
    REFERENCES resources(id)
    ON DELETE CASCADE,
    
  CONSTRAINT fk_assigned_user
    FOREIGN KEY (assigned_to)
    REFERENCES users(id)
    ON DELETE SET NULL,
    
  CONSTRAINT check_dates
    CHECK (next_due_date >= start_date)
);

-- Create maintenance_logs table
CREATE TABLE maintenance_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id UUID,
  resource_id UUID NOT NULL,
  performed_by UUID NOT NULL,
  performed_at TIMESTAMP WITH TIME ZONE NOT NULL,
  notes TEXT NOT NULL,
  photos JSONB DEFAULT '[]'::jsonb,
  issues_found maintenance_issue_level NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  
  CONSTRAINT fk_schedule
    FOREIGN KEY (schedule_id)
    REFERENCES maintenance_schedules(id)
    ON DELETE SET NULL,
    
  CONSTRAINT fk_resource
    FOREIGN KEY (resource_id)
    REFERENCES resources(id)
    ON DELETE CASCADE,
    
  CONSTRAINT fk_performed_by_user
    FOREIGN KEY (performed_by)
    REFERENCES users(id)
    ON DELETE RESTRICT,
    
  CONSTRAINT check_performed_at
    CHECK (performed_at <= CURRENT_TIMESTAMP)
);

-- Create indexes for maintenance_schedules
CREATE INDEX idx_maintenance_schedules_resource_id 
  ON maintenance_schedules(resource_id)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_maintenance_schedules_next_due_date 
  ON maintenance_schedules(next_due_date)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_maintenance_schedules_assigned_to 
  ON maintenance_schedules(assigned_to)
  WHERE deleted_at IS NULL;

CREATE INDEX idx_maintenance_schedules_resource_due 
  ON maintenance_schedules(resource_id, next_due_date)
  WHERE deleted_at IS NULL;

-- Create indexes for maintenance_logs
CREATE INDEX idx_maintenance_logs_schedule_id 
  ON maintenance_logs(schedule_id);

CREATE INDEX idx_maintenance_logs_resource_id 
  ON maintenance_logs(resource_id);

CREATE INDEX idx_maintenance_logs_performed_at 
  ON maintenance_logs(performed_at DESC);

CREATE INDEX idx_maintenance_logs_performed_by 
  ON maintenance_logs(performed_by);

CREATE INDEX idx_maintenance_logs_photos 
  ON maintenance_logs USING GIN (photos);

-- Create update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_maintenance_schedules_updated_at
  BEFORE UPDATE ON maintenance_schedules
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_maintenance_logs_updated_at
  BEFORE UPDATE ON maintenance_logs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Create function to prevent old log modifications
CREATE OR REPLACE FUNCTION prevent_old_log_modification()
RETURNS TRIGGER AS $$
BEGIN
  IF (CURRENT_TIMESTAMP - OLD.created_at) > INTERVAL '30 days' THEN
    RAISE EXCEPTION 'Cannot modify maintenance logs older than 30 days';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to prevent old log modifications
CREATE TRIGGER prevent_old_log_updates
  BEFORE UPDATE ON maintenance_logs
  FOR EACH ROW
  EXECUTE FUNCTION prevent_old_log_modification();

CREATE TRIGGER prevent_old_log_deletes
  BEFORE DELETE ON maintenance_logs
  FOR EACH ROW
  EXECUTE FUNCTION prevent_old_log_modification();

COMMIT;
```

### Rollback Script

```sql
-- Rollback: Drop maintenance scheduling tables
-- Version: 20250915_001
-- Description: Rollback initial maintenance scheduling schema

BEGIN;

-- Drop triggers
DROP TRIGGER IF EXISTS prevent_old_log_deletes ON maintenance_logs;
DROP TRIGGER IF EXISTS prevent_old_log_updates ON maintenance_logs;
DROP TRIGGER IF EXISTS update_maintenance_logs_updated_at ON maintenance_logs;
DROP TRIGGER IF EXISTS update_maintenance_schedules_updated_at ON maintenance_schedules;

-- Drop functions
DROP FUNCTION IF EXISTS prevent_old_log_modification();
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop tables
DROP TABLE IF EXISTS maintenance_logs;
DROP TABLE IF EXISTS maintenance_schedules;

-- Drop ENUM types
DROP TYPE IF EXISTS maintenance_issue_level;
DROP TYPE IF EXISTS maintenance_frequency;

COMMIT;
```

---

## Data Retention Policy

### Maintenance Schedules
- Active schedules: Retained indefinitely
- Deleted schedules: Soft delete retained for 2 years for audit purposes
- Cleanup job runs quarterly to hard delete old soft-deleted records

### Maintenance Logs
- All logs: Retained indefinitely (audit trail)
- Logs become read-only after 30 days
- No automatic deletion policy

---

## Performance Considerations

### Query Optimization
1. **Indexes**: All foreign keys and frequently queried columns are indexed
2. **Partial Indexes**: Indexes on `deleted_at IS NULL` improve performance for active records
3. **JSONB**: GIN index on photos column for potential future queries

### Expected Query Patterns
1. Get all schedules for a resource: ~10ms (using idx_maintenance_schedules_resource_id)
2. Find due maintenance: ~5ms (using idx_maintenance_schedules_next_due_date)
3. Get maintenance history: ~15ms (using idx_maintenance_logs_resource_id)

### Scaling Considerations
- Expected schedule volume: ~10,000 active schedules
- Expected log volume: ~100,000 logs/year
- Table sizes remain manageable for years without partitioning
- If scale exceeds projections, consider partitioning maintenance_logs by year

---

## Security

### Row-Level Security (Future Enhancement)
For multi-tenant isolation, consider implementing RLS:

```sql
-- Enable RLS on tables
ALTER TABLE maintenance_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance_logs ENABLE ROW LEVEL SECURITY;

-- Example policy: Users can only see schedules for resources they have access to
CREATE POLICY maintenance_schedules_select_policy ON maintenance_schedules
  FOR SELECT
  USING (
    resource_id IN (
      SELECT id FROM resources WHERE owner_id = current_user_id()
    )
  );
```

*Note: Not implemented in v1.0 as authorization is handled at application layer.*

---

## Testing Data

### Seed Data for Development

```sql
-- Insert test maintenance schedules
INSERT INTO maintenance_schedules (
  resource_id, 
  schedule_type, 
  frequency, 
  start_date, 
  next_due_date, 
  description,
  assigned_to
) VALUES
  (
    '550e8400-e29b-41d4-a716-446655440000',
    'inspection',
    'monthly',
    '2025-01-15 00:00:00+00',
    '2025-11-15 00:00:00+00',
    'Monthly safety inspection of basketball court',
    '7c9e6679-7425-40de-944b-e07fc1f90ae7'
  ),
  (
    '550e8400-e29b-41d4-a716-446655440000',
    'cleaning',
    'weekly',
    '2025-01-01 00:00:00+00',
    '2025-10-21 00:00:00+00',
    'Weekly cleaning of court surface',
    '7c9e6679-7425-40de-944b-e07fc1f90ae7'
  );

-- Insert test maintenance logs
INSERT INTO maintenance_logs (
  schedule_id,
  resource_id,
  performed_by,
  performed_at,
  notes,
  issues_found
) VALUES
  (
    (SELECT id FROM maintenance_schedules LIMIT 1),
    '550e8400-e29b-41d4-a716-446655440000',
    '7c9e6679-7425-40de-944b-e07fc1f90ae7',
    '2025-10-15 14:30:00+00',
    'Completed monthly inspection. All equipment functional.',
    'none'
  );
```
