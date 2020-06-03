from telegram.ext import CommandHandler, ConversationHandler, Filters, Updater
from telegram.ext import CallbackQueryHandler, InlineQueryHandler, MessageHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from local import get_bot_token
from userdatamgr import UDManager
from staticdatamgr import SDManager
import logging

log = 1

if log: logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

botToken = get_bot_token()


# Encodings
REPORT_STATUS = 1
EXIT_MENU = "EXIT" 

STS = {}
STS["reg_select_faculty"] = 101
STS["reg_accept_faculty"] = 102
STS["select_mods"] = 201
STS["mod_menu_handler"] = 202
STS["ask_confidence"] = 107
STS["req_transcript"] = 206
STS["exit"] = 999


MODLIST = {"CS1010S","MA1101R","CS2040", "GER1000", "GEK1000", "TR3203", "TR3201"}

MOD_REG_TABLE = {}
USER_TABLE = {}

# Storing user chat IDs so the bot can PM them
PM_TABLE = {} # Table. Key: userid; Value: 1-to-1 chat IDs
def add_to_PM_TABLE(userID, chatID):
    PM_TABLE[userID] = chatID
    return

def get_private_chat_id(userID):
    private_chat_id = PM_TABLE.get(userID)
    return private_chat_id

# Check if this user has started a private chat with bot
def is_registered(userID):
    return userID in PM_TABLE

# GENERAL FUNCTIONS
def get_uid(update):
    return update.effective_user.username

def get_chat_id(update):
    return update.effective_chat.id

def get_callback_query(update):
    return update.callback_query

def get_origin_msg(callback_query):
    return callback_query.message

def get_callback_data(callback_query):
    return callback_query.data

# Takes in a list of buttons and return an InlineKeyboardMarkup. Optional flag fo add a "Done" button
def make_menu(blist, add_done = True):
    button_list = []
    for b_txt in blist:
        entry = [InlineKeyboardButton(b_txt, callback_data = b_txt)]
        button_list.append(entry)
    
    if add_done:
        done = [InlineKeyboardButton("Done", callback_data = EXIT_MENU)]
        button_list.append(done)

    menu_mu = InlineKeyboardMarkup(button_list)
    return menu_mu

# Filter to divert people to private chats.
# Returns True if diverted.
def direct_to_privatechat(update, context):
    chat_ID = get_chat_id(update)
    chat_type = update.effective_chat.type
    user = update.effective_user
    firstname = user.first_name
    user_ID = get_uid(update)
    logging.info("<CHAT TYPE> %s" % chat_type)
    if not chat_type == "private":
        if is_registered(user_ID):
            msg = "Hi, {}!\nPlease talk to me in here so as to avoid spamming groups :)".format(firstname)
            private_chat_ID = get_private_chat_id(user_ID)
            context.bot.send_message(chat_id=private_chat_ID, text=msg)
            
        msg = "Hi, {}!\nPlease start a private conversation with me to continue (go to my profile and press 'send message')".format(firstname) 
        context.bot.send_message(chat_id=chat_ID, text=msg)
        return True
    return False

# HOF to build handlers. Replies to the same chat as the update. Does not reply to group chats (see direct_to_privatechat)
# Returns a handler function
def generic_message_composer(contents, buttons, return_state, reply_markup=""):
    def created_state(update,context):
        diverted = direct_to_privatechat(update, context)
        if not diverted:
            update.message.reply_text(contents, reply_markup=reply_markup)
            return return_state
    return created_state

# HOF to build handlers with KEYBOARD markup. Does not reply to group chats (see direct_to_privatechat)
# Returns a handler function
def compose_replykb_state(contents, buttons = [], return_state = False):
    keyboard_markup = ReplyKeyboardMarkup([buttons],one_time_keyboard=True)
    return generic_message_composer(contents, buttons, return_state, reply_markup=keyboard_markup)
    

# HOF to build handlers with INLINE markup. Does not reply to group chats (see direct_to_privatechat)
# Returns a handler function
def compose_inline_state(contents, inline_buttons = [], return_state = False):
    inline_mark = make_menu(inline_buttons,add_done=False)
    return generic_message_composer(contents, inline_buttons, return_state, reply_markup=inline_mark)

# HOF to build handlers to EDIT messages and optionally attach an INLINE markup. Does not reply to group chats (see direct_to_privatechat)
# Returns a handler function
# This must be called from a CallbackQueryHandler or something else with a CALLBACK
def edit_inline_state(format_string = "\n%s", inline_buttons = [], return_state = False, overwrite_msg = "NULL"):
    def created_state(update,context):
        diverted = direct_to_privatechat(update, context)
        if not diverted:
            cb_query = get_callback_query(update)
            og_msg = get_origin_msg(cb_query)
            cb_data = get_callback_data(cb_query)
            inline_mark = make_menu(inline_buttons,add_done=False)
            append = format_string % cb_data
            base_txt = overwrite_msg if not overwrite_msg == "NULL" else og_msg.text
            context.bot.edit_message_text(
                chat_id = og_msg.chat_id,
                message_id = og_msg.message_id,
                text = base_txt + append,
                reply_markup=inline_mark
            )
            return return_state
    return created_state


# CORE COMPONENT
def start_message(update, context):
    # print("START MESSAGE UPDATE ", update , " \nCONTEXT ", context)
    chat_ID = get_chat_id(update)
    user = update.effective_user
    firstname = user.first_name
    diverted = direct_to_privatechat(update, context)
    user_ID = get_uid(update)
    if not diverted:
        add_to_PM_TABLE(user_ID, chat_ID)
        msg = "Hello, {}!\nWelcome to JusAsk! It seems you haven't registered an account yet. Try /register !".format(firstname)
        context.bot.send_message(chat_id=chat_ID, text=msg)


def choose_school(update, context):
    msg = "Which school are you in? If your school is not on the list that means we currently do not support your school at this time :("
    school_buttons = ['NUS']
    return compose_inline_state(msg, inline_buttons=school_buttons, return_state=STS['reg_select_faculty'])(update,context)

def select_faculty(update,context):
    msg = "Please select your faculty:"
    facs = ['ARCHI', 'COMP', 'BIZ','ENGIN','FASS','SCI', 'SDE']
    return edit_inline_state(format_string = ("University: %s\n\n"+msg), inline_buttons=facs, return_state=STS['reg_accept_faculty'], overwrite_msg="")(update,context)

# Should work for any University faculty
def accept_faculty_push_mods(update,context):
    cb_query = get_callback_query(update)
    og_msg = get_origin_msg(cb_query)
    selected_fac = get_callback_data(cb_query)
    append = "\n%s" % selected_fac
    context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text + append
    )
    choose_modules(update,context)
    return STS["mod_menu_handler"]


#### SYMPTOM REPORTING CALLBACKS ####
def _get_personal_mod_table(uid):
    global MOD_REG_TABLE
    if not uid in MOD_REG_TABLE:
        MOD_REG_TABLE[uid] = {}
        MOD_REG_TABLE[uid]["mods"] = {}
    personal_table = MOD_REG_TABLE.get(uid)
    return personal_table["mods"]
    
# Works like a poll bot. Pressing the same value a second time will remove it.
def toggle_mod_in_table(s, uid):
    person_mod_table = _get_personal_mod_table(uid)
    if not s in MODLIST:
        print("UNSUPPORTED MOD {}".format(s))
        return False
    
    if not s in person_mod_table:
        # Create
        person_mod_table[s] = 1
    else:
        # Toggle
        person_mod_table[s] = 1 - person_mod_table[s]

    return

def get_listed_mods_text(uid):
    person_mod_table = _get_personal_mod_table(uid)
    out = ""
    for mod, v in person_mod_table.items():
        if v > 0:
            if out == "":
                out = mod
            else:
                out = out + "\n" + mod
    return out

mod_mu = make_menu(MODLIST)

def choose_modules(update, context): 
    context.bot.send_message(
        chat_id = get_chat_id(update),
        text="Which of the following mods do you wish to recieve help in? (You can select multiple):",
        reply_markup = mod_mu
    )
    return STS['mod_menu_handler']

def handle_mod_buttonpress(update, context):
    user_ID = get_uid(update)
    cb_query = update.callback_query
    og_msg = cb_query.message
    # press_value = cb_query.callback_data
    press_value = cb_query.data

    is_done = (press_value == EXIT_MENU)
    if is_done:
        done_line = "\n-----END-----"
        context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text + done_line
            )
        return STS["exit"]

    s_name = press_value

    toggle_mod_in_table(s_name, user_ID)
    listed_mods_text = get_listed_mods_text(user_ID)
    header = og_msg.text.split(":")[0] + ":\n"
    new_text = header + listed_mods_text
    context.bot.edit_message_text(
        chat_id = og_msg.chat_id,
        message_id = og_msg.message_id,
        text = new_text,
        reply_markup = mod_mu
        )
    
    return STS['mod_menu_handler']

def create_mod_entry(uid):
    global MOD_REG_TABLE
    if not uid in MOD_REG_TABLE:
        d = {}
        d["mods"] = {}
        d["other"] = ""
        MOD_REG_TABLE[uid] = d

# Handler that... does nothing...
def do_nothing(update, context):
    return

# ADMIN/GROUP controls
def open_manager(update, context):
    pass 

def print_table(update,context):
    user_ID = get_uid(update)
    print("USER ATTEMPTING TO DO ADMIN THINGS: ", user_ID)
    if user_ID == "Lessthanfree":
        context.bot.send_message(
            chat_id = get_chat_id(update),
            text="Dumping Table: {}".format(MOD_REG_TABLE)
        )
    return

def handle_manager_buttonpress(update,context):
    user_ID = get_uid(update)
    cb_query = update.callback_query
    og_msg = cb_query.message
    press_value = cb_query.data
    is_done = (press_value == EXIT_MENU)
    if is_done:
        context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text
            )
        return STS["exit"]
    if press_value == "Create group":
        context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text
            )
        return do_nothing(update, context)

    elif press_value == "Review groups":
        context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text
            )
        return do_nothing(update, context)
    else:
        print("UNRECOGNIZED BUTTONPRESS")


# CHATBOT INIT
# Initalizes the handlers for this dispatcher
def init_handlers(dis):
    start_handler = CommandHandler('start', start_message)
    admin_handler = CommandHandler('admin', print_table)
    
    register_handler = ConversationHandler(
        entry_points=[
            CommandHandler('register', choose_school)
            ],
        states={
                STS['reg_select_faculty']: [CallbackQueryHandler(select_faculty)],
                STS['reg_accept_faculty']:[CallbackQueryHandler(accept_faculty_push_mods)],
                STS["mod_menu_handler"]: [CallbackQueryHandler(handle_mod_buttonpress)],
                STS["exit"]: [MessageHandler(Filters.text, do_nothing)]
            },
        fallbacks=[
            CommandHandler('cancel', do_nothing)
        ],
        allow_reentry = True        
    )

    # TODO implement this???
    ask_handler = ConversationHandler(
        entry_points=[CommandHandler("ask", do_nothing)],
        states = {},
        fallbacks = [
            CommandHandler('cancel', do_nothing)
        ],
        allow_reentry = True
    )

    account_manage_handler = ConversationHandler(
        entry_points = [
            CommandHandler('open_manager', open_manager)
            ],
        states = {},
        fallbacks = [
            CommandHandler('cancel', do_nothing)
        ],
        allow_reentry = True        
    )

    dis.add_handler(admin_handler)
    dis.add_handler(start_handler)
    dis.add_handler(register_handler)
    dis.add_handler(ask_handler)
    dis.add_handler(account_manage_handler)

    return dis

def main():
    # Docs say use_context is valid argument. Removing it seems to swap update and context... 
    # Do not remove unless you want to restructure all callbacks
    updater = Updater(token=botToken, use_context=True) 

    dispatcher = updater.dispatcher
    init_handlers(dispatcher)

    print("Started Polling")
    updater.start_polling()

main()