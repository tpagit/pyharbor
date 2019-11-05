import time

import click

from harbor import conf
from harbor.app import App
from harbor.db import base as dbbase
from harbor.utils import GracefulInterruptHandler


@click.group()
def cli():
    pass


@cli.command()
def drop_db():
    dbbase.drop_all()


@cli.command()
def init_db():
    dbbase.drop_all()
    dbbase.create_all()


@cli.command()
def chat_id():
    from harbor.bot.telegram import TelegramBot
    from harbor import conf
    bot = TelegramBot(conf.TELEGRAM_API_KEY, conf.TELEGRAM_CHAT_ID)

    print(bot._get_chat_id())


@cli.command()
def run():
    app = App()

    with GracefulInterruptHandler() as exit_handler:
        while True:
            try:
                app.load()
            except Exception as ex:
                app.release()
                app = App()

            if exit_handler.released:
                app.release()
                break

            time.sleep(conf.UPDATE_FREQUENCY)


if __name__ == "__main__":
    cli()
