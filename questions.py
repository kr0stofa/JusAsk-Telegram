import datetime
import logging

class Question:
    def __init__(self, mod_code, asker, text):
        self.text = text
        self.mod_code = mod_code
        self.asker = asker
        self.create_time = datetime.date.isoformat(datetime.datetime.now())

    def make_key(self):
        # print("MAKE KEY", self.create_time)
        hop = 3 
        k = self.text.lower().replace(" ", "")[::hop][:12]
        ey = self.create_time.lower().replace(" ","")[::hop][:4]
        key = k + ey
        return (key)

    def get_modcode(self):
        return self.mod_code

    def get_text(self):
        return self.text

    def get_asker(self):
        return self.asker

    def toString(self):
        template = "Module: {}\nAsked:{}\n\n{}"
        return template.format(self.mod_code, self.create_time, self.text)

        
class QuestionHolder:
    def __init__(self):
        self.qkey_reverse = {}
        self.asking = {}
        self.unanswered = {}
        self.senior_inventory = {}

    def add_stated_asking(self, user_ID, module):
        if user_ID in self.asking:
            return False
        self.asking[user_ID] = module
        return True

    def _clear_started_asking(self, user_ID):
        return self.asking.pop(user_ID)

    def finished_asking(self, user_ID, question_txt):
        mod_code = self._clear_started_asking(user_ID)
        qn = self.add_new_question(user_ID, mod_code, question_txt)
        return qn

    # def _add_module(self, mod_code):
    #     self.unanswered[mod_code] = {}
    #     return

    def add_new_question(self, user_ID, module_code, question_text):
        q = Question(module_code, user_ID, question_text)
        qkey = q.make_key()
        self.unanswered[qkey] = q
        return q

    def _get_question(self, question_key):
        if not question_key in self.unanswered:
            logging.warn("Question key %s not in dict" % question_key)
        return self.unanswered.get(question_key, False)

    def clear_question(self, module_code, question):
        qkey = question.make_key()
        self.unanswered.pop(qkey)
        return

    # Returns the real pointer, not a copy
    def _get_senior_q_index(self, uid):
        return 

    # Returns the real pointer, not a copy
    def _get_senior_q_list(self, uid):
        assert uid in self.senior_inventory
        return self.senior_inventory[uid][1]

    def add_q_to_senior_inventory(self, user_ID, question_key):
        if not user_ID in self.senior_inventory:
            self.senior_inventory[user_ID] = [0, []]
        question = self._get_question(question_key)
        self._get_senior_q_list(user_ID).append(question)

    def _get_senior_full_inventory(self, user_ID):
        return self.senior_inventory.get(user_ID, []).copy()
    
    # Returns a copy of the question list
    # Blank list if not found
    def get_senior_inventory(self, user_ID):
        return self.senior_inventory.get(user_ID, [0, []])[1].copy()

    def shift_senior_q_index(self, user_ID, shift):
        if not user_ID in self.senior_inventory:
            logging.error("Tried to shift senior index. Senior {} DNE".format(user_ID))
            return
        curr_index = self.senior_inventory[user_ID][0]
        q_list = self._get_senior_q_list(user_ID)
        if curr_index + shift >= len(q_list):
            # Wrap around
            self.senior_inventory[user_ID][0] = 0
        elif curr_index + shift < 0:
            # Don't use negative numbers
            self.senior_inventory[user_ID][0] = len(q_list) - 1 
        else:
            self.senior_inventory[user_ID][0] = curr_index + shift
        
        return

    def get_senior_curr_question_string(self, user_ID):
        curr_index, inventory = self._get_senior_full_inventory(user_ID)
        header = "Question {} out of {}\n".format(curr_index+1, len(inventory))
        print("INVENTORY:",inventory)
        body = inventory[curr_index].toString()
        return header + body

class Answer:
    def __init__(self, question_key, answer_content):
        self.qkey = question_key
        self.ans_content = answer_content

