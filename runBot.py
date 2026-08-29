import discord
from discord.ext import commands
import os
import asyncio


# =========================================================
# TOKEN
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOKEN_FILE = os.path.join(BASE_DIR, "token.txt")

with open(TOKEN_FILE, "r", encoding="utf-8-sig") as f:
    TOKEN = f.read().strip()


if not TOKEN:
    raise RuntimeError("❌ token.txt đang trống.")


print(f"🔑 Token length: {len(TOKEN)}")


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()

intents.message_content = True
intents.polls = True
    
intents.message_content = True
intents.members = True

try:
    intents.polls = True
except AttributeError:
    pass

try:
    intents.guild_polls = True
except AttributeError:
    pass


# =========================================================
# BOT
# =========================================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# READY
# =========================================================

@bot.event
async def on_ready():

    print()
    print("=" * 60)
    print(f"🤖 BOT ONLINE: {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"📦 discord.py: {discord.__version__}")
    print("=" * 60)

    print("\n📋 DANH SÁCH COMMAND:")

    for command in bot.commands:
        print(f"⚔️ {command.name}")

    print("=" * 60)


# =========================================================
# MAIN
# =========================================================

async def main():

    # -----------------------------------------
    # LOAD ROLE CLASS
    # -----------------------------------------

    try:

        await bot.load_extension("role_class")
         

        print("✅ Đã load role_class.py")

    except Exception as e:

        print(f"❌ Lỗi load role_class.py: {e}")

        raise


    # -----------------------------------------
    # LOAD BANG CHIEN
    # -----------------------------------------

    try:

        await bot.load_extension("bang_chien")

        print("✅ Đã load bang_chien.py")

    except Exception as e:

        print(f"❌ Lỗi load bang_chien.py: {e}")

        raise
    try:

        await bot.load_extension("kick_mem")

        print("✅ Đã load kick_mem.py")

    except Exception as e:

        print(
            f"❌ Lỗi load kick_mem.py: {e}"
        )

        raise

    # -----------------------------------------
    # LOGIN
    # -----------------------------------------

    print()
    print("🔑 Đang đăng nhập Discord...")

    await bot.start(TOKEN)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:
         
        print("\n🛑 Bot đã dừng.")