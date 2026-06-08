import os
import json
import requests
import uuid
from datetime import datetime, timedelta
from requests.exceptions import RequestException

GIGACHAT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

CLIENT_ID = os.environ.get("GIGACHAT_CLIENT_ID", "019ea75f-a090-776c-abb4-f4cc236aacb1")
CLIENT_SECRET = os.environ.get("GIGACHAT_CLIENT_SECRET", "MDE5ZWE3NWYtYTA5MC03NzZjLWFiYjQtZjRjYzIzNmFhY2IxOjI2NGE5Zjg2LTkxYTAtNGNhMC04NWNiLWNmNGMzNzNhZDMzZQ==")
SCOPE = "GIGACHAT_API_PERS"

_token = None
_token_expires = datetime.now()

def _get_token():
    global _token, _token_expires
    if _token and datetime.now() < _token_expires:
        return _token
    if not CLIENT_ID or not CLIENT_SECRET:
        return None
    try:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {CLIENT_SECRET}"
        }
        data = {"scope": SCOPE}
        resp = requests.post(GIGACHAT_AUTH_URL, headers=headers, data=data, verify=False, timeout=15)
        resp.raise_for_status()
        body = resp.json()
        _token = body["access_token"]
        _token_expires = datetime.now() + timedelta(seconds=body.get("expires_in", 300) - 60)
        return _token
    except Exception as e:
        return None

_warhammer_topics = [
    "Ересь Хоруса и её последствия для Империума",
    "Битва на Макрагге — разгром флота Тираннидов",
    "Примархи: отцы Космического Десанта",
    "Тёмные боги Варпа и их влияние на галактику",
    "Падение Кадии и Великий Разлом",
    "Имперские рыцари — титаны полей сражений",
    "Тау: Империя Высшего Блага",
    "Некроны: пробуждение древней угрозы",
    "Бог-Император: мифы и реальность",
    "Орки и природа WAAAGH!",
    "Эльдары: павшая цивилизация",
    "Космические Волки: история ордена",
    "Ультрамарины: опора Империума",
    "Чёрные Крестовые Походы Аббадона",
    "Инквизиция: стражи веры человечества",
    "Жиллиман и возрождение Империума",
]

def generate_post(topic=None, style="lore"):
    token = _get_token()
    if token:
        return _generate_via_api(token, topic, style)
    return None

def generate_mock_post(topic=None):
    return _generate_mock(topic)

def _generate_via_api(token, topic, style):
    if not topic:
        topic = _warhammer_topics[__import__('random').randint(0, len(_warhammer_topics) - 1)]
    style_prompt = {
        "lore": "Напиши подробный аналитический пост в стиле летописца Империума. Используй торжественный, эпический тон.",
        "battle": "Опиши сражение в стиле военного отчёта. Добавь детали тактики и атмосферу битвы.",
        "character": "Расскажи о персонаже как легенду. Добавь цитаты и исторический контекст.",
    }
    system_prompt = (
        "Ты — летописец Империума Человечества из вселенной Warhammer 40,000. "
        "Пиши на русском языке. Используй эпический, торжественный стиль. "
        "Добавь атмосферу мрачного будущего. Максимум 1500 символов. "
        f"{style_prompt.get(style, style_prompt['lore'])}"
    )
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Напиши пост на тему: {topic}"}
        ],
        "temperature": 0.8,
        "max_tokens": 1500,
    }
    try:
        resp = requests.post(GIGACHAT_API_URL, headers=headers, json=payload, verify=False, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        title = _generate_title(topic)
        return {"title": title, "content": content.strip(), "topic": topic}
    except Exception:
        return _generate_mock(topic)

def _generate_mock(topic):
    import random
    if not topic:
        topic = random.choice(_warhammer_topics)
    title = _generate_title(topic)
    mock_content = (
        f"В мрачной тьме далёкого будущего есть только война. "
        f"Тема '{topic}' требует глубочайшего анализа с точки зрения истории Империума.\n\n"
        f"Сорок первое тысячелетие — эпоха бесконечных конфликтов. "
        f"Империум Человечества, разбросанный по миллиону миров, ведёт свою вечную войну "
        f"против бесчисленных врагов. Каждый день приносит новые сражения, "
        f"каждая победа — лишь отсрочка неизбежного.\n\n"
        f"Однако даже в этой тьме есть место для героев. "
        f"Космические десантники, Адептус Астартес, стоят на страже человечества, "
        f"готовые отдать жизнь во имя Императора. "
        f"Их генетически улучшенные тела и непоколебимая вера делают их "
        f"самыми грозными воинами в галактике.\n\n"
        f"Но тьма сгущается. Хаос шепчет свои обещания силы. "
        f"Ксеносы точат свои клинки. И только вера в Императора "
        f"и силу человеческого духа может спасти галактику от полного уничтожения.\n\n"
        f"Император защищает."
    )
    return {"title": title, "content": mock_content, "topic": topic}

def _generate_title(topic):
    import random
    prefixes = [
        "Хроники Империума: ", "Архивы Терры: ", "Сказания о ",
        "Легенды: ", "Трактат: ", "Анализ: ", "Эпоха: ",
    ]
    return f"{random.choice(prefixes)}{topic}"

def get_available_topics():
    return _warhammer_topics

def is_configured():
    return bool(CLIENT_ID and CLIENT_SECRET)
