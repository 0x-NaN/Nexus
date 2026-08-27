#!/usr/bin/env python3
"""
Database reset script for local development.
Truncates transactions and kill_switch_events, re-seeds initial state.
"""
import asyncio
import asyncpg
import os

async def reset():
    # Use PGPASSWORD from environment
    password = os.getenv("PGPASSWORD", "postgres")
    
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password=password,
        database="killswitch"
    )
    
    try:
        # Truncate and reseed
        await conn.execute("TRUNCATE transactions, kill_switch_events RESTART IDENTITY")
        await conn.execute(
            "INSERT INTO kill_switch_events (state, triggered_by) VALUES ('active', 'system_startup')"
        )
        print("✓ Database reset complete")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(reset())