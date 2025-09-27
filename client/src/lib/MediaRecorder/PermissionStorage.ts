/**
 * Permission storage utility for managing microphone permissions
 * Uses localStorage to persist permission state across browser sessions
 */

export interface PermissionState {
	granted: boolean;
	timestamp: number;
	domain: string;
	userAgent: string;
}

export class PermissionStorage {
	private static readonly STORAGE_KEY = 'voicesportstat_microphone_permission';
	private static readonly PERMISSION_EXPIRY_DAYS = 30; // Permissions expire after 30 days

	/**
	 * Store microphone permission state
	 */
	static setPermission(granted: boolean): void {
		const permissionState: PermissionState = {
			granted,
			timestamp: Date.now(),
			domain: window.location.hostname,
			userAgent: navigator.userAgent
		};

		try {
			localStorage.setItem(this.STORAGE_KEY, JSON.stringify(permissionState));
			console.log('Microphone permission state saved:', permissionState);
		} catch (error) {
			console.warn('Failed to save permission state to localStorage:', error);
		}
	}

	/**
	 * Get stored microphone permission state
	 */
	static getPermission(): PermissionState | null {
		try {
			const stored = localStorage.getItem(this.STORAGE_KEY);
			if (!stored) return null;

			const permissionState: PermissionState = JSON.parse(stored);

			// Check if permission is expired
			const now = Date.now();
			const expiryTime = this.PERMISSION_EXPIRY_DAYS * 24 * 60 * 60 * 1000; // Convert days to milliseconds

			if (now - permissionState.timestamp > expiryTime) {
				console.log('Stored permission has expired, clearing...');
				this.clearPermission();
				return null;
			}

			// Check if permission is from same domain and similar user agent
			if (permissionState.domain !== window.location.hostname) {
				console.log('Permission from different domain, ignoring...');
				return null;
			}

			return permissionState;
		} catch (error) {
			console.warn('Failed to read permission state from localStorage:', error);
			return null;
		}
	}

	/**
	 * Check if microphone permission was previously granted
	 */
	static hasStoredPermission(): boolean {
		const permission = this.getPermission();
		return permission?.granted === true;
	}

	/**
	 * Clear stored permission state
	 */
	static clearPermission(): void {
		try {
			localStorage.removeItem(this.STORAGE_KEY);
			console.log('Microphone permission state cleared');
		} catch (error) {
			console.warn('Failed to clear permission state from localStorage:', error);
		}
	}

	/**
	 * Get permission age in days
	 */
	static getPermissionAge(): number | null {
		const permission = this.getPermission();
		if (!permission) return null;

		const now = Date.now();
		const ageMs = now - permission.timestamp;
		return Math.floor(ageMs / (24 * 60 * 60 * 1000));
	}

	/**
	 * Check if permission is about to expire (within 7 days)
	 */
	static isPermissionExpiringSoon(): boolean {
		const age = this.getPermissionAge();
		if (age === null) return false;

		return age >= this.PERMISSION_EXPIRY_DAYS - 7;
	}

	/**
	 * Get permission info for display
	 */
	static getPermissionInfo(): {
		hasPermission: boolean;
		age: number | null;
		isExpiringSoon: boolean;
		domain: string | null;
	} {
		const permission = this.getPermission();
		return {
			hasPermission: permission?.granted === true,
			age: this.getPermissionAge(),
			isExpiringSoon: this.isPermissionExpiringSoon(),
			domain: permission?.domain || null
		};
	}
}
