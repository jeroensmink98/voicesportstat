import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PermissionStorage } from './PermissionStorage';

// Mock localStorage
const localStorageMock = {
	getItem: vi.fn(),
	setItem: vi.fn(),
	removeItem: vi.fn(),
	clear: vi.fn(),
	length: 0,
	key: vi.fn()
};

Object.defineProperty(window, 'localStorage', {
	value: localStorageMock
});

// Mock window.location
Object.defineProperty(window, 'location', {
	value: {
		hostname: 'localhost'
	}
});

// Mock navigator.userAgent
Object.defineProperty(navigator, 'userAgent', {
	value: 'Mozilla/5.0 (Test Browser)'
});

describe('PermissionStorage', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should store permission state', () => {
		PermissionStorage.setPermission(true);

		expect(localStorageMock.setItem).toHaveBeenCalledWith(
			'voicesportstat_microphone_permission',
			expect.stringContaining('"granted":true')
		);
	});

	it('should retrieve permission state', () => {
		const mockPermission = {
			granted: true,
			timestamp: Date.now(),
			domain: 'localhost',
			userAgent: 'Mozilla/5.0 (Test Browser)'
		};

		localStorageMock.getItem.mockReturnValue(JSON.stringify(mockPermission));

		const permission = PermissionStorage.getPermission();
		expect(permission).toEqual(mockPermission);
	});

	it('should return null for expired permission', () => {
		const expiredPermission = {
			granted: true,
			timestamp: Date.now() - 31 * 24 * 60 * 60 * 1000, // 31 days ago
			domain: 'localhost',
			userAgent: 'Mozilla/5.0 (Test Browser)'
		};

		localStorageMock.getItem.mockReturnValue(JSON.stringify(expiredPermission));

		const permission = PermissionStorage.getPermission();
		expect(permission).toBeNull();
		expect(localStorageMock.removeItem).toHaveBeenCalledWith(
			'voicesportstat_microphone_permission'
		);
	});

	it('should return null for different domain', () => {
		const differentDomainPermission = {
			granted: true,
			timestamp: Date.now(),
			domain: 'different-domain.com',
			userAgent: 'Mozilla/5.0 (Test Browser)'
		};

		localStorageMock.getItem.mockReturnValue(JSON.stringify(differentDomainPermission));

		const permission = PermissionStorage.getPermission();
		expect(permission).toBeNull();
	});

	it('should check if permission was previously granted', () => {
		const mockPermission = {
			granted: true,
			timestamp: Date.now(),
			domain: 'localhost',
			userAgent: 'Mozilla/5.0 (Test Browser)'
		};

		localStorageMock.getItem.mockReturnValue(JSON.stringify(mockPermission));

		expect(PermissionStorage.hasStoredPermission()).toBe(true);
	});

	it('should clear permission state', () => {
		PermissionStorage.clearPermission();

		expect(localStorageMock.removeItem).toHaveBeenCalledWith(
			'voicesportstat_microphone_permission'
		);
	});

	it('should get permission age', () => {
		const twoDaysAgo = Date.now() - 2 * 24 * 60 * 60 * 1000;
		const mockPermission = {
			granted: true,
			timestamp: twoDaysAgo,
			domain: 'localhost',
			userAgent: 'Mozilla/5.0 (Test Browser)'
		};

		localStorageMock.getItem.mockReturnValue(JSON.stringify(mockPermission));

		const age = PermissionStorage.getPermissionAge();
		expect(age).toBe(2);
	});

	it('should detect expiring permission', () => {
		const twentyFiveDaysAgo = Date.now() - 25 * 24 * 60 * 60 * 1000;
		const mockPermission = {
			granted: true,
			timestamp: twentyFiveDaysAgo,
			domain: 'localhost',
			userAgent: 'Mozilla/5.0 (Test Browser)'
		};

		localStorageMock.getItem.mockReturnValue(JSON.stringify(mockPermission));

		expect(PermissionStorage.isPermissionExpiringSoon()).toBe(true);
	});

	it('should get permission info', () => {
		const twoDaysAgo = Date.now() - 2 * 24 * 60 * 60 * 1000;
		const mockPermission = {
			granted: true,
			timestamp: twoDaysAgo,
			domain: 'localhost',
			userAgent: 'Mozilla/5.0 (Test Browser)'
		};

		localStorageMock.getItem.mockReturnValue(JSON.stringify(mockPermission));

		const info = PermissionStorage.getPermissionInfo();
		expect(info).toEqual({
			hasPermission: true,
			age: 2,
			isExpiringSoon: false,
			domain: 'localhost'
		});
	});
});
