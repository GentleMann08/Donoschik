import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from custom_json import getData, addData, delData
from auxiliary_modules import getPhrase, keyboardRegroup

config_data = getData("data/config.json")

API_TOKEN = config_data["telegram api"] 
DESTINATION_CHAT_ID = config_data["negotiator"]
message_ids = {}
advisors = {}
advisor_translates = {
  "senior advisor": "Старший советник",
  "negotiator": "Переговорщик",
  "leisure": "Советник по досугу",
  "informer": "Советник по информации"
}
answers = {}
all_messages = {}

def report(message: types.Message):
  print(
   f' [{message.message_id}] \n',
   f'User ID: "{message.from_user.id}"; \n',
   f'Username: "{message.from_user.username}"; \n',
   f'Chat ID: {message.chat.id}"; \n',
   f'Message text: "{message.text}";'
  )
  
  data = {
    "User ID": str(message.from_user.id),
    "Username": str(message.from_user.username),
    "Chat ID": str(message.chat.id),
    "Message text": str(message.text)
  }

  addData("data/history.json", key=str(message.message_id), value=data)

def regroupAdvisorKeyboard(message: types.Message):
  keyboard = types.InlineKeyboardMarkup()
  for advisor in advisors[message.chat.id]:
    advisor_status = advisors[message.chat.id][advisor]
    emoji = "✅" if advisor_status else "❌"
    keyboard.add(types.InlineKeyboardMarkup(text=f"{emoji} {advisor_translates[advisor]}",
                                            callback_data=f'{advisor}_callback')
                )
  return keyboard


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    report(message)
    addData('data/all_chats.json', key=message.chat.id, value=message.from_user.username)
    advisors[message.chat.id] = {}
    for advisor in config_data["advisors"]:
        advisors[message.chat.id][advisor] = False
    start_button = types.InlineKeyboardMarkup(text="Начать", callback_data="start_callback")
    help_button = types.InlineKeyboardMarkup(text="Помощь", callback_data="help_callback")
    bot_message = await bot.send_message(chat_id=message.chat.id, 
                                         text=getPhrase('welcome'), 
                                         reply_markup=keyboardRegroup(start_button, help_button)
                                        )
    # Save the sent message ID for the user
    message_ids[message.from_user.id] = [bot_message.message_id]


@dp.callback_query_handler(lambda callback: callback.data == "start_callback")
async def start_work(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    text = getPhrase('denunciation')
    keyboard = regroupAdvisorKeyboard(callback.message)
    help_button = types.InlineKeyboardMarkup(text="Помощь", callback_data="help_callback")
    keyboard.add(help_button)
    await bot.edit_message_text(chat_id=chat_id,
                                message_id=message_ids[callback.from_user.id][-1],
                                text=text, reply_markup=keyboard)


@dp.callback_query_handler(lambda callback: callback.data == "help_callback")
async def help_command(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    functions_button = types.InlineKeyboardButton(text="Как пользоваться?", callback_data="functions help")
    advisors_button = types.InlineKeyboardButton(text="Кто за что отвечает?", callback_data="advisors help")
    exit_to_start_button = types.InlineKeyboardButton(text="Начать", callback_data="start_callback")

    text = getPhrase('help')
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[functions_button], [advisors_button], [exit_to_start_button]])
    bot_message = await bot.edit_message_text(chat_id=chat_id, message_id=message_ids[user_id][-1], text=text, reply_markup=keyboard)
    message_ids[user_id] = [bot_message.message_id]

@dp.callback_query_handler(lambda callback: callback.data == "functions help")
async def help_functions(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    exit_to_help_button = types.InlineKeyboardButton(text="Выход", callback_data="help_callback")

    text = getPhrase('help functions')
    keyboard = keyboardRegroup(exit_to_help_button)
    bot_message = await bot.edit_message_text(chat_id=chat_id, message_id=message_ids[user_id][-1], text=text, reply_markup=keyboard)
    message_ids[user_id] = [bot_message.message_id]

@dp.callback_query_handler(lambda callback: callback.data.endswith("_callback"))
async def advisor_callback_handler(callback: types.CallbackQuery):
    report(callback.message)
    chat_id = callback.message.chat.id
    advisor_name = callback.data[:-9]  # Убираем "_callback" с конца
    if advisor_name in advisors[chat_id]:
        advisors[chat_id][advisor_name] = not advisors[chat_id][advisor_name]  # Инвертируем флаг
        text = getPhrase('denunciation')
        keyboard = regroupAdvisorKeyboard(callback.message)
        await bot.edit_message_text(chat_id=chat_id,
                                    message_id=message_ids[callback.from_user.id][-1],
                                    text=text, reply_markup=keyboard)

@dp.callback_query_handler(lambda callback: callback.data == "advisors help")
async def advisors_help(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    
    advisor_buttons = []  # Создаем список строк с кнопками
    for advisor in advisors[chat_id]:
        advisor_buttons.append([
            types.InlineKeyboardButton(
                text=advisor_translates[advisor],
                callback_data=f"{advisor}_help"  # Используем advisor как часть callback_data
            )
        ])
    
    exit_to_help_button = types.InlineKeyboardButton(text="Выход", callback_data="help_callback")
    
    text = 'Какой советник Вас интерисует?'
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=advisor_buttons + [[exit_to_help_button]])
    bot_message = await bot.edit_message_text(chat_id=chat_id, message_id=message_ids[user_id][-1], text=text, reply_markup=keyboard)
    message_ids[user_id] = [bot_message.message_id]

@dp.callback_query_handler(lambda callback: callback.data.endswith("_help"))
async def advisor_help(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.message.from_user.id
    advisor_name = callback.data[:-5]  # Убираем "_help" с конц
    back_button = types.InlineKeyboardButton(text="Назад", callback_data="advisors help")
    keyboard = keyboardRegroup(back_button)
    help_phrase = getPhrase(f"{advisor_name}_help")
    bot_message = await bot.edit_message_text(chat_id=chat_id, message_id=message_ids[chat_id][-1], text=help_phrase, reply_markup=keyboard)


@dp.message_handler(content_types=['text'])
async def text_handler(message: types.Message):
  report(message)
  all_messages[message.message_id] = message
  chat_id = message.chat.id
  answer_flag = bool(message.reply_to_message)
  second_message = message
  flag = False
  if not answer_flag:
    for advisor in advisors[chat_id]:
      if advisors[chat_id][advisor]:
        first_message = await bot.send_message(chat_id=config_data[advisor], text=message.text)
        answers[first_message] = second_message
        flag = True
    if flag == True:
      await bot.send_message(chat_id=chat_id, text="Сообщение отправлено!")
    else:
      await bot.send_message(chat_id=chat_id, text="Не выбраны советники.")
  else:
    for iteration_message in answers:
      if message.reply_to_message.message_id == iteration_message.message_id:
        original_message = answers[message.reply_to_message]
        first_message = await bot.send_message(chat_id=original_message.chat.id, text=message.text, reply_to_message_id=original_message.message_id)
        answers[first_message] = second_message
        
        

if __name__ == '__main__':
    for chat_id in getData('data/all_chats.json'):
      advisors[chat_id] = {}
      for advisor in config_data["advisors"]:
        advisors[chat_id][advisor] = False
        
    executor.start_polling(dp, skip_updates=True)
