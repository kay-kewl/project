import csv
import datetime
import time
import pandas as pd
import numpy as np
from telethon.tl.types import ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRow
from telethon.sync import TelegramClient
from telethon import events
from db import db_session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import BallTree
from sklearn.base import BaseEstimator
from sklearn.pipeline import make_pipeline
from db.user import User
from db.ids import Id

api_id = 12345678
api_hash = ''
bot_token = ''
me = 1664364250
bot_users = {me}


help_message = '/help - sends help\n' \
               '/add_user [id] - adds user to bot users\n' \
               '/del_user [id] - deletes user from bot users\n' \
               '/on - turns on bot to chat\n' \
               '(alterntive: "Начать разговор")\n' \
               '/off - turns off bot to access functions\n' \
               '(alternative: "Закончить разговор")\n' \
               '/send_log - sends log.csv\n' \
               '/clear_log - clears log.csv\n' \
               '/list - returns list of people who accessed bot\n' \
               '/context_count - returns list of people and the amount of ' \
               'context for log'

users = {
    me:
        {
            'name': 'Кирилл',
            'surname': '',
            'bot': False,
            'sending_file': False
        }
}

FIELDNAMES = ['id', 'timestamp', 'input', 'output', 'mark', 'suggestion']
commands = ['/help', '/add_user', '/del_user', '/on', '/off', '/send_log', '/clear_log',
            'Начать разговор', 'Закончить разговор', '/start', '/update_data']
on_and_off_commands = ['/on', 'Начать разговор', '/off', 'Закончить разговор', '/help']
log = []
db_session.global_init("db/bot.db")

replies = pd.read_csv('data/data_ok.csv', sep=';')
vectorizer = TfidfVectorizer()
vectorizer.fit(replies.input)
matrix = vectorizer.transform(replies.input)

s = time.time()
svd = TruncatedSVD(n_components=100)
svd.fit(matrix)
matrix = svd.transform(matrix)
print(time.time() - s)


class WordNextDoor(BaseEstimator):
    def __init__(self, k=5, temperature=1.0):
        self.k = k
        self.temperature = temperature

    def fit(self, matrix, words):
        self.matrix = BallTree(matrix)
        self.words = np.array(words)

    def predict(self, word):
        distances, indices = self.matrix.query(
            word, return_distance=True, k=self.k)
        distances_indices = zip(distances, indices)
        result = []
        for distance, index in distances_indices:
            p = self.find_max(distance * self.temperature)
            result.append(np.random.choice(index, p=p))
        return self.words[result]

    def find_max(self, x):
        probe = np.exp(-x)
        return probe / sum(probe)


wnd = WordNextDoor()
wnd.fit(matrix, replies.output)
pipe = make_pipeline(vectorizer, svd, wnd)

# bot
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

btns0 = ReplyKeyboardMarkup(
    rows=
    [
        KeyboardButtonRow(
            [
                KeyboardButton(text='Начать разговор'),
                KeyboardButton(text='/help')
            ]
        ),
        KeyboardButtonRow(
            [
                KeyboardButton(text='/send_log')
            ]
        )
    ],
    resize=True
)
btns1 = ReplyKeyboardMarkup(
    [
        KeyboardButtonRow(
            [
                KeyboardButton(text='Закончить разговор'),
                KeyboardButton(text='/help')
            ]
        ),
        KeyboardButtonRow(
            [
                KeyboardButton(text='/send_log')
            ]
        )
    ],
    resize=True
)
all_btns = ReplyKeyboardMarkup(
    [
        KeyboardButtonRow(
            [
                KeyboardButton(text='Начать разговор'),
                KeyboardButton(text='/on')
            ]
        ),
        KeyboardButtonRow(
            [
                KeyboardButton(text='/send_log'),
                KeyboardButton(text='/clear_log')
            ]
        ),
        KeyboardButtonRow(
            [
                KeyboardButton(text='/list'),
                KeyboardButton(text='/context_count')
            ]
        ),
        KeyboardButtonRow(
            [
                KeyboardButton(text='/update_data')
            ]
        )
    ],
    resize=True
)

print('bot works')


@bot.on(events.NewMessage(pattern='^/help$'))  # works
async def send_help_pls(event):
    message = event.message
    id = message.chat_id
    if id in bot_users:
        if users[id]['bot']:
            await bot.send_message(id, f"Hey, {users[id]['name']}! "
                                       f"You can now talk to me and I'll answer",
                                   buttons=btns1)
            return
        await bot.send_message(id, help_message, buttons=all_btns)
    else:
        response = 'Error 401: Access Denied\nYou can cry about it ~~later~~ now.'
        await bot.send_message(id, response)


@bot.on(events.NewMessage(pattern='^/add_user'))  # works
async def add_bot_user(event):
    message = event.message
    id = message.chat_id
    if id not in bot_users:
        await bot.send_message(id, 'Leave me alone.')
        return
    if users[id]['bot']:
        return
    another_id = int(message.message.split()[1])
    bot_users.add(another_id)
    users[another_id] = {
        'name': '',
        'surname': '',
        'bot': False,
        'sending_file': False
    }
    response = f'Success. Access was granted to user with id {another_id}'
    time.sleep(2)
    await bot.send_message(id, response)
    time.sleep(2)
    await bot.send_message(id, f'{another_id} can now finally text me!')


@bot.on(events.NewMessage(pattern='^/del_user'))  # works
async def del_bot_user(event):
    global bot_users
    message = event.message
    id = message.chat_id
    if id not in bot_users:
        await bot.send_message(id, 'You were blacklisted.')
        return
    if users[id]['bot']:
        return
    another_id = int(message.message.split()[1])
    if another_id == me:
        if id != me:
            bot_users = bot_users.difference({id})
            await bot.send_message(id, 'Why would I do that?')
        else:
            await bot.send_message(id, 'Are you deranged?')
        return
    bot_users = bot_users.difference({another_id})
    user = await bot.get_entity(another_id)
    first_name = user.first_name
    last_name = user.last_name
    name = ' '.join([first_name, last_name]) if last_name else first_name
    response = f'Success. Access rights were revoked from user with id {another_id}'
    time.sleep(2)
    await bot.send_message(id, response)
    time.sleep(2)
    await bot.send_message(id, f'{name} can no longer text me!')


@bot.on(events.NewMessage(pattern='^/on$'))  # works
async def turn_on(event):
    message = event.message
    id = message.chat_id
    if id not in bot_users:
        await bot.send_message(id, 'I forbid you to write me ever again.')
        return
    if users[id]['bot']:
        return
    else:
        users[id]['bot'] = True
        await bot.send_message(id, f'{users[id]["name"]} '
                                   f'I will now answer all your messages.',
                               buttons=btns1)


@bot.on(events.NewMessage(pattern='^/off$'))  # works
async def turn_off(event):
    message = event.message
    id = message.chat_id
    if id not in bot_users:
        await bot.send_message(id, "Don't patronize me, you goon.")
        return
    if users[id]['bot']:
        users[id]['bot'] = False
        await bot.send_message(id, f'{users[id]["name"]} '
                                   f'I will no longer answer to your messages.',
                               buttons=btns0)
    else:
        await bot.send_message(id, f'{users[id]["name"]} '
                                   f'I thought we were on the same page...')


@bot.on(events.NewMessage)  # about file
async def answering(event):
    message = event.message
    id = message.chat_id
    if users[id]['name'] == users[id]['surname'] == '':
        user = await bot.get_entity(id)
        first_name = user.first_name
        last_name = user.last_name
        users[id]['name'] = first_name
        users[id]['surname'] = last_name
        db_sess = db_session.create_session()
        if not db_sess.query(Id).filter(Id.tg_id == id).all():
            new_user = User()
            new_user.name = first_name
            new_user.surname = last_name
            new_user.context_count = 0
            new_user.first_access = datetime.datetime.now().strftime('%d/%B/%Y %H:%M:%S.%f')
            new_id = Id()
            new_id.tg_id = id
            db_sess.add(new_user)
            db_sess.add(new_id)
            db_sess.commit()
    if not (id in bot_users):
        await bot.send_message(id, "Don't waste my time!")
        return
    if not users[id]['bot']:
        if not any(x in message.message for x in commands) and not \
                users[id]['sending_file']:
            await bot.send_message(id, 'Unrecognized command')
        if users[id]['sending_file']:
            if message.document:
                file = await message.download_media()
                response = check_file(file)
                await bot.send_message(id, response)
                if 'successfully update' in response:
                    users[id]['sending_file'] = False
            else:
                await bot.send_message(id, 'Still waiting for that file tho...')
        return
    if users[id]['bot'] and any(x in message.message for x in commands):
        if message.message not in on_and_off_commands:
            await bot.send_message(id, 'Эй, ты мне не командир!')
        return
    current = {
        'id': id,
        'timestamp': datetime.datetime.now().strftime('%d/%B/%Y %H:%M:%S.%f'),
        'input': message.message.lower()
    }
    db_sess = db_session.create_session()
    db_sess.query(User).filter(User.tg_id == id).first().context_count += 1
    db_sess.commit()
    answer = get_answer(current)
    await bot.send_message(id, answer)


@bot.on(events.NewMessage(pattern='^Начать разговор$'))  # works
async def start_dialog(event):
    await turn_on(event)


@bot.on(events.NewMessage(pattern='^Закончить разговор$'))  # works
async def finish_dialog(event):
    await turn_off(event)


@bot.on(events.NewMessage(pattern='^/start$'))  # works
async def start_bot(event):
    id = event.message.chat_id
    await bot.send_message(id, 'Hello, stranger')
    time.sleep(1)
    await bot.send_message(
        id, '**I am your digital ~~assistant~~ __friend__**\n'
            'Let me tell you what I can!')
    time.sleep(1)
    sparkles = '\U00002728'
    await bot.send_message(
        id, f'My main function is to\n{sparkles} __reply to your messages__ {sparkles}\n'
            'as best as I can that is', buttons=KeyboardButton(text='/help'))


@bot.on(events.NewMessage(pattern='^/send_log$'))  # works
async def send_log(event):
    message = event.message
    id = message.chat_id
    db_sess = db_session.create_session()
    if not (id in bot_users) or \
            not db_sess.query(User).filter(User.tg_id == id).first().log_access:
        await bot.send_message("Don't you dare.")
        return
    if users[id]['bot']:
        return
    upload_log()
    await bot.send_file(id, 'log.csv')
    await bot.send_file(id, 'replies.csv')


@bot.on(events.NewMessage(pattern='^/clear_log$'))  # works
async def clear_log_file(event):
    message = event.message
    id = message.chat_id
    db_sess = db_session.create_session()
    if not (id in bot_users) or \
            not db_sess.query(User).filter(User.tg_id == id).first().log_access:
        await bot.send_file(id, '6.jpg')
        return
    if users[id]['bot']:
        return
    with open('log.csv', 'w', newline='', encoding='utf8') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(FIELDNAMES)
    await bot.send_message(id, 'log.csv was successfully cleared')
    if id != me:
        name = users[id]['name']
        if users[id]['surname']:
            name += ' ' + users[id]['surname']
        await bot.send_message(me, 'log.csv was cleared by ' + name)


@bot.on(events.NewMessage(pattern='^/update_data$'))  # works
async def update_data(event):
    message = event.message
    id = message.chat_id
    db_sess = db_session.create_session()
    if not (id in bot_users) or \
            not db_sess.query(User).filter(User.tg_id == id).first().update_dataset:
        await bot.send_file(id, 'data/5.jpg')
        return
    if users[id]['bot']:
        return
    users[id]['sending_file'] = True
    await bot.send_message(id, 'I am now waiting for the .csv file')


@bot.on(events.NewMessage(pattern='^/list$'))
async def show_list(event):
    message = event.message
    id = message.chat_id
    if not (id in bot_users):
        await bot.send_file(id, 'data/6.jpg')
        return
    if users[id]['bot']:
        return
    db_sess = db_session.create_session()
    people = db_sess.query(User).filter(User.first_access)
    await bot.send_message(id, '\n'.join(
        [' '.join([i.name, i.surname, i.first_access]) for i in people]))


@bot.on(events.NewMessage(pattern='^/context_count$'))
async def show_list(event):
    message = event.message
    id = message.chat_id
    if not (id in bot_users):
        await bot.send_file(id, 'data/6.jpg')
        return
    if users[id]['bot']:
        return
    db_sess = db_session.create_session()
    people = db_sess.query(User).filter(User.first_access)
    await bot.send_message(id, '\n'.join([' '.join(
        [i.name, i.surname, i.context_count]) for i in people]))


def check_file(file):
    if file.split('.')[1] != 'csv':
        return 'Wrong file! I am expecting .csv file not .' + file.split('.')[1]
    try:
        with open(file, encoding='utf8') as file, \
                open('data/data1.csv', encoding='utf8', mode='a') as out:
            reader = csv.reader(file, delimiter=';')
            writer = csv.writer(out, delimiter=';')
            writer.writerows(reader)
        return 'Dataset was successfully updated.'
    except Exception as e:
        return "Can't update dataset with this .csv file!"


def get_answer(current):  # works
    text = current['input'].lower()
    ans = pipe.predict([text])[0]
    ans = ans.replace(' ,', ',')
    ans = ans.replace(' .', '.')
    ans = ans.replace(' ?', '?')
    ans = ans.replace(' !', '!')
    ans = ans.replace(' "', '"')
    ans = ans.replace(' - ', '-')
    ans = ans.capitalize()
    if ans[-1] == '.':
        ans = ans[:-1]
    current['output'] = ans.lower()
    current['mark'] = '-'
    log.append(current)
    if len(log) == 1000:
        upload_log()
    return ans


def upload_log():  # well it works but needs improvement
    with open('log.csv', 'a', encoding='utf8', newline='') as file:
        writer = csv.DictWriter(file, delimiter=';', fieldnames=FIELDNAMES)
        writer.writerows(log)
    replies_log = []
    for id in set([i['id'] for i in log]):
        user_data = list(filter(lambda x: x['id'] == id, log))
        replies_log += [
            {
                'id': id,
                'timestamp': user_data[i]['timestamp'],
                'input': user_data[i - 1]['output'],
                'output': user_data[i]['input'],
                'mark': '-'
            }
            for i in range(1, len(user_data))
        ]
    replies_log.sort(key=lambda x: x['timestamp'])
    with open('replies.csv', 'a', encoding='utf8', newline='') as file:
        writer = csv.DictWriter(file, delimiter=';', fieldnames=FIELDNAMES)
        writer.writerows(replies_log)
    log.clear()
    replies_log.clear()


with bot:
    bot.run_until_disconnected()
