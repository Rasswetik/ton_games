// ===== NOTIFICATION DRAWER (Top notification system) =====
function showNotification(message, type = 'info', iconSrc = null, duration = 3000) {
    // Helper: return SVG data URI icon for type (fallback when no PNG provided)
    function getDefaultIconDataURI(kind) {
        const icons = {
            success: `<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none'><circle cx='12' cy='12' r='10' fill='%2310B981'/><path d='M7 13l2.5 2.5L17 8' stroke='%23fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>`,
            error: `<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none'><circle cx='12' cy='12' r='10' fill='%23EF4444'/><path d='M15 9L9 15M9 9l6 6' stroke='%23fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>`,
            warning: `<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none'><circle cx='12' cy='12' r='10' fill='%23F59E0B'/><path d='M12 7v6' stroke='%23fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/><path d='M12 16h.01' stroke='%23fff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>`,
            info: `<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48' viewBox='0 0 24 24' fill='none'><circle cx='12' cy='12' r='10' fill='%233B82F6'/><path d='M11 11h2v4h-2z' fill='%23fff'/><path d='M12 8h.01' fill='%23fff'/></svg>`
        };
        const svg = icons[kind] || icons.info;
        return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
    }

    const container = document.getElementById('notification-drawer') || (() => {
        const div = document.createElement('div');
        div.id = 'notification-drawer';
        div.style.cssText = `
            position: fixed;
            top: 12px;
            left: 8px;
            right: 8px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            pointer-events: none;
            align-items: center;
        `;
        document.body.appendChild(div);
        return div;
    })();

    const notification = document.createElement('div');
    const bgColor = {
        'success': 'var(--notify-success, #10b981)',
        'error': 'var(--notify-error, #ef4444)',
        'warning': 'var(--notify-warning, #f59e0b)',
        'info': 'var(--notify-info, #3b82f6)'
    }[type] || 'var(--notify-info, #3b82f6)';

    notification.style.cssText = `
        background: ${bgColor};
        color: white;
        padding: 12px 16px;
        font-size: 14px;
        font-weight: 500;
        animation: slideDown 0.35s ease;
        box-shadow: 0 6px 18px rgba(0,0,0,0.12);
        pointer-events: auto;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 12px;
        border-radius: 10px;
        border: 1px solid rgba(0,0,0,0.06);
        margin: 6px 0;
        max-width: 980px;
        width: calc(100% - 16px);
    `;

    let html = '';

    // Determine icon: prefer provided PNG, otherwise use inline SVG data URI per type
    const finalIcon = iconSrc || getDefaultIconDataURI(type);
    if (finalIcon) {
        html += `<img src="${finalIcon}" style="width: 28px; height: 28px; object-fit: contain; flex-shrink: 0; border-radius:6px;">`;
    }

    // Add message (remove emojis and dingbats)
    const cleanMessage = String(message).replace(/[\u{1F300}-\u{1F9FF}\u{2700}-\u{27BF}\u{2600}-\u{26FF}\u{1F1E6}-\u{1F1FF}]/gu, '').replace(/\s+/g, ' ').trim();
    html += `<span style="line-height:1.2">${cleanMessage}</span>`;
    
    notification.innerHTML = html;
    notification.onclick = () => {
        notification.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    };

    container.appendChild(notification);

    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideUp 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }
}

// Backward compatibility: keep showToast function but use drawer
function showToast(message, type = 'info', iconSrc = null, duration = 3000) {
    showNotification(message, type, iconSrc, duration);
}

// Expose to window for templates to call directly
window.showToast = showToast;
window.showNotification = showNotification;

// Apply stored theme settings early so pages render with correct theme
function applyStoredTheme() {
    try {
        const raw = localStorage.getItem('rps_settings');
        if (!raw) return;
        const s = JSON.parse(raw);
        if (s && s.theme === 'dark') {
            document.body.classList.add('dark-theme');
            try { document.documentElement.setAttribute('data-theme', 'dark'); } catch(e) {}
        } else {
            document.body.classList.remove('dark-theme');
            try { document.documentElement.removeAttribute('data-theme'); } catch(e) {}
        }
    } catch (e) {
        console.error('[THEME] applyStoredTheme error', e);
    }
}

// Apply immediately (runs as soon as this script is parsed)
applyStoredTheme();

// If settings change in another tab, pick it up (theme + language)
window.addEventListener('storage', (e) => {
    if (e.key !== 'rps_settings') return;
    try {
        const raw = e.newValue;
        if (!raw) return;
        const s = JSON.parse(raw);
        if (s && s.theme) applyStoredTheme();
        if (s && s.lang && typeof applyLanguage === 'function') applyLanguage(s.lang);
    } catch (err) {
        console.error('[STORAGE] error parsing rps_settings', err);
    }
});

/* ------------------------- TRANSLATIONS & VIBRATION ------------------------- */
const TRANSLATIONS = {
    en: {
        title_profile: 'Profile',
        title_market: 'Market',
        title_inventory: 'Inventory',
        connect_wallet: 'Connect Wallet',
        settings_title: 'Settings',
        theme: 'Theme',
        language: 'Language',
        vibration: 'Vibration',
        promo_code: 'Promo Code',
        promo_use: 'Use',
        referral_link: 'Referral Link',
        referrals: 'Referrals',
        earnings: 'Earnings',
        copy: 'Copy',
        balance_label: 'Balance',
        title_crafts: 'Crafts',
        crafting_title: 'Crafting',
        crafting_desc: 'Combine 3-10 items to create a new gift',
        your_inventory: 'Your Inventory',
        search_inventory_placeholder: 'Search inventory...',
        promo_field_placeholder: 'Enter code',
        craft_button: 'CRAFT',
        empty_inventory: 'No items',
        loading_gifts: 'Loading gifts...',
        gift: 'Gift',
        buy: 'Buy',
        checking: 'Checking...',
        gifts_unavailable: 'Gifts unavailable',
        gift_description: 'Exclusive gift',
        processing: 'Processing...',
        save: 'Save',
        promo_saved: 'Code saved',
        promo_applied_success: 'Promo code applied',
        copy_success: 'Copied to clipboard',
        copy_failed: 'Copy failed',
        win_title: 'Congratulations!',
        sell: 'Sell',
        continue: 'Continue',
        selected_items_summary: 'Selected: {count} items (3-10 required)',
        selected_items_reward: 'Selected: {count} items | Reward: {min} - {max} TON',
        pending_withdrawal: 'Pending withdrawal'
        ,withdraw: 'Withdraw'
        ,bet_title: 'Enter Bet'
        ,bet_desc: 'Enter amount in TON'
        ,rock: 'Rock'
        ,scissors: 'Scissors'
        ,paper: 'Paper'
        ,refresh: 'Refresh'
        ,stake: 'Stake'
        ,all_stakes: 'All Stakes'
        ,players: 'Players'
        ,all_count: 'All Count'
        ,rounds: 'Rounds'
        ,all_rounds: 'All Rounds'
        ,active_games: 'Active Games'
        ,create_game: 'Create Game'
        ,loading_games: 'Loading games...'
        ,no_games: 'No active games available. Create one to start playing!'
        ,join_game: 'Join Game'
        ,no_games_filter: 'No games match your filters'
        ,create_new_game: 'Create New Game'
        ,game_created: 'Game created successfully'
        ,error_creating_game: 'Error creating game'
        ,error_joining_game: 'Error joining game'
        ,join_success: 'Game joined successfully'
        ,enter_bid: 'Enter bid'
        ,cancel: 'Cancel'
        ,create: 'Create'
        ,waiting: 'Waiting'
    },
    ru: {
        title_profile: 'Профиль',
        title_market: 'Маркет',
        title_inventory: 'Инвентарь',
        connect_wallet: 'Подключить кошелёк',
        settings_title: 'Настройки',
        theme: 'Тема',
        language: 'Язык',
        vibration: 'Вибрация',
        promo_code: 'Промокод',
        promo_use: 'Применить',
        referral_link: 'Реферальная ссылка',
        referrals: 'Рефералы',
        earnings: 'Заработок',
        copy: 'Копировать',
        balance_label: 'Баланс',
        title_crafts: 'Крафт',
        crafting_title: 'Крафт',
        crafting_desc: 'Комбинируйте 3–10 предметов, чтобы создать новый подарок',
        your_inventory: 'Ваш инвентарь',
        search_inventory_placeholder: 'Поиск по инвентарю...',
        promo_field_placeholder: 'Введите код',
        craft_button: 'СОЗДАТЬ',
        empty_inventory: 'Инвентарь пуст',
        loading_gifts: 'Загрузка подарков...',
        gift: 'Подарок',
        buy: 'Купить',
        checking: 'Проверка...',
        gifts_unavailable: 'Подарки недоступны',
        gift_description: 'Эксклюзивный подарок',
        processing: 'Выполняется...',
        save: 'Сохранить',
        promo_saved: 'Код сохранён',
        promo_applied_success: 'Промокод применён',
        copy_success: 'Скопировано в буфер',
        copy_failed: 'Ошибка копирования',
        win_title: 'Поздравляем!',
        sell: 'Продать',
        continue: 'Продолжить',
        selected_items_summary: 'Выбрано: {count} предметов (3-10 треб.)',
        selected_items_reward: 'Выбрано: {count} предметов | Награда: {min} - {max} TON',
        pending_withdrawal: 'В ожидании'
        ,withdraw: 'Вывести'
        ,bet_title: 'Введите ставку'
        ,bet_desc: 'Введите сумму в TON'
        ,rock: 'Камень'
        ,scissors: 'Ножницы'
        ,paper: 'Бумага'
        ,refresh: 'Обновить'
        ,stake: 'Ставка'
        ,all_stakes: 'Все ставки'
        ,players: 'Игроки'
        ,all_count: 'Все'
        ,rounds: 'Раунды'
        ,all_rounds: 'Все раунды'
        ,active_games: 'Активные игры'
        ,create_game: 'Создать игру'
        ,loading_games: 'Загрузка игр...'
        ,no_games: 'Нет активных игр. Создайте одну, чтобы начать играть!'
        ,join_game: 'Присоединиться'
        ,no_games_filter: 'Нет игр, соответствующих фильтрам'
        ,create_new_game: 'Создать новую игру'
        ,game_created: 'Игра создана успешно'
        ,error_creating_game: 'Ошибка при создании игры'
        ,error_joining_game: 'Ошибка при присоединении к игре'
        ,join_success: 'Вы присоединились к игре'
        ,enter_bid: 'Введите ставку'
        ,cancel: 'Отмена'
        ,create: 'Создать'
        ,waiting: 'Ожидание'
    }
};

function translateTemplate(str, vars) {
    if (!str) return '';
    return str.replace(/\{(\w+)\}/g, (_, k) => (vars && vars[k] !== undefined ? vars[k] : ''));
}

function t(key) {
    const lang = (getSettingsFromStorage() || {}).lang || 'en';
    const map = TRANSLATIONS[lang] || TRANSLATIONS['en'];
    return map[key] || key;
}

function getSettingsFromStorage() {
    try { return JSON.parse(localStorage.getItem('rps_settings') || '{}'); } catch(e) { return {}; }
}

function applyLanguage(lang) {
    try {
        const map = TRANSLATIONS[lang] || TRANSLATIONS['en'];
        document.documentElement.lang = lang;
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (!key) return;
            const text = map[key] || key;
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') el.placeholder = text;
            else el.textContent = text;
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (!key) return;
            const text = map[key] || key;
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') el.placeholder = text;
        });
    } catch (e) { console.error('[LANG] applyLanguage error', e); }
}

function t(key, vars) {
    const s = getSettingsFromStorage();
    const lang = s.lang || 'ru';
    const map = TRANSLATIONS[lang] || TRANSLATIONS['en'];
    const str = map[key] || (TRANSLATIONS['en'][key] || key);
    return translateTemplate(str, vars || {});
}

// Apply stored language immediately
(function applyStoredLanguage() {
    try {
        const s = getSettingsFromStorage();
        const lang = s.lang || 'ru';
        applyLanguage(lang);
    } catch (e) { console.error('[LANG] applyStoredLanguage error', e); }
})();

// Global vibration handler: vibrate on important interactions when enabled
document.addEventListener('click', (ev) => {
    try {
        const el = ev.target.closest('button, a, .btn-action, .nav-item, .gift-card, .inventory-item, .craft-slot, .btn-craft');
        if (!el) return;
        const s = getSettingsFromStorage();
        if (s.vibration && navigator.vibrate) navigator.vibrate(12);
    } catch (e) { /* ignore */ }
});

// expose t/applyLanguage globally
window.t = t;
window.applyLanguage = applyLanguage;

// Promise-based confirm modal (non-blocking)
function showConfirm(message, options = {}) {
    return new Promise(resolve => {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 11000;
        `;

        const box = document.createElement('div');
        box.style.cssText = `
            background: var(--card);
            color: var(--text);
            padding: 18px;
            border-radius: 10px;
            max-width: 92%;
            width: 420px;
            box-shadow: var(--shadow);
            font-family: sans-serif;
        `;

        const msg = document.createElement('div');
        msg.style.cssText = 'margin-bottom:12px; font-size:15px; line-height:1.3;';
        msg.textContent = String(message);

        const btnRow = document.createElement('div');
        btnRow.style.cssText = 'display:flex; gap:10px; justify-content:flex-end;';

        const cancelBtn = document.createElement('button');
        cancelBtn.textContent = options.cancelText || 'Cancel';
        cancelBtn.style.cssText = 'padding:8px 12px; background:var(--card); color:var(--text); border-radius:8px; border:0; cursor:pointer;';

        const okBtn = document.createElement('button');
        okBtn.textContent = options.okText || 'Yes';
        okBtn.style.cssText = 'padding:8px 12px; background:var(--primary); color:white; border-radius:8px; border:0; cursor:pointer;';

        btnRow.appendChild(cancelBtn);
        btnRow.appendChild(okBtn);
        box.appendChild(msg);
        box.appendChild(btnRow);
        overlay.appendChild(box);
        document.body.appendChild(overlay);

        function cleanup(result) {
            try { overlay.remove(); } catch (e) {}
            resolve(result);
        }

        cancelBtn.addEventListener('click', () => cleanup(false));
        okBtn.addEventListener('click', () => cleanup(true));

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay && options.dismissOnOverlay !== false) cleanup(false);
        });
    });
}

window.showConfirm = showConfirm;

// Add CSS animations
if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        @keyframes slideDown {
            from { transform: translateY(-100%); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        @keyframes slideUp {
            from { transform: translateY(0); opacity: 1; }
            to { transform: translateY(-100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}

// Override alert() to use toast notifications
const originalAlert = window.alert;
    window.alert = function(message) {
    if (!message) return;

    // Auto-detect type from message content
    let type = 'info';
    const msg = String(message).toUpperCase();
    if (msg.includes('SUCCESS') || msg.includes('✅')) type = 'success';
    else if (msg.includes('ERROR') || msg.includes('❌')) type = 'error';
    else if (msg.includes('WARNING') || msg.includes('⚠️')) type = 'warning';

    showToast(String(message), type, null, 3000);
};

// ===== TELEGRAM INITIALIZATION =====
let tg;
let currentUserId = null;

function initTelegram() {
    if (typeof window.Telegram === 'undefined' || !window.Telegram.WebApp) {
        console.warn('[WARN] Telegram WebApp not available');
        return null;
    }
    
    tg = window.Telegram.WebApp;
    try {
        tg.expand();
        tg.ready();
        console.log('[OK] Telegram initialized');
        return tg;
    } catch (e) {
        console.error('[ERROR] Telegram init error:', e);
        return null;
    }
}

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTelegram);
} else {
    initTelegram();
}

window.addEventListener('load', initTelegram);

// ===== TON CONNECT INITIALIZATION =====
let tonConnectUI = null;
let tonConnectInitialized = false;
// Promise for concurrent init attempts
let tonConnectInitPromise = null;

// Dynamic script loader with timeout
function loadScript(src, timeoutMs = 8000) {
    return new Promise((resolve, reject) => {
        if (typeof TonConnectUI !== 'undefined') return resolve();
        if (!src) return reject(new Error('No src provided'));
        const script = document.createElement('script');
        let done = false;
        const timer = setTimeout(() => {
            if (done) return;
            done = true;
            try { script.remove(); } catch (e) {}
            reject(new Error('Script load timeout: ' + src));
        }, timeoutMs);

        script.onload = () => {
            if (done) return;
            done = true;
            clearTimeout(timer);
            resolve();
        };
        script.onerror = (e) => {
            if (done) return;
            done = true;
            clearTimeout(timer);
            try { script.remove(); } catch (err) {}
            reject(new Error('Failed to load script: ' + src));
        };

        script.src = src;
        script.async = true;
        document.head.appendChild(script);
    });
}

async function waitForTonConnect(timeoutMs = 3000) {
    const startTime = Date.now();
    while (typeof TonConnectUI === 'undefined') {
        if (Date.now() - startTime > timeoutMs) {
            throw new Error('TonConnect library timeout');
        }
        await new Promise(resolve => setTimeout(resolve, 50));
    }
    return TonConnectUI;
}

async function initTONConnect(forceReload = false) {
    try {
        if (forceReload) {
            // allow fresh re-init
            tonConnectInitPromise = null;
            tonConnectInitialized = false;
            tonConnectUI = null;
            if (window.tonConnectUI) try { delete window.tonConnectUI; } catch(e) {}
        }

        // Return existing initialized instance
        if (tonConnectUI && tonConnectInitialized) {
            console.log('[INIT] TonConnect already initialized, returning existing');
            return tonConnectUI;
        }

        // If init in progress, reuse promise
        if (tonConnectInitPromise) {
            console.log('[INIT] Initialization already in progress, awaiting');
            return tonConnectInitPromise;
        }

        tonConnectInitPromise = (async () => {
            // If window already provided an instance, use it
            if (window.tonConnectUI) {
                tonConnectUI = window.tonConnectUI;
                tonConnectInitialized = true;
                console.log('[INIT] Using existing window.tonConnectUI');
                return tonConnectUI;
            }

            console.log('[INIT] Starting TonConnect initialization...');

            // Try waiting briefly for already-loaded library
            let initialWait = forceReload ? 10000 : 5000;
            try {
                await waitForTonConnect(initialWait);
                console.log('[INIT] TonConnectUI detected on window');
            } catch (e) {
                console.warn('[INIT] TonConnectUI not found, attempting to load scripts:', e && e.message ? e.message : e);
                // Try multiple sources sequentially
                const sources = [
                    'https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js',
                    'https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.min.js',
                    '/static/vendor/tonconnect-ui.min.js'
                ];
                let loaded = false;
                for (const src of sources) {
                    try {
                        console.log('[INIT] Loading script:', src);
                        await loadScript(src, 8000);
                        // small pause for the script to register globals
                        await new Promise(r => setTimeout(r, 400));
                        if (typeof TonConnectUI !== 'undefined') {
                            loaded = true;
                            break;
                        }
                    } catch (err) {
                        console.warn('[INIT] loadScript failed for', src, err && err.message ? err.message : err);
                    }
                }

                if (!loaded && typeof TonConnectUI === 'undefined') {
                    showToast('TON Connect library failed to load. Please check your connection or place a local copy at /static/vendor/tonconnect-ui.min.js', 'error', null, 10000);
                    tonConnectInitPromise = null;
                    return null;
                }
            }

            // At this point TonConnectUI should be available
                if (typeof TonConnectUI === 'undefined') {
                    showToast('TON Connect library not available after loading', 'error', null, 8000);
                    tonConnectInitPromise = null;
                    return null;
                }

            try {
                const manifestUrl = window.location.protocol + '//' + window.location.host + '/tonconnect-manifest.json';
                console.log('[INIT] Using manifest URL:', manifestUrl);
                const Constructor = window.TonConnectUI || (window.TON_CONNECT_UI && window.TON_CONNECT_UI.TonConnectUI);
                if (!Constructor) {
                    showToast('TonConnect UI constructor not found on window', 'error', null, 5000);
                    tonConnectInitPromise = null;
                    return null;
                }

                const options = { manifestUrl: manifestUrl };
                // If page contains a mount point for the TonConnect button, pass it to the UI
                if (document.getElementById('ton-connect-button')) options.buttonRootId = 'ton-connect-button';

                const instance = new Constructor(options);
                window.tonConnectUI = instance;
                tonConnectUI = instance;
                tonConnectInitialized = true;
                console.log('[INIT] ✓ TonConnect initialized');
                return tonConnectUI;
            } catch (initError) {
                console.error('[INIT] Failed to create instance:', initError && initError.message ? initError.message : initError);
                showToast('Failed to initialize TON Connect: ' + (initError && initError.message ? initError.message : String(initError)), 'error', null, 5000);
                tonConnectInitPromise = null;
                return null;
            }
        })();

        return await tonConnectInitPromise;
    } catch (e) {
        console.error('[INIT] Exception:', e && e.message ? e.message : e);
        showToast('TON Connect error: ' + (e && e.message ? e.message : String(e)), 'error', null, 5000);
        tonConnectInitPromise = null;
        return null;
    }
}

// Auto-initialize on DOM ready with retry
async function autoInitTonConnect() {
    // Wait for window.load to ensure all scripts are loaded
    if (document.readyState === 'loading') {
        // Still loading, wait
        await new Promise(resolve => {
            window.addEventListener('load', resolve, { once: true });
        });
    }
    
    console.log('[AUTO] Window fully loaded, initializing TonConnect...');
    
    // Small additional delay to ensure @tonconnect/ui is fully ready
    await new Promise(resolve => setTimeout(resolve, 300));
    
    if (!tonConnectInitialized && typeof TonConnectUI !== 'undefined') {
        await initTONConnect();
    }
}

// Start auto-init on DOM content loaded
if (document.readyState !== 'loading') {
    autoInitTonConnect();
} else {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(autoInitTonConnect, 100);
    });
}

// Also ensure it's initialized on window load
window.addEventListener('load', () => {
    if (!tonConnectInitialized) {
        console.log('[RETRY] TonConnect not yet initialized on window load, retrying...');
        initTONConnect();
    }
});

// Helper: Open TonConnect wallet picker / connect modal
async function openTonConnectModal(forceReload = false) {
    try {
        // Ensure UI library/instance is initialized
        const instance = await initTONConnect(forceReload);
        if (!instance && typeof TonConnectUI === 'undefined') {
            showToast('TON Connect UI is not available', 'error', null, 4000);
            return null;
        }

        const uiInstance = instance || window.tonConnectUI || tonConnectUI;
        if (!uiInstance) {
            showToast('TON Connect instance not found', 'error', null, 4000);
            return null;
        }

        const candidates = ['connectWallet', 'connect', 'requestWallet', 'connectToWallet', 'open'];
        for (const name of candidates) {
            try {
                const fn = uiInstance[name];
                if (typeof fn === 'function') {
                    console.log('[TON UI] calling', name);
                    const res = await fn.call(uiInstance);
                    // If method returned data or instance has wallet, return it
                    if (res || uiInstance.wallet) {
                        tonConnectUI = uiInstance;
                        tonConnectInitialized = true;
                        window.tonConnectUI = uiInstance;
                        // update balance if connected
                        try { if (typeof loadBalance === 'function') setTimeout(loadBalance, 500); } catch(e) {}
                        return res || uiInstance.wallet || res;
                    }
                }
            } catch (e) {
                console.warn('[TON UI] method', name, 'failed', e);
            }
        }

        if (uiInstance.wallet) {
            return uiInstance.wallet;
        }

        // Last attempt: call open() if available
        if (typeof uiInstance.open === 'function') {
            try {
                await uiInstance.open();
                return uiInstance.wallet || null;
            } catch (e) { console.warn('[TON UI] open() failed', e); }
        }

        showToast('Не удалось открыть окно TON Connect', 'error');
        return null;
    } catch (e) {
        console.error('[TON UI] openTonConnectModal error', e);
        showToast('TON Connect error: ' + (e && e.message ? e.message : String(e)), 'error');
        return null;
    }
}

// ===== API FUNCTIONS =====
let pendingWithdrawalGifts = [];
let pendingWithdrawalRequests = [];
let pendingByIndex = new Set();
let pendingByGiftId = new Set();

async function loadPendingWithdrawals() {
    if (!currentUserId) {
        console.warn('[WARN] currentUserId not set');
        return;
    }
    try {
        const timestamp = new Date().getTime();
        const response = await fetch(`/api/user/pending-withdrawals?user_id=${currentUserId}&t=${timestamp}`);
        const data = await response.json();
        if (data.status === 'ok') {
            pendingWithdrawalRequests = data.pending_requests || [];
            pendingWithdrawalGifts = (data.pending_gift_ids || pendingWithdrawalRequests.map(r => r.gift_id)).map(id => String(id));

            // Build lookup sets
            pendingByIndex = new Set();
            pendingByGiftId = new Set();
            pendingWithdrawalRequests.forEach(r => {
                if (r.inventory_index !== null && r.inventory_index !== undefined) pendingByIndex.add(String(r.inventory_index));
                if (r.gift_id) pendingByGiftId.add(String(r.gift_id));
            });

            // Fallback: if only gift ids provided, populate pendingByGiftId
            if (pendingByGiftId.size === 0 && Array.isArray(data.pending_gift_ids)) {
                data.pending_gift_ids.forEach(id => pendingByGiftId.add(String(id)));
            }

            console.log('[OK] Loaded pending withdrawals:', { pendingWithdrawalRequests, pendingWithdrawalGifts });
        }
    } catch (e) {
        console.error('[ERROR] loadPendingWithdrawals:', e);
    }
}

async function loadBalance() {
    if (!currentUserId) {
        console.warn('[WARN] currentUserId not set');
        return;
    }
    try {
        const timestamp = new Date().getTime();
        const response = await fetch(`/api/user/get?user_id=${currentUserId}&t=${timestamp}`);
        const data = await response.json();
        if (data.status === 'ok') {
            const balanceEl = document.getElementById('header-balance');
            if (balanceEl) {
                balanceEl.textContent = (data.balance || 0).toFixed(2) + ' TON';
            }
        }
    } catch (e) {
        console.error('[ERROR] loadBalance:', e);
    }
}

async function connectWallet() {
    // New robust connect -> send flow: attempts multiple connect/send API methods and falls back to deep-link
    try {
        console.log('[CONNECT] Wallet connection requested');

        if (!tonConnectUI || !tonConnectInitialized) {
            console.log('[CONNECT] TonConnect not ready, initializing with extended timeout...');
            const result = await initTONConnect(true);
            if (!result) {
                console.warn('[CONNECT] TonConnect did not initialize; will try deep-link fallback');
                showToast('TON Connect not loaded; falling back to direct transfer (deep-link)', 'warning', null, 8000);
            }
        }

        const libraryAvailable = (!!tonConnectUI && !!tonConnectInitialized) || (typeof TonConnectUI !== 'undefined');

        // Helper: try several possible connect method names
        async function tonConnectConnect(instance) {
            const candidates = ['connectWallet', 'connect', 'requestWallet', 'connectToWallet', 'open'];
            let lastErr = null;
            for (const name of candidates) {
                try {
                    const fn = instance && instance[name];
                    if (typeof fn === 'function') {
                        console.log('[CONNECT] Trying method', name);
                        const res = await fn.call(instance);
                        return res || instance.wallet || res;
                    }
                } catch (e) {
                    lastErr = e;
                }
            }
            if (instance && instance.wallet) return instance.wallet;
            throw lastErr || new Error('No connect method available on TonConnectUI');
        }

        // Helper: try several send methods and fallback to deep-link if none available
        async function tonConnectSendTransaction(instance, transaction) {
            const sendCandidates = ['sendTransaction', 'send', 'requestTransfer', 'requestTransaction', 'request'];
            let lastErr = null;
            for (const name of sendCandidates) {
                try {
                    const fn = instance && instance[name];
                    if (typeof fn === 'function') {
                        console.log('[SEND] Trying send method', name);
                        return await fn.call(instance, transaction);
                    }
                } catch (e) {
                    lastErr = e;
                }
            }

            // Try nested wallet methods
            if (instance && instance.wallet) {
                for (const name of sendCandidates) {
                    try {
                        const fn = instance.wallet[name];
                        if (typeof fn === 'function') {
                            console.log('[SEND] Trying wallet.' + name);
                            return await fn.call(instance.wallet, transaction);
                        }
                    } catch (e) { lastErr = e; }
                }
            }

            // Fallback: open deep transfer URI (may trigger wallet apps)
            try {
                const msg = transaction.messages && transaction.messages[0];
                if (msg && msg.address && msg.amount) {
                    const tonAmount = (Number(msg.amount) / 1e9);
                    const uri = `ton://transfer/${msg.address}?amount=${encodeURIComponent(String(tonAmount))}`;
                    console.warn('[SEND] No programmatic send available, redirecting to deep-link:', uri);
                    window.location.href = uri;
                    return { fallback: 'deep-link', uri };
                }
            } catch (e) { /* ignore */ }

            throw lastErr || new Error('No send method available on TonConnectUI');
        }

        if (libraryAvailable) {
            console.log('[CONNECT] Attempting wallet connect...');
            try {
                await tonConnectConnect(tonConnectUI);
            } catch (e) {
                console.error('[CONNECT] Connect failed:', e);
                showToast('Wallet connect failed: ' + (e.message || e), 'error');
                // fall through to deep-link fallback below
            }
        } else {
            console.log('[CONNECT] Library not available, skipping programmatic connect');
        }

        // Fetch receiver address from server (fallback to hard-coded)
        let receiver = 'UQDw7-rC3VhNeN5VUjV_Kz5TVBJ5pX4EEI_OOSdU8J0oQkOh';
        try {
            const r = await fetch('/api/ton/wallet-address');
            const jd = await r.json();
            if (jd && jd.receiver_address) receiver = jd.receiver_address;
        } catch (e) { console.warn('[CONNECT] Could not fetch receiver address, using default'); }

        // Prompt for amount
        const amountStr = prompt('Enter TON amount to send:', '0.1');
        if (!amountStr) return;
        const amount = parseFloat(amountStr);
        if (isNaN(amount) || amount <= 0) { showToast('Invalid amount', 'error'); return; }

        const nanotonAmount = Math.floor(amount * 1e9).toString();

        const transaction = {
            validUntil: Math.floor(Date.now() / 1000) + 300,
            messages: [{ address: receiver, amount: nanotonAmount }]
        };

        if (libraryAvailable) {
            try {
                const res = await tonConnectSendTransaction(tonConnectUI, transaction);
                console.log('[CONNECT] Transaction result:', res);
                showToast('Successfully sent ' + amount + ' TON', 'success');
                await loadBalance();
                return;
            } catch (e) {
                console.error('[CONNECT] Transaction failed via TonConnect:', e);
                showToast('Programmatic transaction failed, attempting deep-link fallback', 'warning', null, 8000);
            }
        }

        // Deep-link fallback (works on mobile wallets / wallet apps)
        try {
            const tonAmount = (Number(nanotonAmount) / 1e9);
            const uri = `ton://transfer/${receiver}?amount=${encodeURIComponent(String(tonAmount))}`;
            console.warn('[CONNECT] Redirecting to deep-link:', uri);
            showToast('Opening wallet app for transfer (deep-link)...', 'info', null, 4000);
            window.location.href = uri;
        } catch (e) {
            console.error('[CONNECT] Deep-link fallback failed:', e);
            showToast('Unable to send transaction: ' + (e.message || e), 'error');
        }

    } catch (error) {
        console.error('[CONNECT] Error:', error);
        showToast('Error: ' + (error.message || 'Unknown error'), 'error');
    }
}

// Global send helper: try multiple send methods on the TonConnect instance, then fallback to deep-link
async function sendTonTransaction(instance, transaction) {
    const sendCandidates = ['sendTransaction', 'send', 'requestTransfer', 'requestTransaction', 'request'];
    let lastErr = null;

    for (const name of sendCandidates) {
        try {
            const fn = (instance && instance[name]) || (instance && instance.connector && instance.connector[name]);
            if (typeof fn === 'function') {
                console.log('[SEND] Trying send method', name);
                return await fn.call(instance, transaction);
            }
        } catch (e) { lastErr = e; }
    }

    // Try nested wallet methods
    if (instance && instance.wallet) {
        for (const name of sendCandidates) {
            try {
                const fn = instance.wallet[name];
                if (typeof fn === 'function') {
                    console.log('[SEND] Trying wallet.' + name);
                    return await fn.call(instance.wallet, transaction);
                }
            } catch (e) { lastErr = e; }
        }
    }

    // Deep-link fallback
    try {
        const msg = transaction.messages && transaction.messages[0];
        if (msg && msg.address && msg.amount) {
            const tonAmount = (Number(msg.amount) / 1e9);
            const uri = `ton://transfer/${msg.address}?amount=${encodeURIComponent(String(tonAmount))}`;
            console.warn('[SEND] No programmatic send available, redirecting to deep-link:', uri);
            window.location.href = uri;
            return { fallback: 'deep-link', uri };
        }
    } catch (e) { /* ignore */ }

    throw lastErr || new Error('No send method available on TonConnectUI');
}

// Top-up flow: open wallet picker immediately, then prompt for amount and send transaction
async function topUpWithTon() {
    console.log('[TOPUP] Top up clicked');
    const instance = await initTONConnect(true);
    if (!instance) {
        showToast('TON Connect failed to initialize', 'error', null, 4000);
        return;
    }

    try {
        if (typeof instance.open === 'function') {
            console.log('[TOPUP] opening wallet picker via instance.open()');
            await instance.open();
        } else if (typeof instance.openWalletsModal === 'function') {
            await instance.openWalletsModal();
        } else {
            // fallback to generic modal/connect
            await openTonConnectModal(true);
        }
    } catch (e) {
        console.warn('[TOPUP] Error opening wallet picker', e);
    }

    // Prompt for amount after wallet picker
    const amountStr = prompt('Enter TON amount to send:', '0.1');
    if (!amountStr) return;
    const amount = parseFloat(amountStr);
    if (isNaN(amount) || amount <= 0) { showToast('Invalid amount', 'error'); return; }

    // Get receiver address
    let receiver = 'UQDw7-rC3VhNeN5VUjV_Kz5TVBJ5pX4EEI_OOSdU8J0oQkOh';
    try {
        const r = await fetch('/api/ton/wallet-address');
        const jd = await r.json();
        if (jd && jd.receiver_address) receiver = jd.receiver_address;
    } catch (e) { console.warn('[TOPUP] Could not fetch receiver address, using default'); }

    const nanotonAmount = Math.floor(amount * 1e9).toString();
    const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 300,
        messages: [{ address: receiver, amount: nanotonAmount }]
    };

    try {
        const res = await sendTonTransaction(instance, transaction);
        console.log('[TOPUP] Transaction result:', res);
        showToast('Successfully sent ' + amount + ' TON', 'success', null, 4000);
        await loadBalance();
        return;
    } catch (e) {
        console.error('[TOPUP] Transaction failed via TonConnect:', e);
        showToast('Programmatic transaction failed, attempting deep-link fallback', 'warning', null, 8000);
    }
}

// ===== PAGE INITIALIZATION =====
async function initIndexPage() {
    console.log('[INDEX] Starting initialization...');
    
    initTelegram();
    
    const tgUser = tg?.initDataUnsafe?.user;
    console.log('[INDEX] tgUser:', tgUser);
    
    if (tgUser?.id) {
        currentUserId = tgUser.id;
        const userName = tgUser.first_name + (tgUser.last_name ? ' ' + tgUser.last_name : '');
        document.getElementById('header-username').textContent = userName;
        
        if (tgUser.photo_url) {
            document.getElementById('header-avatar-img').src = tgUser.photo_url;
            document.getElementById('header-avatar-img').style.display = 'block';
            document.getElementById('header-avatar-svg').style.display = 'none';
        }
        
        const adminIds = [5257227756, 7679909245];
        if (adminIds.includes(tgUser.id)) {
            const adminBtn = document.getElementById('admin-btn');
            if (adminBtn) adminBtn.style.display = 'block';
        }
    } else {
        currentUserId = 123;
        console.log('[INDEX] Using test user 123');
        document.getElementById('header-username').textContent = 'Test User';
    }
    
    await loadBalance();
    
    // Initialize TonConnect with proper waiting
    console.log('[INDEX] Initializing TonConnect...');
    await initTONConnect();
    
    // Setup refresh intervals
    setInterval(loadBalance, 5000);
    
    console.log('[INDEX] Initialization complete');
}

// Auto-initialize on index page when ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (window.location.pathname === '/' || window.location.pathname.includes('index')) {
            // Wait for window to fully load before initializing
            window.addEventListener('load', initIndexPage, { once: true });
        }
    });
} else {
    if (window.location.pathname === '/' || window.location.pathname.includes('index')) {
        window.addEventListener('load', initIndexPage, { once: true });
    }
}

// ===== TON Connect Configuration (Old API) =====
// Compatibility layer for old TON Connect API
let tonConnectUIConfig = null;

try {
    if (typeof TON_CONNECT_UI !== 'undefined') {
        tonConnectUIConfig = new TON_CONNECT_UI.TonConnectUI({
            manifestUrl: window.location.origin + '/tonconnect-manifest.json',
            buttonRootId: 'ton-connect-custom'
        });
        console.log('[OK] TON Connect UI (old API) initialized');
    }
} catch (e) {
    console.debug('[DEBUG] TON Connect (old API) not available:', e.message);
}

// ===== COMPATIBILITY FUNCTIONS =====
async function handleWalletConnect(wallet) {
    console.debug('[DEBUG] handleWalletConnect (old API)');
}

async function handleWalletDisconnect() {
    console.debug('[DEBUG] handleWalletDisconnect (old API)');
}

function showWalletInfo(address) {
    console.debug('[DEBUG] showWalletInfo (old API)');
}

function hideWalletInfo() {
    console.debug('[DEBUG] hideWalletInfo (old API)');
}

async function updateBalance() {
    console.debug('[DEBUG] updateBalance (old API)');
}

async function sendTONTransaction(recipientAddress, amount) {
    console.debug('[DEBUG] sendTONTransaction (old API)');
}

async function checkAdmin() {
    try {
        if (!currentUserId) return;
        
        const response = await fetch(`/api/user/data/${currentUserId}`);
        const data = await response.json();
        
        if (data.is_admin) {
            const adminBtn = document.getElementById('admin-btn');
            if (adminBtn) {
                adminBtn.style.display = 'flex';
                console.log('[OK] Admin button shown');
            }
        }
    } catch (e) {
        console.error('[ERROR] Admin check:', e);
    }
}

// Keep GameState for compatibility
if (typeof window.GameState === 'undefined') {
    window.GameState = {
        getDemoGifts() { return []; },
        getUser() { return { name: "Player", balance: 0, inventory: [], is_new: true }; },
        saveUser(data) {},
        initUI() {
            const path = window.location.pathname;
            document.querySelectorAll('.nav-item').forEach(link => {
                if (link.getAttribute('href') === path) link.classList.add('active');
            });
        }
    };
}