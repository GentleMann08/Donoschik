
from custom_json import addData, delData, getData
import openai
from random import choice
from aiogram import types

# Функция для выдали фразы из базы с текстами
def getPhrase(key):
    texts_data = getData('data/texts.json')
    phrase = texts_data[key]
    if type(phrase) == list:
      return choice(phrase)
    return phrase

def keyboardRegroup(*args):
  keyboard = types.InlineKeyboardMarkup()
  for button in args:
    keyboard.add(button)
  return keyboard

def generateResponse(prompt):
  settings = getData("data/gpt_settings.json")
  openai.api_key = settings["openai key"]
  completions = openai.Completion.create(engine=settings["engine"],
                                         prompt=prompt,
                                         max_tokens=settings["max_tokens"],
                                         n=settings["n"],
                                         stop=None,
                                         temperature=settings["temperature"])

  message = completions.choices[0].text.strip()
  return message



def generatePrompt(player, game_path):
	player_data = getData(game_path + f"/{player}.json")
	general_data = getData(game_path + "/general_data.json")
	
	all_data = {**player_data, **general_data}
	
	all_data =  [value for key, value in sorted(all_data.items())]
	
	
	prompt_text = ''
	
	for string in all_data:
		prompt_text += string + '\n'
		
	return prompt_text
