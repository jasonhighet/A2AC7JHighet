# Mobile App Specification: QR Code Check-in/out

## Feature ID
FEAT-QR-002

## Overview
This document specifies the React Native mobile application for QR code-based resource check-in/out. The app provides a mobile-first experience for community members to quickly scan QR codes and manage resource checkouts without using the web interface.

## Technical Stack

### Core Technologies
- **Framework**: React Native 0.72.6
- **Language**: TypeScript 5.0.4
- **State Management**: Redux Toolkit 1.9.7 + RTK Query
- **Navigation**: React Navigation 6.1.9
- **UI Components**: React Native Paper 5.10.6
- **Camera Library**: react-native-camera 4.2.1 (⚠️ SECURITY VULNERABILITY)
- **Offline Storage**: AsyncStorage + WatermelonDB
- **Real-time**: Socket.io-client 4.6.1

### Native Dependencies
```json
{
  "react-native": "0.72.6",
  "react-native-camera": "4.2.1",
  "react-native-vector-icons": "10.0.0",
  "react-native-permissions": "3.10.1",
  "@react-navigation/native": "6.1.9",
  "@react-navigation/stack": "6.3.20",
  "@react-navigation/bottom-tabs": "6.5.11",
  "@reduxjs/toolkit": "1.9.7",
  "socket.io-client": "4.6.1",
  "@react-native-async-storage/async-storage": "1.19.5",
  "@nozbe/watermelondb": "0.27.1",
  "react-native-device-info": "10.11.0",
  "react-native-keychain": "8.1.2"
}
```

## App Architecture

### Screen Structure
```
App Navigator
├── Auth Flow (Stack)
│   ├── LoginScreen
│   ├── RegisterScreen
│   └── ForgotPasswordScreen
│
└── Main Flow (Bottom Tabs)
    ├── Home Tab (Stack)
    │   ├── HomeScreen
    │   └── ResourceDetailsScreen
    │
    ├── Scanner Tab (Stack)
    │   ├── ScannerScreen
    │   ├── ConfirmationScreen
    │   └── SuccessScreen
    │
    ├── History Tab (Stack)
    │   ├── CheckoutHistoryScreen
    │   └── CheckoutDetailsScreen
    │
    └── Profile Tab (Stack)
        ├── ProfileScreen
        └── SettingsScreen
```

### Component Hierarchy
```
src/
├── components/
│   ├── common/
│   │   ├── Button/
│   │   ├── Card/
│   │   ├── LoadingSpinner/
│   │   └── ErrorBoundary/
│   ├── scanner/
│   │   ├── QRScanner/
│   │   │   ├── QRScanner.tsx
│   │   │   ├── QRScanner.styles.ts
│   │   │   └── QRScanner.test.tsx
│   │   ├── ScannerOverlay/
│   │   └── ScannerGuide/
│   ├── checkout/
│   │   ├── CheckoutCard/
│   │   ├── ConfirmationModal/
│   │   └── CheckoutStatusBadge/
│   └── sync/
│       ├── SyncIndicator/
│       └── OfflineNotice/
│
├── screens/
│   ├── auth/
│   │   ├── LoginScreen/
│   │   └── RegisterScreen/
│   ├── home/
│   │   └── HomeScreen/
│   ├── scanner/
│   │   ├── ScannerScreen/
│   │   ├── ConfirmationScreen/
│   │   └── SuccessScreen/
│   ├── history/
│   │   └── CheckoutHistoryScreen/
│   └── profile/
│       ├── ProfileScreen/
│       └── SettingsScreen/
│
├── navigation/
│   ├── AppNavigator.tsx
│   ├── AuthNavigator.tsx
│   └── MainNavigator.tsx
│
├── store/
│   ├── index.ts
│   ├── slices/
│   │   ├── authSlice.ts
│   │   ├── checkoutSlice.ts
│   │   ├── resourceSlice.ts
│   │   └── syncSlice.ts
│   └── api/
│       ├── baseApi.ts
│       ├── authApi.ts
│       ├── checkoutApi.ts
│       └── resourceApi.ts
│
├── services/
│   ├── QRScanService.ts
│   ├── WebSocketService.ts
│   ├── SyncService.ts
│   ├── StorageService.ts
│   └── PermissionsService.ts
│
├── models/
│   ├── User.ts
│   ├── Resource.ts
│   ├── Checkout.ts
│   └── QRCode.ts
│
└── utils/
    ├── validators/
    │   ├── qrValidator.ts
    │   └── tokenValidator.ts
    ├── formatters/
    ├── constants/
    └── helpers/
```

## Screen Specifications

### 1. ScannerScreen

#### Purpose
Primary screen for scanning QR codes on resources.

#### UI Elements
- **Header**: "Scan QR Code" title, back button, help icon
- **Camera View**: Full-screen camera with overlay
- **Scanner Overlay**: Visual frame indicating scan area
- **Guide Text**: "Point camera at QR code on resource"
- **Flashlight Toggle**: Bottom-left corner
- **Gallery Button**: Bottom-right corner (manual QR upload)
- **Cancel Button**: Bottom-center

#### Behavior
```typescript
// Scanner Screen Logic
const ScannerScreen = () => {
  const [hasPermission, setHasPermission] = useState(false);
  const [scannedData, setScannedData] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  
  useEffect(() => {
    requestCameraPermission();
  }, []);
  
  const handleBarCodeScanned = async ({ data }: BarCodeScanEvent) => {
    if (isValidating) return;
    
    setIsValidating(true);
    setScannedData(data);
    
    // Vibrate for haptic feedback
    Vibration.vibrate(100);
    
    // Validate QR token
    const validation = await validateQRToken(data);
    
    if (validation.valid) {
      navigation.navigate('Confirmation', {
        resourceId: validation.resource_id,
        token: data
      });
    } else {
      showErrorAlert(validation.reason);
      setIsValidating(false);
    }
  };
  
  // ... rest of component
};
```

#### States
- **Idle**: Camera active, waiting for scan
- **Scanning**: QR detected, validating token
- **Success**: Token valid, navigating to confirmation
- **Error**: Invalid token, showing error message
- **No Permission**: Camera permission denied

#### Error Handling
```typescript
enum ScanError {
  INVALID_FORMAT = 'Invalid QR code format',
  EXPIRED_TOKEN = 'QR code has expired',
  ALREADY_USED = 'QR code has already been used',
  NETWORK_ERROR = 'Network error, try again',
  UNKNOWN = 'Unable to scan QR code'
}
```

### 2. ConfirmationScreen

#### Purpose
Confirm checkout/check-in action before completing.

#### UI Elements
- **Resource Card**:
  - Resource image (150x150)
  - Resource name (bold, 20px)
  - Resource category
  - Current availability status
- **Action Type**: "Check Out" or "Check In" (prominent)
- **Checkout Details** (if checking in):
  - Checked out by: {user}
  - Checked out at: {timestamp}
  - Duration: {calculated}
- **Confirm Button**: Large, primary color
- **Cancel Button**: Secondary, outline style

#### Behavior
```typescript
const ConfirmationScreen = ({ route, navigation }) => {
  const { resourceId, token, action } = route.params;
  const [resource, setResource] = useState<Resource | null>(null);
  const [loading, setLoading] = useState(false);
  
  const handleConfirm = async () => {
    setLoading(true);
    
    try {
      if (action === 'checkout') {
        await performCheckout(resourceId, token);
      } else {
        await performCheckin(resourceId, token);
      }
      
      navigation.navigate('Success', {
        action,
        resource
      });
    } catch (error) {
      showErrorAlert(error.message);
    } finally {
      setLoading(false);
    }
  };
  
  // ... rest of component
};
```

### 3. HomeScreen

#### Purpose
Dashboard showing available resources and recent activity.

#### UI Elements
- **Header**: "CommunityShare" logo, sync indicator
- **Search Bar**: Filter resources
- **Category Filter**: Horizontal scroll (Tools, Equipment, Spaces)
- **Available Resources List**:
  - Resource cards (image, name, category, status)
  - Pull-to-refresh
  - Infinite scroll pagination
- **Quick Actions**:
  - "Scan QR Code" FAB (bottom-right)
  - "My Checkouts" button
- **Real-time Badge**: Shows live update indicator

#### Real-time Updates
```typescript
const HomeScreen = () => {
  const dispatch = useDispatch();
  const resources = useSelector(selectAvailableResources);
  const wsConnected = useSelector(selectWebSocketStatus);
  
  useEffect(() => {
    // Connect to WebSocket
    WebSocketService.connect();
    
    // Subscribe to resource updates
    WebSocketService.on('resource_availability_changed', (data) => {
      dispatch(updateResourceAvailability(data));
    });
    
    return () => {
      WebSocketService.disconnect();
    };
  }, []);
  
  // ... rest of component
};
```

### 4. CheckoutHistoryScreen

#### Purpose
View user's checkout history and active checkouts.

#### UI Elements
- **Tabs**: "Active" | "Past"
- **Active Checkouts List**:
  - Resource cards with check-in action
  - Duration timer
  - "Check In" button
- **Past Checkouts List**:
  - Completed checkout records
  - Checkout/check-in timestamps
  - Duration
- **Filter**: Date range, resource type
- **Empty State**: "No checkouts yet"

## Navigation Flow

### Scanner Navigation
```
HomeScreen
    │
    ├─ [Tap "Scan QR Code" FAB]
    ↓
ScannerScreen
    │
    ├─ [QR Scanned Successfully]
    ↓
ConfirmationScreen
    │
    ├─ [User Confirms]
    ↓
SuccessScreen
    │
    └─ [Auto-navigate after 2s or tap "Done"]
    ↓
HomeScreen (refreshed)
```

### Deep Linking
```typescript
// Deep link configuration
const linking = {
  prefixes: ['communityshare://', 'https://app.communityshare.com'],
  config: {
    screens: {
      Scanner: 'scan',
      Confirmation: 'checkout/:token',
      ResourceDetails: 'resource/:id'
    }
  }
};

// Handle QR code URLs
// communityshare://checkout/{token}
```

## State Management

### Redux Store Structure
```typescript
interface RootState {
  auth: {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
  };
  
  checkout: {
    activeCheckouts: Checkout[];
    pendingCheckouts: PendingCheckout[];
    history: Checkout[];
    currentCheckout: Checkout | null;
  };
  
  resources: {
    available: Resource[];
    favorited: Resource[];
    categories: Category[];
  };
  
  sync: {
    isOnline: boolean;
    isSyncing: boolean;
    pendingOperations: number;
    lastSyncTime: Date | null;
  };
  
  websocket: {
    connected: boolean;
    reconnecting: boolean;
  };
}
```

### RTK Query API Endpoints
```typescript
export const checkoutApi = createApi({
  reducerPath: 'checkoutApi',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    }
  }),
  endpoints: (builder) => ({
    validateQRToken: builder.query<ValidationResult, string>({
      query: (token) => ({
        url: '/api/qr/validate',
        method: 'POST',
        body: { token }
      })
    }),
    
    performCheckout: builder.mutation<Checkout, CheckoutRequest>({
      query: (request) => ({
        url: '/api/checkout',
        method: 'POST',
        body: request
      }),
      invalidatesTags: ['Checkouts', 'Resources']
    }),
    
    performCheckin: builder.mutation<void, CheckinRequest>({
      query: (request) => ({
        url: '/api/checkin',
        method: 'POST',
        body: request
      }),
      invalidatesTags: ['Checkouts', 'Resources']
    }),
    
    getActiveCheckouts: builder.query<Checkout[], void>({
      query: () => '/api/checkout/active',
      providesTags: ['Checkouts']
    })
  })
});
```

## Offline Support

### Offline Queue Strategy
```typescript
interface PendingOperation {
  id: string;
  type: 'checkout' | 'checkin';
  resourceId: string;
  token: string;
  timestamp: Date;
  retryCount: number;
}

class SyncService {
  private queue: PendingOperation[] = [];
  
  async queueOperation(operation: PendingOperation) {
    // Add to queue
    this.queue.push(operation);
    
    // Persist to local storage
    await AsyncStorage.setItem('sync_queue', JSON.stringify(this.queue));
    
    // Notify user
    showToast('Operation queued for sync');
  }
  
  async syncPendingOperations() {
    if (!this.isOnline()) return;
    
    for (const operation of this.queue) {
      try {
        if (operation.type === 'checkout') {
          await api.performCheckout(operation);
        } else {
          await api.performCheckin(operation);
        }
        
        // Remove from queue on success
        this.removeFromQueue(operation.id);
      } catch (error) {
        operation.retryCount++;
        
        if (operation.retryCount > 3) {
          // Failed after 3 retries, notify user
          showNotification('Failed to sync checkout');
          this.removeFromQueue(operation.id);
        }
      }
    }
  }
  
  // Auto-sync when connection restored
  onConnectionChange(isOnline: boolean) {
    if (isOnline) {
      this.syncPendingOperations();
    }
  }
}
```

### Local Database (WatermelonDB)
```typescript
// Schema for offline data
const checkoutSchema = {
  name: 'checkouts',
  columns: [
    { name: 'resource_id', type: 'string', isIndexed: true },
    { name: 'user_id', type: 'string', isIndexed: true },
    { name: 'checked_out_at', type: 'number' },
    { name: 'checked_in_at', type: 'number', isOptional: true },
    { name: 'synced', type: 'boolean' },
    { name: 'qr_token', type: 'string' }
  ]
};
```

## Permissions Management

### Required Permissions

#### iOS (Info.plist)
```xml
<key>NSCameraUsageDescription</key>
<string>Camera access is required to scan QR codes on resources</string>

<key>NSPhotoLibraryUsageDescription</key>
<string>Photo library access allows you to select QR codes from your photos</string>

<key>NSLocationWhenInUseUsageDescription</key>
<string>Location helps us show nearby resources</string>
```

#### Android (AndroidManifest.xml)
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.VIBRATE" />
```

### Permission Flow
```typescript
class PermissionsService {
  async requestCameraPermission(): Promise<boolean> {
    const { status } = await Camera.requestCameraPermissionsAsync();
    
    if (status === 'denied') {
      Alert.alert(
        'Camera Permission Required',
        'Please enable camera access in Settings to scan QR codes.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Open Settings', onPress: () => Linking.openSettings() }
        ]
      );
      return false;
    }
    
    return status === 'granted';
  }
  
  async checkPermissionStatus(permission: Permission): Promise<PermissionStatus> {
    const result = await check(permission);
    return result;
  }
}
```

## WebSocket Integration

### Connection Management
```typescript
class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  
  connect(authToken: string) {
    this.socket = io(WS_URL, {
      auth: { token: authToken },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000
    });
    
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      store.dispatch(setWebSocketStatus('connected'));
    });
    
    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      store.dispatch(setWebSocketStatus('disconnected'));
    });
    
    this.socket.on('resource_availability_changed', (data) => {
      store.dispatch(updateResourceAvailability(data));
    });
    
    this.socket.on('checkout_completed', (data) => {
      store.dispatch(addCheckout(data));
      showNotification('Checkout completed successfully');
    });
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
  
  subscribeToResource(resourceId: string) {
    this.socket?.emit('subscribe_resource', { resourceId });
  }
}
```

## Security Implementation

### Token Storage
```typescript
import * as Keychain from 'react-native-keychain';

class SecureStorageService {
  async storeAuthToken(token: string) {
    await Keychain.setGenericPassword('auth_token', token, {
      service: 'com.communityshare.app',
      accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED
    });
  }
  
  async getAuthToken(): Promise<string | null> {
    const credentials = await Keychain.getGenericPassword({
      service: 'com.communityshare.app'
    });
    
    return credentials ? credentials.password : null;
  }
  
  async clearAuthToken() {
    await Keychain.resetGenericPassword({
      service: 'com.communityshare.app'
    });
  }
}
```

### SSL Pinning (Recommended)
```typescript
// iOS: Add SSL certificates to project
// Android: Add certificates to android/app/src/main/res/raw/

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  // SSL pinning configuration
  // Note: Requires native module setup
});
```

## Build & Deployment

### Build Configuration

#### iOS
```bash
# Development build
npx react-native run-ios --configuration Debug

# Production build
cd ios
pod install
xcodebuild -workspace CommunityShare.xcworkspace \
  -scheme CommunityShare \
  -configuration Release \
  -archivePath build/CommunityShare.xcarchive \
  archive
```

#### Android
```bash
# Development build
npx react-native run-android --variant=debug

# Production build
cd android
./gradlew assembleRelease
./gradlew bundleRelease  # For Play Store
```

### App Store Deployment

#### iOS App Store
- **Bundle ID**: com.communityshare.mobile
- **Minimum iOS Version**: 14.0
- **Supported Devices**: iPhone, iPad
- **Required Capabilities**: Camera, Network
- **App Transport Security**: Configured for HTTPS only

#### Google Play Store
- **Package Name**: com.communityshare.mobile
- **Minimum SDK**: 24 (Android 7.0)
- **Target SDK**: 33 (Android 13)
- **Permissions**: Camera, Internet, Vibrate
- **App Bundle**: Yes (required for Play Store)

## Testing Strategy

### Unit Tests
```typescript
// QRScanner component test
describe('QRScanner', () => {
  it('should request camera permission on mount', async () => {
    const { getByTestId } = render(<QRScanner />);
    expect(Camera.requestCameraPermissionsAsync).toHaveBeenCalled();
  });
  
  it('should validate QR token on scan', async () => {
    const mockValidate = jest.fn().mockResolvedValue({ valid: true });
    const { getByTestId } = render(<QRScanner />);
    
    fireEvent(getByTestId('camera'), 'barCodeScanned', {
      data: 'test-token'
    });
    
    await waitFor(() => {
      expect(mockValidate).toHaveBeenCalledWith('test-token');
    });
  });
});
```

### Integration Tests (Detox)
```typescript
describe('Checkout Flow', () => {
  beforeAll(async () => {
    await device.launchApp();
  });
  
  it('should complete full checkout flow', async () => {
    // Navigate to scanner
    await element(by.id('scan-fab')).tap();
    
    // Mock QR scan
    await element(by.id('camera')).tapAtPoint({ x: 50, y: 50 });
    
    // Confirm checkout
    await element(by.id('confirm-button')).tap();
    
    // Verify success screen
    await expect(element(by.text('Success!'))).toBeVisible();
  });
});
```

## Performance Considerations

### Optimization Strategies
- **Code Splitting**: Use React.lazy for screen components
- **Image Optimization**: Use react-native-fast-image for caching
- **List Performance**: Use FlatList with proper optimization props
- **Reduce Re-renders**: Use React.memo and useCallback
- **Bundle Size**: Analyze with react-native-bundle-visualizer

### Performance Targets
- App Launch Time: < 2 seconds
- Screen Navigation: < 300ms
- QR Scan Detection: < 500ms
- API Response Rendering: < 200ms
- Memory Usage: < 100MB (idle)

## Known Issues & Limitations

### Critical Issues
⚠️ **SEC-MOBILE-001**: react-native-camera 4.2.1 has a known security vulnerability (CVE-2023-XXXXX). Migration to react-native-vision-camera is required.

⚠️ **PERF-MOBILE-001**: App crashes on Android 11+ devices when camera permission is denied then re-granted without app restart.

⚠️ **SYNC-MOBILE-001**: Offline sync fails silently when queue exceeds 50 operations. No user feedback provided.

### Limitations
- Maximum 50 pending operations in offline queue
- QR scanner requires good lighting conditions
- WebSocket reconnection may take up to 30 seconds
- iOS < 14.0 not supported
- Android < 7.0 not supported

## Dependencies & Version Constraints

### Breaking Dependencies
```json
{
  "react-native-camera": "4.2.1",  // ⚠️ VULNERABLE - DO NOT UPDATE without testing
  "react-native": "0.72.6",        // ⚠️ 0.73.x has breaking changes
  "socket.io-client": "4.6.1"      // ⚠️ 5.x not compatible with backend
}
```

### Recommended Upgrades (Blocked)
- `react-native-camera` → `react-native-vision-camera` (MAJOR REFACTOR)
- `react-native` 0.72.6 → 0.74.x (BREAKING CHANGES)
- `@react-navigation` 6.x → 7.x (API CHANGES)

## Monitoring & Analytics

### Crash Reporting (Sentry)
```typescript
Sentry.init({
  dsn: SENTRY_DSN,
  environment: __DEV__ ? 'development' : 'production',
  enableAutoSessionTracking: true,
  tracesSampleRate: 1.0
});
```

### Analytics Events
```typescript
enum AnalyticsEvent {
  QR_SCAN_INITIATED = 'qr_scan_initiated',
  QR_SCAN_SUCCESS = 'qr_scan_success',
  QR_SCAN_FAILED = 'qr_scan_failed',
  CHECKOUT_COMPLETED = 'checkout_completed',
  CHECKIN_COMPLETED = 'checkin_completed',
  OFFLINE_OPERATION_QUEUED = 'offline_operation_queued',
  WEBSOCKET_CONNECTED = 'websocket_connected',
  WEBSOCKET_DISCONNECTED = 'websocket_disconnected'
}
```

## Documentation & Resources
- React Native Docs: https://reactnative.dev
- React Navigation: https://reactnavigation.org
- Redux Toolkit: https://redux-toolkit.js.org
- Socket.io Client: https://socket.io/docs/v4/client-api/

## Approval Status
❌ **PENDING IMPLEMENTATION** - Specification approved, implementation in progress with critical blockers.
