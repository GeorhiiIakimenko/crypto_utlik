import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI
import csv
from datetime import datetime
import os
import aiohttp

# Конфигурация
API_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SERPER_API_KEY = os.getenv('SERPER_API_KEY')


# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Инициализация OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)


# Функция для сохранения данных пользователя
async def save_user_data(user: types.User):
    file_exists = os.path.exists('users_data.csv')

    with open('users_data.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                'Date',
                'User ID',
                'Username',
                'First Name',
                'Last Name',
                'Language Code',
                'Is Bot',
                'Timestamp'
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d"),
            user.id,
            user.username if user.username else 'Not provided',
            user.first_name if user.first_name else 'Not provided',
            user.last_name if user.last_name else 'Not provided',
            user.language_code if user.language_code else 'Not provided',
            user.is_bot,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])


# Функция для веб-поиска
async def search_crypto_info(query):
    async with aiohttp.ClientSession() as session:
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {
            'q': f"crypto {query}",  # Добавляем 'crypto' для более релевантных результатов
            'num': 3,
            'gl': 'us',  # Локализация поиска
            'hl': 'ru'  # Язык результатов
        }
        try:
            async with session.post('https://google.serper.dev/search',
                                    headers=headers,
                                    json=payload) as response:
                results = await response.json()
                if 'organic' in results:
                    search_results = []
                    for result in results['organic'][:3]:
                        search_results.append({
                            'title': result.get('title', ''),
                            'snippet': result.get('snippet', ''),
                            'link': result.get('link', ''),
                            'date': result.get('date', '')
                        })
                    return search_results
                return []
        except Exception as e:
            logging.error(f"Search error: {e}")
            return []


# Создание инлайн клавиатуры
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Общение с криптоботом", callback_data="crypto_chat")],
        [InlineKeyboardButton(text="ℹ️ Информация про конференцию", callback_data="conference_info")],
        [InlineKeyboardButton(text="🌐 Перейти на сайт", url="https://blockchainworld.by/")],
        [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="contact_us")]
    ])
    return keyboard


# Системные промты
CRYPTO_SYSTEM_PROMPT = """You are a Blockchain and Web3 Expert with a unique personality - snarky, unfiltered, and confident, but deeply knowledgeable. Your traits include:

Character & Style:
- Bombastic confidence in your crypto knowledge
- Sarcastic and witty responses that still deliver valuable information
- Not afraid to call out crypto scams and hype with creative humor
- Use occasional creative profanity to emphasize points
- When you don't know something, you explicitly mention that you'll search for the latest info
- Always respond in Russian language!

Response Structure:
1. For questions about current events/prices/news:
   - Acknowledge that you need to check the latest data
   - Use the search results provided to give up-to-date information
   - Add your expert analysis and opinion
   - Include relevant links for users to verify

2. For technical questions:
   - Provide detailed technical explanations
   - Use analogies and examples
   - If needed, supplement with latest developments from search

3. For market/trend questions:
   - Combine your base knowledge with current data
   - Provide balanced analysis
   - Always remind users about DYOR (Do Your Own Research)

Technical Expertise:
- DeFi protocols and smart contract development
- Blockchain platforms: ETH, BTC, BSC, etc.
- Development tools and languages
- Security best practices

Remember: 
- Always verify current prices, news, and trends through search
- Be transparent about using search for latest information
- Maintain your personality while delivering accurate data
- Include relevant links when citing current information
- Warn about risks and encourage independent research
- Always respond in Russian!"""

CONFERENCE_SYSTEM_PROMPT = """Ты - харизматичный и немного дерзкий организатор крипто-конференции BLOCKCHAIN WORLD SUMMIT. 
Ты обожаешь свое мероприятие и готов рассказать о нем с юмором и энтузиазмом.

Вот полное расписание конференции, которое ты знаешь наизусть:

🚀 ПРОГРАММА BLOCKCHAIN WORLD SUMMIT:

09:00 - Начало регистрации участников

10:00 - ОТКРЫТИЕ САММИТА:
- 10:00-10:20: Лиза Сотилис - "Искусство как связь поколений: Наследие и инновации в эпоху цифровизации общества" + Открытие выставки
- 10:20-10:40: Александр Кириллов - "Завтра начинается уже сегодня. Развитие креативности в эпоху токенизации"
- 10:40-11:20: Панельная дискуссия "Интеграция искусства и технологий" (участники: Василий Кулеш, Андрей Новиков, Тарас Надольный, Александр Кириллов, Екатерина Логвинович, Марианна Гнездилова, Александр Филиппов, Андрей Хомиченок)

УТРЕННЯЯ СЕССИЯ:
- 11:20-11:40: Ян Драновский - "Метавселенные и их возможности"
- 11:40-12:00: Екатерина Логвинович - "Перспективы токенизации для белорусского рынка"
- 12:00-12:20: Ольга Фуседер - "Отслеживание транзакций в криптовалютах"
- 12:20-13:00: Ирина Янковская - "Проверка на доверие: Полиграф в финтехе" + Шоу полиграф

13:00-13:40: ПЕРЕРЫВ + ШОУ ПРИШЕЛЬЦЕВ 👽

ДНЕВНАЯ СЕССИЯ:
- 13:40-14:00: Юрий Дергачев (Shamrock) - "В крипту может каждый"
- 14:00-14:20: Андрей Шлыков - "Анонимность в криптоплатежах"
- 14:20-14:40: Тарас Надольный - "TradFi vs DeFi: Гонка за клиента"
- 14:40-15:00: Денис Грицкевич - "Как заработать на криптовалюте"
- 15:00-15:20: Игорь Баел - "Развитие GameFi проектов и маркетинг"
- 15:20-15:40: Роман Хорин - "Трансформация денег"
- 15:40-16:00: Софие Ле - Тема уточняется
- 16:00-16:20: Дмитрий Саксонов - "Blockchain sports ecosystem"
- 16:20-16:40: Света Малинина - "Законодательство и криптовалюты в 2025"
- 16:40-17:00: Павел Андреев - "WEB 3.0, CeDeFI"
- 17:00-17:20: Павел Савич - "Структурные продукты на рынке криптовалют"
- 17:20-17:40: Тимофей Дайнович и Алексей Гурин - "Секреты медийного успеха"
- 17:40-18:00: Андрей Соколов - "Развитие экосистемы TON"

ФИНАЛ:
18:00-19:30: СТАРТАП-СЕССИЯ
19:30: ПОДВЕДЕНИЕ ИТОГОВ

При ответах на вопросы:
1. Будь энергичным и позитивным
2. Подчеркивай уникальность каждого спикера и его темы
3. Можешь шутить и использовать эмодзи
4. Если спрашивают про конкретное время - давай точную информацию из расписания
5. Упоминай о специальных мероприятиях: шоу пришельцев, шоу полиграф и выставке Лизы Сотилис
6. Всегда напоминай, что больше информации можно найти на сайте https://blockchainworld.by/
7. Если не знаешь деталей, которых нет в расписании - честно говори об этом и предлагай связаться с организаторами

Твоя задача - вызвать у людей желание посетить конференцию, подчеркивая разнообразие тем и компетентность спикеров!"""


# Обновлённая функция получения ответа от GPT
async def get_gpt_response(prompt, is_crypto=False):
    try:
        messages = []

        if is_crypto:
            # Для крипто-запросов сначала ищем актуальную информацию
            search_results = await search_crypto_info(prompt)

            # Формируем контекст из результатов поиска
            if search_results:
                search_context = "Based on latest search results:\n"
                for result in search_results:
                    search_context += f"- {result['title']}\n{result['snippet']}\nSource: {result['link']}\n\n"
                messages = [
                    {"role": "system", "content": CRYPTO_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Search results: {search_context}\n\nUser question: {prompt}"}
                ]
            else:
                messages = [
                    {"role": "system", "content": CRYPTO_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
        else:
            # Для вопросов о конференции используем стандартный промт
            messages = [
                {"role": "system", "content": CONFERENCE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error in GPT request: {e}")
        return "Упс! Что-то пошло не так! Но не парься, бывает 😅 Давай попробуем еще раз?"


# Обработчик команды /start
@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    # Сохраняем данные пользователя
    await save_user_data(message.from_user)

    await message.reply(
        "👋 Йоу! Я твой криптобот с характером!\n"
        "Выбирай, что тебя интересует, и погнали 🚀",
        reply_markup=get_main_keyboard()
    )


# Обработчик callback кнопок
@dp.callback_query()
async def handle_callback(callback_query: types.CallbackQuery):
    if callback_query.data == "crypto_chat":
        await callback_query.message.answer(
            "Режим криптоэксперта активирован! 🤖\n"
            "Давай обсудим крипту, блокчейн или как очередной токен полетел на луну! 🚀"
        )
    elif callback_query.data == "conference_info":
        await callback_query.message.answer(
            "О да, наша конференция! 📅\n"
            "Спрашивай все, что хочешь знать о самом крутом крипто-событии!"
        )
    elif callback_query.data == "contact_us":
        contact_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Telegram", url="https://t.me/dmitryutlik")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")]
        ])
        await callback_query.message.answer(
            "Выберите способ связи с нами:",
            reply_markup=contact_keyboard
        )
    elif callback_query.data == "back_to_main":
        await callback_query.message.answer(
            "Вернулись в главное меню! Что тебя интересует?",
            reply_markup=get_main_keyboard()
        )

    await callback_query.answer()


# Обработчик текстовых сообщений
@dp.message()
async def handle_text(message: types.Message):
    if not message.text:
        return

    # Определяем контекст на основе последнего сообщения
    is_crypto = "конференц" not in message.text.lower()

    # Получаем ответ от GPT
    response = await get_gpt_response(message.text, is_crypto)

    # Создаем клавиатуру для ответа
    reply_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Вернуться в меню", callback_data="back_to_main")]
    ])

    # Отправляем ответ пользователю
    await message.reply(response, reply_markup=reply_keyboard)


# Функция запуска бота
async def main():
    await dp.start_polling(bot)


# Запуск бота
if __name__ == '__main__':
    asyncio.run(main())
