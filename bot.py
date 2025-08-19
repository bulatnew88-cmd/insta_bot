import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from instagrapi import Client
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
ALLOWED_USERS = set(map(int, filter(None, os.getenv("ALLOWED_USERS", "").split(","))))

if not BOT_TOKEN or not IG_USERNAME or not IG_PASSWORD:
    print("❌ Ошибка: Проверь .env — должны быть заданы BOT_TOKEN, IG_USERNAME и IG_PASSWORD")
    exit()

# Авторизация Instagram
cl = Client()
try:
    cl.load_settings("ig_settings.json")
    cl.get_timeline_feed()  # тестовый запрос
    print("✅ Сессия Instagram загружена")
except Exception as e:
    print(f"❌ Ошибка входа в Instagram: {e}")
    exit()

# Увеличенный таймаут (важно для больших файлов)
bot = Bot(token=BOT_TOKEN, request_timeout=120)
dp = Dispatcher()

@dp.message(F.text)
async def handle_instagram_link(message: Message):
    # Проверка доступа
    if message.from_user.id not in ALLOWED_USERS:
        await message.reply("⛔ Доступ запрещён")
        return

    url = message.text.strip()
    if "instagram.com" not in url:
        await message.reply("Отправь мне ссылку на Instagram пост.")
        return

    try:
        media_pk = cl.media_pk_from_url(url)
        media_info = cl.media_info(media_pk)
        caption = media_info.caption_text or ""

        # Видео
        if media_info.media_type == 2:
            video_path = cl.video_download_by_url(media_info.video_url, folder="downloads")
            await message.reply_video(
                FSInputFile(video_path),
                caption=caption
            )
            os.remove(video_path)

        # Фото
        elif media_info.media_type == 1:
            photo_path = cl.photo_download_by_url(media_info.thumbnail_url, folder="downloads")
            await message.reply_photo(
                FSInputFile(photo_path),
                caption=caption
            )
            os.remove(photo_path)

        # Альбом
        elif media_info.media_type == 8:
            for item in media_info.resources:
                if item.media_type == 1:
                    img_path = cl.photo_download_by_url(item.thumbnail_url, folder="downloads")
                    await message.reply_photo(FSInputFile(img_path))
                    os.remove(img_path)
                elif item.media_type == 2:
                    vid_path = cl.video_download_by_url(item.video_url, folder="downloads")
                    await message.reply_video(FSInputFile(vid_path))
                    os.remove(vid_path)

    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

async def main():
    print("✅ Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

