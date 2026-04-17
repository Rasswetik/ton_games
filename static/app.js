const tg = window.Telegram.WebApp;
tg.expand();

// Инициализация TON Connect с проверкой
let tonConnectUI;
try {
    tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
        manifestUrl: window.location.origin + '/tonconnect-manifest.json',
        buttonRootId: 'ton-connect-custom' 
    });
} catch (e) {
    console.error("TonConnect Error:", e);
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

document.addEventListener('DOMContentLoaded', () => GameState.initUI());