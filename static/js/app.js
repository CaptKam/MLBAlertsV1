class MLBMonitor {
    constructor() {
        this.selectedGames = new Set();
        this.alertsPollingInterval = null;
        this.statusPollingInterval = null;
        this.lastAlertCount = 0;
        this.soundEnabled = localStorage.getItem('soundEnabled') !== 'false';
        this.allAlerts = [];
        this.filteredAlerts = [];
        
        // Initialize with default preferences (will be loaded from database)
        this.notificationPreferences = {
            runners: true,
            hits: true,
            scoring: true,
            inning_change: false,
            home_runs: false,
            strikeouts: false,
            seventh_inning: true,
            game_start: true,
            runners_23_no_outs: true,
            bases_loaded_no_outs: true,
            runner_3rd_no_outs: true,
            runners_13_no_outs: false,
            runners_23_one_out: false,
            bases_loaded_one_out: false
        };
        
        this.initializeEventListeners();
        this.loadUserSettingsFromDatabase();
        this.loadGames();
        this.loadPersistentSettings();
        this.startPolling();
        this.loadSuccessRateStats();
        
        // Refresh success rate stats every 30 seconds
        setInterval(() => {
            this.loadSuccessRateStats();
        }, 30000);
    }

    async loadUserSettingsFromDatabase() {
        try {
            const response = await fetch('/api/user/settings');
            const data = await response.json();
            
            if (data.success && data.settings.notification_preferences) {
                this.notificationPreferences = { ...this.notificationPreferences, ...data.settings.notification_preferences };
                console.log('✅ Loaded user settings from database:', this.notificationPreferences);
            } else {
                console.log('ℹ️ Using default notification preferences');
            }
        } catch (error) {
            console.error('Error loading user settings from database:', error);
        }
        
        // Update UI with loaded preferences
        this.loadNotificationPreferences();
    }

    loadNotificationPreferences() {
        // Load saved preferences and update checkboxes
        if (this.notificationPreferences.runners !== undefined) {
            document.getElementById('alertRunners').checked = this.notificationPreferences.runners;
            document.getElementById('alertHits').checked = this.notificationPreferences.hits;
            document.getElementById('alertScoring').checked = this.notificationPreferences.scoring;
            document.getElementById('alertInningChange').checked = this.notificationPreferences.inning_change;
            document.getElementById('alertHomeRuns').checked = this.notificationPreferences.home_runs;
            document.getElementById('alertStrikeouts').checked = this.notificationPreferences.strikeouts;
            document.getElementById('alert7thInning').checked = this.notificationPreferences.seventh_inning !== false;
            document.getElementById('alertGameStart').checked = this.notificationPreferences.game_start !== false;
            document.getElementById('alertRunners23NoOuts').checked = this.notificationPreferences.runners_23_no_outs;
            document.getElementById('alertBasesLoadedNoOuts').checked = this.notificationPreferences.bases_loaded_no_outs;
            document.getElementById('alertRunner3rdNoOuts').checked = this.notificationPreferences.runner_3rd_no_outs;
            document.getElementById('alertRunners13NoOuts').checked = this.notificationPreferences.runners_13_no_outs;
            document.getElementById('alertRunners23OneOut').checked = this.notificationPreferences.runners_23_one_out;
            document.getElementById('alertBasesLoadedOneOut').checked = this.notificationPreferences.bases_loaded_one_out;
            document.getElementById('alertRunners12NoOuts').checked = this.notificationPreferences.runners_12_no_outs;
            document.getElementById('alertRunner2ndNoOuts').checked = this.notificationPreferences.runner_2nd_no_outs;
            document.getElementById('alertRunner3rdOneOut').checked = this.notificationPreferences.runner_3rd_one_out;
            document.getElementById('alertRunners13OneOut').checked = this.notificationPreferences.runners_13_one_out;
            
            // Weather-based alerts
            if (document.getElementById('alertWindSpeed')) {
                document.getElementById('alertWindSpeed').checked = this.notificationPreferences.wind_speed !== false;
            }
            if (document.getElementById('alertWindShift')) {
                document.getElementById('alertWindShift').checked = this.notificationPreferences.wind_shift !== false;
            }
            if (document.getElementById('alertPrimeHRConditions')) {
                document.getElementById('alertPrimeHRConditions').checked = this.notificationPreferences.prime_hr_conditions !== false;
            }
            if (document.getElementById('alertHotWindy')) {
                document.getElementById('alertHotWindy').checked = this.notificationPreferences.hot_windy !== false;
            }
            if (document.getElementById('alertWeatherDelay')) {
                document.getElementById('alertWeatherDelay').checked = this.notificationPreferences.weather_delay !== false;
            }
            if (document.getElementById('alertGameResumption')) {
                document.getElementById('alertGameResumption').checked = this.notificationPreferences.game_resumption !== false;
            }
            if (document.getElementById('alertTempWind')) {
                document.getElementById('alertTempWind').checked = this.notificationPreferences.temp_wind !== false;
            }
            
            // Power hitter alerts
            if (document.getElementById('alertPowerHitter')) {
                document.getElementById('alertPowerHitter').checked = this.notificationPreferences.power_hitter !== false;
            }
            if (document.getElementById('alertHotHitter')) {
                document.getElementById('alertHotHitter').checked = this.notificationPreferences.hot_hitter !== false;
            }
            if (document.getElementById('alertClutchHR')) {
                document.getElementById('alertClutchHR').checked = this.notificationPreferences.clutch_hr !== false;
            }
            
            // Advanced ROI Alerts
            if (document.getElementById('aiPowerPlusScoring')) {
                document.getElementById('aiPowerPlusScoring').checked = this.notificationPreferences.ai_power_plus_scoring !== false;
            }
            if (document.getElementById('aiPowerHighConfidence')) {
                document.getElementById('aiPowerHighConfidence').checked = this.notificationPreferences.ai_power_high !== false;
            }
            if (document.getElementById('pitcherSoftening')) {
                document.getElementById('pitcherSoftening').checked = this.notificationPreferences.pitcher_softening !== false;
            }

            
            // AI Insights Features - Load from saved preferences
            if (document.getElementById('aiAnalyzeHits')) {
                document.getElementById('aiAnalyzeHits').checked = this.notificationPreferences.ai_analyze_hits === true;
            }
            if (document.getElementById('aiAnalyzeRunners')) {
                document.getElementById('aiAnalyzeRunners').checked = this.notificationPreferences.ai_analyze_runners === true;
            }
            if (document.getElementById('aiAnalyzePowerHitter')) {
                document.getElementById('aiAnalyzePowerHitter').checked = this.notificationPreferences.ai_analyze_power_hitter === true;
            }
            if (document.getElementById('aiPredictScoring')) {
                document.getElementById('aiPredictScoring').checked = this.notificationPreferences.ai_predict_scoring === true;
            }
            if (document.getElementById('aiSummarizeEvents')) {
                document.getElementById('aiSummarizeEvents').checked = this.notificationPreferences.ai_summarize_events === true;
            }
            if (document.getElementById('aiEnhanceAlerts')) {
                document.getElementById('aiEnhanceAlerts').checked = this.notificationPreferences.ai_enhance_alerts === true;
            }
        }
    }

    initializeEventListeners() {
        // Refresh games button
        document.getElementById('refreshGames').addEventListener('click', () => {
            this.loadGames();
        });

        // Update monitoring button
        document.getElementById('updateMonitoring').addEventListener('click', () => {
            this.updateMonitoring();
        });

        // Clear alerts button
        document.getElementById('clearAlerts').addEventListener('click', () => {
            this.clearAlerts();
        });

        // Test Telegram button
        document.getElementById('testTelegram').addEventListener('click', () => {
            this.testTelegram();
        });
        
        // Toggle Auto Monitoring button
        if (document.getElementById('toggleAutoMonitoring')) {
            document.getElementById('toggleAutoMonitoring').addEventListener('click', () => {
                this.toggleAutoMonitoring();
            });
        }

        // Stop monitoring button
        if (document.getElementById('stopMonitoring')) {
            document.getElementById('stopMonitoring').addEventListener('click', () => {
                this.stopMonitoring();
            });
        }

        // Sound toggle button
        if (document.getElementById('toggleSound')) {
            document.getElementById('toggleSound').addEventListener('click', () => {
                this.toggleSound();
            });
            this.updateSoundIcon();
        }

        // Alert search and filter
        if (document.getElementById('alertSearch')) {
            document.getElementById('alertSearch').addEventListener('input', () => {
                this.filterAlerts();
            });
        }
        if (document.getElementById('alertTypeFilter')) {
            document.getElementById('alertTypeFilter').addEventListener('change', () => {
                this.filterAlerts();
            });
        }


        // Notification type checkboxes
        document.getElementById('alertRunners').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertHits').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertScoring').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertInningChange').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertHomeRuns').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertStrikeouts').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alert7thInning').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertGameStart').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });

        // High-probability scoring situation checkboxes
        document.getElementById('alertRunners23NoOuts').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertBasesLoadedNoOuts').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertRunner3rdNoOuts').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertRunners13NoOuts').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertRunners23OneOut').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertBasesLoadedOneOut').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertRunners12NoOuts').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertRunner2ndNoOuts').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertRunner3rdOneOut').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        document.getElementById('alertRunners13OneOut').addEventListener('change', () => {
            this.updateNotificationPreferences();
        });
        
        // Weather-based alert checkboxes
        const windSpeedEl = document.getElementById('alertWindSpeed');
        if (windSpeedEl) {
            windSpeedEl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        const windShiftEl = document.getElementById('alertWindShift');
        if (windShiftEl) {
            windShiftEl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        const primeHREl = document.getElementById('alertPrimeHRConditions');
        if (primeHREl) {
            primeHREl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        const hotWindyEl = document.getElementById('alertHotWindy');
        if (hotWindyEl) {
            hotWindyEl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        const tempWindEl = document.getElementById('alertTempWind');
        if (tempWindEl) {
            tempWindEl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        
        // Power hitter alert checkboxes
        const powerHitterEl = document.getElementById('alertPowerHitter');
        if (powerHitterEl) {
            powerHitterEl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        const hotHitterEl = document.getElementById('alertHotHitter');
        if (hotHitterEl) {
            hotHitterEl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        const clutchHREl = document.getElementById('alertClutchHR');
        if (clutchHREl) {
            clutchHREl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        
        // Advanced ROI Alert checkboxes
        const aiPowerPlusScoringEl = document.getElementById('aiPowerPlusScoring');
        if (aiPowerPlusScoringEl) {
            aiPowerPlusScoringEl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        const aiPowerHighEl = document.getElementById('aiPowerHighConfidence');
        if (aiPowerHighEl) {
            aiPowerHighEl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        const pitcherSofteningEl = document.getElementById('pitcherSoftening');
        if (pitcherSofteningEl) {
            pitcherSofteningEl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        const pitcherBallStreakEl = document.getElementById('pitcherBallStreak');
        if (pitcherBallStreakEl) {
            pitcherBallStreakEl.addEventListener('change', () => this.updateNotificationPreferences());
        }
        
        // AI Insights checkboxes
        const aiCheckboxes = [
            'aiAnalyzeHits',
            'aiAnalyzeRunners', 
            'aiAnalyzePowerHitter',
            'aiPredictScoring',
            'aiSummarizeEvents',
            'aiEnhanceAlerts'
        ];
        
        aiCheckboxes.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.updateNotificationPreferences());
            }
        });
        
        // ROI+ Early-Notice Alert checkboxes - Only weather delay alerts remain
        const roiAlertCheckboxes = [
            'alertWeatherDelay',
            'alertGameResumption'
        ];
        
        roiAlertCheckboxes.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => this.updateNotificationPreferences());
            }
        });
    }

    async loadGames() {
        const loadingEl = document.getElementById('gamesLoading');
        const errorEl = document.getElementById('gamesError');
        const containerEl = document.getElementById('gamesContainer');
        const noGamesEl = document.getElementById('noGames');

        // Show loading state
        loadingEl.classList.remove('d-none');
        errorEl.classList.add('d-none');
        containerEl.classList.add('d-none');
        noGamesEl.classList.add('d-none');

        try {
            const response = await fetch('/api/games');
            const data = await response.json();

            if (data.success && data.games.length > 0) {
                this.renderGames(data.games);
                containerEl.classList.remove('d-none');
            } else if (data.success && data.games.length === 0) {
                noGamesEl.classList.remove('d-none');
            } else {
                throw new Error(data.error || 'Failed to load games');
            }
        } catch (error) {
            console.error('Error loading games:', error);
            document.getElementById('gamesErrorMessage').textContent = error.message;
            errorEl.classList.remove('d-none');
        } finally {
            loadingEl.classList.add('d-none');
        }
    }

    renderGames(games) {
        const listEl = document.getElementById('gamesList');
        listEl.innerHTML = '';

        games.forEach(game => {
            const gameEl = document.createElement('div');
            gameEl.className = 'game-item';
            gameEl.dataset.gameId = game.id;

            const statusClass = this.getStatusClass(game.status);
            const statusIcon = this.getStatusIcon(game.status);
            const timeInfo = this.formatGameTime(game);

            gameEl.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="game-${game.id}">
                    <label class="form-check-label w-100" for="game-${game.id}">
                        <div class="d-flex justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <div class="fw-bold">${game.away_team} @ ${game.home_team}</div>
                                <div class="game-status ${statusClass}">
                                    <i class="${statusIcon} me-1"></i>
                                    ${game.status}
                                    ${timeInfo}
                                </div>
                            </div>
                            <div class="text-end">
                                <div class="badge bg-secondary">${game.away_score} - ${game.home_score}</div>
                            </div>
                        </div>
                    </label>
                </div>
            `;

            // Add event listener for checkbox
            const checkbox = gameEl.querySelector('input[type="checkbox"]');
            checkbox.addEventListener('change', async (e) => {
                // Disable checkbox during update
                e.target.disabled = true;
                
                // Add loading class to game item
                gameEl.classList.add('updating');
                
                if (e.target.checked) {
                    this.selectedGames.add(parseInt(game.id));
                    gameEl.classList.add('selected');
                } else {
                    this.selectedGames.delete(parseInt(game.id));
                    gameEl.classList.remove('selected');
                }
                // Update the monitored count display immediately
                this.updateMonitoredCount();
                
                // Automatically start/update monitoring when games are selected
                try {
                    const response = await fetch('/api/monitor', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            game_ids: Array.from(this.selectedGames),
                            notification_preferences: this.notificationPreferences
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        // Show brief success notification
                        this.showToast('success', `Monitoring ${this.selectedGames.size} game(s)`);
                        
                        // Update button visibility
                        if (this.selectedGames.size > 0) {
                            document.getElementById('updateMonitoring').classList.add('d-none');
                            document.getElementById('stopMonitoring').classList.remove('d-none');
                        } else {
                            document.getElementById('updateMonitoring').classList.remove('d-none');
                            document.getElementById('stopMonitoring').classList.add('d-none');
                        }
                        
                        // Re-enable checkbox and remove loading
                        e.target.disabled = false;
                        gameEl.classList.remove('updating');
                    } else {
                        this.showToast('error', 'Failed to update monitoring');
                        // Revert checkbox state on error
                        e.target.checked = !e.target.checked;
                        if (e.target.checked) {
                            this.selectedGames.add(parseInt(game.id));
                            gameEl.classList.add('selected');
                        } else {
                            this.selectedGames.delete(parseInt(game.id));
                            gameEl.classList.remove('selected');
                        }
                        
                        // Re-enable checkbox and remove loading
                        e.target.disabled = false;
                        gameEl.classList.remove('updating');
                    }
                } catch (error) {
                    console.error('Error updating monitoring:', error);
                    this.showToast('error', 'Network error - please try again');
                    // Revert checkbox state on error
                    e.target.checked = !e.target.checked;
                    if (e.target.checked) {
                        this.selectedGames.add(parseInt(game.id));
                        gameEl.classList.add('selected');
                    } else {
                        this.selectedGames.delete(parseInt(game.id));
                        gameEl.classList.remove('selected');
                    }
                    
                    // Re-enable checkbox and remove loading
                    e.target.disabled = false;
                    gameEl.classList.remove('updating');
                }
            });

            listEl.appendChild(gameEl);
        });
        
        // Initialize monitored count display after all games are rendered
        this.updateMonitoredCount();
    }

    getStatusClass(status) {
        if (status.includes('In Progress') || status.includes('Live')) {
            return 'live';
        } else if (status.includes('Final')) {
            return 'final';
        } else {
            return 'scheduled';
        }
    }

    getStatusIcon(status) {
        if (status.includes('In Progress') || status.includes('Live')) {
            return 'fas fa-circle text-success';
        } else if (status.includes('Final')) {
            return 'fas fa-check-circle';
        } else {
            return 'fas fa-clock';
        }
    }

    formatGameTime(game) {
        if (game.status.includes('In Progress') && game.inning > 0) {
            return `(${game.inning_state} ${game.inning})`;
        } else if (game.start_time) {
            const startTime = new Date(game.start_time);
            return `(${startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})`;
        }
        return '';
    }

    async updateMonitoring() {
        const button = document.getElementById('updateMonitoring');
        const originalHTML = button.innerHTML;

        try {
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Updating...';
            button.disabled = true;

            // Add timeout to prevent hanging
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
            
            const response = await fetch('/api/monitor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    game_ids: Array.from(this.selectedGames),
                    notification_preferences: this.notificationPreferences
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            const data = await response.json();

            if (data.success) {
                this.showToast('success', data.message);
                // Show/hide buttons based on monitoring state
                if (this.selectedGames.size > 0) {
                    document.getElementById('updateMonitoring').classList.add('d-none');
                    document.getElementById('stopMonitoring').classList.remove('d-none');
                } else {
                    document.getElementById('updateMonitoring').classList.remove('d-none');
                    document.getElementById('stopMonitoring').classList.add('d-none');
                }
                // Update status immediately
                setTimeout(() => {
                    this.updateStatus();
                    this.loadPersistentSettings();
                }, 500);
            } else {
                throw new Error(data.error || 'Failed to update monitoring');
            }
        } catch (error) {
            console.error('Error updating monitoring:', error);
            this.showToast('error', error.message || 'Failed to update monitoring');
        } finally {
            // Always reset button state, even on errors
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }

    async updateStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            if (data.success) {
                const status = data.status;
                const statusBadge = document.getElementById('statusBadge');
                const statusText = document.getElementById('statusText');
                const lastUpdate = document.getElementById('lastUpdate');

                if (status.running && status.monitored_games_count > 0) {
                    statusBadge.className = 'badge bg-success me-2';
                    statusBadge.textContent = 'Active';
                    
                    const enabledTypes = status.enabled_alert_types || [];
                    const typesText = enabledTypes.length > 0 ? 
                        ` (${enabledTypes.join(', ')})` : '';
                    
                    statusText.textContent = `Monitoring ${status.monitored_games_count} game(s)${typesText}`;
                } else {
                    statusBadge.className = 'badge bg-secondary me-2';
                    statusBadge.textContent = 'Stopped';
                    statusText.textContent = 'Not monitoring any games';
                }

                const updateTime = new Date(status.last_update);
                lastUpdate.textContent = `Last update: ${updateTime.toLocaleTimeString()}`;
            }
        } catch (error) {
            console.error('Error updating status:', error);
        }
    }

    async updateAlerts() {
        try {
            const response = await fetch('/api/alerts');
            const data = await response.json();

            if (data.success) {
                this.allAlerts = data.alerts;
                this.filterAlerts();
            }
        } catch (error) {
            console.error('Error fetching alerts:', error);
        }
    }

    filterAlerts() {
        const searchTerm = document.getElementById('alertSearch').value.toLowerCase();
        const typeFilter = document.getElementById('alertTypeFilter').value;
        
        this.filteredAlerts = this.allAlerts.filter(alert => {
            const matchesSearch = !searchTerm || 
                alert.game_info.toLowerCase().includes(searchTerm) ||
                alert.message.toLowerCase().includes(searchTerm);
            
            const matchesType = !typeFilter || alert.type === typeFilter;
            
            return matchesSearch && matchesType;
        });
        
        this.renderAlerts(this.filteredAlerts);
    }

    renderAlerts(alerts) {
        const alertsList = document.getElementById('alertsList');
        const noAlerts = document.getElementById('noAlerts');
        const alertCount = document.getElementById('alertCount');

        alertCount.textContent = this.allAlerts.length;

        if (alerts.length === 0) {
            noAlerts.classList.remove('d-none');
            alertsList.innerHTML = '';
            return;
        }

        noAlerts.classList.add('d-none');

        // Check for new alerts
        const isNewAlert = this.allAlerts.length > this.lastAlertCount;
        this.lastAlertCount = this.allAlerts.length;
        
        // Play sound for new alerts if enabled
        if (isNewAlert && this.soundEnabled && this.allAlerts.length > 0) {
            this.playAlertSound(this.allAlerts[0].type);
        }

        alertsList.innerHTML = '';
        alerts.forEach((alert, index) => {
            const alertEl = document.createElement('div');
            alertEl.className = `alert-item alert-type-${alert.type}`;
            
            if (isNewAlert && index === 0) {
                alertEl.classList.add('new');
            }

            const timestamp = new Date(alert.timestamp);
            const timeString = timestamp.toLocaleTimeString();

            alertEl.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="alert-game">${alert.game_info}</div>
                        <div class="alert-message">${alert.message}</div>
                    </div>
                    <div class="alert-timestamp">${timeString}</div>
                </div>
            `;

            alertsList.appendChild(alertEl);
        });

        // Auto-scroll to top for new alerts
        if (isNewAlert) {
            document.getElementById('alertsContainer').scrollTop = 0;
        }
    }

    async clearAlerts() {
        try {
            // Clear alerts on backend first
            const response = await fetch('/api/alerts/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            
            if (data.success) {
                // Clear frontend display
                document.getElementById('alertsList').innerHTML = '';
                document.getElementById('noAlerts').classList.remove('d-none');
                document.getElementById('alertCount').textContent = '0';
                this.lastAlertCount = 0;
                this.allAlerts = [];
                this.filteredAlerts = [];
                
                // Show success message
                this.showToast('success', data.message || 'All alerts cleared');
                console.log(`✅ Cleared ${data.cleared_count} alerts from backend`);
            } else {
                throw new Error(data.error || 'Failed to clear alerts');
            }
        } catch (error) {
            console.error('Error clearing alerts:', error);
            this.showToast('error', 'Failed to clear alerts: ' + error.message);
        }
    }

    async testTelegram() {
        const button = document.getElementById('testTelegram');
        const statusEl = document.getElementById('telegramStatus');
        const originalHTML = button.innerHTML;

        try {
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Sending...';
            button.disabled = true;
            statusEl.textContent = 'Sending test message...';

            const response = await fetch('/api/telegram/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.success) {
                statusEl.textContent = 'Test message sent successfully!';
                statusEl.className = 'small text-success';
                this.showToast('success', 'Telegram test message sent!');
            } else {
                throw new Error(data.error || 'Failed to send test message');
            }
        } catch (error) {
            console.error('Error testing Telegram:', error);
            statusEl.textContent = 'Failed to send test message';
            statusEl.className = 'small text-danger';
            this.showToast('error', error.message || 'Failed to test Telegram');
        } finally {
            button.innerHTML = originalHTML;
            button.disabled = false;
            
            // Reset status text after 5 seconds
            setTimeout(() => {
                statusEl.textContent = 'Ready to send alerts';
                statusEl.className = 'small text-muted';
            }, 5000);
        }
    }

    startPolling() {
        // Poll for alerts every 2 seconds for maximum speed
        this.alertsPollingInterval = setInterval(() => {
            this.updateAlerts();
        }, 2000);

        // Poll for status every 10 seconds
        this.statusPollingInterval = setInterval(() => {
            this.updateStatus();
        }, 10000);

        // Initial status update
        this.updateStatus();
    }

    showToast(type, message) {
        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

        document.body.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    updateNotificationPreferences() {
        this.notificationPreferences = {
            runners: document.getElementById('alertRunners').checked,
            hits: document.getElementById('alertHits').checked,
            scoring: document.getElementById('alertScoring').checked,
            inning_change: document.getElementById('alertInningChange').checked,
            home_runs: document.getElementById('alertHomeRuns').checked,
            strikeouts: document.getElementById('alertStrikeouts').checked,
            seventh_inning: document.getElementById('alert7thInning').checked,
            game_start: document.getElementById('alertGameStart').checked,
            runners_23_no_outs: document.getElementById('alertRunners23NoOuts').checked,
            bases_loaded_no_outs: document.getElementById('alertBasesLoadedNoOuts').checked,
            runner_3rd_no_outs: document.getElementById('alertRunner3rdNoOuts').checked,
            runners_13_no_outs: document.getElementById('alertRunners13NoOuts').checked,
            runners_23_one_out: document.getElementById('alertRunners23OneOut').checked,
            bases_loaded_one_out: document.getElementById('alertBasesLoadedOneOut').checked,
            runners_12_no_outs: document.getElementById('alertRunners12NoOuts').checked,
            runner_2nd_no_outs: document.getElementById('alertRunner2ndNoOuts').checked,
            runner_3rd_one_out: document.getElementById('alertRunner3rdOneOut').checked,
            runners_13_one_out: document.getElementById('alertRunners13OneOut').checked,
            // Weather-based alerts
            wind_speed: document.getElementById('alertWindSpeed') ? document.getElementById('alertWindSpeed').checked : true,
            wind_shift: document.getElementById('alertWindShift') ? document.getElementById('alertWindShift').checked : true,
            prime_hr_conditions: document.getElementById('alertPrimeHRConditions') ? document.getElementById('alertPrimeHRConditions').checked : true,
            hot_windy: document.getElementById('alertHotWindy') ? document.getElementById('alertHotWindy').checked : true,
            weather_delay: document.getElementById('alertWeatherDelay') ? document.getElementById('alertWeatherDelay').checked : true,
            game_resumption: document.getElementById('alertGameResumption') ? document.getElementById('alertGameResumption').checked : true,
            temp_wind: document.getElementById('alertTempWind') ? document.getElementById('alertTempWind').checked : true,
            // Power hitter alerts
            power_hitter: document.getElementById('alertPowerHitter') ? document.getElementById('alertPowerHitter').checked : true,
            hot_hitter: document.getElementById('alertHotHitter') ? document.getElementById('alertHotHitter').checked : true,
            clutch_hr: document.getElementById('alertClutchHR') ? document.getElementById('alertClutchHR').checked : true,
            // Advanced ROI Alerts
            ai_power_plus_scoring: document.getElementById('aiPowerPlusScoring') ? document.getElementById('aiPowerPlusScoring').checked : true,
            ai_power_high: document.getElementById('aiPowerHighConfidence') ? document.getElementById('aiPowerHighConfidence').checked : true,
            pitcher_softening: document.getElementById('pitcherSoftening') ? document.getElementById('pitcherSoftening').checked : true,

            // AI Insights Features - Use checkbox value if present, otherwise use saved preference or false
            ai_analyze_hits: document.getElementById('aiAnalyzeHits') ? document.getElementById('aiAnalyzeHits').checked : false,
            ai_analyze_runners: document.getElementById('aiAnalyzeRunners') ? document.getElementById('aiAnalyzeRunners').checked : false,
            ai_analyze_power_hitter: document.getElementById('aiAnalyzePowerHitter') ? document.getElementById('aiAnalyzePowerHitter').checked : false,
            ai_predict_scoring: document.getElementById('aiPredictScoring') ? document.getElementById('aiPredictScoring').checked : false,
            ai_summarize_events: document.getElementById('aiSummarizeEvents') ? document.getElementById('aiSummarizeEvents').checked : false,
            ai_enhance_alerts: document.getElementById('aiEnhanceAlerts') ? document.getElementById('aiEnhanceAlerts').checked : false
        };
        
        // Save preferences to database instead of localStorage
        this.saveUserSettingsToDatabase();
        
        // If monitoring is active, update preferences immediately
        if (this.selectedGames.size > 0) {
            this.updateMonitoring();
        }
    }

    async saveUserSettingsToDatabase() {
        try {
            const response = await fetch('/api/user/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    notification_preferences: this.notificationPreferences,
                    monitored_games: Array.from(this.selectedGames)
                })
            });

            const data = await response.json();
            if (data.success) {
                console.log('✅ Settings saved to database');
            } else {
                console.error('Failed to save settings to database:', data.error);
            }
        } catch (error) {
            console.error('Error saving settings to database:', error);
        }
    }

    async stopMonitoring() {
        try {
            const response = await fetch('/api/monitor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    game_ids: [],
                    notification_preferences: this.notificationPreferences
                })
            });

            const data = await response.json();
            if (data.success) {
                this.selectedGames.clear();
                document.querySelectorAll('.game-item input[type="checkbox"]').forEach(cb => cb.checked = false);
                document.querySelectorAll('.game-item').forEach(el => el.classList.remove('selected'));
                document.getElementById('updateMonitoring').classList.remove('d-none');
                document.getElementById('stopMonitoring').classList.add('d-none');
                this.showToast('success', 'Monitoring stopped');
                this.updateStatus();
            }
        } catch (error) {
            console.error('Error stopping monitoring:', error);
            this.showToast('error', 'Failed to stop monitoring');
        }
    }

    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        localStorage.setItem('soundEnabled', this.soundEnabled);
        this.updateSoundIcon();
        this.showToast('success', `Sound alerts ${this.soundEnabled ? 'enabled' : 'disabled'}`);
    }

    updateSoundIcon() {
        const icon = document.getElementById('soundIcon');
        icon.className = this.soundEnabled ? 'fas fa-volume-up' : 'fas fa-volume-mute';
    }

    updateMonitoredCount() {
        // Update the game count display in the UI
        const count = this.selectedGames.size;
        const countEl = document.getElementById('monitoredGamesCount');
        if (countEl) {
            countEl.textContent = count;
        }
        
        // Update button text to show count
        const updateBtn = document.getElementById('updateMonitoring');
        if (updateBtn) {
            updateBtn.innerHTML = `<i class="fas fa-play me-2"></i>Start Monitoring (${count} games selected)`;
        }
        
        // Update status text
        const statusEl = document.getElementById('monitoringStatus');
        if (statusEl) {
            const gamesText = count === 1 ? '1 game' : `${count} games`;
            statusEl.innerHTML = `<span class="badge bg-info">${gamesText} selected</span>`;
        }
    }

    playAlertSound(alertType) {
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFjF9fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBzuS2Oy9diMFl2z1qDELoKPAV3hanu7DiVX35MFaEnLkt2fwq/BoAXzGzNbMCqDwU8D8y/z0/H7ExK7IRAfJx2/s+3cGfwYCC8q6qstTzPzO3czZySs');
            audio.volume = 0.5;
            audio.play().catch(e => console.log('Could not play sound:', e));
        } catch (e) {
            console.log('Audio not supported:', e);
        }
    }

    getNotificationSummary() {
        const enabled = [];
        if (this.notificationPreferences.runners) enabled.push('Runners');
        if (this.notificationPreferences.hits) enabled.push('Hits');
        if (this.notificationPreferences.scoring) enabled.push('Scoring');
        if (this.notificationPreferences.inning_change) enabled.push('Innings');
        if (this.notificationPreferences.home_runs) enabled.push('Home Runs');
        if (this.notificationPreferences.strikeouts) enabled.push('Strikeouts');
        
        return enabled.length > 0 ? enabled.join(', ') : 'None';
    }

    async loadPersistentSettings() {
        try {
            const response = await fetch('/api/settings/status');
            const data = await response.json();
            
            if (data.success) {
                const settings = data.settings;
                
                // Update persistent settings status display
                const statusEl = document.getElementById('persistentSettingsStatus');
                if (statusEl) {
                    const autoMonitoringText = settings.auto_monitoring_enabled ? 'Enabled' : 'Disabled';
                    const monitoringText = settings.monitoring_active ? 'Active' : 'Inactive';
                    
                    statusEl.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>Auto-restore monitoring:</span>
                            <span class="badge ${settings.auto_monitoring_enabled ? 'bg-success' : 'bg-secondary'}">${autoMonitoringText}</span>
                        </div>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>Monitoring status:</span>
                            <span class="badge ${settings.monitoring_active ? 'bg-success' : 'bg-secondary'}">${monitoringText}</span>
                        </div>
                        <div class="d-flex justify-content-between align-items-center">
                            <span>Games monitored:</span>
                            <span class="badge bg-info">${settings.monitored_games_count}</span>
                        </div>
                    `;
                }
                
                // Restore selected games in UI if they exist
                if (settings.monitored_games && settings.monitored_games.length > 0) {
                    this.selectedGames = new Set(settings.monitored_games);
                    this.restoreSelectedGames();
                }
                
                // Update button visibility based on current state
                if (settings.monitoring_active && settings.monitored_games_count > 0) {
                    document.getElementById('updateMonitoring').classList.add('d-none');
                    document.getElementById('stopMonitoring').classList.remove('d-none');
                } else {
                    document.getElementById('updateMonitoring').classList.remove('d-none');
                    document.getElementById('stopMonitoring').classList.add('d-none');
                }
            }
        } catch (error) {
            console.error('Error loading persistent settings:', error);
        }
    }

    restoreSelectedGames() {
        // Check boxes for previously selected games
        this.selectedGames.forEach(gameId => {
            const checkbox = document.getElementById(`game-${gameId}`);
            if (checkbox) {
                checkbox.checked = true;
                checkbox.closest('.game-item').classList.add('selected');
            }
        });
    }

    async toggleAutoMonitoring() {
        const button = document.getElementById('toggleAutoMonitoring');
        if (!button) return;
        
        const originalHTML = button.innerHTML;
        
        try {
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Updating...';
            button.disabled = true;
            
            // Get current state and toggle it
            const response = await fetch('/api/settings/status');
            const data = await response.json();
            const currentEnabled = data.success ? data.settings.auto_monitoring_enabled : true;
            
            const toggleResponse = await fetch('/api/settings/auto-monitoring', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    enabled: !currentEnabled
                })
            });
            
            const toggleData = await toggleResponse.json();
            
            if (toggleData.success) {
                this.showToast('success', toggleData.message);
                this.loadPersistentSettings();
            } else {
                this.showToast('error', toggleData.error || 'Failed to toggle auto-monitoring');
            }
        } catch (error) {
            console.error('Error toggling auto-monitoring:', error);
            this.showToast('error', 'Failed to toggle auto-monitoring');
        } finally {
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }

    async loadSuccessRateStats() {
        try {
            console.log('Loading success rate stats...');
            const response = await fetch('/api/alert-success-stats');
            console.log('Response status:', response.status);
            
            if (response.status === 401 || response.status === 302) {
                console.log('Not authenticated for success rate stats');
                return;
            }
            
            const data = await response.json();
            console.log('Success rate data:', data);
            
            if (data.success) {
                this.displaySuccessRateStats(data.stats);
                console.log('Success rate stats displayed');
            } else {
                console.error('Failed to load success rate stats:', data.error);
            }
        } catch (error) {
            console.error('Error loading success rate stats:', error);
        }
    }

    displaySuccessRateStats(stats) {
        console.log('Displaying success rate stats:', stats);
        
        // Update overall statistics
        const overallEl = document.getElementById('overallSuccessRate');
        const recentEl = document.getElementById('recentSuccessRate');
        const totalEl = document.getElementById('totalTrackedAlerts');
        
        if (overallEl) overallEl.textContent = stats.total_alerts > 0 ? `${stats.success_rate}%` : '-%';
        if (recentEl) recentEl.textContent = stats.recent_total > 0 ? `${stats.recent_success_rate}%` : '-%';
        if (totalEl) totalEl.textContent = stats.total_alerts;
        
        // Update alert type breakdown
        const breakdownEl = document.getElementById('alertTypeBreakdown');
        if (breakdownEl) {
            if (stats.alert_type_breakdown && stats.alert_type_breakdown.length > 0) {
                breakdownEl.innerHTML = stats.alert_type_breakdown.map(type => `
                    <div class="d-flex justify-content-between align-items-center mb-2 small">
                        <span class="text-capitalize">${type.type.replace(/_/g, ' ')}</span>
                        <div>
                            <span class="badge bg-${type.rate >= 70 ? 'success' : type.rate >= 50 ? 'warning' : 'secondary'} me-1">
                                ${type.rate}%
                            </span>
                            <span class="text-muted">(${type.successful}/${type.total})</span>
                        </div>
                    </div>
                `).join('');
            } else {
                breakdownEl.innerHTML = `
                    <div class="text-muted text-center py-2">
                        <i class="fas fa-chart-bar me-2"></i>
                        Start monitoring to track your alert performance
                    </div>
                `;
            }
        }
        console.log('Success rate display updated');
    }

    async trackAlertOutcome(alertData) {
        try {
            const response = await fetch('/api/track-alert-outcome', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(alertData)
            });

            const data = await response.json();
            if (data.success) {
                console.log('Alert outcome tracked:', data.outcome_id);
                return data.outcome_id;
            }
        } catch (error) {
            console.error('Error tracking alert outcome:', error);
        }
        return null;
    }

    async updateAlertOutcome(outcomeId, wasSuccessful, scoringDetails = {}) {
        try {
            const response = await fetch(`/api/update-alert-outcome/${outcomeId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    was_successful: wasSuccessful,
                    scoring_occurred: scoringDetails.scoring_occurred || false,
                    runs_scored: scoringDetails.runs_scored || 0
                })
            });

            const data = await response.json();
            if (data.success) {
                // Refresh success rate stats
                this.loadSuccessRateStats();
                console.log('Alert outcome updated:', wasSuccessful ? 'Success' : 'Failed');
            }
        } catch (error) {
            console.error('Error updating alert outcome:', error);
        }
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new MLBMonitor();
});
