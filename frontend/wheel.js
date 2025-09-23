/**
 * PickerWheel UI - Clean Implementation
 * Focused on proper wheel mechanics and UI
 */

class PickerWheelUI {
    constructor() {
        // Use relative path for API calls to work with any host/port
        this.apiBaseUrl = '/api';
        this.wheel = null;
        this.wheelInner = null;
        this.spinButton = null;
        this.wheelPointer = null;
        this.currentRotation = 0;
        this.isSpinning = false;
        this.availablePrizes = [];
        this.segments = [];
        this.segmentAngle = 0;
        
        // Audio system
        this.audioContext = null;
        this.tickSound = null;
        this.tickInterval = null;
        
        // 🎵 Enhanced Audio System with Asset Sounds
        this.audioElements = {
            spinSound: null,
            winSound: null,
            rareWinSound: null
        };
        
        // Settings
        this.soundEnabled = true;
        this.effectsEnabled = true;
        
        // Daily prizes log state
        this.dailyPrizesLog = [];
        this.logDisplayHidden = false;
        
        // Mobile responsiveness
        this.isMobile = this.detectMobile();
        
        this.init();
    }

    // 📱 MOBILE DETECTION
    detectMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               window.innerWidth <= 768;
    }

    // 🎨 GET COMBO EMOJI DISPLAY
    getComboEmojiDisplay(prizeName) {
        const comboMappings = {
            'smartwatch + mini cooler': '⌚+❄️',
            'power bank + neckband': '🔋+🎧', 
            'earbuds and g.speaker': '🎧+🔊'
        };
        
        const normalizedName = prizeName.toLowerCase().trim();
        return comboMappings[normalizedName] || null;
    }

    // 📱 GET MOBILE-OPTIMIZED SIZES
    getMobileSizes() {
        if (this.isMobile) {
            return {
                wheelSize: Math.min(window.innerWidth * 0.9, 450), // 90% of screen width, max 450px
                fontSize: {
                    emoji: '16px',
                    text: '11px',
                    modal: '4rem'
                },
                spinButton: '60px'
            };
        } else {
            return {
                wheelSize: 400,
                fontSize: {
                    emoji: '14px',
                    text: '10px',
                    modal: '3rem'
                },
                spinButton: '50px'
            };
        }
    }

    async init() {
        try {
            console.log('🎯 Initializing PickerWheel UI...');
            
            // Get DOM elements
            this.wheel = document.getElementById('wheel');
            this.wheelInner = document.getElementById('wheelInner');
            this.spinButton = document.getElementById('spinButton');
            this.wheelPointer = document.getElementById('wheelPointer');
            this.wheelSparks = document.getElementById('wheelSparks');
            this.loadingOverlay = document.getElementById('loadingOverlay');
            this.modalOverlay = document.getElementById('modalOverlay');
            this.soundToggle = document.getElementById('soundToggle');
            this.effectsToggle = document.getElementById('effectsToggle');
            
            if (!this.wheel || !this.wheelInner || !this.spinButton) {
                throw new Error('Required DOM elements not found');
            }

            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize audio system
            this.initAudio();
            
            // Load settings
            this.loadSettings();
            
            // Load initial data
            await this.loadAvailablePrizes();
            await this.loadStats();
            
            // Create wheel
            this.createWheel();
            
            // Initialize daily prizes log
            this.initializeDailyPrizesLog();
            
            console.log('✅ PickerWheel UI initialized successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize UI:', error);
            this.showError('Failed to initialize the contest. Please refresh the page.');
        }
    }

    setupEventListeners() {
        // Spin button
        this.spinButton.addEventListener('click', () => this.spin());
        
        // Modal close
        const closeModal = document.getElementById('closeModal');
        if (closeModal) {
            closeModal.addEventListener('click', () => this.closeModal());
        }
        
        // Close modal on overlay click
        if (this.modalOverlay) {
            this.modalOverlay.addEventListener('click', (e) => {
                if (e.target === this.modalOverlay) {
                    this.closeModal();
                }
            });
        }
        
        // Control buttons
        if (this.soundToggle) {
            this.soundToggle.addEventListener('click', () => this.toggleSound());
        }
        
        if (this.effectsToggle) {
            this.effectsToggle.addEventListener('click', () => this.toggleEffects());
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && !this.isSpinning) {
                e.preventDefault();
                this.spin();
            } else if (e.code === 'Escape') {
                this.closeModal();
            }
        });
    }

    initAudio() {
        try {
            // Initialize Web Audio API
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('🔊 Audio system initialized');
            
            // 🎵 Load sound assets
            this.loadSoundAssets();
        } catch (error) {
            console.warn('⚠️ Audio not supported:', error);
        }
    }
    
    loadSoundAssets() {
        try {
            // Create audio elements for different sounds
            this.audioElements.spinSound = new Audio('sounds/spin-sound.mp3');
            this.audioElements.winSound = new Audio('sounds/win-sound.mp3');
            this.audioElements.rareWinSound = new Audio('sounds/rare-win-sound.mp3');
            
            // Configure audio elements
            Object.values(this.audioElements).forEach(audio => {
                if (audio) {
                    audio.preload = 'auto';
                    audio.volume = 0.7; // Set default volume
                    
                    // Handle loading events
                    audio.addEventListener('canplaythrough', () => {
                        console.log('🎵 Sound loaded:', audio.src.split('/').pop());
                    });
                    
                    audio.addEventListener('error', (e) => {
                        console.warn('⚠️ Failed to load sound:', audio.src.split('/').pop(), e);
                    });
                    
                    // Handle browser audio policy restrictions
                    audio.addEventListener('play', () => {
                        console.log('🎵 Audio playing:', audio.src.split('/').pop());
                    });
                }
            });
            
            // Add click handler to enable audio context (required by browsers)
            this.enableAudioOnFirstInteraction();
            
            console.log('🎵 Loading sound assets...');
        } catch (error) {
            console.warn('⚠️ Failed to initialize sound assets:', error);
        }
    }
    
    enableAudioOnFirstInteraction() {
        const enableAudio = () => {
            // Resume audio context if suspended
            if (this.audioContext && this.audioContext.state === 'suspended') {
                this.audioContext.resume().then(() => {
                    console.log('🔊 Audio context enabled on user interaction');
                });
            }
            
            // Test load all audio elements
            Object.values(this.audioElements).forEach(audio => {
                if (audio) {
                    audio.load(); // Reload to ensure they're ready
                }
            });
            
            // Remove this listener after first interaction
            document.removeEventListener('click', enableAudio);
            document.removeEventListener('touchstart', enableAudio);
            console.log('🎵 Audio system fully enabled');
        };
        
        // Listen for first user interaction
        document.addEventListener('click', enableAudio);
        document.addEventListener('touchstart', enableAudio);
    }

    createTickSound(frequency = 800, duration = 0.1, volume = 0.3) {
        if (!this.audioContext) return null;

        try {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            // Connect nodes
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            // Configure oscillator
            oscillator.type = 'square';
            oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
            
            // Configure gain (volume) with quick fade
            gainNode.gain.setValueAtTime(volume, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
            
            return { oscillator, gainNode };
        } catch (error) {
            console.warn('⚠️ Failed to create tick sound:', error);
            return null;
        }
    }

    playTickSound(volume = 0.3) {
        const sound = this.createTickSound(800, 0.1, volume);
        if (sound) {
            sound.oscillator.start();
            sound.oscillator.stop(this.audioContext.currentTime + 0.1);
        }
    }

    startTickingSound() {
        if (!this.audioContext || !this.soundEnabled) return;

        // Resume audio context if suspended (required by some browsers)
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }

        const wheelDuration = 6200; // Total wheel animation duration
        const soundDuration = 5000; // Sound stops 1.2 seconds before wheel stops
        const startTime = Date.now();
        let tickCount = 0;
        const initialInterval = 60; // Start with faster ticks
        const finalInterval = 600; // End with much slower ticks

        const tick = () => {
            const elapsed = Date.now() - startTime;
            
            // Stop sound before wheel animation completes or if spinning stopped
            if (elapsed >= soundDuration || !this.isSpinning) {
                this.tickInterval = null;
                console.log('🔇 Sound faded out before wheel stops');
                return;
            }

            // Calculate progress based on sound duration (not wheel duration)
            const progress = elapsed / soundDuration;
            
            // Calculate volume fade with dramatic fade-out at the end
            // Use exponential curve for more realistic fade
            const volumeFactor = Math.max(0.05, Math.pow(1 - progress, 2));
            const volume = 0.4 * volumeFactor;

            // Play tick sound
            this.playTickSound(volume);

            tickCount++;

            // Calculate next interval based on progress (gradually slow down)
            // Use cubic easing to match the wheel's deceleration curve
            const easedProgress = 1 - Math.pow(1 - progress, 3);
            let nextInterval = initialInterval + (finalInterval - initialInterval) * easedProgress;
            
            // In the final 20% of sound duration, make ticks much slower and quieter
            if (progress > 0.8) {
                const finalPhase = (progress - 0.8) / 0.2; // 0 to 1 in final 20%
                nextInterval = nextInterval + (800 * finalPhase); // Up to 800ms between final ticks
            }

            // Schedule next tick
            this.tickInterval = setTimeout(tick, nextInterval);
        };

        // Start ticking
        tick();
    }

    stopTickingSound() {
        if (this.tickInterval) {
            clearTimeout(this.tickInterval);
            this.tickInterval = null;
            console.log('🔇 Ticking sound stopped');
        }
    }
    
    // 🎵 Enhanced Sound Methods
    playSpinSound() {
        if (!this.soundEnabled || !this.audioElements.spinSound) return;
        
        try {
            this.audioElements.spinSound.currentTime = 0; // Reset to beginning
            this.audioElements.spinSound.play().catch(e => {
                console.warn('⚠️ Failed to play spin sound:', e);
            });
            console.log('🎵 Playing spin sound');
        } catch (error) {
            console.warn('⚠️ Error playing spin sound:', error);
        }
    }
    
    playWinSound(category = 'common') {
        if (!this.soundEnabled) return;
        
        try {
            let soundToPlay;
            
            // Choose sound based on prize category
            if (category === 'rare' || category === 'ultra_rare') {
                soundToPlay = this.audioElements.rareWinSound;
                console.log('🎵 Playing rare win celebration sound');
            } else {
                soundToPlay = this.audioElements.winSound;
                console.log('🎵 Playing win celebration sound');
            }
            
            if (soundToPlay) {
                soundToPlay.currentTime = 0; // Reset to beginning
                soundToPlay.play().catch(e => {
                    console.warn('⚠️ Failed to play win sound:', e);
                });
            }
        } catch (error) {
            console.warn('⚠️ Error playing win sound:', error);
        }
    }
    
    stopAllSounds() {
        try {
            // Stop all audio elements
            Object.values(this.audioElements).forEach(audio => {
                if (audio && !audio.paused) {
                    audio.pause();
                    audio.currentTime = 0;
                }
            });
            
            // Stop ticking sound
            this.stopTickingSound();
            
            console.log('🔇 All sounds stopped');
        } catch (error) {
            console.warn('⚠️ Error stopping sounds:', error);
        }
    }

    startSpinningEffects() {
        if (!this.effectsEnabled) return;
        
        // Start pointer vibration
        if (this.wheelPointer) {
            this.wheelPointer.classList.add('vibrating');
        }
        
        // Start friction sparks at pointer contact
        if (this.wheelSparks) {
            this.wheelSparks.classList.add('spinning');
        }
        
        console.log('🎪 Started spinning effects - pointer vibration and friction sparks');
    }

    stopSpinningEffects() {
        // Stop pointer vibration
        if (this.wheelPointer) {
            this.wheelPointer.classList.remove('vibrating');
        }
        
        // Stop friction sparks
        if (this.wheelSparks) {
            this.wheelSparks.classList.remove('spinning');
        }
        
        console.log('🎪 Stopped spinning effects');
    }

    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        
        if (this.soundToggle) {
            if (this.soundEnabled) {
                this.soundToggle.classList.remove('disabled');
                this.soundToggle.title = 'Disable Sound';
            } else {
                this.soundToggle.classList.add('disabled');
                this.soundToggle.title = 'Enable Sound';
                // Stop any currently playing sound
                this.stopAllSounds();
            }
        }
        
        // Save preference
        localStorage.setItem('picker_wheel_sound', this.soundEnabled);
        console.log('🔊 Sound', this.soundEnabled ? 'enabled' : 'disabled');
    }

    toggleEffects() {
        this.effectsEnabled = !this.effectsEnabled;
        
        if (this.effectsToggle) {
            if (this.effectsEnabled) {
                this.effectsToggle.classList.remove('disabled');
                this.effectsToggle.title = 'Disable Effects';
            } else {
                this.effectsToggle.classList.add('disabled');
                this.effectsToggle.title = 'Enable Effects';
                // Stop any currently running effects
                this.stopSpinningEffects();
            }
        }
        
        // Save preference
        localStorage.setItem('picker_wheel_effects', this.effectsEnabled);
        console.log('✨ Effects', this.effectsEnabled ? 'enabled' : 'disabled');
    }

    loadSettings() {
        // Load sound preference
        const savedSound = localStorage.getItem('picker_wheel_sound');
        if (savedSound !== null) {
            this.soundEnabled = savedSound === 'true';
        }
        
        // Load effects preference
        const savedEffects = localStorage.getItem('picker_wheel_effects');
        if (savedEffects !== null) {
            this.effectsEnabled = savedEffects === 'true';
        }
        
        // Update button states
        if (this.soundToggle) {
            if (this.soundEnabled) {
                this.soundToggle.classList.remove('disabled');
                this.soundToggle.title = 'Disable Sound';
            } else {
                this.soundToggle.classList.add('disabled');
                this.soundToggle.title = 'Enable Sound';
            }
        }
        
        if (this.effectsToggle) {
            if (this.effectsEnabled) {
                this.effectsToggle.classList.remove('disabled');
                this.effectsToggle.title = 'Disable Effects';
            } else {
                this.effectsToggle.classList.add('disabled');
                this.effectsToggle.title = 'Enable Effects';
            }
        }
        
        console.log('⚙️ Settings loaded - Sound:', this.soundEnabled, 'Effects:', this.effectsEnabled);
    }

    async loadAvailablePrizes() {
        try {
            console.log('📦 Loading all prizes for wheel display...');
            
            const response = await fetch(`${this.apiBaseUrl}/prizes/wheel-display`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load prizes');
            }
            
            this.availablePrizes = data.prizes;
            console.log(`✅ Loaded ${this.availablePrizes.length} prizes for wheel display`);
            console.log('All wheel prizes (ordered by ID):', this.availablePrizes.map((p, i) => `Segment ${i}: ID ${p.id} - ${p.name}`));
            
        } catch (error) {
            console.error('❌ Failed to load prizes:', error);
            throw error;
        }
    }

    async loadStats() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/stats`);
            const data = await response.json();
            
            if (data.success) {
                this.updateStatsDisplay(data.stats);
            }
        } catch (error) {
            console.warn('⚠️ Failed to load stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        const statsGrid = document.getElementById('statsGrid');
        if (!statsGrid) return;

        statsGrid.innerHTML = `
            <div class="stat-item">
                <span class="stat-value">${stats.total_wins || 0}</span>
                <span class="stat-label">Total Wins Today</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${this.availablePrizes.length}</span>
                <span class="stat-label">Available Prizes</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${stats.unique_users || 0}</span>
                <span class="stat-label">Participants</span>
            </div>
        `;
    }

    createWheel() {
        if (this.availablePrizes.length === 0) {
            this.showError('No prizes available today. Please try again tomorrow!');
            return;
        }

        console.log('🎡 Creating wheel with', this.availablePrizes.length, 'prizes');

        // Clear existing segments
        this.wheelInner.innerHTML = '';
        
        // Calculate equal segment angle for all prizes
        this.segmentAngle = 360 / this.availablePrizes.length;
        
        // Create segments with equal sizes
        this.segments = this.availablePrizes.map((prize, index) => ({
            ...prize,
            index,
            angle: this.segmentAngle,
            startAngle: index * this.segmentAngle,
            endAngle: (index + 1) * this.segmentAngle,
            color: this.getPrizeColor(prize.category, index),
            textColor: this.getTextColor(prize.category)
        }));

        // Debug: Log segment mapping
        console.log('🎡 Segment mapping:');
        this.segments.forEach((segment, index) => {
            console.log(`  ${index}: ${segment.name} (ID: ${segment.id}) - ${segment.startAngle.toFixed(1)}° to ${segment.endAngle.toFixed(1)}°`);
        });
        
        // Debug: Log available prizes by category
        const breakdown = this.availablePrizes.reduce((acc, prize) => {
            acc[prize.category] = (acc[prize.category] || 0) + 1;
            return acc;
        }, {});
        console.log('📊 Available prizes by category:', breakdown);

        // Create SVG wheel for precise segments
        this.createSVGWheel();

        console.log('✅ Wheel created with', this.segments.length, 'equal segments');
    }

    createSVGWheel() {
        const sizes = this.getMobileSizes();
        const wheelSize = sizes.wheelSize;
        const centerX = wheelSize / 2;
        const centerY = wheelSize / 2;
        const radius = wheelSize / 2 - 10;

        // Create SVG element
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', wheelSize);
        svg.setAttribute('height', wheelSize);
        svg.setAttribute('viewBox', `0 0 ${wheelSize} ${wheelSize}`);
        svg.style.width = '100%';
        svg.style.height = '100%';

        this.segments.forEach((segment, index) => {
            this.createSVGSegment(svg, segment, centerX, centerY, radius);
        });

        // Clear and add SVG to wheel
        this.wheelInner.innerHTML = '';
        this.wheelInner.appendChild(svg);
    }

    createSVGSegment(svg, segment, centerX, centerY, radius) {
        // Convert angles to radians, starting from top (12 o'clock)
        const startAngleRad = (segment.startAngle - 90) * (Math.PI / 180);
        const endAngleRad = (segment.endAngle - 90) * (Math.PI / 180);
        
        // Calculate arc endpoints
        const x1 = centerX + radius * Math.cos(startAngleRad);
        const y1 = centerY + radius * Math.sin(startAngleRad);
        const x2 = centerX + radius * Math.cos(endAngleRad);
        const y2 = centerY + radius * Math.sin(endAngleRad);
        
        // Determine if we need a large arc
        const largeArcFlag = segment.angle > 180 ? 1 : 0;
        
        // Create SVG path
        const pathData = [
            `M ${centerX} ${centerY}`,
            `L ${x1} ${y1}`,
            `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
            'Z'
        ].join(' ');
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', pathData);
        path.setAttribute('fill', segment.color);
        path.setAttribute('stroke', '#ffffff');
        path.setAttribute('stroke-width', '3');
        path.setAttribute('data-prize-id', segment.id);
        path.setAttribute('data-segment-index', segment.index);
        path.style.cursor = 'pointer';
        
        // Add hover effect
        path.addEventListener('mouseenter', () => {
            path.setAttribute('stroke-width', '4');
            path.setAttribute('stroke', '#ffff00');
        });
        
        path.addEventListener('mouseleave', () => {
            path.setAttribute('stroke-width', '3');
            path.setAttribute('stroke', '#ffffff');
        });
        
        svg.appendChild(path);
        
        // Add text label
        this.addSegmentText(svg, segment, centerX, centerY, radius);
    }

    addSegmentText(svg, segment, centerX, centerY, radius) {
        const midAngle = (segment.startAngle + segment.endAngle) / 2;
        
        // Create a group for this segment's text
        const textGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        
        // Calculate the angle in radians for positioning
        const angleRad = (midAngle - 90) * (Math.PI / 180);
        
        // Position emoji much further from center to avoid spin button
        const emojiRadius = radius * 0.45; // Moved much further out
        const emojiX = centerX + emojiRadius * Math.cos(angleRad);
        const emojiY = centerY + emojiRadius * Math.sin(angleRad);
        
        // Create emoji display (combo emojis for combo items, regular emojis for others)
        const comboEmoji = this.getComboEmojiDisplay(segment.name);
        const sizes = this.getMobileSizes();
        
        const displayElement = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        displayElement.setAttribute('x', emojiX);
        displayElement.setAttribute('y', emojiY);
        displayElement.setAttribute('text-anchor', 'middle');
        displayElement.setAttribute('dominant-baseline', 'middle');
        displayElement.setAttribute('font-size', sizes.fontSize.emoji);
        displayElement.setAttribute('fill', '#ffffff');
        displayElement.setAttribute('stroke', '#000000');
        displayElement.setAttribute('stroke-width', '0.3');
        
        if (comboEmoji) {
            displayElement.textContent = comboEmoji;
            console.log(`🎨 Using combo emoji for ${segment.name}: ${comboEmoji}`);
        } else {
            displayElement.textContent = segment.emoji || '🎁';
        }
        
        // Format text for two lines if needed
        const formattedText = this.formatPrizeNameForTwoLines(segment.name);
        const textLines = formattedText.split('\n');
        
        // Create text with proper vertical separation
        if (textLines.length === 1) {
            // Single line - position after emoji
            this.createTextLine(textGroup, textLines[0], segment.id, 0, centerX, centerY, radius, angleRad, sizes);
        } else {
            // Two lines - create them with clear vertical separation
            textLines.forEach((line, index) => {
                if (line.trim()) {
                    this.createTextLine(textGroup, line.trim(), segment.id, index, centerX, centerY, radius, angleRad, sizes);
                }
            });
        }
        
        // Add display element (icon or emoji) to group
        textGroup.appendChild(displayElement);
        
        // Add group to SVG
        svg.appendChild(textGroup);
    }

    createTextLine(textGroup, lineText, segmentId, lineIndex, centerX, centerY, radius, angleRad, sizes) {
        // Create unique path ID for this text line
        const linePathId = `textPath_${segmentId}_line${lineIndex}`;
        const linePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        
        // Calculate slice angle (360° / 23 = ~15.65°)
        const sliceAngleDeg = 360 / 23;
        const sliceAngleRad = sliceAngleDeg * (Math.PI / 180);
        
        // Position lines at different angles WITHIN the same slice to avoid stacking
        // First line slightly above center, second line slightly below center
        const angleOffset = (lineIndex - 0.5) * (sliceAngleRad * 0.3); // 30% of slice width offset
        const adjustedAngleRad = angleRad + angleOffset;
        
        // Use same radial distance for both lines to keep them aligned
        const startRadius = radius * 0.55; // Start after emoji
        const endRadius = radius * 0.85;   // End near edge
        
        const lineStartX = centerX + startRadius * Math.cos(adjustedAngleRad);
        const lineStartY = centerY + startRadius * Math.sin(adjustedAngleRad);
        const lineEndX = centerX + endRadius * Math.cos(adjustedAngleRad);
        const lineEndY = centerY + endRadius * Math.sin(adjustedAngleRad);
        
        // Create the path for this line
        linePath.setAttribute('id', linePathId);
        linePath.setAttribute('d', `M ${lineStartX} ${lineStartY} L ${lineEndX} ${lineEndY}`);
        linePath.setAttribute('stroke', 'none');
        linePath.setAttribute('fill', 'none');
        
        // Create text element for this line
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('font-size', sizes.fontSize.text);
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('fill', '#ffffff');
        text.setAttribute('stroke', '#000000');
        text.setAttribute('stroke-width', '0.2');
        
        const textPathElement = document.createElementNS('http://www.w3.org/2000/svg', 'textPath');
        textPathElement.setAttribute('href', `#${linePathId}`);
        textPathElement.setAttribute('startOffset', '0%');
        textPathElement.textContent = lineText;
        
        text.appendChild(textPathElement);
        
        // Add path and text to group
        textGroup.appendChild(linePath);
        textGroup.appendChild(text);
    }

    formatPrizeNameVertical(name) {
        // Format name for vertical display within segment
        const maxLineLength = 10;
        const words = name.split(' ');
        const lines = [];
        let currentLine = '';
        
        for (const word of words) {
            if ((currentLine + ' ' + word).length <= maxLineLength) {
                currentLine = currentLine ? currentLine + ' ' + word : word;
            } else {
                if (currentLine) {
                    lines.push(currentLine);
                    currentLine = word;
                } else {
                    // Word is too long, split it
                    lines.push(word.substring(0, maxLineLength));
                    currentLine = word.substring(maxLineLength);
                }
            }
        }
        
        if (currentLine) {
            lines.push(currentLine);
        }
        
        // Limit to 3 lines max to fit in segment
        return lines.slice(0, 3).join('\n');
    }

    formatPrizeNameForSegment(name) {
        // Optimized formatting for 23 segments - shorter text
        const words = name.split(' ');
        
        // For very long names, use abbreviations
        if (name.length > 20) {
            return this.abbreviatePrizeName(name);
        }
        
        if (words.length <= 2) {
            return words.join('\n');
        }
        
        // For 3+ words, try to create balanced lines
        if (words.length === 3) {
            return `${words[0]}\n${words[1]}\n${words[2]}`;
        }
        
        // For longer names, split into 2-3 lines
        const mid = Math.ceil(words.length / 2);
        const firstLine = words.slice(0, mid).join(' ');
        const secondLine = words.slice(mid).join(' ');
        
        return `${firstLine}\n${secondLine}`;
    }
    
    abbreviatePrizeName(name) {
        // Create smart abbreviations for long prize names
        const abbreviations = {
            'smartwatch + mini cooler': 'Watch +\nCooler',
            'defy buds + g speaker': 'Buds +\nSpeaker', 
            'power bank + neckband': 'PowerBank\n+ Neckband',
            'intex home theatre': 'Intex\nTheatre',
            'zebronics home theatre': 'Zebronics\nTheatre',
            'zebronics astra bt speaker': 'Zebronics\nBT Speaker',
            'smart tv 32 inches': 'Smart TV\n32"',
            'boult 60w soundbar': 'Boult\nSoundbar',
            'free pouch and screen guard': 'Pouch +\nGuard',
            'trimmer + skull candy earphones': 'Trimmer +\nEarphones',
            'powerbank + wired earphones': 'PowerBank\n+ Earphones'
        };
        
        const lowerName = name.toLowerCase();
        if (abbreviations[lowerName]) {
            return abbreviations[lowerName];
        }
        
        // Fallback: truncate and add ellipsis
        if (name.length > 15) {
            return name.substring(0, 12) + '...';
        }
        
        return name;
    }
    
    formatPrizeNameRadial(name) {
        // Format name for radial display (single line flowing outward)
        // Use smart abbreviations for long names
        if (name.length > 20) {
            return this.abbreviatePrizeNameRadial(name);
        }
        
        // For shorter names, just clean up spacing
        return name.replace(/\s+/g, ' ').trim();
    }
    
    abbreviatePrizeNameRadial(name) {
        // Create compact abbreviations for radial display
        const abbreviations = {
            'smartwatch + mini cooler': 'Watch + Cooler',
            'defy buds + g speaker': 'Buds + Speaker', 
            'power bank + neckband': 'PowerBank + Neckband',
            'intex home theatre': 'Intex Theatre',
            'zebronics home theatre': 'Zebronics Theatre',
            'zebronics astra bt speaker': 'Zebronics BT Speaker',
            'smart tv 32 inches': 'Smart TV 32"',
            'boult 60w soundbar': 'Boult Soundbar',
            'free pouch and screen guard': 'Pouch + Guard',
            'trimmer + skull candy earphones': 'Trimmer + Earphones',
            'powerbank + wired earphones': 'PowerBank + Earphones',
            'mi smart speaker': 'Mi Speaker',
            'budget smartphone': 'Budget Phone'
        };
        
        const lowerName = name.toLowerCase();
        if (abbreviations[lowerName]) {
            return abbreviations[lowerName];
        }
        
        // Fallback: smart truncation
        if (name.length > 18) {
            // Try to truncate at word boundary
            const words = name.split(' ');
            let result = words[0];
            for (let i = 1; i < words.length; i++) {
                if ((result + ' ' + words[i]).length <= 18) {
                    result += ' ' + words[i];
                } else {
                    break;
                }
            }
            return result;
        }
        
        return name;
    }
    
    formatPrizeNameForTwoLines(name) {
        // Format name for two-line radial display to prevent cropping
        const maxLineLength = 12; // Adjust based on available space
        
        // Use smart abbreviations first
        if (name.length > 20) {
            name = this.abbreviatePrizeNameRadial(name);
        }
        
        // If still too long, split into two lines
        if (name.length > maxLineLength) {
            const words = name.split(' ');
            
            if (words.length === 1) {
                // Single long word - split in middle
                const mid = Math.ceil(name.length / 2);
                return `${name.substring(0, mid)}\n${name.substring(mid)}`;
            } else if (words.length === 2) {
                // Two words - one per line
                return `${words[0]}\n${words[1]}`;
            } else {
                // Multiple words - balance the lines
                const mid = Math.ceil(words.length / 2);
                const firstLine = words.slice(0, mid).join(' ');
                const secondLine = words.slice(mid).join(' ');
                
                // Ensure neither line is too long
                if (firstLine.length > maxLineLength || secondLine.length > maxLineLength) {
                    // Fallback: just use first word + "..."
                    return `${words[0]}\n${words[1] || '...'}`;
                }
                
                return `${firstLine}\n${secondLine}`;
            }
        }
        
        // Short enough for single line
        return name;
    }

    formatPrizeNameForSVG(name) {
        if (name.length > 12) {
            const words = name.split(' ');
            if (words.length > 1) {
                const midPoint = Math.ceil(words.length / 2);
                const firstLine = words.slice(0, midPoint).join(' ');
                const secondLine = words.slice(midPoint).join(' ');
                return `${firstLine}\n${secondLine}`;
            }
        }
        return name;
    }

    getPrizeColor(category, index) {
        const colors = {
            'ultra_rare': ['#FFD700', '#FF6B35', '#C41E3A', '#9B59B6', '#E74C3C', '#F39C12'],
            'rare': ['#FF6B6B', '#5F27CD', '#00D2D3', '#2ECC71', '#E67E22', '#3498DB'],
            'common': ['#4ECDC4', '#A8E6CF', '#FFD93D', '#95A5A6', '#1ABC9C', '#F1C40F']
        };
        
        const categoryColors = colors[category] || colors.common;
        return categoryColors[index % categoryColors.length];
    }

    getTextColor(category) {
        return category === 'ultra_rare' ? '#000000' : '#FFFFFF';
    }

    async spin() {
        if (this.isSpinning) {
            console.log('⚠️ Already spinning');
            return;
        }

        if (this.availablePrizes.length === 0) {
            this.showError('No prizes available today!');
            return;
        }

        console.log('🎯 Starting spin...');
        this.isSpinning = true;
        this.spinButton.disabled = true;
        this.spinButton.textContent = 'SPINNING...';
        
        // 🎵 Play spin sound at the start
        this.playSpinSound();
        
        // Prevent page shake during spin
        document.body.classList.add('spinning');

        try {
            console.log('🔍 === SIMPLIFIED SPIN FLOW ===');
            
            // === STEP 1: BACKEND DETERMINES AVAILABLE PRIZE ===
            console.log('📡 Step 1: Backend determining available prize...');
            const availablePrize = await this.getBackendSelectedPrize();
            
            // === STEP 2: FRONTEND CALCULATES WHEEL ROTATION ===
            console.log('🔄 Step 2: Calculating wheel rotation...');
            const rotationData = await this.calculateWheelRotation(availablePrize);
            
            // === STEP 3: ANIMATE WHEEL TO TARGET POSITION ===
            console.log('🎡 Step 3: Animating wheel to target position...');
            await this.animateWheelToPosition(rotationData.totalRotation);
            
            // === STEP 4: VERIFY ALIGNMENT ===
            console.log('✅ Step 4: Verifying wheel alignment...');
            const alignment = this.verifyWheelAlignment(availablePrize, rotationData.targetSegment);
            
            // === STEP 5: BACKEND CONFIRMS AND AWARDS PRIZE ===
            console.log('🏆 Step 5: Confirming prize award with backend...');
            const awardedPrize = await this.confirmPrizeWithBackend(availablePrize, rotationData);
            
            // === STEP 6: DISPLAY RESULT ===
            console.log('🎉 Step 6: Displaying result...');
            this.showCelebration(awardedPrize);
            
            console.log('✅ Spin completed successfully!');
            
        } catch (error) {
            console.error('❌ Spin failed:', error);
            this.showError(error.message || 'Spin failed. Please try again.');
        } finally {
            this.isSpinning = false;
            this.spinButton.disabled = false;
            this.spinButton.textContent = 'SPIN';
            
            // Stop all effects in case of error
            this.stopTickingSound();
            document.body.classList.remove('spinning');
        }
    }


    calculateExactRotation(targetSegmentIndex) {
        // Calculate the exact rotation needed to land on target segment
        const segmentAngle = 360 / this.segments.length;
        
        // Calculate the center of the target segment
        const targetSegmentCenter = targetSegmentIndex * segmentAngle + (segmentAngle / 2);
        
        // ORIGINAL WORKING LOGIC: To align the target segment with the pointer,
        // we need the wheel to be positioned so that the target segment center is at 0°.
        // This means we need to rotate the wheel by: -targetSegmentCenter
        // But since we want positive rotation, we use: 360° - targetSegmentCenter
        let targetFinalPosition = 360 - targetSegmentCenter;
        
        // Normalize to 0-360 range
        targetFinalPosition = targetFinalPosition % 360;
        if (targetFinalPosition < 0) targetFinalPosition += 360;
        
        // Get current wheel position (normalized to 0-360)
        const currentPosition = this.currentRotation % 360;
        
        // Calculate the minimum rotation needed to reach target
        let rotationNeeded = targetFinalPosition - currentPosition;
        
        // Ensure we always rotate in the positive direction and add exciting spins
        if (rotationNeeded <= 0) {
            rotationNeeded += 360; // Complete at least one full rotation
        }
        
        // Add exciting full rotations (8-12 additional spins for visual effect)
        // CRITICAL: Must be whole numbers to maintain precision
        const extraSpins = Math.floor(8 + Math.random() * 4);
        const totalRotationIncrement = rotationNeeded + (extraSpins * 360);
        
        // Calculate the final absolute rotation
        const finalAbsoluteRotation = this.currentRotation + totalRotationIncrement;
        
        console.log(`🎯 ROTATION CALCULATION (CORRECTED):`);
        console.log(`   Target segment: ${targetSegmentIndex}`);
        console.log(`   Segment center angle: ${targetSegmentCenter}°`);
        console.log(`   Target final position: ${targetFinalPosition}° (CORRECTED: segment center at pointer)`);
        console.log(`   Current position: ${currentPosition}° (absolute: ${this.currentRotation}°)`);
        console.log(`   Rotation needed: ${rotationNeeded}°`);
        console.log(`   Extra spins: ${extraSpins.toFixed(1)} (${(extraSpins * 360)}°)`);
        console.log(`   Total rotation increment: ${totalRotationIncrement}°`);
        console.log(`   Final absolute rotation: ${finalAbsoluteRotation}°`);
        
        // Verify our math
        const predictedFinalPosition = finalAbsoluteRotation % 360;
        console.log(`🔍 Predicted final position: ${predictedFinalPosition}° (should be ~${targetFinalPosition}°)`);
        
        // Double-check: which segment will be at pointer?
        const predictedSegment = Math.floor(predictedFinalPosition / segmentAngle) % this.segments.length;
        console.log(`🔍 Predicted segment at pointer: ${predictedSegment} (should be ${targetSegmentIndex})`);
        
        return finalAbsoluteRotation;
    }

    async animateWheelToPosition(targetRotation) {
        return new Promise((resolve) => {
            console.log(`🎡 Starting wheel animation to ${targetRotation}°`);
            
            // Start ticking sound
            this.startTickingSound();
            
            // Reset any existing transition
            this.wheelInner.style.transition = 'none';
            this.wheelInner.style.transform = `rotate(${this.currentRotation}deg)`;
            
            // Force reflow
            this.wheelInner.offsetHeight;
            
            // Apply exciting rotation animation with longer duration
            this.wheelInner.style.transition = 'transform 6s cubic-bezier(0.23, 1, 0.32, 1)';
            this.wheelInner.style.transform = `rotate(${targetRotation}deg)`;
            
            // Update current rotation for next spin
            this.currentRotation = targetRotation;
            
            console.log(`🎡 Wheel rotating to ${targetRotation}° (final position: ${this.currentRotation}°)`);
            
            // Stop ticking sound after animation
            setTimeout(() => {
                this.stopTickingSound();
                console.log('🎡 Wheel animation completed');
                resolve();
            }, 6000);
        });
    }

    // === PHASE 2: CALCULATE EXACT ROTATION ANGLE ===
    calculatePreciseRotation(serverDecision) {
        console.log(`🎯 Calculating precise rotation for sector ${serverDecision.sector_index}...`);
        
        const targetSectorIndex = serverDecision.sector_index;
        const sectorCenter = serverDecision.sector_center;
        
        // Verify the prize exists on our wheel
        const wheelPrize = this.segments[targetSectorIndex];
        if (!wheelPrize || wheelPrize.id !== serverDecision.prize.id) {
            throw new Error(`Mapping error: Server prize ${serverDecision.prize.id} doesn't match wheel segment ${targetSectorIndex}`);
        }
        
        console.log(`✅ Verified mapping: Sector ${targetSectorIndex} = ${wheelPrize.name}`);
        
        // CORRECT LOGIC: Let's think step by step
        // 
        // GOAL: Bring sector center from its current position to the pointer (0°)
        // 
        // EXAMPLE: Sector center is at 211.30°, we want it at 0°
        // 
        // METHOD 1 - Think about wheel rotation:
        // - Currently: sector is at 211.30° position on the wheel
        // - We want: sector to be at 0° position (pointer)
        // - So we need to rotate the wheel by: -211.30° (counterclockwise)
        // - In CSS terms (clockwise positive): 360° - 211.30° = 148.70°
        // 
        // METHOD 2 - Think about final wheel position:
        // - After rotation, we want the sector center to align with pointer
        // - The wheel's final rotation should be such that: 
        //   (sectorCenter + wheelRotation) % 360 = 0
        // - So: wheelRotation = -sectorCenter = 360° - sectorCenter
        
        const rotationNeededFromZero = (360 - sectorCenter) % 360;
        
        console.log(`🔧 CORRECT LOGIC DEBUG:`);
        console.log(`   Sector center: ${sectorCenter}°`);
        console.log(`   To bring to pointer: rotate wheel by ${rotationNeededFromZero}°`);
        console.log(`   Verification: (${sectorCenter}° + ${rotationNeededFromZero}°) % 360 = ${(sectorCenter + rotationNeededFromZero) % 360}° (should be 0°)`);
        
        
        // Add exciting multiple rotations (8-12 spins) - MUST be integer to avoid floating point errors
        const totalSpins = Math.floor(8 + Math.random() * 4);
        
        // NOW: Calculate how much to rotate from current position
        // 
        // Current wheel is at: this.currentRotation
        // We want wheel to end up at: rotationNeededFromZero (absolute position)
        // 
        // But we need to account for the current position:
        // If wheel is currently at 50° and we want it at 100°, we rotate by 50°
        // If wheel is currently at 200° and we want it at 50°, we rotate by 210° (going forward)
        
        const currentNormalized = this.currentRotation % 360;
        let rotationIncrement = rotationNeededFromZero - currentNormalized;
        
        // Always rotate in positive direction (clockwise)
        if (rotationIncrement < 0) {
            rotationIncrement += 360;
        }
        
        // CRITICAL FIX: The final rotation should be calculated correctly
        // We want the wheel to end up at rotationNeededFromZero position
        // So: finalRotation = currentRotation + extraSpins + incrementNeeded
        // Where incrementNeeded = targetPosition - currentNormalized
        
        const finalRotation = this.currentRotation + (totalSpins * 360) + rotationIncrement;
        
        // VERIFICATION: Check that our math is correct
        const expectedFinalPosition = finalRotation % 360;
        const shouldBe = rotationNeededFromZero;
        
        console.log(`🔧 MATH VERIFICATION:`);
        console.log(`   Final rotation: ${finalRotation}°`);
        console.log(`   Expected final position: ${expectedFinalPosition}°`);
        console.log(`   Should be: ${shouldBe}°`);
        console.log(`   Math correct: ${Math.abs(expectedFinalPosition - shouldBe) < 0.01 ? '✅' : '❌'}`);
        
        console.log(`🔧 FINAL CALCULATION:`);
        console.log(`   Current wheel position: ${this.currentRotation}° (normalized: ${currentNormalized}°)`);
        console.log(`   Target wheel position: ${rotationNeededFromZero}°`);
        console.log(`   Rotation increment needed: ${rotationIncrement}°`);
        console.log(`   With ${totalSpins.toFixed(1)} extra spins: ${finalRotation}°`);
        console.log(`   Final position will be: ${finalRotation % 360}° (should be ${rotationNeededFromZero}°)`);
        
        
        return {
            targetSectorIndex: targetSectorIndex,
            sectorCenter: sectorCenter,
            finalRotation: finalRotation,
            totalSpins: totalSpins,
            serverPrize: serverDecision.prize
        };
    }

    // === PHASE 3: EXECUTE SPIN ANIMATION ===
    async executeSpinAnimation(rotationData) {
        console.log(`🎡 Executing spin animation to ${rotationData.finalRotation}°...`);
        
        return new Promise((resolve) => {
            // Start ticking sound
            this.startTickingSound();
            
            // Reset any existing transition
            this.wheelInner.style.transition = 'none';
            this.wheelInner.style.transform = `rotate(${this.currentRotation}deg)`;
            
            // Force reflow
            this.wheelInner.offsetHeight;
            
            // Execute the calculated spin animation
            this.wheelInner.style.transition = 'transform 6s cubic-bezier(0.23, 1, 0.32, 1)';
            this.wheelInner.style.transform = `rotate(${rotationData.finalRotation}deg)`;
            
            // CRITICAL FIX: Get the ACTUAL CSS rotation after animation completes
            // This prevents cumulative errors from multiple spins
            const targetNormalizedPosition = rotationData.finalRotation % 360;
            this.currentRotation = targetNormalizedPosition; // Initial estimate
            
            console.log(`🎡 Wheel spinning to exact position: ${rotationData.finalRotation}°`);
            console.log(`🎯 Expected final position: ${this.currentRotation}°`);
            
            // Wait for animation completion
            setTimeout(() => {
                this.stopTickingSound();
                
                // CRITICAL: Read the actual CSS rotation to prevent cumulative errors
                const actualCSSRotation = this.getActualCSSRotation();
                if (actualCSSRotation !== null) {
                    const difference = Math.abs(actualCSSRotation - this.currentRotation);
                    console.log(`🔄 CSS SYNC: Expected ${this.currentRotation}°, Actual ${actualCSSRotation}°, Diff: ${difference}°`);
                    
                    if (difference > 1) { // If difference is significant
                        console.log(`⚠️ CORRECTING: Updating tracked rotation to match CSS`);
                        this.currentRotation = actualCSSRotation;
                    }
                }
                
                console.log('🎡 Spin animation completed');
                resolve();
            }, 6000);
        });
    }

    // === PHASE 4: VERIFY PRECISE LANDING ===
    verifyPreciseLanding(serverDecision, rotationData) {
        console.log('✅ Verifying precise landing...');
        
        const finalRotation = this.currentRotation;
        const segmentAngle = 360 / this.segments.length;
        
        // Calculate which sector is at the pointer
        const wheelPosition = finalRotation % 360;
        
        // CRITICAL FIX: The sector detection logic is wrong
        // If wheel is at 36.82°, which sector is at the pointer (0°)?
        // 
        // The wheel rotated 36.82° clockwise, so the sector that was originally at 
        // (360° - 36.82°) = 323.18° is now at the pointer
        // 
        // But we need to think differently:
        // If the wheel rotated 36.82° clockwise, then a sector that is now at the pointer (0°)
        // was originally at position (360° - 36.82°) = 323.18°
        // 
        // But sectors are positioned starting from 0°, so:
        // Sector 0 center: 7.83°
        // Sector 1 center: 23.48°
        // etc.
        // 
        // We need to find which sector center is closest to the current pointer position
        // after the rotation
        
        // After rotation, which sector center is now at the pointer (0°)?
        // We need to reverse the rotation to see which sector is there
        const originalPointerPosition = (360 - wheelPosition) % 360;
        const actualSector = Math.floor(originalPointerPosition / segmentAngle);
        const boundaryAdjusted = actualSector >= this.segments.length ? 0 : actualSector;
        
        console.log(`🔧 SECTOR DETECTION FIX:`);
        console.log(`   Wheel position: ${wheelPosition}°`);
        console.log(`   Original pointer position: ${originalPointerPosition}°`);
        console.log(`   Segment angle: ${segmentAngle}°`);
        console.log(`   Calculated sector: ${actualSector}`);
        console.log(`   Boundary adjusted: ${boundaryAdjusted}`);
        console.log(`   Browser: ${navigator.userAgent.includes('Chrome') ? 'Chrome' : navigator.userAgent.includes('Safari') ? 'Safari' : 'Other'}`);
        
        // Let's also check what the CSS transform actually shows
        const computedTransform = window.getComputedStyle(this.wheelInner).transform;
        console.log(`   CSS transform: ${computedTransform}`);
        
        // Try to extract the actual rotation from the transform matrix
        if (computedTransform && computedTransform !== 'none') {
            const matrix = computedTransform.match(/matrix\(([^)]+)\)/);
            if (matrix) {
                const values = matrix[1].split(',').map(parseFloat);
                const actualCSSRotation = Math.atan2(values[1], values[0]) * (180 / Math.PI);
                console.log(`   Actual CSS rotation: ${actualCSSRotation}°`);
                console.log(`   Expected CSS rotation: ${finalRotation % 360}°`);
                console.log(`   CSS rotation difference: ${Math.abs(actualCSSRotation - (finalRotation % 360))}°`);
            }
        }
        
        const landedPrize = this.segments[boundaryAdjusted];
        const expectedSector = serverDecision.sector_index;
        
        console.log(`🎯 Precision Landing Check:`);
        console.log(`   Server selected: Sector ${expectedSector} (${serverDecision.prize.name})`);
        console.log(`   Wheel landed on: Sector ${boundaryAdjusted} (${landedPrize ? landedPrize.name : 'Unknown'})`);
        console.log(`   Final rotation: ${finalRotation}°`);
        console.log(`   Calculated rotation: ${rotationData.finalRotation}°`);
        
        const isPerfect = boundaryAdjusted === expectedSector;
        const prizeMatches = landedPrize && landedPrize.id === serverDecision.prize.id;
        
        console.log(`   Sector match: ${isPerfect ? '✅ PERFECT' : '❌ MISMATCH'}`);
        console.log(`   Prize match: ${prizeMatches ? '✅ PERFECT' : '❌ MISMATCH'}`);
        
        return {
            isPerfect: isPerfect && prizeMatches,
            expectedSector: expectedSector,
            actualSector: boundaryAdjusted,
            landedPrize: landedPrize,
            rotationAccuracy: Math.abs(finalRotation - (rotationData.finalRotation % 360))
        };
    }

    // === UTILITY: GENERATE IDEMPOTENCY KEY ===
    generateIdempotencyKey() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2, 15);
        const userId = this.getUserId();
        return `spin_${userId}_${timestamp}_${random}`;
    }

    // === PHASE 1: CLIENT STARTS RESPONSIVE SPIN ANIMATION ===
    startResponsiveSpinAnimation() {
        console.log('🎡 Starting responsive wheel animation...');
        
        // Start ticking sound
        this.startTickingSound();
        
        // Reset any existing transition
        this.wheelInner.style.transition = 'none';
        this.wheelInner.style.transform = `rotate(${this.currentRotation}deg)`;
        
        // Force reflow
        this.wheelInner.offsetHeight;
        
        // Start continuous spinning while waiting for server
        const continuousSpins = 4; // Keep spinning for 4 rotations
        const continuousRotation = this.currentRotation + (continuousSpins * 360);
        
        this.wheelInner.style.transition = 'transform 3s linear';
        this.wheelInner.style.transform = `rotate(${continuousRotation}deg)`;
        
        console.log(`🎡 Wheel spinning continuously: ${this.currentRotation}° → ${continuousRotation}°`);
        
        return {
            startTime: Date.now(),
            continuousRotation: continuousRotation,
            isResponsive: true
        };
    }

    // === PHASE 2: SERVER DECIDES PRIZE AND RESERVES IT ===
    async requestServerPrizeDecision(idempotencyKey) {
        console.log('📡 Requesting server prize decision with reservation...');
        
        const response = await fetch(`${this.apiBaseUrl}/spin/reserve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Idempotency-Key': idempotencyKey
            },
            body: JSON.stringify({
                user_id: this.getUserId(),
                session_id: this.getSessionId(),
                client_timestamp: Date.now()
            })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Server prize decision failed');
        }

        // Verify signed response
        if (!this.verifyServerSignature(data)) {
            throw new Error('Invalid server signature - response may be tampered');
        }

        console.log('✅ Server decision received and verified:');
        console.log(`   Prize: ${data.prize.name} (ID: ${data.prize.id})`);
        console.log(`   Sector: ${data.sector_index} (angle: ${data.sector_center}°)`);
        console.log(`   Reservation: ${data.reservation_id} (TTL: ${data.reservation_ttl}s)`);
        console.log(`   Signature: ${data.signature.substring(0, 16)}...`);

        return data;
    }

    // === PHASE 3: CLIENT ANIMATES TO SERVER-SELECTED SECTOR ===
    async animateToServerSector(serverDecision, spinAnimation) {
        console.log(`🎯 Animating to server-selected sector ${serverDecision.sector_index}...`);
        
        // Wait for continuous spin to build up
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Calculate exact landing position from server data
        const targetAngle = serverDecision.sector_center || (serverDecision.sector_index * (360 / this.segments.length) + (360 / this.segments.length / 2));
        const finalPosition = 360 - targetAngle;
        
        // Add exciting spins (8-12 total)
        const totalSpins = 8 + Math.random() * 4;
        const finalRotation = (totalSpins * 360) + (finalPosition % 360);
        
        console.log(`📐 Server sector center: ${targetAngle}°`);
        console.log(`🎡 Final rotation: ${finalRotation}° (${totalSpins.toFixed(1)} spins)`);
        
        // Smooth deceleration to exact server position
        this.wheelInner.style.transition = 'transform 4s cubic-bezier(0.23, 1, 0.32, 1)';
        this.wheelInner.style.transform = `rotate(${finalRotation}deg)`;
        
        // Update current rotation
        this.currentRotation = finalRotation % 360;
        
        // Wait for animation completion
        return new Promise(resolve => {
            setTimeout(() => {
                this.stopTickingSound();
                console.log('🎡 Wheel landed on server-selected sector');
                resolve();
            }, 4000);
        });
    }

    // === PHASE 4: DISPLAY SERVER MESSAGE ===
    displayServerAuthorizedResult(serverDecision) {
        console.log('🎉 Displaying server-authorized result...');
        
        // Verify the wheel actually landed on the correct sector
        const actualSector = this.getCurrentSector();
        const expectedSector = serverDecision.sector_index;
        
        console.log(`🎯 Landing verification:`);
        console.log(`   Expected sector: ${expectedSector}`);
        console.log(`   Actual sector: ${actualSector}`);
        console.log(`   Match: ${actualSector === expectedSector ? '✅ PERFECT' : '❌ MISMATCH'}`);
        
        // === DEBUG: LOG EXACTLY WHAT WILL BE DISPLAYED ===
        const prizeToDisplay = {
            ...serverDecision.prize,
            serverMessage: serverDecision.message,
            reservationId: serverDecision.reservation_id,
            isServerAuthorized: true
        };
        
        console.log('🔍 DEBUG: Prize being sent to popup');
        console.log(`   Prize ID: ${prizeToDisplay.id}`);
        console.log(`   Prize name: ${prizeToDisplay.name}`);
        console.log(`   Prize emoji: ${prizeToDisplay.emoji}`);
        console.log(`   Prize category: ${prizeToDisplay.category}`);
        console.log(`   Server message: ${prizeToDisplay.serverMessage}`);
        console.log(`   Is server authorized: ${prizeToDisplay.isServerAuthorized}`);
        
        // Display the server-authorized prize (regardless of visual landing)
        this.showCelebration(prizeToDisplay);
    }

    // === PHASE 5: CLIENT CONFIRMS RECEIPT, SERVER FINALIZES ===
    async confirmReceiptAndFinalize(serverDecision, idempotencyKey) {
        console.log('✅ Confirming receipt and requesting finalization...');
        
        const response = await fetch(`${this.apiBaseUrl}/spin/finalize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Idempotency-Key': idempotencyKey
            },
            body: JSON.stringify({
                user_id: this.getUserId(),
                reservation_id: serverDecision.reservation_id,
                client_confirmation: {
                    received_at: Date.now(),
                    prize_id: serverDecision.prize.id,
                    sector_index: serverDecision.sector_index
                },
                signature_verification: 'confirmed'
            })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Prize finalization failed');
        }

        console.log('🏆 Prize finalized by server:');
        console.log(`   Award ID: ${data.award_id}`);
        console.log(`   Status: ${data.status}`);
        console.log(`   Inventory updated: ${data.inventory_updated}`);
        
        return data;
    }

    // === UTILITY: VERIFY SERVER SIGNATURE ===
    verifyServerSignature(serverResponse) {
        // In production, implement proper HMAC/JWT verification
        // For now, just check that signature exists and has reasonable format
        const signature = serverResponse.signature;
        if (!signature || signature.length < 32) {
            console.warn('⚠️ Server signature missing or too short');
            return false;
        }
        
        // TODO: Implement actual cryptographic verification
        // const expectedSignature = hmac_sha256(serverResponse.payload, SECRET_KEY);
        // return signature === expectedSignature;
        
        console.log('✅ Server signature verified (mock implementation)');
        return true;
    }

    // === UTILITY: GET CURRENT SECTOR ===
    getCurrentSector() {
        const currentRotation = this.currentRotation % 360;
        const segmentAngle = 360 / this.segments.length;
        const sectorAtPointer = (360 - currentRotation) % 360;
        return Math.floor(sectorAtPointer / segmentAngle);
    }

    // === UTILITY: GET SESSION ID ===
    getSessionId() {
        if (!this.sessionId) {
            this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
        }
        return this.sessionId;
    }

    // === UTILITY: GET ACTUAL CSS ROTATION ===
    getActualCSSRotation() {
        try {
            const computedTransform = window.getComputedStyle(this.wheelInner).transform;
            if (computedTransform && computedTransform !== 'none') {
                const matrix = computedTransform.match(/matrix\(([^)]+)\)/);
                if (matrix) {
                    const values = matrix[1].split(',').map(parseFloat);
                    const actualRotation = Math.atan2(values[1], values[0]) * (180 / Math.PI);
                    // Normalize to 0-360 range
                    return ((actualRotation % 360) + 360) % 360;
                }
            }
            return null;
        } catch (error) {
            console.warn('Could not read CSS rotation:', error);
            return null;
        }
    }

    // === STEP 1: START WHEEL SPINNING IMMEDIATELY ===
    startWheelSpinning() {
        console.log('🎡 Starting immediate wheel rotation...');
        
        // Start ticking sound
        this.startTickingSound();
        
        // Start with a continuous spinning animation (no end point yet)
        this.wheelInner.style.transition = 'none';
        this.wheelInner.style.transform = `rotate(${this.currentRotation}deg)`;
        
        // Force reflow
        this.wheelInner.offsetHeight;
        
        // Start continuous spinning - we'll adjust the endpoint later
        const initialSpins = 3; // Start with 3 full rotations
        const initialRotation = this.currentRotation + (initialSpins * 360);
        
        this.wheelInner.style.transition = 'transform 2s linear';
        this.wheelInner.style.transform = `rotate(${initialRotation}deg)`;
        
        console.log(`🎡 Wheel spinning continuously from ${this.currentRotation}° to ${initialRotation}°`);
        
        return {
            startTime: Date.now(),
            initialRotation: initialRotation
        };
    }

    // === STEP 3: FIND WHERE WINNING PRIZE IS LOCATED ON WHEEL ===
    findPrizeLocationOnWheel(winningPrize) {
        console.log(`🎯 Finding location of ${winningPrize.name} (ID: ${winningPrize.id}) on wheel...`);
        
        // Find which segment contains this prize
        const targetSegmentIndex = this.segments.findIndex(segment => segment.id === winningPrize.id);
        
        if (targetSegmentIndex === -1) {
            throw new Error(`Prize ${winningPrize.name} (ID: ${winningPrize.id}) not found on wheel!`);
        }
        
        const segmentAngle = 360 / this.segments.length;
        const segmentCenterAngle = targetSegmentIndex * segmentAngle + (segmentAngle / 2);
        
        console.log(`✅ Found prize at segment ${targetSegmentIndex}, center angle: ${segmentCenterAngle}°`);
        
        return {
            segmentIndex: targetSegmentIndex,
            centerAngle: segmentCenterAngle,
            prize: winningPrize
        };
    }

    // === STEP 4: ADJUST WHEEL TO LAND ON WINNING ITEM ===
    async adjustWheelToLandOnPrize(targetLocation, spinPromise) {
        console.log(`🔄 Adjusting wheel to land on ${targetLocation.prize.name}...`);
        
        // Wait a moment for the initial spin to get going
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Calculate the exact final position needed
        const targetFinalRotation = 360 - targetLocation.centerAngle;
        const normalizedTarget = targetFinalRotation % 360;
        
        // Add many more spins for excitement (total 8-12 spins)
        const totalSpins = 8 + Math.random() * 4;
        const finalRotation = (totalSpins * 360) + normalizedTarget;
        
        console.log(`🎯 Target segment: ${targetLocation.segmentIndex}`);
        console.log(`📐 Segment center: ${targetLocation.centerAngle}°`);
        console.log(`🎡 Final rotation: ${finalRotation}° (${totalSpins.toFixed(1)} total spins)`);
        
        // Smoothly transition to the exact landing position
        this.wheelInner.style.transition = 'transform 4s cubic-bezier(0.23, 1, 0.32, 1)';
        this.wheelInner.style.transform = `rotate(${finalRotation}deg)`;
        
        // Update current rotation for next spin
        this.currentRotation = finalRotation % 360;
        
        // Wait for the wheel to finish spinning
        return new Promise(resolve => {
            setTimeout(() => {
                this.stopTickingSound();
                console.log('🎡 Wheel finished spinning');
                resolve();
            }, 4000);
        });
    }

    // === STEP 5: VERIFY PERFECT LANDING ===
    verifyFinalLanding(expectedPrize, targetLocation) {
        console.log('✅ Verifying final landing position...');
        
        const finalRotation = this.currentRotation;
        const segmentAngle = 360 / this.segments.length;
        
        // Calculate which segment is at the pointer
        const wheelPosition = finalRotation % 360;
        const segmentAtPointer = (360 - wheelPosition) % 360;
        const actualSegment = Math.floor(segmentAtPointer / segmentAngle);
        const boundaryAdjusted = actualSegment >= this.segments.length ? 0 : actualSegment;
        
        const landedPrize = this.segments[boundaryAdjusted];
        
        console.log(`🎯 Landing Verification:`);
        console.log(`   Expected: Segment ${targetLocation.segmentIndex} (${expectedPrize.name})`);
        console.log(`   Actual: Segment ${boundaryAdjusted} (${landedPrize ? landedPrize.name : 'Unknown'})`);
        console.log(`   Final rotation: ${finalRotation}°`);
        
        const isPerfect = boundaryAdjusted === targetLocation.segmentIndex;
        console.log(`   Result: ${isPerfect ? '✅ PERFECT LANDING' : '❌ MISSED TARGET'}`);
        
        return {
            isPerfect: isPerfect,
            expectedSegment: targetLocation.segmentIndex,
            actualSegment: boundaryAdjusted,
            landedPrize: landedPrize
        };
    }

    // === STEP 1: BACKEND DETERMINES AVAILABLE PRIZE ===
    async getBackendSelectedPrize() {
        console.log('📡 Requesting available prize from backend...');
        
        const response = await fetch(`${this.apiBaseUrl}/pre-spin`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: this.getUserId()
            })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Backend prize selection failed');
        }

        const prize = data.selected_prize;
        const targetSegment = data.target_segment_index;
        
        console.log(`✅ Backend selected: ${prize.name} (ID: ${prize.id}) → Segment ${targetSegment}`);
        
        return {
            prize: prize,
            targetSegment: targetSegment,
            totalSegments: data.total_segments
        };
    }

    // === STEP 2: FRONTEND CALCULATES WHEEL ROTATION ===
    async calculateWheelRotation(availablePrize) {
        console.log('🔄 Calculating precise wheel rotation...');
        
        const targetSegment = availablePrize.targetSegment;
        const prize = availablePrize.prize;
        
        // Verify mapping between backend selection and wheel display
        const wheelPrizeAtSegment = this.segments[targetSegment];
        if (!wheelPrizeAtSegment || wheelPrizeAtSegment.id !== prize.id) {
            throw new Error(`Mapping error: Backend prize ${prize.id} doesn't match wheel segment ${targetSegment}`);
        }
        
        console.log(`✅ Mapping verified: Segment ${targetSegment} = ${wheelPrizeAtSegment.name}`);
        
        // Calculate exact rotation needed
        const totalRotation = this.calculateExactRotation(targetSegment);
        
        return {
            targetSegment: targetSegment,
            totalRotation: totalRotation,
            prize: prize
        };
    }

    // === STEP 4: VERIFY ALIGNMENT ===
    verifyWheelAlignment(availablePrize, targetSegment) {
        console.log('✅ Verifying wheel landed correctly...');
        
        const finalRotation = this.currentRotation;
        const segmentAngle = 360 / this.segments.length;
        
        // Calculate which segment is at the pointer (top of wheel)
        // The pointer is at 0° (top). We need to find which segment is currently at 0°
        // Since the wheel rotates clockwise, we need to account for the rotation
        const wheelPosition = finalRotation % 360;
        
        // ORIGINAL WORKING LOGIC: Calculate which segment is at the pointer
        const segmentAtPointer = (360 - wheelPosition) % 360;
        const actualLandedSegment = Math.floor(segmentAtPointer / segmentAngle);
        const boundaryAdjustedSegment = actualLandedSegment >= this.segments.length ? 0 : actualLandedSegment;
        
        const landedPrize = this.segments[boundaryAdjustedSegment];
        
        console.log(`🎯 Alignment Check:`);
        console.log(`   Expected: Segment ${targetSegment} (${availablePrize.prize.name})`);
        console.log(`   Actual: Segment ${boundaryAdjustedSegment} (${landedPrize ? landedPrize.name : 'Unknown'})`);
        console.log(`   Final rotation: ${finalRotation}°`);
        console.log(`   Wheel position: ${wheelPosition}°`);
        console.log(`   Segment angle: ${segmentAngle}°`);
        console.log(`   Segment at pointer: ${segmentAtPointer}°`);
        
        const isAligned = boundaryAdjustedSegment === targetSegment;
        console.log(`   Alignment: ${isAligned ? '✅ PERFECT' : '❌ MISALIGNED'}`);
        
        return {
            isAligned: isAligned,
            expectedSegment: targetSegment,
            actualSegment: boundaryAdjustedSegment,
            landedPrize: landedPrize
        };
    }

    // === STEP 5: BACKEND CONFIRMS AND AWARDS PRIZE ===
    async confirmPrizeWithBackend(availablePrize, rotationData) {
        console.log('🏆 Confirming prize award with backend...');
        
        const response = await fetch(`${this.apiBaseUrl}/spin`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: this.getUserId(),
                selected_prize_id: availablePrize.prize.id,
                target_segment_index: rotationData.targetSegment,
                final_rotation: rotationData.totalRotation
            })
        });

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Prize confirmation failed');
        }

        const awardedPrize = data.prize;
        console.log(`✅ Prize confirmed and awarded: ${awardedPrize.name}`);
        
        // Add prize to daily log
        this.addPrizeToLog(awardedPrize);
        
        // Verify backend didn't change the prize
        if (awardedPrize.id !== availablePrize.prize.id) {
            console.warn('⚠️ Backend changed the prize!');
            console.warn(`   Originally selected: ${availablePrize.prize.name}`);
            console.warn(`   Actually awarded: ${awardedPrize.name}`);
        }
        
        return awardedPrize;
    }

    showCelebration(prize) {
        console.log('🎉 Showing prize modal for:', prize.name);
        
        // 🎉 ENHANCED CELEBRATION SEQUENCE
        this.startCelebrationSequence(prize);
        
        // === DEBUG: LOG POPUP DISPLAY DETAILS ===
        console.log('🔍 DEBUG: Popup display details');
        console.log(`   Received prize object:`, prize);
        console.log(`   Prize ID: ${prize.id}`);
        console.log(`   Prize name: ${prize.name}`);
        console.log(`   Prize emoji: ${prize.emoji}`);
        console.log(`   Prize category: ${prize.category}`);

        const prizeEmoji = document.getElementById('prizeEmoji');
        const prizeName = document.getElementById('prizeName');
        const prizeCategory = document.getElementById('prizeCategory');
        const prizeDisplay = document.getElementById('prizeDisplay');

        console.log('🔍 DEBUG: Setting DOM elements');
        console.log(`   Setting emoji to: ${prize.emoji || '🎁'}`);
        console.log(`   Setting name to: ${prize.name}`);

        if (prizeEmoji) {
            // Check if this is a combo item first
            const comboEmoji = this.getComboEmojiDisplay(prize.name);
            const sizes = this.getMobileSizes();
            
            prizeEmoji.innerHTML = '';
            
            if (comboEmoji) {
                // Use combo emoji display for combo items
                prizeEmoji.textContent = comboEmoji;
                prizeEmoji.style.fontSize = sizes.fontSize.modal;
                console.log(`🎨 Using combo emoji in modal for ${prize.name}: ${comboEmoji}`);
            } else {
                // Use regular emoji
                prizeEmoji.textContent = prize.emoji || '🎁';
                prizeEmoji.style.fontSize = sizes.fontSize.modal;
            }
        }
        if (prizeName) prizeName.textContent = prize.name;
        
        if (prizeCategory) {
            prizeCategory.textContent = prize.category_display || prize.category.replace('_', ' ').toUpperCase();
            prizeCategory.className = `prize-category ${prize.category}`;
        }

        if (prizeDisplay) {
            prizeDisplay.innerHTML = '';
            const description = document.createElement('p');
            description.textContent = prize.description || `Congratulations on winning ${prize.name}!`;
            description.style.fontSize = '1.1rem';
            description.style.color = 'var(--text-secondary)';
            prizeDisplay.appendChild(description);
        }

        this.modalOverlay.classList.add('show');
    }
    
    // 🎉 ENHANCED CELEBRATION SYSTEM
    startCelebrationSequence(prize) {
        console.log('🎉 Starting celebration sequence for:', prize.name, 'Category:', prize.category);
        
        // Stop any ongoing sounds first
        this.stopTickingSound();
        
        // 1. Play celebration sound with proper timing (1-2 seconds)
        setTimeout(() => {
            this.playCelebrationSound(prize.category);
        }, 300); // Small delay after wheel stops
        
        // 2. Start confetti animation
        setTimeout(() => {
            this.showConfetti(prize.category);
        }, 500);
        
        // 3. Add celebration effects to modal
        setTimeout(() => {
            this.addModalCelebrationEffects(prize.category);
        }, 200);
    }
    
    playCelebrationSound(category) {
        if (!this.soundEnabled) {
            console.log('🔇 Sound disabled, skipping celebration sound');
            return;
        }
        
        try {
            let soundToPlay;
            let duration = 4000; // 4 seconds default
            
            // Choose sound and duration based on prize category
            if (category === 'rare' || category === 'ultra_rare') {
                soundToPlay = this.audioElements.rareWinSound;
                duration = 5000; // 5 seconds for rare prizes - more celebration!
                console.log('🎵 Playing RARE celebration sound for', category);
            } else {
                soundToPlay = this.audioElements.winSound;
                duration = 4000; // 4 seconds for common prizes
                console.log('🎵 Playing COMMON celebration sound for', category);
            }
            
            if (soundToPlay) {
                // Reset and play
                soundToPlay.currentTime = 0;
                soundToPlay.volume = 0.8; // Slightly louder for celebration
                
                const playPromise = soundToPlay.play();
                
                if (playPromise !== undefined) {
                    playPromise
                        .then(() => {
                            console.log('🎵 Celebration sound started successfully');
                            
                            // Stop sound after specified duration
                            setTimeout(() => {
                                if (!soundToPlay.paused) {
                                    soundToPlay.pause();
                                    soundToPlay.currentTime = 0;
                                    console.log('🔇 Celebration sound stopped after', duration + 'ms');
                                }
                            }, duration);
                        })
                        .catch(error => {
                            console.warn('⚠️ Failed to play celebration sound:', error);
                            // Fallback: try to enable audio context
                            if (this.audioContext && this.audioContext.state === 'suspended') {
                                this.audioContext.resume().then(() => {
                                    console.log('🔊 Audio context resumed, retrying sound...');
                                    soundToPlay.play().catch(e => console.warn('⚠️ Retry failed:', e));
                                });
                            }
                        });
                }
            } else {
                console.warn('⚠️ No sound element available for category:', category);
            }
        } catch (error) {
            console.warn('⚠️ Error playing celebration sound:', error);
        }
    }
    
    showConfetti(category) {
        console.log('🎊 Starting confetti animation for:', category);
        
        // Create confetti container
        const confettiContainer = document.createElement('div');
        confettiContainer.className = 'confetti-container';
        confettiContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: 10000;
            overflow: hidden;
        `;
        
        document.body.appendChild(confettiContainer);
        
        // Determine confetti intensity based on category
        const confettiCount = category === 'rare' || category === 'ultra_rare' ? 50 : 30;
        const colors = category === 'rare' || category === 'ultra_rare' 
            ? ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
            : ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'];
        
        // Create confetti pieces
        for (let i = 0; i < confettiCount; i++) {
            setTimeout(() => {
                this.createConfettiPiece(confettiContainer, colors);
            }, i * 50); // Stagger creation
        }
        
        // Remove confetti container after animation (match celebration duration)
        const confettiDuration = category === 'rare' || category === 'ultra_rare' ? 6000 : 5000;
        setTimeout(() => {
            if (confettiContainer.parentNode) {
                confettiContainer.parentNode.removeChild(confettiContainer);
                console.log('🧹 Confetti cleaned up');
            }
        }, confettiDuration);
    }
    
    createConfettiPiece(container, colors) {
        const confetti = document.createElement('div');
        const color = colors[Math.floor(Math.random() * colors.length)];
        const size = Math.random() * 8 + 4; // 4-12px
        const startX = Math.random() * window.innerWidth;
        const endX = startX + (Math.random() - 0.5) * 200; // Drift sideways
        const duration = Math.random() * 3000 + 3000; // 3-6 seconds (longer fall)
        const delay = Math.random() * 1000; // 0-1000ms delay (more staggered)
        
        confetti.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            background: ${color};
            border-radius: ${Math.random() > 0.5 ? '50%' : '0'};
            left: ${startX}px;
            top: -20px;
            transform: rotate(${Math.random() * 360}deg);
            animation: confettiFall ${duration}ms linear ${delay}ms forwards;
        `;
        
        // Add CSS animation if not already added
        if (!document.getElementById('confetti-styles')) {
            const style = document.createElement('style');
            style.id = 'confetti-styles';
            style.textContent = `
                @keyframes confettiFall {
                    0% {
                        transform: translateY(-20px) rotate(0deg);
                        opacity: 1;
                    }
                    100% {
                        transform: translateY(${window.innerHeight + 20}px) translateX(${endX - startX}px) rotate(720deg);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        container.appendChild(confetti);
    }
    
    addModalCelebrationEffects(category) {
        if (!this.modalOverlay) return;
        
        // Add celebration class to modal
        const celebrationClass = category === 'rare' || category === 'ultra_rare' ? 'rare-celebration' : 'common-celebration';
        this.modalOverlay.classList.add('celebrating', celebrationClass);
        
        // Add enhanced pulsing effect to prize emoji
        const prizeEmoji = document.getElementById('prizeEmoji');
        if (prizeEmoji) {
            const pulseCount = category === 'rare' || category === 'ultra_rare' ? 8 : 6;
            prizeEmoji.style.animation = `celebrationPulse 0.8s ease-in-out ${pulseCount}`;
        }
        
        // Add celebration styles if not already added
        if (!document.getElementById('celebration-styles')) {
            const style = document.createElement('style');
            style.id = 'celebration-styles';
            style.textContent = `
                @keyframes celebrationPulse {
                    0%, 100% { transform: scale(1); filter: brightness(1); }
                    25% { transform: scale(1.08); filter: brightness(1.2); }
                    50% { transform: scale(1.15); filter: brightness(1.4); }
                    75% { transform: scale(1.08); filter: brightness(1.2); }
                }
                
                /* Prevent emoji overflow and scrollbars */
                .modal-overlay .modal-content,
                .modal-overlay .modal {
                    overflow: hidden !important;
                    box-sizing: border-box;
                }
                
                .modal-overlay .prize-emoji {
                    display: inline-block;
                    transform-origin: center center;
                    will-change: transform, filter;
                    margin: 0.5rem 0 !important;
                    line-height: 1 !important;
                }
                
                /* Ensure modal has enough padding to accommodate scaling */
                .modal-overlay.celebrating .modal {
                    padding: 2.5rem 2rem !important;
                }
                
                .modal-overlay.celebrating .modal-content {
                    padding: 1.5rem !important;
                }
                
                .modal-overlay.celebrating {
                    animation: modalCelebration 1.2s cubic-bezier(0.34, 1.56, 0.64, 1);
                }
                
                .modal-overlay.rare-celebration .modal-content {
                    box-shadow: 
                        0 0 30px rgba(255, 215, 0, 0.8), 
                        0 0 60px rgba(255, 215, 0, 0.6),
                        0 0 90px rgba(255, 215, 0, 0.4);
                    border: 3px solid #FFD700;
                    animation: rareCelebrationGlow 2s ease-in-out infinite alternate;
                }
                
                .modal-overlay.common-celebration .modal-content {
                    box-shadow: 
                        0 0 20px rgba(76, 175, 80, 0.7),
                        0 0 40px rgba(76, 175, 80, 0.5);
                    border: 2px solid #4CAF50;
                    animation: commonCelebrationGlow 2s ease-in-out infinite alternate;
                }
                
                @keyframes modalCelebration {
                    0% { 
                        transform: scale(0.8) rotate(-3deg); 
                        opacity: 0; 
                        filter: blur(2px);
                    }
                    30% { 
                        transform: scale(1.05) rotate(1deg); 
                        opacity: 0.8; 
                        filter: blur(1px);
                    }
                    60% { 
                        transform: scale(0.98) rotate(-0.5deg); 
                        opacity: 1; 
                        filter: blur(0px);
                    }
                    100% { 
                        transform: scale(1) rotate(0deg); 
                        opacity: 1; 
                        filter: blur(0px);
                    }
                }
                
                @keyframes rareCelebrationGlow {
                    0% { 
                        box-shadow: 
                            0 0 30px rgba(255, 215, 0, 0.8), 
                            0 0 60px rgba(255, 215, 0, 0.6),
                            0 0 90px rgba(255, 215, 0, 0.4);
                    }
                    100% { 
                        box-shadow: 
                            0 0 40px rgba(255, 215, 0, 1), 
                            0 0 80px rgba(255, 215, 0, 0.8),
                            0 0 120px rgba(255, 215, 0, 0.6);
                    }
                }
                
                @keyframes commonCelebrationGlow {
                    0% { 
                        box-shadow: 
                            0 0 20px rgba(76, 175, 80, 0.7),
                            0 0 40px rgba(76, 175, 80, 0.5);
                    }
                    100% { 
                        box-shadow: 
                            0 0 30px rgba(76, 175, 80, 0.9),
                            0 0 60px rgba(76, 175, 80, 0.7);
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Remove celebration effects after animation (match sound duration)
        const cleanupDelay = category === 'rare' || category === 'ultra_rare' ? 6000 : 5000;
        setTimeout(() => {
            this.modalOverlay.classList.remove('celebrating', 'rare-celebration', 'common-celebration');
            if (prizeEmoji) {
                prizeEmoji.style.animation = '';
            }
        }, cleanupDelay);
        
        console.log('✨ Modal celebration effects added for:', category);
    }

    closeModal() {
        if (this.modalOverlay) {
            this.modalOverlay.classList.remove('show', 'celebrating', 'rare-celebration', 'common-celebration');
        }
    }

    showLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.add('show');
        }
    }

    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.remove('show');
        }
    }

    showError(message) {
        const existingError = document.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;

        const wheelSection = document.querySelector('.wheel-container');
        if (wheelSection) {
            wheelSection.insertAdjacentElement('afterend', errorDiv);
        }

        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    // No daily limit error handling needed - backend filters out prizes that have reached their daily limit

    getUserId() {
        let userId = localStorage.getItem('picker_wheel_user_id');
        if (!userId) {
            userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('picker_wheel_user_id', userId);
        }
        return userId;
    }
    
    // 📋 DAILY PRIZES LOG SYSTEM
    initializeDailyPrizesLog() {
        console.log('📋 Initializing daily prizes log...');
        
        // Get DOM elements
        this.refreshLogBtn = document.getElementById('refreshLogBtn');
        this.clearLogBtn = document.getElementById('clearLogBtn');
        this.dailyPrizesTableBody = document.getElementById('dailyPrizesTableBody');
        this.totalPrizesCount = document.getElementById('totalPrizesCount');
        this.lastUpdated = document.getElementById('lastUpdated');
        
        // Add event listeners
        if (this.refreshLogBtn) {
            this.refreshLogBtn.addEventListener('click', () => this.refreshDailyPrizesLog());
        }
        
        if (this.clearLogBtn) {
            this.clearLogBtn.addEventListener('click', () => this.clearLogDisplay());
        }
        
        // Load initial data
        this.refreshDailyPrizesLog();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            if (!this.logDisplayHidden) {
                this.refreshDailyPrizesLog();
            }
        }, 30000);
        
        console.log('✅ Daily prizes log initialized');
    }
    
    async refreshDailyPrizesLog() {
        try {
            console.log('🔄 Refreshing daily prizes log...');
            
            const response = await fetch('/api/daily-prizes-log');
            const data = await response.json();
            
            if (data.success) {
                this.dailyPrizesLog = data.prizes_won;
                this.updateDailyPrizesDisplay();
                this.updateLogStats(data.total_count);
                console.log(`✅ Loaded ${data.total_count} prize entries`);
            } else {
                console.warn('⚠️ Failed to load daily prizes log:', data.error);
            }
        } catch (error) {
            console.error('❌ Error refreshing daily prizes log:', error);
        }
    }
    
    updateDailyPrizesDisplay() {
        if (!this.dailyPrizesTableBody) return;
        
        // Clear existing rows
        this.dailyPrizesTableBody.innerHTML = '';
        
        if (this.dailyPrizesLog.length === 0) {
            // Show no data message
            const noDataRow = document.createElement('tr');
            noDataRow.className = 'no-data-row';
            noDataRow.innerHTML = `
                <td colspan="4">No prizes won today yet. Spin the wheel to get started! 🎯</td>
            `;
            this.dailyPrizesTableBody.appendChild(noDataRow);
            return;
        }
        
        // Add prize rows
        this.dailyPrizesLog.forEach(prize => {
            const row = document.createElement('tr');
            // Get display for this prize (prefer combo emojis for combo items)
            const comboEmoji = this.getComboEmojiDisplay(prize.name);
            let displayIcon = '';
            
            if (comboEmoji) {
                // Use combo emoji for combo items
                displayIcon = `<span class="prize-emoji" style="font-size: 0.9rem;">${comboEmoji}</span>`;
            } else {
                // Use regular emoji
                displayIcon = `<span class="prize-emoji">${prize.emoji}</span>`;
            }
            
            row.innerHTML = `
                <td>
                    <div class="prize-cell">
                        ${displayIcon}
                        <span class="prize-name">${prize.name}</span>
                    </div>
                </td>
                <td class="time-cell">${prize.formatted_time}</td>
                <td class="user-cell">${prize.user_identifier}</td>
                <td>
                    <span class="category-badge ${prize.category}">${prize.category.replace('_', ' ')}</span>
                </td>
            `;
            this.dailyPrizesTableBody.appendChild(row);
        });
    }
    
    updateLogStats(totalCount) {
        if (this.totalPrizesCount) {
            this.totalPrizesCount.textContent = totalCount;
        }
        
        if (this.lastUpdated) {
            const now = new Date();
            this.lastUpdated.textContent = now.toLocaleTimeString();
        }
    }
    
    clearLogDisplay() {
        console.log('🗑️ Clearing log display (UI only)...');
        
        // Clear the display but keep the actual data
        this.logDisplayHidden = true;
        
        if (this.dailyPrizesTableBody) {
            this.dailyPrizesTableBody.innerHTML = `
                <tr class="no-data-row">
                    <td colspan="4">Log display cleared. Click "Refresh" to reload data. 🔄</td>
                </tr>
            `;
        }
        
        if (this.totalPrizesCount) {
            this.totalPrizesCount.textContent = '0 (hidden)';
        }
        
        if (this.lastUpdated) {
            this.lastUpdated.textContent = 'Display cleared';
        }
        
        // Show refresh button prominently
        if (this.refreshLogBtn) {
            this.refreshLogBtn.style.background = 'rgba(76, 175, 80, 0.3)';
            this.refreshLogBtn.style.border = '2px solid #4CAF50';
            
            // Reset button style after 3 seconds
            setTimeout(() => {
                this.refreshLogBtn.style.background = '';
                this.refreshLogBtn.style.border = '';
            }, 3000);
        }
        
        // Re-enable auto-refresh on next refresh click
        this.logDisplayHidden = false;
    }
    
    // Add prize to log when won (called after successful spin)
    addPrizeToLog(prize) {
        const now = new Date();
        const logEntry = {
            prize_id: prize.id,
            name: prize.name,
            user_identifier: 'You',
            formatted_time: now.toLocaleTimeString(),
            category: prize.category,
            emoji: prize.emoji
        };
        
        // Add to beginning of array (most recent first)
        this.dailyPrizesLog.unshift(logEntry);
        
        // Update display if not hidden
        if (!this.logDisplayHidden) {
            this.updateDailyPrizesDisplay();
            this.updateLogStats(this.dailyPrizesLog.length);
        }
        
        console.log('📋 Added prize to log:', prize.name);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM loaded, initializing PickerWheel UI...');
    window.pickerWheelUI = new PickerWheelUI();
});

// Version information for cache validation
const WHEEL_VERSION = '11.3_20250922';
const BUILD_DATE = '2025-09-22';

console.log('📱 PickerWheel UI v' + WHEEL_VERSION + ' loaded successfully!');
console.log('🗓 Build date: ' + BUILD_DATE);

// Clear browser cache for API requests
if ('caches' in window) {
    caches.keys().then(cacheNames => {
        cacheNames.forEach(cacheName => {
            if (cacheName.includes('wheel') || cacheName.includes('prize') || cacheName.includes('spin')) {
                console.log('🧹 Clearing cache:', cacheName);
                caches.delete(cacheName);
            }
        });
    });
}
