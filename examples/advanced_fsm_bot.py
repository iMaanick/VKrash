import asyncio
import os

from dotenv import load_dotenv

from src.vk_bot_framework.client.vk_client import VKClient
from src.vk_bot_framework.dispatcher.dispatcher import Dispatcher
from src.vk_bot_framework.filters import StateFilter, TextFilter
from src.vk_bot_framework.fsm import StatesGroup, State
from src.vk_bot_framework.fsm.context import FSMContext
from src.vk_bot_framework.methods.methods import MessagesMethods
from src.vk_bot_framework.middleware import BaseMiddleware
from src.vk_bot_framework.router import Router
from src.vk_bot_framework.types.vk_update import VKUpdate
from src.vk_bot_framework.utils.keyboard_builder import KeyboardBuilder

# Load environment variables
load_dotenv()

TOKEN = os.environ.get("TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))


# Define states for user profile
class ProfileStates(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_gender = State()
    waiting_interests = State()


# Create router
router = Router()


# Create middleware for user tracking
class UserTrackingMiddleware(BaseMiddleware):
    async def before_update(self, update: VKUpdate, data: dict):
        if update.type == "message_new":
            user_id = update.object["message"]["from_id"]
            data["user_id"] = user_id
            print(f"Processing message from user {user_id}")
        return True

    async def after_update(self, update: VKUpdate, data: dict):
        print(f"Finished processing update for user {data.get('user_id')}")


# Command handlers
@router.message(TextFilter("/start"))
async def cmd_start(update: VKUpdate, context: dict, fsm: FSMContext, user_id):
    print(user_id)
    peer_id = update.object["message"]["peer_id"]
    # Create keyboard
    kb = KeyboardBuilder(one_time=True)
    kb.add_button("Start Profile Creation", color="primary")

    async with VKClient(TOKEN, GROUP_ID) as client:
        messages = MessagesMethods(client)
        await messages.send(
            peer_id=peer_id,
            message="Welcome to the Profile Bot! Press the button to start creating your profile.",
            keyboard=kb.get_keyboard()
        )


@router.message(TextFilter("Start Profile Creation"))
async def start_profile(update: VKUpdate, context: dict, fsm: FSMContext):
    peer_id = update.object["message"]["peer_id"]

    await fsm.set_state(ProfileStates.waiting_name)

    async with VKClient(TOKEN, GROUP_ID) as client:
        messages = MessagesMethods(client)
        await messages.send(
            peer_id=peer_id,
            message="Let's create your profile! What's your name?"
        )


@router.message(StateFilter(ProfileStates.waiting_name))
async def process_name(update: VKUpdate, context: dict, fsm: FSMContext):
    peer_id = update.object["message"]["peer_id"]
    name = update.object["message"]["text"]

    await fsm.update_data(name=name)
    await fsm.set_state(ProfileStates.waiting_age)

    async with VKClient(TOKEN, GROUP_ID) as client:
        messages = MessagesMethods(client)
        await messages.send(
            peer_id=peer_id,
            message=f"Nice to meet you, {name}! How old are you?"
        )


@router.message(StateFilter(ProfileStates.waiting_age))
async def process_age(update: VKUpdate, context: dict, fsm: FSMContext):
    peer_id = update.object["message"]["peer_id"]
    age = update.object["message"]["text"]

    if not age.isdigit():
        async with VKClient(TOKEN, GROUP_ID) as client:
            messages = MessagesMethods(client)
            await messages.send(
                peer_id=peer_id,
                message="Please enter a valid age (numbers only)"
            )
        return

    await fsm.update_data(age=int(age))
    await fsm.set_state(ProfileStates.waiting_gender)

    kb = KeyboardBuilder(one_time=True)
    kb.add_button("Male", color="primary")
    kb.add_button("Female", color="primary")

    async with VKClient(TOKEN, GROUP_ID) as client:
        messages = MessagesMethods(client)
        await messages.send(
            peer_id=peer_id,
            message="Please select your gender:",
            keyboard=kb.get_keyboard()
        )


@router.message(StateFilter(ProfileStates.waiting_gender))
async def process_gender(update: VKUpdate, context: dict, fsm: FSMContext):
    peer_id = update.object["message"]["peer_id"]
    gender = update.object["message"]["text"]

    if gender not in ["Male", "Female"]:
        async with VKClient(TOKEN, GROUP_ID) as client:
            messages = MessagesMethods(client)
            await messages.send(
                peer_id=peer_id,
                message="Please select gender using the buttons"
            )
        return

    await fsm.update_data(gender=gender)
    await fsm.set_state(ProfileStates.waiting_interests)

    async with VKClient(TOKEN, GROUP_ID) as client:
        messages = MessagesMethods(client)
        await messages.send(
            peer_id=peer_id,
            message="Great! Finally, tell me about your interests and hobbies."
        )


router2 = Router()


@router2.message(StateFilter(ProfileStates.waiting_interests))
async def process_interests(update: VKUpdate, context: dict, fsm: FSMContext):
    peer_id = update.object["message"]["peer_id"]
    interests = update.object["message"]["text"]

    # Get all profile data
    data = await fsm.get_data()
    data["interests"] = interests

    # Clear state
    await fsm.clear()

    # Format profile summary
    profile = f"""Your profile is complete!

Name: {data['name']}
Age: {data['age']}
Gender: {data['gender']}
Interests: {data['interests']}

User ID: {context['user_id']}"""

    async with VKClient(TOKEN, GROUP_ID) as client:
        messages = MessagesMethods(client)
        await messages.send(
            peer_id=peer_id,
            message=profile
        )


async def main():
    client = VKClient(TOKEN, GROUP_ID)
    dp = Dispatcher(client)

    # Setup middleware
    dp.middleware_manager.setup(UserTrackingMiddleware())

    # Include router
    dp.include_router(router)
    dp.include_router(router2)

    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
