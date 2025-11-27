import json
import os
from typing import Dict, Any, Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Telegram webhook для P2P торговли криптовалютой
    Args: event с httpMethod, body (Telegram update), context с request_id
    Returns: HTTP response для Telegram API
    '''
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    try:
        update = json.loads(event.get('body', '{}'))
        
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            username = message.get('from', {}).get('username', 'Anonymous')
            telegram_id = message['from']['id']
            
            response_data = handle_message(telegram_id, username, text, chat_id)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(response_data),
                'isBase64Encoded': False
            }
        
        elif 'callback_query' in update:
            callback = update['callback_query']
            chat_id = callback['message']['chat']['id']
            data = callback['data']
            telegram_id = callback['from']['id']
            username = callback['from'].get('username', 'Anonymous')
            
            response_data = handle_callback(telegram_id, username, data, chat_id)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(response_data),
                'isBase64Encoded': False
            }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True}),
            'isBase64Encoded': False
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }


def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)


def get_or_create_user(telegram_id: int, username: str) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM users WHERE telegram_id = %s",
        (telegram_id,)
    )
    user = cursor.fetchone()
    
    if not user:
        cursor.execute(
            """INSERT INTO users (telegram_id, username) 
               VALUES (%s, %s) RETURNING *""",
            (telegram_id, username)
        )
        user = cursor.fetchone()
        conn.commit()
    
    cursor.close()
    conn.close()
    
    return dict(user)


def create_keyboard(buttons: List[List[Dict[str, str]]]) -> Dict[str, Any]:
    return {
        'inline_keyboard': buttons
    }


def handle_message(telegram_id: int, username: str, text: str, chat_id: int) -> Dict[str, Any]:
    user = get_or_create_user(telegram_id, username)
    
    if text == '/start':
        keyboard = create_keyboard([
            [{'text': '👤 Профиль', 'callback_data': 'profile'}],
            [{'text': '🛒 Купить', 'callback_data': 'buy'}, {'text': '💼 Продать', 'callback_data': 'sell'}],
            [{'text': '📋 Сделки', 'callback_data': 'deals'}, {'text': '💰 Баланс', 'callback_data': 'balance'}]
        ])
        
        return {
            'method': 'sendMessage',
            'chat_id': chat_id,
            'text': f"""👋 <b>Добро пожаловать в P2P Exchange Bot!</b>

Безопасная торговля виртуальной валютой с эскроу-защитой.

Ваш текущий режим: <b>{get_role_text(user['role'])}</b>

Выберите действие:""",
            'parse_mode': 'HTML',
            'reply_markup': keyboard
        }
    
    elif text == '/profile':
        return format_profile(user, chat_id)
    
    elif text == '/buy':
        if user['role'] != 'buyer':
            return {
                'method': 'sendMessage',
                'chat_id': chat_id,
                'text': "⚠️ Переключитесь в режим покупателя через Профиль",
                'parse_mode': 'HTML'
            }
        return format_offers(chat_id)
    
    elif text == '/sell':
        if user['role'] != 'seller':
            return {
                'method': 'sendMessage',
                'chat_id': chat_id,
                'text': "⚠️ Переключитесь в режим продавца через Профиль",
                'parse_mode': 'HTML'
            }
        return format_sell_form(chat_id)
    
    elif text == '/deals':
        return format_deals(user['id'], chat_id)
    
    elif text == '/balance':
        return format_balance(user, chat_id)
    
    elif user['role'] == 'seller' and ' ' in text:
        parts = text.split()
        if len(parts) == 4:
            try:
                price, min_amt, max_amt, currency = float(parts[0]), float(parts[1]), float(parts[2]), parts[3]
                create_offer(user['id'], price, min_amt, max_amt, currency)
                
                keyboard = create_keyboard([[{'text': '🏠 Главное меню', 'callback_data': 'menu'}]])
                
                return {
                    'method': 'sendMessage',
                    'chat_id': chat_id,
                    'text': f"""✅ <b>Объявление создано!</b>

💵 Цена: {price:.2f}₽
📊 Лимит: {min_amt:.0f}₽ - {max_amt:.0f}₽
💎 Валюта: {currency}

Ваше объявление теперь видно покупателям.""",
                    'parse_mode': 'HTML',
                    'reply_markup': keyboard
                }
            except:
                pass
    
    keyboard = create_keyboard([
        [{'text': '👤 Профиль', 'callback_data': 'profile'}],
        [{'text': '🛒 Купить', 'callback_data': 'buy'}, {'text': '💼 Продать', 'callback_data': 'sell'}],
        [{'text': '📋 Сделки', 'callback_data': 'deals'}, {'text': '💰 Баланс', 'callback_data': 'balance'}]
    ])
    
    return {
        'method': 'sendMessage',
        'chat_id': chat_id,
        'text': "ℹ️ Выберите действие:",
        'parse_mode': 'HTML',
        'reply_markup': keyboard
    }


def handle_callback(telegram_id: int, username: str, data: str, chat_id: int) -> Dict[str, Any]:
    user = get_or_create_user(telegram_id, username)
    
    if data == 'menu':
        keyboard = create_keyboard([
            [{'text': '👤 Профиль', 'callback_data': 'profile'}],
            [{'text': '🛒 Купить', 'callback_data': 'buy'}, {'text': '💼 Продать', 'callback_data': 'sell'}],
            [{'text': '📋 Сделки', 'callback_data': 'deals'}, {'text': '💰 Баланс', 'callback_data': 'balance'}]
        ])
        
        return {
            'method': 'sendMessage',
            'chat_id': chat_id,
            'text': f"Главное меню\n\nВаш режим: <b>{get_role_text(user['role'])}</b>",
            'parse_mode': 'HTML',
            'reply_markup': keyboard
        }
    
    elif data == 'profile':
        return format_profile(user, chat_id)
    
    elif data == 'buy':
        if user['role'] != 'buyer':
            keyboard = create_keyboard([[{'text': '🏠 Главное меню', 'callback_data': 'menu'}]])
            return {
                'method': 'sendMessage',
                'chat_id': chat_id,
                'text': "⚠️ Переключитесь в режим покупателя через Профиль",
                'parse_mode': 'HTML',
                'reply_markup': keyboard
            }
        return format_offers(chat_id)
    
    elif data == 'sell':
        if user['role'] != 'seller':
            keyboard = create_keyboard([[{'text': '🏠 Главное меню', 'callback_data': 'menu'}]])
            return {
                'method': 'sendMessage',
                'chat_id': chat_id,
                'text': "⚠️ Переключитесь в режим продавца через Профиль",
                'parse_mode': 'HTML',
                'reply_markup': keyboard
            }
        return format_sell_form(chat_id)
    
    elif data == 'deals':
        return format_deals(user['id'], chat_id)
    
    elif data == 'balance':
        return format_balance(user, chat_id)
    
    elif data == 'switch_buyer':
        update_user_role(user['id'], 'buyer')
        return format_profile(get_user_by_id(user['id']), chat_id)
    
    elif data == 'switch_seller':
        update_user_role(user['id'], 'seller')
        return format_profile(get_user_by_id(user['id']), chat_id)
    
    elif data.startswith('buy_'):
        offer_id = int(data.replace('buy_', ''))
        return initiate_deal(user['id'], offer_id, chat_id)
    
    elif data.startswith('complete_'):
        deal_id = int(data.replace('complete_', ''))
        return complete_deal(deal_id, user['id'], chat_id)
    
    elif data.startswith('dispute_'):
        deal_id = int(data.replace('dispute_', ''))
        return open_dispute(deal_id, user['id'], chat_id)
    
    return {
        'method': 'sendMessage',
        'chat_id': chat_id,
        'text': "Действие выполнено",
        'parse_mode': 'HTML'
    }


def get_role_text(role: str) -> str:
    return "🛒 Покупатель" if role == 'buyer' else "💼 Продавец"


def get_user_by_id(user_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(user)


def format_profile(user: Dict[str, Any], chat_id: int) -> Dict[str, Any]:
    opposite_role = 'seller' if user['role'] == 'buyer' else 'buyer'
    opposite_text = '💼 Стать продавцом' if user['role'] == 'buyer' else '🛒 Стать покупателем'
    
    keyboard = create_keyboard([
        [{'text': opposite_text, 'callback_data': f'switch_{opposite_role}'}],
        [{'text': '💰 Баланс', 'callback_data': 'balance'}],
        [{'text': '🏠 Главное меню', 'callback_data': 'menu'}]
    ])
    
    return {
        'method': 'sendMessage',
        'chat_id': chat_id,
        'text': f"""👤 <b>Ваш профиль</b>

<b>Режим:</b> {get_role_text(user['role'])}

💰 <b>Баланс:</b> {user['balance']:.2f}₽

📊 <b>Статистика:</b>
• Куплено: {user['total_bought']:.2f}₽
• Продано: {user['total_sold']:.2f}₽
• Сделок завершено: {user['completed_deals']}
• Рейтинг: {'⭐' * int(user['rating'])} ({user['rating']:.1f})""",
        'parse_mode': 'HTML',
        'reply_markup': keyboard
    }


def format_balance(user: Dict[str, Any], chat_id: int) -> Dict[str, Any]:
    keyboard = create_keyboard([
        [{'text': '➕ Пополнить', 'callback_data': 'deposit'}, {'text': '➖ Вывести', 'callback_data': 'withdraw'}],
        [{'text': '🏠 Главное меню', 'callback_data': 'menu'}]
    ])
    
    return {
        'method': 'sendMessage',
        'chat_id': chat_id,
        'text': f"""💰 <b>Ваш баланс</b>

Доступно: <b>{user['balance']:.2f}₽</b>

Выберите действие:""",
        'parse_mode': 'HTML',
        'reply_markup': keyboard
    }


def format_offers(chat_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT o.*, u.username, u.rating, u.completed_deals
        FROM offers o
        JOIN users u ON o.seller_id = u.id
        WHERE o.is_active = true
        ORDER BY o.price ASC
        LIMIT 5
    """)
    
    offers = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not offers:
        keyboard = create_keyboard([[{'text': '🏠 Главное меню', 'callback_data': 'menu'}]])
        return {
            'method': 'sendMessage',
            'chat_id': chat_id,
            'text': "📭 Нет доступных предложений",
            'parse_mode': 'HTML',
            'reply_markup': keyboard
        }
    
    text = "💎 <b>Лучшие предложения</b>\n\n"
    buttons = []
    
    for offer in offers:
        text += f"""━━━━━━━━━━━━━━━
👤 {offer['username']}
⭐ {offer['rating']:.1f} • {offer['completed_deals']} сделок
💵 Цена: {offer['price']:.2f}₽
📊 Лимит: {offer['min_amount']:.0f}₽ - {offer['max_amount']:.0f}₽
💎 {offer['currency']}

"""
        buttons.append([{'text': f"Купить у {offer['username']}", 'callback_data': f"buy_{offer['id']}"}])
    
    buttons.append([{'text': '🏠 Главное меню', 'callback_data': 'menu'}])
    keyboard = create_keyboard(buttons)
    
    return {
        'method': 'sendMessage',
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': keyboard
    }


def format_sell_form(chat_id: int) -> Dict[str, Any]:
    keyboard = create_keyboard([[{'text': '🏠 Главное меню', 'callback_data': 'menu'}]])
    
    return {
        'method': 'sendMessage',
        'chat_id': chat_id,
        'text': """📝 <b>Создание объявления о продаже</b>

Отправьте данные в формате:
<code>цена минсумма макссумма валюта</code>

Пример: <code>95.50 1000 50000 USDT</code>""",
        'parse_mode': 'HTML',
        'reply_markup': keyboard
    }


def format_deals(user_id: int, chat_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT d.*, 
               buyer.username as buyer_name,
               seller.username as seller_name
        FROM deals d
        JOIN users buyer ON d.buyer_id = buyer.id
        JOIN users seller ON d.seller_id = seller.id
        WHERE d.buyer_id = %s OR d.seller_id = %s
        ORDER BY d.created_at DESC
        LIMIT 10
    """, (user_id, user_id))
    
    deals = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not deals:
        keyboard = create_keyboard([[{'text': '🏠 Главное меню', 'callback_data': 'menu'}]])
        return {
            'method': 'sendMessage',
            'chat_id': chat_id,
            'text': "📭 У вас пока нет сделок",
            'parse_mode': 'HTML',
            'reply_markup': keyboard
        }
    
    text = "📋 <b>Ваши сделки</b>\n\n"
    buttons = []
    
    for deal in deals:
        status_emoji = {'pending': '⏳', 'escrow': '🔒', 'completed': '✅', 'cancelled': '❌', 'dispute': '⚠️'}
        
        text += f"""━━━━━━━━━━━━━━━
{status_emoji.get(deal['status'], '•')} Сделка #{deal['id']}
💵 {deal['amount']:.0f}₽ • {deal['currency']}
👤 {deal['buyer_name']} ↔ {deal['seller_name']}
📅 {deal['created_at'].strftime('%d.%m.%Y %H:%M')}
Статус: {get_status_text(deal['status'])}

"""
        
        if deal['status'] == 'escrow':
            buttons.append([
                {'text': f"✅ Завершить #{deal['id']}", 'callback_data': f"complete_{deal['id']}"},
                {'text': f"⚠️ Спор #{deal['id']}", 'callback_data': f"dispute_{deal['id']}"}
            ])
    
    buttons.append([{'text': '🏠 Главное меню', 'callback_data': 'menu'}])
    keyboard = create_keyboard(buttons)
    
    return {
        'method': 'sendMessage',
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': keyboard
    }


def get_status_text(status: str) -> str:
    statuses = {
        'pending': 'Ожидание',
        'escrow': 'В эскроу',
        'completed': 'Завершена',
        'cancelled': 'Отменена',
        'dispute': 'Спор'
    }
    return statuses.get(status, status)


def update_user_role(user_id: int, role: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = %s WHERE id = %s", (role, user_id))
    conn.commit()
    cursor.close()
    conn.close()


def create_offer(seller_id: int, price: float, min_amount: float, max_amount: float, currency: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO offers (seller_id, price, min_amount, max_amount, currency)
           VALUES (%s, %s, %s, %s, %s)""",
        (seller_id, price, min_amount, max_amount, currency)
    )
    conn.commit()
    cursor.close()
    conn.close()


def initiate_deal(buyer_id: int, offer_id: int, chat_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM offers WHERE id = %s AND is_active = true", (offer_id,))
    offer = cursor.fetchone()
    
    if not offer:
        cursor.close()
        conn.close()
        keyboard = create_keyboard([[{'text': '🏠 Главное меню', 'callback_data': 'menu'}]])
        return {
            'method': 'sendMessage',
            'chat_id': chat_id,
            'text': "❌ Предложение недоступно",
            'parse_mode': 'HTML',
            'reply_markup': keyboard
        }
    
    cursor.execute(
        """INSERT INTO deals (offer_id, buyer_id, seller_id, amount, price, currency, status)
           VALUES (%s, %s, %s, %s, %s, %s, 'escrow')""",
        (offer_id, buyer_id, offer['seller_id'], offer['min_amount'], offer['price'], offer['currency'])
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    keyboard = create_keyboard([
        [{'text': '📋 Мои сделки', 'callback_data': 'deals'}],
        [{'text': '🏠 Главное меню', 'callback_data': 'menu'}]
    ])
    
    return {
        'method': 'sendMessage',
        'chat_id': chat_id,
        'text': f"""✅ <b>Сделка создана!</b>

💰 Сумма: {offer['min_amount']:.0f}₽
💵 Цена: {offer['price']:.2f}₽
🔒 Средства в эскроу

Ожидайте подтверждения продавца.""",
        'parse_mode': 'HTML',
        'reply_markup': keyboard
    }


def complete_deal(deal_id: int, user_id: int, chat_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE deals SET status = 'completed' WHERE id = %s AND (buyer_id = %s OR seller_id = %s)",
        (deal_id, user_id, user_id)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    keyboard = create_keyboard([
        [{'text': '📋 Мои сделки', 'callback_data': 'deals'}],
        [{'text': '🏠 Главное меню', 'callback_data': 'menu'}]
    ])
    
    return {
        'method': 'sendMessage',
        'chat_id': chat_id,
        'text': "✅ Сделка успешно завершена!",
        'parse_mode': 'HTML',
        'reply_markup': keyboard
    }


def open_dispute(deal_id: int, user_id: int, chat_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE deals SET status = 'dispute' WHERE id = %s AND (buyer_id = %s OR seller_id = %s)",
        (deal_id, user_id, user_id)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    keyboard = create_keyboard([
        [{'text': '📋 Мои сделки', 'callback_data': 'deals'}],
        [{'text': '🏠 Главное меню', 'callback_data': 'menu'}]
    ])
    
    return {
        'method': 'sendMessage',
        'chat_id': chat_id,
        'text': "⚠️ Спор открыт. Администратор свяжется с вами.",
        'parse_mode': 'HTML',
        'reply_markup': keyboard
    }
