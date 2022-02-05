import importlib
import random
import time
import re

from sys import argv
from typing import Optional

from VegetaRobot import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,UPDATES_CHANNEL,
    dispatcher,
    StartTime,
    telethn,
    updater)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from VegetaRobot.modules import ALL_MODULES
from VegetaRobot.modules.helper_funcs.chat_status import is_user_admin
from VegetaRobot.modules.helper_funcs.misc import paginate_modules
from VegetaRobot.modules.disable import DisableAbleCommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown



def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time



PM_START_TEXT = """
[🌸](https://te.legra.ph/file/a8b31611b9ebcad22b95e.jpg)𝓱𝓮𝔂 𝓽𝓱𝓮𝓻𝓮 𝓶𝔂 𝓷𝓪𝓶𝓮 𝓲𝓼 *🌸𝓪𝓵𝓮𝔁𝓪 𝓻𝓸𝓫𝓸𝓽🌸* 𝓲'𝓶 𝓪 𝓹𝓸𝔀𝓮𝓻𝓯𝓾𝓵𝓵 𝓰𝓻𝓸𝓾𝓹 𝓶𝓪𝓷𝓪𝓰𝓮𝓻 𝓫𝓸𝓽 𝔀𝓲𝓽𝓱 𝓬𝓸𝓸𝓵 𝓶𝓸𝓭𝓾𝓵𝓮𝓼. 𝓯𝓮𝓵𝓵 𝓯𝓻𝓮𝓮 𝓽𝓸 𝓪𝓭𝓭 𝓶𝓮 𝓽𝓸 𝔂𝓸𝓾𝓻 𝓰𝓻𝓸𝓾𝓹𝓼 𝓱𝓲𝓽 𝓱𝓮𝓵𝓹 𝓫𝓾𝓽𝓽𝓸𝓷 𝓽𝓸 𝓴𝓷𝓸𝔀 𝓶𝔂 𝓬𝓸𝓶𝓶𝓪𝓷𝓭𝓼\n
[𝓼𝓾𝓹𝓹𝓸𝓻𝓽](t.me/DARKAMANSUPPORT)  [𝓬𝓱𝓪𝓷𝓷𝓮𝓵](t.me/DARKAMANCHANNEL)\n
"""

buttons = [
    [
        InlineKeyboardButton(
                            text="🌸𝓪𝓭𝓭 𝓶𝓮 𝓽𝓸 𝔂𝓸𝓾𝓻 𝓰𝓻𝓸𝓾𝓹🌸",
                            url="t.me/alexa_manager_robot?startgroup=true"),
                    ],
                    [                  
                       InlineKeyboardButton(
                             text="🌸𝓼𝓾𝓹𝓹𝓸𝓻𝓽🌸",
                             url=f"https://t.me/{SUPPORT_CHAT}"),
                       InlineKeyboardButton(
                             text="🌸𝓾𝓹𝓭𝓪𝓽𝓮𝓼🌸",
                             url=f"https://t.me/{UPDATES_CHANNEL}"),
                        ],
                       [
                           InlineKeyboardButton(text="🌸𝓱𝓮𝓵𝓹 𝓪𝓷𝓭 𝓬𝓸𝓶𝓶𝓪𝓷𝓭𝓼🌸", callback_data="help_back"
         ),
    ],
] 

HELP_STRINGS = """
✘ [𝓱𝓮𝔂](https://te.legra.ph/file/a8b31611b9ebcad22b95e.jpg) 𝓽𝓱𝓮𝓻𝓮𝔀 𝓲 𝓪𝓶 🌸𝓪𝓵𝓮𝔁𝓪 𝓻𝓸𝓫𝓸𝓽🌸 𝓽𝓸 𝓶𝓪𝓴𝓮 𝓶𝓮 𝓯𝓾𝓷𝓬𝓽𝓲𝓸𝓷𝓪𝓵, 𝓶𝓪𝓴𝓮 𝓼𝓾𝓻𝓮 𝓽𝓱𝓪𝓽 𝓲 𝓱𝓪𝓿𝓮 𝓮𝓷𝓸𝓾𝓰𝓱𝓽 𝓻𝓲𝓰𝓱𝓽𝓼 𝓲𝓷 𝔂𝓸𝓾𝓻 𝓰𝓻𝓸𝓾𝓹.
✘ /start ☞︎︎︎ 𝓼𝓽𝓪𝓻𝓽𝓼 𝓶𝓮 𝔂𝓸𝓾'𝓿𝓮 𝓹𝓻𝓸𝓫𝓪𝓫𝓵𝔂 𝓪𝓵𝓻𝓮𝓪𝓭𝔂 𝓾𝓼𝓮𝓭 𝓽𝓱𝓲𝓼.
✘ /help ☞︎︎︎ 𝓼𝓮𝓷𝓭𝓼 𝓽𝓱𝓲𝓼 𝓶𝓮𝓼𝓼𝓪𝓰𝓮 𝓲 𝔀𝓲𝓵𝓵 𝓽𝓮𝓵𝓵 𝔂𝓸𝓾 𝓶𝓸𝓻𝓮 𝓪𝓫𝓸𝓾𝓽 𝓶𝔂𝓼𝓮𝓵𝓯 𝓪𝓵𝓵 𝓬𝓸𝓶𝓶𝓪𝓷𝓭𝓼 𝓬𝓪𝓷 𝓫𝓮 𝓾𝓼𝓮𝓭 𝔀𝓲𝓽𝓱 𝓽𝓱𝓮 𝓯𝓸𝓵𝓵𝓸𝔀𝓲𝓷𝓰 ✘ (/),(!),(?),(.),(~)
""".format( 
    dispatcher.bot.first_name,
    "" if not ALLOW_EXCL else "✘ 𝒶𝓁𝓁 𝓬𝓸𝓶𝓶𝓪𝓷𝓭𝓼 𝓬𝓪𝓷 𝓮𝓲𝓽𝓱𝓮𝓻 𝓫𝓮 𝓾𝓼𝓮𝓭 𝔀𝓲𝓽𝓱 / 𝓸𝓻 !.",
)

HELP_MSG = "𝓬𝓵𝓲𝓬𝓴 𝓽𝓱𝓮 𝓫𝓾𝓽𝓽𝓸𝓷 𝓫𝓮𝓵𝓸𝔀 𝓽𝓸 𝓰𝓮𝓽 𝓱𝓮𝓵𝓹 𝓶𝓮𝓷𝓾𝓲𝓷 𝔂𝓸𝓾𝓻 𝓹𝓶."
DONATE_STRING = """𝓬𝓸𝓷𝓽𝓪𝓬𝓽 𝓽𝓸 [𝓭𝓪𝓻𝓴𝓪𝓶𝓪𝓷](t.me/darkaman)"""
HELP_IMG= "https://te.legra.ph/file/a8b31611b9ebcad22b95e.jpg"

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("VegetaRobot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)





def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors



def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Powered by @DARKAMANSUPPORT\nHere is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="⬅ Back", callback_data="help_back"),
                      InlineKeyboardButton(text="⬅ Home", callback_data="vegeta_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass



def vegeta_data_callback(update, context):
    query = update.callback_query
    if query.data == "vegeta_":
        query.message.edit_text(
            text="""CallBackQueriesData Here""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Back", callback_data="vegeta_back")
                 ]
                ]
            ),
        )
    elif query.data == "vegeta_back":
        query.message.edit_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )




def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Help",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_photo(
            HELP_IMG, HELP_MSG,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Help",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ]
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )



def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))



def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Settings",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)



def donate(update: Update, context: CallbackContext):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 1610284626 and DONATION_LINK:
            update.effective_message.reply_text(
                "You can also donate to the person currently running me "
                "[here]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        try:
            bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            update.effective_message.reply_text(
                "I've PM'ed you about donating to my creator!"
            )
        except Unauthorized:
            update.effective_message.reply_text(
                "Contact me in PM first to get donation information."
            )


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop




def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendMessage(f"@{SUPPORT_CHAT}","𝙰𝙻𝙴𝚇𝙰 𝙾𝙽 𝙵𝙸𝚁𝙴🔥", parse_mode=ParseMode.MARKDOWN) 
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!",
            )
        except BadRequest as e:
            LOGGER.warning(e.message)


    start_handler = DisableAbleCommandHandler("start", start)

    help_handler = DisableAbleCommandHandler("help", get_help)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_.*")

    settings_handler = CommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")

    data_callback_handler = CallbackQueryHandler(vegeta_data_callback, pattern=r"vegeta_")
    donate_handler = CommandHandler("donate", donate)
    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats)

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(data_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("alexa is now alive and functioning")
        updater.start_polling(timeout=15, read_latency=4, clean=True)

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == '__main__':
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    main()
