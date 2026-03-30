# Database Schema: Contribution Tracking & Community Credits

## Overview

This document defines the PostgreSQL database schema for the contribution tracking and community credits system. The design uses a polymorphic approach for different contribution types while maintaining referential integrity and audit capabilities.

## Schema Diagram

```
┌─────────────────┐
│     users       │
│  (existing)     │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼─────────────────────────────────────────────┐
│              contributions                            │
├──────────────────────────────────────────────────────┤
│ id (PK)                      UUID                     │
│ user_id (FK) →users          UUID                     │
│ type                         contribution_type ENUM   │
│ value_json                   JSONB                    │
│ status                       contribution_status ENUM │
│ calculated_credits           DECIMAL(10,2)            │
│ approved_by (FK) →users      UUID                     │
│ approved_at                  TIMESTAMP                │
│ rejection_reason             TEXT                     │
│ created_at                   TIMESTAMP                │
│ updated_at                   TIMESTAMP                │
└──────────────────┬───────────────────────────────────┘
                   │
                   │ 1:N
                   │
         ┌─────────▼──────────────┐
         │ credit_transactions     │
         ├────────────────────────┤
         │ id (PK)          UUID  │
         │ user_id (FK)     UUID  │
         │ amount           DEC   │
         │ balance_after    DEC   │
         │ reason           TEXT  │
         │ contribution_id  UUID  │
         │ created_by       UUID  │
         │ created_at       TS    │
         └────────────────────────┘

┌─────────────────────────────┐
│     credit_balances          │
├─────────────────────────────┤
│ user_id (PK, FK) →users UUID│
│ balance              DEC    │
│ last_calculated_at   TS     │
│ tier                 VARCHAR│
│ created_at           TS     │
│ updated_at           TS     │
└─────────────────────────────┘
```

## Table Definitions

### contributions

Stores all contribution records with polymorphic data structure.

```sql
CREATE TABLE contributions (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Foreign keys
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  approved_by UUID REFERENCES users(id) ON DELETE SET NULL,

  -- Contribution data
  type contribution_type NOT NULL,
  value_json JSONB NOT NULL,
  status contribution_status NOT NULL DEFAULT 'pending',
  calculated_credits DECIMAL(10,2),

  -- Approval tracking
  approved_at TIMESTAMP,
  rejection_reason TEXT,

  -- Timestamps
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

  -- Constraints
  CONSTRAINT chk_credits_positive CHECK (calculated_credits >= 0),
  CONSTRAINT chk_approved_when_approved CHECK (
    status != 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)
  ),
  CONSTRAINT chk_rejected_when_rejected CHECK (
    status != 'rejected' OR rejection_reason IS NOT NULL
  )
);

COMMENT ON TABLE contributions IS 'All member contributions (items, money, volunteer hours)';
COMMENT ON COLUMN contributions.value_json IS 'Type-specific contribution data stored as JSON';
COMMENT ON COLUMN contributions.calculated_credits IS 'Credits calculated from contribution value';
```

### contribution_type ENUM

```sql
CREATE TYPE contribution_type AS ENUM (
  'item_donation',
  'money',
  'volunteer_hours'
);

COMMENT ON TYPE contribution_type IS 'Types of contributions members can make';
```

### contribution_status ENUM

```sql
CREATE TYPE contribution_status AS ENUM (
  'pending',
  'approved',
  'rejected'
);

COMMENT ON TYPE contribution_status IS 'Approval status of contribution submissions';
```

### credit_balances

Stores current credit balance for each user.

```sql
CREATE TABLE credit_balances (
  -- Primary key (also foreign key)
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,

  -- Balance data
  balance DECIMAL(10,2) NOT NULL DEFAULT 0,
  tier VARCHAR(20) NOT NULL DEFAULT 'bronze',
  last_calculated_at TIMESTAMP NOT NULL DEFAULT NOW(),

  -- Timestamps
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

  -- Constraints
  CONSTRAINT chk_balance_not_negative CHECK (balance >= 0),
  CONSTRAINT chk_valid_tier CHECK (tier IN ('bronze', 'silver', 'gold', 'platinum'))
);

COMMENT ON TABLE credit_balances IS 'Current credit balance and tier for each user';
COMMENT ON COLUMN credit_balances.tier IS 'Member tier: bronze (0-20), silver (21-50), gold (51-100), platinum (101+)';
```

### credit_transactions

Audit trail of all credit balance changes.

```sql
CREATE TABLE credit_transactions (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Foreign keys
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  contribution_id UUID REFERENCES contributions(id) ON DELETE SET NULL,
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,

  -- Transaction data
  amount DECIMAL(10,2) NOT NULL,
  balance_after DECIMAL(10,2) NOT NULL,
  reason VARCHAR(255) NOT NULL,

  -- Timestamp
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),

  -- Constraints
  CONSTRAINT chk_balance_after_not_negative CHECK (balance_after >= 0)
);

COMMENT ON TABLE credit_transactions IS 'Immutable audit log of all credit balance changes';
COMMENT ON COLUMN credit_transactions.amount IS 'Credit amount added (positive) or removed (negative)';
COMMENT ON COLUMN credit_transactions.reason IS 'Human-readable explanation of transaction';
```

## Indexes

### contributions Indexes

```sql
-- Fast lookup of user's contributions
CREATE INDEX idx_contributions_user ON contributions(user_id);

-- Admin queue: pending contributions ordered by submission time
CREATE INDEX idx_contributions_pending ON contributions(status, created_at DESC)
  WHERE status = 'pending';

-- Contribution history (most recent first)
CREATE INDEX idx_contributions_created ON contributions(created_at DESC);

-- Lookup by type for analytics
CREATE INDEX idx_contributions_type ON contributions(type);

-- Admin view: recently approved
CREATE INDEX idx_contributions_approved ON contributions(approved_at DESC)
  WHERE status = 'approved';

-- Composite index for user + status queries
CREATE INDEX idx_contributions_user_status ON contributions(user_id, status, created_at DESC);

-- JSON search on value_json (GIN index for fast JSON queries)
CREATE INDEX idx_contributions_value_json ON contributions USING GIN (value_json);
```

### credit_balances Indexes

```sql
-- Leaderboard: highest balances first
CREATE INDEX idx_credit_balances_balance ON credit_balances(balance DESC);

-- Tier distribution queries
CREATE INDEX idx_credit_balances_tier ON credit_balances(tier);

-- Stale balance detection
CREATE INDEX idx_credit_balances_calculation ON credit_balances(last_calculated_at);
```

### credit_transactions Indexes

```sql
-- User transaction history
CREATE INDEX idx_transactions_user ON credit_transactions(user_id, created_at DESC);

-- Lookup transactions by contribution
CREATE INDEX idx_transactions_contribution ON credit_transactions(contribution_id)
  WHERE contribution_id IS NOT NULL;

-- Admin audit queries
CREATE INDEX idx_transactions_created ON credit_transactions(created_at DESC);
```

## Triggers

### Auto-update updated_at Timestamp

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_contributions_updated_at
  BEFORE UPDATE ON contributions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_credit_balances_updated_at
  BEFORE UPDATE ON credit_balances
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
```

### Log Credit Transaction on Approval

```sql
CREATE OR REPLACE FUNCTION log_credit_transaction()
RETURNS TRIGGER AS $$
DECLARE
  current_balance DECIMAL(10,2);
  new_balance DECIMAL(10,2);
BEGIN
  -- Only run when status changes to approved
  IF NEW.status = 'approved' AND OLD.status != 'approved' THEN
    -- Get current balance (with row-level lock)
    SELECT balance INTO current_balance
    FROM credit_balances
    WHERE user_id = NEW.user_id
    FOR UPDATE;

    -- If no balance record exists, create one
    IF current_balance IS NULL THEN
      INSERT INTO credit_balances (user_id, balance, tier)
      VALUES (NEW.user_id, 0, 'bronze');
      current_balance := 0;
    END IF;

    -- Calculate new balance
    new_balance := current_balance + NEW.calculated_credits;

    -- Update balance
    UPDATE credit_balances
    SET balance = new_balance,
        tier = CASE
          WHEN new_balance >= 101 THEN 'platinum'
          WHEN new_balance >= 51 THEN 'gold'
          WHEN new_balance >= 21 THEN 'silver'
          ELSE 'bronze'
        END,
        last_calculated_at = NOW()
    WHERE user_id = NEW.user_id;

    -- Log transaction
    INSERT INTO credit_transactions (
      user_id,
      amount,
      balance_after,
      reason,
      contribution_id,
      created_by
    )
    VALUES (
      NEW.user_id,
      NEW.calculated_credits,
      new_balance,
      'Contribution approved: ' || NEW.type,
      NEW.id,
      NEW.approved_by
    );
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER contribution_approved_trigger
  AFTER UPDATE OF status ON contributions
  FOR EACH ROW
  EXECUTE FUNCTION log_credit_transaction();
```

### Prevent Balance Tampering

```sql
CREATE OR REPLACE FUNCTION prevent_direct_balance_manipulation()
RETURNS TRIGGER AS $$
BEGIN
  -- Prevent manual UPDATE unless from trusted functions
  IF TG_OP = 'UPDATE' AND current_setting('app.allow_balance_update', true) != 'true' THEN
    RAISE EXCEPTION 'Direct balance updates not allowed. Use API endpoints.';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- This trigger can be enabled in production to prevent manual SQL updates
-- CREATE TRIGGER prevent_balance_tampering
--   BEFORE UPDATE ON credit_balances
--   FOR EACH ROW
--   EXECUTE FUNCTION prevent_direct_balance_manipulation();
```

## Views

### Contribution Summary View

Convenient view for common contribution queries with user details.

```sql
CREATE VIEW contribution_summary AS
SELECT
  c.id,
  c.user_id,
  u.name as user_name,
  u.email as user_email,
  c.type,
  c.status,
  c.calculated_credits,
  c.created_at,
  c.approved_at,
  c.approved_by,
  approver.name as approved_by_name,
  CASE c.type
    WHEN 'item_donation' THEN c.value_json->>'description'
    WHEN 'money' THEN 'Monetary contribution'
    WHEN 'volunteer_hours' THEN c.value_json->>'activity'
  END as contribution_description,
  CASE c.type
    WHEN 'item_donation' THEN (c.value_json->>'estimated_value')::decimal
    WHEN 'money' THEN (c.value_json->>'amount')::decimal
    WHEN 'volunteer_hours' THEN (c.value_json->>'hours')::decimal
  END as contribution_value
FROM contributions c
JOIN users u ON c.user_id = u.id
LEFT JOIN users approver ON c.approved_by = approver.id;

COMMENT ON VIEW contribution_summary IS 'Convenient view of contributions with user details';
```

### User Credit Summary View

```sql
CREATE VIEW user_credit_summary AS
SELECT
  u.id as user_id,
  u.name,
  u.email,
  COALESCE(cb.balance, 0) as credit_balance,
  COALESCE(cb.tier, 'bronze') as tier,
  COUNT(c.id) as total_contributions,
  COUNT(c.id) FILTER (WHERE c.status = 'approved') as approved_contributions,
  COUNT(c.id) FILTER (WHERE c.status = 'pending') as pending_contributions,
  SUM(c.calculated_credits) FILTER (WHERE c.status = 'approved') as total_credits_earned,
  MAX(c.created_at) as last_contribution_date
FROM users u
LEFT JOIN credit_balances cb ON u.id = cb.user_id
LEFT JOIN contributions c ON u.id = c.user_id
GROUP BY u.id, u.name, u.email, cb.balance, cb.tier;

COMMENT ON VIEW user_credit_summary IS 'User statistics including contributions and credits';
```

## Sample Data

### Insert Sample Contributions

```sql
-- Sample item donation
INSERT INTO contributions (user_id, type, value_json, status, calculated_credits, approved_by, approved_at)
VALUES (
  '7c9e6679-7425-40de-944b-e07fc1f90ae7',
  'item_donation',
  '{
    "description": "Camping tent, 4-person Coleman",
    "estimated_value": 50.00,
    "condition": "like_new",
    "photos": ["https://example.com/photo1.jpg"],
    "notes": "Lightly used, all poles included"
  }'::jsonb,
  'approved',
  5.00,
  'admin-uuid',
  NOW()
);

-- Sample monetary contribution
INSERT INTO contributions (user_id, type, value_json, status, calculated_credits)
VALUES (
  '7c9e6679-7425-40de-944b-e07fc1f90ae7',
  'money',
  '{
    "amount": 50.00,
    "currency": "USD",
    "payment_method": "online_transfer",
    "transaction_id": "TXN123456"
  }'::jsonb,
  'pending',
  10.00
);

-- Sample volunteer hours
INSERT INTO contributions (user_id, type, value_json, status, calculated_credits, approved_by, approved_at)
VALUES (
  '7c9e6679-7425-40de-944b-e07fc1f90ae7',
  'volunteer_hours',
  '{
    "activity": "Community garden maintenance",
    "hours": 3.0,
    "date": "2025-10-15",
    "supervisor": "Jane Smith",
    "notes": "Weeding and planting"
  }'::jsonb,
  'approved',
  6.00,
  'admin-uuid',
  NOW()
);
```

## Query Examples

### Get user's approved contributions

```sql
SELECT
  id,
  type,
  value_json,
  calculated_credits,
  approved_at
FROM contributions
WHERE user_id = '7c9e6679-7425-40de-944b-e07fc1f90ae7'
  AND status = 'approved'
ORDER BY created_at DESC;
```

### Get pending contributions for admin queue

```sql
SELECT
  c.id,
  c.type,
  c.value_json,
  c.calculated_credits,
  c.created_at,
  u.name as user_name,
  u.email as user_email
FROM contributions c
JOIN users u ON c.user_id = u.id
WHERE c.status = 'pending'
ORDER BY c.created_at ASC;
```

### Get credit balance with breakdown

```sql
SELECT
  cb.user_id,
  cb.balance,
  cb.tier,
  COUNT(c.id) FILTER (WHERE c.type = 'item_donation') as item_count,
  SUM(c.calculated_credits) FILTER (WHERE c.type = 'item_donation') as item_credits,
  COUNT(c.id) FILTER (WHERE c.type = 'money') as money_count,
  SUM(c.calculated_credits) FILTER (WHERE c.type = 'money') as money_credits,
  COUNT(c.id) FILTER (WHERE c.type = 'volunteer_hours') as volunteer_count,
  SUM(c.calculated_credits) FILTER (WHERE c.type = 'volunteer_hours') as volunteer_credits
FROM credit_balances cb
LEFT JOIN contributions c ON cb.user_id = c.user_id AND c.status = 'approved'
WHERE cb.user_id = '7c9e6679-7425-40de-944b-e07fc1f90ae7'
GROUP BY cb.user_id, cb.balance, cb.tier;
```

### Get leaderboard

```sql
SELECT
  u.id,
  u.name,
  cb.balance,
  cb.tier,
  COUNT(c.id) as contribution_count
FROM credit_balances cb
JOIN users u ON cb.user_id = u.id
LEFT JOIN contributions c ON u.id = c.user_id AND c.status = 'approved'
GROUP BY u.id, u.name, cb.balance, cb.tier
ORDER BY cb.balance DESC
LIMIT 10;
```

## Backup & Maintenance

### Backup Strategy

```sql
-- Full backup (use pg_dump in production)
-- pg_dump -t contributions -t credit_balances -t credit_transactions > backup.sql

-- Point-in-time recovery enabled
-- Continuous archiving with WAL
```

### Maintenance Jobs

```sql
-- Vacuum and analyze weekly
VACUUM ANALYZE contributions;
VACUUM ANALYZE credit_balances;
VACUUM ANALYZE credit_transactions;

-- Reindex monthly
REINDEX TABLE contributions;
REINDEX TABLE credit_balances;
REINDEX TABLE credit_transactions;
```

### Data Archival

```sql
-- Archive old rejected contributions (older than 1 year)
CREATE TABLE contributions_archive (LIKE contributions INCLUDING ALL);

INSERT INTO contributions_archive
SELECT * FROM contributions
WHERE status = 'rejected'
  AND created_at < NOW() - INTERVAL '1 year';

DELETE FROM contributions
WHERE status = 'rejected'
  AND created_at < NOW() - INTERVAL '1 year';
```

## Migration Scripts

### Initial Migration (V1)

```sql
-- migrations/001_create_contribution_tables.sql

BEGIN;

-- Create types
CREATE TYPE contribution_type AS ENUM ('item_donation', 'money', 'volunteer_hours');
CREATE TYPE contribution_status AS ENUM ('pending', 'approved', 'rejected');

-- Create tables
CREATE TABLE contributions ( /* ... */ );
CREATE TABLE credit_balances ( /* ... */ );
CREATE TABLE credit_transactions ( /* ... */ );

-- Create indexes
CREATE INDEX idx_contributions_user ON contributions(user_id);
-- ... (all indexes)

-- Create triggers
CREATE FUNCTION update_updated_at_column() /* ... */;
CREATE TRIGGER update_contributions_updated_at /* ... */;
-- ... (all triggers)

-- Create views
CREATE VIEW contribution_summary AS /* ... */;
CREATE VIEW user_credit_summary AS /* ... */;

COMMIT;
```

### Rollback Script

```sql
-- migrations/001_create_contribution_tables_rollback.sql

BEGIN;

DROP VIEW IF EXISTS user_credit_summary;
DROP VIEW IF EXISTS contribution_summary;

DROP TRIGGER IF EXISTS contribution_approved_trigger ON contributions;
DROP TRIGGER IF EXISTS update_credit_balances_updated_at ON credit_balances;
DROP TRIGGER IF EXISTS update_contributions_updated_at ON contributions;

DROP FUNCTION IF EXISTS log_credit_transaction();
DROP FUNCTION IF EXISTS update_updated_at_column();

DROP TABLE IF EXISTS credit_transactions;
DROP TABLE IF EXISTS credit_balances;
DROP TABLE IF EXISTS contributions;

DROP TYPE IF EXISTS contribution_status;
DROP TYPE IF EXISTS contribution_type;

COMMIT;
```

## Performance Considerations

- **Partitioning**: Consider partitioning `contributions` table by `created_at` if volume exceeds 10M rows
- **Connection Pooling**: Use PgBouncer with max 20 connections
- **Query Optimization**: All queries use indexes, validated with EXPLAIN ANALYZE
- **Read Replicas**: Route analytics queries to read replicas in production
- **Caching**: Cache `credit_balances` in Redis for 5 minutes

## Security

- **Row-Level Security**: Can be enabled for multi-tenant scenarios
- **Encryption**: Use transparent data encryption (TDE) in production
- **Auditing**: All schema changes logged
- **Backups**: Encrypted backups stored in separate region
- **Access Control**: Principle of least privilege for application database user
