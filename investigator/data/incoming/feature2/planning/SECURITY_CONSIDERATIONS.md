# Security Considerations: QR Code Check-in/out

## Feature ID
FEAT-QR-002

## Overview
This document outlines security considerations, threats, vulnerabilities, and mitigation strategies for the QR code check-in/out feature. Given the nature of QR codes being easily photographed and shared, security is a critical concern for this feature.

## Security Threat Model

### Attack Surface
1. **QR Code Token Generation**: Backend API endpoints
2. **QR Code Validation**: Token verification logic
3. **Mobile Application**: Client-side security
4. **WebSocket Communication**: Real-time data channels
5. **Database**: Token storage and checkout records
6. **Network**: API and WebSocket traffic

### Trust Boundaries
```
Untrusted Zone          DMZ                  Trusted Zone
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│              │   │              │   │              │
│  Mobile App  │──▶│  API Gateway │──▶│  Backend API │
│  (Client)    │   │  WAF         │   │  Database    │
│              │   │              │   │              │
└──────────────┘   └──────────────┘   └──────────────┘
    Untrusted         Semi-trusted        Trusted
```

## Critical Vulnerabilities

### 1. Race Condition in Token Validation (CRITICAL)
**Vulnerability ID**: SEC-QR-001  
**Severity**: Critical  
**CVSS Score**: 8.1 (High)

#### Description
Time-of-check-time-of-use (TOCTOU) vulnerability in QR token validation allows concurrent requests to bypass one-time-use enforcement.

#### Attack Scenario
```typescript
// Vulnerable code (current implementation)
async function validateQRToken(token: string): Promise<ValidationResult> {
  // 1. Check if token exists and is valid
  const qrCode = await db.qrCodes.findUnique({ where: { token } });
  
  if (!qrCode) return { valid: false, reason: 'invalid_token' };
  if (qrCode.expiresAt < new Date()) return { valid: false, reason: 'expired' };
  if (qrCode.invalidatedAt) return { valid: false, reason: 'already_used' };
  
  // ⚠️ RACE CONDITION: Another request can pass validation here
  
  // 2. Mark token as used
  await db.qrCodes.update({
    where: { token },
    data: { invalidatedAt: new Date() }
  });
  
  return { valid: true, resourceId: qrCode.resourceId };
}
```

**Attack Steps**:
1. Attacker photographs QR code
2. Attacker sends 100 simultaneous checkout requests with the same token
3. Multiple requests pass validation before any can invalidate the token
4. Multiple checkouts created with single token

#### Impact
- Resource can be checked out multiple times by different users
- Inventory tracking becomes unreliable
- Potential for resource theft or double-booking

#### Current Status
🔴 **UNMITIGATED** - Known vulnerability, fix not implemented

#### Proposed Mitigation
**Option 1: Pessimistic Locking (Database-level)**
```typescript
async function validateQRToken(token: string): Promise<ValidationResult> {
  return await db.$transaction(async (tx) => {
    // SELECT FOR UPDATE locks the row
    const qrCode = await tx.$queryRaw`
      SELECT * FROM qr_codes 
      WHERE token = ${token} 
      FOR UPDATE
    `;
    
    if (!qrCode) return { valid: false, reason: 'invalid_token' };
    if (qrCode.expiresAt < new Date()) return { valid: false, reason: 'expired' };
    if (qrCode.invalidatedAt) return { valid: false, reason: 'already_used' };
    
    // Now safe to update - row is locked
    await tx.qrCodes.update({
      where: { id: qrCode.id },
      data: { invalidatedAt: new Date() }
    });
    
    return { valid: true, resourceId: qrCode.resourceId };
  });
}
```

**Option 2: Distributed Locking (Redis)**
```typescript
import { Redlock } from 'redlock';

async function validateQRToken(token: string): Promise<ValidationResult> {
  const lock = await redlock.acquire([`lock:qr:${token}`], 5000);
  
  try {
    const qrCode = await db.qrCodes.findUnique({ where: { token } });
    
    if (!qrCode) return { valid: false, reason: 'invalid_token' };
    if (qrCode.invalidatedAt) return { valid: false, reason: 'already_used' };
    
    await db.qrCodes.update({
      where: { token },
      data: { invalidatedAt: new Date() }
    });
    
    return { valid: true, resourceId: qrCode.resourceId };
  } finally {
    await lock.release();
  }
}
```

**Recommendation**: Implement Option 1 (Pessimistic Locking) as it:
- Requires no additional infrastructure (Redis)
- Provides stronger consistency guarantees
- Lower latency than distributed locks
- Simpler to implement and maintain

**Estimated Fix Time**: 2-3 days  
**Testing Required**: Load testing with 1000+ concurrent requests

---

### 2. QR Code Spoofing/Replay Attacks (HIGH)
**Vulnerability ID**: SEC-QR-002  
**Severity**: High  
**CVSS Score**: 7.4 (High)

#### Description
QR codes can be photographed, duplicated, and shared. Current implementation relies only on token expiration (15 minutes) to prevent reuse, which provides a large window for attack.

#### Attack Scenario
1. Legitimate user generates QR code for Resource A
2. Attacker photographs the QR code (using camera or screenshot)
3. Attacker shares the QR code image with multiple accomplices
4. Within 15-minute window, multiple people attempt to use the same QR code
5. Even with race condition fix, first scan succeeds, creating checkout

**Additional Concerns**:
- QR codes displayed on physical labels can be photographed once and reused repeatedly (until regenerated)
- No binding between QR code and intended user
- No verification that the person scanning is physically present at the resource

#### Impact
- Unauthorized resource checkouts
- Resource theft
- Circumvention of checkout approval workflows
- Difficult to trace actual user when token is shared

#### Current Status
🟡 **PARTIALLY MITIGATED** - Token expiration limits exposure window, but 15 minutes is significant

#### Proposed Mitigation Strategies

**Strategy 1: Device Fingerprinting (Implemented in Code, Not Enforced)**
```typescript
interface QRTokenPayload {
  resourceId: string;
  expiresAt: Date;
  nonce: string;
  deviceId?: string;  // ⚠️ Optional, not enforced
  signature: string;
}

// During generation
function generateQRToken(resourceId: string, deviceId: string) {
  const payload = {
    resourceId,
    deviceId,  // Bind to specific device
    expiresAt: new Date(Date.now() + 15 * 60 * 1000),
    nonce: crypto.randomBytes(16).toString('hex')
  };
  
  // ... generate signature
}

// During validation
function validateQRToken(token: string, requestDeviceId: string) {
  const payload = decodeToken(token);
  
  // ⚠️ NOT CURRENTLY ENFORCED
  if (payload.deviceId !== requestDeviceId) {
    return { valid: false, reason: 'device_mismatch' };
  }
  
  // ... continue validation
}
```

**Issues with Device Fingerprinting**:
- Device ID can be spoofed
- Not privacy-friendly (tracking concerns)
- Breaks legitimate use cases (device change, browser switch)

**Strategy 2: Reduce Token Expiration Time**
```typescript
// Current: 15 minutes
const EXPIRATION_TIME = 15 * 60 * 1000;

// Proposed: 2 minutes
const EXPIRATION_TIME = 2 * 60 * 1000;
```

**Pros**:
- Significantly reduces attack window
- Simple to implement
- No privacy concerns

**Cons**:
- Poor user experience (rushing to scan)
- May require regeneration if network issues
- Doesn't prevent sharing within 2-minute window

**Strategy 3: Biometric Verification (iOS/Android)**
```typescript
// Mobile app: Require biometric before scanning
async function scanQRCode() {
  // 1. Prompt for biometric
  const biometricResult = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Authenticate to checkout resource',
    fallbackLabel: 'Use passcode'
  });
  
  if (!biometricResult.success) {
    throw new Error('Biometric authentication failed');
  }
  
  // 2. Include biometric proof in request
  const biometricToken = generateBiometricProof(biometricResult);
  
  // 3. Proceed with QR scan
  // ...
}
```

**Pros**:
- Strong authentication
- Proves physical presence
- Native OS support

**Cons**:
- Not all devices support biometrics
- Additional complexity
- Privacy concerns (biometric data handling)

**Strategy 4: Location-Based Validation**
```typescript
interface QRTokenPayload {
  resourceId: string;
  locationId: string;  // Expected location
  geofenceRadius: number;  // In meters
}

async function validateQRToken(token: string, userLocation: GeoLocation) {
  const payload = decodeToken(token);
  const resource = await db.resources.findUnique({
    where: { id: payload.resourceId },
    include: { location: true }
  });
  
  const distance = calculateDistance(
    userLocation,
    resource.location.coordinates
  );
  
  if (distance > payload.geofenceRadius) {
    return { valid: false, reason: 'location_mismatch' };
  }
  
  // ... continue validation
}
```

**Pros**:
- Proves physical presence at resource
- Difficult to spoof (requires GPS spoofing)

**Cons**:
- Requires location permissions
- GPS accuracy issues indoors
- Privacy concerns
- Legitimate failures (GPS drift, building layout)

**Recommended Approach**: Layered defense
1. ✅ **Reduce token expiration to 5 minutes** (balance security vs UX)
2. ✅ **Implement rate limiting per device** (max 10 scans/minute)
3. 🟡 **Optional biometric verification** (user preference)
4. ❌ **Skip location verification** (too many false positives)

---

### 3. WebSocket Authentication Persistence (MEDIUM)
**Vulnerability ID**: SEC-WS-001  
**Severity**: Medium  
**CVSS Score**: 6.5 (Medium)

#### Description
WebSocket connections do not re-authenticate on reconnection, allowing potential session hijacking if connection token is compromised.

#### Attack Scenario
```typescript
// Current WebSocket setup (vulnerable)
io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  
  if (isValidJWT(token)) {
    socket.userId = extractUserId(token);
    next();
  } else {
    next(new Error('Authentication failed'));
  }
});

// ⚠️ On reconnection, uses same socket.id and credentials
// No re-validation of JWT expiration
```

**Attack Steps**:
1. Attacker intercepts WebSocket connection token (MITM, XSS, etc.)
2. User's JWT expires or is revoked
3. Attacker maintains active WebSocket connection
4. Attacker continues to receive real-time updates despite invalid JWT

#### Impact
- Unauthorized access to real-time resource availability data
- Information disclosure
- Potential for subscription to resources attacker shouldn't see

#### Current Status
🟡 **PARTIALLY MITIGATED** - JWT validation on initial connection only

#### Proposed Mitigation
```typescript
io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  
  if (!isValidJWT(token)) {
    return next(new Error('Authentication failed'));
  }
  
  socket.userId = extractUserId(token);
  next();
});

// Periodic re-authentication (every 5 minutes)
setInterval(() => {
  io.sockets.sockets.forEach((socket) => {
    const token = socket.handshake.auth.token;
    
    if (!isValidJWT(token)) {
      socket.emit('auth_expired', { reason: 'Token expired' });
      socket.disconnect(true);
    }
  });
}, 5 * 60 * 1000);

// Client-side: Handle re-authentication
socket.on('auth_expired', async () => {
  const newToken = await refreshAuthToken();
  socket.auth.token = newToken;
  socket.connect();
});
```

---

### 4. QR Code Token Cryptographic Weaknesses (MEDIUM)
**Vulnerability ID**: SEC-CRYPTO-001  
**Severity**: Medium  
**CVSS Score**: 5.9 (Medium)

#### Description
Current token signing uses HMAC-SHA256 with shared secret. If secret is compromised, attacker can forge arbitrary tokens.

#### Current Implementation
```typescript
function generateQRToken(resourceId: string): QRToken {
  const payload = {
    resource_id: resourceId,
    expires_at: new Date(Date.now() + 15 * 60 * 1000),
    nonce: crypto.randomBytes(16).toString('hex')
  };
  
  const payloadString = JSON.stringify(payload);
  
  // ⚠️ Symmetric key - if leaked, full compromise
  const signature = crypto
    .createHmac('sha256', process.env.QR_SECRET_KEY)
    .update(payloadString)
    .digest('hex');
  
  return {
    token: Buffer.from(payloadString).toString('base64'),
    signature
  };
}
```

#### Issues
- Symmetric key shared across all services
- Key rotation requires invalidating all active QR codes
- No forward secrecy
- Secret stored in environment variable (potential exposure)

#### Proposed Mitigation: Asymmetric Signing (JWT)
```typescript
import jwt from 'jsonwebtoken';

function generateQRToken(resourceId: string): string {
  const payload = {
    resource_id: resourceId,
    expires_at: Date.now() + 15 * 60 * 1000,
    nonce: crypto.randomBytes(16).toString('hex'),
    iat: Date.now()
  };
  
  // Sign with RSA private key
  const token = jwt.sign(payload, PRIVATE_KEY, {
    algorithm: 'RS256',
    expiresIn: '15m'
  });
  
  return token;
}

function validateQRToken(token: string): ValidationResult {
  try {
    // Verify with RSA public key
    const payload = jwt.verify(token, PUBLIC_KEY, {
      algorithms: ['RS256']
    });
    
    return { valid: true, resourceId: payload.resource_id };
  } catch (err) {
    return { valid: false, reason: err.message };
  }
}
```

**Benefits**:
- Public key can be distributed safely
- Key rotation only requires rotating private key
- Industry-standard JWT format
- Better audit trail (iat, exp claims)

**Recommendation**: Migrate to RS256 JWT signing in next major release

---

## Security Best Practices Implementation

### 1. Rate Limiting
```typescript
import rateLimit from 'express-rate-limit';

// QR generation rate limit
const qrGenerationLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each user to 100 QR generations per 15 minutes
  message: 'Too many QR codes generated, please try again later',
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => req.user.id // Per-user limiting
});

// QR scanning rate limit (per device)
const qrScanLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 10, // Max 10 scans per minute
  message: 'Too many scan attempts, please try again later',
  keyGenerator: (req) => req.headers['x-device-id'] || req.ip
});

app.post('/api/qr/generate', qrGenerationLimiter, generateQRCodeHandler);
app.post('/api/qr/validate', qrScanLimiter, validateQRCodeHandler);
```

#### Current Status
🔴 **NOT IMPLEMENTED** - No rate limiting in place

---

### 2. Input Validation
```typescript
import { z } from 'zod';

// QR token validation schema
const QRTokenSchema = z.object({
  token: z.string()
    .min(20)
    .max(1000)
    .regex(/^[A-Za-z0-9+/=]+$/), // Base64 only
});

// Checkout request validation
const CheckoutRequestSchema = z.object({
  token: z.string(),
  resourceId: z.string().uuid(),
  deviceId: z.string().max(255).optional(),
  clientVersion: z.string().max(50).optional()
});

// Middleware
function validateRequest(schema: z.ZodSchema) {
  return (req, res, next) => {
    try {
      schema.parse(req.body);
      next();
    } catch (err) {
      res.status(400).json({ error: 'Invalid request', details: err.errors });
    }
  };
}

app.post('/api/qr/validate', 
  validateRequest(QRTokenSchema), 
  validateQRCodeHandler
);
```

#### Current Status
🟡 **PARTIALLY IMPLEMENTED** - Basic validation exists, needs strengthening

---

### 3. Audit Logging
```typescript
async function auditQREvent(event: AuditEvent) {
  await db.qrAuditLog.create({
    data: {
      qrCodeId: event.qrCodeId,
      resourceId: event.resourceId,
      userId: event.userId,
      eventType: event.eventType,
      eventStatus: event.status,
      ipAddress: event.ipAddress,
      userAgent: event.userAgent,
      deviceId: event.deviceId,
      errorCode: event.errorCode,
      errorMessage: event.errorMessage
    }
  });
  
  // Also log to centralized logging (DataDog, Splunk, etc.)
  logger.info('QR Event', {
    event: event.eventType,
    status: event.status,
    userId: event.userId,
    resourceId: event.resourceId
  });
}

// Usage
await auditQREvent({
  qrCodeId: qrCode.id,
  resourceId: resource.id,
  userId: req.user.id,
  eventType: 'QR_VALIDATED',
  status: 'SUCCESS',
  ipAddress: req.ip,
  userAgent: req.headers['user-agent'],
  deviceId: req.headers['x-device-id']
});
```

#### Current Status
✅ **IMPLEMENTED** - Comprehensive audit logging in place

---

### 4. HTTPS/TLS Enforcement
```typescript
// Express middleware: Enforce HTTPS
app.use((req, res, next) => {
  if (req.headers['x-forwarded-proto'] !== 'https' && process.env.NODE_ENV === 'production') {
    return res.redirect(301, `https://${req.headers.host}${req.url}`);
  }
  next();
});

// HSTS header
app.use((req, res, next) => {
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
  next();
});
```

#### Current Status
✅ **IMPLEMENTED** - All traffic over HTTPS/TLS 1.3

---

### 5. Content Security Policy (CSP)
```typescript
import helmet from 'helmet';

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      connectSrc: ["'self'", "wss://api.communityshare.com"],
      imgSrc: ["'self'", "data:", "https:"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      frameSrc: ["'none'"],
      objectSrc: ["'none'"]
    }
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));
```

#### Current Status
🟡 **PARTIALLY IMPLEMENTED** - CSP configured but needs tuning

---

## Mobile App Security

### 1. Secure Storage (react-native-keychain)
```typescript
import * as Keychain from 'react-native-keychain';

class SecureStorage {
  async storeAuthToken(token: string) {
    await Keychain.setGenericPassword('auth_token', token, {
      service: 'com.communityshare.app',
      accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
      securityLevel: Keychain.SECURITY_LEVEL.SECURE_HARDWARE
    });
  }
  
  async getAuthToken(): Promise<string | null> {
    const credentials = await Keychain.getGenericPassword({
      service: 'com.communityshare.app'
    });
    
    return credentials ? credentials.password : null;
  }
}
```

#### Current Status
✅ **IMPLEMENTED** - Auth tokens stored in Keychain/Keystore

---

### 2. Root/Jailbreak Detection
```typescript
import JailMonkey from 'jail-monkey';

function checkDeviceSecurity() {
  const isJailBroken = JailMonkey.isJailBroken();
  const isDebuggable = JailMonkey.isDebuggable(); // Android
  
  if (isJailBroken) {
    Alert.alert(
      'Security Warning',
      'This app cannot run on jailbroken/rooted devices for security reasons.',
      [{ text: 'Exit', onPress: () => BackHandler.exitApp() }]
    );
    return false;
  }
  
  return true;
}
```

#### Current Status
🔴 **NOT IMPLEMENTED** - Recommended for production

---

### 3. Certificate Pinning (SSL Pinning)
```typescript
// react-native-ssl-pinning
import { fetch } from 'react-native-ssl-pinning';

const response = await fetch('https://api.communityshare.com/checkout', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify(checkoutData),
  sslPinning: {
    certs: ['api-cert-sha256']  // SHA256 hash of certificate
  }
});
```

#### Current Status
🔴 **NOT IMPLEMENTED** - Highly recommended for production

---

## Compliance & Privacy

### GDPR Considerations
- **QR Audit Logs**: Contains user actions and device IDs
  - Must allow user to request deletion (Right to Erasure)
  - Must inform user about logging (Privacy Policy)
  - Must implement data retention limits (90 days)

### Data Minimization
- Only collect necessary device information
- Don't log GPS coordinates unless required
- Pseudonymize device IDs where possible

### User Consent
```typescript
// First launch: Request consent for device tracking
async function requestTrackingConsent() {
  const consent = await AsyncStorage.getItem('tracking_consent');
  
  if (!consent) {
    Alert.alert(
      'Privacy Notice',
      'We collect device information to prevent fraud and improve security. Do you consent?',
      [
        { text: 'Decline', onPress: () => disableTracking() },
        { text: 'Accept', onPress: () => enableTracking() }
      ]
    );
  }
}
```

---

## Incident Response Plan

### Security Incident Levels

**Level 1 - LOW**: Minor security concern, no immediate risk
- Example: Single failed validation attempt
- Response: Log and monitor

**Level 2 - MEDIUM**: Suspicious activity detected
- Example: Multiple failed scans from same device
- Response: Rate limit, temporary device block, alert security team

**Level 3 - HIGH**: Active attack detected
- Example: 100+ failed validations in 1 minute
- Response: Block device/IP, invalidate all QR codes for affected resources, notify users

**Level 4 - CRITICAL**: System compromise suspected
- Example: Pattern of successful fraudulent checkouts
- Response: Disable QR checkout feature, full security audit, notify all users

### Incident Detection
```typescript
// Automated monitoring rules
const SECURITY_RULES = {
  maxFailedScansPerDevice: 10,
  maxFailedScansPerMinute: 50,
  maxCheckoutsPerUser: 20,
  suspiciousPatternThreshold: 0.8
};

// Real-time monitoring
function monitorSecurityEvents() {
  setInterval(async () => {
    // Check for suspicious patterns
    const recentFailures = await db.qrAuditLog.count({
      where: {
        eventStatus: 'FAILURE',
        createdAt: { gte: new Date(Date.now() - 60000) }
      }
    });
    
    if (recentFailures > SECURITY_RULES.maxFailedScansPerMinute) {
      await triggerSecurityAlert('HIGH', 'Excessive failed scans detected');
    }
  }, 30000); // Check every 30 seconds
}
```

---

## Penetration Testing Results

### Last Test Date
2025-10-08

### Findings Summary
| Finding | Severity | Status |
|---------|----------|--------|
| Race condition in token validation | Critical | 🔴 Open |
| QR spoofing possible | High | 🟡 Partial |
| WebSocket auth persistence | Medium | 🟡 Partial |
| No rate limiting | Medium | 🔴 Open |
| HMAC key rotation difficult | Medium | 🟡 Documented |
| No certificate pinning | Low | 🔴 Open |

### Recommendations from Pentest Team
1. **CRITICAL**: Fix race condition before production (BLOCKER)
2. **HIGH**: Implement rate limiting on all QR endpoints
3. **MEDIUM**: Add certificate pinning to mobile apps
4. **MEDIUM**: Periodic WebSocket re-authentication
5. **LOW**: Consider migrating to RS256 JWT signing

---

## Security Metrics & Monitoring

### Key Metrics
- Failed validation rate: < 5% (current: ~12% 🔴)
- Average scans per QR code: 1.2 (current: 1.8 🟡)
- Token expiration before use: < 10% (current: 15% 🟡)
- Security incidents: 0/month (current: 0 ✅)

### Alerting Thresholds
```typescript
const ALERT_THRESHOLDS = {
  failedValidations: {
    warning: 100 / 'hour',
    critical: 500 / 'hour'
  },
  suspiciousDevices: {
    warning: 5,
    critical: 20
  },
  tokenReuse: {
    warning: 1,
    critical: 5
  }
};
```

---

## Security Review Status

### Design Review
✅ **APPROVED** (2025-08-20) - Design approved with noted concerns

### Code Review
⚠️ **CONCERNS RAISED** - Race condition identified, fix required

### Penetration Testing
🔴 **FAILED** - Critical vulnerabilities found

### Security Team Review
❌ **BLOCKED** (2025-10-10) - Cannot proceed to production without:
1. Race condition fix (SEC-QR-001)
2. Rate limiting implementation
3. Re-penetration test after fixes

---

## Remediation Plan

### Phase 1: Critical Fixes (BLOCKER - 1 week)
- [ ] Implement pessimistic locking for token validation
- [ ] Add rate limiting (per-device and per-user)
- [ ] Load test race condition fix (1000+ concurrent requests)

### Phase 2: High Priority (2 weeks)
- [ ] Reduce token expiration to 5 minutes
- [ ] Implement periodic WebSocket re-authentication
- [ ] Add device fingerprinting enforcement

### Phase 3: Recommended (1 month)
- [ ] Certificate pinning in mobile apps
- [ ] Migrate to RS256 JWT signing
- [ ] Root/jailbreak detection
- [ ] Re-penetration test

### Phase 4: Nice-to-Have
- [ ] Optional biometric verification
- [ ] Advanced anomaly detection
- [ ] Key rotation automation

---

## References & Resources
- OWASP Mobile Security Project: https://owasp.org/www-project-mobile-security/
- OWASP API Security Top 10: https://owasp.org/www-project-api-security/
- JWT Best Practices: https://tools.ietf.org/html/rfc8725
- PostgreSQL Row Locking: https://www.postgresql.org/docs/current/explicit-locking.html

---

## Document Status
**Status**: 🔴 **CRITICAL ISSUES IDENTIFIED**  
**Last Updated**: 2025-10-15  
**Next Review**: After Phase 1 remediation  
**Approval**: ❌ **SECURITY TEAM BLOCKED** - Production deployment prohibited until critical fixes implemented
