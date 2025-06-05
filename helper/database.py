import motor.motor_asyncio
from config import Config
from .utils import send_log

class Database:

    def __init__(self, uri, database_name):
        if not uri or uri == "":
            print("Warning: No database URL provided. Using in-memory storage.")
            self._client = None
            self.madflixbotz = None
            self.col = None
            self.use_memory = True
            self.memory_store = {}
        else:
            try:
                self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
                self.madflixbotz = self._client[database_name]
                self.col = self.madflixbotz.user
                self.use_memory = False
                self.memory_store = {}
                print("Database connected successfully!")
            except Exception as e:
                print(f"Database connection failed: {e}")
                print("Falling back to in-memory storage.")
                self._client = None
                self.madflixbotz = None
                self.col = None
                self.use_memory = True
                self.memory_store = {}

    async def test_connection(self):
        """Test database connection"""
        if self.use_memory:
            return True
        try:
            await self._client.admin.command('ping')
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False

    def new_user(self, id):
        return dict(
            _id=int(id),                                   
            file_id=None,
            caption=None,
            format_template=None,
            upload_mode='Telegram',
            send_as_document=False,
            upload_destination=None,
            media_type=None,
            prefix=None,
            suffix=None,
            rename_mode='Manual'
        )

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            if self.use_memory:
                self.memory_store[u.id] = user
                print(f"User {u.id} added to memory storage")
            else:
                try:
                    await self.col.insert_one(user)
                    print(f"User {u.id} added to database")
                except Exception as e:
                    print(f"Error adding user to database: {e}")
                    # Fallback to memory
                    self.memory_store[u.id] = user
            await send_log(b, u)

    async def is_user_exist(self, id):
        if self.use_memory:
            return int(id) in self.memory_store
        else:
            try:
                user = await self.col.find_one({'_id': int(id)})
                return bool(user)
            except:
                return int(id) in self.memory_store

    async def total_users_count(self):
        if self.use_memory:
            return len(self.memory_store)
        else:
            try:
                count = await self.col.count_documents({})
                return count
            except:
                return len(self.memory_store)

    async def get_all_users(self):
        if self.use_memory:
            class MemoryUsersGenerator:
                def __init__(self, users):
                    self.users = list(users.values())
                    self.index = 0
                
                def __aiter__(self):
                    return self
                
                async def __anext__(self):
                    if self.index >= len(self.users):
                        raise StopAsyncIteration
                    user = self.users[self.index]
                    self.index += 1
                    return user
            
            return MemoryUsersGenerator(self.memory_store)
        else:
            try:
                all_users = self.col.find({})
                return all_users
            except:
                return MemoryUsersGenerator(self.memory_store)

    async def delete_user(self, user_id):
        if self.use_memory:
            if int(user_id) in self.memory_store:
                del self.memory_store[int(user_id)]
        else:
            try:
                await self.col.delete_many({'_id': int(user_id)})
            except:
                if int(user_id) in self.memory_store:
                    del self.memory_store[int(user_id)]
    
    async def set_thumbnail(self, id, file_id):
        if self.use_memory:
            user_id = int(id)
            if user_id not in self.memory_store:
                self.memory_store[user_id] = self.new_user(user_id)
            self.memory_store[user_id]['file_id'] = file_id
        else:
            try:
                await self.col.update_one({'_id': int(id)}, {'$set': {'file_id': file_id}})
            except:
                user_id = int(id)
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = self.new_user(user_id)
                self.memory_store[user_id]['file_id'] = file_id

    async def get_thumbnail(self, id):
        if self.use_memory:
            user = self.memory_store.get(int(id))
            return user.get('file_id', None) if user else None
        else:
            try:
                user = await self.col.find_one({'_id': int(id)})
                return user.get('file_id', None) if user else None
            except:
                user = self.memory_store.get(int(id))
                return user.get('file_id', None) if user else None

    async def set_caption(self, id, caption):
        if self.use_memory:
            user_id = int(id)
            if user_id not in self.memory_store:
                self.memory_store[user_id] = self.new_user(user_id)
            self.memory_store[user_id]['caption'] = caption
        else:
            try:
                await self.col.update_one({'_id': int(id)}, {'$set': {'caption': caption}})
            except:
                user_id = int(id)
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = self.new_user(user_id)
                self.memory_store[user_id]['caption'] = caption

    async def get_caption(self, id):
        if self.use_memory:
            user = self.memory_store.get(int(id))
            return user.get('caption', None) if user else None
        else:
            try:
                user = await self.col.find_one({'_id': int(id)})
                return user.get('caption', None) if user else None
            except:
                user = self.memory_store.get(int(id))
                return user.get('caption', None) if user else None

    async def set_format_template(self, id, format_template):
        if self.use_memory:
            user_id = int(id)
            if user_id not in self.memory_store:
                self.memory_store[user_id] = self.new_user(user_id)
            self.memory_store[user_id]['format_template'] = format_template
        else:
            try:
                await self.col.update_one({'_id': int(id)}, {'$set': {'format_template': format_template}})
            except:
                user_id = int(id)
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = self.new_user(user_id)
                self.memory_store[user_id]['format_template'] = format_template

    async def get_format_template(self, id):
        if self.use_memory:
            user = self.memory_store.get(int(id))
            return user.get('format_template', None) if user else None
        else:
            try:
                user = await self.col.find_one({'_id': int(id)})
                return user.get('format_template', None) if user else None
            except:
                user = self.memory_store.get(int(id))
                return user.get('format_template', None) if user else None

    async def set_prefix(self, id, prefix):
        if self.use_memory:
            user_id = int(id)
            if user_id not in self.memory_store:
                self.memory_store[user_id] = self.new_user(user_id)
            self.memory_store[user_id]['prefix'] = prefix
        else:
            try:
                await self.col.update_one({'_id': int(id)}, {'$set': {'prefix': prefix}})
            except:
                user_id = int(id)
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = self.new_user(user_id)
                self.memory_store[user_id]['prefix'] = prefix

    async def get_prefix(self, id):
        if self.use_memory:
            user = self.memory_store.get(int(id))
            return user.get('prefix', None) if user else None
        else:
            try:
                user = await self.col.find_one({'_id': int(id)})
                return user.get('prefix', None) if user else None
            except:
                user = self.memory_store.get(int(id))
                return user.get('prefix', None) if user else None

    async def set_suffix(self, id, suffix):
        if self.use_memory:
            user_id = int(id)
            if user_id not in self.memory_store:
                self.memory_store[user_id] = self.new_user(user_id)
            self.memory_store[user_id]['suffix'] = suffix
        else:
            try:
                await self.col.update_one({'_id': int(id)}, {'$set': {'suffix': suffix}})
            except:
                user_id = int(id)
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = self.new_user(user_id)
                self.memory_store[user_id]['suffix'] = suffix

    async def get_suffix(self, id):
        if self.use_memory:
            user = self.memory_store.get(int(id))
            return user.get('suffix', None) if user else None
        else:
            try:
                user = await self.col.find_one({'_id': int(id)})
                return user.get('suffix', None) if user else None
            except:
                user = self.memory_store.get(int(id))
                return user.get('suffix', None) if user else None
        
    async def set_media_preference(self, id, media_type):
        if self.use_memory:
            user_id = int(id)
            if user_id not in self.memory_store:
                self.memory_store[user_id] = self.new_user(user_id)
            self.memory_store[user_id]['media_type'] = media_type
        else:
            try:
                await self.col.update_one({'_id': int(id)}, {'$set': {'media_type': media_type}})
            except:
                user_id = int(id)
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = self.new_user(user_id)
                self.memory_store[user_id]['media_type'] = media_type
        
    async def get_media_preference(self, id):
        if self.use_memory:
            user = self.memory_store.get(int(id))
            return user.get('media_type', None) if user else None
        else:
            try:
                user = await self.col.find_one({'_id': int(id)})
                return user.get('media_type', None) if user else None
            except:
                user = self.memory_store.get(int(id))
                return user.get('media_type', None) if user else None

    async def set_upload_mode(self, id, upload_mode):
        if self.use_memory:
            user_id = int(id)
            if user_id not in self.memory_store:
                self.memory_store[user_id] = self.new_user(user_id)
            self.memory_store[user_id]['upload_mode'] = upload_mode
        else:
            try:
                await self.col.update_one({'_id': int(id)}, {'$set': {'upload_mode': upload_mode}})
            except:
                user_id = int(id)
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = self.new_user(user_id)
                self.memory_store[user_id]['upload_mode'] = upload_mode

    async def get_upload_mode(self, id):
        if self.use_memory:
            user = self.memory_store.get(int(id))
            return user.get('upload_mode', 'Telegram') if user else 'Telegram'
        else:
            try:
                user = await self.col.find_one({'_id': int(id)})
                return user.get('upload_mode', 'Telegram') if user else 'Telegram'
            except:
                user = self.memory_store.get(int(id))
                return user.get('upload_mode', 'Telegram') if user else 'Telegram'

    async def set_send_as_document(self, id, send_as_document):
        if self.use_memory:
            user_id = int(id)
            if user_id not in self.memory_store:
                self.memory_store[user_id] = self.new_user(user_id)
            self.memory_store[user_id]['send_as_document'] = send_as_document
        else:
            try:
                await self.col.update_one({'_id': int(id)}, {'$set': {'send_as_document': send_as_document}})
            except:
                user_id = int(id)
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = self.new_user(user_id)
                self.memory_store[user_id]['send_as_document'] = send_as_document

    async def get_send_as_document(self, id):
        if self.use_memory:
            user = self.memory_store.get(int(id))
            return user.get('send_as_document', False) if user else False
        else:
            try:
                user = await self.col.find_one({'_id': int(id)})
                return user.get('send_as_document', False) if user else False
            except:
                user = self.memory_store.get(int(id))
                return user.get('send_as_document', False) if user else False

    async def set_upload_destination(self, id, upload_destination):
        if self.use_memory:
            user_id = int(id)
            if user_id not in self.memory_store:
                self.memory_store[user_id] = self.new_user(user_id)
            self.memory_store[user_id]['upload_destination'] = upload_destination
        else:
            try:
                await self.col.update_one({'_id': int(id)}, {'$set': {'upload_destination': upload_destination}})
            except:
                user_id = int(id)
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = self.new_user(user_id)
                self.memory_store[user_id]['upload_destination'] = upload_destination

    async def get_upload_destination(self, id):
        if self.use_memory:
            user = self.memory_store.get(int(id))
            return user.get('upload_destination', None) if user else None
        else:
            try:
                user = await self.col.find_one({'_id': int(id)})
                return user.get('upload_destination', None) if user else None
            except:
                user = self.memory_store.get(int(id))
                return user.get('upload_destination', None) if user else None

    async def set_rename_mode(self, id, rename_mode):
        if self.use_memory:
            user_id = int(id)
            if user_id not in self.memory_store:
                self.memory_store[user_id] = self.new_user(user_id)
            self.memory_store[user_id]['rename_mode'] = rename_mode
        else:
            try:
                await self.col.update_one({'_id': int(id)}, {'$set': {'rename_mode': rename_mode}})
            except:
                user_id = int(id)
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = self.new_user(user_id)
                self.memory_store[user_id]['rename_mode'] = rename_mode

    async def get_rename_mode(self, id):
        if self.use_memory:
            user = self.memory_store.get(int(id))
            return user.get('rename_mode', 'Manual') if user else 'Manual'
        else:
            try:
                user = await self.col.find_one({'_id': int(id)})
                return user.get('rename_mode', 'Manual') if user else 'Manual'
            except:
                user = self.memory_store.get(int(id))
                return user.get('rename_mode', 'Manual') if user else 'Manual'


# Initialize database instance
madflixbotz = Database(Config.DB_URL, Config.DB_NAME)


# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Developer @JishuDeveloper
