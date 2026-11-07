import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("API kalitlari .env faylida topilmadi!")

client = genai.Client(api_key=GEMINI_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"] = []
    await update.message.reply_text(
        "Assalomu alaykum! 🤖\n\n"
        "Men Universal AI yordamchisiman.\n"
        "Savol yozing yoki rasm yuboring!\n\n"
        "/clear — suhbat tarixini tozalash"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"] = []
    await update.message.reply_text("Suhbat tarixi tozalandi! ✅")


def ask_ai(prompt):
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )
    return response.text or "Javob yaratilmadi."


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    history = context.user_data.setdefault("history", [])

    prompt = (
        "Sen Universal AI yordamchisisan. "
        "O'zbek, rus va ingliz tillarida javob ber. "
        "Savollarga aniq va tushunarli javob ber.\n\n"
    )

    for item in history[-10:]:
        prompt += f"{item['role']}: {item['text']}\n"

    prompt += f"Foydalanuvchi: {question}\nAI:"

    try:
        await update.message.chat.send_action("typing")
        answer = await asyncio.to_thread(ask_ai, prompt)

        history.append({"role": "Foydalanuvchi", "text": question})
        history.append({"role": "AI", "text": answer})
        context.user_data["history"] = history[-20:]

        for i in range(0, len(answer), 4000):
            await update.message.reply_text(answer[i:i+4000])

    except Exception as e:
        print("AI XATOLIK:", repr(e))
        await update.message.reply_text("AI bilan bog'lanishda xatolik yuz berdi.")


def analyze_image(image_bytes, question):
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/jpeg"
    )

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=[
            question,
            image_part
        ]
    )
    return response.text or "Rasm tahlil qilinmadi."


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("Rasmni tahlil qilyapman... 🔍")

        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        image_bytes = bytes(await photo_file.download_as_bytearray())

        question = update.message.caption or "Bu rasmda nima tasvirlangan? Tushuntirib ber."

        answer = await asyncio.to_thread(
            analyze_image,
            image_bytes,
            question
        )

        await update.message.reply_text(answer[:4000])

    except Exception as e:
        print("RASM XATOLIGI:", repr(e))
        await update.message.reply_text("Rasmni tahlil qilishda xatolik yuz berdi.")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))

    app.add_handler(
        MessageHandler(filters.PHOTO, photo_handler)
    )

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, chat)
    )

    print("UNIVERSAL AI BOT ISHLAYAPTI!")
    app.run_polling()


if __name__ == "__main__":
    main()