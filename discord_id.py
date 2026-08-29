import os


# =========================================================
# CẤU HÌNH FILE
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DISCORD_ID_FILE = os.path.join(
    BASE_DIR,
    "discord_id.txt"
)


# =========================================================
# DEBUG
# =========================================================

print("============================================================")
print("🔐 LOAD DISCORD_ID")
print("============================================================")

print(
    f"📂 File quyền: {DISCORD_ID_FILE}"
)


# =========================================================
# ĐỌC DANH SÁCH NGƯỜI ĐƯỢC PHÉP
# =========================================================

def load_allowed_users():

    allowed = set()

    if not os.path.exists(DISCORD_ID_FILE):

        print(
            f"⚠️ Không tìm thấy file: "
            f"{DISCORD_ID_FILE}"
        )

        return allowed


    try:

        with open(
            DISCORD_ID_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            for line in f:

                line = line.strip()

                # Bỏ dòng trống
                if not line:
                    continue

                # Bỏ comment
                if line.startswith("#"):
                    continue

                # -------------------------------------------------
                # Cho phép dạng:
                #
                # cuabro123
                #
                # hoặc:
                #
                # 123456789012345678
                #
                # hoặc:
                #
                # cuabro123 | 123456789012345678
                # -------------------------------------------------

                parts = line.split("|")

                for part in parts:

                    part = part.strip()

                    if not part:
                        continue

                    allowed.add(
                        part.lower()
                    )


    except Exception as e:

        print(
            f"❌ Lỗi đọc {DISCORD_ID_FILE}: {e}"
        )

        return set()


    print(
        f"✅ Đã đọc {len(allowed)} mục "
        f"từ discord_id.txt"
    )

    for item in sorted(allowed):

        print(
            f"   🔐 {item}"
        )

    print(
        "============================================================"
    )

    return allowed


# =========================================================
# KIỂM TRA USER ĐƯỢC PHÉP
# =========================================================

def is_allowed_user(user):

    """
    Kiểm tra user có nằm trong discord_id.txt hay không.

    Cho phép:

        cuabro123

    hoặc:

        123456789012345678

    hoặc:

        username | 123456789012345678
    """

    if user is None:

        return False


    allowed_users = load_allowed_users()


    if not allowed_users:

        print(
            "⚠️ Danh sách discord_id.txt đang trống."
        )

        return False


    # =====================================================
    # LẤY THÔNG TIN USER
    # =====================================================

    user_id = str(
        getattr(
            user,
            "id",
            ""
        )
    ).strip().lower()


    username = str(
        getattr(
            user,
            "name",
            ""
        )
    ).strip().lower()


    display_name = str(
        getattr(
            user,
            "display_name",
            ""
        )
    ).strip().lower()


    # =====================================================
    # DEBUG
    # =====================================================

    print()
    print("🔎 KIỂM TRA QUYỀN DISCORD")

    print(
        f"   🆔 ID          : {user_id}"
    )

    print(
        f"   👤 Username    : {username}"
    )

    print(
        f"   📛 DisplayName : {display_name}"
    )


    # =====================================================
    # KIỂM TRA ID
    # =====================================================

    if user_id and user_id in allowed_users:

        print(
            "   ✅ ĐƯỢC PHÉP → khớp Discord ID"
        )

        return True


    # =====================================================
    # KIỂM TRA USERNAME
    # =====================================================

    if username and username in allowed_users:

        print(
            "   ✅ ĐƯỢC PHÉP → khớp username"
        )

        return True


    # =====================================================
    # KIỂM TRA DISPLAY NAME
    # =====================================================

    if display_name and display_name in allowed_users:

        print(
            "   ✅ ĐƯỢC PHÉP → khớp display name"
        )

        return True


    # =====================================================
    # KHÔNG CÓ QUYỀN
    # =====================================================

    print(
        "   ❌ KHÔNG ĐƯỢC PHÉP"
    )

    return False


# =========================================================
# THÊM USER
# =========================================================

# def add_discord_user(
#     discord_id=None,
#     username=None
# ):

#     """
#     Thêm user vào discord_id.txt.

#     Ví dụ:

#         add_discord_user(
#             discord_id=123456789,
#             username="cuabro123"
#         )
#     """

#     values = []


#     if discord_id:

#         values.append(
#             str(discord_id).strip()
#         )


#     if username:

#         values.append(
#             str(username).strip()
#         )


#     if not values:

#         return False


#     try:

#         # Đảm bảo file tồn tại
#         if not os.path.exists(DISCORD_ID_FILE):

#             open(
#                 DISCORD_ID_FILE,
#                 "a",
#                 encoding="utf-8"
#             ).close()


#         existing = load_allowed_users()


#         # =================================================
#         # KIỂM TRA ĐÃ CÓ CHƯA
#         # =================================================

#         new_values = []

#         for value in values:

#             if value.lower() not in existing:

#                 new_values.append(value)


#         if not new_values:

#             print(
#                 "ℹ️ User đã tồn tại trong discord_id.txt"
#             )

#             return True


#         # =================================================
#         # GHI FILE
#         # =================================================

#         with open(
#             DISCORD_ID_FILE,
#             "a",
#             encoding="utf-8"
#         ) as f:

#             for value in new_values:

#                 f.write(
#                     value + "\n"
#                 )


#         print(
#             f"✅ Đã thêm vào discord_id.txt: "
#             f"{', '.join(new_values)}"
#         )

#         return True


#     except Exception as e:

#         print(
#             f"❌ Lỗi thêm Discord user: {e}"
#         )

#         return False


# =========================================================
# ALIAS TƯƠNG THÍCH CODE CŨ
# =========================================================

# def add_discord_name(
#     username
# ):

#     """
#     Tương thích với code cũ nếu nơi khác
#     vẫn đang import add_discord_name.
#     """

#     return add_discord_user(
#         username=username
#     )


# =========================================================
# TEST KHI CHẠY TRỰC TIẾP
# =========================================================

if __name__ == "__main__":

    print()
    print("🔎 TEST discord_id.py")
    print()

    allowed = load_allowed_users()

    print(
        f"📊 Tổng số mục: {len(allowed)}"
    )