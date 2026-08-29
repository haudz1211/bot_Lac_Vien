import os


# =========================================================
# THƯ MỤC BOT
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# =========================================================
# FILE ID KÊNH
# =========================================================

CHANNEL_FILE = os.path.join(
    BASE_DIR,
    "ID_kênh.txt"
)


# =========================================================
# ĐỌC ID KÊNH
# =========================================================

def load_channels():

    channels = {}

    if not os.path.exists(CHANNEL_FILE):

        print(
            f"❌ Không tìm thấy file ID kênh:"
        )

        print(
            CHANNEL_FILE
        )

        return channels


    with open(
        CHANNEL_FILE,
        "r",
        encoding="utf-8-sig"
    ) as f:

        for line in f:

            line = line.strip()

            # Bỏ dòng trống
            if not line:
                continue

            # Bỏ comment
            if line.startswith("#"):
                continue

            # Không có dấu =
            if "=" not in line:
                continue

            key, value = line.split(
                "=",
                1
            )

            key = key.strip().upper()
            value = value.strip()

            try:

                channels[key] = int(value)

            except ValueError:

                print(
                    f"⚠️ ID không hợp lệ: {line}"
                )


    return channels


# =========================================================
# LOAD
# =========================================================

CHANNELS = load_channels()


# =========================================================
# ID KÊNH
# =========================================================

BANG_CHIEN_CHANNEL_ID = CHANNELS.get(
    "BANG_CHIEN"
)

KICK_CHANNEL_ID = CHANNELS.get(
    "KICK"
)

ROLE_CLASS_CHANNEL_ID = CHANNELS.get(
    "ROLE_CLASS"
)


# =========================================================
# DEBUG
# =========================================================

print()
print("=" * 60)
print("📂 CHANNEL CONFIG")
print("=" * 60)

print(
    f"📄 File: {CHANNEL_FILE}"
)

print(
    f"⚔️ BANG_CHIEN: {BANG_CHIEN_CHANNEL_ID}"
)

print(
    f"🦵 KICK: {KICK_CHANNEL_ID}"
)

print(
    f"🏷️ ROLE_CLASS: {ROLE_CLASS_CHANNEL_ID}"
)

print("=" * 60)