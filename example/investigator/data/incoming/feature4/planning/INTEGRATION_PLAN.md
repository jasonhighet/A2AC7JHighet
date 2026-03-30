# Integration Plan: Contribution Tracking & Community Credits

## Overview

This document outlines the integration strategy for connecting the Contribution Tracking & Community Credits system with existing platform components. The feature integrates with three main systems: Reservation System, Admin Panel, and Member Dashboard.

## Integration Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Existing Systems                       │
├────────────────┬──────────────────┬──────────────────────┤
│  Reservation   │   Admin Panel    │  Member Dashboard    │
│    System      │                  │                       │
└────────┬───────┴────────┬─────────┴──────────┬───────────┘
         │                │                     │
         │                │                     │
         └────────────────┼─────────────────────┘
                          │
         ┌────────────────▼─────────────────┐
         │   Contribution & Credits API     │
         │   (New Feature)                  │
         └──────────────────────────────────┘
```

## 1. Reservation System Integration

### Objective
Enable priority booking for members with high credit balances by modifying the waitlist queue logic.

### Current State
The reservation system currently uses first-come-first-served (FCFS) waitlist ordering:
```sql
SELECT * FROM reservations
WHERE resource_id = $1 AND status = 'waitlist'
ORDER BY requested_at ASC
```

### Integration Changes

#### Modified Waitlist Query
```sql
SELECT
  r.id,
  r.user_id,
  r.requested_at,
  u.name,
  COALESCE(cb.balance, 0) as credit_balance,
  CASE
    WHEN cb.balance >= 51 THEN 1   -- Gold/Platinum: High priority
    WHEN cb.balance >= 21 THEN 2   -- Silver: Medium priority
    ELSE 3                          -- Bronze/None: Normal priority
  END as priority_tier
FROM reservations r
JOIN users u ON r.user_id = u.id
LEFT JOIN credit_balances cb ON u.id = cb.user_id
WHERE r.resource_id = $1
  AND r.status = 'waitlist'
ORDER BY
  priority_tier ASC,          -- Higher tier first
  cb.balance DESC,            -- More credits first within tier
  r.requested_at ASC          -- FCFS as tiebreaker
```

#### Code Changes

**File**: `src/services/reservation/waitlist.service.ts`

```typescript
// BEFORE
async getWaitlist(resourceId: string): Promise<WaitlistEntry[]> {
  return await this.db.query(
    `SELECT * FROM reservations
     WHERE resource_id = $1 AND status = 'waitlist'
     ORDER BY requested_at ASC`,
    [resourceId]
  );
}

// AFTER
async getWaitlist(resourceId: string): Promise<WaitlistEntry[]> {
  return await this.db.query(
    `SELECT
       r.id,
       r.user_id,
       r.requested_at,
       u.name,
       COALESCE(cb.balance, 0) as credit_balance,
       CASE
         WHEN cb.balance >= 51 THEN 1
         WHEN cb.balance >= 21 THEN 2
         ELSE 3
       END as priority_tier
     FROM reservations r
     JOIN users u ON r.user_id = u.id
     LEFT JOIN credit_balances cb ON u.id = cb.user_id
     WHERE r.resource_id = $1 AND r.status = 'waitlist'
     ORDER BY priority_tier ASC, cb.balance DESC, r.requested_at ASC`,
    [resourceId]
  );
}
```

#### UI Changes

**File**: `src/components/reservation/WaitlistStatus.tsx`

Add priority indicator:
```tsx
interface WaitlistStatusProps {
  position: number;
  creditBalance: number;
  priorityTier: number;
}

export function WaitlistStatus({ position, creditBalance, priorityTier }: WaitlistStatusProps) {
  const isPriority = priorityTier <= 2;

  return (
    <div className="waitlist-status">
      {isPriority && <Star className="priority-icon" />}
      <span>Position #{position}</span>
      {isPriority && (
        <Tooltip content={`Your ${creditBalance} credits give you priority access`}>
          <Badge variant="success">High Priority</Badge>
        </Tooltip>
      )}
    </div>
  );
}
```

#### Testing Requirements

- [ ] Unit tests for priority queue logic
- [ ] Integration tests for waitlist ordering with various credit balances
- [ ] UI tests for priority indicator display
- [ ] Performance tests for waitlist queries with 100+ entries

#### Rollout Strategy

1. **Phase 1** (UAT): Enable priority queue in UAT environment only
2. **Phase 2** (Production Soft Launch): Enable for 10% of resources
3. **Phase 3** (Full Launch): Enable for all resources
4. **Monitoring**: Track priority vs non-priority member booking success rates

---

## 2. Admin Panel Integration

### Objective
Add contribution approval workflow and credit management tools to the admin panel.

### New Admin Features

#### 2.1 Contribution Approval Queue

**Route**: `/admin/contributions/pending`

**Component**: `src/components/admin/ContributionApprovalQueue.tsx`

**Features**:
- List all pending contributions
- View contribution details (photos, values, submitter history)
- Approve with optional credit adjustment
- Reject with reason
- Bulk actions (approve multiple, export)

**API Integration**:
```typescript
// Get pending contributions
GET /api/contributions?status=pending

// Approve contribution
PATCH /api/contributions/:id/approve
Body: { adjusted_credits: 5.0, notes: "Approved as submitted" }

// Reject contribution
PATCH /api/contributions/:id/reject
Body: { reason: "Value appears too high" }
```

**Permissions**: `admin.contributions.approve` role required

#### 2.2 Credit Adjustment Tool

**Route**: `/admin/credits/adjust`

**Component**: `src/components/admin/CreditAdjustmentTool.tsx`

**Features**:
- Search for user by name/email
- View current balance and history
- Add or remove credits with reason
- Audit trail of all adjustments

**API Integration**:
```typescript
// Manual credit adjustment
POST /api/contributions/credits/adjust
Body: {
  user_id: "uuid",
  amount: -5.0,
  reason: "Correction for duplicate"
}
```

**Permissions**: `admin.credits.adjust` role required

**Validation**:
- Reason required (min 10 characters)
- Cannot make balance negative
- Audit log entry created automatically

#### 2.3 Community Statistics Dashboard

**Route**: `/admin/stats/contributions`

**Component**: `src/components/admin/CommunityStatsReport.tsx`

**Features**:
- Total contributions by type (charts)
- Credits issued over time (line graph)
- Active contributors count
- Tier distribution (pie chart)
- Top contributors list
- Export to CSV

**API Integration**:
```typescript
// Get community stats
GET /api/contributions/stats?period=month

// Get detailed report
GET /api/contributions/stats/detailed?start=2025-10-01&end=2025-10-31
```

#### Testing Requirements

- [ ] Admin can access approval queue
- [ ] Non-admins cannot access admin tools
- [ ] Credit adjustments create audit entries
- [ ] Statistics display correctly
- [ ] Export functionality works

---

## 3. Member Dashboard Integration

### Objective
Display credit balance, contribution history, and submission form in member dashboard.

### New Member Features

#### 3.1 Credit Balance Card

**Location**: Member dashboard top section

**Component**: `src/components/member/CreditBalanceCard.tsx`

**Features**:
- Current credit balance (large display)
- Progress bar to next tier
- Tier badge
- Credit breakdown by type (pie chart)
- Link to contribution history

**API Integration**:
```typescript
// Get credit balance
GET /api/contributions/credits/:user_id

Response:
{
  balance: 47,
  tier: "gold",
  breakdown: {
    item_donations: { credits: 28, percentage: 60 },
    money: { credits: 12, percentage: 26 },
    volunteer_hours: { credits: 7, percentage: 14 }
  }
}
```

#### 3.2 Contribution History

**Route**: `/dashboard/contributions`

**Component**: `src/components/member/ContributionHistory.tsx`

**Features**:
- Paginated list of contributions
- Filter by type and status
- Sort by date or credits
- View details modal
- Status indicators (pending, approved, rejected)

**API Integration**:
```typescript
// Get user contributions
GET /api/contributions?user_id=:id&limit=20&offset=0
```

#### 3.3 Submit Contribution Form

**Route**: `/dashboard/contributions/new`

**Component**: `src/components/member/ContributionForm.tsx`

**Features**:
- Dynamic form based on contribution type
- Real-time credit calculation preview
- Photo upload (for items)
- Validation with helpful errors
- Success notification on submit

**API Integration**:
```typescript
// Create contribution
POST /api/contributions
Body: {
  type: "item_donation",
  data: { description: "...", estimated_value: 50, ... }
}
```

#### Testing Requirements

- [ ] Credit balance displays correctly
- [ ] Contribution history loads and paginates
- [ ] Form validation works for all types
- [ ] Photo upload successful
- [ ] Success/error notifications appear

---

## 4. Email Notification Service Integration

### Objective
Send automated emails for contribution events.

### Email Templates

#### 4.1 Contribution Submitted (to Admins)
```
Subject: New Contribution Pending Approval
Body:
  - Contributor name
  - Contribution type
  - Value/description
  - Link to approval queue
```

#### 4.2 Contribution Approved (to Member)
```
Subject: Your Contribution Has Been Approved! 🎉
Body:
  - Contribution details
  - Credits added
  - New balance
  - New tier (if upgraded)
  - Link to dashboard
```

#### 4.3 Contribution Rejected (to Member)
```
Subject: Update on Your Contribution Submission
Body:
  - Contribution details
  - Rejection reason
  - How to resubmit
  - Link to support
```

#### 4.4 Tier Upgraded (to Member)
```
Subject: Congratulations! You've Reached {Tier} Status
Body:
  - New tier badge
  - Benefits unlocked
  - Credits required for next tier
  - Link to dashboard
```

### Integration Code

**File**: `src/services/notification/email.service.ts`

```typescript
// Event listeners
eventBus.on('contribution.created', async (data) => {
  await emailService.send({
    to: ADMIN_EMAILS,
    template: 'contribution-submitted-admin',
    data: { ...data }
  });
});

eventBus.on('contribution.approved', async (data) => {
  await emailService.send({
    to: data.member_email,
    template: 'contribution-approved-member',
    data: { ...data }
  });

  // Check if tier upgraded
  if (data.old_tier !== data.new_tier) {
    await emailService.send({
      to: data.member_email,
      template: 'tier-upgraded',
      data: { tier: data.new_tier, ...data }
    });
  }
});

eventBus.on('contribution.rejected', async (data) => {
  await emailService.send({
    to: data.member_email,
    template: 'contribution-rejected-member',
    data: { ...data }
  });
});
```

---

## 5. User Service Integration

### Objective
Link contribution data with user profiles.

### User Profile Enhancements

Add credit information to user profile responses:

**File**: `src/services/user/profile.service.ts`

```typescript
async getUserProfile(userId: string): Promise<UserProfile> {
  const user = await this.db.getUserById(userId);
  const creditBalance = await this.creditService.getBalance(userId);

  return {
    ...user,
    credits: {
      balance: creditBalance.balance,
      tier: creditBalance.tier
    }
  };
}
```

---

## 6. Migration Plan

### Data Migration

#### 6.1 Seed Initial Credits

For existing active members, seed initial credits based on historical activity:

```sql
-- Calculate initial credits based on existing data
INSERT INTO credit_balances (user_id, balance, tier)
SELECT
  u.id,
  -- Formula: 1 credit per 5 past reservations + 2 credits per year of membership
  (COUNT(r.id) / 5) + (EXTRACT(YEAR FROM AGE(NOW(), u.created_at)) * 2) as initial_balance,
  CASE
    WHEN calculated_balance >= 51 THEN 'gold'
    WHEN calculated_balance >= 21 THEN 'silver'
    ELSE 'bronze'
  END as tier
FROM users u
LEFT JOIN reservations r ON u.id = r.user_id
WHERE u.status = 'active'
GROUP BY u.id;
```

#### 6.2 Create Audit Entries

```sql
-- Create transaction records for initial credits
INSERT INTO credit_transactions (user_id, amount, balance_after, reason)
SELECT
  user_id,
  balance,
  balance,
  'Initial credit allocation based on historical activity'
FROM credit_balances;
```

### Deployment Sequence

1. **Database Migration** (5 min)
   - Run schema creation scripts
   - Seed initial credits
   - Verify indexes created

2. **API Deployment** (10 min)
   - Deploy contribution & credits API
   - Run smoke tests
   - Verify endpoints responding

3. **Reservation System Update** (5 min)
   - Deploy modified waitlist logic
   - Test priority queue
   - Verify backward compatibility

4. **Admin Panel Update** (5 min)
   - Deploy admin components
   - Test approval workflow
   - Verify permissions

5. **Member Dashboard Update** (5 min)
   - Deploy member components
   - Test contribution submission
   - Verify credit display

6. **Email Service Configuration** (2 min)
   - Register event listeners
   - Test email templates
   - Verify delivery

**Total Estimated Deployment Time**: 32 minutes

### Rollback Plan

If integration issues occur:

1. **Revert Reservation System** (2 min)
   - Restore original waitlist query
   - Removes priority feature but keeps reservations working

2. **Disable Admin Tools** (1 min)
   - Feature flag off admin components
   - Admins lose access but no data lost

3. **Disable Member Dashboard Features** (1 min)
   - Feature flag off contribution components
   - Members lose access but existing data preserved

4. **Keep API Running** (no action)
   - Leave contribution API running for data collection
   - Can approve contributions via direct database access if needed

**Total Rollback Time**: 4 minutes

---

## 7. Testing Strategy

### Integration Test Scenarios

#### Scenario 1: End-to-End Contribution Flow
1. Member submits item donation
2. Admin receives email notification
3. Admin approves contribution
4. Member receives approval email
5. Credit balance updates
6. Member sees priority status in reservation

#### Scenario 2: Priority Queue Ordering
1. Create 10 test members with varying credit balances
2. All members join waitlist for same resource
3. Verify queue ordered by priority tier, then credits, then time
4. Resource becomes available
5. Verify high-credit member gets first access

#### Scenario 3: Credit Adjustment
1. Admin adjusts member credits (add 10)
2. Verify balance updates
3. Verify transaction logged
4. Verify tier recalculated if applicable
5. Verify audit trail created

### Performance Testing

- Waitlist query performance with 1000+ members
- Contribution approval latency
- Credit calculation job duration
- API response times under load

---

## 8. Monitoring & Alerts

### Metrics to Monitor

- **Integration Health**
  - Reservation system priority queue query time
  - Admin approval latency
  - Email delivery success rate

- **Business Metrics**
  - Contributions submitted per day
  - Approval rate
  - Average time to approval
  - Priority booking utilization

### Alerts

- Credit calculation job fails
- Email delivery failure rate > 5%
- API error rate > 1%
- Waitlist query time > 500ms

---

## 9. Documentation

### Developer Documentation

- [ ] API integration guide
- [ ] Database schema documentation
- [ ] Event system documentation
- [ ] Testing guide

### User Documentation

- [ ] Member guide: How to submit contributions
- [ ] Member guide: Understanding credit system
- [ ] Admin guide: Approving contributions
- [ ] Admin guide: Managing credits

---

## 10. Success Criteria

Integration is considered successful when:

- [ ] All integration tests passing
- [ ] UAT sign-off received
- [ ] Performance benchmarks met
- [ ] No critical bugs in production for 1 week
- [ ] 80%+ member satisfaction with feature
- [ ] Priority booking feature used by 60%+ eligible members
