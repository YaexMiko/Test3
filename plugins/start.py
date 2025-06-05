from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from config import Config, Txt
from helper.database import madflixbotz

async def is_user_subscribed(client, user_id):
    """Check if user is subscribed to force sub channel"""
    if not Config.FORCE_SUB:
        return True
        
    try:
        user = await client.get_chat_member(Config.FORCE_SUB, user_id)
        return user.status in [
            enums.ChatMemberStatus.MEMBER,
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER
        ]
    except:
        return False

@Client.on_message(filters.private & filters.command("start"))
async def start_command(client, message):
    try:
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        
        print(f"Start command received from {user_id} - {first_name}")
        
        # Add user to database
        await madflixbotz.add_user(client, message)
        print(f"User {user_id} added to database")
        
        # Check subscription status
        is_subscribed = await is_user_subscribed(client, user_id)
        print(f"User {user_id} subscription status: {is_subscribed}")
        
        if not is_subscribed:
            print(f"User {user_id} is not subscribed, sending force sub message")
            
            # Get channel link
            if Config.FORCE_SUB.startswith('-100'):
                try:
                    chat = await client.get_chat(Config.FORCE_SUB)
                    if chat.username:
                        channel_link = f"https://t.me/{chat.username}"
                        channel_display = f"@{chat.username}"
                    else:
                        channel_link = f"https://t.me/c/{Config.FORCE_SUB[4:]}/1"
                        channel_display = chat.title or Config.FORCE_SUB
                except:
                    channel_link = f"https://t.me/{Config.FORCE_SUB}"
                    channel_display = Config.FORCE_SUB
            else:
                channel_username = Config.FORCE_SUB.replace('@', '')
                channel_link = f"https://t.me/{channel_username}"
                channel_display = f"@{channel_username}"
                
            buttons = [
                [InlineKeyboardButton(text="🔺 Join Channel 🔺", url=channel_link)],
                [InlineKeyboardButton(text="🔄 Check Again", callback_data="check_subscription")]
            ]
            
            force_sub_text = f"""<b>Hello {first_name}! 👋</b>

<b>You need to join our channel to use this bot.</b>

<b>📢 Channel:</b> {channel_display}

<b>After joining, click "🔄 Check Again" button below.</b>"""

            await message.reply_text(
                text=force_sub_text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return
        
        # User is subscribed, send start message
        print(f"User {user_id} is subscribed, sending start message")
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Tutorial", callback_data="tutorial"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")
            ],
            [
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
                InlineKeyboardButton("💰 Donate", callback_data="donate")
            ],
            [
                InlineKeyboardButton("📞 Support", url="https://t.me/MadflixBots_Support"),
                InlineKeyboardButton("📢 Channel", url="https://t.me/Madflix_Bots")
            ]
        ])
        
        start_text = Txt.START_TXT.format(first_name)
        
        # Send start message
        if Config.START_PIC:
            try:
                await message.reply_photo(
                    photo=Config.START_PIC,
                    caption=start_text,
                    reply_markup=keyboard
                )
                print(f"Start photo sent to {user_id}")
            except Exception as e:
                print(f"Error sending photo: {e}")
                await message.reply_text(
                    text=start_text,
                    reply_markup=keyboard
                )
                print(f"Start text sent to {user_id}")
        else:
            await message.reply_text(
                text=start_text,
                reply_markup=keyboard
            )
            print(f"Start text sent to {user_id}")
            
    except Exception as e:
        print(f"Critical error in start command: {e}")
        import traceback
        traceback.print_exc()
        try:
            await message.reply_text("❌ Bot is having some issues. Please try again later.")
        except:
            print("Failed to send error message")

@Client.on_callback_query(filters.regex("^check_subscription$"))
async def check_subscription_callback(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        first_name = callback_query.from_user.first_name
        
        print(f"Check subscription callback from {user_id}")
        
        # Check subscription status
        is_subscribed = await is_user_subscribed(client, user_id)
        print(f"User {user_id} subscription status after check: {is_subscribed}")
        
        if not is_subscribed:
            await callback_query.answer("❌ Please join the channel first!", show_alert=True)
            return
        
        # User is now subscribed
        await callback_query.answer("✅ Welcome! You can now use the bot.", show_alert=True)
        
        # Send start message
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Tutorial", callback_data="tutorial"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")
            ],
            [
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
                InlineKeyboardButton("💰 Donate", callback_data="donate")
            ],
            [
                InlineKeyboardButton("📞 Support", url="https://t.me/MadflixBots_Support"),
                InlineKeyboardButton("📢 Channel", url="https://t.me/Madflix_Bots")
            ]
        ])
        
        start_text = Txt.START_TXT.format(first_name)
        
        # Delete force sub message and send start message
        await callback_query.message.delete()
        
        if Config.START_PIC:
            try:
                await client.send_photo(
                    chat_id=user_id,
                    photo=Config.START_PIC,
                    caption=start_text,
                    reply_markup=keyboard
                )
                print(f"Start photo sent via callback to {user_id}")
            except Exception as e:
                print(f"Error sending photo via callback: {e}")
                await client.send_message(
                    chat_id=user_id,
                    text=start_text,
                    reply_markup=keyboard
                )
                print(f"Start text sent via callback to {user_id}")
        else:
            await client.send_message(
                chat_id=user_id,
                text=start_text,
                reply_markup=keyboard
            )
            print(f"Start text sent via callback to {user_id}")
            
    except Exception as e:
        print(f"Error in check subscription callback: {e}")
        import traceback
        traceback.print_exc()
        await callback_query.answer("❌ An error occurred!", show_alert=True)

@Client.on_callback_query(filters.regex("^tutorial$"))
async def tutorial_callback(client, callback_query):
    user_id = callback_query.from_user.id
    format_template = await madflixbotz.get_format_template(user_id)
    
    back_button = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🦋 Admin", url="https://t.me/CallAdminRobot"), 
            InlineKeyboardButton("⚡ Tutorial", url="https://t.me/MadflixBots_Support")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="start_back")]
    ])
    
    await callback_query.edit_message_caption(
        caption=Txt.FILE_NAME_TXT.format(format_template=format_template or "Not Set"),
        reply_markup=back_button
    )

@Client.on_callback_query(filters.regex("^about$"))
async def about_callback(client, callback_query):
    await callback_query.edit_message_caption(
        caption=Txt.ABOUT_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="start_back")]
        ])
    )

@Client.on_callback_query(filters.regex("^donate$"))
async def donate_callback(client, callback_query):
    await callback_query.edit_message_caption(
        caption=Txt.DONATE_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="start_back")]
        ])
    )

@Client.on_callback_query(filters.regex("^start_back$"))
async def start_back_callback(client, callback_query):
    first_name = callback_query.from_user.first_name
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Tutorial", callback_data="tutorial"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
            InlineKeyboardButton("💰 Donate", callback_data="donate")
        ],
        [
            InlineKeyboardButton("📞 Support", url="https://t.me/MadflixBots_Support"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/Madflix_Bots")
        ]
    ])
    
    await callback_query.edit_message_caption(
        caption=Txt.START_TXT.format(first_name),
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^close$"))
async def close_callback(client, callback_query):
    await callback_query.message.delete()

# Test command for debugging
@Client.on_message(filters.private & filters.command("test"))
async def test_command(client, message):
    user_id = message.from_user.id
    is_subscribed = await is_user_subscribed(client, user_id)
    await message.reply_text(f"✅ Bot is working!\n🔍 Subscribed: {is_subscribed}")

# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Developer @JishuDeveloper
