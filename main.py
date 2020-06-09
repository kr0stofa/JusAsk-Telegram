from telegram.ext import CommandHandler, ConversationHandler, Filters, Updater
from telegram.ext import CallbackQueryHandler, InlineQueryHandler, MessageHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from local import get_bot_token
from configs import CHOPE_DURATION
from account import Accounter
from staticdatamgr import SDManager
from questions import QuestionHolder

import logging

log = 1

if log: logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

botToken = get_bot_token()

sdmanager = SDManager()
sdmanager.load()
MODLIST = sdmanager.get_modlist("NUS")

accounter = Accounter()
qholder = QuestionHolder()


# Encodings
REPORT_STATUS = 1
EXIT_MENU = "EXIT" 

STS = {}
STS["reg_select_faculty"] = 101
STS["reg_accept_faculty"] = 102
STS["reg_accept_year"] = 103
STS["select_mods"] = 201
STS["mod_menu_handler"] = 202
STS["handle_senior_choice"] = 301
STS["ask_confidence"] = 107
STS["req_transcript"] = 206
STS["handle_account_buttonpress"] = 501
STS["handle_question_loop"] = 601
STS["finish_asking_question"] = 602
STS["edit_profile"] = 801
STS["handle_answer_menu_press"] = 701
STS["recieve_senior_answer"] = 702
STS["exit"] = 999


MOD_REG_TABLE = {}
MQ_MAP = {} # Message-question mapping

# Storing user chat IDs so the bot can PM them
def add_to_PM_TABLE(userID, chatID):
    accounter.add_to_pmtable(userID, chatID)
    return

def get_private_chat_id(userID):
    return accounter.get_chatID(userID) 


############################## GENERAL TELEGRAM FUNCTIONS ##############################
def get_uid(update):
    return update.effective_user.username

def get_message(update):
    return update.message

def get_chat_id(update):
    return update.effective_chat.id

def get_callback_query(update):
    return update.callback_query

def get_origin_msg(callback_query):
    return callback_query.message

def get_callback_data(callback_query):
    return callback_query.data

# Returns the message object
def send_message(update, context, content, markup=""):
    return send_message_to_chatid(context.bot, get_chat_id(update), content, markup)

# Returns message object
def send_message_to_chatid(bot, chat_id, content, markup = ""):
    return bot.send_message(
        chat_id = chat_id,
        text = content,
        reply_markup = markup
    )

# Takes in a list of buttons and return an InlineKeyboardMarkup. Optional flag fo add a "Done" button
# The final format must be a list of lists of button objects like [[button1, button2], [button3], [donebutton]]
def make_menu(blist, add_done = True, vertical = True):
    if vertical:
        button_wrap = lambda x: [x]
        l_wrap = lambda y: y
    else:
        button_wrap = lambda x: x
        l_wrap = lambda y:[y]

    button_list = []
    for b_txt in blist:
        entry = button_wrap(InlineKeyboardButton(b_txt, callback_data = b_txt))
        button_list.append(entry)
    
    button_list = l_wrap(button_list)
    
    if add_done:
        done = [(InlineKeyboardButton("Done", callback_data = EXIT_MENU))] # Done is always on the bottom row
        button_list.append(done)

    # print("<MAKE MENU>: %s" % button_list)

    menu_mu = InlineKeyboardMarkup(button_list)
    return menu_mu

# Removes inline buttons
def remove_inline_buttons(update, context):
    og_msg = get_origin_msg(get_callback_query(update))
    context.bot.edit_message_text(
                chat_id = og_msg.chat_id,
                message_id = og_msg.message_id,
                text = og_msg.text,
                reply_markup=""
            )

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
        if accounter.is_registered(user_ID):
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
# MAKE SURE TO ADD (update,context) as a suffix
def compose_replykb_state(contents, buttons = [], return_state = False):
    keyboard_markup = ReplyKeyboardMarkup([buttons],one_time_keyboard=True)
    return generic_message_composer(contents, buttons, return_state, reply_markup=keyboard_markup)
    

# HOF to build handlers with INLINE markup. Does not reply to group chats (see direct_to_privatechat)
# Returns a handler function. 
# MAKE SURE TO ADD (update,context) as a suffix
def compose_inline_state(contents, inline_buttons = [], add_done=False, return_state = False, vertical = True):
    inline_mark = make_menu(inline_buttons,add_done=add_done ,vertical=vertical)
    return generic_message_composer(contents, inline_buttons, return_state, reply_markup=inline_mark)

# HOF to build handlers to EDIT messages and optionally attach an INLINE markup. Does not reply to group chats (see direct_to_privatechat)
# Returns a handler function
# This must be called from a CallbackQueryHandler or something else with a CALLBACK
def edit_inline_state(format_string = "\n{}", inline_buttons = [], add_done=False, return_state = False, overwrite_msg = "NULL", collect_fn = lambda b,a: (b+a), vertical = True):
    def created_state(update,context):
        diverted = direct_to_privatechat(update, context)
        if not diverted:
            cb_query = get_callback_query(update)
            og_msg = get_origin_msg(cb_query)
            cb_data = get_callback_data(cb_query)
            inline_mark = make_menu(inline_buttons,add_done=add_done, vertical=vertical)
            append = format_string.format(cb_data)
            base_txt = overwrite_msg if not overwrite_msg == "NULL" else og_msg.text
            context.bot.edit_message_text(
                chat_id = og_msg.chat_id,
                message_id = og_msg.message_id,
                text = collect_fn(base_txt, append),
                reply_markup=inline_mark
            )
            return return_state
    return created_state


############################## CORE FUNCTIONS ##############################
def start_message(update, context):
    # print("START MESSAGE UPDATE ", update , " \nCONTEXT ", context)
    chat_ID = get_chat_id(update)
    user = update.effective_user
    firstname = user.first_name
    diverted = direct_to_privatechat(update, context)
    user_ID = get_uid(update)
    if not diverted:
        registered = accounter.is_registered(user_ID)
        if not registered:
            add_to_PM_TABLE(user_ID, chat_ID)
            msg = "Hello, {}!\nWelcome to JusAsk! It seems you haven't registered an account yet. Try /register !".format(firstname)
            context.bot.send_message(chat_id=chat_ID, text=msg)
        else:
            msg = "Hi, {}!\nTo ask a question just hit /ask!\nTo toggle question notifications on/off as a Senior hit /dnd\nTo manage your account, use /account".format(firstname)
            context.bot.send_message(chat_id=chat_ID, text=msg)

def choose_school(update, context):
    msg = "Which school are you in? If your school is not on the list that means we currently do not support your school at this time :("
    school_buttons = ['NUS']
    return compose_inline_state(msg, inline_buttons=school_buttons, return_state=STS['reg_select_faculty'])(update,context)

def select_faculty(update,context):
    msg = "Please select your faculty:"
    facs = ['ARCHI', 'COMP', 'BIZ','ENGIN','FASS','SCI', 'SDE']
    return edit_inline_state(format_string = ("University:\n{}\n\n"+msg), inline_buttons=facs, return_state=STS['reg_accept_faculty'], overwrite_msg="")(update,context)

# Should work for any University faculty
def accept_faculty_push_year_qn(update,context):
    userID = get_uid(update)
    cb_query = get_callback_query(update)
    selected_fac = get_callback_data(cb_query)
    accounter.add_faculty(userID, selected_fac) # Update the backend

    new_qn = "Which year of study are you in?"
    years = ['Year 1', 'Year 2', 'Year 3','Year 4','Year 5','Masters', 'PHD']
    return edit_inline_state(format_string = ("\n{}\n\n"+new_qn), inline_buttons=years, return_state=STS['reg_accept_year'])(update,context)

def accept_year_push_senior_qn(update,context):
    userID = get_uid(update)
    cb_query = get_callback_query(update)
    year = get_callback_data(cb_query)
    accounter.add_year(userID, year) # Update the backend

    og_msg = get_origin_msg(cb_query)
    append = "\nYear: %s" % year
    context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text + append
    )
    choose_senior(update, context) # Ask the followup question
    return STS["mod_menu_handler"]


# Is embedded in the accept_faculty callback
def choose_senior(update, context):
    mu = make_menu(["Yes!", "No, maybe later"], add_done=False)
    send_message(
        update, 
        context,
        "Would you like to help answer questions from modules you've already taken? You'll have a chance to win prizes based on the quality and quantity of your answers",
        markup = mu
    )
    return STS['handle_senior_choice']

def handle_senior_choice(update, context):
    cb_query = get_callback_query(update)
    press_value = get_callback_data(cb_query)
    if "Yes" in press_value:
        return STS["select_mods"]
    else:
        close_registration(update,context)
        return STS["exit"]
        

mod_mu = make_menu(MODLIST)
def choose_modules_message(update, context): 
    send_message(
        update, 
        context,
        "Which of the following mods do you wish help out for? (You can select multiple):",
        markup = mod_mu
    )
    return STS['mod_menu_handler']

def handle_mod_buttonpress(update, context):
    user_ID = get_uid(update)
    cb_query = get_callback_query(update)
    og_msg = get_origin_msg(cb_query)
    press_value = get_callback_data(cb_query)

    is_done = (press_value == EXIT_MENU)
    if is_done:
        done_line = "\n-----END-----"
        accounter.add_senior_modules(user_ID, _get_personal_mod_table(user_ID)) # TODO reimplement
        context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text + done_line
            )
        close_registration(update, context)
        return STS["exit"]

    toggle_mod_in_table(press_value, user_ID)
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

def close_registration(update,context):
    send_message(
        update,
        context,
        "Registration successful! Hit /ask to start asking questions! If you registered as a senior, you will automatically recieve a message notifying you of questions"
    )
    return 

############################## REGISTRATION ##############################
def _get_personal_mod_table(uid):
    global MOD_REG_TABLE
    if not uid in MOD_REG_TABLE:
        MOD_REG_TABLE[uid] = {}
        MOD_REG_TABLE[uid]["mods"] = {}
    personal_table = MOD_REG_TABLE.get(uid)
    return personal_table["mods"]
    
# Works like a poll bot. Pressing the same value a second time will remove it.
# TODO CLEAN UP THESE FUNCTIONS
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
        person_mod_table.pop(s)

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

# Account management
def open_account_manager(update, context):
    userID = get_uid(update)
    account_text = accounter.get_profile_text(userID)
    account_options = ["Edit profile"]
    return compose_inline_state(account_text, inline_buttons=account_options,return_state = STS["handle_account_buttonpress"])(update,context)

def print_table(update,context):
    user_ID = get_uid(update)
    print("USER ATTEMPTING TO DO ADMIN THINGS: ", user_ID)
    if user_ID == "Lessthanfree":
        context.bot.send_message(
            chat_id = get_chat_id(update),
            text="Dumping Registration Table: {}".format(MOD_REG_TABLE)
        )
    return

def handle_manager_buttonpress(update,context):
    user_ID = get_uid(update)
    account_text = accounter.get_profile_text(userID)

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

    if press_value == "Edit profile":
        context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text
            )
        return STS["edit_profile"]

    elif press_value == "Review groups":
        context.bot.edit_message_text(
            chat_id = og_msg.chat_id,
            message_id = og_msg.message_id,
            text = og_msg.text
            )
        return do_nothing(update, context)
    else:
        print("UNRECOGNIZED BUTTONPRESS")

############################## ASK ##############################
def handle_ask_question(update, context):
    msg = "Which module are you asking help for?"
    mods = MODLIST
    return compose_inline_state(msg, inline_buttons = mods, return_state=STS["handle_question_loop"])(update,context)

def handle_accept_question_loop(update, context):
    chosen_mod = get_callback_data(get_callback_query(update))
    og_msg = get_origin_msg(get_callback_query(update))
    context.bot.edit_message_text(
                chat_id = og_msg.chat_id,
                message_id = og_msg.message_id,
                text = og_msg.text + "\n%s" % chosen_mod,
                reply_markup=""
            )

    userid = get_uid(update)
    selected_mod = get_callback_data(get_callback_query(update))
    qholder.add_stated_asking(userid, selected_mod)    
    msg = "Please send the question below."
    send_message(update, context, msg)
    return STS["finish_asking_question"]

def handle_question_finish(update, context):
    userid = get_uid(update)
    question_txt = update.message.text # Raw text
    msg = "Thanks for your question! We'll let you know once someone responds!"   
    send_message(update, context, msg)
    
    question = qholder.finished_asking(userid, question_txt)
    send_chope_message(context, question)
    return STS["exit"]
    
def send_chope_message(context, question):
    bot = context.bot
    module_code = question.get_modcode()
    senior_chat_ids = accounter.get_chatids_for_mod(module_code)
    question_text = question.get_text()

    chope_button = make_menu(["Chope", "Nope"], add_done=False)
    for cid in senior_chat_ids:
        logging.debug("<SEND CHOPE MSG> PM message to chatid: ", cid)
        msg = "New question for {}!\n\n{}\n\nWould you like to chope?\n".format(module_code, question_text)
        msg_obj = send_message_to_chatid(
            bot,
            cid,
            msg,
            markup=chope_button
        )
        msg_id = msg_obj.message_id
        # Insert information to bot_data
        # Guessing bot_data is a dict that is within the bot
        MQ_MAP.update({msg_id: question.make_key()})
    return

def accept_chope(update,context):
    # print("ACCEPT CHOPE ", update)
    cb_query = get_callback_query(update)
    msg = get_message(cb_query)
    msg_id = msg.message_id
    qkey = MQ_MAP.get(msg_id)

    # REMOVE MARKUP
    remove_inline_buttons(update, context)

    s_uid = get_uid(update)
    qholder.add_q_to_senior_inventory(s_uid, qkey)
    accept_msg = "Great! This question will be reserved for you for the next {} hours. When you are ready to provide an answer, type /answer".format(CHOPE_DURATION)
    send_message(update,context,accept_msg)
    return

# A menu with left and right buttons.
ans_menu_buttons = ["<", "Select current", ">"]

def answer_menu(update, context):
    uid = get_uid(update)
    q_inventory = qholder.get_senior_inventory(uid)
    print("<ANS MENU> Q inventory", q_inventory)
    if len(q_inventory) < 1:
        send_message(update, context, "You have not choped any questions! When you recieve a question message, be sure to hit the 'Chope' button!")
    else:
        q_content = qholder.get_senior_curr_question_string(uid)
        msg = "Please choose the question you would like to respond to. Use the arrows to browse your choped questions\n{}".format(q_content)
        if len(q_inventory) > 1:
            buttons = ans_menu_buttons
        else:
            buttons = ["Select current"]
        return compose_inline_state(msg, inline_buttons=buttons, return_state=STS["handle_answer_menu_press"],add_done=True, vertical=False)(update,context)

def answer_menu_loop(update, context):
    cbq = get_callback_query(update)
    userID = get_uid(update)
    buttonpress = get_callback_data(cbq)
    if "current" in buttonpress:
        return STS["recieve_senior_answer"]
    elif "<" in buttonpress or ">" in buttonpress:
        # Assuming there's no way you can reach this stage if you only have 1 question
        if buttonpress == "<":
            ishift = -1
        elif buttonpress == ">":
            ishift = 1
        else:
            remove_inline_buttons(update, context)
            logging.error("<ANSWER MENU LOOP> Unexpected callback data value! {}".format(buttonpress))
        
        qholder.shift_senior_q_index(userID, ishift)
        q_content = qholder.get_senior_curr_question_string(userID)
        msg = "Please choose the question you would like to respond to. Use the arrows to browse your choped questions\n {}".format(q_content)
        return edit_inline_state(format_string="", inline_buttons=ans_menu_buttons, overwrite_msg=msg,add_done=True,vertical=False, return_state=STS["handle_answer_menu_press"])(update, context)
    else:
        remove_inline_buttons(update, context)
        return EXIT_MENU
def accept_answer(update, context):
    remove_inline_buttons(update, context)

    userID = get_uid(update)
    text = "Please enter your answer below"
    send_message(update, context, text)
    return 

# CHATBOT INIT
# Initalizes the handlers for this dispatcher
def init_handlers(dis):
    start_handler = CommandHandler('start', start_message)
    admin_handler = CommandHandler('admin', print_table)
    chope_button_handler = CallbackQueryHandler(accept_chope)

    register_handler = ConversationHandler(
        entry_points=[
            CommandHandler('register', choose_school)
            ],
        states={
                STS['reg_select_faculty']: [CallbackQueryHandler(select_faculty)],
                STS['reg_accept_faculty']:[CallbackQueryHandler(accept_faculty_push_year_qn)],
                STS["reg_accept_year"]:[CallbackQueryHandler(accept_year_push_senior_qn)],
                STS["handle_senior_choice"]:[CallbackQueryHandler(handle_senior_choice)],
                STS["select_mods"]:[CallbackQueryHandler(choose_modules_message)],
                STS["mod_menu_handler"]: [CallbackQueryHandler(handle_mod_buttonpress)],
                STS["exit"]: [MessageHandler(Filters.text, do_nothing)],
                EXIT_MENU:[]
            },
        fallbacks=[
            CommandHandler('cancel', do_nothing)
        ],
        allow_reentry = True        
    )
    ask_handler = ConversationHandler(
        entry_points=[CommandHandler("ask", handle_ask_question)],
        states = {
            STS["handle_question_loop"]:[CallbackQueryHandler(handle_accept_question_loop)],
            STS["finish_asking_question"]:[MessageHandler(Filters.all, handle_question_finish)],
            EXIT_MENU:[]
        },
        fallbacks = [
            CommandHandler('cancel', do_nothing)
        ],
        allow_reentry = True
    )

    account_manage_handler = ConversationHandler(
        entry_points = [
            CommandHandler('account', open_account_manager)
            ],
        states = {
            EXIT_MENU:[]
        },
        fallbacks = [
            CommandHandler('cancel', do_nothing)
        ],
        allow_reentry = True        
    )

    answer_handler = ConversationHandler(
        entry_points = [CommandHandler("answer", answer_menu)],
        states={
            STS["handle_answer_menu_press"]:[CallbackQueryHandler(answer_menu_loop)],
            STS["recieve_senior_answer"]:[CallbackQueryHandler(accept_answer)],
            EXIT_MENU:[]
        },
        fallbacks = [
            CommandHandler('cancel', do_nothing)
        ],
        allow_reentry = True        
    )

    dis.add_handler(admin_handler)
    dis.add_handler(start_handler)
    dis.add_handler(register_handler)
    dis.add_handler(ask_handler)
    dis.add_handler(answer_handler)
    dis.add_handler(account_manage_handler)
    dis.add_handler(chope_button_handler)

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