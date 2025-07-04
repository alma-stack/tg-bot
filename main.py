from pyrogram import Client, filters
from pyrogram.types import Message
import pymorphy2
from rp_db import add_custom_command, get_custom_command
import config
import random

morph = pymorphy2.MorphAnalyzer()
bot = Client("rp_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

# Падежи pymorphy
CASE_MAP = {
    "n": "nomn",  # именительный
    "v": "accs",  # винительный
    "d": "datv",  # дательный
}

def get_gender(username, default="masc"):
    parsed = morph.parse(username.split()[0])[0]
    return parsed.tag.gender or default

def inflect_name(name: str, case="nomn"):
    parsed = morph.parse(name)[0]
    try:
        inflected = parsed.inflect({case})
        return inflected.word if inflected else name
    except:
        return name

def get_random_member(chat, exclude_ids):
    members = [m for m in chat.members if m.user and m.user.id not in exclude_ids]
    return random.choice(members).user if members else None

@bot.on_message(filters.command("крп", ".") & filters.me)
async def create_rp(client, message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.reply("Пример: `.крп 🐱 @a1 обнимает @a2[d]`")
    emoji, template = parts[1], parts[2]
    command = template.split()[0].lstrip("@").lower()
    add_custom_command(command, emoji, template)
    await message.reply(f"✅ Команда .{command} добавлена!")

@bot.on_message(filters.text & filters.group)
async def handle_rp(client, message: Message):
    if not message.reply_to_message or not message.text.startswith("."):
        return

    parts = message.text[1:].split()
    command = parts[0].lower()

    from_user = message.from_user
    to_user = message.reply_to_message.from_user
    chat = await client.get_chat(message.chat.id)
    chat_members = await client.get_chat_members(message.chat.id, limit=100)

    emoji = "🤝"  # по умолчанию
    gender = get_gender(from_user.first_name)

    # Если команда есть в базе — используем шаблон
    custom = get_custom_command(command)
    if custom:
        emoji, template = custom
        result_text = template

        replacements = {
            "@a1": f"@{from_user.username or from_user.id}",
            "@a2": f"@{to_user.username or to_user.id}"
        }

        name2 = to_user.first_name
        for code, case in CASE_MAP.items():
            tag = f"@a2[{code}]"
            if tag in result_text:
                replacements[tag] = inflect_name(name2, case)

        a3_user = get_random_member(chat_members, exclude_ids={from_user.id, to_user.id})
        if a3_user:
            name3 = a3_user.first_name
            for code, case in CASE_MAP.items():
                tag = f"@a3[{code}]"
                if tag in result_text:
                    replacements[tag] = inflect_name(name3, case)
            replacements["@a3"] = f"@{a3_user.username or a3_user.id}"

        for key, val in replacements.items():
            result_text = result_text.replace(key, val)

        return await message.reply(f"{emoji} | {result_text}")

    # Если кастомной команды нет — обрабатываем глагол
    try:
        verb = morph.parse(command)[0]
        if "INFN" not in verb.tag:
            return  # не инфинитив — пропускаем

        action = verb.inflect({gender}).word
        text = f"{emoji} | @{from_user.username or from_user.id} {action} @{to_user.username or to_user.id}"
        return await message.reply(text)

    except Exception as e:
        print(f"[ERROR RP] {e}")
