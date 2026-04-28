/**
 * TonConnect UI Integration
 * Простая и надёжная интеграция с TonConnect UI library
 */

window.tonConnectUI = null;
window.tonConnectReady = false;
window.tonConnectError = null;

/**
 * Загрузить TonConnectUI скрипт
 */
function loadTonConnectScript() {
  return new Promise((resolve, reject) => {
    // Проверить если уже загруженo
    if (typeof TonConnectUI !== 'undefined') {
      console.log('[TonConnect] TonConnectUI already available in window');
      window.tonConnectReady = true;
      resolve();
      return;
    }

    const timeout = setTimeout(() => {
      const err = 'Script load timeout (20s)';
      console.error('[TonConnect]', err);
      window.tonConnectError = err;
      reject(new Error(err));
    }, 20000);

    // Попытаться загрузить из локального файла СНАЧАЛА
    const sources = [
      '/static/vendor/tonconnect-ui.min.js',  // Локальный файл - наиболее надёжный
      'https://cdn.jsdelivr.net/npm/@tonconnect/ui@latest/dist/tonconnect-ui.min.js',
      'https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js'
    ];

    let currentSourceIndex = 0;

    function loadNextSource() {
      if (currentSourceIndex >= sources.length) {
        clearTimeout(timeout);
        const err = 'Failed to load TonConnectUI from all sources';
        console.error('[TonConnect]', err);
        window.tonConnectError = err;
        reject(new Error(err));
        return;
      }

      const src = sources[currentSourceIndex];
      currentSourceIndex++;

      console.log('[TonConnect] Attempting to load from:', src);

      const script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.crossOrigin = 'anonymous';

      script.onload = () => {
        console.log('[TonConnect] Script loaded from:', src);
        // Дождаться регистрации глобальной переменной
        setTimeout(() => {
          if (typeof window.TonConnectUI !== 'undefined') {
            clearTimeout(timeout);
            window.tonConnectReady = true;
            console.log('[TonConnect] ✓ TonConnectUI available globally from:', src);
            resolve();
          } else {
            console.warn('[TonConnect] TonConnectUI not in window after load, trying next source');
            loadNextSource();
          }
        }, 500);
      };

      script.onerror = () => {
        console.warn('[TonConnect] Failed to load script from:', src);
        loadNextSource();
      };

      document.head.appendChild(script);
    }

    loadNextSource();
  });
}

/**
 * Инициализировать TonConnect UI
 */
async function initTonConnectUI() {
  if (window.tonConnectUI) {
    console.log('[TonConnect] Already initialized');
    return window.tonConnectUI;
  }

  try {
    console.log('[TonConnect] Initializing...');

    // Проверить, есть ли TonConnectUI в window
    if (typeof TonConnectUI === 'undefined') {
      console.log('[TonConnect] TonConnectUI not found in window, loading script...');
      await loadTonConnectScript();
    }

    if (typeof TonConnectUI === 'undefined') {
      throw new Error('TonConnectUI still not available after loading');
    }

    // Создать инстанс
    const ui = new TonConnectUI({
      manifestUrl: window.location.origin + '/tonconnect-manifest.json'
    });

    window.tonConnectUI = ui;
    console.log('[TonConnect] ✓ Initialized successfully');
    return ui;

  } catch (error) {
    console.error('[TonConnect] Init error:', error);
    window.tonConnectError = error.message;
    return null;
  }
}



/**
 * Открыть wallet picker modal
 */
async function openWalletModal() {
  try {
    const ui = await initTonConnectUI();
    if (!ui) {
      const errMsg = window.tonConnectError || 'TonConnect library failed to load. Please check your connection or place a local copy at /static/vendor/tonconnect-ui.min.js';
      showNotification(errMsg, 'error');
      console.error('[TonConnect] Init failed:', errMsg);
      return;
    }

    console.log('[TonConnect] Opening wallet modal...');
    
    // Попробовать разные методы
    if (typeof ui.openModal === 'function') {
      await ui.openModal();
    } else if (typeof ui.connectWallet === 'function') {
      await ui.connectWallet();
    } else if (typeof ui.connect === 'function') {
      await ui.connect();
    } else {
      throw new Error('No connect method found in TonConnectUI');
    }

    showNotification('✓ Кошелёк подключен', 'success');

  } catch (error) {
    console.error('[TonConnect] Modal error:', error);
    if (!error.message.includes('user')) {
      showNotification('Ошибка подключения: ' + error.message, 'error');
    }
  }
}

/**
 * Отправить TON транзакцию
 */
async function sendTonTransaction(toAddress, amountTon, comment = '') {
  try {
    const ui = await initTonConnectUI();
    if (!ui) {
      showNotification('TonConnect не инициализирован', 'error');
      return null;
    }

    const wallet = ui.wallet;
    if (!wallet) {
      showNotification('Подключите кошелёк', 'warning');
      await openWalletModal();
      return null;
    }

    console.log('[TonConnect] Sending transaction...');

    // Конвертировать TON в nanotons
    const amountNano = Math.floor(amountTon * 1e9).toString();

    const transaction = {
      validUntil: Math.floor(Date.now() / 1000) + 600,
      messages: [
        {
          address: toAddress,
          amount: amountNano,
          payload: comment ? encodeComment(comment) : undefined
        }
      ]
    };

    if (typeof ui.sendTransaction === 'function') {
      const result = await ui.sendTransaction(transaction);
      showNotification('✓ Транзакция отправлена', 'success');
      return result;
    }

    throw new Error('sendTransaction not available');

  } catch (error) {
    console.error('[TonConnect] Transaction error:', error);
    if (!error.message.includes('user')) {
      showNotification('Ошибка: ' + error.message, 'error');
    }
    return null;
  }
}

/**
 * Пополнить баланс
 */
async function topUpBalance(amountTon = 0.5) {
  try {
    const address = 'UQDw7-rC3VhNeN5VUjV_Kz5TVBJ5pX4EEI_OOSdU8J0oQkOh'; // TON receiver
    
    let ui = await initTonConnectUI();
    if (!ui) {
      const errMsg = window.tonConnectError || 'TonConnect library failed to load. Please check your connection or place a local copy at /static/vendor/tonconnect-ui.min.js';
      showNotification(errMsg, 'error');
      console.error('[TonConnect] Init failed:', errMsg);
      return;
    }

    // Если нет подключённого кошелька, открыть picker
    if (!ui.wallet) {
      console.log('[TonConnect] No wallet connected, opening modal...');
      await openWalletModal();
      
      // Ждём, пока кошелёк подключится
      await new Promise(r => setTimeout(r, 1000));
      ui = await initTonConnectUI();
    }

    if (ui && ui.wallet) {
      showNotification('⏳ Отправка ' + amountTon + ' TON...', 'info');
      await sendTonTransaction(address, amountTon, 'Top-up');
    }

  } catch (error) {
    console.error('[TonConnect] Top-up error:', error);
    showNotification('Ошибка пополнения: ' + error.message, 'error');
  }
}

/**
 * Закодировать комментарий
 */
function encodeComment(text) {
  // Простое кодирование текста в base64
  try {
    return btoa(text);
  } catch (e) {
    return undefined;
  }
}

/**
 * Получить статус подключения
 */
async function getTonConnectStatus() {
  try {
    const ui = await initTonConnectUI();
    if (!ui) return null;
    return ui.wallet || null;
  } catch (error) {
    console.error('[TonConnect] Status error:', error);
    return null;
  }
}

/**
 * Отключить кошелёк
 */
async function disconnectTonWallet() {
  try {
    const ui = await initTonConnectUI();
    if (ui && typeof ui.disconnect === 'function') {
      await ui.disconnect();
      showNotification('Кошелёк отключен', 'info');
    }
  } catch (error) {
    console.error('[TonConnect] Disconnect error:', error);
  }
}

// Экспортировать глобально
window.TonConnect = {
  init: initTonConnectUI,
  openModal: openWalletModal,
  sendTx: sendTonTransaction,
  topUp: topUpBalance,
  getStatus: getTonConnectStatus,
  disconnect: disconnectTonWallet
};

console.log('[TonConnect] Module loaded');

/**
 * Поддержка Telegram Stars
 */

/**
 * Инициализировать Telegram Web App для Stars платежей
 */
function initTelegramWebApp() {
  if (typeof window.Telegram === 'undefined' || !window.Telegram.WebApp) {
    console.warn('[TelegramStars] Telegram Web App not available');
    return null;
  }
  
  const tg = window.Telegram.WebApp;
  try {
    tg.expand();
    tg.ready();
    console.log('[TelegramStars] Telegram Web App initialized');
    return tg;
  } catch (e) {
    console.error('[TelegramStars] Error initializing Telegram:', e);
    return null;
  }
}

/**
 * Открыть платёж Telegram Stars
 */
async function topUpWithTelegramStars(starAmount = 1) {
  try {
    console.log('[TelegramStars] Initiating stars top-up:', starAmount);
    
    const tg = initTelegramWebApp();
    if (!tg) {
      showNotification('Telegram Web App не доступен', 'error');
      return;
    }
    
    // Получить ссылку на платёж от сервера
    const response = await fetch('/api/create-stars-invoice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stars_amount: starAmount })
    });
    
    if (!response.ok) {
      throw new Error('Failed to create invoice');
    }
    
    const data = await response.json();
    
    if (!data.success || !data.invoice_link) {
      throw new Error('Invalid invoice response');
    }
    
    // Открыть инвойс
    showNotification('⏳ Открываем платёж Telegram Stars...', 'info');
    
    if (typeof tg.openInvoice === 'function') {
      tg.openInvoice(data.invoice_link, (status) => {
        console.log('[TelegramStars] Invoice closed with status:', status);
        
        if (status === 'paid') {
          showNotification('✓ Спасибо за пополнение!', 'success');
        } else if (status === 'failed') {
          showNotification('Платёж не прошёл', 'error');
        } else if (status === 'cancelled') {
          console.log('[TelegramStars] Payment cancelled by user');
        }
      });
    } else {
      // Fallback: открыть в новом окне
      window.open(data.invoice_link, '_blank');
      showNotification('Откройте ссылку для завершения платежа', 'info');
    }
    
  } catch (error) {
    console.error('[TelegramStars] Top-up error:', error);
    showNotification('Ошибка: ' + error.message, 'error');
  }
}

// Добавить в глобальный API
window.TonConnect.topUpStars = topUpWithTelegramStars;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('[TonConnect] DOM ready, auto-initializing...');
    loadTonConnectScript().then(() => {
      console.log('[TonConnect] ✓ Auto-initialization completed');
    }).catch(err => {
      console.error('[TonConnect] Auto-initialization failed:', err.message);
    });
  });
} else {
  // DOM already loaded
  console.log('[TonConnect] DOM already loaded, auto-initializing...');
  loadTonConnectScript().then(() => {
    console.log('[TonConnect] ✓ Auto-initialization completed');
  }).catch(err => {
    console.error('[TonConnect] Auto-initialization failed:', err.message);
  });
}
