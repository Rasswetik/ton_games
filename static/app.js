const tg = window.Telegram.WebApp;
tg.expand();

// ===== TON Connect Configuration =====
let tonConnectUI;
let currentUserId = null;

// Инициализация TON Connect
try {
    tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
        manifestUrl: window.location.origin + '/tonconnect-manifest.json',
        buttonRootId: 'ton-connect-custom'
    });
    
    console.log('✅ TON Connect UI initialized');
} catch (e) {
    console.error('❌ TonConnect Error:', e);
}

// Обработчик подключения кошелька
if (tonConnectUI) {
    tonConnectUI.uiOptions = {
        uiPreferences: {
            theme: 'DARK'
        }
    };
    
    tonConnectUI.onStatusChange(async (wallet) => {
        if (wallet) {
            console.log('✅ Wallet connected:', wallet.account.address);
            await handleWalletConnect(wallet);
        } else {
            console.log('❌ Wallet disconnected');
            await handleWalletDisconnect();
        }
    });
}

// ===== TON Wallet Functions =====

async function initTONUser() {
    const tgUser = tg.initDataUnsafe?.user;
    currentUserId = tgUser?.id || 'guest_' + Math.random().toString(36).substr(2, 9);
    
    try {
        const response = await fetch('/api/ton/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUserId })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ User session initialized:', data);
            return data;
        }
    } catch (e) {
        console.error('❌ Failed to init user:', e);
    }
}

async function handleWalletConnect(wallet) {
    if (!currentUserId) await initTONUser();
    
    const address = wallet.account.address;
    
    try {
        const response = await fetch('/api/ton/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                user_id: currentUserId,
                address: address
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Wallet connected:', data);
            
            // Обновляем UI
            showWalletInfo(address);
            updateBalance();
        }
    } catch (e) {
        console.error('❌ Wallet connect error:', e);
    }
}

async function handleWalletDisconnect() {
    if (!currentUserId) return;
    
    try {
        await fetch('/api/ton/disconnect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUserId })
        });
        
        console.log('✅ Wallet disconnected');
        hideWalletInfo();
    } catch (e) {
        console.error('❌ Wallet disconnect error:', e);
    }
}

function showWalletInfo(address) {
    const walletBlock = document.getElementById('wallet-info-block');
    const connectBlock = document.getElementById('ton-connect-custom');
    
    if (walletBlock) {
        walletBlock.style.display = 'flex';
        const shortAddress = address.slice(0, 10) + '...' + address.slice(-10);
        walletBlock.innerHTML = `
            <div class="balance-badge">
                <svg class="ton-svg-icon" viewBox="0 0 56 56" fill="none">
                    <path d="M28 56C43.464 56 56 43.464 56 28C56 12.536 43.464 0 28 0C12.536 0 0 12.536 0 28C0 43.464 12.536 56 28 56Z" fill="#0088CC"/>
                    <path d="M13.13 15.31H42.87L28 42.13L13.13 15.31ZM25.35 18.74V34.5L16.48 18.74H25.35ZM30.65 34.5V18.74H39.52L30.65 34.5Z" fill="white"/>
                </svg>
                <span id="user-balance" class="balance-display">0.0</span>
            </div>
            <span class="wallet-address" title="${address}">${shortAddress}</span>
        `;
    }
}

function hideWalletInfo() {
    const walletBlock = document.getElementById('wallet-info-block');
    if (walletBlock) {
        walletBlock.style.display = 'none';
    }
}

async function updateBalance() {
    if (!currentUserId) return;
    
    try {
        const response = await fetch(`/api/ton/balance/${currentUserId}`);
        if (response.ok) {
            const data = await response.json();
            const balanceEl = document.getElementById('user-balance');
            if (balanceEl) {
                balanceEl.textContent = data.balance.toFixed(2);
            }
        }
    } catch (e) {
        console.error('❌ Failed to update balance:', e);
    }
}

async function sendTONTransaction(recipientAddress, amount) {
    if (!currentUserId || !tonConnectUI?.wallet) {
        alert('❌ Кошелек не подключен');
        return;
    }
    
    try {
        const transaction = {
            validUntil: Math.floor(Date.now() / 1000) + 600,
            messages: [
                {
                    address: recipientAddress,
                    amount: (amount * 1e9).toString(),
                    payload: null
                }
            ]
        };
        
        const result = await tonConnectUI.sendTransaction(transaction);
        console.log('✅ Transaction sent:', result);
        
        return result;
    } catch (e) {
        console.error('❌ Transaction error:', e);
        alert('❌ Ошибка при отправке транзакции');
        throw e;
    }
}

window.GameState = {
    // Тот самый список подарков из твоего gifts.json (вставлен сюда)
    getDemoGifts() {
        return [
            { "name": "Vice Cream", "price": 2.39, "image": "/static/img/gifts/vicecream.png" },
            { "name": "Chill Flame", "price": 2.63, "image": "/static/img/gifts/chillflame.png" },
            { "name": "Snake Box", "price": 2.75, "image": "/static/img/gifts/snakebox.png" },
            { "name": "Candy Cane", "price": 2.77, "image": "/static/img/gifts/candycane.png" },
            { "name": "Lunar Snake", "price": 2.9, "image": "/static/img/gifts/lunarsnake.png" },
            { "name": "Instant Ramen", "price": 2.91, "image": "/static/img/gifts/instantramen.png" },
            { "name": "Loot Bag", "price": 138.8, "image": "/static/img/gifts/lootbag.png" },
            { "name": "Astral Shard", "price": 184.9, "image": "/static/img/gifts/astralshard.png" }
        ];
    },

    getUser() {
        let user = localStorage.getItem('user_data');
        if (!user || user === "undefined" || JSON.parse(user).inventory.length === 0) {
            const all = this.getDemoGifts();
            // Даем пользователю 12 предметов для теста
            const startInv = [...all, ...all].slice(0, 12);
            user = { name: "Player", balance: 100.0, inventory: startInv };
            this.saveUser(user);
            return user;
        }
        return JSON.parse(user);
    },

    saveUser(data) {
        localStorage.setItem('user_data', JSON.stringify(data));
    },

    initUI() {
        const user = this.getUser();
        const tgUser = tg.initDataUnsafe?.user;
        const name = tgUser ? (tgUser.username || tgUser.first_name) : user.name;
        
        document.querySelectorAll('.username-text').forEach(el => el.textContent = name);
        document.querySelectorAll('.user-balance').forEach(el => el.textContent = user.balance.toFixed(1));

        // Подсветка активной кнопки в меню
        const path = window.location.pathname;
        document.querySelectorAll('.nav-item').forEach(link => {
            if (link.getAttribute('href') === path) link.classList.add('active');
        });
    }
};

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', async () => {
    GameState.initUI();
    
    // Инициализация TON Connect
    console.log('🚀 Initializing TON Connect...');
    await initTONUser();
    
    // Проверяем админа
    await checkAdmin();
    
    // Проверяем статус кошелька
    if (tonConnectUI) {
        const wallet = tonConnectUI.wallet;
        if (wallet) {
            console.log('✅ Wallet already connected');
            await handleWalletConnect(wallet);
        }
    }
});

async function checkAdmin() {
    try {
        if (!currentUserId) return;
        
        const response = await fetch(`/api/user/data/${currentUserId}`);
        const data = await response.json();
        
        if (data.is_admin) {
            const adminBtn = document.getElementById('admin-btn');
            if (adminBtn) {
                adminBtn.style.display = 'flex';
                console.log('✅ Admin button shown');
            }
        }
    } catch (e) {
        console.error('❌ Admin check error:', e);
    }
}