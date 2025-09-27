# Microphone Permission Storage

This implementation provides persistent microphone permission storage for the VoiceSportStat application, eliminating the need for users to grant permission every time they use the app.

## Features

- **Persistent Storage**: Uses localStorage to remember microphone permissions across browser sessions
- **Auto-Restore**: Automatically requests permission on app load if previously granted
- **Expiration**: Permissions expire after 30 days for security
- **Domain Security**: Permissions are tied to the specific domain
- **User Control**: Users can revoke permissions at any time
- **Visual Feedback**: Shows permission status, age, and expiration warnings

## How It Works

### PermissionStorage Class

The `PermissionStorage` class manages permission state in localStorage:

```typescript
// Store permission
PermissionStorage.setPermission(true);

// Check if permission exists
const hasPermission = PermissionStorage.hasStoredPermission();

// Get detailed permission info
const info = PermissionStorage.getPermissionInfo();

// Clear permission
PermissionStorage.clearPermission();
```

### AudioRecorder Integration

The `AudioRecorder` component automatically:

1. **On Mount**: Checks for stored permissions and restores them if valid
2. **On Permission Grant**: Saves the permission to localStorage
3. **On Permission Deny**: Clears any stored permission
4. **On Revoke**: Provides a button to manually clear stored permissions

### Security Features

- **Domain Binding**: Permissions are only valid for the domain where they were granted
- **Expiration**: Permissions automatically expire after 30 days
- **User Agent Check**: Basic validation to ensure permissions aren't transferred between different browsers
- **Manual Revoke**: Users can always revoke permissions

## Usage

The permission storage is automatically integrated into the AudioRecorder component. No additional setup is required.

### For Users

1. **First Time**: Click "Grant Microphone Permission" - permission will be saved
2. **Return Visits**: Permission will be automatically restored
3. **Revoke**: Click the "Revoke" button to clear saved permissions
4. **Expiration**: After 30 days, you'll need to grant permission again

### For Developers

The permission storage system is transparent to the rest of the application. The AudioRecorder component handles all permission management automatically.

## Storage Format

Permissions are stored in localStorage with the following structure:

```typescript
interface PermissionState {
	granted: boolean; // Whether permission was granted
	timestamp: number; // When permission was granted (Unix timestamp)
	domain: string; // Domain where permission was granted
	userAgent: string; // User agent for basic validation
}
```

## Browser Compatibility

- Works in all modern browsers that support localStorage
- Gracefully degrades if localStorage is not available
- No impact on functionality if permission storage fails
