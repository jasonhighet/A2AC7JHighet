# Deployment Plan: Maintenance Scheduling & Alert System

## Overview
This document outlines the deployment strategy for the Maintenance Scheduling & Alert System feature. The deployment uses a phased rollout approach with feature flags to minimize risk.

## Deployment Metadata
- **Feature ID**: FEAT-MS-001
- **Target Environment**: Production
- **Scheduled Date**: October 18, 2025 at 02:00 AM UTC
- **Duration**: ~2 hours deployment window
- **Rollback Time**: < 15 minutes if needed

---

## Pre-Deployment Checklist

### Code Readiness
- [x] All code merged to main branch (PR #342)
- [x] Code review approved by 2+ reviewers
- [x] All tests passing (Unit: 156/156, Integration: 23/23)
- [x] Test coverage ≥ 80% (Current: 87%)
- [x] No critical or high severity security vulnerabilities
- [x] Performance benchmarks met (all endpoints < 200ms p95)

### Documentation
- [x] API documentation complete and published
- [x] User guide created and reviewed
- [x] Admin guide created and reviewed
- [x] Runbook for on-call engineers complete
- [x] Architecture diagrams updated

### Infrastructure
- [x] Database migration tested in staging
- [x] Background job scheduler configured
- [x] CloudWatch dashboards created
- [x] PagerDuty alerts configured
- [x] Feature flag created in LaunchDarkly

### Dependencies
- [x] Notification Service v2.3+ deployed and stable
- [x] Resource Management v1.3+ available
- [x] S3 bucket for photo uploads created and configured
- [x] IAM roles and permissions configured

### Team Readiness
- [x] Deployment team briefed
- [x] On-call engineers notified
- [x] Customer support trained on new feature
- [x] Rollback plan reviewed with team

---

## Feature Flag Configuration

### LaunchDarkly Setup

**Flag Name**: `maintenance_scheduling_enabled`

**Initial Configuration**:
```json
{
  "key": "maintenance_scheduling_enabled",
  "name": "Maintenance Scheduling & Alert System",
  "description": "Enables the maintenance scheduling and alert system for resources",
  "kind": "boolean",
  "variations": [
    {
      "value": true,
      "name": "Enabled"
    },
    {
      "value": false,
      "name": "Disabled"
    }
  ],
  "defaultVariation": 1,
  "targets": [],
  "rules": []
}
```

**Rollout Phases**:
1. **Phase 1**: Internal team only (10 users) - Days 1-2
2. **Phase 2**: Beta users (100 users) - Days 3-5
3. **Phase 3**: 25% of all users - Days 6-7
4. **Phase 4**: 50% of all users - Days 8-9
5. **Phase 5**: 100% of all users - Day 10

---

## Deployment Steps

### Phase 1: Database Migration (02:00 - 02:15 AM UTC)

**Step 1.1**: Create database backup
```bash
# Run on production DB instance
pg_dump -U communityshare_admin -d communityshare_prod > backup_pre_maintenance_$(date +%Y%m%d_%H%M%S).sql

# Upload to S3
aws s3 cp backup_pre_maintenance_*.sql s3://communityshare-backups/maintenance-feature/
```
**Expected Duration**: 10 minutes  
**Rollback**: Restore from backup if migration fails

**Step 1.2**: Run database migration
```bash
# Connect to production database
psql -U communityshare_admin -d communityshare_prod

# Run migration
\i migrations/20250915_001_create_maintenance_tables.sql

# Verify tables created
\dt maintenance_*

# Check indexes
\di maintenance_*
```
**Expected Duration**: 2 minutes  
**Validation**: 
- Verify maintenance_schedules table exists with correct schema
- Verify maintenance_logs table exists with correct schema
- Verify all indexes created
- Verify ENUM types created

**Step 1.3**: Insert seed data for testing
```bash
# Run seed script
\i seeds/maintenance_test_data.sql

# Verify data
SELECT COUNT(*) FROM maintenance_schedules;
SELECT COUNT(*) FROM maintenance_logs;
```
**Expected Duration**: 1 minute

---

### Phase 2: Application Deployment (02:15 - 02:45 AM UTC)

**Step 2.1**: Deploy backend API changes
```bash
# SSH to deployment server
ssh deploy@prod-deploy-server.communityshare.io

# Navigate to project directory
cd /opt/communityshare/api

# Pull latest code
git fetch origin
git checkout v2.5.0-maintenance

# Install dependencies
npm ci --production

# Build application
npm run build

# Run smoke tests
npm run test:smoke
```
**Expected Duration**: 15 minutes  
**Validation**: Smoke tests pass

**Step 2.2**: Restart API servers (rolling restart)
```bash
# Restart servers one at a time via deployment script
./scripts/rolling-restart.sh --service api --version v2.5.0

# Monitor health checks
watch -n 5 'curl https://api.communityshare.io/health'
```
**Expected Duration**: 10 minutes  
**Validation**: All health checks return 200 OK

**Step 2.3**: Deploy background job scheduler
```bash
# Deploy cron job configuration
kubectl apply -f k8s/maintenance-checker-cronjob.yaml

# Verify cron job created
kubectl get cronjobs -n production | grep maintenance-checker

# Check job schedule
kubectl describe cronjob maintenance-checker -n production
```
**Expected Duration**: 5 minutes  
**Validation**: CronJob shows correct schedule (0 6 * * *)

---

### Phase 3: Frontend Deployment (02:45 - 03:00 AM UTC)

**Step 3.1**: Deploy React application
```bash
# Build frontend with feature flag check
cd /opt/communityshare/frontend
npm ci
REACT_APP_FEATURE_MAINTENANCE=true npm run build

# Deploy to S3
aws s3 sync build/ s3://communityshare-frontend/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E2QWRTY123456 \
  --paths "/*"
```
**Expected Duration**: 10 minutes  
**Validation**: CloudFront serves new version

**Step 3.2**: Smoke test frontend
```bash
# Run automated E2E tests
npm run test:e2e:smoke -- --env=production
```
**Expected Duration**: 5 minutes  
**Validation**: All smoke tests pass

---

### Phase 4: Post-Deployment Validation (03:00 - 03:30 AM UTC)

**Step 4.1**: Manual testing
- [ ] Login to production as test user
- [ ] Navigate to Maintenance Calendar
- [ ] Create a new maintenance schedule
- [ ] Verify schedule appears in calendar
- [ ] Mark schedule as complete (create log)
- [ ] Verify log appears in maintenance history
- [ ] Check email notification sent

**Expected Duration**: 15 minutes

**Step 4.2**: Monitor metrics
```bash
# Check CloudWatch dashboard
# Verify:
- API error rate < 0.5%
- API latency p95 < 200ms
- Database connection pool healthy
- Background job ready to run
```

**Step 4.3**: Enable feature flag for internal team (Phase 1 rollout)
```javascript
// In LaunchDarkly dashboard
// Add targeting rule:
{
  "targets": [
    { "variation": 0, "values": ["internal-team-members"] }
  ]
}
```

**Expected Duration**: 5 minutes  
**Validation**: Internal team members can access feature

---

## Rollout Schedule

### Phase 1: Internal Team (Day 0-2)
- **Users**: ~10 internal team members
- **Duration**: 48 hours
- **Monitoring**: Hourly checks of error rates and user feedback
- **Success Criteria**: 
  - Zero critical bugs
  - All internal users successfully create schedules
  - Alert delivery rate > 95%

### Phase 2: Beta Users (Day 3-5)
- **Users**: ~100 beta testers (opted-in community admins)
- **Duration**: 72 hours
- **Monitoring**: Every 4 hours
- **Success Criteria**:
  - Error rate < 0.5%
  - User satisfaction score > 4/5
  - Performance metrics stable

### Phase 3: 25% Rollout (Day 6-7)
- **Users**: ~2,500 users (random selection)
- **Duration**: 48 hours
- **Monitoring**: Every 6 hours
- **Success Criteria**:
  - No increase in error rate
  - Database performance stable
  - Alert delivery success rate > 90%

### Phase 4: 50% Rollout (Day 8-9)
- **Users**: ~5,000 users
- **Duration**: 48 hours
- **Monitoring**: Daily
- **Success Criteria**:
  - All metrics within acceptable ranges
  - Support ticket volume normal

### Phase 5: 100% Rollout (Day 10+)
- **Users**: All users (~10,000)
- **Monitoring**: Ongoing
- **Success Criteria**:
  - Feature adoption rate > 50% within first month
  - User satisfaction maintained

---

## Monitoring & Observability

### CloudWatch Dashboard

**Dashboard Name**: `Maintenance-Feature-Production`

**Widgets**:
1. **API Metrics**
   - Request count per endpoint
   - Error rate per endpoint
   - Latency (p50, p95, p99) per endpoint

2. **Background Job Metrics**
   - Job execution count (daily)
   - Job execution duration
   - Job failure rate
   - Alerts generated count
   - Alert delivery success rate

3. **Database Metrics**
   - Connection pool utilization
   - Query execution time
   - Slow query count
   - Table sizes

4. **Application Metrics**
   - Active user count
   - Feature adoption rate
   - Schedule creation rate
   - Log creation rate

### PagerDuty Alerts

**Critical Alerts** (immediate notification):
- Background job failure rate > 10%
- API error rate > 5%
- Database connection pool exhausted
- Alert delivery rate < 80%

**Warning Alerts** (notification within 15 minutes):
- API latency p95 > 500ms
- Background job execution time > 5 minutes
- Database query time > 1 second

### Log Aggregation

All logs sent to CloudWatch Logs with structured format:
```json
{
  "timestamp": "2025-10-18T02:30:15Z",
  "level": "INFO",
  "service": "maintenance-api",
  "endpoint": "/api/maintenance/schedules",
  "method": "POST",
  "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "correlation_id": "abc123-def456",
  "duration_ms": 145,
  "status": 201
}
```

---

## Rollback Procedures

### Rollback Triggers
Initiate rollback if any of the following occur:
- Critical bug affecting > 10% of users
- API error rate > 10% for > 5 minutes
- Database performance degradation (p95 latency > 1 second)
- Background job completely failing
- Data corruption detected

### Rollback Steps

**Step 1: Disable Feature Flag (< 1 minute)**
```javascript
// In LaunchDarkly dashboard, set default variation to "Disabled"
// This immediately disables feature for all users
```

**Step 2: Stop Background Job (< 2 minutes)**
```bash
# Delete CronJob
kubectl delete cronjob maintenance-checker -n production

# Verify no jobs running
kubectl get jobs -n production | grep maintenance
```

**Step 3: Rollback Application Code (< 5 minutes)**
```bash
# Rollback to previous version
./scripts/rolling-restart.sh --service api --version v2.4.0

# Verify rollback
curl https://api.communityshare.io/version
# Should show v2.4.0
```

**Step 4: Rollback Database (< 10 minutes, only if necessary)**
```bash
# ONLY if data corruption detected
# Restore from backup
psql -U communityshare_admin -d communityshare_prod < backup_pre_maintenance_*.sql

# Run rollback migration
\i migrations/20250915_001_rollback.sql
```

**Step 5: Verify Rollback**
- [ ] Feature disabled in UI
- [ ] API endpoints return 404 for maintenance routes
- [ ] No background jobs running
- [ ] Database tables dropped (if full rollback)
- [ ] Monitor metrics return to normal

### Communication Plan

**During Rollback**:
1. Post status update on status page: "Investigating issues with new maintenance feature"
2. Notify internal team via Slack
3. Notify affected users via email (if applicable)
4. Update support team with known issues

**Post-Rollback**:
1. Send all-hands email with incident details
2. Schedule postmortem meeting within 24 hours
3. Document lessons learned
4. Create action items to prevent recurrence

---

## Post-Deployment Monitoring Period

### First 24 Hours
- **Frequency**: Hourly checks
- **On-call**: Primary and secondary engineer available
- **Focus**: Error rates, performance, user feedback

### First Week
- **Frequency**: Daily checks
- **Focus**: Adoption metrics, user satisfaction, edge cases

### First Month
- **Frequency**: Weekly review
- **Focus**: Long-term stability, feature utilization, optimization opportunities

---

## Success Metrics

### Technical Metrics (Day 1)
- [x] API error rate < 0.5%
- [x] API p95 latency < 200ms
- [x] Background job success rate > 95%
- [x] Alert delivery rate > 90%
- [x] Zero critical bugs

### User Adoption Metrics (Week 1)
- [ ] 20% of eligible users create at least one schedule
- [ ] 50% of created schedules have alerts enabled
- [ ] User satisfaction score > 4/5

### Business Metrics (Month 1)
- [ ] 50% of resources have maintenance schedules
- [ ] Average of 3+ schedules per resource
- [ ] 15% reduction in emergency repair requests
- [ ] 95% maintenance completion rate

---

## Rollback Decision Matrix

| Scenario | Severity | Action | Timeline |
|----------|----------|--------|----------|
| API error rate 5-10% | High | Monitor closely, prepare rollback | 10 minutes |
| API error rate > 10% | Critical | Immediate rollback | < 5 minutes |
| 1-2 critical bugs | High | Fix forward if possible, else rollback | 30 minutes |
| 3+ critical bugs | Critical | Immediate rollback | < 5 minutes |
| Performance degradation (2x slower) | High | Investigate, rollback if not fixed in 15 min | 15 minutes |
| Data corruption | Critical | Immediate rollback + DB restore | < 15 minutes |
| Background job failure | Medium | Investigate, disable job if not fixed in 30 min | 30 minutes |
| Alert delivery < 80% | Medium | Investigate Notification Service | 30 minutes |

---

## Communication Plan

### Pre-Deployment Announcement (Day -3)
**To**: All users  
**Channel**: Email, in-app notification  
**Message**:
```
🎉 New Feature Coming: Maintenance Scheduling

We're excited to announce a new feature launching on October 18th that will help you 
keep your resources in top condition. The Maintenance Scheduling & Alert System will 
allow you to:

- Schedule recurring maintenance for your resources
- Receive automatic alerts when maintenance is due
- Track maintenance history with notes and photos

Stay tuned for more details!
```

### Launch Day Announcement (Day 0)
**To**: Phased user groups  
**Channel**: Email  
**Message**:
```
✅ Maintenance Scheduling is Now Available!

You now have access to the new Maintenance Scheduling & Alert System. 

Get started:
1. Go to any resource page
2. Click "Schedule Maintenance"
3. Set up your first maintenance schedule

Need help? Check out our [User Guide] or contact support.
```

### Post-Launch Updates
- **Day 3**: Success metrics shared internally
- **Day 7**: Feature adoption stats shared with beta users
- **Day 14**: Public blog post about feature launch
- **Day 30**: Success story featuring high-adopting community

---

## Appendix

### Deployment Team Contacts

| Role | Name | Contact |
|------|------|---------|
| Deployment Lead | Alex Thompson | alex.t@communityshare.io |
| Backend Engineer | Sarah Chen | sarah.c@communityshare.io |
| Frontend Engineer | James Wilson | james.w@communityshare.io |
| DevOps Engineer | Maria Garcia | maria.g@communityshare.io |
| On-Call Primary | David Kim | david.k@communityshare.io |
| On-Call Secondary | Lisa Park | lisa.p@communityshare.io |
| Product Manager | Emma Rodriguez | emma.r@communityshare.io |

### Useful Links
- [Feature Documentation](https://docs.communityshare.io/maintenance-scheduling)
- [API Specification](https://docs.communityshare.io/api/maintenance)
- [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/dashboard/Maintenance-Feature-Production)
- [PagerDuty Service](https://communityshare.pagerduty.com/services/PXYZ123)
- [LaunchDarkly Feature Flag](https://app.launchdarkly.com/flags/maintenance_scheduling_enabled)
- [GitHub PR #342](https://github.com/communityshare/platform/pull/342)
- [Jira Epic PLAT-1523](https://communityshare.atlassian.net/browse/PLAT-1523)
