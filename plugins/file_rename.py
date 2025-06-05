from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaDocument, Message, InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image
from datetime import datetime
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, humanbytes, convert
from helper.database import madflixbotz
from config import Config
import os
import time
import re
from collections import defaultdict

# Global storage for batch processing
user_file_queues = defaultdict(list)
user_batch_states = {}

renaming_operations = {}
# Store user states for manual renaming
user_manual_rename_state = {}

# Pattern 1: S01E02 or S01EP02
pattern1 = re.compile(r'S(\d+)(?:E|EP)(\d+)')
# Pattern 2: S01 E02 or S01 EP02 or S01 - E01 or S01 - EP02
pattern2 = re.compile(r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)')
# Pattern 3: Episode Number After "E" or "EP"
pattern3 = re.compile(r'(?:[([<{]?\s*(?:E|EP)\s*(\d+)\s*[)\]>}]?)')
# Pattern 3_2: episode number after - [hyphen]
pattern3_2 = re.compile(r'(?:\s*-\s*(\d+)\s*)')
# Pattern 4: S2 09 ex.
pattern4 = re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)
# Pattern X: Standalone Episode Number
patternX = re.compile(r'(\d+)')
# Pattern Y: Any number in filename (fallback)
patternY = re.compile(r'[^\d]*(\d+)[^\d]*', re.IGNORECASE)

#QUALITY PATTERNS 
# Pattern 5: 3-4 digits before 'p' as quality
pattern5 = re.compile(r'\b(?:.*?(\d{3,4}[^\dp]*p).*?|.*?(\d{3,4}p))\b', re.IGNORECASE)
# Pattern 6: Find 4k in brackets or parentheses
pattern6 = re.compile(r'[([<{]?\s*4k\s*[)\]>}]?', re.IGNORECASE)
# Pattern 7: Find 2k in brackets or parentheses
pattern7 = re.compile(r'[([<{]?\s*2k\s*[)\]>}]?', re.IGNORECASE)
# Pattern 8: Find HdRip without spaces
pattern8 = re.compile(r'[([<{]?\s*HdRip\s*[)\]>}]?|\bHdRip\b', re.IGNORECASE)
# Pattern 9: Find 4kX264 in brackets or parentheses
pattern9 = re.compile(r'[([<{]?\s*4kX264\s*[)\]>}]?', re.IGNORECASE)
# Pattern 10: Find 4kx265 in brackets or parentheses
pattern10 = re.compile(r'[([<{]?\s*4kx265\s*[)\]>}]?', re.IGNORECASE)

def extract_quality(filename):
    # Try Quality Patterns
    match5 = re.search(pattern5, filename)
    if match5:
        print("Matched Pattern 5")
        quality5 = match5.group(1) or match5.group(2)  # Extracted quality from both patterns
        print(f"Quality: {quality5}")
        return quality5

    match6 = re.search(pattern6, filename)
    if match6:
        print("Matched Pattern 6")
        quality6 = "4k"
        print(f"Quality: {quality6}")
        return quality6

    match7 = re.search(pattern7, filename)
    if match7:
        print("Matched Pattern 7")
        quality7 = "2k"
        print(f"Quality: {quality7}")
        return quality7

    match8 = re.search(pattern8, filename)
    if match8:
        print("Matched Pattern 8")
        quality8 = "HdRip"
        print(f"Quality: {quality8}")
        return quality8

    match9 = re.search(pattern9, filename)
    if match9:
        print("Matched Pattern 9")
        quality9 = "4kX264"
        print(f"Quality: {quality9}")
        return quality9

    match10 = re.search(pattern10, filename)
    if match10:
        print("Matched Pattern 10")
        quality10 = "4kx265"
        print(f"Quality: {quality10}")
        return quality10    

    # Return "720p" as default if no pattern matches
    default_quality = "720p"
    print(f"Quality: {default_quality} (default)")
    return default_quality
    

def extract_episode_number(filename):    
    # Try Pattern 1
    match = re.search(pattern1, filename)
    if match:
        print("Matched Pattern 1")
        return match.group(2)  # Extracted episode number
    
    # Try Pattern 2
    match = re.search(pattern2, filename)
    if match:
        print("Matched Pattern 2")
        return match.group(2)  # Extracted episode number

    # Try Pattern 3
    match = re.search(pattern3, filename)
    if match:
        print("Matched Pattern 3")
        return match.group(1)  # Extracted episode number

    # Try Pattern 3_2
    match = re.search(pattern3_2, filename)
    if match:
        print("Matched Pattern 3_2")
        return match.group(1)  # Extracted episode number
        
    # Try Pattern 4
    match = re.search(pattern4, filename)
    if match:
        print("Matched Pattern 4")
        return match.group(2)  # Extracted episode number

    # Try Pattern X
    match = re.search(patternX, filename)
    if match:
        print("Matched Pattern X")
        return match.group(1)  # Extracted episode number
    
    # Try Pattern Y as last resort - any number in filename
    match = re.search(patternY, filename)
    if match:
        print("Matched Pattern Y (any number)")
        return match.group(1)
        
    # Return "01" as default if no number found
    print("No episode number found, using default: 01")
    return "01"

def determine_file_type(file_extension):
    """Determine if file should be treated as video, audio, or document based on extension"""
    video_extensions = [
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
        '.3gp', '.ts', '.mpg', '.mpeg', '.rm', '.rmvb', '.asf', '.divx',
        '.xvid', '.f4v', '.m2ts', '.mts', '.vob', '.ogv', '.mxf', '.qt'
    ]
    audio_extensions = [
        '.mp3', '.flac', '.wav', '.aac', '.ogg', '.wma', '.m4a', '.opus',
        '.ape', '.ac3', '.dts', '.amr', '.ra', '.au', '.aiff', '.caf'
    ]
    
    file_extension = file_extension.lower()
    
    if file_extension in video_extensions:
        return "video"
    elif file_extension in audio_extensions:
        return "audio"
    else:
        return "document"

def sequence_files(files):
    """Sequence files based on episode numbers extracted from filenames"""
    def get_sort_key(file_info):
        filename = file_info['original_filename']
        episode = extract_episode_number(filename)
        if episode:
            try:
                return int(episode)
            except:
                pass
        return float('inf')  # Put files without episode numbers at the end
    
    return sorted(files, key=get_sort_key)

# Handle /stop command for manual rename
@Client.on_message(filters.private & filters.command("stop"))
async def stop_manual_rename(client, message):
    user_id = message.from_user.id
    
    if user_id in user_manual_rename_state:
        # Clear the user's manual rename state
        del user_manual_rename_state[user_id]
        await message.reply_text("**Manual rename cancelled ❌**\n\nYou can now send files normally.")
    else:
        await message.reply_text("**No active manual rename session found.**")

# Handle text messages for manual rename
@Client.on_message(filters.private & filters.text & ~filters.command(["start", "settings", "tutorial", "stats", "broadcast", "restart", "stop", "autorename", "done"]))
async def handle_manual_rename_text(client, message):
    user_id = message.from_user.id
    
    # Check rename mode first
    rename_mode = await madflixbotz.get_rename_mode(user_id)
    if rename_mode == "Auto":
        return  # Don't process manual rename in auto mode
    
    # Check if user is in manual rename state
    if user_id in user_manual_rename_state:
        new_filename = message.text.strip()
        
        # Validate filename
        if not new_filename:
            return await message.reply_text("**Please provide a valid filename with extension.**")
        
        # Check if filename has extension
        if '.' not in new_filename:
            return await message.reply_text("**Please include file extension in the filename.**\n\nExample: `MyMovie.mkv`")
        
        # Store the new filename
        user_manual_rename_state[user_id]['new_filename'] = new_filename
        
        # Delete the user's filename message
        try:
            await message.delete()
        except:
            pass
        
        # Delete the instruction message
        try:
            if 'instruction_msg_id' in user_manual_rename_state[user_id]:
                await client.delete_messages(
                    user_id, 
                    user_manual_rename_state[user_id]['instruction_msg_id']
                )
        except:
            pass
        
        # Start renaming process
        await process_manual_rename(client, user_id)

# AUTO RENAME COMMAND
@Client.on_message(filters.private & filters.command("autorename"))
async def autorename_command(client, message):
    user_id = message.from_user.id
    
    if len(message.command) == 1:
        # Show current template
        current_template = await madflixbotz.get_format_template(user_id)
        await message.reply_text(
            f"**📝 Current Auto Rename Template:**\n\n"
            f"`{current_template or 'Not Set'}`\n\n"
            f"**💡 Usage:**\n"
            f"`/autorename Your Template Here`\n\n"
            f"**📋 Variables:**\n"
            f"• `episode` - Episode number\n"
            f"• `quality` - Video quality\n\n"
            f"**📌 Example:**\n"
            f"`/autorename Naruto Shippuden S02 - EPepisode - quality [Dual Audio] - @YourChannel`"
        )
        return
    
    # Set new template
    template = message.text.split(" ", 1)[1]
    await madflixbotz.set_format_template(user_id, template)
    await message.reply_text(
        f"**✅ Auto Rename Template Set Successfully!**\n\n"
        f"**Template:** `{template}`\n\n"
        f"**📝 Note:** Now send files and they will be collected for batch processing. Use /done when finished."
    )

# Main file handler - ENHANCED FOR BATCH PROCESSING
@Client.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def handle_file(client, message):
    user_id = message.from_user.id
    
    # Check if user has auto rename template set
    format_template = await madflixbotz.get_format_template(user_id)
    
    if format_template:
        # Auto rename mode - collect files for batch processing
        await handle_batch_collection(client, message, user_id)
    else:
        # Manual rename mode
        rename_mode = await madflixbotz.get_rename_mode(user_id)
        if rename_mode == "Auto":
            return
        await handle_manual_rename_file(client, message)

async def handle_batch_collection(client, message, user_id):
    """Handle file collection for batch processing"""
    
    # Get file information
    if message.document:
        file_info = {
            'type': 'document',
            'file_id': message.document.file_id,
            'original_filename': message.document.file_name or "document",
            'file_size': message.document.file_size,
            'message': message
        }
    elif message.video:
        file_info = {
            'type': 'video', 
            'file_id': message.video.file_id,
            'original_filename': message.video.file_name or "video.mp4",
            'file_size': message.video.file_size,
            'message': message
        }
    elif message.audio:
        file_info = {
            'type': 'audio',
            'file_id': message.audio.file_id, 
            'original_filename': message.audio.file_name or "audio.mp3",
            'file_size': message.audio.file_size,
            'message': message
        }
    else:
        return
    
    # Add to user's file queue
    user_file_queues[user_id].append(file_info)
    
    # Send or update collection message
    if user_id not in user_batch_states:
        # First file - send collection message
        collection_msg = await message.reply_text(
            "**Auto Rename Mode ✅**\n\n"
            "Please send your videos; they will be automatically sequenced. "
            "Once you have sent all videos, send the /done command.\n\n"
            "**Note:** Bot will not send message that file is added just send all your files & send /done command.\n\n"
            "**Do not delete your original files.**"
        )
        
        user_batch_states[user_id] = {
            'collection_msg': collection_msg,
            'file_count': 1
        }
    else:
        # Update file count
        user_batch_states[user_id]['file_count'] += 1
    
    print(f"File collected for user {user_id}: {file_info['original_filename']} (Total: {len(user_file_queues[user_id])})")

# /done command handler
@Client.on_message(filters.private & filters.command("done"))
async def done_command(client, message):
    user_id = message.from_user.id
    
    if user_id not in user_file_queues or not user_file_queues[user_id]:
        await message.reply_text("**No files found to process!**\n\nPlease send some files first.")
        return
    
    # Sequence files
    files = user_file_queues[user_id]
    sequenced_files = sequence_files(files)
    user_file_queues[user_id] = sequenced_files
    
    await message.reply_text("**Sequencing your files...**")
    
    # Show rename options menu
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Filename", callback_data="rename_option_filename")],
        [InlineKeyboardButton("Caption", callback_data="rename_option_caption")], 
        [InlineKeyboardButton("Default Filename", callback_data="rename_option_default_filename")],
        [InlineKeyboardButton("Default Caption", callback_data="rename_option_default_caption")]
    ])
    
    options_text = (
        "**『Auto Rename』**\n\n"
        "**Choose AutoRename Through!**\n\n"
        "**Filename:**\n"
        "• Extract Information from filename.\n\n"
        "**Caption:**\n"
        "• Extract Information from Caption.\n"
        "• Useful If your file Filename is present in caption.\n\n"
        "**Default Filename:**\n"
        "• Use your file Filename as a new filename.\n"
        "• Useful If you want to change only thumbnail or Remove/Replace Specific words from filename.\n\n"
        "**Default Caption:**\n"
        "• Use your Caption Filename as a new filename.\n"
        "• Useful If you want to change only thumbnail or Remove/Replace Specific words from filename."
    )
    
    await message.reply_text(options_text, reply_markup=keyboard)

# Callback handlers for rename options
@Client.on_callback_query(filters.regex("^rename_option_"))
async def handle_rename_option(client, callback_query):
    user_id = callback_query.from_user.id
    option = callback_query.data.replace("rename_option_", "")
    
    if user_id not in user_file_queues or not user_file_queues[user_id]:
        await callback_query.answer("No files found to process!", show_alert=True)
        return
    
    await callback_query.answer()
    
    if option == "filename":
        await process_files_with_template(client, callback_query.message, user_id)
    elif option == "caption":
        await callback_query.edit_message_text("**Caption option coming soon!**")
    elif option == "default_filename":
        await process_files_default_filename(client, callback_query.message, user_id)
    elif option == "default_caption":
        await callback_query.edit_message_text("**Default Caption option coming soon!**")

async def process_files_with_template(client, message, user_id):
    """Process files using auto rename template"""
    files = user_file_queues[user_id]
    format_template = await madflixbotz.get_format_template(user_id)
    
    # Create downloads directory if it doesn't exist
    os.makedirs("downloads", exist_ok=True)
    
    total_files = len(files)
    
    for i, file_info in enumerate(files, 1):
        try:
            # Generate new filename using template - ENHANCED VERSION
            original_filename = file_info['original_filename']
            episode_num = extract_episode_number(original_filename)
            quality = extract_quality(original_filename)

            new_filename = format_template

            # Replace episode number (if found)
            if episode_num and "episode" in new_filename:
                new_filename = new_filename.replace("episode", episode_num)
            elif "episode" in new_filename:
                # If no episode found but template has "episode", replace with "01"
                new_filename = new_filename.replace("episode", "01")

            # Replace quality (if found)
            if quality and "quality" in new_filename:
                new_filename = new_filename.replace("quality", quality)
            elif "quality" in new_filename:
                # If no quality found but template has "quality", replace with "720p"
                new_filename = new_filename.replace("quality", "720p")

            # Get file extension and ensure it's added
            _, ext = os.path.splitext(original_filename)
            if not new_filename.endswith(ext):
                new_filename += ext

            print(f"Original: {original_filename}")
            print(f"Template: {format_template}")
            print(f"Episode: {episode_num}")
            print(f"Quality: {quality}")
            print(f"New filename: {new_filename}")
            
            # Update progress message
            progress_msg = await message.edit_text(
                f"**Task Running: {i}**\n\n"
                f"**{i}.Downloading...**\n"
                f"**Progress:** 0.0%\n"
                f"**Processed:** 0.00B of {humanbytes(file_info['file_size'])}\n"
                f"**Speed:** 0.00B/s | **ETA:** -\n"
                f"**Elapsed:** 0s\n"
                f"**Upload:** Telegram\n"
                f"**/cancel** AgADMRoAAqLp"
            )
            
            # Download file (let pyrogram handle filename automatically)
            start_time = time.time()
            downloaded_file = await client.download_media(
                file_info['message'],
                progress=batch_progress_callback,
                progress_args=(progress_msg, f"**{i}.Downloading...**", file_info['file_size'], start_time)
            )
            
            # Upload with new filename
            await progress_msg.edit_text(
                f"**Task Running: {i}**\n\n"
                f"**{i}.Uploading...**\n"
                f"**Progress:** 0.0%\n"
                f"**Upload:** Telegram"
            )
            
            # Get thumbnail
            thumbnail = await madflixbotz.get_thumbnail(user_id)
            
            # Upload file
            start_time = time.time()
            if file_info['type'] == 'video':
                await client.send_video(
                    chat_id=user_id,
                    video=downloaded_file,
                    caption=f"**Renamed:** `{new_filename}`",
                    thumb=thumbnail,
                    progress=batch_progress_callback,
                    progress_args=(progress_msg, f"**{i}.Uploading...**", file_info['file_size'], start_time)
                )
            elif file_info['type'] == 'document':
                await client.send_document(
                    chat_id=user_id,
                    document=downloaded_file,
                    caption=f"**Renamed:** `{new_filename}`",
                    thumb=thumbnail,
                    progress=batch_progress_callback,
                    progress_args=(progress_msg, f"**{i}.Uploading...**", file_info['file_size'], start_time)
                )
            elif file_info['type'] == 'audio':
                await client.send_audio(
                    chat_id=user_id,
                    audio=downloaded_file,
                    caption=f"**Renamed:** `{new_filename}`",
                    thumb=thumbnail,
                    progress=batch_progress_callback,
                    progress_args=(progress_msg, f"**{i}.Uploading...**", file_info['file_size'], start_time)
                )
            
            # Clean up downloaded file
            try:
                os.remove(downloaded_file)
            except:
                pass
                
        except Exception as e:
            await client.send_message(user_id, f"**Error processing file {i}:** {str(e)}")
            print(f"Error processing file {i} for user {user_id}: {e}")
    
    # Clear user's queue and state
    user_file_queues[user_id].clear()
    if user_id in user_batch_states:
        del user_batch_states[user_id]
    
    await message.edit_text(f"**✅ All {total_files} files processed successfully!**")

async def process_files_default_filename(client, message, user_id):
    """Process files with default filenames (no template)"""
    files = user_file_queues[user_id]
    
    # Create downloads directory if it doesn't exist
    os.makedirs("downloads", exist_ok=True)
    
    total_files = len(files)
    
    for i, file_info in enumerate(files, 1):
        try:
            # Use original filename
            new_filename = file_info['original_filename']
            
            # Update progress message
            progress_msg = await message.edit_text(
                f"**Task Running: {i}**\n\n"
                f"**{i}.Downloading...**\n"
                f"**Progress:** 0.0%"
            )
            
            # Download file (let pyrogram handle filename automatically)
            start_time = time.time()
            downloaded_file = await client.download_media(
                file_info['message'],
                progress=batch_progress_callback,
                progress_args=(progress_msg, f"**{i}.Downloading...**", file_info['file_size'], start_time)
            )
            
            # Upload with original filename
            await progress_msg.edit_text(
                f"**Task Running: {i}**\n\n"
                f"**{i}.Uploading...**"
            )
            
            # Get thumbnail
            thumbnail = await madflixbotz.get_thumbnail(user_id)
            
            # Upload file
            start_time = time.time()
            if file_info['type'] == 'video':
                await client.send_video(
                    chat_id=user_id,
                    video=downloaded_file,
                    caption=f"**File:** `{new_filename}`",
                    thumb=thumbnail,
                    progress=batch_progress_callback,
                    progress_args=(progress_msg, f"**{i}.Uploading...**", file_info['file_size'], start_time)
                )
            elif file_info['type'] == 'document':
                await client.send_document(
                    chat_id=user_id,
                    document=downloaded_file,
                    caption=f"**File:** `{new_filename}`",
                    thumb=thumbnail,
                    progress=batch_progress_callback,
                    progress_args=(progress_msg, f"**{i}.Uploading...**", file_info['file_size'], start_time)
                )
            elif file_info['type'] == 'audio':
                await client.send_audio(
                    chat_id=user_id,
                    audio=downloaded_file,
                    caption=f"**File:** `{new_filename}`",
                    thumb=thumbnail,
                    progress=batch_progress_callback,
                    progress_args=(progress_msg, f"**{i}.Uploading...**", file_info['file_size'], start_time)
                )
            
            # Clean up
            try:
                os.remove(downloaded_file)
            except:
                pass
                
        except Exception as e:
            await client.send_message(user_id, f"**Error processing file {i}:** {str(e)}")
    
    # Clear queue
    user_file_queues[user_id].clear()
    if user_id in user_batch_states:
        del user_batch_states[user_id]
    
    await message.edit_text(f"**✅ All {total_files} files processed successfully!**")

async def batch_progress_callback(current, total, message, status, file_size, start_time):
    """Progress callback for batch download/upload"""
    try:
        now = time.time()
        diff = now - start_time
        if round(diff % 5.00) == 0 or current == total:
            percentage = current * 100 / total
            speed = current / diff if diff > 0 else 0
            elapsed_time = round(diff) * 1000
            time_to_completion = round((total - current) / speed) * 1000 if speed > 0 else 0
            estimated_total_time = elapsed_time + time_to_completion

            elapsed_time_str = convert(diff)
            estimated_time_str = convert(time_to_completion / 1000) if time_to_completion > 0 else "0s"

            await message.edit_text(
                f"{status}\n"
                f"**Progress:** {percentage:.1f}%\n"
                f"**Processed:** {humanbytes(current)} of {humanbytes(total)}\n"
                f"**Speed:** {humanbytes(speed)}/s | **ETA:** {estimated_time_str}\n"
                f"**Elapsed:** {elapsed_time_str}\n"
                f"**Upload:** Telegram"
            )
    except:
        pass

async def handle_manual_rename_file(client, message):
    """Handle manual rename file"""
    user_id = message.from_user.id
    
    # Store file message for manual rename
    user_manual_rename_state[user_id] = {
        'file_message': message,
        'new_filename': None
    }
    
    # Get original filename
    if message.document:
        original_filename = message.document.file_name or "document"
    elif message.video:
        original_filename = message.video.file_name or "video.mp4"
    elif message.audio:
        original_filename = message.audio.file_name or "audio.mp3"
    else:
        original_filename = "file"
    
    instruction_msg = await message.reply_text(
        f"**📝 Manual Rename Mode**\n\n"
        f"**Original:** `{original_filename}`\n\n"
        f"**💡 Send new filename with extension**\n"
        f"**Example:** `MyMovie.mkv`\n\n"
        f"**⚠️ Use /stop to cancel**"
    )
    
    # Store instruction message ID for deletion
    user_manual_rename_state[user_id]['instruction_msg_id'] = instruction_msg.id

async def process_manual_rename(client, user_id):
    """Process manual rename"""
    if user_id not in user_manual_rename_state:
        return
    
    file_message = user_manual_rename_state[user_id]['file_message']
    new_filename = user_manual_rename_state[user_id]['new_filename']
    
    # Clear the state
    del user_manual_rename_state[user_id]
    
    # Start rename process
    await start_rename_process(client, file_message, new_filename, user_id)

async def start_rename_process(client, file_message, new_filename, user_id):
    """Start the rename process"""
    try:
        # Create downloads directory if it doesn't exist
        os.makedirs("downloads", exist_ok=True)
        
        # Get file info
        if file_message.document:
            file_id = file_message.document.file_id
            file_size = file_message.document.file_size
            file_type = "document"
            original_filename = file_message.document.file_name or "document"
        elif file_message.video:
            file_id = file_message.video.file_id
            file_size = file_message.video.file_size
            file_type = "video"
            original_filename = file_message.video.file_name or "video.mp4"
        elif file_message.audio:
            file_id = file_message.audio.file_id
            file_size = file_message.audio.file_size
            file_type = "audio"
            original_filename = file_message.audio.file_name or "audio.mp3"
        else:
            return
        
        # Create progress message
        progress_msg = await file_message.reply_text(
            "**🔄 Processing File...**\n\n"
            "**📥 Downloading:** 0%\n"
            "**📤 Uploading:** Waiting..."
        )
        
        # Download the file (let pyrogram handle filename automatically)
        start_time = time.time()
        downloaded_file = await client.download_media(
            file_message,
            progress=progress_for_pyrogram,
            progress_args=("**📥 Downloading File...**", progress_msg, start_time)
        )
        
        # Get user preferences
        thumbnail = await madflixbotz.get_thumbnail(user_id)
        caption = await madflixbotz.get_caption(user_id)
        
        # Prepare caption
        if caption:
            caption = caption.format(filename=new_filename, filesize=humanbytes(file_size))
        else:
            caption = f"**📁 File:** `{new_filename}`"
        
        # Update progress
        await progress_msg.edit_text("**📤 Uploading File...**")
        
        # Upload the file
        start_time = time.time()
        if file_type == "video":
            await client.send_video(
                chat_id=user_id,
                video=downloaded_file,
                caption=caption,
                thumb=thumbnail,
                progress=progress_for_pyrogram,
                progress_args=("**📤 Uploading File...**", progress_msg, start_time)
            )
        elif file_type == "document":
            await client.send_document(
                chat_id=user_id,
                document=downloaded_file,
                caption=caption,
                thumb=thumbnail,
                progress=progress_for_pyrogram,
                progress_args=("**📤 Uploading File...**", progress_msg, start_time)
            )
        elif file_type == "audio":
            await client.send_audio(
                chat_id=user_id,
                audio=downloaded_file,
                caption=caption,
                thumb=thumbnail,
                progress=progress_for_pyrogram,
                progress_args=("**📤 Uploading File...**", progress_msg, start_time)
            )
        
        # Clean up
        try:
            os.remove(downloaded_file)
        except:
            pass
        
        # Delete progress message
        try:
            await progress_msg.delete()
        except:
            pass
        
        # Send success message
        await client.send_message(user_id, f"**✅ File renamed successfully!**\n\n**New name:** `{new_filename}`")
        
    except Exception as e:
        await client.send_message(user_id, f"**❌ Error renaming file:** {str(e)}")
        print(f"Error renaming file for user {user_id}: {e}")


# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Developer @JishuDeveloper
