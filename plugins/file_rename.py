from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaDocument, Message 
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

    # Return "Unknown" if no pattern matches
    unknown_quality = "Unknown"
    print(f"Quality: {unknown_quality}")
    return unknown_quality
    

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
        
    # Return None if no pattern matches
    return None

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
@Client.on_message(filters.private & filters.text & ~filters.command(["start", "settings", "tutorial", "stats", "broadcast", "restart", "stop"]))
async def handle_manual_rename_text(client, message):
    user_id = message.from_user.id
    
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

async def process_manual_rename(client, user_id):
    """Process the manual rename operation"""
    if user_id not in user_manual_rename_state:
        return
    
    state = user_manual_rename_state[user_id]
    file_message = state['file_message']
    new_filename = state['new_filename']
    
    # Clear the state
    del user_manual_rename_state[user_id]
    
    # Get user settings
    send_as_document = await madflixbotz.get_send_as_document(user_id)
    upload_destination = await madflixbotz.get_upload_destination(user_id)
    prefix = await madflixbotz.get_prefix(user_id)
    suffix = await madflixbotz.get_suffix(user_id)
    
    # Extract file information
    if file_message.document:
        file_id = file_message.document.file_id
        file_size = file_message.document.file_size
    elif file_message.video:
        file_id = file_message.video.file_id
        file_size = file_message.video.file_size
    elif file_message.audio:
        file_id = file_message.audio.file_id
        file_size = file_message.audio.file_size
    else:
        return
    
    # Apply prefix and suffix
    base_name, file_extension = os.path.splitext(new_filename)
    
    if prefix:
        base_name = f"{prefix} {base_name}"
    
    if suffix:
        base_name = f"{base_name} {suffix}"
    
    final_filename = f"{base_name}{file_extension}"
    file_path = f"downloads/{final_filename}"
    
    # Check if already being renamed
    if file_id in renaming_operations:
        elapsed_time = (datetime.now() - renaming_operations[file_id]).seconds
        if elapsed_time < 10:
            return
    
    # Mark as being renamed
    renaming_operations[file_id] = datetime.now()
    
    download_msg = await client.send_message(user_id, "**Trying To Download.....**")
    
    try:
        path = await client.download_media(
            message=file_message, 
            file_name=file_path, 
            progress=progress_for_pyrogram, 
            progress_args=("Download Started....", download_msg, time.time())
        )
    except Exception as e:
        del renaming_operations[file_id]
        return await download_msg.edit(str(e))

    # Get duration for video files
    duration = 0
    try:
        metadata = extractMetadata(createParser(file_path))
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
    except Exception as e:
        print(f"Error getting duration: {e}")

    upload_msg = await download_msg.edit("**Trying To Upload.....**")
    
    # Get caption and thumbnail
    c_caption = await madflixbotz.get_caption(user_id)
    c_thumb = await madflixbotz.get_thumbnail(user_id)
    
    caption = c_caption.format(
        filename=final_filename, 
        filesize=humanbytes(file_size), 
        duration=convert(duration)
    ) if c_caption else f"**{final_filename}**"
    
    ph_path = None
    if c_thumb:
        ph_path = await client.download_media(c_thumb)
        print(f"Thumbnail downloaded successfully. Path: {ph_path}")
    elif file_message.video and file_message.video.thumbs:
        ph_path = await client.download_media(file_message.video.thumbs[0].file_id)

    if ph_path:
        try:
            Image.open(ph_path).convert("RGB").save(ph_path)
            img = Image.open(ph_path)
            img.resize((320, 320))
            img.save(ph_path, "JPEG")
        except Exception as e:
            print(f"Error processing thumbnail: {e}")
    
    upload_chat_id = upload_destination if upload_destination else user_id
    
    try:
        if send_as_document:
            print("Upload Mode: DOCUMENT - Uploading as DOCUMENT")
            await client.send_document(
                upload_chat_id,
                document=path,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("Upload Started....", upload_msg, time.time())
            )
        else:
            file_type = determine_file_type(file_extension)
            
            if file_type == "video":
                print("Upload Mode: MEDIA - Uploading as VIDEO")
                await client.send_video(
                    upload_chat_id,
                    video=path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload Started....", upload_msg, time.time())
                )
            elif file_type == "audio":
                print("Upload Mode: MEDIA - Uploading as AUDIO")
                await client.send_audio(
                    upload_chat_id,
                    audio=path,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload Started....", upload_msg, time.time())
                )
            else:
                print("Upload Mode: MEDIA - Uploading as DOCUMENT (non-media file)")
                await client.send_document(
                    upload_chat_id,
                    document=path,
                    thumb=ph_path,
                    caption=caption,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload Started....", upload_msg, time.time())
                )
        
        await upload_msg.edit("**Successfully Renamed ✅**")
        
    except Exception as e:
        await upload_msg.edit(f"**Error during upload:** {str(e)}")
    
    finally:
        # Cleanup
        try:
            os.remove(path)
            if ph_path:
                os.remove(ph_path)
        except:
            pass
        
        if file_id in renaming_operations:
            del renaming_operations[file_id]

# Modified file handler for manual rename mode
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_files(client, message):
    user_id = message.from_user.id
    
    # Check rename mode
    rename_mode = await madflixbotz.get_rename_mode(user_id)
    
    if rename_mode == "Manual":
        # Store file message and ask for new name
        instruction_msg = await message.reply_text(
            "**Manual Rename Mode ✅**\n\n"
            "**Send New file name with extension.**\n\n"
            "To cancel send /stop\n\n"
            "**Note: Don't delete your original file.**"
        )
        
        user_manual_rename_state[user_id] = {
            'file_message': message,
            'instruction_msg_id': instruction_msg.id
        }
    else:
        # Handle auto rename mode
        await auto_rename_files(client, message)

# Auto rename function for when format template is set
async def auto_rename_files(client, message):
    user_id = message.from_user.id
    firstname = message.from_user.first_name
    format_template = await madflixbotz.get_format_template(user_id)
    send_as_document = await madflixbotz.get_send_as_document(user_id)
    upload_destination = await madflixbotz.get_upload_destination(user_id)
    
    # Get prefix and suffix from database
    prefix = await madflixbotz.get_prefix(user_id)
    suffix = await madflixbotz.get_suffix(user_id)

    if not format_template:
        return await message.reply_text("**Please Set An Auto Rename Format First Using Auto Rename Mode in Settings**")

    # Extract information from the incoming file name and get file size
    file_size = 0
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_size = message.document.file_size
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name if message.video.file_name else "video.mp4"
        file_size = message.video.file_size
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name if message.audio.file_name else "audio.mp3"
        file_size = message.audio.file_size
    else:
        return await message.reply_text("Unsupported File Type")

    print(f"Original File Name: {file_name}")
    print(f"Send as document setting: {send_as_document}")
    print(f"File size: {humanbytes(file_size)}")
    print(f"Prefix: {prefix}")
    print(f"Suffix: {suffix}")
    
    # Check whether the file is already being renamed or has been renamed recently
    if file_id in renaming_operations:
        elapsed_time = (datetime.now() - renaming_operations[file_id]).seconds
        if elapsed_time < 10:
            print("File is being ignored as it is currently being renamed or was renamed recently.")
            return  # Exit the handler if the file is being ignored

    # Mark the file as currently being renamed
    renaming_operations[file_id] = datetime.now()

    # Extract episode number and qualities
    episode_number = extract_episode_number(file_name)
    
    print(f"Extracted Episode Number: {episode_number}")
    
    if episode_number:
        placeholders = ["episode", "Episode", "EPISODE", "{episode}"]
        for placeholder in placeholders:
            format_template = format_template.replace(placeholder, str(episode_number), 1)
            
        # Add extracted qualities to the format template
        quality_placeholders = ["quality", "Quality", "QUALITY", "{quality}"]
        for quality_placeholder in quality_placeholders:
            if quality_placeholder in format_template:
                extracted_qualities = extract_quality(file_name)
                if extracted_qualities == "Unknown":
                    await message.reply_text("I Was Not Able To Extract The Quality Properly. Renaming As 'Unknown'...")
                    # Mark the file as ignored
                    del renaming_operations[file_id]
                    return  # Exit the handler if quality extraction fails
                
                format_template = format_template.replace(quality_placeholder, "".join(extracted_qualities))           
            
        _, file_extension = os.path.splitext(file_name)
        new_file_name = f"{format_template}{file_extension}"
        
        # Apply prefix if set
        if prefix:
            base_name = os.path.splitext(new_file_name)[0]
            new_file_name = f"{prefix} {base_name}{file_extension}"
        
        # Apply suffix if set
        if suffix:
            base_name = os.path.splitext(new_file_name)[0]
            new_file_name = f"{base_name} {suffix}{file_extension}"
        
        file_path = f"downloads/{new_file_name}"
        file = message

        download_msg = await message.reply_text(text="Trying To Download.....")
        try:
            path = await client.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram, progress_args=("Download Started....", download_msg, time.time()))
        except Exception as e:
            # Mark the file as ignored
            del renaming_operations[file_id]
            return await download_msg.edit(str(e))     

        duration = 0
        try:
            metadata = extractMetadata(createParser(file_path))
            if metadata.has("duration"):
                duration = metadata.get('duration').seconds
        except Exception as e:
            print(f"Error getting duration: {e}")

        upload_msg = await download_msg.edit("Trying To Uploading.....")
        ph_path = None
        c_caption = await madflixbotz.get_caption(message.chat.id)
        c_thumb = await madflixbotz.get_thumbnail(message.chat.id)

        # Create caption with correct file size
        caption = c_caption.format(filename=new_file_name, filesize=humanbytes(file_size), duration=convert(duration)) if c_caption else f"**{new_file_name}**"

        if c_thumb:
            ph_path = await client.download_media(c_thumb)
            print(f"Thumbnail downloaded successfully. Path: {ph_path}")
        elif message.video and message.video.thumbs:
            ph_path = await client.download_media(message.video.thumbs[0].file_id)

        if ph_path:
            try:
                Image.open(ph_path).convert("RGB").save(ph_path)
                img = Image.open(ph_path)
                img.resize((320, 320))
                img.save(ph_path, "JPEG")
            except Exception as e:
                print(f"Error processing thumbnail: {e}")
        
        # Determine upload destination
        upload_chat_id = upload_destination if upload_destination else message.chat.id

        try:
            # Check send_as_document setting
            if send_as_document:
                # User wants everything sent as DOCUMENT
                print("Upload Mode: DOCUMENT - Uploading as DOCUMENT")
                await client.send_document(
                    upload_chat_id,
                    document=file_path,
                    thumb=ph_path,
                    caption=caption,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload Started....", upload_msg, time.time())
                )
            else:
                # User wants intelligent upload based on file type
                file_type = determine_file_type(file_extension)
                
                if file_type == "video":
                    print("Upload Mode: MEDIA - Uploading as VIDEO")
                    await client.send_video(
                        upload_chat_id,
                        video=file_path,
                        caption=caption,
                        thumb=ph_path,
                        duration=duration,
                        progress=progress_for_pyrogram,
                        progress_args=("Upload Started....", upload_msg, time.time())
                    )
                elif file_type == "audio":
                    print("Upload Mode: MEDIA - Uploading as AUDIO")
                    await client.send_audio(
                        upload_chat_id,
                        audio=file_path,
                        caption=caption,
                        thumb=ph_path,
                        duration=duration,
                        progress=progress_for_pyrogram,
                        progress_args=("Upload Started....", upload_msg, time.time())
                    )
                else:
                    print("Upload Mode: MEDIA - Uploading as DOCUMENT (non-media file)")
                    await client.send_document(
                        upload_chat_id,
                        document=file_path,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("Upload Started....", upload_msg, time.time())
                    )

            await upload_msg.edit("**Successfully Renamed ✅**")

        except FloodWait as f:
            await asyncio.sleep(f.value)  
            # Retry after flood wait

        except Exception as e:
            # Mark the file as ignored
            del renaming_operations[file_id]
            return await upload_msg.edit(f"Error: {e}")

        finally:
            # Cleanup downloaded files
            try:
                os.remove(file_path)
                if ph_path:
                    os.remove(ph_path)
            except:
                pass

            # Mark the file as no longer being renamed
            if file_id in renaming_operations:
                del renaming_operations[file_id]
    
    else:
        # Mark the file as ignored if no episode number is found
        del renaming_operations[file_id]
        await message.reply_text("❌ **Episode Number Not Found!**\n\nI couldn't extract episode number from the filename. Please make sure your file has episode number in the format like E01, EP01, S01E01, etc.")


# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Developer @JishuDeveloper
