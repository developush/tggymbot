import json
import traceback

from telegram import (
    InlineKeyboardMarkup,
    LabeledPrice,
)
from datetime import timedelta, datetime

from constants import (
    DATE_FORMAT,
    SubscriptionValue
)
from config import PAYMENT_TOKEN, CURRENCY
from models import (
    User,
    Subscription
)
from logic.base import DefaultMessageHandler


class SubscriptionMenuController(DefaultMessageHandler):
    async def _call(self):
        if not self._update.message:
            await self.callback_query.answer()

        text, buttons = self._get_data()
        try:
            await self.callback_query.edit_message_text(
                text=text,
                reply_markup=buttons,
            )
        except:
            await self._context.bot.sendMessage(
                chat_id=self.chat_id,
                text=text,
                reply_markup=buttons,
                disable_notification=self.silent
            )
        if not self._update.message:
            self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        end_date = self.user.subscription_end.strftime(DATE_FORMAT)
        subscription = self.user.subscription
        if not subscription:
            subscription = Subscription.get(value=SubscriptionValue.Low)

        subscriptions_descriptions = '\n\n'.join([f'{s.name[self.lang]}:\n{s.description[self.lang]}'
                                                  for s in (Subscription
                                                            .select()
                                                            .order_by(Subscription.id.asc()))])
        texts = {
            'en': f'💰Subscription\n'
                  f'Level: {subscription.name[self.lang]}\n'
                  f'Subscription active till {end_date}\n\n'
                  f'Subscription level differences 🧐\n{subscriptions_descriptions}',
            'ru': f'💰Подписка\n'
                  f'Уровень: {subscription.name[self.lang]}\n'
                  f'Подписка активна до {end_date}\n\n'
                  f'Отличия уровней подписки 🧐\n{subscriptions_descriptions}',
            'ua': f'💰Передплата\n'
                  f'Рівень: {subscription.name[self.lang]}\n'
                  f'Передплата активна до {end_date}\n\n'
                  f'Відмінності рівнів підписки 🧐\n{subscriptions_descriptions}',
        }

        buttons = [{'name': s.name[self.lang],
                    'callback_data': {'subscription': True,
                                      'subscription_id': s.unique_id}} for s in (Subscription
                                                                                 .select()
                                                                                 .order_by(Subscription.id.asc()))]
        buttons = self.build_menu(buttons, raw=True, buttons_in_row=1)
        buttons.extend(self.attach_back_button('menu'))
        return texts[self.lang], InlineKeyboardMarkup(buttons)

    @staticmethod
    def pattern(callback_data):
        return 'subscription' == callback_data


class InvoiceController(DefaultMessageHandler):
    async def _call(self):
        if not self._update.message:
            await self.callback_query.answer()

        title, description, prices, payload = self._get_data()
        try:
            await self.callback_query.delete_message()
        finally:
            await self._context.bot.sendInvoice(
                chat_id=self.chat_id,
                title=title,
                description=description,
                payload=payload,
                provider_token=PAYMENT_TOKEN,
                currency=CURRENCY,
                prices=prices,
                max_tip_amount=10000,
                suggested_tip_amounts=[100, 500, 1000, 2500],
                disable_notification=self.silent
            )
        if not self._update.message:
            self._context.drop_callback_data(self.callback_query)

    def _get_data(self):
        callback_data = self.callback_query.data
        self._log.info(f'Callback data - {callback_data}')
        subscription = Subscription.get(unique_id=callback_data["subscription_id"])

        payload = {
            'subscription_id': subscription.unique_id,
            'user_id': self.user.id
        }

        title = {
            'en': f'💰Subscription\n'
                  f'Level: {subscription.name[self.lang]}\n',
            'ru': f'💰Подписка\n'
                  f'Уровень: {subscription.name[self.lang]}\n',
            'ua': f'💰Передплата\n'
                  f'Рівень: {subscription.name[self.lang]}\n',
        }

        prices = [LabeledPrice(subscription.name[self.lang], int(subscription.price * 100))]

        description = {
            'en': '⚠️Payment is made through a verified PrivatBank bot\n\n'
                  f'Level: {subscription.name[self.lang]}\n',
            'ru': '⚠️Платёж осуществляется через верифицированный бот ПриватБанка\n\n'
                  f'Уровень: {subscription.name[self.lang]}\n',
            'ua': '⚠️Платіж здійснюється через верифікований бот ПриватБанку\n\n'
                  f'Рівень: {subscription.name[self.lang]}\n',
        }

        return title[self.lang], description[self.lang], prices, payload

    @staticmethod
    def pattern(callback_data):
        if type(callback_data) == dict:
            return callback_data.get('subscription')
        return False


class CheckoutController(DefaultMessageHandler):
    async def _call(self):
        query = self._update.pre_checkout_query
        invoice_payload = query.invoice_payload
        try:
            if type(invoice_payload) == dict:
                if ((User.select()
                        .where(User.id == invoice_payload['user_id'])
                        .exists())
                        and (Subscription
                                .select()
                                .where(Subscription.unique_id == invoice_payload['subscription_id'])
                                .exists())):
                    await query.answer(ok=True)
                    return
            await query.answer(ok=True)
        except Exception:
            self._log(traceback.format_exc())
            await query.answer(ok=False, error_message="Something went wrong...")


class SuccessInvoiceController(DefaultMessageHandler):
    async def _call(self):
        user = await self._update_subscription_end()
        text, buttons = self._get_data(user)
        await self._context.bot.sendMessage(
            chat_id=self.chat_id,
            text=text,
            reply_markup=buttons,
            disable_notification=self.silent
        )

    def _get_data(self, user):
        subscription = user.subscription
        text = {
            'en': f'Payment successful!👌\n'
                  f'Subscription continued until {user.subscription_end.strftime(DATE_FORMAT)}\n'
                  f'Level: {subscription.name[self.lang]}\n',
            'ru': f'Платёж успешен!👌\n'
                  f'Подписка продолжена до {user.subscription_end.strftime(DATE_FORMAT)}\n'
                  f'Уровень: {subscription.name[self.lang]}\n',
            'ua': f'Платіж успішний!👌\n'
                  f'Передплата продовжена до {user.subscription_end.strftime(DATE_FORMAT)}\n'
                  f'Рівень: {subscription.name[self.lang]}\n',
        }

        buttons = self.build_menu(self._menu_buttons[self.lang])

        return text[self.lang], buttons

    async def _update_subscription_end(self):
        payload_data = self._update.message.effective_attachment['invoice_payload']
        payload_data = json.loads(payload_data) if type(payload_data) == str else payload_data
        self._log.info(f'Invoice data - {payload_data}')
        user = User.get_by_id(payload_data['user_id'])
        user.subscription_end = max(user.subscription_end,
                                    datetime.now()) + timedelta(days=30)
        subscription = Subscription.get(unique_id=payload_data['subscription_id'])
        user.subscription = subscription
        user.save()
        return user
