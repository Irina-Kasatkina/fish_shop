# Telegram bot selling fish

The project presents a [Telegram-bot](t.me/moltin_fish_shop_bot) selling fish. A feature of the bot is that it uses [Redis](https://app.redislabs.com/) to remember at what stage the dialogue with a particular user is.

You can test the operation of [this Telegram bot](t.me/moltin_fish_shop_bot) by following the link.

## Your own use of the bot

### How to install

You will need Python version 3.8 to run the bot.

Download the code from GitHub.

Create a virtual environment and activate it:
```
python -m venv venv
cd venv/Scripts
activate
cd ../..
```

Install dependencies with `pip` (or `pip3`, there is a conflict with Python2):
```
pip install -r requirements.txt
```

### Environment variables

Part of the utility settings is taken from the environment variables. To define them, create a `.env` file in the same folder as the scripts, and write data there in the following format: `VARIABLE=value`.

The following required environment variables are available:

- `TELEGRAM_BOT_TOKEN` - The API token of the Telegram bot that will be used to send notifications. If there is no such telegram bot yet, [create it](https://way23.ru/регистрация-бота-в-telegram.html).
- `TELEGRAM_MODERATOR_CHAT_ID` - ID of the bot moderator's chat to which the bot sends error messages.
- `MOLTIN_CLIENT_ID` - ID of the [Moltin] service client (https://www.moltin.com/). To get this key, you need to register on this service.
- `MOLTIN_CLIENT_SECRET` - Moltin service client secret key.
- `REDIS_DB_HOST`, `REDIS_DB_PORT` and `REDIS_DB_PASSWORD` - host, port and password of the Redis database, which can be obtained by registering at [link](https://app.redislabs.com/).

An example of the contents of the .env file:
```
#
TELEGRAM_BOT_TOKEN=958423683:AAEAtJ5Lde5YYfkjergber
TELEGRAM_MODERATOR_CHAT_ID=12345
MOLTIN_CLIENT_ID=kjcfjkk796d7fi7i46xnn8HJFBf465
MOLTIN_CLIENT_SECRET=69869uigxgKIJFRD4747hkjb786
REDIS_DB_HOST=redis-12345.c123.eu-central-1-1.ec1.cloud.redislabs.com
REDIS_DB_PORT=12345
REDIS_DB_PASSWORD=h5269869uigxgKIJFRD4747
```

### How to start

To start the bot, open the `cmd` console and type the command in the command line:
```
python telegram_bot.py
```

### Objective of the project

The code was written for educational purposes in an online course for web developers [dvmn.org](https://dvmn.org/).
