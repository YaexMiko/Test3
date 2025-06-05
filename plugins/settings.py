from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InputMediaPhoto
from helper.database import madflixbotz
from config import Config
import asyncio

UPLOAD_MODES = ["Telegram", "Gdrive", "Reclone"]
user_states = {}
user_settings_messages = {}

# =========================
# Settings Text Function
# =========================

async def create_settings_text(
    username, upload_mode, send_as_document, upload_destination,
    thumbnail, prefix=None, suffix=None, rename_mode="Manual", user_id=None
):
    upload_type = "DOCUMENT" if send_as_document else "MEDIA"
    destination_text = upload_destination if upload_destination else "None"
    thumbnail_status = "Exists" if thumbnail else "Not Exists"
    prefix_text = prefix if prefix else "None"
    suffix_text = suffix if suffix else "None"

    # Get batch mode status using user_id instead of username
    batch_mode_status = "Disabled"
    if user_id:
        try:
            format_template = await madflixbotz.get_format_template(user_id)
            batch_mode_status = "Enabled" if format_template else "Disabled"
        except:
            batch_mode_status = "Disabled"

    if upload_mode == "Telegram":
        settings_text = f"""Settings for {username}

Custom Thumbnail {thumbnail_status}
Upload Type is {upload_type}
Prefix is {prefix_text}
Suffix is {suffix_text}

Upload Destination is {destination_text}
Sample Video is Disabled
Screenshot is Disabled

Metadata is Disabled
Remove/Replace Words is None
Rename mode is {rename_mode}
Batch Auto Rename is {batch_mode_status}"""
    elif upload_mode == "Gdrive":
        settings_text = f"""Settings for {username}

Gdrive Token Not Exists
Gdrive ID is None
Index Link is None
Stop Duplicate is Disabled

Sample Video is Disabled
Screenshot is Disabled
Prefix is {prefix_text}

Suffix is {suffix_text}
Metadata is Disabled
Remove/Replace Words is None
Rename mode is {rename_mode}
Batch Auto Rename is {batch_mode_status}"""
    else:  # Reclone
        settings_text = f"""Settings for {username}

Reclone Config Not Exists
Reclone Path is None
Prefix is {prefix_text}

Sample Video is Disabled
Screenshot is Disabled
Suffix is {suffix_text}

Metadata is Disabled
Remove/Replace Words is None
Rename mode is {rename_mode}
Batch Auto Rename is {batch_mode_status}"""

    return settings_text

# =========================
# Settings Keyboard Function
# =========================

async def create_settings_keyboard(
    upload_mode, send_as_document, upload_destination, thumbnail,
    prefix=None, suffix=None, rename_mode="Manual", user_id=None
):
    upload_text = f"Upload Mode | {upload_mode}"
    if upload_mode in UPLOAD_MODES:
        upload_text += " ✓"

    document_text = "Send As Media" if send_as_document else "Send As Document"
    destination_text = "Set Upload Destination"
    if upload_destination:
        destination_text += " ✓"
    thumbnail_text = "Set Thumbnail"
    if thumbnail:
        thumbnail_text = "Thumbnail ✓"
    prefix_text = "Set Prefix"
    if prefix:
        prefix_text = "Prefix ✓"
    suffix_text = "Set Suffix"
    if suffix:
        suffix_text = "Suffix ✓"

    rename_mode_text = f"Rename Mode | {rename_mode}"

    if upload_mode == "Telegram":
        keyboard = [
            [InlineKeyboardButton(upload_text, callback_data="toggle_upload_mode")],
            [
                InlineKeyboardButton(document_text, callback_data="toggle_send_as_document"),
                InlineKeyboardButton(destination_text, callback_data="set_upload_destination")
            ]
        ]
        if upload_destination:
            keyboard.append([InlineKeyboardButton("Reset Upload Destination", callback_data="reset_upload_destination")])
        keyboard.extend([
            [
                InlineKeyboardButton(thumbnail_text, callback_data="set_thumbnail"),
                InlineKeyboardButton("Set Caption", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton(suffix_text, callback_data="set_suffix"),
                InlineKeyboardButton(prefix_text, callback_data="set_prefix")
            ],
            [
                InlineKeyboardButton(rename_mode_text, callback_data="rename_mode_menu"),
                InlineKeyboardButton("Set Metadata", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton("Auto Rename Template", callback_data="set_auto_rename_template"),
                InlineKeyboardButton("Enable Sample Video", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton("Remove Words", callback_data="coming_soon"),
                InlineKeyboardButton("Enable Screenshot", callback_data="coming_soon")
            ]
        ])
    elif upload_mode == "Gdrive":
        keyboard = [
            [InlineKeyboardButton(upload_text, callback_data="toggle_upload_mode")],
            [
                InlineKeyboardButton("token.pickle", callback_data="coming_soon"),
                InlineKeyboardButton("Gdrive ID", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton("Index URL", callback_data="coming_soon"),
                InlineKeyboardButton(suffix_text, callback_data="set_suffix")
            ],
            [
                InlineKeyboardButton(prefix_text, callback_data="set_prefix"),
                InlineKeyboardButton(rename_mode_text, callback_data="rename_mode_menu")
            ],
            [
                InlineKeyboardButton("Auto Rename Template", callback_data="set_auto_rename_template"),
                InlineKeyboardButton("Enable Sample Video", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton("Set Metadata", callback_data="coming_soon"),
                InlineKeyboardButton("Remove Words", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton("Enable Screenshot", callback_data="coming_soon")
            ]
        ]
    else:  # Reclone
        keyboard = [
            [InlineKeyboardButton(upload_text, callback_data="toggle_upload_mode")],
            [
                InlineKeyboardButton("Reclone Config", callback_data="coming_soon"),
                InlineKeyboardButton("Reclone Path", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton(suffix_text, callback_data="set_suffix"),
                InlineKeyboardButton(prefix_text, callback_data="set_prefix")
            ],
            [
                InlineKeyboardButton(rename_mode_text, callback_data="rename_mode_menu"),
                InlineKeyboardButton("Set Metadata", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton("Auto Rename Template", callback_data="set_auto_rename_template"),
                InlineKeyboardButton("Enable Sample Video", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton("Remove Words", callback_data="coming_soon"),
                InlineKeyboardButton("Enable Screenshot", callback_data="coming_soon")
            ]
        ]

    return InlineKeyboardMarkup(keyboard)

# =========================
# Settings Menu Functions
# =========================

async def send_settings_menu(client, user_id, message_to_edit=None):
    try:
        user_info = await client.get_users(user_id)
        username = user_info.username or user_info.first_name
    except:
        username = "User"

    upload_mode = await madflixbotz.get_upload_mode(user_id) or "Telegram"
    send_as_document = await madflixbotz.get_send_as_document(user_id)
    upload_destination = await madflixbotz.get_upload_destination(user_id)
    thumbnail = await madflixbotz.get_thumbnail(user_id)
    prefix = await madflixbotz.get_prefix(user_id)
    suffix = await madflixbotz.get_suffix(user_id)
    rename_mode = await madflixbotz.get_rename_mode(user_id) or "Manual"

    settings_text = await create_settings_text(
        username, upload_mode, send_as_document, upload_destination,
        thumbnail, prefix, suffix, rename_mode, user_id
    )
    keyboard = await create_settings_keyboard(
        upload_mode, send_as_document, upload_destination,
        thumbnail, prefix, suffix, rename_mode, user_id
    )

    if message_to_edit:
        try:
            await message_to_edit.edit_caption(
                caption=settings_text,
                reply_markup=keyboard
            )
            return
        except:
            try:
                await message_to_edit.edit_text(
                    text=settings_text,
                    reply_markup=keyboard
                )
                return
            except:
                pass

    settings_photo = thumbnail if thumbnail else Config.START_PIC

    if settings_photo:
        await client.send_photo(
            user_id,
            settings_photo,
            caption=settings_text,
            reply_markup=keyboard
        )
    else:
        await client.send_message(
            user_id,
            settings_text,
            reply_markup=keyboard
        )

# =========================
# Command & Callback Handlers
# =========================

@Client.on_message(filters.private & filters.command("settings"))
async def settings_command(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    upload_mode = await madflixbotz.get_upload_mode(user_id) or "Telegram"
    send_as_document = await madflixbotz.get_send_as_document(user_id)
    upload_destination = await madflixbotz.get_upload_destination(user_id)
    thumbnail = await madflixbotz.get_thumbnail(user_id)
    prefix = await madflixbotz.get_prefix(user_id)
    suffix = await madflixbotz.get_suffix(user_id)
    rename_mode = await madflixbotz.get_rename_mode(user_id) or "Manual"

    settings_text = await create_settings_text(
        username, upload_mode, send_as_document, upload_destination,
        thumbnail, prefix, suffix, rename_mode, user_id
    )
    keyboard = await create_settings_keyboard(
        upload_mode, send_as_document, upload_destination,
        thumbnail, prefix, suffix, rename_mode, user_id
    )

    settings_photo = thumbnail if thumbnail else Config.START_PIC

    if settings_photo:
        await message.reply_photo(
            settings_photo,
            caption=settings_text,
            reply_markup=keyboard
        )
    else:
        await message.reply_text(
            settings_text,
            reply_markup=keyboard
        )

@Client.on_callback_query(filters.regex("^toggle_upload_mode$"))
async def toggle_upload_mode(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name

    current_mode = await madflixbotz.get_upload_mode(user_id) or "Telegram"
    current_index = UPLOAD_MODES.index(current_mode)
    next_index = (current_index + 1) % len(UPLOAD_MODES)
    new_mode = UPLOAD_MODES[next_index]
    await madflixbotz.set_upload_mode(user_id, new_mode)

    send_as_document = await madflixbotz.get_send_as_document(user_id)
    upload_destination = await madflixbotz.get_upload_destination(user_id)
    thumbnail = await madflixbotz.get_thumbnail(user_id)
    prefix = await madflixbotz.get_prefix(user_id)
    suffix = await madflixbotz.get_suffix(user_id)
    rename_mode = await madflixbotz.get_rename_mode(user_id) or "Manual"

    settings_text = await create_settings_text(
        username, new_mode, send_as_document, upload_destination, thumbnail, prefix, suffix, rename_mode, user_id
    )
    keyboard = await create_settings_keyboard(
        new_mode, send_as_document, upload_destination, thumbnail, prefix, suffix, rename_mode, user_id
    )

    await callback_query.edit_message_caption(
        caption=settings_text,
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^toggle_send_as_document$"))
async def toggle_send_as_document(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name

    current_setting = await madflixbotz.get_send_as_document(user_id)
    new_setting = not current_setting
    await madflixbotz.set_send_as_document(user_id, new_setting)

    upload_mode = await madflixbotz.get_upload_mode(user_id) or "Telegram"
    upload_destination = await madflixbotz.get_upload_destination(user_id)
    thumbnail = await madflixbotz.get_thumbnail(user_id)
    prefix = await madflixbotz.get_prefix(user_id)
    suffix = await madflixbotz.get_suffix(user_id)
    rename_mode = await madflixbotz.get_rename_mode(user_id) or "Manual"

    settings_text = await create_settings_text(
        username, upload_mode, new_setting, upload_destination, thumbnail, prefix, suffix, rename_mode, user_id
    )
    keyboard = await create_settings_keyboard(
        upload_mode, new_setting, upload_destination, thumbnail, prefix, suffix, rename_mode, user_id
    )

    await callback_query.edit_message_caption(
        caption=settings_text,
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^set_upload_destination$"))
async def set_upload_destination(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_settings_messages[user_id] = callback_query.message

    destination_text = """If you Add Bot Will Upload your files in your channel or group.

Steps To Add:
1. First Create a new channel or group if u don't have.
2. After that Click on below button to add in your channel or group(As Admin with enough permission).
3. After adding send /id command in your channel or group.
4. You will get a chat_id starting with -100
5. Copy That and send here.

You can also upload on specific Group Topic.
Example:
-100xxx:topic_id

Send Upload Destination ID. Timeout: 60 sec"""

    bot_username = client.username
    channel_link = f"http://t.me/{bot_username}?startchannel&admin=post_messages+edit_messages+delete_messages"
    group_link = f"http://t.me/{bot_username}?startgroup&admin=post_messages+edit_messages+delete_messages"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Add In Channel", url=channel_link)],
        [InlineKeyboardButton("Add In Group", url=group_link)],
        [InlineKeyboardButton("Back", callback_data="back_to_settings")],
        [InlineKeyboardButton("Close", callback_data="close")]
    ])

    await callback_query.edit_message_caption(
        caption=destination_text,
        reply_markup=keyboard
    )

    user_states[user_id] = "waiting_for_destination"
    asyncio.create_task(destination_timeout(client, callback_query, user_id))

@Client.on_callback_query(filters.regex("^reset_upload_destination$"))
async def reset_upload_destination(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await madflixbotz.set_upload_destination(user_id, None)
    await back_to_settings(client, callback_query)

@Client.on_callback_query(filters.regex("^set_prefix$"))
async def set_prefix(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_settings_messages[user_id] = callback_query.message
    current_prefix = await madflixbotz.get_prefix(user_id)

    if current_prefix:
        prefix_text = f"""Prefix is the Front Part attached with the Filename.

Example:
Prefix = @PublicMirrorLeech

This will give output of:
@PublicMirrorLeech Fast_And_Furious.mkv

Current Prefix: {current_prefix}"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Remove Prefix", callback_data="remove_prefix")],
            [InlineKeyboardButton("Back", callback_data="back_to_settings")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ])
    else:
        prefix_text = """Prefix is the Front Part attached with the Filename.

Example:
Prefix = @PublicMirrorLeech

This will give output of:
@PublicMirrorLeech Fast_And_Furious.mkv

Send Prefix. Timeout: 60 sec"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Back", callback_data="back_to_settings")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ])
        user_states[user_id] = "waiting_for_prefix"
        asyncio.create_task(prefix_timeout(client, callback_query, user_id))

    await callback_query.edit_message_caption(
        caption=prefix_text,
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^set_suffix$"))
async def set_suffix(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_settings_messages[user_id] = callback_query.message
    current_suffix = await madflixbotz.get_suffix(user_id)

    if current_suffix:
        suffix_text = f"""Suffix is the End Part attached with the Filename.

Example:
Suffix = @PublicMirrorLeech

This will give output of:
Fast_And_Furious @PublicMirrorLeech.mkv

Current Suffix: {current_suffix}"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Remove Suffix", callback_data="remove_suffix")],
            [InlineKeyboardButton("Back", callback_data="back_to_settings")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ])
    else:
        suffix_text = """Suffix is the End Part attached with the Filename.

Example:
Suffix = @PublicMirrorLeech

This will give output of:
Fast_And_Furious @PublicMirrorLeech.mkv

Send Suffix. Timeout: 60 sec"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Back", callback_data="back_to_settings")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ])
        user_states[user_id] = "waiting_for_suffix"
        asyncio.create_task(suffix_timeout(client, callback_query, user_id))

    await callback_query.edit_message_caption(
        caption=suffix_text,
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^remove_prefix$"))
async def remove_prefix(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await madflixbotz.set_prefix(user_id, None)
    await back_to_settings(client, callback_query)

@Client.on_callback_query(filters.regex("^remove_suffix$"))
async def remove_suffix(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await madflixbotz.set_suffix(user_id, None)
    await back_to_settings(client, callback_query)

@Client.on_callback_query(filters.regex("^back_to_settings$"))
async def back_to_settings(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_settings_messages:
        del user_settings_messages[user_id]
    await send_settings_menu(client, user_id, callback_query.message)

@Client.on_callback_query(filters.regex("^settings_menu$"))
async def settings_menu_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await send_settings_menu(client, user_id, callback_query.message)

@Client.on_callback_query(filters.regex("^set_thumbnail$"))
async def set_thumbnail_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_settings_messages[user_id] = callback_query.message

    thumbnail_text = """📸 HOW TO SET THUMBNAIL

⦿ You Can Add Custom Thumbnail Simply By Sending A Photo To Me....

⦿ /viewthumb - Use This Command To See Your Thumbnail
⦿ /delthumb - Use This Command To Delete Your Thumbnail

Send a photo to set as thumbnail. Timeout: 60 sec"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Back", callback_data="back_to_settings")],
        [InlineKeyboardButton("Close", callback_data="close")]
    ])

    await callback_query.edit_message_caption(
        caption=thumbnail_text,
        reply_markup=keyboard
    )

    user_states[user_id] = "waiting_for_thumbnail"
    asyncio.create_task(thumbnail_timeout(client, callback_query, user_id))

@Client.on_callback_query(filters.regex("^coming_soon$"))
async def coming_soon_callback(client, callback_query: CallbackQuery):
    await callback_query.answer("🔜 Coming Soon!", show_alert=True)

@Client.on_callback_query(filters.regex("^close$"))
async def close_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_settings_messages:
        del user_settings_messages[user_id]
    await callback_query.message.delete()

@Client.on_message(filters.private & filters.text)
async def handle_text_input(client, message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)
    if user_state not in ["waiting_for_prefix", "waiting_for_suffix", "waiting_for_destination"]:
        return

    if user_state == "waiting_for_prefix":
        prefix = message.text.strip()
        await madflixbotz.set_prefix(user_id, prefix)
        try:
            await message.delete()
        except:
            pass
        if user_id in user_states:
            del user_states[user_id]
        success_msg = await message.reply_text("**Prefix Set Successfully! ✅**")
        await asyncio.sleep(2)
        await success_msg.delete()
        original_message = user_settings_messages.get(user_id)
        if original_message:
            await send_settings_menu(client, user_id, original_message)
            del user_settings_messages[user_id]

    elif user_state == "waiting_for_suffix":
        suffix = message.text.strip()
        await madflixbotz.set_suffix(user_id, suffix)
        try:
            await message.delete()
        except:
            pass
        if user_id in user_states:
            del user_states[user_id]
        success_msg = await message.reply_text("**Suffix Set Successfully! ✅**")
        await asyncio.sleep(2)
        await success_msg.delete()
        original_message = user_settings_messages.get(user_id)
        if original_message:
            await send_settings_menu(client, user_id, original_message)
            del user_settings_messages[user_id]

    elif user_state == "waiting_for_destination":
        destination = message.text.strip()
        if destination.startswith('-100'):
            await madflixbotz.set_upload_destination(user_id, destination)
            try:
                await message.delete()
            except:
                pass
            if user_id in user_states:
                del user_states[user_id]
            success_msg = await message.reply_text("**Upload Destination Set Successfully! ✅**")
            await asyncio.sleep(2)
            await success_msg.delete()
            original_message = user_settings_messages.get(user_id)
            if original_message:
                await send_settings_menu(client, user_id, original_message)
                del user_settings_messages[user_id]
        else:
            await message.reply_text("**Invalid destination! Please send a valid chat ID starting with -100**")

@Client.on_message(filters.private & filters.photo)
async def handle_thumbnail_photo(client, message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)
    if user_state == "waiting_for_thumbnail":
        await madflixbotz.set_thumbnail(user_id, message.photo.file_id)
        try:
            await message.delete()
        except:
            pass
        if user_id in user_states:
            del user_states[user_id]
        success_msg = await message.reply_text("**Thumbnail Set Successfully! ✅**")
        await asyncio.sleep(2)
        await success_msg.delete()
        original_message = user_settings_messages.get(user_id)
        if original_message:
            await send_settings_menu(client, user_id, original_message)
            del user_settings_messages[user_id]

# =========================
# Timeout Functions
# =========================

async def destination_timeout(client, callback_query, user_id):
    await asyncio.sleep(60)
    if user_states.get(user_id) == "waiting_for_destination":
        if user_id in user_states:
            del user_states[user_id]
        try:
            await send_settings_menu(client, user_id, callback_query.message)
            if user_id in user_settings_messages:
                del user_settings_messages[user_id]
        except:
            pass

async def prefix_timeout(client, callback_query, user_id):
    await asyncio.sleep(60)
    if user_states.get(user_id) == "waiting_for_prefix":
        if user_id in user_states:
            del user_states[user_id]
        try:
            await send_settings_menu(client, user_id, callback_query.message)
            if user_id in user_settings_messages:
                del user_settings_messages[user_id]
        except:
            pass

async def suffix_timeout(client, callback_query, user_id):
    await asyncio.sleep(60)
    if user_states.get(user_id) == "waiting_for_suffix":
        if user_id in user_states:
            del user_states[user_id]
        try:
            await send_settings_menu(client, user_id, callback_query.message)
            if user_id in user_settings_messages:
                del user_settings_messages[user_id]
        except:
            pass

async def thumbnail_timeout(client, callback_query, user_id):
    await asyncio.sleep(60)
    if user_states.get(user_id) == "waiting_for_thumbnail":
        if user_id in user_states:
            del user_states[user_id]
        try:
            await send_settings_menu(client, user_id, callback_query.message)
            if user_id in user_settings_messages:
                del user_settings_messages[user_id]
        except:
            pass

# ========== RENAME MODE MENU & HANDLERS ==========

@Client.on_callback_query(filters.regex("^rename_mode_menu$"))
async def rename_mode_menu(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    current_mode = await madflixbotz.get_rename_mode(user_id) or "Manual"

    keyboard = [
        [InlineKeyboardButton("Set Auto Rename Mode" + (" ✅" if current_mode == "Auto" else ""), callback_data="set_auto_rename")],
        [InlineKeyboardButton("Manual Mode" + (" ✅" if current_mode == "Manual" else ""), callback_data="set_manual_mode")],
        [InlineKeyboardButton("Use AI Autorename ❌", callback_data="coming_soon")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_back")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ]
    await callback_query.edit_message_caption(
        caption=f"Choose from Below Buttons!\n\nRename mode is {current_mode}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@Client.on_callback_query(filters.regex("^set_auto_rename$"))
async def set_auto_rename_mode(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await madflixbotz.set_rename_mode(user_id, "Auto")
    await rename_mode_menu(client, callback_query)

@Client.on_callback_query(filters.regex("^set_manual_mode$"))
async def set_manual_rename_mode(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await madflixbotz.set_rename_mode(user_id, "Manual")
    await rename_mode_menu(client, callback_query)

@Client.on_callback_query(filters.regex("^settings_back$"))
async def settings_back(client, callback_query: CallbackQuery):
    await send_settings_menu(client, callback_query.from_user.id, callback_query.message)

@Client.on_callback_query(filters.regex("^coming_soon$"))
async def coming_soon_handler(client, callback_query: CallbackQuery):
    await callback_query.answer("🚧 This feature is coming soon! Stay tuned for updates.", show_alert=True)

# =========================
# Auto Rename Template Handlers
# =========================

@Client.on_callback_query(filters.regex("^set_auto_rename_template$"))
async def set_auto_rename_template(client, callback_query):
    user_id = callback_query.from_user.id
    current_template = await madflixbotz.get_format_template(user_id)
    
    if current_template:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Remove Template", callback_data="remove_auto_template")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
        ])
        
        await callback_query.edit_message_text(
            f"**📝 Current Auto Rename Template:**\n\n"
            f"`{current_template}`\n\n"
            f"**To change:** `/autorename Your New Template`",
            reply_markup=keyboard
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
        ])
        
        await callback_query.edit_message_text(
            "**📝 Auto Rename Template Not Set**\n\n"
            "**To set:** `/autorename Your Template Here`\n\n"
            "**Example:** `/autorename Naruto S02 - EPepisode - quality`",
            reply_markup=keyboard
        )

@Client.on_callback_query(filters.regex("^remove_auto_template$"))
async def remove_auto_template(client, callback_query):
    user_id = callback_query.from_user.id
    await madflixbotz.set_format_template(user_id, None)
    await callback_query.answer("✅ Template removed!", show_alert=True)
    await send_settings_menu(client, user_id, callback_query.message)

# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Developer @JishuDeveloper
