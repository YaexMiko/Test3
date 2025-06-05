from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
from aiohttp import web
from route import web_server
from helper.database import madflixbotz
import pyrogram.utils
import asyncio

pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -1009999999999

class Bot(Client):

    def __init__(self):
        super().__init__(
            name="renamer",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=15,
        )

    async def start(self):
        try:
            await super().start()
            me = await self.get_me()
            self.mention = me.mention
            self.username = me.username  
            self.uptime = Config.BOT_UPTIME
            
            print("=" * 50)
            print(f"🤖 Bot Started Successfully!")
            print(f"📛 Name: {me.first_name}")
            print(f"🆔 Username: @{me.username}")
            print(f"🔢 ID: {me.id}")
            
            # Test database connection
            db_status = await madflixbotz.test_connection()
            db_type = "MongoDB" if not madflixbotz.use_memory else "Memory"
            print(f"🗄️ Database: {db_type} ({'✅ Connected' if db_status else '❌ Failed'})")
            
            # Start web server if webhook is enabled
            if Config.WEBHOOK:
                try:
                    app = web.AppRunner(await web_server())
                    await app.setup()       
                    await web.TCPSite(app, "0.0.0.0", 8089).start()
                    print("🌐 Webhook Server: ✅ Started on port 8089")
                except Exception as e:
                    print(f"🌐 Webhook Server: ❌ Failed - {e}")
            
            print("=" * 50)
            
            # Send startup message to admins and log channel
            startup_msg = f"**🤖 {me.first_name} Started Successfully!**\n\n"
            startup_msg += f"📛 **Name:** {me.first_name}\n"
            startup_msg += f"🆔 **Username:** @{me.username}\n"
            startup_msg += f"🔢 **ID:** `{me.id}`\n"
            startup_msg += f"🗄️ **Database:** {db_type}\n"
            startup_msg += f"🌐 **Webhook:** {'Enabled' if Config.WEBHOOK else 'Disabled'}\n\n"
            startup_msg += f"📅 **Date:** `{datetime.now(timezone('Asia/Kolkata')).strftime('%d %B, %Y')}`\n"
            startup_msg += f"⏰ **Time:** `{datetime.now(timezone('Asia/Kolkata')).strftime('%I:%M:%S %p')}`\n"
            startup_msg += f"🉐 **Version:** `v{__version__} (Layer {layer})`"
            
            # Send to log channel
            if Config.LOG_CHANNEL:
                try:
                    await self.send_message(Config.LOG_CHANNEL, startup_msg)
                    print(f"📢 Startup message sent to log channel")
                except Exception as e:
                    print(f"📢 Failed to send to log channel: {e}")
            
            # Send to admins
            for admin_id in Config.ADMIN:
                try:
                    await self.send_message(admin_id, startup_msg)
                    print(f"👤 Startup message sent to admin: {admin_id}")
                except Exception as e:
                    print(f"👤 Failed to send to admin {admin_id}: {e}")
            
            print("🎉 Bot is now ready to handle messages!")
            
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            raise e

    async def stop(self):
        try:
            await super().stop()
            print("🛑 Bot stopped successfully!")
        except Exception as e:
            print(f"❌ Error stopping bot: {e}")

def main():
    """Main function to run the bot"""
    try:
        print("🚀 Starting Auto Rename Bot...")
        print("=" * 50)
        
        # Validate config
        if not Config.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        if not Config.API_ID:
            raise ValueError("API_ID is required")
        if not Config.API_HASH:
            raise ValueError("API_HASH is required")
            
        print("✅ Configuration validated")
        
        # Create and run bot
        bot = Bot()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        raise e

if __name__ == "__main__":
    main()


# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Developer @JishuDeveloper
