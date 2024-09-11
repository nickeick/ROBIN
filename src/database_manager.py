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

    async def get_brain_cells(self, name):
        points = await self.execute_with_retries('SELECT points FROM braincell_points WHERE name=?', (name,))
        return points[0]

    async def get_point_leader(self):
        leader = await self.execute_with_retries("SELECT name FROM braincell_points ORDER BY points DESC", ())
        return leader[0]

    async def get_all_points(self) -> list:
        points = await self.execute_with_retries("SELECT * FROM braincell_points ORDER BY points DESC", (), fetchall=True)
        return points
    
    async def add_counter(self, counter, number):
        count = await self.execute_with_retries("SELECT count FROM counters WHERE counter=?", (counter,))
        new_count = count[0] + 1
        await self.execute_with_retries("REPLACE INTO counters (counter, count) VALUES (?, ?)", (counter, new_count))
        return new_count

    async def add_command(self, command, output, author):
        await self.execute_with_retries("INSERT INTO commands VALUES (?,?,?)", (command, output, author))

    async def delete_command(self, command):
        await self.execute_with_retries("DELETE from commands WHERE command_name=?", (command,))

    async def delete_command_output(self, command, output):
        await self.execute_with_retries("DELETE from commands WHERE command_name=? AND output=?", (command, output))

    async def does_command_exist(self, command, output) -> bool:
        comm = await self.execute_with_retries("SELECT * from commands WHERE command_name=? AND output=?", (command, output))
        return comm != None

    async def get_all_commands(self) -> list:
        comms = await self.execute_with_retries("SELECT command_name from commands", (), fetchall=True)
        return comms

    async def get_output(self, command):
        output = await self.execute_with_retries("SELECT output from commands WHERE command_name=?", (command,), fetchall=True)
        return output

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


