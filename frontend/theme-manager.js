/**
 * ThemeManager - Dynamic Theme Loading and Application
 * Loads theme configuration from backend and applies to the UI
 */

class ThemeManager {
    constructor() {
        this.apiBaseUrl = '/api';
        // Default theme: Magenta Pink (#E20074) with Soft White (#FFF5F8)
        this.defaultTheme = {
            name: 'default',
            background: {
                type: 'gradient',
                colors: ['#E20074', '#FFF5F8', '#FF4D9F'],
                style: 'radial'
            },
            wheel: {
                colors: ['#E20074', '#FF4D9F', '#B8005D', '#FF80B5', '#9E0052', '#FF66A3'],
                borderColor: '#B8005D',
                textColor: '#FFFFFF'
            },
            header: {
                backgroundColor: '#E20074',
                gradientEnd: '#B8005D',
                textColor: '#FFFFFF',
                title: 'SPIN & WIN',
                subtitle: 'Win Exciting Prizes!'
            },
            floatingElements: ['🎁', '✨', '💫', '🎊', '🏆', '⭐', '🎈', '🎉']
        };
        this.activeTheme = null;
        this.activeEvent = null;
    }

    /**
     * Load configuration from backend
     */
    async loadConfig() {
        try {
            console.log('🎨 Loading theme configuration...');
            const response = await fetch(`${this.apiBaseUrl}/config`, {
                cache: 'no-cache'
            });
            const data = await response.json();

            if (data.success) {
                this.activeTheme = data.theme || this.defaultTheme;
                this.activeEvent = data.event;
                
                console.log('✅ Theme loaded:', this.activeTheme.name);
                if (data.event?.is_active) {
                    console.log('🎉 Active event:', data.event.name);
                }
                
                return data;
            } else {
                console.warn('⚠️ Failed to load config, using defaults');
                this.activeTheme = this.defaultTheme;
                return null;
            }
        } catch (error) {
            console.error('❌ Error loading theme:', error);
            this.activeTheme = this.defaultTheme;
            return null;
        }
    }

    /**
     * Apply the active theme to the page
     */
    applyTheme() {
        if (!this.activeTheme) {
            console.warn('No theme to apply, using defaults');
            this.activeTheme = this.defaultTheme;
        }

        console.log('🎨 Applying theme:', this.activeTheme.name);

        // Apply CSS variables
        this.applyCSSVariables();

        // Apply background
        this.applyBackground();

        // Apply header styling
        this.applyHeader();

        // Apply floating elements
        this.applyFloatingElements();

        console.log('✅ Theme applied successfully');
    }

    /**
     * Apply CSS variables from theme
     */
    applyCSSVariables() {
        const root = document.documentElement;
        const theme = this.activeTheme;

        // Background colors
        if (theme.background?.colors) {
            root.style.setProperty('--theme-bg-primary', theme.background.colors[0] || '#FF9933');
            root.style.setProperty('--theme-bg-secondary', theme.background.colors[1] || '#FFFFFF');
            root.style.setProperty('--theme-bg-tertiary', theme.background.colors[2] || '#138808');
        }

        // Wheel colors
        if (theme.wheel) {
            root.style.setProperty('--wheel-border-color', theme.wheel.borderColor || '#E67300');
            root.style.setProperty('--wheel-text-color', theme.wheel.textColor || '#FFFFFF');
        }

        // Header colors
        if (theme.header) {
            root.style.setProperty('--header-bg-color', theme.header.backgroundColor || '#FF9933');
            root.style.setProperty('--header-gradient-end', theme.header.gradientEnd || '#E67300');
            root.style.setProperty('--header-text-color', theme.header.textColor || '#FFFFFF');
        }
    }

    /**
     * Apply background styling
     */
    applyBackground() {
        const theme = this.activeTheme;
        const body = document.body;

        if (theme.background) {
            const bg = theme.background;
            
            if (bg.type === 'gradient' && bg.colors) {
                const colors = bg.colors;
                
                if (bg.style === 'radial') {
                    // Watercolor-inspired radial gradient
                    body.style.background = `
                        radial-gradient(ellipse at 0% 0%, ${this.hexToRgba(colors[0], 0.4)} 0%, transparent 50%),
                        radial-gradient(ellipse at 100% 0%, ${this.hexToRgba(colors[0], 0.3)} 0%, transparent 40%),
                        radial-gradient(ellipse at 0% 100%, ${this.hexToRgba(colors[2] || colors[0], 0.4)} 0%, transparent 50%),
                        radial-gradient(ellipse at 100% 100%, ${this.hexToRgba(colors[2] || colors[0], 0.3)} 0%, transparent 40%),
                        radial-gradient(ellipse at 50% 50%, rgba(255, 255, 255, 0.95) 0%, rgba(255, 248, 240, 0.9) 100%)
                    `;
                    body.style.backgroundColor = '#FFF8F0';
                } else if (bg.style === 'linear') {
                    // Linear gradient (like tricolor)
                    body.style.background = `linear-gradient(180deg, ${colors.join(', ')})`;
                } else {
                    // Default to simple gradient
                    body.style.background = `linear-gradient(135deg, ${colors[0]}, ${colors[1] || colors[0]})`;
                }
                
                body.style.backgroundAttachment = 'fixed';
            } else if (bg.type === 'solid' && bg.colors) {
                body.style.background = bg.colors[0];
            } else if (bg.type === 'image' && bg.imageUrl) {
                body.style.background = `url('${bg.imageUrl}') no-repeat center center`;
                body.style.backgroundSize = 'cover';
                body.style.backgroundAttachment = 'fixed';
            }
        }
    }

    /**
     * Apply header styling
     */
    applyHeader() {
        const theme = this.activeTheme;
        
        if (theme.header) {
            const header = theme.header;
            
            // Update header navigation background
            const topNav = document.querySelector('.top-nav');
            if (topNav) {
                topNav.style.background = `linear-gradient(135deg, ${header.backgroundColor || '#FF9933'}, ${header.gradientEnd || '#E67300'})`;
            }

            // Update title text
            const mainTitle = document.querySelector('.main-title');
            if (mainTitle && header.title) {
                mainTitle.textContent = `🎉 ${header.title} 🎊`;
                mainTitle.style.color = header.textColor || '#FFFFFF';
            }

            // Update subtitle
            const subtitle = document.querySelector('.subtitle');
            if (subtitle && header.subtitle) {
                subtitle.textContent = `✨ ${header.subtitle} ✨`;
                subtitle.style.color = header.textColor || '#FFFFFF';
            }
        }
    }

    /**
     * Apply floating elements
     */
    applyFloatingElements() {
        const theme = this.activeTheme;
        
        if (theme.floatingElements && Array.isArray(theme.floatingElements)) {
            const container = document.querySelector('.background-elements');
            if (container) {
                const floatingEls = container.querySelectorAll('.floating-element');
                const emojis = theme.floatingElements;
                
                floatingEls.forEach((el, index) => {
                    el.textContent = emojis[index % emojis.length];
                });
            }
        }
    }

    /**
     * Get wheel colors from theme
     */
    getWheelColors() {
        return this.activeTheme?.wheel?.colors || this.defaultTheme.wheel.colors;
    }

    /**
     * Get wheel text color from theme
     */
    getWheelTextColor() {
        return this.activeTheme?.wheel?.textColor || '#FFFFFF';
    }

    /**
     * Convert hex color to rgba
     */
    hexToRgba(hex, alpha = 1) {
        if (!hex) return `rgba(255, 153, 51, ${alpha})`;
        
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if (result) {
            const r = parseInt(result[1], 16);
            const g = parseInt(result[2], 16);
            const b = parseInt(result[3], 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }
        return `rgba(255, 153, 51, ${alpha})`;
    }

    /**
     * Check if an event is currently active
     */
    hasActiveEvent() {
        return this.activeEvent?.is_active === true;
    }

    /**
     * Get active event info
     */
    getActiveEvent() {
        return this.activeEvent;
    }
}

// Create global instance
window.themeManager = new ThemeManager();
console.log('🎨 ThemeManager initialized');
