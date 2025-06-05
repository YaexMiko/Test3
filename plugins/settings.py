from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InputMediaPhoto
from helper.database import madflixbotz
from config import Config
import asyncio

# Upload mode states
UPLOAD_MODES = ["Telegram", "Gdrive", "Reclone"]

# Store conversation states
user_states = {}

# Store original settings messages for each user
user_settings_messages = {}

@Client.on_message(filters.private & filters.command("settings"))
async def settings_command(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Get user settings from database
    upload_mode = await madflixbotz.get_upload_mode(user_id) or "Telegram"
    send_as_document = await madflixbotz.get_send_as_document(user_id)
    upload_destination = await madflixbotz.get_upload_destination(user_id)
    thumbnail = await madflixbotz.get_thumbnail(user_id)
    prefix = await madflixbotz.get_prefix(user_id)
    suffix = await madflixbotz.get_suffix(user_id)
    
    # Create settings text
    settings_text = await create_settings_text(username, upload_mode, send_as_document, upload_destination, thumbnail, prefix, suffix)
    
    # Create inline keyboard
    keyboard = await create_settings_keyboard(upload_mode, send_as_document, upload_destination, thumbnail, prefix, suffix)
    
    # Get the photo for settings (custom thumbnail or start pic)
    settings_photo = thumbnail if thumbnail else Config.START_PIC
    
    # Send settings message with photo
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

async def create_settings_text(username, upload_mode, send_as_document, upload_destination, thumbnail, prefix=None, suffix=None):
    upload_type = "DOCUMENT" if send_as_document else "MEDIA"
    destination_text = upload_destination if upload_destination else "None"
    thumbnail_status = "Exists" if thumbnail else "Not Exists"
    prefix_text = prefix if prefix else "None"
    suffix_text = suffix if suffix else "None"
    
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
Rename mode is Manual"""
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
Rename mode is Manual"""
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
Rename mode is Manual"""
    
    return settings_text

async def create_settings_keyboard(upload_mode, send_as_document, upload_destination, thumbnail, prefix=None, suffix=None):
    # Create checkmark for current upload mode
    upload_text = f"Upload Mode | {upload_mode}"
    if upload_mode in UPLOAD_MODES:
        upload_text += " ✓"
    
    # Send as document/media button text
    document_text = "Send As Media" if send_as_document else "Send As Document"
    
    # Upload destination button text
    destination_text = "Set Upload Destination"
    if upload_destination:
        destination_text += " ✓"
    
    # Thumbnail button text
    thumbnail_text = "Set Thumbnail"
    if thumbnail:
        thumbnail_text = "Thumbnail ✓"
    
    # Prefix button text
    prefix_text = "Set Prefix"
    if prefix:
        prefix_text = "Prefix ✓"
    
    # Suffix button text
    suffix_text = "Set Suffix"
    if suffix:
        suffix_text = "Suffix ✓"
    
    if upload_mode == "Telegram":
        keyboard = [
            [InlineKeyboardButton(upload_text, callback_data="toggle_upload_mode")],
            [
                InlineKeyboardButton(document_text, callback_data="toggle_send_as_document"),
                InlineKeyboardButton(destination_text, callback_data="set_upload_destination")
            ]
        ]
        
        # Add reset destination button if destination is set
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
                InlineKeyboardButton("Rename Mode | Manual", callback_data="rename_mode_menu"),
                InlineKeyboardButton("Set Metadata", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton("Remove Words", callback_data="coming_soon"),
                InlineKeyboardButton("Enable Sample Video", callback_data="coming_soon")
            ],
            [
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
                InlineKeyboardButton("Rename Mode | Manual", callback_data="rename_mode_menu")
            ],
            [
                InlineKeyboardButton("Set Metadata", callback_data="coming_soon"),
                InlineKeyboardButton("Remove Words", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton("Enable Sample Video", callback_data="coming_soon"),
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
                InlineKeyboardButton("Rename Mode | Manual", callback_data="rename_mode_menu"),
                InlineKeyboardButton("Set Metadata", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton("Remove Words", callback_data="coming_soon"),
                InlineKeyboardButton("Enable Sample Video", callback_data="coming_soon")
            ],
            [
                InlineKeyboardButton("Enable Screenshot", callback_data="coming_soon")
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

async def send_settings_menu(client, user_id, message_to_edit=None):
    """Send or edit settings menu"""
    try:
        user_info = await client.get_users(user_id)
        username = user_info.username or user_info.first_name
    except:
        username = "User"
    
    # Get user settings
    upload_mode = await madflixbotz.get_upload_mode(user_id) or "Telegram"
    send_as_document = await madflixbotz.get_send_as_document(user_id)
    upload_destination = await madflixbotz.get_upload_destination(user_id)
    thumbnail = await madflixbotz.get_thumbnail(user_id)
    prefix = await madflixbotz.get_prefix(user_id)
    suffix = await madflixbotz.get_suffix(user_id)
    
    # Create settings text
    settings_text = await create_settings_text(username, upload_mode, send_as_document, upload_destination, thumbnail, prefix, suffix)
    
    # Create keyboard
    keyboard = await create_settings_keyboard(upload_mode, send_as_document, upload_destination, thumbnail, prefix, suffix)
    
    # If message_to_edit is provided, edit that message
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
    
    # Otherwise send new message
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

@Client.on_callback_query(filters.regex("^toggle_upload_mode$"))
async def toggle_upload_mode(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name
    
    # Get current upload mode
    current_mode = await madflixbotz.get_upload_mode(user_id) or "Telegram"
    
    # Get next mode in cycle
    current_index = UPLOAD_MODES.index(current_mode)
    next_index = (current_index + 1) % len(UPLOAD_MODES)
    new_mode = UPLOAD_MODES[next_index]
    
    # Save new mode to database
    await madflixbotz.set_upload_mode(user_id, new_mode)
    
    # Get other settings
    send_as_document = await madflixbotz.get_send_as_document(user_id)
    upload_destination = await madflixbotz.get_upload_destination(user_id)
    thumbnail = await madflixbotz.get_thumbnail(user_id)
    prefix = await madflixbotz.get_prefix(user_id)
    suffix = await madflixbotz.get_suffix(user_id)
    
    # Update settings text and keyboard
    settings_text = await create_settings_text(username, new_mode, send_as_document, upload_destination, thumbnail, prefix, suffix)
    keyboard = await create_settings_keyboard(new_mode, send_as_document, upload_destination, thumbnail, prefix, suffix)
    
    # Update message
    await callback_query.edit_message_caption(
        caption=settings_text,
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^toggle_send_as_document$"))
async def toggle_send_as_document(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name
    
    # Get current setting
    current_setting = await madflixbotz.get_send_as_document(user_id)
    new_setting = not current_setting
    
    # Save new setting
    await madflixbotz.set_send_as_document(user_id, new_setting)
    
    # Get other settings
    upload_mode = await madflixbotz.get_upload_mode(user_id) or "Telegram"
    upload_destination = await madflixbotz.get_upload_destination(user_id)
    thumbnail = await madflixbotz.get_thumbnail(user_id)
    prefix = await madflixbotz.get_prefix(user_id)
    suffix = await madflixbotz.get_suffix(user_id)
    
    # Update settings text and keyboard
    settings_text = await create_settings_text(username, upload_mode, new_setting, upload_destination, thumbnail, prefix, suffix)
    keyboard = await create_settings_keyboard(upload_mode, new_setting, upload_destination, thumbnail, prefix, suffix)
    
    # Update message
    await callback_query.edit_message_caption(
        caption=settings_text,
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^set_upload_destination$"))
async def set_upload_destination(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Store the original settings message
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
    
    # Set user state to waiting for destination
    user_states[user_id] = "waiting_for_destination"
    
    # Start timeout task
    asyncio.create_task(destination_timeout(client, callback_query, user_id))

@Client.on_callback_query(filters.regex("^reset_upload_destination$"))
async def reset_upload_destination(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Reset upload destination
    await madflixbotz.set_upload_destination(user_id, None)
    
    # Redirect back to settings
    await back_to_settings(client, callback_query)

@Client.on_callback_query(filters.regex("^set_prefix$"))
async def set_prefix(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Store the original settings message
    user_settings_messages[user_id] = callback_query.message
    
    # Check if prefix is already set
    current_prefix = await madflixbotz.get_prefix(user_id)
    
    if current_prefix:
        # Show remove option
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
        # Show set option
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
        
        # Set user state to waiting for prefix
        user_states[user_id] = "waiting_for_prefix"
        
        # Start timeout task
        asyncio.create_task(prefix_timeout(client, callback_query, user_id))
    
    await callback_query.edit_message_caption(
        caption=prefix_text,
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^set_suffix$"))
async def set_suffix(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Store the original settings message
    user_settings_messages[user_id] = callback_query.message
    
    # Check if suffix is already set
    current_suffix = await madflixbotz.get_suffix(user_id)
    
    if current_suffix:
        # Show remove option
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
        # Show set option
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
        
        # Set user state to waiting for suffix
        user_states[user_id] = "waiting_for_suffix"
        
        # Start timeout task
        asyncio.create_task(suffix_timeout(client, callback_query, user_id))
    
    await callback_query.edit_message_caption(
        caption=suffix_text,
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^remove_prefix$"))
async def remove_prefix(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Remove prefix from database
    await madflixbotz.set_prefix(user_id, None)
    
    # Edit back to main settings (same message)
    await back_to_settings(client, callback_query)

@Client.on_callback_query(filters.regex("^remove_suffix$"))
async def remove_suffix(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Remove suffix from database
    await madflixbotz.set_suffix(user_id, None)
    
    # Edit back to main settings (same message)
    await back_to_settings(client, callback_query)

@Client.on_callback_query(filters.regex("^back_to_settings$"))
async def back_to_settings(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Clear any pending states
    if user_id in user_states:
        del user_states[user_id]
    
    # Clear stored message reference
    if user_id in user_settings_messages:
        del user_settings_messages[user_id]
    
    # Edit current message back to settings
    await send_settings_menu(client, user_id, callback_query.message)

@Client.on_callback_query(filters.regex("^settings_menu$"))
async def settings_menu_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Edit current message to show settings
    await send_settings_menu(client, user_id, callback_query.message)

@Client.on_callback_query(filters.regex("^set_thumbnail$"))
async def set_thumbnail_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Store the original settings message
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
    
    # Set user state to waiting for thumbnail
    user_states[user_id] = "waiting_for_thumbnail"
    
    # Start timeout task
    asyncio.create_task(thumbnail_timeout(client, callback_query, user_id))

@Client.on_callback_query(filters.regex("^coming_soon$"))
async def coming_soon_callback(client, callback_query: CallbackQuery):
    await callback_query.answer("🔜 Coming Soon!", show_alert=True)

@Client.on_callback_query(filters.regex("^close$"))
async def close_callback(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Clear any pending states
    if user_id in user_states:
        del user_states[user_id]
    
    # Clear stored message reference
    if user_id in user_settings_messages:
        del user_settings_messages[user_id]
    
    await callback_query.message.delete()

# Message handler for prefix/suffix/destination/thumbnail input
@Client.on_message(filters.private & filters.text)
async def handle_text_input(client, message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)
    
    # Skip if not in a waiting state
    if user_state not in ["waiting_for_prefix", "waiting_for_suffix", "waiting_for_destination"]:
        return
    
    if user_state == "waiting_for_prefix":
        # Save prefix
        prefix = message.text.strip()
        await madflixbotz.set_prefix(user_id, prefix)
        
        # Delete user message
        try:
            await message.delete()
        except:
            pass
        
        # Remove user state
        if user_id in user_states:
            del user_states[user_id]
        
        # Send success message
        success_msg = await message.reply_text("**Prefix Set Successfully! ✅**")
        await asyncio.sleep(2)
        await success_msg.delete()
        
        # Edit the original settings message (not send new)
        original_message = user_settings_messages.get(user_id)
        if original_message:
            await send_settings_menu(client, user_id, original_message)
            # Clean up
            del user_settings_messages[user_id]
        
    elif user_state == "waiting_for_suffix":
        # Save suffix
        suffix = message.text.strip()
        await madflixbotz.set_suffix(user_id, suffix)
        
        # Delete user message
        try:
            await message.delete()
        except:
            pass
        
        # Remove user state
        if user_id in user_states:
            del user_states[user_id]
        
        # Send success message
        success_msg = await message.reply_text("**Suffix Set Successfully! ✅**")
        await asyncio.sleep(2)
        await success_msg.delete()
        
        # Edit the original settings message (not send new)
        original_message = user_settings_messages.get(user_id)
        if original_message:
            await send_settings_menu(client, user_id, original_message)
            # Clean up
            del user_settings_messages[user_id]
    
    elif user_state == "waiting_for_destination":
        # Handle destination setting
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
            
            # Edit original message
            original_message = user_settings_messages.get(user_id)
            if original_message:
                await send_settings_menu(client, user_id, original_message)
                del user_settings_messages[user_id]
        else:
            await message.reply_text("**Invalid destination! Please send a valid chat ID starting with -100**")

# Message handler for thumbnail photos
@Client.on_message(filters.private & filters.photo)
async def handle_thumbnail_photo(client, message):
    user_id = message.from_user.id
    user_state = user_states.get(user_id)
    
    if user_state == "waiting_for_thumbnail":
        # Save thumbnail
        await madflixbotz.set_thumbnail(user_id, message.photo.file_id)
        
        # Delete user message
        try:
            await message.delete()
        except:
            pass
        
        # Remove user state
        if user_id in user_states:
            del user_states[user_id]
        
        # Send success message
        success_msg = await message.reply_text("**Thumbnail Set Successfully! ✅**")
        await asyncio.sleep(2)
        await success_msg.delete()
        
        # Edit the original settings message
        original_message = user_settings_messages.get(user_id)
        if original_message:
            await send_settings_menu(client, user_id, original_message)
            # Clean up
            del user_settings_messages[user_id]

async def destination_timeout(client, callback_query, user_id):
    """Handle destination input timeout"""
    await asyncio.sleep(60)
    
    # Check if user is still waiting for destination
    if user_states.get(user_id) == "waiting_for_destination":
        # Remove user state
        if user_id in user_states:
            del user_states[user_id]
        
        # Edit back to settings
        try:
            await send_settings_menu(client, user_id, callback_query.message)
            # Clean up
            if user_id in user_settings_messages:
                del user_settings_messages[user_id]
        except:
            pass

async def prefix_timeout(client, callback_query, user_id):
    """Handle prefix input timeout"""
    await asyncio.sleep(60)
    
    # Check if user is still waiting for prefix
    if user_states.get(user_id) == "waiting_for_prefix":
        # Remove user state
        if user_id in user_states:
            del user_states[user_id]
        
        # Edit back to settings
        try:
            await send_settings_menu(client, user_id, callback_query.message)
            # Clean up
            if user_id in user_settings_messages:
                del user_settings_messages[user_id]
        except:
            pass

async def suffix_timeout(client, callback_query, user_id):
    """Handle suffix input timeout"""
    await asyncio.sleep(60)
    
    # Check if user is still waiting for suffix
    if user_states.get(user_id) == "waiting_for_suffix":
        # Remove user state
        if user_id in user_states:
            del user_states[user_id]
        
        # Edit back to settings
        try:
            await send_settings_menu(client, user_id, callback_query.message)
            # Clean up
            if user_id in user_settings_messages:
                del user_settings_messages[user_id]
        except:
            pass

async def thumbnail_timeout(client, callback_query, user_id):
    """Handle thumbnail input timeout"""
    await asyncio.sleep(60)
    
    # Check if user is still waiting for thumbnail
    if user_states.get(user_id) == "waiting_for_thumbnail":
        # Remove user state
        if user_id in user_states:
            del user_states[user_id]
        
        # Edit back to settings
        try:
            await send_settings_menu(client, user_id, callback_query.message)
            # Clean up
            if user_id in user_settings_messages:
                del user_settings_messages[user_id]
        except:
            pass

# ========== RENAME MODE MENU ==========

@Client.on_callback_query(filters.regex("^rename_mode_menu$"))
async def rename_mode_menu(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Get current rename mode
    rename_mode = await madflixbotz.get_rename_mode(user_id) or "Manual"
    
    keyboard = [
        [InlineKeyboardButton("Set Auto Rename Mode", callback_data="coming_soon")],
        [InlineKeyboardButton("Manual Mode ✓" if rename_mode == "Manual" else "Manual Mode", callback_data="set_manual_mode")],
        [InlineKeyboardButton("Use AI Autorename ❌", callback_data="coming_soon")],
        [InlineKeyboardButton("Back", callback_data="settings_menu")],
        [InlineKeyboardButton("Close", callback_data="close")]
    ]
    
    await callback_query.edit_message_caption(
        caption=f"**Choose from Below Buttons!**\n\n**Rename mode is {rename_mode}**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@Client.on_callback_query(filters.regex("^set_manual_mode$"))
async def set_manual_mode(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Set manual mode in database
    await madflixbotz.set_rename_mode(user_id, "Manual")
    
    # Return to settings menu
    await send_settings_menu(client, user_id, callback_query.message)

@Client.on_callback_query(filters.regex("^coming_soon$"))
async def coming_soon_handler(client, callback_query: CallbackQuery):
    await callback_query.answer("🚧 This feature is coming soon! Stay tuned for updates.", show_alert=True)

# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Developer @JishuDeveloper
