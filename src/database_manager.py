import sqlite3
import asyncio
import random

#tables:
#commands (command_name, output, author)
#play_requests (game text UNIQUE, time text, yes text, no text, requestor text)
#braincell_points (name text UNIQUE, points integer)
#calendar (event_name text, year integer, month integer, day integer, time text, gang text)
#emojis (emoji text UNIQUE)
#counters (counter text UNIQUE, count integer)
#casino (outcome string UNIQUE, bets string)
#music (userid text, song text, liked integer (0 or 1))
#nfts (id integer UNIQUE, url text, userid text, price integer)
#gangs (id integer UNIQUE, name text)

class DatabaseManager:
    def __init__(self, dsn, min_size=1, max_size=5, max_lifetime=300, max_idle=60):
        self.dsn = dsn

    async def execute_with_retries(self, query, params=None, fetchall=False, retries=3, initial_delay=1, max_delay=30):
        attempts = 0
        delay = initial_delay
        
        while attempts < retries:
            try:
                with self.connection as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    if query.strip().lower().startswith('select'):
                        if fetchall:
                            return cursor.fetchall()
                        else:
                            return cursor.fetchone()
                    else:
                        return None
            except (sqlite3.OperationalError, sqlite3.InterfaceError) as e:
                print(f'Database connection error: {e}. Retrying in {delay} seconds...')
                attempts += 1
                await asyncio.sleep(delay)
                
                # Exponential backoff with jitter
                delay = min(max_delay, delay * 2 + random.uniform(0, 1))
        
        raise Exception('Failed to execute query after multiple attempts.')

    async def add_brain_cell(self, name):
        points = await self.execute_with_retries('SELECT points FROM braincell_points WHERE name=?', (name,))
        if points != None:
            await self.execute_with_retries("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", (name, points[0] + 1))
        else:
            await self.execute_with_retries("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", (name, 1))
        await self.commit()

    async def add_brain_cells(self, name: str, amount: int):
        if amount < 0:
            raise ValueError('Cannot add a negative value')
        points = await self.execute_with_retries('SELECT points FROM braincell_points WHERE name=?', (name,))
        if points != None:
            await self.execute_with_retries("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", (name, points[0] + amount))
        else:
            await self.execute_with_retries("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", (name, amount))
        await self.commit()

    async def remove_brain_cells(self, name: str, amount: int):
        if amount < 0:
            raise ValueError('Cannot remove a negative value')
        points = await self.execute_with_retries('SELECT points FROM braincell_points WHERE name=?', (name,))
        if points == None:
            raise ValueError('User has no brain cells to remove')
        if points[0] < amount:
            raise ValueError('User has insufficient brain cells to remove')
        await self.execute_with_retries("REPLACE INTO braincell_points (name, points) VALUES (?, ?)", (name, points[0] - amount))
        await self.commit()

    async def get_brain_cells(self, name):
        points = await self.execute_with_retries('SELECT points FROM braincell_points WHERE name=?', (name,))
        if points == None:
            raise ValueError('User has no brain cells')
        return points[0]

    async def get_point_leader(self):
        leader = await self.execute_with_retries("SELECT name FROM braincell_points ORDER BY points DESC", ())
        return leader[0]

    async def get_all_points(self) -> list:
        points = await self.execute_with_retries("SELECT * FROM braincell_points ORDER BY points DESC", (), fetchall=True)
        return points

    async def add_counter(self, counter):
        await self.execute_with_retries("INSERT INTO counters VALUES (?,?)", (counter, 0))
        await self.commit()
    
    async def add_one_to_counter(self, counter, number):
        count = await self.execute_with_retries("SELECT count FROM counters WHERE counter=?", (counter,))
        new_count = count[0] + 1
        await self.execute_with_retries("REPLACE INTO counters (counter, count) VALUES (?, ?)", (counter, new_count))
        await self.commit()
        return new_count

    async def add_command(self, command, output, author):
        await self.execute_with_retries("INSERT INTO commands VALUES (?,?,?)", (command, output, author))
        await self.commit()

    async def delete_command(self, command):
        await self.execute_with_retries("DELETE from commands WHERE command_name=?", (command,))
        await self.commit()

    async def delete_command_output(self, command, output):
        await self.execute_with_retries("DELETE from commands WHERE command_name=? AND output=?", (command, output))
        await self.commit()

    async def does_command_exist(self, command) -> bool:
        comm = await self.execute_with_retries("SELECT * from commands WHERE command_name=?", (command,))
        return comm != None

    async def does_output_exist(self, command):
        comm = await self.execute_with_retries("SELECT * from commands WHERE command_name=? AND output=?", (command, output))
        return comm != None

    async def does_counter_exist(self, command) -> bool:
        comm = await self.execute_with_retries("SELECT * from counters WHERE counter=?", (command,))
        return comm != None

    async def get_all_commands(self) -> list:
        comms = await self.execute_with_retries("SELECT command_name from commands", (), fetchall=True)
        return comms

    async def get_output(self, command):
        output = await self.execute_with_retries("SELECT output from commands WHERE command_name=?", (command,), fetchall=True)
        return output

    async def add_gang(self, role_id, role_name):
        await self.execute_with_retries("INSERT INTO gangs VALUES (?,?)", (role_name, role_id))
        await self.commit()

    async def make_gang_table(self):
        await self.execute_with_retries('''
        CREATE TABLE IF NOT EXISTS gangs (
            role_name TEXT,
            role_id INTEGER UNIQUE)
        ''', ())
        await self.commit()

    async def delete_gang(self, role_id, role_name):
        await self.execute_with_retries("DELETE from gangs WHERE role_id=? AND role_name=?)", (role_id, role_name))
        await self.commit()

    async def get_gang_id(self, role_name):
        role_id = await self.execute_with_retries("SELECT role_id from gangs WHERE role_name=?", (role_name,))
        return role_id

    async def get_gang_name(self, role_id):
        role_name = await self.execute_with_retries("SELECT role_name from gangs WHERE role_id=?", (role_id,))
        return role_name

    async def get_all_gang_ids(self):
        role_ids = await self.execute_with_retries("SELECT role_id from gangs", (), fetchall=True)
        return role_ids
    
    async def add_new_nft(self, url: str, user_id: int, price: int):
        highest_id = await self.execute_with_retries("SELECT MAX(id) FROM nfts", ())
        await self.execute_with_retries("INSERT INTO nfts VALUES (?,?,?,?)", (highest_id[0] + 1, url, str(user_id), price))
        await self.commit()
        return highest_id[0] + 1
    
    async def get_nft_url(self, id: int):
        url = await self.execute_with_retries("SELECT url FROM nfts WHERE id = ?", (id,))
        return url
    
    async def get_nft_shop(self, user_id: int):
        urls = await self.execute_with_retries("SELECT url FROM nfts WHERE userid = ? AND price != ?", (str(user_id), 0), fetchall=True)
        return urls
    
    async def get_nft_shop_amount(self, user_id: int):
        amount = await self.execute_with_retries("SELECT COUNT(*) FROM nfts WHERE userid = ? AND price != ?", (str(user_id), 0))
        return amount
    
    async def get_nft_owner(self, id: int):
        owner  = await self.execute_with_retries("SELECT userid FROM nfts WHERE id = ?", (id,))
        return int(owner[0])
    
    async def remove_nft(self, id: int):
        await self.execute_with_retries("DELETE FROM nfts WHERE id = ?", (id,))
        await self.commit()

    async def move_nft(self, id: int, user_id: int):
        url  = await self.execute_with_retries("SELECT url FROM nfts WHERE id = ?", (id,))
        await self.execute_with_retries("REPLACE INTO nfts (id, url, userid, price) VALUES (?,?,?,?)", (id, url[0], str(user_id), 0))
        await self.commit()

    async def commit(self):
        with self.connection as conn:
            conn.commit()

    async def close(self):
        self.connection.close()
    
    async def __aenter__(self):
        self.connection = sqlite3.connect(self.dsn)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


