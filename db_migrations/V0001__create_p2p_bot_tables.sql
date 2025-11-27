-- Создание таблиц для P2P Telegram бота

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    role VARCHAR(20) DEFAULT 'buyer' CHECK (role IN ('buyer', 'seller')),
    balance DECIMAL(15, 2) DEFAULT 0.00,
    total_bought DECIMAL(15, 2) DEFAULT 0.00,
    total_sold DECIMAL(15, 2) DEFAULT 0.00,
    completed_deals INT DEFAULT 0,
    rating DECIMAL(3, 2) DEFAULT 5.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица объявлений о продаже
CREATE TABLE IF NOT EXISTS offers (
    id SERIAL PRIMARY KEY,
    seller_id INT REFERENCES users(id),
    price DECIMAL(10, 2) NOT NULL,
    min_amount DECIMAL(15, 2) NOT NULL,
    max_amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USDT',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сделок
CREATE TABLE IF NOT EXISTS deals (
    id SERIAL PRIMARY KEY,
    offer_id INT REFERENCES offers(id),
    buyer_id INT REFERENCES users(id),
    seller_id INT REFERENCES users(id),
    amount DECIMAL(15, 2) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USDT',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'escrow', 'completed', 'cancelled', 'dispute')),
    escrow_amount DECIMAL(15, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_offers_seller_active ON offers(seller_id, is_active);
CREATE INDEX IF NOT EXISTS idx_deals_buyer ON deals(buyer_id);
CREATE INDEX IF NOT EXISTS idx_deals_seller ON deals(seller_id);
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);
