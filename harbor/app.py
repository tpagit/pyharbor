from threading import Event
from typing import TYPE_CHECKING, Optional
from urllib.parse import urljoin

from harbor import conf
from harbor.bot import TelegramBot
from harbor.db.models import DbApartment, DbApartmentPhoto
from harbor.db.service import DbService
from harbor import logger
from harbor.provider.manager import provider_manager

if TYPE_CHECKING:
    from harbor.provider.base import PropertyItem


class App:
    def __init__(self):
        self.db = DbService()
        self.telegram_client = TelegramBot.get_default()
        self.telegram_client.start_polling()

        self._is_released = Event()

    def load(self):
        logger.info("Start loading data")
        loaded_items = provider_manager.load()

        for item in loaded_items:
            db_apartment = self._create_or_none(item)

            if db_apartment:
                self.db.add_apartment(db_apartment)

                logger.info(f'New property item:\n{item}')

        logger.info("Finish loading data")

        self.telegram_client.remove_broken_messages()
        self.telegram_client.post_new_apartments()

    def _create_or_none(self, data: 'PropertyItem') -> Optional[DbApartment]:
        exists = self.db.is_apartment_exists(data.provider, data.external_id)

        if exists:
            return None

        db_apartment = DbApartment()
        db_apartment.external_id = data.external_id
        db_apartment.provider = data.provider
        db_apartment.rel_url = data.rel_url
        db_apartment.address = data.address
        db_apartment.rooms = data.rooms
        db_apartment.floor = data.floor
        db_apartment.max_floor = data.max_floor
        db_apartment.square = data.square
        db_apartment.useful_square = data.useful_square
        db_apartment.kitchen_square = data.kitchen
        db_apartment.price = data.price
        db_apartment.description = data.description
        db_apartment.is_liked = False

        host = conf.get_provider(data.provider)['base_url']
        db_apartment.absolute_url = urljoin(host, data.rel_url)

        for link in data.photos:
            db_apartment.photos.append(
                DbApartmentPhoto(absolute_photo_url=link)
            )

        return db_apartment

    def release(self):
        self._is_released.set()
        self.telegram_client.stop_polling()
