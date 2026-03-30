# Architecture Document: Contribution Tracking & Community Credits

## System Overview

The Contribution Tracking & Community Credits system is designed as a modular, extensible platform for tracking member contributions and calculating credit balances. The architecture supports multiple contribution types through a polymorphic data model and integrates with existing community management systems.

## Architecture Principles

1. **Polymorphism**: Single table design with type-specific JSON data
2. **Event-Driven**: Audit trail for all credit changes
3. **Asynchronous Processing**: Background jobs for credit calculation
4. **Integration-Friendly**: Clear APIs for reservation system integration
5. **Scalability**: Designed to handle growth from hundreds to thousands of members

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                              │
├─────────────────┬────────────────┬─────────────────────────┤
│   Member Web    │  Admin Panel   │   Mobile App (Future)   │
│   Dashboard     │                │                          │
└────────┬────────┴────────┬───────┴──────────────────┬──────┘
         │                 │                           │
         └─────────────────┴───────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   API        │
                    │   Gateway    │
                    │   (Express)  │
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                  │
    ┌────▼─────┐    ┌─────▼──────┐    ┌─────▼──────┐
    │ Contrib  │    │   Credit    │    │ Integration│
    │ Service  │    │   Service   │    │   Service  │
    └────┬─────┘    └─────┬───────┘    └─────┬──────┘
         │                 │                   │
         └─────────────────┴───────────────────┘
                           │
                    ┌──────▼──────┐
                    │  PostgreSQL  │
                    │   Database   │
                    └──────┬───────┘
                           │
                    ┌──────▼──────┐
                    │   Background │
                    │   Job Queue  │
                    │  (Node-cron) │
                    └──────────────┘
```

## Data Model

### Polymorphic Contribution Design

The system uses a single `contributions` table with a polymorphic type field and JSON column for type-specific data.

#### Contribution Types

**Item Donation**
```json
{
  "type": "item_donation",
  "data": {
    "description": "Camping tent, 4-person Coleman",
    "estimated_value": 50.00,
    "condition": "like_new",
    "photos": ["url1", "url2"],
    "notes": "Lightly used, all poles included"
  }
}
```

**Monetary Contribution**
```json
{
  "type": "money",
  "data": {
    "amount": 50.00,
    "currency": "USD",
    "payment_method": "online_transfer",
    "receipt_url": "url",
    "transaction_id": "TXN123"
  }
}
```

**Volunteer Hours**
```json
{
  "type": "volunteer_hours",
  "data": {
    "activity": "Community garden maintenance",
    "hours": 3.0,
    "date": "2025-10-15",
    "supervisor": "Jane Smith",
    "notes": "Weeding and planting"
  }
}
```

### Database Schema

#### Tables

**contributions**
```sql
CREATE TABLE contributions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  type contribution_type NOT NULL,
  value_json JSONB NOT NULL,
  status contribution_status DEFAULT 'pending',
  calculated_credits DECIMAL(10,2),
  approved_by UUID REFERENCES users(id),
  approved_at TIMESTAMP,
  rejection_reason TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TYPE contribution_type AS ENUM ('item_donation', 'money', 'volunteer_hours');
CREATE TYPE contribution_status AS ENUM ('pending', 'approved', 'rejected');

CREATE INDEX idx_contributions_user ON contributions(user_id);
CREATE INDEX idx_contributions_status ON contributions(status);
CREATE INDEX idx_contributions_created ON contributions(created_at DESC);
```

**credit_balances**
```sql
CREATE TABLE credit_balances (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  balance DECIMAL(10,2) NOT NULL DEFAULT 0,
  last_calculated_at TIMESTAMP DEFAULT NOW(),
  tier VARCHAR(20) DEFAULT 'bronze',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_credit_balance ON credit_balances(balance DESC);
```

**credit_transactions**
```sql
CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  amount DECIMAL(10,2) NOT NULL,
  balance_after DECIMAL(10,2) NOT NULL,
  reason VARCHAR(255) NOT NULL,
  contribution_id UUID REFERENCES contributions(id),
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transactions_user ON credit_transactions(user_id);
CREATE INDEX idx_transactions_created ON credit_transactions(created_at DESC);
```

### Database Triggers

**Audit Trail Trigger**
```sql
CREATE OR REPLACE FUNCTION log_credit_transaction()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO credit_transactions (
    user_id,
    amount,
    balance_after,
    reason,
    contribution_id
  )
  VALUES (
    NEW.user_id,
    NEW.calculated_credits,
    (SELECT balance FROM credit_balances WHERE user_id = NEW.user_id),
    'Contribution approved: ' || NEW.type,
    NEW.id
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER contribution_approved_trigger
AFTER UPDATE OF status ON contributions
FOR EACH ROW
WHEN (NEW.status = 'approved' AND OLD.status != 'approved')
EXECUTE FUNCTION log_credit_transaction();
```

## Credit Calculation Formula

### Base Formula
```javascript
function calculateCredits(contribution) {
  switch(contribution.type) {
    case 'item_donation':
      // Value in dollars divided by 10
      return contribution.data.estimated_value / 10;

    case 'money':
      // Amount in dollars divided by 5
      return contribution.data.amount / 5;

    case 'volunteer_hours':
      // Hours multiplied by 2
      return contribution.data.hours * 2;

    default:
      throw new Error('Unknown contribution type');
  }
}
```

### Credit Tiers
- **Bronze**: 0-20 credits
- **Silver**: 21-50 credits
- **Gold**: 51-100 credits
- **Platinum**: 101+ credits

### Business Rules
- Credits are calculated when contribution is approved
- Minimum contribution values enforced:
  - Items: $10 minimum
  - Money: $5 minimum
  - Volunteer: 0.5 hours (30 minutes) minimum
- Credits rounded to 2 decimal places
- No negative credits allowed (floor at 0)
- Credits expire after 2 years of account inactivity

## Background Job Architecture

### Credit Calculation Service

**Job Schedule**: Daily at 3:00 AM UTC

**Purpose**:
- Recalculate credit balances for all users
- Update tier assignments
- Flag expired credits
- Generate daily statistics

**Implementation**:
```javascript
// Node-cron scheduled job
const cron = require('node-cron');

// Run every day at 3 AM UTC
cron.schedule('0 3 * * *', async () => {
  console.log('Starting credit calculation job');

  try {
    await recalculateAllBalances();
    await updateTierAssignments();
    await expireInactiveCredits();
    await generateDailyStats();

    console.log('Credit calculation job completed successfully');
  } catch (error) {
    console.error('Credit calculation job failed:', error);
    await notifyAdmins(error);
  }
});
```

**Processing Strategy**:
- Batch processing in chunks of 100 users
- Transaction isolation to prevent race conditions
- Retry logic with exponential backoff
- Dead letter queue for failed calculations
- Comprehensive logging for audit purposes

**Error Handling**:
- Wrap each user calculation in try-catch
- Continue processing on individual failures
- Log all errors to monitoring system
- Send summary report to admins
- Alert if failure rate > 5%

### Race Condition Prevention

**Problem**: Multiple processes updating credit balance simultaneously

**Solution**: Database-level locking
```sql
BEGIN;
SELECT balance FROM credit_balances
WHERE user_id = $1 FOR UPDATE;

UPDATE credit_balances
SET balance = balance + $2,
    last_calculated_at = NOW()
WHERE user_id = $1;

COMMIT;
```

## Integration Points

### 1. Reservation System Integration

**Priority Queue Sorting**

The reservation system queries credit balances to prioritize high-credit members in waitlists.

```javascript
// Modified waitlist query
async function getWaitlist(resourceId) {
  return await db.query(`
    SELECT
      r.id,
      r.user_id,
      r.requested_at,
      u.name,
      COALESCE(cb.balance, 0) as credit_balance,
      CASE
        WHEN cb.balance >= 51 THEN 1  -- Gold/Platinum priority
        WHEN cb.balance >= 21 THEN 2  -- Silver priority
        ELSE 3                        -- Bronze/no credits
      END as priority_tier
    FROM reservations r
    JOIN users u ON r.user_id = u.id
    LEFT JOIN credit_balances cb ON u.id = cb.user_id
    WHERE r.resource_id = $1
      AND r.status = 'waitlist'
    ORDER BY
      priority_tier ASC,        -- Higher tier first
      cb.balance DESC,          -- More credits first within tier
      r.requested_at ASC        -- Earlier request time as tiebreaker
  `, [resourceId]);
}
```

**API Contract**:
```javascript
// Endpoint for reservation system to check priority
GET /api/contributions/credits/:user_id/priority

Response:
{
  "user_id": "uuid",
  "credit_balance": 47,
  "tier": "gold",
  "priority_level": 1,
  "estimated_waitlist_position_improvement": "Top 15%"
}
```

### 2. Admin Panel Integration

**Approval Workflow**
```javascript
// Admin approves contribution
POST /api/contributions/:id/approve

Request:
{
  "adjusted_credits": 5,  // Optional: admin can adjust
  "notes": "Approved as submitted"
}

Response:
{
  "contribution_id": "uuid",
  "status": "approved",
  "credits_added": 5,
  "new_balance": 52,
  "new_tier": "gold"
}
```

**Manual Credit Adjustment**
```javascript
// Admin manually adjusts credits
POST /api/contributions/credits/adjust

Request:
{
  "user_id": "uuid",
  "amount": 10,  // Can be negative
  "reason": "Correction for duplicate submission"
}

Response:
{
  "user_id": "uuid",
  "old_balance": 47,
  "new_balance": 57,
  "transaction_id": "uuid"
}
```

### 3. Email Notification Service

**Events Triggering Notifications**:
- Contribution submitted (notify admins)
- Contribution approved (notify member)
- Contribution rejected (notify member with reason)
- New tier reached (notify member)
- Credits expiring soon (notify member)

**Integration**:
```javascript
// Event-driven notification
eventBus.on('contribution.approved', async (data) => {
  await emailService.send({
    to: data.member_email,
    template: 'contribution-approved',
    data: {
      contribution_type: data.type,
      credits_added: data.credits,
      new_balance: data.new_balance,
      new_tier: data.new_tier
    }
  });
});
```

## API Architecture

### RESTful Endpoints

**Contribution Management**
```
POST   /api/contributions              Create new contribution
GET    /api/contributions              List all (admin only)
GET    /api/contributions?user_id=X    List user's contributions
GET    /api/contributions/:id          Get contribution details
PATCH  /api/contributions/:id/approve  Approve contribution (admin)
PATCH  /api/contributions/:id/reject   Reject contribution (admin)
DELETE /api/contributions/:id          Delete contribution (admin)
```

**Credit Management**
```
GET    /api/contributions/credits/:user_id          Get credit balance
GET    /api/contributions/credits/:user_id/history  Get transaction history
POST   /api/contributions/credits/adjust            Manual adjustment (admin)
```

**Statistics & Reporting**
```
GET    /api/contributions/stats                Community-wide stats (admin)
GET    /api/contributions/stats/user/:user_id  User-specific stats
GET    /api/contributions/leaderboard          Top contributors
```

### Authentication & Authorization

**Middleware Stack**:
```javascript
app.use('/api/contributions', [
  authenticate,           // Verify JWT token
  rateLimit,             // Prevent abuse
  validateRequest,       // Schema validation
  authorize,             // Check permissions
  auditLog               // Log all actions
]);
```

**Permission Matrix**:
| Endpoint | Member | Admin |
|----------|--------|-------|
| Create contribution | ✅ Own | ✅ Any |
| View contributions | ✅ Own | ✅ All |
| Approve/Reject | ❌ | ✅ |
| Adjust credits | ❌ | ✅ |
| View stats | ❌ | ✅ |

## Performance Considerations

### Database Optimization

**Indexes**:
- User ID index on contributions for fast lookups
- Status index for admin queue queries
- Created timestamp index for history pagination
- Balance index for leaderboard queries

**Query Optimization**:
- Use EXPLAIN ANALYZE for slow queries
- Implement connection pooling (max 20 connections)
- Cache frequently accessed data (credit balances)
- Pagination for large result sets (20 items per page)

### Caching Strategy

**Redis Cache**:
```javascript
// Cache credit balances for 5 minutes
const balance = await cache.get(`credit_balance:${userId}`);
if (!balance) {
  balance = await db.getCreditBalance(userId);
  await cache.set(`credit_balance:${userId}`, balance, 300);
}
```

**Cache Invalidation**:
- Invalidate on contribution approval
- Invalidate on manual credit adjustment
- Invalidate after nightly recalculation

### API Rate Limiting

```javascript
// Rate limits by endpoint
const limits = {
  'POST /contributions': '10 per hour',         // Prevent spam
  'GET /contributions': '100 per hour',         // Normal usage
  'POST /credits/adjust': '50 per hour',        // Admin actions
};
```

## Security Considerations

### Input Validation

**Contribution Submission**:
- Sanitize all user input
- Validate contribution type enum
- Enforce minimum/maximum values
- Validate file uploads (images only, max 5MB)
- Check for malicious JSON in value_json

### SQL Injection Prevention

- Use parameterized queries exclusively
- Never concatenate user input into SQL
- Validate all UUID formats
- Use ORM/query builder (Knex.js)

### Authorization

- JWT tokens with 24-hour expiration
- Role-based access control (RBAC)
- Admin actions require additional verification
- Audit log for all sensitive operations

## Monitoring & Observability

### Metrics to Track

**Application Metrics**:
- Contribution submission rate
- Approval latency (time from submit to approve)
- Credit calculation job duration
- API response times
- Error rates by endpoint

**Business Metrics**:
- Active contributors per month
- Average credits per member
- Contribution type distribution
- Tier distribution
- Credit utilization in reservations

### Logging

**Structured Logging**:
```javascript
logger.info('Contribution approved', {
  contribution_id: id,
  user_id: userId,
  type: type,
  credits_added: credits,
  approved_by: adminId,
  duration_ms: approvalTime
});
```

**Log Levels**:
- ERROR: Failed operations, exceptions
- WARN: Validation failures, rate limits
- INFO: Successful operations
- DEBUG: Detailed flow information

## Scalability & Future Growth

### Horizontal Scaling

**Stateless API Servers**:
- Load balancer distributes requests
- No server-side session storage
- Shared Redis cache for all servers
- Background jobs run on dedicated workers

### Database Scaling

**Read Replicas**:
- Route read queries to replicas
- Write queries to primary
- Contribution history queries use replicas
- Stats and reporting use replicas

**Partitioning Strategy** (Future):
- Partition contributions table by year
- Archive old contributions to cold storage
- Maintain hot data for recent 2 years

### Future Enhancements

- GraphQL API for flexible queries
- Real-time credit updates via WebSockets
- Machine learning for fraud detection
- Blockchain integration for transparency
- Mobile SDK for native apps
