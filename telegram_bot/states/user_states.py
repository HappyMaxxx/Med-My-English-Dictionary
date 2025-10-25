from aiogram.fsm.state import State, StatesGroup

class UserLinkState(StatesGroup):
    linked = State()
    unlinked = State()