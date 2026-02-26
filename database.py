import aiosqlite

DB_PATH = "bot_database.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                price_uzs INTEGER NOT NULL,
                video_file_id TEXT,
                thumbnail_file_id TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                payment_charge_id TEXT,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, course_id)
            )
        """)
        # Pending payments: waiting for admin approval
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pending_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                screenshot_file_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
        await db.commit()


async def user_exists(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM users WHERE id=?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None


async def get_all_courses():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM courses WHERE is_active=1 ORDER BY id") as cursor:
            return await cursor.fetchall()


async def get_course(course_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM courses WHERE id=?", (course_id,)) as cursor:
            return await cursor.fetchone()


async def add_course(title, description, price_uzs, video_file_id, thumbnail_file_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO courses (title, description, price_uzs, video_file_id, thumbnail_file_id) VALUES (?, ?, ?, ?, ?)",
            (title, description, price_uzs, video_file_id, thumbnail_file_id)
        )
        await db.commit()
        return cursor.lastrowid


async def delete_course(course_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE courses SET is_active=0 WHERE id=?", (course_id,))
        await db.commit()


async def has_purchased(user_id: int, course_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM purchases WHERE user_id=? AND course_id=?",
            (user_id, course_id)
        ) as cursor:
            return await cursor.fetchone() is not None


async def add_purchase(user_id: int, course_id: int, charge_id: str = "manual"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO purchases (user_id, course_id, payment_charge_id) VALUES (?, ?, ?)",
            (user_id, course_id, charge_id)
        )
        await db.commit()


async def add_pending_payment(user_id: int, course_id: int, screenshot_file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # Remove old pending for same user+course
        await db.execute(
            "DELETE FROM pending_payments WHERE user_id=? AND course_id=? AND status='pending'",
            (user_id, course_id)
        )
        cursor = await db.execute(
            "INSERT INTO pending_payments (user_id, course_id, screenshot_file_id) VALUES (?, ?, ?)",
            (user_id, course_id, screenshot_file_id)
        )
        await db.commit()
        return cursor.lastrowid


async def get_pending_payment(payment_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM pending_payments WHERE id=?", (payment_id,)) as cursor:
            return await cursor.fetchone()


async def update_pending_status(payment_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE pending_payments SET status=? WHERE id=?",
            (status, payment_id)
        )
        await db.commit()


async def get_pending_payments():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM pending_payments WHERE status='pending' ORDER BY created_at"
        ) as cursor:
            return await cursor.fetchall()


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM courses WHERE is_active=1") as c:
            total_courses = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM purchases") as c:
            total_purchases = (await c.fetchone())[0]
        async with db.execute(
            "SELECT COALESCE(SUM(c.price_uzs), 0) FROM purchases p JOIN courses c ON p.course_id=c.id"
        ) as c:
            total_uzs = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM pending_payments WHERE status='pending'") as c:
            pending = (await c.fetchone())[0]
        return total_users, total_courses, total_purchases, total_uzs, pending


async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_user_purchases(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT c.* FROM courses c
            JOIN purchases p ON c.id = p.course_id
            WHERE p.user_id=?
        """, (user_id,)) as cursor:
            return await cursor.fetchall()
