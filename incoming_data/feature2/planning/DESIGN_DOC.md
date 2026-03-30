# Design Document: QR Code Check-in/out with Mobile App

## Feature ID
FEAT-QR-002

## Design Overview
A mobile-first QR code scanning solution that enables instant resource check-in and check-out through a React Native mobile application. The design prioritizes speed, simplicity, and accessibility while maintaining security.

## Mobile App Design

### Platform-Specific Considerations

#### iOS (iOS 14+)
- Native-feeling navigation with iOS design patterns
- Face ID / Touch ID integration for security
- iOS-style alerts and confirmations
- Camera access follows iOS permission model
- Push notifications via APNs

#### Android (Android 8+)
- Material Design 3 components
- Fingerprint authentication where available
- Android-style bottom sheets and snackbars
- Camera access follows Android permission model
- Push notifications via FCM

### Screen Designs

#### Home Screen
```
┌──────────────────────────┐
│  ☰  CommunityShare    🔔 │
├──────────────────────────┤
│                          │
│   [QR CODE ICON]         │
│                          │
│   Scan to Check         │
│   In/Out                │
│                          │
│   ┌──────────────────┐   │
│   │  Scan QR Code    │   │
│   └──────────────────┘   │
│                          │
│   ┌──────────────────┐   │
│   │  My Checkouts    │   │
│   └──────────────────┘   │
│                          │
│   ┌──────────────────┐   │
│   │  Browse Tools    │   │
│   └──────────────────┘   │
│                          │
└──────────────────────────┘
```

**Design Notes**:
- Large, tappable scan button (minimum 48x48dp touch target)
- High contrast for accessibility
- Clear visual hierarchy
- Quick access to primary action

#### QR Scanner Screen
```
┌──────────────────────────┐
│  ←  Scan QR Code      💡 │
├──────────────────────────┤
│                          │
│  ┌────────────────────┐  │
│  │                    │  │
│  │    [CAMERA VIEW]   │  │
│  │                    │  │
│  │    ┌──────────┐    │  │
│  │    │          │    │  │
│  │    │ SCANNING │    │  │
│  │    │   AREA   │    │  │
│  │    │          │    │  │
│  │    └──────────┘    │  │
│  │                    │  │
│  └────────────────────┘  │
│                          │
│  "Position QR code       │
│   within the frame"      │
│                          │
│  [ ] Auto-scan           │
│                          │
└──────────────────────────┘
```

**Design Notes**:
- Clear scanning guide overlay
- Flashlight toggle (💡) for low-light conditions
- Auto-scan toggle for continuous scanning mode
- Visual feedback when QR detected (green highlight)
- Error messages displayed below camera view

#### Checkout Confirmation Screen
```
┌──────────────────────────┐
│  ←  Confirm Checkout     │
├──────────────────────────┤
│                          │
│  ┌────────────────────┐  │
│  │   [TOOL IMAGE]     │  │
│  └────────────────────┘  │
│                          │
│  Milwaukee Drill Press   │
│  Model: DP-4550          │
│                          │
│  ━━━━━━━━━━━━━━━━━━━━━  │
│                          │
│  Location: Workshop A    │
│  Condition: Good         │
│  Last serviced: 10/1/25  │
│                          │
│  ━━━━━━━━━━━━━━━━━━━━━  │
│                          │
│  ⚠️ Max checkout: 7 days │
│                          │
│  ┌──────────────────┐    │
│  │ ✓ Check Out      │    │
│  └──────────────────┘    │
│                          │
│  [Cancel]                │
│                          │
└──────────────────────────┘
```

**Design Notes**:
- Clear tool identification with image
- Important metadata displayed upfront
- Warning badges for restrictions
- Large, primary action button
- Secondary cancel action (less prominent)

#### Success State
```
┌──────────────────────────┐
│  ✓  Checked Out          │
├──────────────────────────┤
│                          │
│        ✓                 │
│   [SUCCESS ICON]         │
│                          │
│  Milwaukee Drill Press   │
│  successfully checked    │
│  out to you.             │
│                          │
│  Due back: Oct 23, 2025  │
│                          │
│  ┌──────────────────┐    │
│  │  View My Items   │    │
│  └──────────────────┘    │
│                          │
│  [Scan Another]          │
│                          │
└──────────────────────────┘
```

**Design Notes**:
- Clear success feedback with icon and color
- Key information (due date) highlighted
- Quick navigation to next actions
- Auto-dismiss after 3 seconds option

#### Error States

**Expired QR Code**:
```
┌──────────────────────────┐
│  ⚠️  QR Code Expired     │
├──────────────────────────┤
│                          │
│  This QR code is no      │
│  longer valid.           │
│                          │
│  Please request a new    │
│  QR code from the        │
│  resource page or scan   │
│  the current code on     │
│  the tool.               │
│                          │
│  ┌──────────────────┐    │
│  │  Try Again       │    │
│  └──────────────────┘    │
│                          │
└──────────────────────────┘
```

**Offline Mode**:
```
┌──────────────────────────┐
│  🔄  Queued for Sync     │
├──────────────────────────┤
│                          │
│  ℹ️ No internet          │
│  connection detected.    │
│                          │
│  Your checkout has been  │
│  saved and will sync     │
│  automatically when      │
│  connection is restored. │
│                          │
│  Milwaukee Drill Press   │
│                          │
│  ┌──────────────────┐    │
│  │  OK              │    │
│  └──────────────────┘    │
│                          │
│  [View Queue: 1 item]    │
│                          │
└──────────────────────────┘
```

#### History Screen
```
┌──────────────────────────┐
│  ←  My Checkout History  │
├──────────────────────────┤
│                          │
│  ┌────────────────────┐  │
│  │ 🔧 Drill Press     │  │
│  │ Checked out        │  │
│  │ Oct 16, 2:30 PM    │  │
│  │ Due: Oct 23        │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ 🪚 Circular Saw    │  │
│  │ Returned           │  │
│  │ Oct 14, 4:15 PM    │  │
│  └────────────────────┘  │
│                          │
│  ┌────────────────────┐  │
│  │ 🔨 Nail Gun        │  │
│  │ Returned           │  │
│  │ Oct 10, 11:22 AM   │  │
│  └────────────────────┘  │
│                          │
└──────────────────────────┘
```

## UI/UX Patterns

### Camera Permission Request
- **When**: On first scan attempt (not on app launch)
- **Why**: Better UX, reduces friction for new users
- **Message**: "CommunityShare needs camera access to scan QR codes for checking out tools"

### Loading States
- Skeleton screens for content loading
- Spinner for API calls
- Progress indicators for sync operations

### Real-time Sync Indicator
```
Connection status in header:
● Connected (green dot)
🔄 Syncing (animated)
⚠️ Offline (yellow)
```

### Accessibility
- Minimum 48x48dp touch targets
- Sufficient color contrast (WCAG AA)
- Screen reader support for all interactive elements
- Voice guidance for QR scanning
- Alternative text for all icons
- Support for large text sizes

## QR Code Design

### Physical QR Code Requirements
- **Size**: 200x200px minimum (scales to physical 2" x 2")
- **Format**: PNG with transparent or white background
- **Error correction**: Level Q (25% damage tolerance)
- **Border**: 4-module quiet zone (white space around code)

### QR Code Label Template
```
┌────────────────────────┐
│  CommunityShare        │
│                        │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
│  ▓▓▓▓  QR CODE  ▓▓▓▓  │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
│                        │
│  Milwaukee Drill Press │
│  ID: TOOL-4550         │
│                        │
│  Scan to check in/out  │
│                        │
└────────────────────────┘
```

### Digital QR Code Display
- Display in web interface for printing
- Download as high-res PNG
- Print instructions included
- Batch generation for multiple resources

## Animations & Transitions

### Scan Success Animation
1. QR code detected: Green border flash (200ms)
2. Fade to confirmation screen (300ms)
3. Scale-in success icon (400ms)

### Real-time Update Animation
When another user checks out a tool:
1. Tool card slides out (300ms)
2. "Not Available" badge fades in (200ms)
3. Haptic feedback (iOS) or vibration (Android)

## Design Review Decisions

### Approved (2025-08-20)
✅ QR Code Size: 200x200px minimum for easy scanning
✅ Offline Mode: Queue scans for later sync when network unavailable
✅ Camera Permissions: Request on first scan attempt (not on app launch)

### Design Tokens
```css
/* Colors */
--primary: #2196F3
--success: #4CAF50
--warning: #FF9800
--error: #F44336
--background: #FFFFFF
--surface: #F5F5F5
--text-primary: #212121
--text-secondary: #757575

/* Spacing */
--spacing-xs: 4px
--spacing-sm: 8px
--spacing-md: 16px
--spacing-lg: 24px
--spacing-xl: 32px

/* Typography */
--font-size-sm: 12px
--font-size-md: 16px
--font-size-lg: 20px
--font-size-xl: 24px
```

## Responsive Behavior
- Portrait mode primary (QR scanning works best in portrait)
- Landscape support for history and browsing
- Tablet support with larger touch targets
- Fold-able device support (Galaxy Fold, etc.)

## Dark Mode Support
- System-level dark mode detection
- All screens have dark mode variants
- Adjusted QR scanner overlay for dark mode
- Reduced blue light in scanning interface

## Performance Considerations
- Image caching for tool photos
- Progressive loading for history
- Optimistic UI updates for instant feedback
- Background sync for offline operations
