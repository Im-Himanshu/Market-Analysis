from telegram.ext import Updater, InlineQueryHandler, CommandHandler
import requests
import re
import json

def get_url(term):
    headers = {
        'Accept': 'application/json',
    }
    params = (
        ('term', term),
    )
    response = requests.get('https://icanhazdadjoke.com/search', headers=headers, params=params)
    response = json.loads(response.text);
    if response['total_jokes'] < 1 :
        return get_url('hipster'); #if no jokes are found then do this..
    return response['results'];

def joke(bot, update):
    str = update.message.text.split(' ')[1]
    chat_id = update.message.chat_id
    print("query came ", str, "from user : " , chat_id)
    if(str == None or str == ''):
        bot.send_message(chat_id=chat_id, text='Send a valid joke type');
    responses = get_url(str)
    print(responses)
    for response in responses:
        bot.send_message(chat_id=chat_id, text=response['joke']);

def start(bot, update) :
    print(update.message.text)
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id,text = 'Send command like "/joke Topic"  to get a joke for that topic i.e. /joke hipster');
    bot.send_message(chat_id=chat_id,text = 'If the search result doesnt match any query it will send result of a default query : hipster');
    bot.send_message(chat_id=chat_id,
                     text='try : hipster, man, girls, fake, school,');
def main():
    updater = Updater('1127561839:AAEFl4cMq-XC7CvTXk2yXrMUOJsXE2oVuQE')
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('bop',joke))
    dp.add_handler(CommandHandler('joke',joke))
    dp.add_handler(CommandHandler('start',start))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()