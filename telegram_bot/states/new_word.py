from aiogram.fsm.state import State, StatesGroup

class NewWordState(StatesGroup):
    english = State()
    translation = State()
    example = State()
    confirm = State()