import telebot
from telebot import types
from dotenv import load_dotenv
import random
import os
import json


load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

with open("questions.json", encoding="utf-8") as f:
    all_questions = json.load(f)

CATEGORIES = list(all_questions.keys())

user_data = {}

right_answers = ["Верно! 👍", "Молодец!", "Это правильный ответ!", "Отлично!"]
wrong_answers = ["Неверно! 😥", "Нет, попробуй ещё!", "Промах!", "Увы, пока не верно."]


def reset_user(user_id):
    user_data.pop(user_id, None)


@bot.message_handler(commands=['quiz'])
def start_category_selection(message):
    reset_user(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for category in CATEGORIES:
        markup.add(types.KeyboardButton(category))
    bot.send_message(message.chat.id, "Выберите тему квиза:", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text in CATEGORIES)
def start_quiz(message):
    user_id = message.from_user.id
    category = message.text
    selected_q = random.sample(all_questions[category], 5)
    user_data[user_id] = {
        "category": category,
        "questions": selected_q,
        "curr": 0,
        "points": 0,
        "options_shuffled": []
    }
    bot.send_message(message.chat.id, f"Начинаем викторину по теме: {category}")
    send_question(message.chat.id, user_id)


def send_question(chat_id, user_id):
    state = user_data.get(user_id)
    if not state:
        bot.send_message(chat_id, "Викторина не найдена. Используйте /quiz чтобы начать.")
        return

    curr = state["curr"]
    questions = state["questions"]
    if curr < len(questions):
        q = questions[curr]
        options = q["options"][:]
        random.shuffle(options)  
        state["options_shuffled"] = options

        markup = types.InlineKeyboardMarkup()
        for opt in options:
            markup.add(types.InlineKeyboardButton(opt, callback_data=opt))
        bot.send_message(
            chat_id,
            f"{curr+1}) {q['question']}",
            reply_markup=markup
        )
    else:
        points = state["points"]
        bot.send_message(
            chat_id,
            f"Викторина завершена!\nВаши баллы: {points}/{len(questions)}",
            reply_markup=types.ReplyKeyboardRemove()
        )
        reset_user(user_id)


@bot.callback_query_handler(func=lambda call: True)
def handle_inline_answer(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    state = user_data.get(user_id)
    if not state:
        bot.answer_callback_query(call.id, 'Начните новую викторину командой /quiz')
        return

    curr = state["curr"]
    question = state["questions"][curr]
    correct_answer = question["answer"]
    selected = call.data

    if selected == correct_answer:
        bot.send_message(chat_id, random.choice(right_answers))
        state["points"] += 1
    else:
        bot.send_message(chat_id, random.choice(wrong_answers) + f"\nПравильный ответ: {correct_answer}")

    state["curr"] += 1
    send_question(chat_id, user_id)

@bot.message_handler(content_types=['text'])
def remind_use_quiz(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        bot.send_message(message.chat.id, "Чтобы начать викторину, отправьте /quiz")


bot.infinity_polling()
