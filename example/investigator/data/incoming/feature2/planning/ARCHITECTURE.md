# Architecture Document: QR Code Check-in/out with Mobile App

## Feature ID
FEAT-QR-002

## System Architecture Overview

This feature introduces a mobile-first QR code scanning system with real-time synchronization capabilities. The architecture spans three main components: backend services, mobile application, and real-time communication layer.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Mobile Apps                          │
│  ┌──────────────┐              ┌──────────────┐        │
│  │ iOS App      │              │ Android App  │        │
│  │ React Native │              │ React Native │        │
│  └──────┬───────┘              └──────┬───────┘        │
│         │                              │                 │
│         └──────────────┬───────────────┘                │
└────────────────────────┼────────────────────────────────┘
                         │
                         │ HTTPS / WebSocket
                         │
┌────────────────────────┼────────────────────────────────┐
│                        │       Backend Services          │
│                        │                                 │
│    ┌───────────────────▼──────────────────┐            │
│    │      API Gateway / Load Balancer     │            │
│    └───────┬──────────────────────┬────────┘            │
│            │                      │                     │
│   ┌────────▼────────┐    ┌───────▼────────┐            │
│   │  REST API       │    │  WebSocket     │            │
│   │  Server         │    │  Server        │            │
│   │  (Express.js)   │    │  (Socket.io)   │            │
│   └────────┬────────┘    └───────┬────────┘            │
│            │                      │                     │
│   ┌────────▼────────┐    ┌───────▼────────┐            │
│   │  QR Generation  │    │  Event         │            │
│   │  Service        │    │  Broadcaster   │            │
│   └────────┬────────┘    └───────┬────────┘            │
│            │                      │                     │
│            └──────────┬───────────┘                     │
│                       │                                 │
│              ┌────────▼────────┐                        │
│              │   PostgreSQL     │                        │
│              │   Database       │                        │
│              └──────────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Mobile Application Architecture

#### Technology Stack
- **Framework**: React Native 0.72+
- **Language**: TypeScript 5.0+
- **State Management**: Redux Toolkit + RTK Query
- **Navigation**: React Navigation 6.x
- **Camera**: react-native-camera (to be migrated to react-native-vision-camera)
- **Storage**: AsyncStorage for local persistence
- **Networking**: Axios + Socket.io-client

#### App Structure
```
mobile-app/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── QRScanner/
│   │   ├── CheckoutCard/
│   │   └── SyncIndicator/
│   ├── screens/           # Screen components
│   │   ├── HomeScreen/
│   │   ├── ScannerScreen/
│   │   ├── ConfirmationScreen/
│   │   └── HistoryScreen/
│   ├── navigation/        # Navigation configuration
│   ├── store/            # Redux store
│   │   ├── slices/
│   │   │   ├── authSlice.ts
│   │   │   ├── checkoutSlice.ts
│   │   │   └── syncSlice.ts
│   │   └── api/
│   │       └── checkoutApi.ts
│   ├── services/         # Business logic
│   │   ├── QRScanService.ts
│   │   ├── SyncService.ts
│   │   └── WebSocketService.ts
│   └── utils/           # Utility functions
│       ├── qrValidator.ts
│       ├── storage.ts
│       └── permissions.ts
├── ios/                 # iOS native code
└── android/             # Android native code
```

#### Key Mobile Features

**QR Scanning Flow**:
1. User opens scanner screen
2. Camera permission check/request
3. QR code detection via react-native-camera
4. Token extraction and validation
5. API call to validate token
6. Confirmation screen display
7. User confirms action
8. API call to complete checkout
9. Success feedback

**Offline Mode**:
- Local SQLite queue for pending operations
- Background sync service
- Conflict resolution strategy: Server wins
- User notification when sync completes

**Real-time Updates**:
- WebSocket connection established on app launch
- Subscribe to resource availability events
- Update local state on receiving events
- Visual indicators for sync status

### 2. Backend API Architecture

#### Technology Stack
- **Runtime**: Node.js 18 LTS
- **Framework**: Express.js 4.18+
- **Language**: TypeScript 5.0+
- **Database**: PostgreSQL 14+
- **ORM**: Prisma 5.0+
- **WebSocket**: Socket.io 4.6+
- **QR Generation**: node-qrcode 1.5+
- **Crypto**: Node.js crypto module

#### API Server Structure
```
backend/
├── src/
│   ├── api/
│   │   ├── resources/
│   │   │   └── qr-code.controller.ts
│   │   └── checkin/
│   │       └── scan.controller.ts
│   ├── services/
│   │   ├── QRGenerationService.ts
│   │   ├── QRValidationService.ts
│   │   └── CheckoutService.ts
│   ├── models/
│   │   ├── QRCode.model.ts
│   │   └── Checkout.model.ts
│   ├── middleware/
│   │   ├── auth.middleware.ts
│   │   ├── rateLimit.middleware.ts
│   │   └── validation.middleware.ts
│   └── websocket/
│       ├── server.ts
│       ├── handlers/
│       └── events.ts
└── prisma/
    └── schema.prisma
```

### 3. QR Code Generation Service

#### Token Structure
```typescript
interface QRToken {
  resource_id: string;        // UUID of resource
  token: string;              // HMAC-SHA256 signed token
  expires_at: Date;           // 15 minute expiration
  nonce: string;              // Random nonce for uniqueness
  signature: string;          // Cryptographic signature
}
```

#### Generation Process
```typescript
// QR Token Generation Algorithm
function generateQRToken(resourceId: string): QRToken {
  const nonce = crypto.randomBytes(16).toString('hex');
  const expiresAt = new Date(Date.now() + 15 * 60 * 1000); // 15 min
  
  const payload = {
    resource_id: resourceId,
    nonce: nonce,
    expires_at: expiresAt.toISOString()
  };
  
  const payloadString = JSON.stringify(payload);
  const signature = crypto
    .createHmac('sha256', process.env.QR_SECRET_KEY)
    .update(payloadString)
    .digest('hex');
  
  const token = Buffer.from(payloadString).toString('base64');
  
  return {
    resource_id: resourceId,
    token: token,
    expires_at: expiresAt,
    nonce: nonce,
    signature: signature
  };
}
```

#### QR Code Format
- **Protocol**: `communityshare://checkout/{token}`
- **Encoding**: UTF-8
- **Error Correction**: Level Q (25%)
- **Size**: 200x200px minimum

### 4. WebSocket Real-time Architecture

#### Socket.io Configuration
```typescript
// WebSocket Server Setup
const io = new Server(httpServer, {
  cors: {
    origin: process.env.ALLOWED_ORIGINS,
    credentials: true
  },
  transports: ['websocket', 'polling'],
  pingTimeout: 60000,
  pingInterval: 25000
});

// Authentication Middleware
io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  if (isValidJWT(token)) {
    socket.userId = extractUserId(token);
    next();
  } else {
    next(new Error('Authentication failed'));
  }
});
```

#### Event Flow
```
Mobile App                 WebSocket Server              Database
    │                            │                          │
    │ ─── connect() ───────────> │                          │
    │ <── authenticated ──────── │                          │
    │                            │                          │
    │ ─── subscribe(resource) ─> │                          │
    │                            │                          │
    │ [User scans QR]           │                          │
    │                            │                          │
    │ ─── POST /checkout ──────> │ ─── INSERT ──────────> │
    │                            │ <── success ─────────── │
    │ <── 200 OK ─────────────── │                          │
    │                            │                          │
    │                            │ ─── broadcast ────────> │
    │ <── resource_updated ───── │                          │
    │                            │                          │
    │ [All clients updated]     │                          │
```

#### WebSocket Events

**Client → Server**:
- `subscribe_resource`: Subscribe to resource availability updates
- `unsubscribe_resource`: Unsubscribe from resource updates
- `ping`: Keepalive heartbeat

**Server → Client**:
- `resource_availability_changed`: Resource availability updated
- `checkout_completed`: Checkout operation completed
- `checkin_completed`: Check-in operation completed
- `error`: Error notification

### 5. Database Schema

#### New Tables

**qr_codes**:
```sql
CREATE TABLE qr_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id UUID NOT NULL REFERENCES resources(id),
  token TEXT NOT NULL UNIQUE,
  signature TEXT NOT NULL,
  nonce TEXT NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  invalidated_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by UUID REFERENCES users(id),
  
  INDEX idx_token (token),
  INDEX idx_resource_id (resource_id),
  INDEX idx_expires_at (expires_at)
);
```

#### Modified Tables

**checkouts** (add QR tracking):
```sql
ALTER TABLE checkouts 
ADD COLUMN qr_code_id UUID REFERENCES qr_codes(id),
ADD COLUMN checkout_method VARCHAR(20) DEFAULT 'web' 
  CHECK (checkout_method IN ('web', 'qr', 'api'));
```

### 6. Security Architecture

#### Token Security
- **HMAC-SHA256 Signature**: Prevents token tampering
- **15-minute Expiration**: Limits exposure window
- **One-time Use**: Token invalidated after successful scan
- **Nonce**: Prevents replay attacks
- **Rate Limiting**: Max 10 scans per minute per user

#### Validation Flow
```typescript
function validateQRToken(token: string): ValidationResult {
  // 1. Decode base64 token
  const payload = JSON.parse(Buffer.from(token, 'base64').toString());
  
  // 2. Check expiration
  if (new Date(payload.expires_at) < new Date()) {
    return { valid: false, reason: 'expired' };
  }
  
  // 3. Verify signature
  const signature = generateSignature(payload);
  if (signature !== payload.signature) {
    return { valid: false, reason: 'invalid_signature' };
  }
  
  // 4. Check database for invalidation
  const qrCode = await db.qrCodes.findUnique({
    where: { token: token }
  });
  
  if (qrCode?.invalidated_at) {
    return { valid: false, reason: 'already_used' };
  }
  
  // 5. Atomic invalidation with transaction
  await db.$transaction(async (tx) => {
    const existing = await tx.qrCodes.findUnique({
      where: { token: token },
      select: { invalidated_at: true }
    });
    
    if (existing?.invalidated_at) {
      throw new Error('Token already used');
    }
    
    await tx.qrCodes.update({
      where: { token: token },
      data: { invalidated_at: new Date() }
    });
  });
  
  return { valid: true, resource_id: payload.resource_id };
}
```

#### Current Security Issues (CRITICAL)
⚠️ **Race Condition (SEC-QR-001)**: Current validation logic has a TOCTOU vulnerability where concurrent scans can bypass the one-time-use check. Fixed requires distributed locking or pessimistic locking at database level.

⚠️ **QR Spoofing (SEC-QR-002)**: QR codes can be photographed and duplicated. Mitigation requires device fingerprinting or biometric validation.

⚠️ **WebSocket Auth (SEC-WS-001)**: WebSocket reconnection does not re-authenticate the connection, allowing potential session hijacking.

### 7. Integration Points

#### Existing System Integration
- **Resource Management API**: Validates resource availability
- **User Authentication**: JWT token validation
- **Notification Service**: Sends checkout confirmations
- **Audit Logging**: Records all checkout activities

#### Third-party Integrations
- **Apple Push Notification Service (APNs)**: iOS notifications
- **Firebase Cloud Messaging (FCM)**: Android notifications
- **Sentry**: Error tracking and monitoring
- **DataDog**: Performance monitoring and metrics

### 8. Deployment Architecture

#### Infrastructure
```
┌─────────────────────────────────────────┐
│           Load Balancer (AWS ALB)        │
└────────────┬───────────────┬────────────┘
             │               │
    ┌────────▼────────┐  ┌──▼────────────┐
    │  API Server     │  │ WebSocket     │
    │  (ECS Fargate)  │  │ Server        │
    │  3 instances    │  │ (ECS Fargate) │
    └────────┬────────┘  │ 2 instances   │
             │           └───┬───────────┘
             │               │
    ┌────────▼───────────────▼────────┐
    │     PostgreSQL (RDS)             │
    │     Multi-AZ, Read Replicas      │
    └──────────────────────────────────┘
```

#### Scaling Strategy
- **Horizontal Scaling**: Auto-scale API and WebSocket servers based on CPU/memory
- **WebSocket Sticky Sessions**: Use AWS ALB session affinity
- **Database Read Replicas**: Offload read queries for QR validation
- **CDN**: CloudFront for QR code image delivery

### 9. Performance Considerations

#### Latency Targets
- QR Generation: < 100ms (p95)
- QR Validation: < 200ms (p95)
- Checkout Complete: < 300ms (p95)
- WebSocket Message Delivery: < 100ms (p95)

#### Current Performance Issues (CRITICAL)
⚠️ **WebSocket Bottleneck**: Server drops connections at >50 concurrent users. Investigation shows:
- Socket.io default settings not tuned for scale
- Missing connection pooling
- No load balancing for WebSocket connections
- Memory leak in event broadcaster

#### Optimization Strategies (Proposed)
- Implement Redis adapter for Socket.io clustering
- Add WebSocket connection pooling
- Optimize database queries with proper indexing
- Implement caching layer for frequently accessed resources

### 10. Monitoring & Observability

#### Key Metrics
- QR scan success/failure rate
- Token validation latency
- WebSocket connection count
- Message delivery latency
- API endpoint response times
- Mobile app crash rate

#### Alerting Thresholds
- WebSocket connections > 100: Warning
- Token validation errors > 5%: Critical
- API latency > 500ms (p95): Warning
- Database connection pool exhaustion: Critical

## Architecture Review Status

✅ **Approved Components**:
- QR token generation algorithm
- Database schema design
- Mobile app architecture
- API endpoint design

⚠️ **Components Requiring Rework**:
- WebSocket scaling architecture (performance issues identified)
- QR token validation (race condition vulnerability)
- Mobile app dependency (security vulnerability in react-native-camera)

## Next Steps

1. Resolve WebSocket performance bottleneck (BLOCKING)
2. Fix QR token race condition (CRITICAL SECURITY)
3. Upgrade react-native-camera or migrate to react-native-vision-camera (HIGH SECURITY)
4. Complete load testing with >100 concurrent users
5. Security review re-approval after fixes
