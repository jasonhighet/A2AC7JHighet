# Database Schema: QR Code Check-in/out

## Feature ID
FEAT-QR-002

## Overview
This document specifies the database schema changes required for the QR code check-in/out feature, including new tables, modified tables, indexes, and migrations.

## Database Technology
- **DBMS**: PostgreSQL 14.9
- **ORM**: Prisma 5.3.1
- **Migration Tool**: Prisma Migrate

## Schema Changes Summary

### New Tables
1. `qr_codes` - Stores QR code tokens and metadata
2. `qr_audit_log` - Audit trail for QR code usage

### Modified Tables
1. `checkouts` - Add QR tracking fields
2. `resources` - Add QR enabled flag

### New Indexes
7 new indexes for query optimization

## New Tables

### 1. qr_codes

**Purpose**: Store generated QR code tokens with expiration and invalidation tracking.

```sql
CREATE TABLE qr_codes (
  -- Primary Key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Foreign Keys
  resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  
  -- Token Data
  token TEXT NOT NULL UNIQUE,
  signature TEXT NOT NULL,
  nonce TEXT NOT NULL,
  
  -- Lifecycle Timestamps
  expires_at TIMESTAMP NOT NULL,
  invalidated_at TIMESTAMP,
  used_at TIMESTAMP,
  
  -- Usage Tracking
  scan_count INTEGER DEFAULT 0,
  last_scanned_at TIMESTAMP,
  used_by UUID REFERENCES users(id) ON DELETE SET NULL,
  
  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  -- Constraints
  CONSTRAINT valid_expiration CHECK (expires_at > created_at),
  CONSTRAINT used_implies_invalidated CHECK (
    (used_at IS NULL) OR (invalidated_at IS NOT NULL)
  )
);

-- Indexes
CREATE INDEX idx_qr_codes_token ON qr_codes(token);
CREATE INDEX idx_qr_codes_resource_id ON qr_codes(resource_id);
CREATE INDEX idx_qr_codes_expires_at ON qr_codes(expires_at);
CREATE INDEX idx_qr_codes_invalidated_at ON qr_codes(invalidated_at) WHERE invalidated_at IS NOT NULL;
CREATE INDEX idx_qr_codes_created_at ON qr_codes(created_at);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_qr_codes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_qr_codes_updated_at
  BEFORE UPDATE ON qr_codes
  FOR EACH ROW
  EXECUTE FUNCTION update_qr_codes_updated_at();

-- Comments
COMMENT ON TABLE qr_codes IS 'Stores QR code tokens for resource checkout/checkin';
COMMENT ON COLUMN qr_codes.token IS 'Base64-encoded JWT-like token';
COMMENT ON COLUMN qr_codes.signature IS 'HMAC-SHA256 signature for token validation';
COMMENT ON COLUMN qr_codes.nonce IS 'Random nonce for replay attack prevention';
COMMENT ON COLUMN qr_codes.scan_count IS 'Number of times QR code has been scanned (including failed attempts)';
```

**Column Details**:

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | gen_random_uuid() | Primary key |
| resource_id | UUID | NO | - | Reference to resources table |
| created_by | UUID | YES | - | User who generated the QR code |
| token | TEXT | NO | - | Base64-encoded token string |
| signature | TEXT | NO | - | HMAC-SHA256 signature |
| nonce | TEXT | NO | - | Random nonce (32 hex chars) |
| expires_at | TIMESTAMP | NO | - | Token expiration timestamp (15 min) |
| invalidated_at | TIMESTAMP | YES | - | When token was invalidated |
| used_at | TIMESTAMP | YES | - | When token was successfully used |
| scan_count | INTEGER | NO | 0 | Number of scan attempts |
| last_scanned_at | TIMESTAMP | YES | - | Last scan timestamp |
| used_by | UUID | YES | - | User who used the token |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | Last update timestamp |

**Indexes**:
- `idx_qr_codes_token`: Fast token lookup for validation
- `idx_qr_codes_resource_id`: Query QR codes by resource
- `idx_qr_codes_expires_at`: Cleanup expired tokens
- `idx_qr_codes_invalidated_at`: Query active vs invalidated tokens
- `idx_qr_codes_created_at`: Audit queries by creation time

### 2. qr_audit_log

**Purpose**: Audit trail for all QR code operations for security and debugging.

```sql
CREATE TABLE qr_audit_log (
  -- Primary Key
  id BIGSERIAL PRIMARY KEY,
  
  -- Foreign Keys
  qr_code_id UUID REFERENCES qr_codes(id) ON DELETE CASCADE,
  resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  
  -- Event Details
  event_type VARCHAR(50) NOT NULL,
  event_status VARCHAR(20) NOT NULL,
  
  -- Request Metadata
  ip_address INET,
  user_agent TEXT,
  device_id VARCHAR(255),
  
  -- Error Details (if applicable)
  error_code VARCHAR(50),
  error_message TEXT,
  
  -- Timing
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  -- Constraints
  CONSTRAINT valid_event_type CHECK (
    event_type IN (
      'QR_GENERATED',
      'QR_SCANNED',
      'QR_VALIDATED',
      'QR_INVALIDATED',
      'CHECKOUT_ATTEMPTED',
      'CHECKOUT_COMPLETED',
      'CHECKIN_ATTEMPTED',
      'CHECKIN_COMPLETED',
      'TOKEN_EXPIRED',
      'TOKEN_REUSED'
    )
  ),
  CONSTRAINT valid_event_status CHECK (
    event_status IN ('SUCCESS', 'FAILURE', 'WARNING')
  )
);

-- Indexes
CREATE INDEX idx_qr_audit_log_qr_code_id ON qr_audit_log(qr_code_id);
CREATE INDEX idx_qr_audit_log_resource_id ON qr_audit_log(resource_id);
CREATE INDEX idx_qr_audit_log_user_id ON qr_audit_log(user_id);
CREATE INDEX idx_qr_audit_log_event_type ON qr_audit_log(event_type);
CREATE INDEX idx_qr_audit_log_created_at ON qr_audit_log(created_at);
CREATE INDEX idx_qr_audit_log_device_id ON qr_audit_log(device_id) WHERE device_id IS NOT NULL;

-- Partitioning by month (for audit log retention)
-- Note: Implement if retention policy requires automatic archival
-- CREATE TABLE qr_audit_log_2025_10 PARTITION OF qr_audit_log
--   FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

-- Comments
COMMENT ON TABLE qr_audit_log IS 'Audit trail for all QR code operations';
COMMENT ON COLUMN qr_audit_log.event_type IS 'Type of event (e.g., QR_SCANNED, CHECKOUT_COMPLETED)';
COMMENT ON COLUMN qr_audit_log.event_status IS 'Outcome of event (SUCCESS, FAILURE, WARNING)';
COMMENT ON COLUMN qr_audit_log.device_id IS 'Mobile device identifier for tracking';
```

**Column Details**:

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| qr_code_id | UUID | YES | - | Reference to qr_codes (null if generation failed) |
| resource_id | UUID | NO | - | Reference to resources table |
| user_id | UUID | YES | - | User who performed action |
| event_type | VARCHAR(50) | NO | - | Type of event (enum) |
| event_status | VARCHAR(20) | NO | - | Success/Failure/Warning |
| ip_address | INET | YES | - | Client IP address |
| user_agent | TEXT | YES | - | HTTP User-Agent header |
| device_id | VARCHAR(255) | YES | - | Mobile device unique identifier |
| error_code | VARCHAR(50) | YES | - | Error code if failure |
| error_message | TEXT | YES | - | Detailed error message |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | Event timestamp |

## Modified Tables

### 1. checkouts (Modifications)

**Purpose**: Add fields to track QR-based checkouts.

```sql
-- Add new columns to existing checkouts table
ALTER TABLE checkouts
  ADD COLUMN qr_code_id UUID REFERENCES qr_codes(id) ON DELETE SET NULL,
  ADD COLUMN checkout_method VARCHAR(20) NOT NULL DEFAULT 'web',
  ADD COLUMN device_id VARCHAR(255),
  ADD COLUMN client_version VARCHAR(50),
  ADD CONSTRAINT valid_checkout_method CHECK (
    checkout_method IN ('web', 'qr', 'api', 'admin')
  );

-- Add index for QR code lookup
CREATE INDEX idx_checkouts_qr_code_id ON checkouts(qr_code_id) WHERE qr_code_id IS NOT NULL;
CREATE INDEX idx_checkouts_checkout_method ON checkouts(checkout_method);
CREATE INDEX idx_checkouts_device_id ON checkouts(device_id) WHERE device_id IS NOT NULL;

-- Comments
COMMENT ON COLUMN checkouts.qr_code_id IS 'Reference to QR code used for checkout (null for web/admin checkouts)';
COMMENT ON COLUMN checkouts.checkout_method IS 'Method used to perform checkout (web, qr, api, admin)';
COMMENT ON COLUMN checkouts.device_id IS 'Mobile device ID if checked out via mobile app';
COMMENT ON COLUMN checkouts.client_version IS 'Mobile app version (e.g., "1.2.3") or "web" for web checkouts';
```

**New Columns**:

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| qr_code_id | UUID | YES | NULL | Reference to qr_codes table |
| checkout_method | VARCHAR(20) | NO | 'web' | Checkout method (web/qr/api/admin) |
| device_id | VARCHAR(255) | YES | NULL | Device identifier for mobile checkouts |
| client_version | VARCHAR(50) | YES | NULL | App version or 'web' |

### 2. resources (Modifications)

**Purpose**: Add flag to enable/disable QR checkout per resource.

```sql
-- Add QR enablement flag
ALTER TABLE resources
  ADD COLUMN qr_enabled BOOLEAN NOT NULL DEFAULT true,
  ADD COLUMN last_qr_generated_at TIMESTAMP;

-- Add index for QR-enabled resources query
CREATE INDEX idx_resources_qr_enabled ON resources(qr_enabled) WHERE qr_enabled = true;

-- Comments
COMMENT ON COLUMN resources.qr_enabled IS 'Whether QR code checkout is enabled for this resource';
COMMENT ON COLUMN resources.last_qr_generated_at IS 'Timestamp of last QR code generation for this resource';
```

**New Columns**:

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| qr_enabled | BOOLEAN | NO | true | Enable/disable QR checkout |
| last_qr_generated_at | TIMESTAMP | YES | NULL | Last QR generation timestamp |

## Index Strategy

### Query Optimization

**Critical Queries**:

1. **Token Validation** (most frequent):
```sql
-- Query: Find active QR code by token
SELECT * FROM qr_codes 
WHERE token = ? 
  AND expires_at > CURRENT_TIMESTAMP 
  AND invalidated_at IS NULL;

-- Index: idx_qr_codes_token (covers lookup)
-- Index: idx_qr_codes_expires_at (helps with expiration filter)
```

2. **Resource Availability with QR Status**:
```sql
-- Query: Get resources with QR codes available
SELECT r.*, qr.token 
FROM resources r
LEFT JOIN qr_codes qr ON r.id = qr.resource_id 
  AND qr.expires_at > CURRENT_TIMESTAMP 
  AND qr.invalidated_at IS NULL
WHERE r.qr_enabled = true 
  AND r.available = true;

-- Index: idx_resources_qr_enabled
-- Index: idx_qr_codes_resource_id
-- Index: idx_qr_codes_expires_at
```

3. **Audit Trail Queries**:
```sql
-- Query: Get recent audit events for a resource
SELECT * FROM qr_audit_log 
WHERE resource_id = ? 
  AND created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Index: idx_qr_audit_log_resource_id
-- Index: idx_qr_audit_log_created_at
```

### Index Summary

| Table | Index Name | Columns | Purpose |
|-------|------------|---------|---------|
| qr_codes | idx_qr_codes_token | token | Token validation lookup |
| qr_codes | idx_qr_codes_resource_id | resource_id | Resource QR codes query |
| qr_codes | idx_qr_codes_expires_at | expires_at | Expiration cleanup |
| qr_codes | idx_qr_codes_invalidated_at | invalidated_at (partial) | Active tokens filter |
| qr_codes | idx_qr_codes_created_at | created_at | Audit queries |
| qr_audit_log | idx_qr_audit_log_qr_code_id | qr_code_id | Audit by QR code |
| qr_audit_log | idx_qr_audit_log_resource_id | resource_id | Audit by resource |
| qr_audit_log | idx_qr_audit_log_user_id | user_id | Audit by user |
| qr_audit_log | idx_qr_audit_log_event_type | event_type | Audit by event |
| qr_audit_log | idx_qr_audit_log_created_at | created_at | Time-based audit |
| qr_audit_log | idx_qr_audit_log_device_id | device_id (partial) | Device tracking |
| checkouts | idx_checkouts_qr_code_id | qr_code_id (partial) | QR checkout lookup |
| checkouts | idx_checkouts_checkout_method | checkout_method | Method-based queries |
| checkouts | idx_checkouts_device_id | device_id (partial) | Device checkout history |
| resources | idx_resources_qr_enabled | qr_enabled (partial) | QR-enabled resources |

## Prisma Schema

### Prisma Models

```prisma
model QrCode {
  id              String    @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  resourceId      String    @map("resource_id") @db.Uuid
  createdBy       String?   @map("created_by") @db.Uuid
  token           String    @unique
  signature       String
  nonce           String
  expiresAt       DateTime  @map("expires_at")
  invalidatedAt   DateTime? @map("invalidated_at")
  usedAt          DateTime? @map("used_at")
  scanCount       Int       @default(0) @map("scan_count")
  lastScannedAt   DateTime? @map("last_scanned_at")
  usedBy          String?   @map("used_by") @db.Uuid
  createdAt       DateTime  @default(now()) @map("created_at")
  updatedAt       DateTime  @default(now()) @updatedAt @map("updated_at")
  
  resource        Resource  @relation(fields: [resourceId], references: [id], onDelete: Cascade)
  creator         User?     @relation("QrCodeCreator", fields: [createdBy], references: [id], onDelete: SetNull)
  user            User?     @relation("QrCodeUser", fields: [usedBy], references: [id], onDelete: SetNull)
  checkouts       Checkout[]
  auditLogs       QrAuditLog[]
  
  @@index([token], name: "idx_qr_codes_token")
  @@index([resourceId], name: "idx_qr_codes_resource_id")
  @@index([expiresAt], name: "idx_qr_codes_expires_at")
  @@index([invalidatedAt], name: "idx_qr_codes_invalidated_at")
  @@index([createdAt], name: "idx_qr_codes_created_at")
  @@map("qr_codes")
}

model QrAuditLog {
  id           BigInt    @id @default(autoincrement())
  qrCodeId     String?   @map("qr_code_id") @db.Uuid
  resourceId   String    @map("resource_id") @db.Uuid
  userId       String?   @map("user_id") @db.Uuid
  eventType    String    @map("event_type") @db.VarChar(50)
  eventStatus  String    @map("event_status") @db.VarChar(20)
  ipAddress    String?   @map("ip_address") @db.Inet
  userAgent    String?   @map("user_agent")
  deviceId     String?   @map("device_id") @db.VarChar(255)
  errorCode    String?   @map("error_code") @db.VarChar(50)
  errorMessage String?   @map("error_message")
  createdAt    DateTime  @default(now()) @map("created_at")
  
  qrCode       QrCode?   @relation(fields: [qrCodeId], references: [id], onDelete: Cascade)
  resource     Resource  @relation(fields: [resourceId], references: [id], onDelete: Cascade)
  user         User?     @relation(fields: [userId], references: [id], onDelete: SetNull)
  
  @@index([qrCodeId], name: "idx_qr_audit_log_qr_code_id")
  @@index([resourceId], name: "idx_qr_audit_log_resource_id")
  @@index([userId], name: "idx_qr_audit_log_user_id")
  @@index([eventType], name: "idx_qr_audit_log_event_type")
  @@index([createdAt], name: "idx_qr_audit_log_created_at")
  @@index([deviceId], name: "idx_qr_audit_log_device_id")
  @@map("qr_audit_log")
}

model Checkout {
  // ... existing fields ...
  qrCodeId       String?   @map("qr_code_id") @db.Uuid
  checkoutMethod String    @default("web") @map("checkout_method") @db.VarChar(20)
  deviceId       String?   @map("device_id") @db.VarChar(255)
  clientVersion  String?   @map("client_version") @db.VarChar(50)
  
  qrCode         QrCode?   @relation(fields: [qrCodeId], references: [id], onDelete: SetNull)
  
  @@index([qrCodeId], name: "idx_checkouts_qr_code_id")
  @@index([checkoutMethod], name: "idx_checkouts_checkout_method")
  @@index([deviceId], name: "idx_checkouts_device_id")
  @@map("checkouts")
}

model Resource {
  // ... existing fields ...
  qrEnabled          Boolean   @default(true) @map("qr_enabled")
  lastQrGeneratedAt  DateTime? @map("last_qr_generated_at")
  
  qrCodes            QrCode[]
  qrAuditLogs        QrAuditLog[]
  
  @@index([qrEnabled], name: "idx_resources_qr_enabled")
  @@map("resources")
}
```

## Migrations

### Migration Plan

**Migration 001: Create QR Tables**
```sql
-- File: migrations/20251015_001_create_qr_tables.sql

-- Create qr_codes table
CREATE TABLE qr_codes (
  -- (full schema as shown above)
);

-- Create qr_audit_log table
CREATE TABLE qr_audit_log (
  -- (full schema as shown above)
);
```

**Migration 002: Modify Existing Tables**
```sql
-- File: migrations/20251015_002_modify_checkout_tables.sql

-- Add QR tracking to checkouts
ALTER TABLE checkouts
  ADD COLUMN qr_code_id UUID REFERENCES qr_codes(id) ON DELETE SET NULL,
  ADD COLUMN checkout_method VARCHAR(20) NOT NULL DEFAULT 'web',
  ADD COLUMN device_id VARCHAR(255),
  ADD COLUMN client_version VARCHAR(50);

-- Add QR enablement to resources
ALTER TABLE resources
  ADD COLUMN qr_enabled BOOLEAN NOT NULL DEFAULT true,
  ADD COLUMN last_qr_generated_at TIMESTAMP;
```

**Migration 003: Create Indexes**
```sql
-- File: migrations/20251015_003_create_indexes.sql

-- (all CREATE INDEX statements as shown above)
```

**Rollback Plan**:
```sql
-- Rollback 003: Drop indexes
DROP INDEX IF EXISTS idx_qr_codes_token;
DROP INDEX IF EXISTS idx_qr_codes_resource_id;
-- ... (all indexes)

-- Rollback 002: Remove columns
ALTER TABLE checkouts DROP COLUMN IF EXISTS qr_code_id;
ALTER TABLE checkouts DROP COLUMN IF EXISTS checkout_method;
ALTER TABLE checkouts DROP COLUMN IF EXISTS device_id;
ALTER TABLE checkouts DROP COLUMN IF EXISTS client_version;
ALTER TABLE resources DROP COLUMN IF EXISTS qr_enabled;
ALTER TABLE resources DROP COLUMN IF EXISTS last_qr_generated_at;

-- Rollback 001: Drop tables
DROP TABLE IF EXISTS qr_audit_log;
DROP TABLE IF EXISTS qr_codes;
```

## Data Retention & Cleanup

### Expired QR Codes Cleanup
```sql
-- Automated cleanup job (runs every hour)
DELETE FROM qr_codes
WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '24 hours'
  AND invalidated_at IS NOT NULL;
```

### Audit Log Retention
```sql
-- Archive audit logs older than 90 days (runs daily)
-- Option 1: Partition-based archival (if partitioning implemented)
-- DROP TABLE qr_audit_log_2025_07;

-- Option 2: Direct deletion
DELETE FROM qr_audit_log
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
```

## Database Performance Considerations

### Connection Pooling
```typescript
// Prisma connection pool settings
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  
  // Connection pool configuration
  connection_limit = 20
  pool_timeout = 30
}
```

### Query Performance Targets
- QR Token Validation: < 10ms (p95)
- QR Code Generation: < 20ms (p95)
- Audit Log Insert: < 5ms (p95)
- Checkout with QR: < 50ms (p95)

### Expected Load
- Peak QR scans: 100/minute
- Peak checkouts: 50/minute
- Audit log inserts: 200/minute
- Concurrent connections: 50-100

## Security Considerations

### Row-Level Security (Optional)
```sql
-- Enable RLS for audit log
ALTER TABLE qr_audit_log ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own audit logs
CREATE POLICY audit_log_user_policy ON qr_audit_log
  FOR SELECT
  USING (user_id = current_setting('app.user_id')::uuid);

-- Policy: Admins can see all logs
CREATE POLICY audit_log_admin_policy ON qr_audit_log
  FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = current_setting('app.user_id')::uuid 
        AND role = 'ADMIN'
    )
  );
```

### Encryption at Rest
- Database encryption: AWS RDS encryption enabled
- Sensitive fields: Consider application-level encryption for tokens if storing plain tokens

## Testing Data

### Seed Data for Testing
```sql
-- Insert test QR codes
INSERT INTO qr_codes (resource_id, token, signature, nonce, expires_at, created_by)
VALUES
  -- Valid QR code
  ('resource-uuid-1', 'test-token-valid', 'test-signature-1', 'nonce-1', 
   CURRENT_TIMESTAMP + INTERVAL '15 minutes', 'admin-uuid'),
  
  -- Expired QR code
  ('resource-uuid-2', 'test-token-expired', 'test-signature-2', 'nonce-2',
   CURRENT_TIMESTAMP - INTERVAL '1 minute', 'admin-uuid'),
  
  -- Invalidated QR code
  ('resource-uuid-3', 'test-token-used', 'test-signature-3', 'nonce-3',
   CURRENT_TIMESTAMP + INTERVAL '15 minutes', 'admin-uuid');

UPDATE qr_codes SET invalidated_at = CURRENT_TIMESTAMP 
WHERE token = 'test-token-used';
```

## Known Issues

### Critical Schema Issues
⚠️ **RACE-DB-001**: No database-level locking mechanism for QR token invalidation. Current CHECK constraint and transaction logic insufficient for high-concurrency scenarios. Requires:
- Pessimistic row locking with `SELECT ... FOR UPDATE`
- Or distributed lock via Redis

⚠️ **PERF-DB-001**: Missing composite index on `(resource_id, expires_at, invalidated_at)` for the most common query pattern. Current indexes not optimal for:
```sql
SELECT * FROM qr_codes 
WHERE resource_id = ? 
  AND expires_at > ? 
  AND invalidated_at IS NULL;
```

**Recommended Fix**:
```sql
CREATE INDEX idx_qr_codes_resource_expiry_status 
ON qr_codes(resource_id, expires_at, invalidated_at) 
WHERE invalidated_at IS NULL;
```

## Documentation & References
- PostgreSQL Docs: https://www.postgresql.org/docs/14/
- Prisma Schema Reference: https://www.prisma.io/docs/reference/api-reference/prisma-schema-reference
- Database Indexing Best Practices: https://use-the-index-luke.com/

## Approval Status
✅ **DESIGN APPROVED** - Schema design approved, implementation blocked by race condition concerns.

❌ **IMPLEMENTATION BLOCKED** - Security team requires distributed locking solution before production deployment.
