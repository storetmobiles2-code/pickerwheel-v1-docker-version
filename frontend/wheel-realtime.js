/**
 * PickerWheel Real-Time WebSocket Support
 * Adds WebSocket capability for live updates from admin panel
 * Include this AFTER wheel.js
 * 
 * Features:
 * - Feature flag controlled (REALTIME_WHEEL_UPDATES)
 * - WebSocket with fallback polling
 * - Smooth wheel updates without disrupting spins
 * - Connection status indicator
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        POLLING_INTERVAL: 30000,  // Fallback polling every 30 seconds
        RECONNECT_ATTEMPTS: 10,
        RECONNECT_DELAY: 1000,
        CHECK_INTERVAL: 100,
        INIT_TIMEOUT: 10000
    };

    // State
    let realtimeEnabled = true;
    let pollingTimer = null;
    let lastPrizeHash = null;
    let connectionStatus = 'disconnected';

    // Wait for PickerWheelUI to be available
    const checkInterval = setInterval(() => {
        if (typeof PickerWheelUI !== 'undefined' && window.pickerWheel) {
            clearInterval(checkInterval);
            checkFeatureFlagAndInit();
        }
    }, CONFIG.CHECK_INTERVAL);

    // Timeout after 10 seconds
    setTimeout(() => clearInterval(checkInterval), CONFIG.INIT_TIMEOUT);

    /**
     * Check feature flag from /api/config before initializing
     */
    async function checkFeatureFlagAndInit() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();
            
            if (data.success && data.settings) {
                realtimeEnabled = data.settings.realtime_updates_enabled !== false;
                console.log(`🔧 Real-time updates feature flag: ${realtimeEnabled ? 'ENABLED' : 'DISABLED'}`);
            }
            
            if (realtimeEnabled) {
                initializeRealtime();
            } else {
                console.log('⏸️ Real-time updates disabled by feature flag');
            }
        } catch (error) {
            console.warn('⚠️ Could not check feature flag, defaulting to enabled:', error);
            initializeRealtime();
        }
    }

    /**
     * Initialize real-time updates (WebSocket + fallback polling)
     */
    function initializeRealtime() {
        const wheel = window.pickerWheel;
        
        // Calculate initial prize hash for change detection
        lastPrizeHash = calculatePrizeHash(wheel.availablePrizes);

        // Try WebSocket first
        if (typeof io !== 'undefined') {
            initializeWebSocket(wheel);
        } else {
            console.warn('⚠️ Socket.IO not loaded. Using polling fallback.');
            startPolling(wheel);
        }

        // Add connection status indicator
        addConnectionStatusIndicator();
        
        console.log('🔌 Real-time support initialized');
    }

    /**
     * Initialize WebSocket connection
     */
    function initializeWebSocket(wheel) {
        console.log('🔌 Initializing WebSocket connection...');

        const socket = io({
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: CONFIG.RECONNECT_DELAY,
            reconnectionAttempts: CONFIG.RECONNECT_ATTEMPTS
        });

        wheel.socket = socket;

        // Connection events
        socket.on('connect', () => {
            console.log('✅ WebSocket connected');
            updateConnectionStatus('connected');
            socket.emit('join', { room: 'wheel' });
            
            // Stop polling if it was active
            stopPolling();
        });

        socket.on('disconnect', () => {
            console.log('❌ WebSocket disconnected');
            updateConnectionStatus('disconnected');
            
            // Start polling as fallback
            startPolling(wheel);
        });

        socket.on('reconnect', (attemptNumber) => {
            console.log(`🔄 WebSocket reconnected after ${attemptNumber} attempts`);
            updateConnectionStatus('connected');
            stopPolling();
        });

        socket.on('connect_error', (error) => {
            console.warn('⚠️ WebSocket connection error:', error.message);
            updateConnectionStatus('error');
        });

        // Listen for prize updates from admin
        socket.on('prizes:updated', async (data) => {
            console.log('📦 Received prizes:updated event');
            handlePrizesUpdate(wheel, data.prizes);
        });

        socket.on('prize:added', async (data) => {
            console.log('➕ Prize added:', data.prize?.name);
            showRealtimeNotification(`New prize added: ${data.prize?.name}`, 'success');
            // Fetch fresh data to ensure consistency
            await refreshPrizesFromServer(wheel);
        });

        socket.on('prize:removed', async (data) => {
            console.log('➖ Prize removed:', data.prize_name);
            showRealtimeNotification(`Prize removed: ${data.prize_name}`, 'warning');
            // Fetch fresh data to ensure consistency
            await refreshPrizesFromServer(wheel);
        });

        socket.on('prize:enabled_changed', async (data) => {
            const status = data.is_enabled ? 'enabled' : 'disabled';
            console.log(`🔄 Prize ${status}:`, data.prize_name);
            // Fetch fresh data to update wheel
            await refreshPrizesFromServer(wheel);
        });

        socket.on('prize:inventory_updated', (data) => {
            console.log('📊 Inventory updated for prize:', data.prize_id);
            // Inventory updates don't require wheel rebuild
        });

        // Override spin completion to check for pending updates
        setupSpinCompletionHandler(wheel);

        console.log('🔌 WebSocket handlers registered');
    }

    /**
     * Start polling fallback
     */
    function startPolling(wheel) {
        if (pollingTimer) return; // Already polling
        
        console.log('🔄 Starting polling fallback...');
        updateConnectionStatus('polling');
        
        pollingTimer = setInterval(async () => {
            await refreshPrizesFromServer(wheel);
        }, CONFIG.POLLING_INTERVAL);
    }

    /**
     * Stop polling
     */
    function stopPolling() {
        if (pollingTimer) {
            clearInterval(pollingTimer);
            pollingTimer = null;
            console.log('⏹️ Polling stopped');
        }
    }

    /**
     * Refresh prizes from server
     */
    async function refreshPrizesFromServer(wheel) {
        try {
            const response = await fetch('/api/prizes/wheel-display?t=' + Date.now());
            const data = await response.json();
            
            if (data.success && data.prizes) {
                const newHash = calculatePrizeHash(data.prizes);
                
                // Only update if prizes have changed
                if (newHash !== lastPrizeHash) {
                    console.log('🔄 Prize changes detected, updating wheel...');
                    handlePrizesUpdate(wheel, data.prizes);
                    lastPrizeHash = newHash;
                }
            }
        } catch (error) {
            console.error('Error refreshing prizes:', error);
        }
    }

    /**
     * Calculate a hash of prizes for change detection
     */
    function calculatePrizeHash(prizes) {
        if (!prizes || !Array.isArray(prizes)) return '';
        return prizes.map(p => `${p.id || p.prize_id}:${p.name}:${p.is_enabled}`).join('|');
    }

    /**
     * Handle prize updates
     */
    function handlePrizesUpdate(wheel, prizes) {
        if (!prizes || prizes.length === 0) {
            console.warn('No prizes received');
            return;
        }

        // Don't update while spinning
        if (wheel.isSpinning) {
            console.log('⏳ Wheel is spinning, queuing update...');
            wheel._pendingPrizeUpdate = prizes;
            return;
        }

        updateWheelPrizes(wheel, prizes);
    }

    /**
     * Update wheel prizes and rebuild the wheel
     */
    function updateWheelPrizes(wheel, prizes) {
        try {
            // Get current rotation to preserve position
            const currentRotation = wheel.currentRotation || 0;
            
            // Transform prizes to expected format
            const formattedPrizes = prizes.map((prize) => ({
                id: prize.prize_id || prize.id,
                prize_id: prize.prize_id || prize.id,
                name: prize.name || prize.prize_name,
                category: prize.category_name || prize.category,
                category_name: prize.category_name || prize.category,
                emoji: prize.emoji || '🎁',
                is_enabled: prize.is_enabled !== false,
                remaining_quantity: prize.remaining_quantity || 0
            }));

            // Check what changed
            const oldCount = wheel.availablePrizes?.length || 0;
            const newCount = formattedPrizes.length;
            
            if (oldCount !== newCount) {
                console.log(`🎡 Prize count changed: ${oldCount} → ${newCount}`);
            }

            // Update wheel's prize list
            wheel.availablePrizes = formattedPrizes;

            // Rebuild the wheel with animation
            if (wheel.createWheel) {
                console.log(`🎡 Rebuilding wheel with ${formattedPrizes.length} prizes`);
                
                // Add a subtle fade effect during rebuild
                const wheelElement = document.getElementById('wheelInner');
                if (wheelElement) {
                    wheelElement.style.transition = 'opacity 0.3s';
                    wheelElement.style.opacity = '0.7';
                    
                    setTimeout(() => {
                        wheel.createWheel();
                        wheelElement.style.opacity = '1';
                    }, 150);
                } else {
                    wheel.createWheel();
                }
            }

            // Update stats display
            if (wheel.loadStats) {
                wheel.loadStats();
            }

            // Update the prize count display
            updatePrizeCountDisplay(formattedPrizes.length);

            console.log('✅ Wheel updated successfully');

        } catch (error) {
            console.error('Error updating wheel prizes:', error);
        }
    }

    /**
     * Setup spin completion handler to apply pending updates
     */
    function setupSpinCompletionHandler(wheel) {
        const originalShowWinModal = wheel.showWinModal?.bind(wheel);
        if (originalShowWinModal) {
            wheel.showWinModal = function(prize) {
                originalShowWinModal(prize);
                
                // Check for pending prize update after spin
                setTimeout(() => {
                    if (wheel._pendingPrizeUpdate) {
                        console.log('📦 Applying pending prize update...');
                        updateWheelPrizes(wheel, wheel._pendingPrizeUpdate);
                        wheel._pendingPrizeUpdate = null;
                    }
                }, 1000);
            };
        }
    }

    /**
     * Update prize count display
     */
    function updatePrizeCountDisplay(count) {
        const countElement = document.querySelector('.stat-value');
        if (countElement && countElement.closest('.stat-card')?.textContent.includes('Items')) {
            countElement.textContent = count;
        }
    }

    /**
     * Add connection status indicator to UI
     */
    function addConnectionStatusIndicator() {
        // Check if indicator already exists
        if (document.getElementById('realtime-status')) return;

        const indicator = document.createElement('div');
        indicator.id = 'realtime-status';
        indicator.style.cssText = `
            position: fixed;
            bottom: 10px;
            right: 10px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            z-index: 9999;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.3s ease;
            opacity: 0.8;
        `;
        
        document.body.appendChild(indicator);
        updateConnectionStatus('connecting');
    }

    /**
     * Update connection status indicator
     */
    function updateConnectionStatus(status) {
        connectionStatus = status;
        const indicator = document.getElementById('realtime-status');
        if (!indicator) return;

        const statusConfig = {
            connected: { color: '#22c55e', bg: 'rgba(34, 197, 94, 0.15)', text: '● Live', icon: '🟢' },
            disconnected: { color: '#dc2626', bg: 'rgba(220, 38, 38, 0.15)', text: '● Offline', icon: '🔴' },
            connecting: { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', text: '● Connecting...', icon: '🟡' },
            polling: { color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', text: '● Polling', icon: '🔵' },
            error: { color: '#dc2626', bg: 'rgba(220, 38, 38, 0.15)', text: '● Error', icon: '⚠️' }
        };

        const config = statusConfig[status] || statusConfig.disconnected;
        indicator.style.color = config.color;
        indicator.style.background = config.bg;
        indicator.innerHTML = `<span>${config.icon}</span><span>${config.text}</span>`;
    }

    /**
     * Show a notification for real-time updates
     */
    function showRealtimeNotification(message, type = 'info') {
        const notification = document.createElement('div');
        
        const typeStyles = {
            success: { bg: 'rgba(34, 197, 94, 0.95)', border: '#22c55e' },
            warning: { bg: 'rgba(245, 158, 11, 0.95)', border: '#f59e0b' },
            error: { bg: 'rgba(220, 38, 38, 0.95)', border: '#dc2626' },
            info: { bg: 'rgba(59, 130, 246, 0.95)', border: '#3b82f6' }
        };
        
        const style = typeStyles[type] || typeStyles.info;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: ${style.bg};
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            z-index: 10000;
            animation: slideDown 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            border-left: 4px solid ${style.border};
        `;
        notification.textContent = message;

        // Add animation keyframes
        if (!document.getElementById('realtime-notification-styles')) {
            const styleEl = document.createElement('style');
            styleEl.id = 'realtime-notification-styles';
            styleEl.textContent = `
                @keyframes slideDown {
                    from {
                        opacity: 0;
                        transform: translateX(-50%) translateY(-20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(-50%) translateY(0);
                    }
                }
            `;
            document.head.appendChild(styleEl);
        }

        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Expose for manual testing and external access
    window.WheelRealtime = {
        showNotification: showRealtimeNotification,
        getConnectionStatus: () => connectionStatus,
        isEnabled: () => realtimeEnabled,
        refresh: () => {
            if (window.pickerWheel) {
                refreshPrizesFromServer(window.pickerWheel);
            }
        }
    };

})();
