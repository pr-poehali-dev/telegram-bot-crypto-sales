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
            
            response_text = handle_message(telegram_id, username, text, chat_id)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'method': 'sendMessage',
                    'chat_id': chat_id,
                    'text': response_text,
                    'parse_mode': 'HTML'
                }),
                'isBase64Encoded': False
            }
        
        elif 'callback_query' in update:
            callback = update['callback_query']
            chat_id = callback['message']['chat']['id']
            data = callback['data']
            telegram_id = callback['from']['id']
            username = callback['from'].get('username', 'Anonymous')
            
            response_text = handle_callback(telegram_id, username, data, chat_id)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'method': 'sendMessage',
                    'chat_id': chat_id,
                    'text': response_text,
                    'parse_mode': 'HTML'
                }),
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


def handle_message(telegram_id: int, username: str, text: str, chat_id: int) -> str:
    user = get_or_create_user(telegram_id, username)
    
    if text == '/start':
        return f"""👋 <b>Добро пожаловать в P2P Exchange Bot!</b>

Безопасная торговля виртуальной валютой с эскроу-защитой.

<b>Доступные команды:</b>
/profile - Ваш профиль и статистика
/buy - Купить валюту
/sell - Продать валюту
/deals - Мои сделки
/balance - Баланс и операции

Ваш текущий режим: <b>{get_role_text(user['role'])}</b>
Используйте /profile для переключения режима."""
    
    elif text == '/profile':
        return format_profile(user)
    
    elif text == '/buy':
        if user['role'] != 'buyer':
            return "⚠️ Переключитесь в режим покупателя через /profile"
        return format_offers()
    
    elif text == '/sell':
        if user['role'] != 'seller':
            return "⚠️ Переключитесь в режим продавца через /profile"
        return """📝 <b>Создание объявления о продаже</b>

Отправьте данные в формате:
<code>цена минсумма макссумма валюта</code>

Пример: <code>95.50 100 5000 USDT</code>"""
    
    elif text == '/deals':
        return format_deals(user['id'])
    
    elif text == '/balance':
        return f"""💰 <b>Ваш баланс</b>

Доступно: <b>${user['balance']:.2f}</b>

Используйте:
/deposit - Пополнить баланс
/withdraw - Вывести средства"""
    
    elif text.startswith('/switch_'):
        new_role = text.replace('/switch_', '')
        if new_role in ['buyer', 'seller']:
            update_user_role(user['id'], new_role)
            return f"✅ Режим изменён на: <b>{get_role_text(new_role)}</b>"
    
    elif user['role'] == 'seller' and ' ' in text:
        parts = text.split()
        if len(parts) == 4:
            try:
                price, min_amt, max_amt, currency = float(parts[0]), float(parts[1]), float(parts[2]), parts[3]
                create_offer(user['id'], price, min_amt, max_amt, currency)
                return f"""✅ <b>Объявление создано!</b>

💵 Цена: ${price}
📊 Лимит: ${min_amt} - ${max_amt}
💎 Валюта: {currency}

Ваше объявление теперь видно покупателям."""
            except:
                pass
    
    return """ℹ️ Используйте команды для навигации:

/profile - Профиль
/buy - Купить
/sell - Продать
/deals - Сделки
/balance - Баланс"""


def handle_callback(telegram_id: int, username: str, data: str, chat_id: int) -> str:
    user = get_or_create_user(telegram_id, username)
    
    if data.startswith('buy_'):
        offer_id = int(data.replace('buy_', ''))
        return initiate_deal(user['id'], offer_id)
    
    elif data.startswith('complete_'):
        deal_id = int(data.replace('complete_', ''))
        return complete_deal(deal_id, user['id'])
    
    elif data.startswith('dispute_'):
        deal_id = int(data.replace('dispute_', ''))
        return open_dispute(deal_id, user['id'])
    
    return "Действие выполнено"


def get_role_text(role: str) -> str:
    return "🛒 Покупатель" if role == 'buyer' else "💼 Продавец"


def format_profile(user: Dict[str, Any]) -> str:
    opposite_role = 'seller' if user['role'] == 'buyer' else 'buyer'
    
    return f"""👤 <b>Ваш профиль</b>

<b>Режим:</b> {get_role_text(user['role'])}
Переключить: /switch_{opposite_role}

💰 <b>Баланс:</b> ${user['balance']:.2f}

📊 <b>Статистика:</b>
• Куплено: ${user['total_bought']:.2f}
• Продано: ${user['total_sold']:.2f}
• Сделок завершено: {user['completed_deals']}
• Рейтинг: {'⭐' * int(user['rating'])} ({user['rating']:.1f})"""


def format_offers() -> str:
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
        return "📭 Нет доступных предложений"
    
    text = "💎 <b>Лучшие предложения</b>\n\n"
    
    for offer in offers:
        text += f"""━━━━━━━━━━━━━━━
👤 {offer['username']}
⭐ {offer['rating']:.1f} • {offer['completed_deals']} сделок
💵 Цена: ${offer['price']}
📊 Лимит: ${offer['min_amount']} - ${offer['max_amount']}
💎 {offer['currency']}

/buy_{offer['id']} - Купить

"""
    
    return text


def format_deals(user_id: int) -> str:
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
        return "📭 У вас пока нет сделок"
    
    text = "📋 <b>Ваши сделки</b>\n\n"
    
    for deal in deals:
        status_emoji = {'pending': '⏳', 'escrow': '🔒', 'completed': '✅', 'cancelled': '❌', 'dispute': '⚠️'}
        
        text += f"""━━━━━━━━━━━━━━━
{status_emoji.get(deal['status'], '•')} Сделка #{deal['id']}
💵 ${deal['amount']} • {deal['currency']}
👤 {deal['buyer_name']} ↔ {deal['seller_name']}
📅 {deal['created_at'].strftime('%d.%m.%Y %H:%M')}

"""
        
        if deal['status'] == 'escrow':
            text += f"/complete_{deal['id']} - Завершить\n/dispute_{deal['id']} - Спор\n\n"
    
    return text


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


def initiate_deal(buyer_id: int, offer_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM offers WHERE id = %s AND is_active = true", (offer_id,))
    offer = cursor.fetchone()
    
    if not offer:
        cursor.close()
        conn.close()
        return "❌ Предложение недоступно"
    
    cursor.execute(
        """INSERT INTO deals (offer_id, buyer_id, seller_id, amount, price, currency, status)
           VALUES (%s, %s, %s, %s, %s, %s, 'escrow')""",
        (offer_id, buyer_id, offer['seller_id'], offer['min_amount'], offer['price'], offer['currency'])
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return f"""✅ <b>Сделка создана!</b>

💰 Сумма: ${offer['min_amount']}
💵 Цена: ${offer['price']}
🔒 Средства в эскроу

Ожидайте подтверждения продавца."""


def complete_deal(deal_id: int, user_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE deals SET status = 'completed' WHERE id = %s AND (buyer_id = %s OR seller_id = %s)",
        (deal_id, user_id, user_id)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return "✅ Сделка успешно завершена!"


def open_dispute(deal_id: int, user_id: int) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE deals SET status = 'dispute' WHERE id = %s AND (buyer_id = %s OR seller_id = %s)",
        (deal_id, user_id, user_id)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return "⚠️ Спор открыт. Администратор свяжется с вами."
