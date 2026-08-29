import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import re
import pymysql
import schedule
import time
import threading
from datetime import datetime, timedelta
import pytz
import traceback
import os
import sys
import platform
from collections import defaultdict
import uuid
import gc
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ========== НАСТРОЙКИ ==========
TOKEN = "vk1.a.k5WTNSZIHAPb8JVP0BEQoCbPxRgbb-CV8sjYzz4hV2Pf0dceNVG9k3GViS0pRtODldKl-42XZLuEQd42T6oK-iEX7WymP5HrTELjkqwBl2z2lhDlQPUPXs_VuWEbsfcBAPh-XNJKYxIr4oAhGLQhIJsvZfjqD3JKqVaxvYs8DffFZwkDaMPyY5fu4A3GZOcQJ7JRnj5cT59SW7C7VtQboA"
GROUP_ID = "237645354"
MAINTENANCE_ADMINS = [548205491]
DEV_USER_ID = 548205491

STAFF_CHAT_ID = 2000000001
STAFF_GAI_CHAT_ID = 2000000010
STAFF_VCH_CHAT_ID = 2000000011

ORG_CHATS = {
    STAFF_CHAT_ID: 'FSIN',
    STAFF_GAI_CHAT_ID: 'TEST',
    STAFF_VCH_CHAT_ID: 'VCH'
}

CHAT_ID_BY_ORG = {v: k for k, v in ORG_CHATS.items()}

ORG_NAMES = {
    'FSIN': 'ФСИН',
    'GAI': 'ТЕСТОВАЯ ВЕТКА (РАЗРАБ)',
    'VCH': 'ВЧ'
}

ORG_ALLOWED = {
    'FSIN': True,
    'GAI': False,
    'VCH': False
}

REMINDER_TIMES = ["14:00", "14:30"]

# ========== ДАННЫЕ GIGACHAT ==========
GIGA_CLIENT_SECRET_B64 = "MDE5ZWZmMDktZjc2NC03MWFiLTk2YjgtY2YwZTcwMjhiNTcxOjBkZmRjN2U4LTk2YjQtNDdiNS1hYjdmLTVlMmY5ZTFkNDJkYg=="
GIGA_CLIENT_ID = "019eff09-f764-71ab-96b8-cf0e7028b571"

# ========== БАЗА ДАННЫХ ==========
DB_HOST = "bpnsjupqnrsnfbdkpag7-mysql.services.clever-cloud.com"
DB_PORT = 3306
DB_NAME = "bpnsjupqnrsnfbdkpag7"
DB_USER = "ucdennlmuxfhwhmf"
DB_PASSWORD = "iyhORGLPfCNVMYkn5VCb"

# ========== VK API ==========
vk_session = vk_api.VkApi(token=TOKEN, api_version='5.131')
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

# ========== ВРЕМЕННЫЕ ХРАНИЛИЩА ==========
pending_confirmations = {}
pending_attachments = {}
pending_complaint_text = {}
pending_rating = {}
pending_rclear = {}
pending_organization = {}
pending_org_redirect = {}
pending_anonymous = {}
pending_anonymous_flag = {}
pending_extra_question = {}
pending_suggestions = {}

user_complaint_times = defaultdict(list)
user_blocked_until = {}

bot_start_time = datetime.now()
last_error = None
last_overdue_check = defaultdict(lambda: datetime.min)
global_maintenance = False

antislip_enabled = True
ANTISLIP_EXEMPT_ADMINS = [548205491]
antislip_warnings = {}

moderation_activity = defaultdict(list)
frozen_admins = {}

blacklist = set()
user_blacklist_info = {}
pending_amnesty = {}
user_amnesty_cooldown = {}

BAD_WORDS = [
    'хуй', 'хуесос', 'хуйло', 'хуеплёт', 'хуйня', 'хуёвый',
    'пизда', 'пиздец', 'пиздабол', 'пиздюк', 'пизданутый',
    'ебать', 'ебало', 'еблан', 'ебанутый', 'ёб твою мать', 'ёб', 'заебал', 'заебало',
    'блядь', 'бля', 'блядина', 'блядский',
    'сука', 'сучара', 'сукин сын',
    'пидор', 'пидарас', 'пидрила', 'пидрильный',
    'мудак', 'мудила', 'мудачина',
    'гандон', 'гондон', 'чмо', 'чмошник', 'лох', 'лошара', 'чертила',
    'урод', 'уродина', 'дебил', 'дебилоид', 'даун', 'аутист',
    'шлюха', 'проститутка', 'блядища',
    'жопа', 'жополиз', 'говно', 'говнюк', 'дерьмо', 'дерьмоед',
    'сволочь', 'сволота', 'гнида', 'падла', 'падлюка',
    'козёл', 'козлина', 'баран', 'тупица', 'идиот', 'идиотка',
    'кретин', 'полудурок', 'отморозок', 'ублюдок', 'недоумок',
    'мразь', 'мразота', 'тварь', 'тварюга', 'скотина',
    'чурка', 'чурбан', 'хачик', 'хач', 'жид', 'жидовская морда', 'черножопый',
    'нигер', 'косоглазый', 'узкоглазый',
    'жирный', 'жиртрест', 'толстуха', 'уродливый', 'рожа', 'морда',
    'кривой', 'косой', 'лысый', 'плешивый',
    'тряпка', 'слабак', 'ничтожество', 'бесполезный',
    'продажная шкура', 'шестёрка',
    'нахер', 'пошел на хутор', 'иди на хрен', 'иди в баню',
]

def normalize_text(text):
    text = text.lower()
    text = text.replace('0', 'о').replace('3', 'з').replace('4', 'ч').replace('6', 'б')
    text = text.replace('1', 'и').replace('2', 'з').replace('5', 'с').replace('7', 'т')
    text = text.replace('8', 'в').replace('9', 'д')
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    return text

def contains_bad_words(text):
    normalized = normalize_text(text)
    for word in BAD_WORDS:
        pattern = r'(?<![а-яё])' + re.escape(word) + r'(?![а-яё])'
        if re.search(pattern, normalized):
            return True
    return False

EXTRA_QUESTIONS = [
    "Укажите дату инцидента (в любом формате):",
    "Укажите подразделение или место происшествия:",
    "Были ли свидетели? Если да, укажите их имена:",
    "Опишите последствия инцидента:"
]

user_bot_msg_ids = defaultdict(list)
user_notifications_disabled = set()
draft_sessions = {}
user_unsent_ratings = defaultdict(list)
pending_bug_reports = {}

admin_disabled_chats = set()
pending_admin_confirm = {}

# ========== ГЛОБАЛЬНЫЕ СЧЁТЧИКИ ==========
command_stats = defaultdict(int)
event_counter = 0
last_errors = []
last_events_ts = []
db_integrity_cache = {'time': datetime.min, 'result': None}
last_longpoll_info = {'ts': 0, 'last_event_time': datetime.min, 'key_age': 0, 'server_age': 0}

# ========== AI AGENT CONFIG ==========
AI_COMPLAINT_PROMPT = """Ты — AMZ GREEN | Жалобная книга. Ты помогаешь принимать обращения. Никогда не говори, что ты GigaChat, Сбер или любая другая модель. Если тебя спрашивают, кто ты, отвечай: «Я AMZ GREEN | Жалобная книга. Мой разработчик — Михаил Храмцов».
Твоя задача — мягко выяснить у гражданина суть проблемы, в какую организацию подать (ФСИН, ГАИ, ВЧ), желает ли он остаться анонимным. Затем задай уточняющие вопросы: дата инцидента, место, свидетели, последствия. Предложи приложить фото/документы. Не задавай больше одного вопроса за раз. Когда всё выяснишь — выведи итоговый текст жалобы и спроси «Всё верно? Отправляем?»"""

AI_FAQ_PROMPT = """Ты — AMZ GREEN | Жалобная книга. Ты консультируешь пользователей по функционалу бота и помогаешь с жалобами. Никогда не говори, что ты GigaChat, Сбер или любая другая модель. На вопросы о себе отвечай: «Я AMZ GREEN | Жалобная книга. Мой разработчик — Михаил Храмцов».

Ты можешь рассказывать пользователям только об этих возможностях бота (обычные пользователи, не сотрудники):
- 📝 Подать жалобу — запуск стандартной формы подачи обращения.
- 🤖 Умный помощник — ИИ-ассистент, который в диалоге помогает собрать и отправить жалобу.
- 📋 Мои жалобы — просмотр списка своих поданных жалоб (команда #мои).
- ⭐ Оценить — оценка работы сотрудника по пятибалльной шкале после закрытия жалобы (#оценить).
- ❓ Задать вопрос — консультация по регламенту, статусам жалоб, срокам и т.д.
- ❓ Помощь — краткая инструкция по использованию бота (/help).
- 🐞 Сообщить о баге — отправка сообщения разработчику (/bug).
- #отозвать — отзыв своей активной жалобы.
- #ответ — отправить сообщение сотруднику по отработанной жалобе.
- #сотрудник — задать вопрос по отработанной жалобе.
- #добавить — добавить уточнение к своей жалобе, пока она не отработана.
- #уведомления вкл / #уведомления выкл — управление автоматическими уведомлениями.
- #очистить — удалить историю диалога с ботом.

О сроках, регламенте, статусах жалоб, а также о трудоустройстве во ФСИН (критерии, звания, зарплаты, график, задачи, адрес) ты знаешь и можешь отвечать развёрнуто.

Никогда, ни при каких обстоятельствах не упоминай команды администраторов и сотрудников: /ahelp, /fsin, /gai, /vch, /blacklist, /unblacklist, /rreset, /rset, /radd, /rcheck, /rdelete, /rclear, /unspam, /antislip, /undo, /modlog, /unfreeze, /userinfo, /resetuser, /stats, /allcomplaints, /restart, /reminder, /adminmode, /resetcomplaints, /aitest, /aistats, /notify, /testconfirm, #взять, #отработал, #передать, #связь, #логи, #рейтинг, #досье, #жалоба. Если пользователь спрашивает о них, просто скажи: «Это служебные функции, для получения информации обратитесь к администратору». Не объясняй их работу.

При необходимости ты можешь выполнить действия:
- Оценить жалобу: [ACTION:rate complaint_id=номер rating=оценка]
- Отозвать жалобу: [ACTION:revoke complaint_id=номер]
Делай это только когда пользователь явно просит и жалоба принадлежит ему. В ответе пиши сначала результат действия, а затем пояснения.

Ниже тебе будет предоставлена сводка по жалобам пользователя и (при необходимости) подробная информация о конкретной жалобе. Используй эти данные для ответа."""

pending_ai_complaint = {}
pending_ai_faq = {}

# ========== GIGACHAT ==========
_gigachat_token = None
_gigachat_token_expires = 0

# Счётчики для /aistats
ai_requests_today = 0
ai_tokens_today = 0
ai_last_reset_date = datetime.now().date()

def is_night_time():
    msk = pytz.timezone('Europe/Moscow')
    now = datetime.now(msk)
    return now.hour >= 22 or now.hour < 8

def _ensure_token():
    global _gigachat_token, _gigachat_token_expires
    if _gigachat_token and time.time() < _gigachat_token_expires - 60:
        return _gigachat_token

    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Authorization": f"Basic {GIGA_CLIENT_SECRET_B64}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = "grant_type=client_credentials&scope=GIGACHAT_API_PERS"

    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, data=data, timeout=10, verify=False)
            if resp.status_code == 429:
                print("429 Too Many Requests, ждём 30 секунд...")
                time.sleep(30)
                continue
            resp.raise_for_status()
            token_data = resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise Exception("access_token not found")
            expires_in = token_data.get("expires_in", 1800)
            _gigachat_token = access_token
            _gigachat_token_expires = time.time() + int(expires_in) - 60
            print(f"GigaChat token obtained, expires in {expires_in}s")
            return _gigachat_token
        except Exception as e:
            print(f"OAuth error: {e}")
            if attempt == 2:
                return None
            time.sleep(10)
    return None

def ask_gigachat(messages, model="GigaChat", temperature=0.7, max_tokens=1000):
    global ai_requests_today, ai_tokens_today, ai_last_reset_date
    # Сброс суточных счётчиков
    today = datetime.now().date()
    if today != ai_last_reset_date:
        ai_requests_today = 0
        ai_tokens_today = 0
        ai_last_reset_date = today

    token = _ensure_token()
    if not token:
        return None

    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    for retry in range(2):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)
            if resp.status_code == 401:
                print("GigaChat 401, сбрасываем токен и пробуем обновить")
                global _gigachat_token, _gigachat_token_expires
                _gigachat_token = None
                _gigachat_token_expires = 0
                new_token = _ensure_token()
                if new_token:
                    headers["Authorization"] = f"Bearer {new_token}"
                    continue
                else:
                    return None
            if resp.status_code != 200:
                print(f"GigaChat API error {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            data = resp.json()
            # Обновляем счётчики
            ai_requests_today += 1
            usage = data.get("usage", {})
            tokens = usage.get("total_tokens", 0)
            if tokens == 0:
                # Примерная оценка, если API не вернуло usage
                prompt_len = sum(len(m["content"]) for m in messages)
                answer_len = len(data["choices"][0]["message"]["content"])
                tokens = (prompt_len + answer_len) // 4
            ai_tokens_today += tokens
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"GigaChat API exception: {e}")
            return None
    return None

def generate_confirm_key():
    return str(uuid.uuid4())[:8]

def mention(user_id):
    try:
        user = vk.users.get(user_ids=user_id, fields=['first_name', 'last_name'])
        if user:
            return f"[id{user_id}|{user[0]['first_name']} {user[0]['last_name']}]"
    except:
        pass
    return f"[id{user_id}|id{user_id}]"

def is_group_admin(user_id):
    try:
        managers = vk.groups.getMembers(group_id=GROUP_ID, filter='managers')
        for m in managers['items']:
            if m['id'] == user_id:
                return True
        return False
    except Exception:
        return False

def check_spam(user_id):
    now = datetime.now()
    if user_id in user_complaint_times:
        user_complaint_times[user_id] = [t for t in user_complaint_times[user_id] if now - t < timedelta(hours=1)]
    if user_id in user_blocked_until:
        if now < user_blocked_until[user_id]:
            return True
        else:
            del user_blocked_until[user_id]
    if len(user_complaint_times.get(user_id, [])) > 2:
        user_blocked_until[user_id] = now + timedelta(hours=1)
        return True
    return False

def add_complaint_time(user_id):
    user_complaint_times[user_id].append(datetime.now())

def remove_spam_block(user_id):
    if user_id in user_blocked_until:
        del user_blocked_until[user_id]
    if user_id in user_complaint_times:
        del user_complaint_times[user_id]

def get_allowed_orgs():
    return [k for k, v in ORG_ALLOWED.items() if v]

def get_allowed_org_names():
    return [ORG_NAMES[k] for k in get_allowed_orgs()]

def save_draft(user_id):
    data = {}
    if user_id in pending_organization:
        data['organization'] = pending_organization[user_id]
    if user_id in pending_anonymous_flag:
        data['anonymous'] = pending_anonymous_flag[user_id]
    if user_id in pending_complaint_text:
        data['complaint_text'] = pending_complaint_text[user_id]
    if user_id in pending_attachments:
        data['attachments'] = pending_attachments[user_id][:10]
    if user_id in pending_extra_question:
        data['extra'] = pending_extra_question[user_id]
    if user_id in pending_confirmations:
        data['confirm_text'] = pending_confirmations[user_id]
    if data:
        draft_sessions[user_id] = {'data': data, 'timestamp': datetime.now()}

def reset_user_state(user_id):
    save_draft(user_id)
    for d in (pending_confirmations, pending_attachments, pending_complaint_text,
              pending_rating, pending_organization, pending_org_redirect, pending_anonymous,
              pending_extra_question):
        d.pop(user_id, None)
    pending_anonymous_flag.pop(user_id, None)

def load_draft(user_id):
    if user_id in draft_sessions:
        draft = draft_sessions[user_id]
        if datetime.now() - draft['timestamp'] < timedelta(hours=1):
            return draft['data']
        else:
            del draft_sessions[user_id]
    return None

def send_message(peer_id, message, keyboard=None):
    try:
        params = {
            'peer_id': peer_id,
            'message': message,
            'random_id': get_random_id()
        }
        if keyboard:
            params['keyboard'] = keyboard.get_keyboard()
        resp = vk.messages.send(**params)
        return resp
    except Exception as e:
        last_errors.append({'time': datetime.now(), 'msg': str(e)})
        if len(last_errors) > 5:
            last_errors.pop(0)
        print(f"Send error: {e}")
        return 0

def send_user_message(user_id, message, keyboard=None, save_msg=True):
    if user_id in user_notifications_disabled and keyboard is None:
        return 0
    msg_id = send_message(user_id, message, keyboard)
    if save_msg and msg_id:
        user_bot_msg_ids[user_id].append(msg_id)
        if len(user_bot_msg_ids[user_id]) > 50:
            user_bot_msg_ids[user_id] = user_bot_msg_ids[user_id][-50:]
    return msg_id

# ===== КЛАВИАТУРЫ =====
def main_menu_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📝 Подать жалобу", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🤖 Умный помощник", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("📋 Мои жалобы", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("❓ Задать вопрос", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("⭐ Оценить", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("❓ Помощь", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("🐞 Сообщить о баге", color=VkKeyboardColor.NEGATIVE)
    return keyboard

def help_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("🐞 Сообщить о баге", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_openlink_button("👨‍💻 Написать разработчику", "https://vk.com/alpha62")
    keyboard.add_line()
    keyboard.add_button("↩️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def yes_no_back_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Да", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("Нет", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("↩️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def back_only_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("↩️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def attachments_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Готово", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("↩️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def org_select_keyboard(allowed_orgs):
    keyboard = VkKeyboard(one_time=True)
    for org_key in allowed_orgs:
        keyboard.add_button(ORG_NAMES[org_key], color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("↩️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def confirm_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Подтверждаю", color=VkKeyboardColor.POSITIVE)
    return keyboard

def amnesty_request_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Написать амнистию", color=VkKeyboardColor.POSITIVE)
    return keyboard

def amnesty_decision_keyboard(user_id):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(f"/amnesty accept {user_id}", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button(f"/amnesty reject {user_id}", color=VkKeyboardColor.NEGATIVE)
    return keyboard

def agreement_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_openlink_button("📄 Ознакомиться", "https://vk.cc/cYEEtR")
    keyboard.add_line()
    keyboard.add_button("✅ Я принимаю условия", color=VkKeyboardColor.POSITIVE)
    return keyboard

def clear_user_dialog(user_id):
    ids = user_bot_msg_ids.get(user_id, [])
    if ids:
        try:
            vk.messages.delete(message_ids=ids, delete_for_all=1)
        except:
            pass
        user_bot_msg_ids[user_id] = []
        send_user_message(user_id, "🧹 История диалога очищена.", save_msg=False)
    else:
        send_user_message(user_id, "ℹ️ Нет сообщений для очистки.", save_msg=False)

def extract_attachments(msg):
    attachments = []
    for att in msg.get('attachments', []):
        if att['type'] == 'photo':
            url = att['photo']['sizes'][-1]['url']
            attachments.append({'url': url, 'type': 'photo'})
        elif att['type'] == 'doc':
            url = att['doc']['url']
            attachments.append({'url': url, 'type': 'doc'})
        elif att['type'] == 'video':
            owner_id = att['video']['owner_id']
            video_id = att['video']['id']
            url = f"https://vk.com/video{owner_id}_{video_id}"
            attachments.append({'url': url, 'type': 'video'})
        elif att['type'] == 'video_message':
            url = att['video_message'].get('link_mp4') or att['video_message'].get('link_ogg')
            if url:
                attachments.append({'url': url, 'type': 'video_message'})
    return attachments

# ===== БАЗА ДАННЫХ =====
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME,
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            user_message TEXT NOT NULL,
            extra_answers TEXT,
            organization VARCHAR(10) NOT NULL DEFAULT 'FSIN',
            anonymous TINYINT(1) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'новая',
            assigned_staff_id BIGINT NULL,
            rating TINYINT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_org (organization)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    for col, dtype in [
        ('rating', 'TINYINT NULL'),
        ('organization', "VARCHAR(10) NOT NULL DEFAULT 'FSIN'"),
        ('anonymous', 'TINYINT(1) DEFAULT 0'),
        ('extra_answers', 'TEXT')
    ]:
        try:
            cur.execute(f"ALTER TABLE complaints ADD COLUMN {col} {dtype}")
        except pymysql.err.OperationalError:
            pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaint_attachments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            complaint_id INT NOT NULL,
            url VARCHAR(500) NOT NULL,
            type VARCHAR(10) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nicknames (
            user_id BIGINT NOT NULL,
            chat_peer_id BIGINT NOT NULL,
            nickname VARCHAR(100) NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, chat_peer_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaint_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            complaint_id INT NOT NULL,
            staff_id BIGINT NOT NULL,
            action VARCHAR(20) NOT NULL,
            action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mod_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            peer_id BIGINT NOT NULL,
            action VARCHAR(20) NOT NULL,
            initiator_id BIGINT NOT NULL,
            target_id BIGINT NOT NULL,
            extra_info VARCHAR(20) NULL,
            action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_agreements (
            user_id BIGINT PRIMARY KEY,
            agreed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована.")

def add_complaint_db(user_id, user_message, organization='FSIN', anonymous=False, extra_answers=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO complaints (user_id, user_message, organization, anonymous, extra_answers, status) VALUES (%s,%s,%s,%s,%s,'новая')",
        (user_id, user_message, organization, anonymous, extra_answers))
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid

def add_attachment(complaint_id, url, att_type):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO complaint_attachments (complaint_id, url, type) VALUES (%s,%s,%s)",
               (complaint_id, url, att_type))
    conn.commit()
    conn.close()

def set_complaint_rating(complaint_id, rating):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE complaints SET rating = %s WHERE complaint_id = %s", (rating, complaint_id))
    conn.commit()
    conn.close()

def get_complaint(complaint_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, status, assigned_staff_id, organization, anonymous, extra_answers FROM complaints WHERE complaint_id = %s", (complaint_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return (row['user_id'], row['status'], row['assigned_staff_id'], row['organization'], row['anonymous'], row['extra_answers'])
    return None

def update_complaint_status(complaint_id, status, staff_id=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if staff_id is not None:
        cur.execute("UPDATE complaints SET status = %s, assigned_staff_id = %s WHERE complaint_id = %s",
                   (status, staff_id, complaint_id))
    else:
        cur.execute("UPDATE complaints SET status = %s WHERE complaint_id = %s", (status, complaint_id))
    conn.commit()
    conn.close()

def log_complaint_action(complaint_id, staff_id, action):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO complaint_logs (complaint_id, staff_id, action) VALUES (%s,%s,%s)",
                   (complaint_id, staff_id, action))
        conn.commit()
        conn.close()
    except:
        pass

def get_active_complaint_for_staff(staff_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT complaint_id FROM complaints WHERE assigned_staff_id = %s AND status = 'в_работе' LIMIT 1", (staff_id,))
    row = cur.fetchone()
    conn.close()
    return row['complaint_id'] if row else None

def get_last_closed_complaint(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT complaint_id FROM complaints WHERE user_id = %s AND status = 'отработана' ORDER BY complaint_id DESC LIMIT 1", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row['complaint_id'] if row else None

def get_last_complaint_for_staff(staff_id, organization=None):
    conn = get_db_connection()
    cur = conn.cursor()
    query = "SELECT complaint_id FROM complaints WHERE assigned_staff_id = %s AND status = 'отработана'"
    params = [staff_id]
    if organization:
        query += " AND organization = %s"
        params.append(organization)
    query += " ORDER BY complaint_id DESC LIMIT 1"
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row['complaint_id'] if row else None

def get_recent_logs(limit=10, organization=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if organization:
        cur.execute("""
            SELECT l.complaint_id, l.staff_id, l.action, l.action_time
            FROM complaint_logs l
            JOIN complaints c ON l.complaint_id = c.complaint_id
            WHERE c.organization = %s
            ORDER BY l.action_time DESC LIMIT %s
        """, (organization, limit))
    else:
        cur.execute("SELECT l.complaint_id, l.staff_id, l.action, l.action_time FROM complaint_logs l ORDER BY l.action_time DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_staff_ratings(organization=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if organization:
        cur.execute("""
            SELECT assigned_staff_id, SUM(rating) as total_rating, COUNT(*) as cnt
            FROM complaints
            WHERE assigned_staff_id IS NOT NULL AND rating IS NOT NULL AND organization = %s
            GROUP BY assigned_staff_id
            ORDER BY total_rating DESC, cnt DESC
        """, (organization,))
    else:
        cur.execute("""
            SELECT assigned_staff_id, SUM(rating) as total_rating, COUNT(*) as cnt
            FROM complaints
            WHERE assigned_staff_id IS NOT NULL AND rating IS NOT NULL
            GROUP BY assigned_staff_id
            ORDER BY total_rating DESC, cnt DESC
        """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_staff_rating_info(staff_id, organization=None):
    conn = get_db_connection()
    cur = conn.cursor()
    query = "SELECT SUM(rating) as total_rating, COUNT(*) as cnt FROM complaints WHERE assigned_staff_id = %s AND rating IS NOT NULL"
    params = [staff_id]
    if organization:
        query += " AND organization = %s"
        params.append(organization)
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row

def get_staff_stats(staff_id, organization=None):
    stats = {'closed':0, 'in_work':0, 'total_rating':0, 'rating_count':0, 'last_activity':None}
    conn = get_db_connection()
    cur = conn.cursor()
    org_filter = f"AND organization = '{organization}'" if organization else ""
    cur.execute(f"SELECT COUNT(*) as cnt FROM complaints WHERE assigned_staff_id = %s AND status = 'отработана' {org_filter}", (staff_id,))
    stats['closed'] = cur.fetchone()['cnt']
    cur.execute(f"SELECT COUNT(*) as cnt FROM complaints WHERE assigned_staff_id = %s AND status = 'в_работе' {org_filter}", (staff_id,))
    stats['in_work'] = cur.fetchone()['cnt']
    cur.execute(f"SELECT SUM(rating) as total_rating, COUNT(*) as cnt FROM complaints WHERE assigned_staff_id = %s AND rating IS NOT NULL {org_filter}", (staff_id,))
    row = cur.fetchone()
    if row and row['cnt'] > 0:
        stats['total_rating'] = row['total_rating'] or 0
        stats['rating_count'] = row['cnt']
    cur.execute(f"SELECT action_time FROM complaint_logs WHERE staff_id = %s ORDER BY action_time DESC LIMIT 1", (staff_id,))
    row = cur.fetchone()
    if row:
        stats['last_activity'] = row['action_time']
    conn.close()
    return stats

def get_open_complaints(organization=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if organization:
        cur.execute("SELECT complaint_id, user_id, status, assigned_staff_id, anonymous FROM complaints WHERE status IN ('новая','в_работе') AND organization = %s ORDER BY created_at DESC", (organization,))
    else:
        cur.execute("SELECT complaint_id, user_id, status, assigned_staff_id, anonymous FROM complaints WHERE status IN ('новая','в_работе') ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def reset_staff_ratings(staff_id, organization=None):
    conn = get_db_connection()
    cur = conn.cursor()
    query = "UPDATE complaints SET rating = NULL WHERE assigned_staff_id = %s AND rating IS NOT NULL"
    params = [staff_id]
    if organization:
        query += " AND organization = %s"
        params.append(organization)
    cur.execute(query, params)
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected

def set_last_rating_for_staff(staff_id, rating, organization=None):
    cid = get_last_complaint_for_staff(staff_id, organization)
    if not cid: return None
    set_complaint_rating(cid, rating)
    return cid

def award_rating(staff_id, rating, organization):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO complaints (user_id, user_message, organization, status, assigned_staff_id, rating) VALUES (0,'Поощрительная оценка',%s,'отработана',%s,%s)",
               (organization, staff_id, rating))
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid

def delete_complaint_rating(complaint_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE complaints SET rating = NULL WHERE complaint_id = %s", (complaint_id,))
    conn.commit()
    conn.close()
    return True

def clear_all_ratings(organization=None):
    conn = get_db_connection()
    cur = conn.cursor()
    if organization:
        cur.execute("UPDATE complaints SET rating = NULL WHERE rating IS NOT NULL AND organization = %s", (organization,))
    else:
        cur.execute("UPDATE complaints SET rating = NULL WHERE rating IS NOT NULL")
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected

def is_user_blacklisted(user_id):
    return user_id in blacklist

def get_user_complaints(user_id, limit=10):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT complaint_id, organization, status, created_at, rating FROM complaints WHERE user_id = %s ORDER BY created_at DESC LIMIT %s", (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_all_complaints(organization=None, status=None, limit=20):
    conn = get_db_connection()
    cur = conn.cursor()
    query = "SELECT complaint_id, user_id, organization, status, assigned_staff_id, created_at FROM complaints WHERE 1=1"
    params = []
    if organization:
        query += " AND organization = %s"
        params.append(organization)
    if status:
        query += " AND status = %s"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def is_agreement_accepted(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM user_agreements WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        conn.close()
        return row is not None
    except:
        return False

def accept_agreement(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT IGNORE INTO user_agreements (user_id) VALUES (%s)", (user_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# ===== НАПОМИНАНИЯ =====
def send_reminder():
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
    for chat_id in ORG_CHATS:
        send_message(chat_id, f"⏰ Напоминание! Не забудьте провести плановую проверку личного состава. ({now.strftime('%H:%M %d.%m.%Y')})")

def setup_schedule():
    schedule.clear()
    days = [
        schedule.every().monday,
        schedule.every().wednesday,
        schedule.every().friday,
        schedule.every().sunday
    ]
    for t in REMINDER_TIMES:
        for day_func in days:
            day_func.at(t).do(send_reminder)
    schedule.every().monday.at("09:00").do(weekly_report)

def check_overdue_complaints():
    global last_overdue_check
    now = datetime.now()
    for org_key in ORG_CHATS.values():
        if now - last_overdue_check[org_key] < timedelta(hours=6):
            continue
        last_overdue_check[org_key] = now
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT complaint_id, assigned_staff_id FROM complaints WHERE status = 'в_работе' AND created_at < DATE_SUB(NOW(), INTERVAL 1 DAY) AND organization = %s", (org_key,))
            overdue = cur.fetchall()
            conn.close()
            chat_id = CHAT_ID_BY_ORG.get(org_key)
            if not chat_id:
                continue
            for c in overdue:
                staff_id = c['assigned_staff_id']
                if not staff_id: continue
                send_message(staff_id, f"⏰ Напоминание! Жалоба #{c['complaint_id']} ({ORG_NAMES[org_key]}) не отработана уже более суток.")
                send_message(chat_id, f"⏰ {mention(staff_id)}, ваша жалоба #{c['complaint_id']} (просрочена более 24ч).")
        except:
            pass

def run_scheduler():
    schedule.every(6).hours.do(check_overdue_complaints)
    check_overdue_complaints()
    while True:
        schedule.run_pending()
        time.sleep(30)

def weekly_report():
    msk = pytz.timezone('Europe/Moscow')
    now = datetime.now(msk)
    week_ago = now - timedelta(days=7)
    for org_key, chat_id in CHAT_ID_BY_ORG.items():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as cnt FROM complaints WHERE created_at >= %s AND organization = %s", (week_ago, org_key))
            new_cnt = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(DISTINCT l.complaint_id) as cnt FROM complaint_logs l JOIN complaints c ON l.complaint_id=c.complaint_id WHERE l.action='close' AND l.action_time>=%s AND c.organization=%s", (week_ago, org_key))
            closed_cnt = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) as cnt FROM complaints WHERE status = 'в_работе' AND organization = %s", (org_key,))
            in_work = cur.fetchone()['cnt']
            cur.execute("SELECT AVG(rating) as avg_rating FROM complaints WHERE rating IS NOT NULL AND created_at >= %s AND organization = %s", (week_ago, org_key))
            avg_rating = cur.fetchone()['avg_rating']
            cur.execute("""
                SELECT c.assigned_staff_id, COUNT(*) as cnt
                FROM complaints c
                JOIN complaint_logs l ON c.complaint_id = l.complaint_id AND l.action = 'close'
                WHERE l.action_time >= %s AND c.organization = %s AND c.assigned_staff_id IS NOT NULL
                GROUP BY c.assigned_staff_id
                ORDER BY cnt DESC LIMIT 3
            """, (week_ago, org_key))
            top = cur.fetchall()
            cur.execute("""
                SELECT c.complaint_id, TIMESTAMPDIFF(MINUTE, c.created_at, MIN(l.action_time)) as diff
                FROM complaints c
                JOIN complaint_logs l ON c.complaint_id = l.complaint_id AND l.action = 'close'
                WHERE l.action_time >= %s AND c.organization = %s
                GROUP BY c.complaint_id
                ORDER BY diff ASC LIMIT 1
            """, (week_ago, org_key))
            record = cur.fetchone()
            conn.close()
            lines = [f"📊 Еженедельный отчёт ({ORG_NAMES[org_key]})", "─" * 25]
            lines.append(f"🆕 Новых: {new_cnt}")
            lines.append(f"✅ Отработано: {closed_cnt}")
            lines.append(f"🔄 В работе: {in_work}")
            if avg_rating:
                lines.append(f"⭐ Средняя оценка: {avg_rating:.1f} / 5")
            if top:
                lines.append("🏆 Топ-3 по закрытым:")
                for i,t in enumerate(top,1):
                    lines.append(f"{i}. {mention(t['assigned_staff_id'])} — {t['cnt']} шт.")
            if record:
                lines.append(f"🚀 Рекорд скорости: #{record['complaint_id']} ({record['diff']} мин.)")
            if new_cnt == 0:
                lines.insert(1, "😴 Неделя прошла спокойно.")
            send_message(chat_id, "\n".join(lines))
        except Exception as e:
            print(f"Ошибка отчёта {org_key}: {e}")

def notify_rating(complaint_id, rating, org):
    comp = get_complaint(complaint_id)
    if not comp: return
    user_id, _, staff_id, _, _, _ = comp
    if not staff_id: return
    chat_id = CHAT_ID_BY_ORG.get(org)
    if not chat_id: return
    if rating <= 2:
        reaction = f"😡 {mention(user_id)} поставил низкую оценку ({rating}) за жалобу #{complaint_id} сотруднику {mention(staff_id)}."
    elif rating == 3:
        reaction = f"😐 {mention(user_id)} поставил нейтральную оценку ({rating}) за жалобу #{complaint_id} сотруднику {mention(staff_id)}."
    else:
        reaction = f"🌟 Отличная работа! {mention(user_id)} оценил вашу работу на {rating} за жалобу #{complaint_id}, {mention(staff_id)}!"
    send_message(chat_id, reaction)

# ===== МОДЕРАЦИЯ =====
def get_chat_admins(peer_id):
    try:
        members = vk.messages.getConversationMembers(peer_id=peer_id)
        return [m['member_id'] for m in members['items'] if m.get('is_admin') or m.get('is_owner')]
    except:
        return []

def is_user_admin(peer_id, user_id):
    return user_id in get_chat_admins(peer_id)

def extract_id_from_mention(text):
    match = re.search(r'\[id(\d+)\|.*?\]', text)
    if match: return int(match.group(1))
    match = re.search(r'(\d+)', text)
    if match: return int(match.group(1))
    return None

def is_moderation_frozen(user_id):
    if user_id in frozen_admins:
        if datetime.now() < frozen_admins[user_id]:
            return True
        else:
            del frozen_admins[user_id]
    return False

def check_moderation_rate(user_id):
    now = datetime.now()
    if user_id in moderation_activity:
        moderation_activity[user_id] = [t for t in moderation_activity[user_id] if now - t < timedelta(minutes=5)]
    moderation_activity[user_id].append(now)
    if len(moderation_activity[user_id]) > 3:
        frozen_admins[user_id] = now + timedelta(minutes=15)
        return True
    return False

def kick_user(peer_id, target_id, initiator_id):
    if is_moderation_frozen(initiator_id):
        send_message(peer_id, f"🚫 Ваши права модератора временно заморожены до {frozen_admins[initiator_id].strftime('%H:%M')}")
        return False
    if not is_user_admin(peer_id, initiator_id):
        send_message(peer_id, "❌ У вас недостаточно прав.")
        return False
    try:
        vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
        log_mod_action(peer_id, 'kick', initiator_id, target_id)
        send_message(peer_id, f"👢 Пользователь {mention(target_id)} исключён.")
        if check_moderation_rate(initiator_id):
            send_message(peer_id, f"⚠️ Превышен лимит модерации. Ваши права заморожены на 15 минут.")
        return True
    except:
        send_message(peer_id, "❌ Не удалось кикнуть.")
        return False

def mute_user(peer_id, target_id, initiator_id, duration=0):
    if is_moderation_frozen(initiator_id):
        send_message(peer_id, f"🚫 Ваши права модератора временно заморожены до {frozen_admins[initiator_id].strftime('%H:%M')}")
        return False
    if not is_user_admin(peer_id, initiator_id):
        send_message(peer_id, "❌ У вас недостаточно прав.")
        return False
    try:
        params = {'peer_id': peer_id, 'member_ids': target_id, 'action': 'ro'}
        if duration > 0: params['for'] = duration
        vk.messages.changeConversationMemberRestrictions(**params)
        dur_str = f"на {duration} сек" if duration else "навсегда"
        send_message(peer_id, f"🔇 {mention(target_id)} заглушён {dur_str}.")
        log_mod_action(peer_id, 'mute', initiator_id, target_id, str(duration) if duration else None)
        if check_moderation_rate(initiator_id):
            send_message(peer_id, f"⚠️ Превышен лимит модерации. Ваши права заморожены на 15 минут.")
        return True
    except:
        send_message(peer_id, "❌ Не удалось замутить.")
        return False

def unmute_user(peer_id, target_id, initiator_id):
    if not is_user_admin(peer_id, initiator_id):
        send_message(peer_id, "❌ У вас недостаточно прав.")
        return False
    try:
        vk.messages.changeConversationMemberRestrictions(peer_id=peer_id, member_ids=target_id, action='rw')
        send_message(peer_id, f"🔊 С {mention(target_id)} снят мут.")
        return True
    except:
        send_message(peer_id, "❌ Не удалось размутить.")
        return False

def ban_user(peer_id, target_id, initiator_id):
    if is_moderation_frozen(initiator_id):
        send_message(peer_id, f"🚫 Ваши права модератора временно заморожены до {frozen_admins[initiator_id].strftime('%H:%M')}")
        return False
    if not is_user_admin(peer_id, initiator_id):
        send_message(peer_id, "❌ У вас недостаточно прав.")
        return False
    try:
        vk.messages.removeChatUser(chat_id=peer_id - 2000000000, user_id=target_id)
        try:
            vk.groups.ban(group_id=GROUP_ID, owner_id=target_id, reason="Нарушение правил")
        except:
            pass
        log_mod_action(peer_id, 'ban', initiator_id, target_id)
        send_message(peer_id, f"🚫 {mention(target_id)} забанен.")
        if check_moderation_rate(initiator_id):
            send_message(peer_id, f"⚠️ Превышен лимит модерации. Ваши права заморожены на 15 минут.")
        return True
    except:
        send_message(peer_id, "❌ Не удалось забанить.")
        return False

def unban_user(peer_id, target_id, initiator_id):
    if not is_user_admin(peer_id, initiator_id):
        send_message(peer_id, "❌ У вас недостаточно прав.")
        return False
    try:
        vk.groups.unban(group_id=GROUP_ID, owner_id=target_id)
        send_message(peer_id, f"✅ {mention(target_id)} разбанен.")
        return True
    except:
        send_message(peer_id, "❌ Не удалось разбанить.")
        return False

def set_admin_role(peer_id, target_id, initiator_id, role='admin'):
    if not is_user_admin(peer_id, initiator_id):
        send_message(peer_id, "❌ У вас недостаточно прав.")
        return False
    try:
        vk.messages.setMemberRole(peer_id=peer_id, member_id=target_id, role=role)
        send_message(peer_id, f"👑 {mention(target_id)} назначен администратором.")
        log_mod_action(peer_id, 'setadmin', initiator_id, target_id)
        return True
    except:
        send_message(peer_id, "❌ Не удалось изменить роль.")
        return False

def remove_admin_role(peer_id, target_id, initiator_id):
    if not is_user_admin(peer_id, initiator_id):
        send_message(peer_id, "❌ У вас недостаточно прав.")
        return False
    admins = get_chat_admins(peer_id)
    if len(admins) <= 1 and target_id in admins:
        send_message(peer_id, "❌ Нельзя снять права с последнего администратора чата.")
        return False
    try:
        vk.messages.setMemberRole(peer_id=peer_id, member_id=target_id, role='member')
        send_message(peer_id, f"⬇️ {mention(target_id)} теперь обычный участник.")
        log_mod_action(peer_id, 'unadmin', initiator_id, target_id)
        return True
    except:
        send_message(peer_id, "❌ Не удалось снять роль.")
        return False

def log_mod_action(peer_id, action, initiator_id, target_id, extra_info=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO mod_logs (peer_id, action, initiator_id, target_id, extra_info) VALUES (%s,%s,%s,%s,%s)",
                   (peer_id, action, initiator_id, target_id, extra_info))
        conn.commit()
        conn.close()
    except:
        pass

def get_last_mod_action(peer_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM mod_logs WHERE peer_id = %s ORDER BY action_time DESC LIMIT 1", (peer_id,))
        row = cur.fetchone()
        conn.close()
        return row
    except:
        return None

def delete_mod_log(log_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM mod_logs WHERE log_id = %s", (log_id,))
        conn.commit()
        conn.close()
    except:
        pass

def get_mod_logs(peer_id, limit=10):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM mod_logs WHERE peer_id = %s ORDER BY action_time DESC LIMIT %s", (peer_id, limit))
        rows = cur.fetchall()
        conn.close()
        return rows
    except:
        return []

def undo_last_action(peer_id, user_id):
    if not is_group_admin(user_id):
        send_message(peer_id, "❌ Недостаточно прав (требуется администратор сообщества).")
        return
    last = get_last_mod_action(peer_id)
    if not last:
        send_message(peer_id, "ℹ️ Нет действий для отката.")
        return
    action, target, log_id = last['action'], last['target_id'], last['log_id']
    try:
        if action in ('kick', 'ban'):
            vk.messages.addChatUser(chat_id=peer_id - 2000000000, user_id=target)
            send_message(peer_id, f"↩️ Откат: пользователь {mention(target)} возвращён в чат.")
        elif action == 'mute':
            vk.messages.changeConversationMemberRestrictions(peer_id=peer_id, member_ids=target, action='rw')
            send_message(peer_id, f"↩️ Откат: мут с {mention(target)} снят.")
        elif action == 'setadmin':
            vk.messages.setMemberRole(peer_id=peer_id, member_id=target, role='member')
            send_message(peer_id, f"↩️ Откат: права администратора с {mention(target)} сняты.")
        elif action == 'unadmin':
            vk.messages.setMemberRole(peer_id=peer_id, member_id=target, role='admin')
            send_message(peer_id, f"↩️ Откат: права администратора {mention(target)} восстановлены.")
        delete_mod_log(log_id)
    except Exception as e:
        send_message(peer_id, f"❌ Не удалось выполнить откат: {e}")

# ===== НИКНЕЙМЫ =====
def set_nickname(peer_id, target_id, nickname, initiator_id):
    if not is_user_admin(peer_id, initiator_id):
        send_message(peer_id, "❌ У вас недостаточно прав.")
        return False
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO nicknames (user_id, chat_peer_id, nickname) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE nickname = VALUES(nickname)",
                   (target_id, peer_id, nickname))
        conn.commit()
        conn.close()
        send_message(peer_id, f"✏️ Для {mention(target_id)} установлен ник: {nickname}")
        return True
    except:
        send_message(peer_id, "❌ Не удалось установить ник.")
        return False

def delete_nickname(peer_id, target_id, initiator_id):
    if not is_user_admin(peer_id, initiator_id):
        send_message(peer_id, "❌ У вас недостаточно прав.")
        return False
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM nicknames WHERE user_id = %s AND chat_peer_id = %s", (target_id, peer_id))
        conn.commit()
        conn.close()
        send_message(peer_id, f"🗑️ Ник для {mention(target_id)} удалён.")
        return True
    except:
        send_message(peer_id, "❌ Не удалось удалить ник.")
        return False

def get_nickname(peer_id, target_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT nickname FROM nicknames WHERE user_id = %s AND chat_peer_id = %s", (target_id, peer_id))
        row = cur.fetchone()
        conn.close()
        if row:
            send_message(peer_id, f"🔖 Ник {mention(target_id)}: {row['nickname']}")
        else:
            send_message(peer_id, f"❓ Для {mention(target_id)} ник не установлен.")
    except:
        pass

def list_nicknames(peer_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, nickname FROM nicknames WHERE chat_peer_id = %s ORDER BY nickname", (peer_id,))
        rows = cur.fetchall()
        conn.close()
        if not rows:
            send_message(peer_id, "📭 Список ников пуст.")
            return
        nick_list = "\n".join([f"• {mention(row['user_id'])} — {row['nickname']}" for row in rows])
        send_message(peer_id, f"📋 Список ников:\n{nick_list}")
    except:
        pass

# ========== ДИАГНОСТИКА ==========
def check_db_integrity():
    global db_integrity_cache
    if datetime.now() - db_integrity_cache['time'] < timedelta(minutes=5):
        return db_integrity_cache['result']
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        issues = []
        cur.execute("SELECT COUNT(*) as cnt FROM complaint_attachments WHERE complaint_id NOT IN (SELECT complaint_id FROM complaints)")
        if cur.fetchone()['cnt'] > 0:
            issues.append(f"аттачментов-сирот")
        cur.execute("SELECT COUNT(*) as cnt FROM complaint_logs WHERE complaint_id NOT IN (SELECT complaint_id FROM complaints)")
        if cur.fetchone()['cnt'] > 0:
            issues.append(f"логов-сирот")
        result = (len(issues) == 0, issues)
        db_integrity_cache = {'time': datetime.now(), 'result': result}
        conn.close()
        return result
    except Exception as e:
        return False, [f"Ошибка проверки: {e}"]

def check_token():
    try:
        vk.users.get(user_ids=[1])
        return True, "Валиден"
    except Exception as e:
        return False, str(e)

def check_chats():
    results = {}
    for name, cid in [('FSIN', STAFF_CHAT_ID), ('GAI', STAFF_GAI_CHAT_ID), ('VCH', STAFF_VCH_CHAT_ID)]:
        try:
            vk.messages.getConversationMembers(peer_id=cid)
            results[name] = True
        except:
            results[name] = False
    return results

def test_message():
    try:
        start = time.time()
        msg_id = vk.messages.send(
            user_id=DEV_USER_ID,
            message="🧪 Тестовое сообщение самодиагностики",
            random_id=get_random_id()
        )
        elapsed = int((time.time() - start) * 1000)
        if msg_id:
            try:
                vk.messages.delete(message_ids=[msg_id], delete_for_all=1)
            except:
                pass
            return True, f"{elapsed} мс"
        return False, "Не отправлено"
    except Exception as e:
        return False, str(e)

def check_longpoll():
    info = last_longpoll_info
    now = datetime.now()
    if info.get('last_event_time'):
        delta = (now - info['last_event_time']).total_seconds()
        if delta > 30:
            return False, f"Событий нет {delta:.0f} сек"
        else:
            return True, f"Активен, посл. событие {delta:.1f} сек назад"
    return False, "Нет данных"

def check_scheduler():
    jobs = schedule.jobs
    if not jobs:
        return False, "Нет задач"
    next_run = schedule.next_run()
    return True, f"Задач: {len(jobs)}, след. {next_run.strftime('%H:%M') if next_run else 'неизвестно'}"

def check_disk():
    if not PSUTIL_AVAILABLE:
        return None, "psutil недоступен"
    try:
        usage = psutil.disk_usage('/')
        free_gb = usage.free / (1024**3)
        percent = usage.percent
        if percent > 85:
            return False, f"Критично: {percent}% ({free_gb:.1f} GB)"
        elif percent > 70:
            return True, f"Внимание: {percent}% ({free_gb:.1f} GB)"
        else:
            return True, f"Норма: {percent}% ({free_gb:.1f} GB)"
    except:
        return None, "Ошибка"

def check_filesystem_write():
    try:
        test_file = "diag_test.tmp"
        with open(test_file, 'w') as f:
            f.write("1")
        os.remove(test_file)
        return True, "OK"
    except:
        return False, "Нет прав"

def run_diagnostics(peer_id, user_id):
    global last_error, event_counter, last_events_ts
    is_dev = user_id in MAINTENANCE_ADMINS
    lines = ["🔍 Полная диагностика бота", "─" * 30]

    uptime = datetime.now() - bot_start_time
    days, remainder = divmod(uptime.seconds, 3600)
    hours, minutes = divmod(remainder, 60)
    lines.append(f"⏱️ Аптайм: {uptime.days}д {hours}ч {minutes}м")
    lines.append(f"🐍 Python: {sys.version.split()[0]} | {platform.system()} {platform.architecture()[0]}")
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process(os.getpid())
            mem = process.memory_info().rss / 1024 / 1024
            cpu = process.cpu_percent(interval=0.5)
            lines.append(f"📊 Память: {mem:.1f} MB | CPU: {cpu:.1f}%")
        except:
            pass
    disk_status, disk_msg = check_disk()
    if disk_status is not None:
        icon = "✅" if disk_status else "⚠️"
        lines.append(f"💾 Диск: {icon} {disk_msg}")

    lines.append("─" * 30)

    diag_items = []
    ok, issues = check_db_integrity()
    if ok:
        diag_items.append("✅ База данных: целостность подтверждена")
    else:
        diag_items.append(f"⚠️ База данных: проблемы ({', '.join(issues)})")
    tok_ok, tok_msg = check_token()
    diag_items.append(f"{'✅' if tok_ok else '❌'} Токен VK: {tok_msg}")
    chats = check_chats()
    all_ok = all(chats.values())
    chat_str = ', '.join([f"{n}: {'✅' if s else '❌'}" for n,s in chats.items()])
    diag_items.append(f"{'✅' if all_ok else '⚠️'} Рабочие чаты: {chat_str}")
    msg_ok, msg_res = test_message()
    diag_items.append(f"{'✅' if msg_ok else '❌'} Тест сообщения: {msg_res}")
    sched_ok, sched_msg = check_scheduler()
    diag_items.append(f"{'✅' if sched_ok else '⚠️'} Планировщик: {sched_msg}")
    lp_ok, lp_msg = check_longpoll()
    diag_items.append(f"{'✅' if lp_ok else '⚠️'} Longpoll: {lp_msg}")
    write_ok, write_msg = check_filesystem_write()
    diag_items.append(f"{'✅' if write_ok else '❌'} Права на запись: {write_msg}")
    if last_errors:
        diag_items.append(f"⚠️ Обнаружено ошибок: {len(last_errors)} (см. ниже)")
    else:
        diag_items.append("✅ Критических ошибок нет")

    lines.append("🧪 Самодиагностика:")
    lines.extend(diag_items)
    lines.append("─" * 30)

    now = datetime.now()
    recent_events = [t for t in last_events_ts if (now - t).total_seconds() < 3600]
    lines.append(f"📬 Последнее событие: {'только что' if recent_events else 'нет данных'} | за час: {len(recent_events)}")
    lines.append(f"🔌 VK API: пинг ~{msg_res if msg_ok else '?'}")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT VERSION() as ver")
        ver = cur.fetchone()['ver']
        conn.close()
        lines.append(f"🗄️ База данных: подключена (MySQL {ver})")
    except:
        lines.append("❌ База данных: ошибка подключения")

    lines.append(f"📂 Активные сессии:")
    lines.append(f"  • Подают жалобу: {len(pending_organization)}")
    lines.append(f"  • Черновиков: {len(draft_sessions)}")
    lines.append(f"  • Ожидают оценки: {len(pending_rating)}")
    lines.append(f"  • Прикрепляют файлы: {len(pending_attachments)}")

    lines.append(f"🛡️ Антислив: {'включён' if antislip_enabled else 'отключен'} | предупреждений: {len(antislip_warnings)}")
    lines.append(f"🚫 Чёрный список: {len(blacklist)} чел.")
    lines.append(f"❄️ Замороженных модераторов: {len(frozen_admins)}")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        for org_key in ORG_NAMES:
            cur.execute("SELECT status, COUNT(*) as cnt FROM complaints WHERE organization = %s GROUP BY status", (org_key,))
            rows = cur.fetchall()
            total = sum(r['cnt'] for r in rows)
            new = next((r['cnt'] for r in rows if r['status']=='новая'), 0)
            in_work = next((r['cnt'] for r in rows if r['status']=='в_работе'), 0)
            lines.append(f"📝 {ORG_NAMES[org_key]}: всего {total} (новых: {new}, в работе: {in_work})")
        conn.close()
    except:
        pass

    if command_stats:
        sorted_cmds = sorted(command_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        cmd_str = ',  '.join([f"{c}: {n}" for c,n in sorted_cmds])
        lines.append(f"📈 Популярные команды: {cmd_str}")
    else:
        lines.append("📈 Популярные команды: (нет данных)")

    lines.append(f"⏰ Планировщик: {sched_msg}")

    if last_errors:
        lines.append("⚠️ Последние ошибки:")
        for i, err in enumerate(last_errors[-3:], 1):
            lines.append(f"  {i}. [{err['time'].strftime('%H:%M')}] {err['msg'][:100]}")

    lines.append("─" * 30)
    lines.append("🟢 Бот работает стабильно" if not last_error else "🟡 Обнаружены проблемы")

    if is_dev:
        lines.append("")
        lines.append("🔬 Низкоуровневая диагностика (только для разработчика)")
        threads = threading.enumerate()
        lines.append(f"🐍 Активных потоков: {len(threads)}")
        for t in threads:
            lines.append(f"   {t.name} (daemon={t.daemon})")
        info = last_longpoll_info
        lines.append(f"📡 Longpoll: key_age={info.get('key_age','?')}с, server_age={info.get('server_age','?')}с, last_ts={info.get('ts','?')}")
        lines.append(f"🗑️ GC generations: {gc.get_count()}, collections: {gc.get_stats()}")
        if PSUTIL_AVAILABLE:
            try:
                mem = process.memory_info()
                lines.append(f"💾 Память: RSS {mem.rss/1024/1024:.1f} MB, VMS {mem.vms/1024/1024:.1f} MB")
                if hasattr(process, 'num_fds'):
                    try:
                        fds = process.num_fds()
                        lines.append(f"📁 Файловых дескрипторов: {fds}")
                    except:
                        pass
                try:
                    conns = process.connections()
                    states = defaultdict(int)
                    for c in conns:
                        states[c.status] += 1
                    lines.append("🌐 Сетевые соединения: " + ", ".join([f"{s}: {n}" for s,n in states.items()]))
                except:
                    pass
            except:
                pass
        lines.append(f"⚠️ Счётчики ошибок (последние): {len(last_errors)} шт.")
        lines.append("🟢 Цикл событий активен" if recent_events else "🔴 Нет событий")
        lines.append("─" * 30)

    return "\n".join(lines)

def count_command(cmd_name):
    command_stats[cmd_name] += 1

# ========== ФИЛЬТР ЗАПРЕЩЁННЫХ КОМАНД ==========
FORBIDDEN_COMMANDS = [
    '/ahelp', '/fsin', '/gai', '/vch', '/blacklist', '/unblacklist',
    '/rreset', '/rset', '/radd', '/rcheck', '/rdelete', '/rclear',
    '/unspam', '/antislip', '/undo', '/modlog', '/unfreeze',
    '/userinfo', '/resetuser', '/stats', '/allcomplaints', '/restart',
    '/reminder', '/adminmode', '/resetcomplaints', '/aitest', '/aistats',
    '/notify', '/testconfirm',
    '#взять', '#отработал', '#передать', '#связь', '#логи', '#рейтинг',
    '#досье', '#жалоба'
]

def censor_ai_response(text):
    """Если ответ содержит запрещённые команды, заменяет его на стандартный отказ."""
    for cmd in FORBIDDEN_COMMANDS:
        if cmd in text:
            return "Извините, я не могу предоставить информацию по этому запросу. Обратитесь к администратору."
    return text

# ========== ИИ-АГЕНТ (НОВЫЕ ФУНКЦИИ) ==========
def execute_action(user_id, action_type, complaint_id, rating=None):
    """Выполняет действие (rate / revoke) с проверкой принадлежности жалобы."""
    complaint = get_complaint(complaint_id)
    if not complaint or complaint[0] != user_id:
        return False, "Жалоба не найдена или не принадлежит вам."
    if action_type == "rate":
        if rating is None or not (1 <= rating <= 5):
            return False, "Некорректная оценка."
        if complaint[1] != "отработана":
            return False, "Оценить можно только отработанную жалобу."
        set_complaint_rating(complaint_id, rating)
        return True, f"Оценка {rating} установлена для жалобы №{complaint_id}."
    elif action_type == "revoke":
        if complaint[1] in ("отработана", "отозвана"):
            return False, f"Жалоба №{complaint_id} уже обработана или отозвана."
        update_complaint_status(complaint_id, "отозвана")
        return True, f"Жалоба №{complaint_id} отозвана."
    return False, "Неизвестное действие."

def process_ai_actions(user_id, ai_response):
    """Извлекает из ответа модели [ACTION:...] и выполняет их. Возвращает чистый ответ."""
    pattern = r'\[ACTION:(rate|revoke)\s+complaint_id=(\d+)(?:\s+rating=(\d))?\]'
    actions = list(re.finditer(pattern, ai_response))
    if not actions:
        return ai_response

    clean_response = ai_response
    for match in reversed(actions):
        action_type = match.group(1)
        complaint_id = int(match.group(2))
        rating = int(match.group(3)) if match.group(3) else None
        success, message = execute_action(user_id, action_type, complaint_id, rating)
        # Удаляем команду из ответа
        clean_response = clean_response[:match.start()] + clean_response[match.end():]
        # Добавляем результат в начало ответа
        prefix = "✅ " + message + "\n" if success else "❌ " + message + "\n"
        clean_response = prefix + clean_response.strip()

    return clean_response.strip()

def start_ai_complaint(user_id):
    pending_ai_complaint[user_id] = {
        'history': [{"role": "system", "content": AI_COMPLAINT_PROMPT}],
        'collected': {},
        'phase': 'collecting',
        'attachments': []
    }
    user_msg = {"role": "user", "content": "Здравствуйте, я хочу подать жалобу. Помогите мне."}
    full_messages = pending_ai_complaint[user_id]['history'] + [user_msg]
    first_msg = ask_gigachat(full_messages)
    if first_msg:
        pending_ai_complaint[user_id]['history'].append(user_msg)
        pending_ai_complaint[user_id]['history'].append({"role": "assistant", "content": first_msg})
        send_user_message(user_id, first_msg, keyboard=back_only_keyboard())
    else:
        send_user_message(user_id, "⚠️ Ассистент временно недоступен. Попробуйте стандартную форму.", keyboard=main_menu_keyboard())
        del pending_ai_complaint[user_id]

def start_ai_faq(user_id):
    pending_ai_faq[user_id] = {
        'history': [{"role": "system", "content": AI_FAQ_PROMPT}],
        'phase': 'answering'
    }
    user_msg = {"role": "user", "content": "Здравствуйте! У меня вопрос."}
    full_messages = pending_ai_faq[user_id]['history'] + [user_msg]
    first_msg = ask_gigachat(full_messages)
    if first_msg:
        pending_ai_faq[user_id]['history'].append(user_msg)
        pending_ai_faq[user_id]['history'].append({"role": "assistant", "content": first_msg})
        send_user_message(user_id, first_msg, keyboard=back_only_keyboard())
    else:
        send_user_message(user_id, "⚠️ Ассистент временно недоступен.", keyboard=main_menu_keyboard())
        del pending_ai_faq[user_id]

def handle_ai_complaint(user_id, text, msg):
    if text == '↩️ назад':
        del pending_ai_complaint[user_id]
        send_user_message(user_id, "Диалог прерван. Главное меню:", keyboard=main_menu_keyboard())
        return

    if text in ['меню', 'главное меню', 'в меню']:
        pending_ai_complaint.pop(user_id, None)
        reset_user_state(user_id)
        send_user_message(user_id, "Главное меню:", keyboard=main_menu_keyboard())
        return

    state = pending_ai_complaint[user_id]

    if state['phase'] == 'selecting_org':
        org_map = {'фсин':'FSIN', 'тестовая ветка':'TEST', 'вч':'VCH'}
        org_key = org_map.get(text)
        if org_key and ORG_ALLOWED.get(org_key):
            complaint_text = state.get('collected_text', '')
            if not complaint_text:
                send_user_message(user_id, "❌ Не удалось извлечь текст жалобы. Попробуйте снова.")
                del pending_ai_complaint[user_id]
                return
            if is_user_blacklisted(user_id):
                send_user_message(user_id, "🚫 Вы находитесь в чёрном списке.")
                del pending_ai_complaint[user_id]
                return
            if contains_bad_words(complaint_text):
                send_user_message(user_id, "🚫 В жалобе обнаружены оскорбления. Подача отменена.")
                del pending_ai_complaint[user_id]
                return
            if check_spam(user_id):
                blocked_until = user_blocked_until.get(user_id)
                time_str = blocked_until.strftime('%H:%M') if blocked_until else 'некоторое время'
                send_user_message(user_id, f"🚫 Вы временно заблокированы за частые жалобы. Блокировка до {time_str}.")
                del pending_ai_complaint[user_id]
                return

            complaint_id = add_complaint_db(user_id, complaint_text, org_key, anonymous=False, extra_answers=None)
            if complaint_id:
                add_complaint_time(user_id)
                for att in state.get('attachments', []):
                    add_attachment(complaint_id, att['url'], att['type'])
                chat_id = CHAT_ID_BY_ORG.get(org_key)
                if chat_id:
                    send_message(chat_id,
                        f"🆕 ЖАЛОБА #{complaint_id} ({ORG_NAMES[org_key]})\nОт: {mention(user_id)}\nТекст: {complaint_text}")
                send_user_message(user_id,
                    f"✅ Ваша жалоба №{complaint_id} ({ORG_NAMES[org_key]}) передана в обработку. "
                    f"💡 Для отзыва отправьте: #отозвать {complaint_id}",
                    keyboard=main_menu_keyboard())
                if is_night_time():
                    send_user_message(user_id, "🌙 Обратите внимание: сейчас нерабочее время. Ваша жалоба принята и будет рассмотрена утром, после 08:00 по МСК.")
            else:
                send_user_message(user_id, "❌ Ошибка сохранения жалобы.")
            del pending_ai_complaint[user_id]
            return
        elif text == '↩️ назад':
            del pending_ai_complaint[user_id]
            send_user_message(user_id, "Главное меню:", keyboard=main_menu_keyboard())
            return
        else:
            send_user_message(user_id, "Пожалуйста, выберите организацию с помощью кнопок или нажмите «↩️ Назад».",
                            keyboard=org_select_keyboard(get_allowed_orgs()))
            return

    atts = extract_attachments(msg)
    if atts:
        state['attachments'].extend(atts)

    state['history'].append({"role": "user", "content": text})
    response = ask_gigachat(state['history'])
    if response is None:
        send_user_message(user_id, "❌ Ошибка связи с ИИ. Попробуйте позже.", keyboard=main_menu_keyboard())
        del pending_ai_complaint[user_id]
        return

    # Цензура ответа (на всякий случай)
    response = censor_ai_response(response)

    state['history'].append({"role": "assistant", "content": response})
    if "отправляем?" in response.lower() or "всё верно?" in response.lower():
        state['collected_text'] = response
        allowed_names = get_allowed_org_names()
        if not allowed_names:
            send_user_message(user_id, "🚧 К сожалению, сейчас подача жалоб временно недоступна во все организации.",
                            keyboard=main_menu_keyboard())
            del pending_ai_complaint[user_id]
        else:
            state['phase'] = 'selecting_org'
            send_user_message(user_id,
                f"📂 Выберите организацию для отправки жалобы:\n{', '.join(allowed_names)}",
                keyboard=org_select_keyboard(get_allowed_orgs()))
    else:
        send_user_message(user_id, response, keyboard=back_only_keyboard())

def handle_ai_faq(user_id, text):
    if text == '↩️ назад':
        del pending_ai_faq[user_id]
        send_user_message(user_id, "Главное меню:", keyboard=main_menu_keyboard())
        return

    if text in ['меню', 'главное меню', 'в меню']:
        pending_ai_faq.pop(user_id, None)
        reset_user_state(user_id)
        send_user_message(user_id, "Главное меню:", keyboard=main_menu_keyboard())
        return

    state = pending_ai_faq[user_id]

    match = re.search(r'№?\s*(\d+)', text)
    complaint_info = None
    if match:
        potential_id = int(match.group(1))
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT complaint_id, status, organization, created_at, assigned_staff_id "
            "FROM complaints WHERE complaint_id = %s AND user_id = %s",
            (potential_id, user_id)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            complaint_info = row

    recent = get_user_complaints(user_id, limit=5)
    summary_lines = []
    if recent:
        for c in recent:
            org = ORG_NAMES.get(c['organization'], c['organization'])
            status = c['status']
            summary_lines.append(f"№{c['complaint_id']} ({org}) — {status} от {c['created_at'].strftime('%d.%m.%y')}")
    summary_text = "\n".join(summary_lines) if summary_lines else "У пользователя пока нет поданных жалоб."

    system_content = AI_FAQ_PROMPT + "\n\nСводка последних жалоб пользователя:\n" + summary_text
    if complaint_info:
        staff_mention = mention(complaint_info['assigned_staff_id']) if complaint_info['assigned_staff_id'] else "не назначен"
        detail = (
            f"\n\nПодробности о жалобе №{complaint_info['complaint_id']}:\n"
            f"- Организация: {ORG_NAMES.get(complaint_info['organization'], complaint_info['organization'])}\n"
            f"- Статус: {complaint_info['status']}\n"
            f"- Создана: {complaint_info['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            f"- Ответственный: {staff_mention}"
        )
        system_content += detail

    messages_for_ai = [{"role": "system", "content": system_content}]
    for msg in state['history'][1:]:
        messages_for_ai.append(msg)

    messages_for_ai.append({"role": "user", "content": text})

    response = ask_gigachat(messages_for_ai)
    if response is None:
        send_user_message(user_id, "❌ Ошибка связи с ИИ.", keyboard=main_menu_keyboard())
        del pending_ai_faq[user_id]
        return

    # Обработка действий (оценка, отзыв)
    response = process_ai_actions(user_id, response)
    # Жёсткий пост-фильтр запрещённых команд
    response = censor_ai_response(response)

    state['history'].append({"role": "user", "content": text})
    state['history'].append({"role": "assistant", "content": response})
    send_user_message(user_id, response, keyboard=back_only_keyboard())

# ========== ОСНОВНАЯ ФУНКЦИЯ ОБРАБОТКИ СОБЫТИЙ ==========
def process_event(event):
    global event_counter, last_events_ts, last_longpoll_info, antislip_enabled, global_maintenance

    if event.type != VkBotEventType.MESSAGE_NEW:
        return
    msg = event.object.get('message')
    if not msg:
        return
    user_id = msg.get('from_id')
    text = msg.get('text', '').strip().lower()
    peer_id = msg.get('peer_id')
    original_text = msg.get('text', '').strip()

    event_counter += 1
    now = datetime.now()
    last_events_ts.append(now)
    if len(last_events_ts) > 100:
        last_events_ts = last_events_ts[-50:]
    last_longpoll_info['last_event_time'] = now

    print(f"peer_id = {peer_id} | user_id = {user_id} | text = {original_text}")

    if text == '/test':
        send_message(peer_id, f"📌 peer_id этого чата: {peer_id}")
        return

    if global_maintenance:
        if not (peer_id == user_id and user_id in MAINTENANCE_ADMINS and text == '/tech off'):
            if text.startswith('/') or text.startswith('#'):
                send_message(peer_id, "🚧 Ведутся технические работы. Попробуйте позже.")
            return

    if antislip_enabled and user_id not in ANTISLIP_EXEMPT_ADMINS and not is_group_admin(user_id):
        if text.startswith(('/kick', '/ban', '/mute', '/setadmin', '/unadmin')):
            target_id = extract_id_from_mention(original_text)
            if target_id and target_id != user_id and is_user_admin(peer_id, target_id):
                now = datetime.now()
                last_warn = antislip_warnings.get(user_id)
                if last_warn and (now - last_warn).total_seconds() < 3 * 3600:
                    kick_user(peer_id, user_id, user_id)
                    send_message(peer_id, f"🛡️ Система антислив: повторная попытка за 3 часа. Нарушитель {mention(user_id)} исключён.")
                    if user_id in antislip_warnings: del antislip_warnings[user_id]
                else:
                    antislip_warnings[user_id] = now
                    send_message(peer_id, f"⚠️ Система антислив активна! Чтобы выполнить это действие, сначала отключите защиту командой /antislip off. Повторная попытка в течение 3 часов приведёт к исключению.")
                return

    # --- КОМАНДЫ АДМИНИСТРАТОРА СООБЩЕСТВА ---
    if peer_id != user_id:
        if GROUP_ID == "237645354" and is_group_admin(user_id):
            if peer_id in admin_disabled_chats and not text.startswith('/adminmode') and text not in ['/ahelp', '/restart', '/tech', '/техрежим'] \
                    and (text.startswith('/') or text.startswith('#')):
                send_message(peer_id, "⛔ Команды администратора временно отключены. Используйте /adminmode для управления.")
                return

            if text == '/adminmode':
                status = "включён" if peer_id in admin_disabled_chats else "отключён"
                send_message(peer_id, f"ℹ️ Режим 'Только чтение' в этом чате: {status}.")
                return
            elif text == '/adminmode on':
                admin_disabled_chats.add(peer_id)
                send_message(peer_id, "🔒 Режим 'Только чтение' включён. Команды администрирования в этом чате заблокированы.")
                return
            elif text == '/adminmode off':
                admin_disabled_chats.discard(peer_id)
                send_message(peer_id, "🔓 Режим 'Только чтение' отключён. Команды администрирования доступны.")
                return

            if text.startswith('/blacklist'):
                target_id = extract_id_from_mention(original_text)
                if target_id:
                    blacklist.add(target_id)
                    user_blacklist_info[target_id] = {
                        'admin_id': user_id,
                        'timestamp': datetime.now(),
                        'reason': 'Административная блокировка'
                    }
                    send_message(peer_id, f"🚫 Пользователь {mention(target_id)} добавлен в чёрный список.")
                    send_user_message(target_id,
                        f"🚫 Вы были заблокированы администратором {mention(user_id)}.\n"
                        f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                        f"Причина: Административная блокировка\n\n"
                        f"Вы можете подать амнистию, нажав кнопку ниже.",
                        keyboard=amnesty_request_keyboard()
                    )
                else:
                    send_message(peer_id, "❌ /blacklist @user")
                return
            if text.startswith('/unblacklist'):
                target_id = extract_id_from_mention(original_text)
                if target_id:
                    blacklist.discard(target_id)
                    user_blacklist_info.pop(target_id, None)
                    send_message(peer_id, f"✅ Пользователь {mention(target_id)} удалён из чёрного списка.")
                else:
                    send_message(peer_id, "❌ /unblacklist @user")
                return

            if text.startswith('/fsin') or text.startswith('/gai') or text.startswith('/vch'):
                parts = text.split()
                org_cmd = parts[0][1:]
                org_key = org_cmd.upper()
                if len(parts) == 1:
                    status = "включена" if ORG_ALLOWED[org_key] else "отключена"
                    send_message(peer_id, f"ℹ️ Подача жалоб в {ORG_NAMES[org_key]}: {status}")
                elif len(parts) == 2 and parts[1] in ('on', 'off'):
                    ORG_ALLOWED[org_key] = (parts[1] == 'on')
                    status = "включена" if ORG_ALLOWED[org_key] else "отключена"
                    send_message(peer_id, f"✅ Подача жалоб в {ORG_NAMES[org_key]} {status}.")
                else:
                    send_message(peer_id, f"❌ Используйте: /{org_cmd} или /{org_cmd} on/off")
                return

            if text.startswith('/rreset'):
                target_id = extract_id_from_mention(original_text)
                if target_id:
                    count = reset_staff_ratings(target_id)
                    send_message(peer_id, f"🔄 Сброшено {count} оценок сотрудника {mention(target_id)}.")
                else:
                    send_message(peer_id, "❌ /rreset @user")
                return
            if text.startswith('/rset'):
                parts = original_text.split()
                if len(parts) >= 3:
                    target_id = extract_id_from_mention(parts[1])
                    rating = parts[2]
                    if target_id and rating.isdigit() and 1 <= int(rating) <= 5:
                        cid = set_last_rating_for_staff(target_id, int(rating))
                        if cid:
                            send_message(peer_id, f"⭐ Установлена оценка {rating} для жалобы #{cid} сотрудника {mention(target_id)}.")
                        else:
                            send_message(peer_id, f"❌ Нет отработанных жалоб.")
                else:
                    send_message(peer_id, "❌ /rset @user 1-5")
                return
            if text.startswith('/radd'):
                parts = original_text.split()
                if len(parts) >= 3:
                    target_id = extract_id_from_mention(parts[1])
                    rating = parts[2]
                    if target_id and rating.isdigit() and 1 <= int(rating) <= 5:
                        new_id = award_rating(target_id, int(rating), 'FSIN')
                        send_message(peer_id, f"🌟 Начислен поощрительный балл {rating} сотруднику {mention(target_id)} (запись #{new_id}).")
                else:
                    send_message(peer_id, "❌ /radd @user 1-5")
                return
            if text.startswith('/rcheck'):
                target_id = extract_id_from_mention(original_text)
                if target_id:
                    info = get_staff_rating_info(target_id)
                    if info and info['cnt'] > 0:
                        send_message(peer_id, f"📊 {mention(target_id)}: сумма баллов {info['total_rating']} ({info['cnt']} оценок).")
                    else:
                        send_message(peer_id, f"ℹ️ Нет оценок.")
                else:
                    send_message(peer_id, "❌ /rcheck @user")
                return
            if text.startswith('/rdelete'):
                parts = original_text.split()
                if len(parts) >= 3:
                    target_id = extract_id_from_mention(parts[1])
                    complaint_id = parts[2]
                    if target_id and complaint_id.isdigit():
                        comp = get_complaint(int(complaint_id))
                        if comp and comp[2] == target_id:
                            delete_complaint_rating(int(complaint_id))
                            send_message(peer_id, f"🗑️ Оценка удалена.")
                        else:
                            send_message(peer_id, "❌ Жалоба не принадлежит сотруднику.")
                else:
                    send_message(peer_id, "❌ /rdelete @user ID")
                return
            if text.startswith('/unspam'):
                target_id = extract_id_from_mention(original_text)
                if target_id:
                    remove_spam_block(target_id)
                    send_message(peer_id, f"✅ Блокировка спама снята с {mention(target_id)}.")
                else:
                    send_message(peer_id, "❌ /unspam @user")
                return
            if text.startswith('/antislip'):
                if text == '/antislip':
                    status = "включена" if antislip_enabled else "отключена"
                    send_message(peer_id, f"🛡️ Система антислив: {status}.")
                elif text == '/antislip on':
                    antislip_enabled = True
                    send_message(peer_id, "🛡️ Система антислив включена.")
                elif text == '/antislip off':
                    antislip_enabled = False
                    send_message(peer_id, "⚠️ Система антислив отключена.")
                    antislip_warnings.clear()
                else:
                    send_message(peer_id, "❌ /antislip on/off")
                return
            if text.startswith('/undo'):
                undo_last_action(peer_id, user_id)
                return
            if text.startswith('/modlog'):
                limit = 10
                parts = original_text.split()
                if len(parts) >= 2 and parts[1].isdigit(): limit = int(parts[1])
                logs = get_mod_logs(peer_id, limit)
                if not logs:
                    send_message(peer_id, "📭 Журнал модерации пуст.")
                else:
                    lines = ["📋 Журнал модерации:"]
                    for log in logs:
                        t = log['action_time'].strftime('%Y-%m-%d %H:%M')
                        lines.append(f"[{t}] {log['action']} → {mention(log['target_id'])} (от {mention(log['initiator_id'])})")
                    send_message(peer_id, "\n".join(lines))
                return
            if text.startswith('/unfreeze'):
                target_id = extract_id_from_mention(original_text)
                if not target_id:
                    send_message(peer_id, "❌ Укажите пользователя: /unfreeze @user")
                    return
                if target_id not in frozen_admins:
                    send_message(peer_id, f"ℹ️ Пользователь {mention(target_id)} не заморожен.")
                else:
                    del frozen_admins[target_id]
                    send_message(peer_id, f"✅ Заморозка с {mention(target_id)} снята.")
                return
            if text.startswith('/userinfo'):
                target_id = extract_id_from_mention(original_text)
                if not target_id:
                    send_message(peer_id, "❌ /userinfo @user")
                    return
                complaints = get_user_complaints(target_id)
                blocked = "да" if target_id in user_blocked_until else "нет"
                blacklisted = "да" if is_user_blacklisted(target_id) else "нет"
                info = f"📊 Информация о {mention(target_id)}:\n"
                info += f"• Жалоб: {len(complaints)}\n"
                info += f"• Спам-блок: {blocked}\n"
                info += f"• Чёрный список: {blacklisted}\n"
                if complaints:
                    last = complaints[0]
                    info += f"• Последняя жалоба: №{last['complaint_id']} ({last['status']}) от {last['created_at'].strftime('%d.%m.%y')}"
                send_message(peer_id, info)
                return
            if text == '/stats':
                count_command('/stats')
                lines = ["📊 Общая статистика:"]
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) as total FROM complaints")
                total = cur.fetchone()['total']
                cur.execute("SELECT status, COUNT(*) as cnt FROM complaints GROUP BY status")
                statuses = cur.fetchall()
                conn.close()
                lines.append(f"Всего жалоб: {total}")
                for s in statuses:
                    lines.append(f"  {s['status']}: {s['cnt']}")
                send_message(peer_id, "\n".join(lines))
                return
            if text.startswith('/allcomplaints'):
                parts = original_text.split()
                org = None
                status = None
                for p in parts[1:]:
                    if p.upper() in ('FSIN','GAI','VCH'):
                        org = p.upper()
                    elif p.lower() in ('новая','в_работе','отработана','отозвана'):
                        status = p.lower()
                complaints = get_all_complaints(organization=org, status=status)
                if not complaints:
                    send_message(peer_id, "📭 Жалобы не найдены.")
                else:
                    lines = ["📋 Последние жалобы:"]
                    for c in complaints:
                        user_disp = mention(c['user_id'])
                        staff = mention(c['assigned_staff_id']) if c['assigned_staff_id'] else "не назначен"
                        lines.append(f"№{c['complaint_id']} [{c['status']}] {user_disp} → {staff} ({c['organization']})")
                    send_message(peer_id, "\n".join(lines))
                return
            if text.startswith('/reminder'):
                parts = text.split()
                if len(parts) == 3 and ':' in parts[1] and ':' in parts[2]:
                    REMINDER_TIMES.clear()
                    REMINDER_TIMES.extend([parts[1], parts[2]])
                    schedule.clear()
                    setup_schedule()
                    send_message(peer_id, f"✅ Время напоминаний изменено на {parts[1]} и {parts[2]} (МСК).")
                else:
                    send_message(peer_id, "❌ Используйте: /reminder 10:00 10:30")
                return
            if text == '/ahelp':
                help_text = (
                    "🛡️ Полный контроль администратора:\n"
                    "• /fsin on/off — включить/отключить приём жалоб в ФСИН\n"
                    "• /gai on/off — включить/отключить приём жалоб в тестовую ветку\n"
                    "• /vch on/off — включить/отключить приём жалоб в ВЧ\n"
                    "• /blacklist @user — добавить пользователя в чёрный список\n"
                    "• /unblacklist @user — убрать пользователя из чёрного списка\n"
                    "• /rreset @user — сбросить все оценки сотрудника\n"
                    "• /rset @user N — установить оценку N последней отработанной жалобе сотрудника\n"
                    "• /radd @user N — начислить поощрительный балл N сотруднику\n"
                    "• /rcheck @user — показать текущий рейтинг сотрудника\n"
                    "• /rdelete @user ID — удалить оценку у жалобы с указанным ID\n"
                    "• /rclear — удалить все оценки (требует подтверждения в ЛС)\n"
                    "• /unspam @user — снять спам-блокировку с пользователя\n"
                    "• /antislip on/off — включить/отключить систему антислива\n"
                    "• /undo — откатить последнее действие модерации\n"
                    "• /modlog [N] — показать последние N записей журнала модерации\n"
                    "• /unfreeze @user — разморозить модератора\n"
                    "• /userinfo @user — показать информацию о пользователе (жалобы, блокировки)\n"
                    "• /resetuser @user — сбросить все состояния и спам-блок (требует подтверждения)\n"
                    "• /stats — общая статистика жалоб по статусам\n"
                    "• /allcomplaints [ORG] [статус] — список жалоб с фильтром по организации и статусу\n"
                    "• /restart — перезагрузка бота (требует подтверждения в ЛС)\n"
                    "• /reminder 14:00 14:30 — изменить время напоминаний\n"
                    "• /adminmode on/off — режим «Только чтение» в этом чате (блокировка админ-команд)\n"
                    "• /resetcomplaints — удалить все жалобы и сбросить нумерацию на 1 (требует подтверждения в ЛС)\n"
                    "• /aitest — проверить доступность GigaChat\n"
                    "• /aistats — статистика запросов к ИИ за сегодня\n"
                    "• /notify @user текст — отправить уведомление пользователю\n"
                    "• /testconfirm — тест двухфакторного подтверждения\n"
                    "\n⚠️ Критические команды (/rclear, /restart, /resetuser, /resetcomplaints, /testconfirm) требуют подтверждения в ЛС."
                    "\nПо вопросам: https://vk.com/alpha62"
                )
                send_message(peer_id, help_text)
                return

            # Новая команда сброса жалоб
            if text.startswith('/resetcomplaints'):
                pending_admin_confirm[user_id] = 'resetcomplaints'
                send_message(peer_id, "⚠️ Сброс ВСЕХ жалоб и обнуление нумерации. Для подтверждения отправьте /confirm в личные сообщения бота.")
                return

            # === НОВЫЕ КОМАНДЫ ===
            if text == '/aitest':
                start = time.time()
                test_msg = ask_gigachat([{"role": "user", "content": "test"}])
                if test_msg is not None:
                    elapsed = int((time.time() - start) * 1000)
                    send_message(peer_id, f"✅ GigaChat доступен. Ответ получен за {elapsed} мс.")
                else:
                    send_message(peer_id, "❌ GigaChat недоступен.")
                return

            if text == '/aistats':
                msg = (f"📊 Статистика ИИ за сегодня:\n"
                       f"• Запросов: {ai_requests_today}\n"
                       f"• Токенов (примерно): {ai_tokens_today}")
                send_message(peer_id, msg)
                return

            if text.startswith('/notify'):
                parts = original_text.split(maxsplit=2)
                if len(parts) < 3:
                    send_message(peer_id, "❌ Используйте: /notify @user текст")
                    return
                target_id = extract_id_from_mention(parts[1])
                if not target_id:
                    send_message(peer_id, "❌ Не удалось извлечь ID пользователя.")
                    return
                notification_text = parts[2]
                send_user_message(target_id, f"📢 Сообщение от администратора:\n\n{notification_text}")
                send_message(peer_id, f"✅ Уведомление отправлено пользователю {mention(target_id)}.")
                return

        if text.startswith(('/rreset', '/rset', '/radd', '/rcheck', '/rdelete', '/rclear', '/unspam', '/antislip',
                           '/undo', '/modlog', '/unfreeze', '/ahelp', '/fsin', '/gai', '/vch',
                           '/blacklist', '/unblacklist', '/reminder', '/restart', '/stats',
                           '/userinfo', '/resetuser', '/allcomplaints', '/adminmode', '/testconfirm',
                           '/resetcomplaints', '/aitest', '/aistats', '/notify')):
            if GROUP_ID != "237645354":
                send_message(peer_id, "⛔ Эта команда доступна только в основной группе.")
            else:
                send_message(peer_id, "❌ Недостаточно прав.")
            return

    # ---------- ЛИЧНЫЕ СООБЩЕНИЯ ----------
    if peer_id == user_id:
        if not is_agreement_accepted(user_id) and user_id not in MAINTENANCE_ADMINS:
            if text == '✅ я принимаю условия':
                accept_agreement(user_id)
                send_user_message(user_id, "✅ Спасибо! Вы приняли условия пользовательского соглашения. Теперь вам доступны все функции бота.", keyboard=main_menu_keyboard())
            else:
                send_user_message(
                    user_id,
                    "Для использования бота необходимо принять пользовательское соглашение. Ознакомьтесь с ним по ссылке ниже и нажмите «Я принимаю условия».",
                    keyboard=agreement_keyboard()
                )
            return

        if is_user_blacklisted(user_id):
            if user_id in pending_amnesty:
                if text == '↩️ назад':
                    pending_amnesty.pop(user_id)
                    info = user_blacklist_info.get(user_id, {})
                    admin_mention = mention(info.get('admin_id')) if info.get('admin_id') else 'неизвестно'
                    date_str = info.get('timestamp').strftime('%d.%m.%Y %H:%M') if info.get('timestamp') else 'неизвестно'
                    send_user_message(user_id, f"🚫 Вы заблокированы администрацией.\nЗаблокировал: {admin_mention}\nДата: {date_str}\nПричина: {info.get('reason', 'не указана')}\n\nДля обжалования нажмите кнопку «Написать амнистию».", keyboard=amnesty_request_keyboard())
                    return
                amnesty_text = original_text
                if user_id in user_amnesty_cooldown and datetime.now() < user_amnesty_cooldown[user_id]:
                    next_time = user_amnesty_cooldown[user_id].strftime('%d.%m.%Y %H:%M')
                    send_user_message(user_id, f"Вы уже подавали амнистию. Следующая попытка возможна после {next_time}.")
                    pending_amnesty.pop(user_id)
                    return
                info = user_blacklist_info.get(user_id, {})
                admin_mention = mention(info.get('admin_id')) if info.get('admin_id') else 'неизвестно'
                date_str = info.get('timestamp').strftime('%d.%m.%Y %H:%M') if info.get('timestamp') else 'неизвестно'
                dev_msg = (
                    f"📩 Амнистия от {mention(user_id)}\n"
                    f"Заблокировал: {admin_mention}\n"
                    f"Дата блокировки: {date_str}\n"
                    f"Причина: {info.get('reason', 'не указана')}\n\n"
                    f"Текст амнистии:\n{amnesty_text}"
                )
                send_message(DEV_USER_ID, dev_msg, keyboard=amnesty_decision_keyboard(user_id))
                send_user_message(user_id, "✅ Ваша амнистия отправлена. Ожидайте решения.")
                pending_amnesty.pop(user_id)
                return

            if text == 'написать амнистию':
                if user_id in user_amnesty_cooldown and datetime.now() < user_amnesty_cooldown[user_id]:
                    next_time = user_amnesty_cooldown[user_id].strftime('%d.%m.%Y %H:%M')
                    send_user_message(user_id, f"Вы уже подавали амнистию. Следующая попытка возможна после {next_time}.")
                    return
                pending_amnesty[user_id] = True
                send_user_message(user_id, "Напишите текст амнистии (объясните, почему вас нужно разблокировать).", keyboard=back_only_keyboard())
                return
            else:
                info = user_blacklist_info.get(user_id, {})
                admin_mention = mention(info.get('admin_id')) if info.get('admin_id') else 'неизвестно'
                date_str = info.get('timestamp').strftime('%d.%m.%Y %H:%M') if info.get('timestamp') else 'неизвестно'
                send_user_message(user_id, f"🚫 Вы заблокированы администрацией.\nЗаблокировал: {admin_mention}\nДата: {date_str}\nПричина: {info.get('reason', 'не указана')}\n\nДля обжалования нажмите кнопку «Написать амнистию».", keyboard=amnesty_request_keyboard())
            return

        if user_id == DEV_USER_ID:
            if text.startswith('/amnesty accept'):
                parts = text.split()
                if len(parts) >= 3 and parts[2].isdigit():
                    target_id = int(parts[2])
                    if target_id in blacklist:
                        blacklist.discard(target_id)
                        user_blacklist_info.pop(target_id, None)
                        user_amnesty_cooldown.pop(target_id, None)
                        send_user_message(target_id, "✅ Ваше наказание амнистировано. Пожалуйста, впредь соблюдайте правила.")
                        send_message(DEV_USER_ID, f"Пользователь {mention(target_id)} амнистирован.")
                    else:
                        send_message(DEV_USER_ID, "Пользователь не в чёрном списке.")
                return
            elif text.startswith('/amnesty reject'):
                parts = text.split()
                if len(parts) >= 3 and parts[2].isdigit():
                    target_id = int(parts[2])
                    user_amnesty_cooldown[target_id] = datetime.now() + timedelta(days=3)
                    send_user_message(target_id, "❌ Ваша амнистия отклонена. Следующую попытку можно подать через 3 дня.")
                    send_message(DEV_USER_ID, f"Амнистия пользователя {mention(target_id)} отклонена.")
                return

        if text == 'подтверждаю' and user_id in MAINTENANCE_ADMINS:
            pass

        if text == "📝 подать жалобу":
            text = "/start"
        elif text == "📋 мои жалобы":
            text = "#мои"
        elif text == "⭐ оценить":
            text = "#оценить"
        elif text == "❓ помощь":
            text = "/help"
        elif text == "🐞 сообщить о баге":
            text = "/bug"

        if text == '↩️ назад':
            pending_bug_reports.pop(user_id, None)
            draft_sessions.pop(user_id, None)
            pending_amnesty.pop(user_id, None)
            pending_ai_complaint.pop(user_id, None)
            pending_ai_faq.pop(user_id, None)
            reset_user_state(user_id)
            send_user_message(user_id, "Главное меню:", keyboard=main_menu_keyboard())
            return

        if text in ['меню', 'главное меню', 'в меню']:
            pending_bug_reports.pop(user_id, None)
            draft_sessions.pop(user_id, None)
            pending_amnesty.pop(user_id, None)
            pending_ai_complaint.pop(user_id, None)
            pending_ai_faq.pop(user_id, None)
            reset_user_state(user_id)
            send_user_message(user_id, "Главное меню:", keyboard=main_menu_keyboard())
            return

        if text.startswith('/tech'):
            if user_id not in MAINTENANCE_ADMINS:
                send_user_message(user_id, "❌ Недостаточно прав.")
                return
            if text == '/tech':
                status = "включён" if global_maintenance else "выключен"
                send_user_message(user_id, f"ℹ️ Режим техобслуживания: {status}.")
            elif text == '/tech on':
                global_maintenance = True
                send_user_message(user_id, "🔧 Режим техобслуживания включён.")
            elif text == '/tech off':
                global_maintenance = False
                send_user_message(user_id, "✅ Режим техобслуживания отключён.")
            else:
                send_user_message(user_id, "❌ /tech on/off")
            return

        # Обработка подтверждений действий администраторов
        if text == '/confirm' and user_id in pending_admin_confirm:
            action = pending_admin_confirm.pop(user_id)
            if action == 'resetcomplaints':
                conn = get_db_connection()
                cur = conn.cursor()
                try:
                    cur.execute("DELETE FROM complaint_attachments")
                    cur.execute("DELETE FROM complaint_logs")
                    cur.execute("DELETE FROM complaints")
                    cur.execute("ALTER TABLE complaints AUTO_INCREMENT = 1")
                    conn.commit()
                    send_user_message(user_id, "✅ Все жалобы удалены. Нумерация начнётся с 1.")
                except Exception as e:
                    conn.rollback()
                    send_user_message(user_id, f"❌ Ошибка при сбросе: {e}")
                finally:
                    conn.close()
            return

        if text == '#очистить':
            clear_user_dialog(user_id)
            return

        if text == '#уведомления вкл':
            user_notifications_disabled.discard(user_id)
            send_user_message(user_id, "🔔 Автоуведомления включены.")
            return
        if text == '#уведомления выкл':
            user_notifications_disabled.add(user_id)
            send_user_message(user_id, "🔕 Автоуведомления отключены (запросы оценки и напоминания не будут приходить).")
            return

        if text == '/help':
            help_text = (
                "📖 Как пользоваться ботом:\n"
                "• Нажмите «Подать жалобу» или напишите организацию (ФСИН, ГАИ, ВЧ).\n"
                "• Следуйте инструкциям, чтобы указать детали и приложить файлы.\n"
                "• После обработки вы получите уведомление и сможете оценить работу.\n"
                "• Команды: #мои, #оценить, #добавить, #отозвать, #ответ, #сотрудник.\n"
                "• #уведомления вкл/выкл — управление уведомлениями.\n"
                "• #очистить — удалить историю диалога с ботом.\n"
                "• Если вы заметили ошибку или баг, нажмите «Сообщить о баге» в меню или напишите /bug.\n"
                "Вы сможете описать проблему и приложить скриншоты/видео."
            )
            send_user_message(user_id, help_text, keyboard=help_keyboard())
            return
        if text == '/bug':
            pending_bug_reports[user_id] = {'state': 'desc', 'description': None, 'attachments': []}
            send_user_message(user_id, "🐞 Опишите проблему или ошибку. Можете сразу приложить скриншоты. Для отмены нажмите «↩️ Назад».", keyboard=back_only_keyboard())
            return

        if user_id in pending_bug_reports:
            state = pending_bug_reports[user_id]['state']
            if state == 'desc':
                if text == '↩️ назад':
                    del pending_bug_reports[user_id]
                    send_user_message(user_id, "❌ Отправка отменена.", keyboard=main_menu_keyboard())
                    return
                pending_bug_reports[user_id]['description'] = original_text
                atts = extract_attachments(msg)
                pending_bug_reports[user_id]['attachments'].extend(atts)
                pending_bug_reports[user_id]['state'] = 'attachments'
                send_user_message(user_id, "📎 Приложите скриншоты, видео или документы (не более 10 файлов). Когда закончите, напишите «готово» или нажмите кнопку.", keyboard=attachments_keyboard())
                return
            elif state == 'attachments':
                if text == 'готово':
                    desc = pending_bug_reports[user_id]['description']
                    atts = pending_bug_reports[user_id]['attachments']
                    report_msg = f"🐞 Новый баг-репорт от {mention(user_id)}:\n{desc}"
                    if atts:
                        att_lines = "\n".join([f"{i+1}. {a['url']}" for i, a in enumerate(atts)])
                        report_msg += f"\n\nПрикрепления:\n{att_lines}"
                    send_message(DEV_USER_ID, report_msg)
                    send_user_message(user_id, "✅ Спасибо! Ваше сообщение отправлено разработчику.", keyboard=main_menu_keyboard())
                    del pending_bug_reports[user_id]
                    return
                elif text == '↩️ назад':
                    del pending_bug_reports[user_id]
                    send_user_message(user_id, "Отправка отменена.", keyboard=main_menu_keyboard())
                    return
                else:
                    atts = extract_attachments(msg)
                    current = pending_bug_reports[user_id]['attachments']
                    if len(current) + len(atts) > 10:
                        send_user_message(user_id, "⚠️ Можно прикрепить не более 10 файлов. Отправьте «готово» или «↩️ Назад».")
                    else:
                        current.extend(atts)
                        cnt = len(current)
                        send_user_message(user_id, f"📎 Принято файлов: {cnt}. Отправьте ещё, напишите «готово» или нажмите «↩️ Назад».", keyboard=attachments_keyboard())
                    return

        # ===== Новые обработчики ИИ-агента =====
        if user_id in pending_ai_complaint:
            handle_ai_complaint(user_id, original_text, msg)
            return
        if user_id in pending_ai_faq:
            handle_ai_faq(user_id, original_text)
            return
        if text == "🤖 умный помощник":
            start_ai_complaint(user_id)
            return
        if text == "❓ задать вопрос":
            start_ai_faq(user_id)
            return
        # =================================

        if text == '#мои' or text == '#жалобы':
            count_command('#мои')
            complaints = get_user_complaints(user_id)
            if not complaints:
                send_user_message(user_id, "📭 У вас ещё нет поданных жалоб.")
            else:
                lines = ["📂 Ваши последние жалобы:"]
                for c in complaints:
                    org_name = ORG_NAMES.get(c['organization'], c['organization'])
                    status = c['status']
                    rating_str = f" (оценка: {c['rating']})" if c['rating'] else ""
                    lines.append(f"• №{c['complaint_id']} — {org_name} — {status}{rating_str} — {c['created_at'].strftime('%d.%m.%y %H:%M')}")
                send_user_message(user_id, "\n".join(lines))
            return

        if text == '#оценить':
            unsent = user_unsent_ratings.get(user_id, [])
            if not unsent:
                send_user_message(user_id, "⭐ У вас нет неоценённых жалоб.")
            else:
                lines = ["🌟 Выберите жалобу для оценки. Введите **только её номер** из списка:"]
                for i, (cid, _) in enumerate(unsent, 1):
                    comp = get_complaint(cid)
                    if comp:
                        org = ORG_NAMES.get(comp[3], comp[3])
                        lines.append(f"{i}. №{cid} ({org})")
                send_user_message(user_id, "\n".join(lines) + "\nИли «↩️ Назад».", keyboard=back_only_keyboard())
                pending_rating[user_id] = (user_id, unsent)
            return

        if user_id in pending_rating and isinstance(pending_rating[user_id], tuple):
            orig_user, unsent_list = pending_rating[user_id]
            if text == '↩️ назад':
                del pending_rating[user_id]
                send_user_message(user_id, "❌ Оценка отменена.", keyboard=main_menu_keyboard())
                return
            if text.isdigit():
                idx = int(text) - 1
                if 0 <= idx < len(unsent_list):
                    cid, _ = unsent_list[idx]
                    send_user_message(user_id, f"Введите оценку от 1 до 5 для жалобы #{cid}:")
                    pending_rating[user_id] = cid
                else:
                    send_user_message(user_id, "Неверный номер. Пожалуйста, введите **только номер** жалобы.", keyboard=back_only_keyboard())
            elif text == 'отмена':
                del pending_rating[user_id]
                send_user_message(user_id, "❌ Оценка отменена.", keyboard=main_menu_keyboard())
            else:
                send_user_message(user_id, "Введите **только номер** жалобы (одно число). Оценку вы поставите на следующем шаге.", keyboard=back_only_keyboard())
            return

        if user_id in pending_rating and isinstance(pending_rating[user_id], int):
            if text == '↩️ назад':
                del pending_rating[user_id]
                send_user_message(user_id, "❌ Оценка отменена.", keyboard=main_menu_keyboard())
                return
            if text.isdigit() and 1 <= int(text) <= 5:
                rating = int(text)
                complaint_id = pending_rating.pop(user_id)
                set_complaint_rating(complaint_id, rating)
                comp = get_complaint(complaint_id)
                if comp:
                    org = comp[3]
                    notify_rating(complaint_id, rating, org)
                user_unsent_ratings[user_id] = [(c, t) for c, t in user_unsent_ratings[user_id] if c != complaint_id]
                send_user_message(user_id, "✨ Спасибо за оценку!", keyboard=main_menu_keyboard())
                reset_user_state(user_id)
            else:
                send_user_message(user_id, "Введите число от 1 до 5.")
            return

        if text.startswith('#добавить'):
            parts = original_text.split(maxsplit=2)
            if len(parts) >= 3 and parts[1].isdigit():
                cid = int(parts[1])
                extra_text = parts[2]
                comp = get_complaint(cid)
                if comp and comp[0] == user_id and comp[1] in ('новая', 'в_работе'):
                    org = comp[3]
                    chat_id = CHAT_ID_BY_ORG.get(org)
                    if chat_id:
                        send_message(chat_id, f"📎 Уточнение от {mention(user_id)} к жалобе #{cid}: {extra_text}")
                        send_user_message(user_id, f"✅ Уточнение по жалобе #{cid} передано.")
                    else:
                        send_user_message(user_id, "❌ Не удалось определить чат организации.")
                else:
                    send_user_message(user_id, f"❌ Жалоба #{cid} не найдена или уже завершена.")
            else:
                send_user_message(user_id, "❌ Формат: #добавить ID текст")
            return

        if user_id in pending_extra_question:
            state_info = pending_extra_question[user_id]
            if text == '↩️ назад':
                draft_sessions.pop(user_id, None)
                send_user_message(user_id, "❌ Подача жалобы отменена.", keyboard=main_menu_keyboard())
                reset_user_state(user_id)
                return

            state_info['answers'].append(original_text)
            state_info['state'] += 1

            if state_info['state'] >= len(EXTRA_QUESTIONS):
                complaint_text = state_info['complaint_text']
                org_key = state_info['org_key']
                anonymous = state_info['anonymous']
                extra_answers = ' | '.join(state_info['answers'])
                attachments = state_info.get('attachments', [])

                if contains_bad_words(complaint_text):
                    send_user_message(user_id, "🚫 В вашей жалобе обнаружены оскорбительные выражения. Пожалуйста, переформулируйте текст и подайте заново.")
                    reset_user_state(user_id)
                    return

                if check_spam(user_id):
                    blocked_until = user_blocked_until.get(user_id)
                    time_str = blocked_until.strftime('%H:%M') if blocked_until else 'некоторое время'
                    send_user_message(user_id, f"🚫 Вы временно заблокированы за частую отправку жалоб (спам). Блокировка до {time_str}.")
                    reset_user_state(user_id)
                    return

                complaint_id = add_complaint_db(user_id, complaint_text, org_key, anonymous, extra_answers)
                if complaint_id:
                    add_complaint_time(user_id)
                    for att in attachments:
                        add_attachment(complaint_id, att['url'], att['type'])
                    chat_id = CHAT_ID_BY_ORG.get(org_key)
                    if not chat_id:
                        send_user_message(user_id, "❌ Не удалось найти чат организации.")
                        reset_user_state(user_id)
                        return
                    user_display = "Аноним" if anonymous else mention(user_id)

                    extra_formatted = ""
                    if extra_answers:
                        answers = extra_answers.split(' | ')
                        questions = [
                            "Дата инцидента",
                            "Подразделение / место",
                            "Свидетели",
                            "Последствия"
                        ]
                        extra_lines = []
                        for i, ans in enumerate(answers):
                            if i < len(questions):
                                extra_lines.append(f"• {questions[i]}: {ans}")
                        if extra_lines:
                            extra_formatted = "Дополнительно:\n" + "\n".join(extra_lines)

                    if attachments:
                        att_lines = [f"Прикреплённые файлы ({len(attachments)}):"]
                        for i, att in enumerate(attachments, 1):
                            att_lines.append(f"{i}. {att['url']}")
                        if extra_formatted:
                            extra_formatted += "\n" + "\n".join(att_lines)
                        else:
                            extra_formatted = "\n".join(att_lines)

                    msg_to_staff = f"🆕 ЖАЛОБА #{complaint_id} ({ORG_NAMES[org_key]})\nОт: {user_display}\nТекст: {complaint_text}"
                    if extra_formatted:
                        msg_to_staff += f"\n{extra_formatted}"

                    send_message(chat_id, msg_to_staff)
                    send_user_message(user_id, f"✅ Ваша жалоба №{complaint_id} ({ORG_NAMES[org_key]}) передана в обработку. 💡 Если передумаете, отправьте: #отозвать {complaint_id}", keyboard=main_menu_keyboard())
                    if is_night_time():
                        send_user_message(user_id, "🌙 Обратите внимание: сейчас нерабочее время. Ваша жалоба принята и будет рассмотрена утром, после 08:00 по МСК.")
                    send_user_message(user_id, "🐞 Если вы заметили ошибку в работе бота, пожалуйста, сообщите нам через кнопку «Сообщить о баге» в главном меню или командой /bug. Спасибо!")
                    draft_sessions.pop(user_id, None)
                else:
                    send_user_message(user_id, "❌ Ошибка сохранения.")

                reset_user_state(user_id)
                return
            else:
                next_question = EXTRA_QUESTIONS[state_info['state']]
                send_user_message(user_id, f"📝 {next_question}", keyboard=back_only_keyboard())
                return

        if user_id in pending_attachments:
            if text == '↩️ назад':
                draft_sessions.pop(user_id, None)
                send_user_message(user_id, "❌ Подача жалобы отменена.", keyboard=main_menu_keyboard())
                reset_user_state(user_id)
                return
            if text == 'готово':
                complaint_text = pending_complaint_text.pop(user_id)
                attachments = pending_attachments.pop(user_id)
                if is_user_blacklisted(user_id):
                    send_user_message(user_id, "🚫 Вы находитесь в чёрном списке.")
                    reset_user_state(user_id)
                    return
                if contains_bad_words(complaint_text):
                    send_user_message(user_id, "🚫 В вашей жалобе обнаружены оскорбительные выражения.")
                    reset_user_state(user_id)
                    return
                if check_spam(user_id):
                    blocked_until = user_blocked_until.get(user_id)
                    time_str = blocked_until.strftime('%H:%M') if blocked_until else 'некоторое время'
                    send_user_message(user_id, f"🚫 Вы временно заблокированы за частую отправку жалоб (спам). Блокировка до {time_str}.")
                    reset_user_state(user_id)
                    return
                org_key = pending_organization.pop(user_id, 'FSIN')
                anonymous = pending_anonymous_flag.pop(user_id, False)
                pending_extra_question[user_id] = {
                    'state': 0,
                    'answers': [],
                    'complaint_text': complaint_text,
                    'org_key': org_key,
                    'anonymous': anonymous,
                    'attachments': attachments
                }
                send_user_message(user_id, f"📝 {EXTRA_QUESTIONS[0]}", keyboard=back_only_keyboard())
                return
            else:
                atts = extract_attachments(msg)
                current = pending_attachments[user_id]
                if len(current) + len(atts) > 10:
                    send_user_message(user_id, "⚠️ Максимум 10 файлов. Отправьте «готово» или «↩️ Назад».")
                else:
                    current.extend(atts)
                    cnt = len(current)
                    send_user_message(user_id, f"📎 Принято файлов: {cnt}. Отправьте ещё, напишите «готово» или нажмите кнопку.", keyboard=attachments_keyboard())
                return

        if user_id in pending_org_redirect:
            allowed = pending_org_redirect[user_id]
            if text == '↩️ назад':
                del pending_org_redirect[user_id]
                draft_sessions.pop(user_id, None)
                send_user_message(user_id, "❌ Подача жалобы отменена.", keyboard=main_menu_keyboard())
                reset_user_state(user_id)
                return
            if text.upper() in [k.upper() for k in allowed]:
                org_key = text.upper()
                pending_organization[user_id] = org_key
                del pending_org_redirect[user_id]
                send_user_message(user_id, f"📂 Выбрана организация: {ORG_NAMES[org_key]}. Хотите подать жалобу анонимно? (да/нет)", keyboard=yes_no_back_keyboard())
                pending_anonymous[user_id] = True
                return
            else:
                send_user_message(user_id, f"Пожалуйста, выберите организацию из доступных или нажмите «↩️ Назад».", keyboard=org_select_keyboard(allowed))
                return

        if text in ('фсин', 'тестовая ветка', 'вч'):
            org_map = {'фсин':'FSIN', 'тестовая ветка':'TEST', 'вч':'VCH'}
            org_key = org_map[text]
            if ORG_ALLOWED[org_key]:
                pending_organization[user_id] = org_key
                send_user_message(user_id, f"📂 Выбрана организация: {ORG_NAMES[org_key]}. Хотите подать жалобу анонимно? (да/нет)", keyboard=yes_no_back_keyboard())
                pending_anonymous[user_id] = True
            else:
                allowed = get_allowed_orgs()
                if not allowed:
                    send_user_message(user_id, "🚧 К сожалению, сейчас подача жалоб временно недоступна во все организации. Попробуйте позже.", keyboard=main_menu_keyboard())
                    reset_user_state(user_id)
                else:
                    pending_org_redirect[user_id] = allowed
                    send_user_message(user_id, f"🚧 Подача жалоб в «{ORG_NAMES[org_key]}» временно недоступна. Сейчас работают: {', '.join(get_allowed_org_names())}. Пожалуйста, выберите одну из них или нажмите «↩️ Назад».", keyboard=org_select_keyboard(allowed))
            return

        if user_id in pending_anonymous:
            if text == '↩️ назад':
                pending_anonymous.pop(user_id)
                draft_sessions.pop(user_id, None)
                send_user_message(user_id, "❌ Подача жалобы отменена.", keyboard=main_menu_keyboard())
                reset_user_state(user_id)
                return
            if text == 'да':
                pending_anonymous_flag[user_id] = True
                send_user_message(user_id, "📂 Ваша жалоба будет отправлена анонимно. Теперь напишите текст жалобы.", keyboard=back_only_keyboard())
                pending_anonymous.pop(user_id)
            elif text == 'нет':
                pending_anonymous_flag[user_id] = False
                send_user_message(user_id, "📂 Ваша жалоба будет отправлена от вашего имени. Теперь напишите текст жалобы.", keyboard=back_only_keyboard())
                pending_anonymous.pop(user_id)
            elif text == 'отмена':
                pending_anonymous.pop(user_id)
                draft_sessions.pop(user_id, None)
                send_user_message(user_id, "❌ Подача жалобы отменена.", keyboard=main_menu_keyboard())
                reset_user_state(user_id)
            else:
                send_user_message(user_id, "Пожалуйста, ответьте «да» или «нет».", keyboard=yes_no_back_keyboard())
            return

        if user_id in pending_confirmations:
            if pending_confirmations[user_id] == '__DRAFT_RESTORE__':
                if text == '↩️ назад':
                    draft_sessions.pop(user_id, None)
                    pending_confirmations.pop(user_id, None)
                    send_user_message(user_id, "Главное меню:", keyboard=main_menu_keyboard())
                    return
                if text in ('да', 'yes'):
                    draft = load_draft(user_id)
                    if draft:
                        if 'organization' in draft:
                            pending_organization[user_id] = draft['organization']
                        if 'anonymous' in draft:
                            pending_anonymous_flag[user_id] = draft['anonymous']
                        if 'complaint_text' in draft:
                            pending_complaint_text[user_id] = draft['complaint_text']
                        if 'attachments' in draft:
                            pending_attachments[user_id] = draft['attachments']
                        if 'extra' in draft:
                            pending_extra_question[user_id] = draft['extra']
                        if 'confirm_text' in draft:
                            pending_confirmations[user_id] = draft['confirm_text']
                        del draft_sessions[user_id]
                        if 'extra' in draft:
                            state = draft['extra']['state']
                            if state < len(EXTRA_QUESTIONS):
                                send_user_message(user_id, f"📝 {EXTRA_QUESTIONS[state]}", keyboard=back_only_keyboard())
                        elif 'attachments' in draft:
                            send_user_message(user_id, "📎 У вас есть сохранённые файлы. Отправьте ещё или «готово».", keyboard=attachments_keyboard())
                        elif 'complaint_text' in draft:
                            pending_confirmations[user_id] = draft['complaint_text']
                            send_user_message(user_id, "❓ Отправить жалобу? (да/нет)", keyboard=yes_no_back_keyboard())
                        elif 'organization' in draft:
                            send_user_message(user_id, f"📂 Организация: {ORG_NAMES[draft['organization']]}. Хотите подать анонимно? (да/нет)", keyboard=yes_no_back_keyboard())
                            pending_anonymous[user_id] = True
                        else:
                            send_user_message(user_id, "Черновик повреждён, начните заново: /start")
                        pending_confirmations.pop(user_id, None)
                    else:
                        send_user_message(user_id, "Черновик не найден. Начните заново: /start")
                        pending_confirmations.pop(user_id, None)
                elif text in ('нет', 'no'):
                    draft_sessions.pop(user_id, None)
                    pending_confirmations.pop(user_id, None)
                    send_user_message(user_id, "Хорошо, начинаем заново. Напишите /start", keyboard=main_menu_keyboard())
                else:
                    send_user_message(user_id, "Ответьте «да» или «нет».", keyboard=yes_no_back_keyboard())
                return

            if text == '↩️ назад':
                pending_confirmations.pop(user_id)
                draft_sessions.pop(user_id, None)
                send_user_message(user_id, "❌ Отправка отменена.", keyboard=main_menu_keyboard())
                reset_user_state(user_id)
                return
            if text in ('да', 'подтвердить', 'yes'):
                complaint_text = pending_confirmations.pop(user_id)
                if is_user_blacklisted(user_id):
                    send_user_message(user_id, "🚫 Вы находитесь в чёрном списке.")
                    reset_user_state(user_id)
                    return
                if contains_bad_words(complaint_text):
                    send_user_message(user_id, "🚫 В вашей жалобе обнаружены оскорбительные выражения.")
                    reset_user_state(user_id)
                    return
                if check_spam(user_id):
                    blocked_until = user_blocked_until.get(user_id)
                    time_str = blocked_until.strftime('%H:%M') if blocked_until else 'некоторое время'
                    send_user_message(user_id, f"🚫 Вы временно заблокированы за частую отправку жалоб (спам). Блокировка до {time_str}.")
                    reset_user_state(user_id)
                    return
                pending_complaint_text[user_id] = complaint_text
                pending_attachments[user_id] = []
                send_user_message(user_id,
                    "✅ Текст жалобы принят. Хотите приложить фото или документы? "
                    "Отправьте их сейчас (не более 10 файлов). Когда закончите, напишите «готово» или нажмите кнопку.",
                    keyboard=attachments_keyboard()
                )
                return
            elif text in ('нет', 'отмена', 'no'):
                pending_confirmations.pop(user_id)
                draft_sessions.pop(user_id, None)
                send_user_message(user_id, "❌ Отправка отменена.", keyboard=main_menu_keyboard())
                reset_user_state(user_id)
                return
            else:
                send_user_message(user_id, "Ответьте «да» или «нет».", keyboard=yes_no_back_keyboard())
                return

        if text.startswith('#отозвать'):
            parts = original_text.split()
            complaint_id = None
            if len(parts) >= 2 and parts[1].isdigit():
                complaint_id = int(parts[1])
            else:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT complaint_id FROM complaints WHERE user_id = %s AND status NOT IN ('отработана','отозвана') ORDER BY created_at DESC LIMIT 1", (user_id,))
                row = cur.fetchone()
                conn.close()
                if row: complaint_id = row['complaint_id']
            if not complaint_id:
                send_user_message(user_id, "❌ У вас нет активных жалоб для отзыва.")
                return
            comp = get_complaint(complaint_id)
            if not comp or comp[0] != user_id:
                send_user_message(user_id, f"❌ Жалоба #{complaint_id} не найдена среди ваших.")
                return
            if comp[1] == 'отработана':
                send_user_message(user_id, f"❌ Жалоба #{complaint_id} уже обработана, отзыв невозможен.")
                return
            if comp[1] == 'отозвана':
                send_user_message(user_id, f"❌ Жалоба #{complaint_id} уже отозвана.")
                return
            update_complaint_status(complaint_id, 'отозвана')
            org_key = comp[3]
            chat_id = CHAT_ID_BY_ORG.get(org_key)
            if chat_id:
                send_message(chat_id, f"📩 Пользователь {mention(user_id)} отозвал свою жалобу #{complaint_id} ({ORG_NAMES[org_key]}).")
            send_user_message(user_id, f"✅ Жалоба #{complaint_id} отозвана.")
            reset_user_state(user_id)
            return

        if text.startswith('#ответ'):
            parts = original_text.split(maxsplit=2)
            complaint_id = None
            answer_text = ""
            if len(parts) >= 3:
                if parts[1].isdigit():
                    complaint_id = int(parts[1])
                    answer_text = parts[2].strip()
                else:
                    answer_text = (parts[1] + " " + parts[2]).strip()
            elif len(parts) == 2:
                answer_text = parts[1].strip()
            else:
                send_user_message(user_id, "❌ Используйте: #ответ [номер_жалобы] [ваше сообщение]")
                return
            if not answer_text:
                send_user_message(user_id, "❌ Укажите текст ответа.")
                return
            if not complaint_id:
                complaint_id = get_last_closed_complaint(user_id)
            if not complaint_id:
                send_user_message(user_id, "❌ У вас нет отработанных жалоб для ответа.")
                return
            comp = get_complaint(complaint_id)
            if not comp or comp[0] != user_id:
                send_user_message(user_id, f"❌ Жалоба #{complaint_id} не найдена среди ваших.")
                return
            org_key = comp[3]
            chat_id = CHAT_ID_BY_ORG.get(org_key)
            if chat_id:
                send_message(chat_id, f"📩 Ответ пользователя {mention(user_id)} по жалобе #{complaint_id}: {answer_text}")
            send_user_message(user_id, "✅ Ваш ответ отправлен сотрудникам.")
            return

        if text.startswith('#сотрудник'):
            parts = original_text.split(maxsplit=2)
            complaint_id = None
            question = ""
            if len(parts) >= 3:
                if parts[1].isdigit():
                    complaint_id = int(parts[1])
                    question = parts[2].strip()
                else:
                    question = (parts[1] + " " + parts[2]).strip()
            elif len(parts) == 2:
                question = parts[1].strip()
            else:
                send_user_message(user_id, "❌ Используйте: #сотрудник [номер_жалобы] [ваш вопрос]")
                return
            if not question:
                send_user_message(user_id, "❌ Укажите текст вопроса.")
                return
            if not complaint_id:
                complaint_id = get_last_closed_complaint(user_id)
            if not complaint_id:
                send_user_message(user_id, "❌ У вас нет отработанных жалоб для уточнения.")
                return
            comp = get_complaint(complaint_id)
            if not comp or comp[1] != 'отработана' or comp[0] != user_id:
                send_user_message(user_id, f"❌ Жалоба #{complaint_id} не найдена среди ваших отработанных.")
                return
            org_key = comp[3]
            chat_id = CHAT_ID_BY_ORG.get(org_key)
            if chat_id:
                send_message(chat_id, f"📩 Уточнение по жалобе #{complaint_id} от {mention(user_id)}: {question}")
            send_user_message(user_id, "✅ Ваш вопрос отправлен сотрудникам.")
            return

        if text == '/start':
            count_command('/start')
            reset_user_state(user_id)
            draft = load_draft(user_id)
            if draft:
                send_user_message(user_id, "⚡ У вас есть незавершённая жалоба. Хотите продолжить? (да/нет)", keyboard=yes_no_back_keyboard())
                pending_confirmations[user_id] = '__DRAFT_RESTORE__'
                return
            allowed_names = get_allowed_org_names()
            if not allowed_names:
                send_user_message(user_id, "🚧 К сожалению, сейчас подача жалоб временно недоступна во все организации. Попробуйте позже.", keyboard=main_menu_keyboard())
            else:
                send_user_message(user_id, f"📂 Вы можете подать новую жалобу. Доступные организации: {', '.join(allowed_names)}.", keyboard=org_select_keyboard(get_allowed_orgs()))
            return

        if user_id not in pending_organization and user_id not in pending_anonymous and user_id not in pending_confirmations and user_id not in pending_attachments and user_id not in pending_extra_question:
            draft = load_draft(user_id)
            if draft and pending_confirmations.get(user_id) != '__DRAFT_RESTORE__':
                send_user_message(user_id, "⚡ У вас есть незавершённая жалоба. Хотите продолжить? (да/нет)", keyboard=yes_no_back_keyboard())
                pending_confirmations[user_id] = '__DRAFT_RESTORE__'
            else:
                allowed_names = get_allowed_org_names()
                if not allowed_names:
                    send_user_message(user_id, "🚧 К сожалению, сейчас подача жалоб временно недоступна во все организации. Попробуйте позже.", keyboard=main_menu_keyboard())
                else:
                    send_user_message(user_id, f"📂 Вы можете подать новую жалобу. Доступные организации: {', '.join(allowed_names)}.", keyboard=org_select_keyboard(get_allowed_orgs()))
            return

        pending_confirmations[user_id] = original_text
        send_user_message(user_id, "❓ Отправить жалобу? (да/нет)", keyboard=yes_no_back_keyboard())
        return

    # ---------- ЧАТЫ СОТРУДНИКОВ ----------
    org_key = ORG_CHATS.get(peer_id)
    if org_key:
        if text.startswith('#досье'):
            target_id = extract_id_from_mention(original_text)
            if target_id:
                stats = get_staff_stats(target_id, org_key)
                last_act = stats['last_activity'].strftime('%d.%m.%Y %H:%M') if stats['last_activity'] else "нет данных"
                msg = (
                    f"📊 Досье {mention(target_id)} ({ORG_NAMES[org_key]}):\n"
                    f"✅ Отработано жалоб: {stats['closed']}\n"
                    f"🔄 В работе: {stats['in_work']}\n"
                    f"⭐ Сумма баллов: {stats['total_rating']} ({stats['rating_count']} оценок)\n"
                    f"🕒 Последняя активность: {last_act}"
                )
                send_message(peer_id, msg)
            else:
                send_message(peer_id, "❌ #досье @user")
            return

        if text == '#жалобы':
            count_command('#жалобы')
            complaints = get_open_complaints(org_key)
            if not complaints:
                send_message(peer_id, "📭 Нет незакрытых жалоб.")
            else:
                lines = [f"📋 Незакрытые жалобы ({ORG_NAMES[org_key]}):"]
                for c in complaints:
                    user_display = "Аноним" if c['anonymous'] else mention(c['user_id'])
                    staff = mention(c['assigned_staff_id']) if c['assigned_staff_id'] else "не назначен"
                    status = "🆕" if c['status'] == 'новая' else "🔄"
                    lines.append(f"{status} #{c['complaint_id']} от {user_display} → {staff}")
                send_message(peer_id, "\n".join(lines))
            return

        if text == '#проверка':
            count_command('#проверка')
            report = run_diagnostics(peer_id, user_id)
            send_message(peer_id, report)
            return

        if text.startswith('/kick'):
            target_id = extract_id_from_mention(original_text)
            if target_id:
                kick_user(peer_id, target_id, user_id)
            else:
                send_message(peer_id, "❌ Укажите пользователя.")
            return
        if text.startswith('/mute'):
            parts = original_text.split()
            if len(parts) >= 2:
                target_id = extract_id_from_mention(parts[1])
                duration = 0
                if len(parts) >= 3:
                    dur_str = parts[2]
                    if dur_str.endswith('m'): duration = int(dur_str[:-1]) * 60
                    elif dur_str.endswith('h'): duration = int(dur_str[:-1]) * 3600
                    elif dur_str.endswith('d'): duration = int(dur_str[:-1]) * 86400
                    else: duration = int(dur_str)
                if target_id:
                    mute_user(peer_id, target_id, user_id, duration)
                else:
                    send_message(peer_id, "❌ Неверный формат.")
            else:
                send_message(peer_id, "❌ /mute @user [время]")
            return
        if text.startswith('/unmute'):
            target_id = extract_id_from_mention(original_text)
            if target_id:
                unmute_user(peer_id, target_id, user_id)
            else:
                send_message(peer_id, "❌ Укажите пользователя.")
            return
        if text.startswith('/ban'):
            target_id = extract_id_from_mention(original_text)
            if target_id:
                ban_user(peer_id, target_id, user_id)
            else:
                send_message(peer_id, "❌ Укажите пользователя.")
            return
        if text.startswith('/unban'):
            target_id = extract_id_from_mention(original_text)
            if target_id:
                unban_user(peer_id, target_id, user_id)
            else:
                send_message(peer_id, "❌ Укажите пользователя.")
            return
        if text.startswith('/setadmin'):
            target_id = extract_id_from_mention(original_text)
            if target_id:
                set_admin_role(peer_id, target_id, user_id)
            else:
                send_message(peer_id, "❌ Укажите пользователя.")
            return
        if text.startswith('/unadmin'):
            target_id = extract_id_from_mention(original_text)
            if target_id:
                remove_admin_role(peer_id, target_id, user_id)
            else:
                send_message(peer_id, "❌ Укажите пользователя.")
            return
        if text.startswith('/snick') or text.startswith('/setnick'):
            parts = original_text.split(maxsplit=2)
            if len(parts) >= 3:
                target_id = extract_id_from_mention(parts[1])
                if target_id:
                    set_nickname(peer_id, target_id, parts[2], user_id)
                else:
                    send_message(peer_id, "❌ Неверный формат.")
            else:
                send_message(peer_id, "❌ /snick @user ник")
            return
        if text.startswith('/dnick') or text.startswith('/delnick') or text.startswith('/rnick'):
            target_id = extract_id_from_mention(original_text)
            if target_id:
                delete_nickname(peer_id, target_id, user_id)
            else:
                send_message(peer_id, "❌ Укажите пользователя.")
            return
        if text.startswith('/gnick') or text.startswith('/getnick'):
            target_id = extract_id_from_mention(original_text)
            if target_id:
                get_nickname(peer_id, target_id)
            else:
                send_message(peer_id, "❌ Укажите пользователя.")
            return
        if text == '/nlist':
            list_nicknames(peer_id)
            return
        if text in ('/admins', '/staff'):
            admins = get_chat_admins(peer_id)
            if not admins:
                send_message(peer_id, "ℹ️ В чате нет администраторов.")
            else:
                admin_list = "\n".join([f"👤 {mention(admin_id)}" for admin_id in admins])
                send_message(peer_id, f"👮‍♂️ Администраторы чата:\n{admin_list}")
            return
        if text == '/help':
            help_text = (
                f"📋 Команды ({ORG_NAMES[org_key]}):\n"
                "/kick @user – исключить\n"
                "/mute @user [10m/2h/1d] – заглушить\n"
                "/unmute @user – снять мут\n"
                "/ban @user – бан\n"
                "/unban @user – разбан\n"
                "/setadmin @user – назначить админа\n"
                "/unadmin @user – снять админа\n"
                "/admins – список админов\n"
                "/snick @user ник – установить ник\n"
                "/dnick @user – удалить ник\n"
                "/rnick @user – удалить ник (аналог)\n"
                "/gnick @user – показать ник\n"
                "/nlist – все ники\n"
                "#проверка – диагностика\n"
                "#взять ID – взять жалобу\n"
                "#отработал ID – закрыть жалобу\n"
                "#передать ID @user – передать жалобу\n"
                "#связь ID текст – написать подателю\n"
                "#логи [N] – последние действия\n"
                "#рейтинг – рейтинг сотрудников\n"
                "#досье @user – статистика сотрудника\n"
                "#жалобы – список незакрытых жалоб\n"
                "\nПо вопросам/ошибкам: https://vk.com/alpha62"
            )
            send_message(peer_id, help_text)
            return

        if text == '#рейтинг':
            count_command('#рейтинг')
            ratings = get_staff_ratings(org_key)
            if not ratings:
                send_message(peer_id, "🏆 Пока нет оценок.")
            else:
                lines = [f"🏆 Рейтинг сотрудников ({ORG_NAMES[org_key]}):"]
                for i, row in enumerate(ratings, 1):
                    staff_id = row['assigned_staff_id']
                    total = row['total_rating']
                    cnt = row['cnt']
                    lines.append(f"{i}. {mention(staff_id)} — сумма баллов: {total} ({cnt} оценок)")
                send_message(peer_id, "\n".join(lines))
            return

        if text == '#жалоба':
            match = re.search(r'#жалоба\s+@id(\d+)\s+(.+)', original_text, re.I)
            if match:
                target = int(match.group(1))
                complaint_text = match.group(2)
                cid = add_complaint_db(target, complaint_text, org_key)
                send_message(peer_id, f"📝 Жалоба #{cid} для {mention(target)}")
                send_message(target, f"✅ Ваша жалоба №{cid} ({ORG_NAMES[org_key]}) передана в обработку. 💡 Если передумаете, отправьте: #отозвать {cid}")
            else:
                send_message(peer_id, "❌ #жалоба @id123 текст")
            return

        if text.startswith('#взять'):
            match = re.search(r'#взять\s+(\d+)', original_text)
            if not match:
                send_message(peer_id, "❌ Формат: #взять ID_жалобы")
                return
            complaint_id = int(match.group(1))
            active_id = get_active_complaint_for_staff(user_id)
            if active_id and active_id != complaint_id:
                send_message(peer_id, f"⛔ У вас уже есть неотработанная жалоба #{active_id}. Сначала завершите её (#отработал {active_id}).")
                return
            complaint = get_complaint(complaint_id)
            if not complaint or complaint[3] != org_key:
                send_message(peer_id, f"❌ Жалоба #{complaint_id} не найдена в этой организации.")
                return
            user_complaint_id, status, assigned_staff, _, _, _ = complaint
            if status != 'новая':
                send_message(peer_id, f"⚠️ Жалоба #{complaint_id} уже обрабатывается или отработана.")
                return
            update_complaint_status(complaint_id, 'в_работе', staff_id=user_id)
            log_complaint_action(complaint_id, user_id, 'take')
            send_message(peer_id, f"👍 {mention(user_id)} взял жалобу #{complaint_id}.")
            send_message(user_complaint_id, f"🔔 Ваша жалоба #{complaint_id} ({ORG_NAMES[org_key]}) принята в обработку.")
            return

        if text.startswith('#отработал'):
            match = re.search(r'#отработал\s+(\d+)', original_text)
            if not match:
                send_message(peer_id, "❌ Формат: #отработал ID_жалобы")
                return
            complaint_id = int(match.group(1))
            complaint = get_complaint(complaint_id)
            if not complaint or complaint[3] != org_key:
                send_message(peer_id, f"❌ Жалоба #{complaint_id} не найдена в этой организации.")
                return
            user_complaint_id, status, assigned_staff, _, _, _ = complaint
            if status != 'в_работе':
                send_message(peer_id, f"⚠️ Жалоба #{complaint_id} не в работе.")
                return
            if assigned_staff != user_id and not is_user_admin(peer_id, user_id):
                send_message(peer_id, f"⛔ Закрыть может только её исполнитель или администратор чата.")
                return
            update_complaint_status(complaint_id, 'отработана')
            log_complaint_action(complaint_id, user_id, 'close')
            send_message(peer_id, f"✅ Жалоба #{complaint_id} отработана.")
            user_unsent_ratings[user_complaint_id].append((complaint_id, datetime.now()))
            send_message(user_complaint_id,
                "✅ Ваша жалоба отработана. Спасибо!\n"
                "🌟 Пожалуйста, оцените качество обработки (1–5):"
            )
            return

        if text.startswith('#передать'):
            match = re.search(r'#передать\s+(\d+)\s+\[id(\d+)\|.*?\]', original_text, re.IGNORECASE)
            if not match:
                send_message(peer_id, "❌ Формат: #передать ID_жалобы @новый_сотрудник")
                return
            complaint_id = int(match.group(1))
            new_staff_id = int(match.group(2))
            complaint = get_complaint(complaint_id)
            if not complaint or complaint[3] != org_key:
                send_message(peer_id, f"❌ Жалоба #{complaint_id} не найдена в этой организации.")
                return
            user_complaint_id, status, assigned_staff, _, _, _ = complaint
            if status != 'в_работе':
                send_message(peer_id, f"⚠️ Жалоба #{complaint_id} не находится в работе.")
                return
            if assigned_staff != user_id and not is_user_admin(peer_id, user_id):
                send_message(peer_id, "⛔ Передать может только исполнитель или администратор чата.")
                return
            if new_staff_id == user_id and assigned_staff == user_id:
                send_message(peer_id, "❌ Нельзя передать жалобу самому себе.")
                return
            old_staff_id = assigned_staff
            update_complaint_status(complaint_id, 'в_работе', staff_id=new_staff_id)
            log_complaint_action(complaint_id, old_staff_id, 'transfer')
            if is_user_admin(peer_id, user_id) and old_staff_id != user_id:
                transfer_msg = f"🔄 Администратор {mention(user_id)} передал жалобу #{complaint_id} от {mention(old_staff_id)} → {mention(new_staff_id)}"
            else:
                transfer_msg = f"🔄 {mention(old_staff_id)} передал жалобу #{complaint_id} → {mention(new_staff_id)}"
            send_message(peer_id, transfer_msg)
            send_message(user_complaint_id, f"🔔 По вашей жалобе #{complaint_id} назначен новый ответственный.")
            return

        if text.startswith('#связь'):
            match = re.search(r'#связь\s+(\d+)\s+(.+)', original_text, re.I)
            if match:
                cid = int(match.group(1))
                msg_text = match.group(2)
                c = get_complaint(cid)
                if c and c[3] == org_key:
                    full_msg = f"📩 По жалобе #{cid}:\n{msg_text}\n\n💬 Чтобы ответить, используйте команду #ответ [номер жалобы] [ваше сообщение]"
                    send_message(c[0], full_msg)
                    send_message(peer_id, f"✅ Сообщение отправлено {mention(c[0])}.")
                else:
                    send_message(peer_id, f"❌ Жалоба #{cid} не найдена.")
            else:
                send_message(peer_id, "❌ #связь ID текст")
            return

        if text.startswith('#логи'):
            match = re.search(r'#логи\s+(\d+)', original_text)
            limit = int(match.group(1)) if match else 10
            logs = get_recent_logs(limit, org_key)
            if not logs:
                send_message(peer_id, "📭 Логи отсутствуют.")
            else:
                lines = ["📋 Последние действия:"]
                for log in logs:
                    t = log['action_time'].strftime('%Y-%m-%d %H:%M')
                    act = "взял" if log['action'] == 'take' else "закрыл" if log['action'] == 'close' else "передал"
                    lines.append(f"[{t}] #{log['complaint_id']}: {mention(log['staff_id'])} {act}")
                send_message(peer_id, "\n".join(lines))
            return

        return

    # ---------- ОСТАЛЬНЫЕ ЧАТЫ ----------
    if text.startswith(('#взять', '#отработал', '#передать', '#связь', '#логи', '#рейтинг', '#досье', '#жалобы')):
        send_message(peer_id, "🚫 Ограничено, не балуйся.")
        return
    if text == '#проверка' and user_id in MAINTENANCE_ADMINS:
        count_command('#проверка')
        report = run_diagnostics(peer_id, user_id)
        send_message(peer_id, report)
        return

    if text.startswith('/kick'):
        target_id = extract_id_from_mention(original_text)
        if target_id:
            kick_user(peer_id, target_id, user_id)
        else:
            send_message(peer_id, "❌ Укажите пользователя.")
        return
    if text.startswith('/mute'):
        parts = original_text.split()
        if len(parts) >= 2:
            target_id = extract_id_from_mention(parts[1])
            duration = 0
            if len(parts) >= 3:
                dur_str = parts[2]
                if dur_str.endswith('m'): duration = int(dur_str[:-1]) * 60
                elif dur_str.endswith('h'): duration = int(dur_str[:-1]) * 3600
                elif dur_str.endswith('d'): duration = int(dur_str[:-1]) * 86400
                else: duration = int(dur_str)
            if target_id:
                mute_user(peer_id, target_id, user_id, duration)
            else:
                send_message(peer_id, "❌ Неверный формат.")
        else:
            send_message(peer_id, "❌ /mute @user [время]")
        return
    if text.startswith('/unmute'):
        target_id = extract_id_from_mention(original_text)
        if target_id:
            unmute_user(peer_id, target_id, user_id)
        else:
            send_message(peer_id, "❌ Укажите пользователя.")
        return
    if text.startswith('/ban'):
        target_id = extract_id_from_mention(original_text)
        if target_id:
            ban_user(peer_id, target_id, user_id)
        else:
            send_message(peer_id, "❌ Укажите пользователя.")
        return
    if text.startswith('/unban'):
        target_id = extract_id_from_mention(original_text)
        if target_id:
            unban_user(peer_id, target_id, user_id)
        else:
            send_message(peer_id, "❌ Укажите пользователя.")
        return
    if text.startswith('/setadmin'):
        target_id = extract_id_from_mention(original_text)
        if target_id:
            set_admin_role(peer_id, target_id, user_id)
        else:
            send_message(peer_id, "❌ Укажите пользователя.")
        return
    if text.startswith('/unadmin'):
        target_id = extract_id_from_mention(original_text)
        if target_id:
            remove_admin_role(peer_id, target_id, user_id)
        else:
            send_message(peer_id, "❌ Укажите пользователя.")
        return
    if text.startswith('/snick') or text.startswith('/setnick'):
        parts = original_text.split(maxsplit=2)
        if len(parts) >= 3:
            target_id = extract_id_from_mention(parts[1])
            if target_id:
                set_nickname(peer_id, target_id, parts[2], user_id)
            else:
                send_message(peer_id, "❌ Неверный формат.")
        else:
            send_message(peer_id, "❌ /snick @user ник")
        return
    if text.startswith('/dnick') or text.startswith('/delnick') or text.startswith('/rnick'):
        target_id = extract_id_from_mention(original_text)
        if target_id:
            delete_nickname(peer_id, target_id, user_id)
        else:
            send_message(peer_id, "❌ Укажите пользователя.")
        return
    if text.startswith('/gnick') or text.startswith('/getnick'):
        target_id = extract_id_from_mention(original_text)
        if target_id:
            get_nickname(peer_id, target_id)
        else:
            send_message(peer_id, "❌ Укажите пользователя.")
        return
    if text == '/nlist':
        list_nicknames(peer_id)
        return
    if text in ('/admins', '/staff'):
        admins = get_chat_admins(peer_id)
        if not admins:
            send_message(peer_id, "ℹ️ В чате нет администраторов.")
        else:
            admin_list = "\n".join([f"👤 {mention(admin_id)}" for admin_id in admins])
            send_message(peer_id, f"👮‍♂️ Администраторы чата:\n{admin_list}")
        return
    if text == '/help':
        help_text = (
            "📋 Команды чат-менеджера:\n"
            "/kick @user – исключить\n"
            "/mute @user [10m/2h/1d] – заглушить\n"
            "/unmute @user – снять мут\n"
            "/ban @user – бан\n"
            "/unban @user – разбан\n"
            "/setadmin @user – назначить админа\n"
            "/unadmin @user – снять админа\n"
            "/admins – список админов\n"
            "/snick @user ник – установить ник\n"
            "/dnick @user – удалить ник\n"
            "/rnick @user – удалить ник (аналог)\n"
            "/gnick @user – показать ник\n"
            "/nlist – все ники"
        )
        if GROUP_ID == "237645354":
            help_text += (
                "\n🔧 Управление рейтингом (только админам группы):\n"
                "/rreset @user – сбросить все оценки сотруднику\n"
                "/rset @user 1-5 – установить оценку последней жалобе\n"
                "/radd @user 1-5 – начислить поощрительный балл\n"
                "/rcheck @user – показать рейтинг сотрудника\n"
                "/rdelete @user ID – удалить оценку жалобы\n"
                "/rclear – очистить все оценки (осторожно!)"
            )
        help_text += "\n\nПо вопросам и ошибкам: https://vk.com/alpha62"
        send_message(peer_id, help_text)
        return

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    init_db()
    setup_schedule()
    threading.Thread(target=run_scheduler, daemon=True).start()
    print("Бот запущен и готов к работе!")

    while True:
        try:
            for event in longpoll.listen():
                try:
                    process_event(event)
                except Exception as e:
                    last_errors.append({'time': datetime.now(), 'msg': str(e)})
                    if len(last_errors) > 5:
                        last_errors.pop(0)
                    print(f"Error in process_event: {e}")
        except requests.exceptions.ReadTimeout:
            print("Longpoll timeout, reconnecting...")
            time.sleep(5)
        except Exception as e:
            print(f"Longpoll error: {e}, reconnecting in 5s...")
            time.sleep(5)