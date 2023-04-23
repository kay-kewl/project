import time

from telethon.sync import TelegramClient
from telethon import events

# vars
api_id = 12345678
api_hash = ''
bot_token = ''
bot_users = {1664364250}
me = 1664364250
help_message = '/help - send help\n' \
               '/add_user [id] - adds user to the bot users\n' \
               '/del_user [id] - deletes user from the bot users\n' \

users = {}
# bot
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
print('bot works')


@bot.on(events.NewMessage(pattern='^/help$'))
async def send_help_pls(event):
    message = event.message
    id = message.chat_id
    if id in bot_users:
        await bot.send_message(id, help_message)
    else:
        response = 'Error 401: Access Denied\nYou can cry about it later.'
        await bot.send_message(id, response)


@bot.on(events.NewMessage(pattern='^/add_user'))
async def add_bot_user(event):
    message = event.message
    id = message.chat_id
    if id not in bot_users:
        await bot.send_message(id, 'Leave me alone.')
        return
    another_id = int(message.split()[1])
    bot_users.add(another_id)
    user = await bot.get_entity(another_id)
    first_name = user.first_name
    last_name = user.last_name
    name = ' '.join([first_name, last_name]) if last_name else first_name
    users[another_id] = {
        'name': first_name,
        'surname': last_name,
        'bot': False
    }
    response = f'Success. Access was granted to the user with id {another_id}'
    time.sleep(5)
    await bot.send_file(id, response)
    time.sleep(2)
    await bot.send_message(id, f'{name} can now finally text me!')


@bot.on(events.NewMessage(pattern='^/del_user'))
async def del_bot_user(event):
    global bot_users
    message = event.message
    id = message.chat_id
    if id not in bot_users:
        await bot.send_message(id, 'You number was blacklisted.')
        return
    another_id = int(message.split()[1])
    if another_id == me:
        if id != me:
            bot_users = bot_users.difference({id})
            await bot.send_message(id, 'You are no longer my friend.')
        else:
            await bot.send_message(id, 'Why am I doing this?')
    bot_users = bot_users.difference({another_id})
    user = await bot.get_entity(another_id)
    first_name = user.first_name
    last_name = user.last_name
    name = ' '.join([first_name, last_name]) if last_name else first_name
    response = f'Success. Access rights were revoked from the user with id {another_id}'
    time.sleep(5)
    await bot.send_file(id, response)
    time.sleep(2)
    await bot.send_message(id, f'{name} can no longer text me!')


@bot.on(events.NewMessage(pattern='^/on$'))
async def turn_on(event):
    message = event.message
    id = message.chat_id
    if id not in bot_users:
        await bot.send_message(id, 'I forbid you to write me ever again.')
        return
    if not users[id]['bot']:
        users[id]['bot'] = True
        await bot.send_message(id, f'{users[id]["name"]} I will now answer all your messages.')
    else:
        await bot.send_message(id, f'{users[id]["name"]} I thought we were on the same page...')


@bot.on(events.NewMessage(pattern='^/off$'))
async def turn_off(event):
    message = event.message
    id = message.chat_id
    if id not in bot_users:
        await bot.send_message(id, "Don't patronize me, you goon.")
        return
    if users[id]['bot']:
        users[id]['bot'] = False
        await bot.send_message(id, f'{users[id]} I will now answer all your messages.')
    else:
        await bot.send_message(id, f'{users[id]["name"]} I thought we were on the same page...')


@bot.on(events.NewMessage)
async def answering(event):
    message = event.message
    id = message.chat_id
    await bot.send_message(id, message)




