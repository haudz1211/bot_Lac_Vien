import gspread
from google.oauth2.service_account import Credentials


# =========================================================
# GOOGLE SHEETS CONFIG
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


# =========================================================
# GOOGLE CREDENTIALS
# =========================================================

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)


# =========================================================
# GOOGLE CLIENT
# =========================================================

client = gspread.authorize(
    creds
)


# =========================================================
# GOOGLE SHEET
#
# sheet1 = tab đầu tiên
# Hiện tại là "Danh sách thành viên"
# =========================================================

spreadsheet = client.open_by_key(
    "1paKSN6vm5SThjEjBNjhDZTSGXlaccng3Kx2A4_u9eq4"
)

sheet = spreadsheet.sheet1


# =========================================================
# CLASS MAP
# =========================================================

CLASS_MAP = {

    "thần tương": "Thần Tương",

    "tố vấn": "Tố Vấn",

    "thiết y": "Thiết Y",

    "cửu linh": "Cửu Linh",

    "huyết hà": "Huyết Hà",

    "long ngâm": "Long Ngâm",

    "tuyết ẩn": "Tuyết Ẩn",

    "toái mộng": "Toái Mộng"

}


# =========================================================
# MÀU TỪNG MÔN PHÁI
#
# Google Sheets dùng RGB từ 0.0 -> 1.0
# =========================================================

CLASS_ROW_COLORS = {

    # Xanh dương
    "Thần Tương": {
        "red": 0.30,
        "green": 0.60,
        "blue": 1.00
    },

    # Xanh dương nhạt
    "Toái Mộng": {
        "red": 0.65,
        "green": 0.85,
        "blue": 1.00
    },

    # Hồng
    "Tố Vấn": {
        "red": 1.00,
        "green": 0.65,
        "blue": 0.80
    },

    # Đỏ
    "Huyết Hà": {
        "red": 1.00,
        "green": 0.40,
        "blue": 0.40
    },

    # Xanh lá
    "Long Ngâm": {
        "red": 0.45,
        "green": 0.85,
        "blue": 0.45
    },

    # Tím
    "Cửu Linh": {
        "red": 0.70,
        "green": 0.45,
        "blue": 0.85
    },

    # Vàng
    "Thiết Y": {
        "red": 1.00,
        "green": 0.85,
        "blue": 0.35
    },

    # Tuyết Ẩn
    #
    # Bạn chưa yêu cầu màu nên để màu trắng.
    "Tuyết Ẩn": {
        "red": 1.00,
        "green": 1.00,
        "blue": 1.00
    }
}


# =========================================================
# CHUYỂN SỐ CỘT -> CHỮ CỘT
#
# 1  -> A
# 2  -> B
# 26 -> Z
# 27 -> AA
# =========================================================

def column_to_letter(
    column_number
):

    result = ""

    while column_number > 0:

        column_number, remainder = divmod(
            column_number - 1,
            26
        )

        result = (
            chr(65 + remainder)
            + result
        )

    return result


# =========================================================
# LẤY MÀU MÔN PHÁI
# =========================================================

def get_class_color(
    mon_phai
):

    mon_phai = str(
        mon_phai
    ).strip()

    # Chuẩn hóa nếu người dùng nhập
    # thần tương / THẦN TƯƠNG...
    normalized = CLASS_MAP.get(
        mon_phai.lower(),
        mon_phai
    )

    return CLASS_ROW_COLORS.get(
        normalized
    )


# =========================================================
# TÔ MÀU HÀNG NGƯỜI CHƠI
#
# Tô từ cột A đến cột cuối cùng
# đang có dữ liệu trong hàng đó.
#
# Ví dụ:
# A:D có dữ liệu
# -> tô A:D
#
# A:H có dữ liệu
# -> tô A:H
#
# Không tô các cột trống phía sau.
# =========================================================

def color_player_row(
    worksheet,
    row_number,
    mon_phai
):

    try:

        color = get_class_color(
            mon_phai
        )

        if color is None:

            print(
                f"⚠️ Không có màu cho môn phái: "
                f"{mon_phai}"
            )

            return False

        # =================================================
        # LẤY DỮ LIỆU HÀNG
        # =================================================

        row_values = worksheet.row_values(
            row_number
        )

        if not row_values:

            print(
                f"⚠️ Hàng {row_number} không có dữ liệu."
            )

            return False

        # =================================================
        # TÌM CỘT CUỐI CÙNG CÓ DỮ LIỆU
        # =================================================

        last_column = 0

        for index, value in enumerate(
            row_values,
            start=1
        ):

            if str(value).strip():

                last_column = index

        if last_column == 0:

            return False

        end_column = column_to_letter(
            last_column
        )

        # =================================================
        # TÔ MÀU
        # =================================================

        worksheet.format(
            f"A{row_number}:{end_column}{row_number}",
            {
                "backgroundColor": color
            }
        )

        print(
            f"🎨 Đã tô màu hàng {row_number}: "
            f"{mon_phai}"
        )

        return True

    except Exception as e:

        print(
            f"❌ Lỗi tô màu hàng {row_number}: "
            f"{e}"
        )

        return False


# =========================================================
# SAVE PLAYER
# =========================================================

def save_player(
    member,
    ten_nv,
    mon_phai
):

    # =====================================================
    # CHUẨN HÓA MÔN PHÁI
    # =====================================================

    mon_phai = CLASS_MAP.get(
        str(mon_phai).lower().strip(),
        str(mon_phai).strip()
    )

    print("=" * 60)

    print(
        "💾 SAVE PLAYER"
    )

    print(
        f"👤 Discord: {member.name}"
    )

    print(
        f"🆔 Discord ID: {member.id}"
    )

    print(
        f"📝 Tên nhân vật: {ten_nv}"
    )

    print(
        f"⚔️ Môn phái: {mon_phai}"
    )

    print("=" * 60)

    try:

        # =================================================
        # LẤY DATA
        # =================================================

        rows = sheet.get_all_values()

        if not rows:

            print(
                "⚠️ Sheet đang trống."
            )

            rows = [
                []
            ]

        # =================================================
        # KIỂM TRA NGƯỜI ĐÃ TỒN TẠI
        # =================================================

        for i, row in enumerate(
            rows[1:],
            start=2
        ):

            if (
                len(row) > 0
                and str(row[0]).strip()
                == str(member.name).strip()
            ):

                # =========================================
                # UPDATE DỮ LIỆU
                # =========================================

                sheet.update(
                    f"A{i}:D{i}",
                    [[
                        member.name,
                        member.display_name,
                        ten_nv,
                        mon_phai
                    ]]
                )

                print(
                    f"🔄 Đã cập nhật người chơi: "
                    f"{member.name}"
                )

                # =========================================
                # TÔ MÀU LẠI HÀNG
                # =========================================

                color_player_row(
                    sheet,
                    i,
                    mon_phai
                )

                print(
                    "✅ Đã cập nhật màu hàng."
                )

                print("=" * 60)

                return

        # =================================================
        # THÊM NGƯỜI CHƠI MỚI
        # =================================================

        sheet.append_row([
            member.name,
            member.display_name,
            ten_nv,
            mon_phai
        ])

        print(
            f"➕ Đã thêm người chơi: "
            f"{member.name}"
        )

        # =================================================
        # LẤY DÒNG VỪA THÊM
        # =================================================

        row_number = len(
            sheet.get_all_values()
        )

        print(
            f"📌 Dòng mới: {row_number}"
        )

        # =================================================
        # TÔ MÀU
        # =================================================

        color_player_row(
            sheet,
            row_number,
            mon_phai
        )

        print(
            "✅ Đã tô màu hàng mới."
        )

        print("=" * 60)

    except Exception as e:

        print("=" * 60)

        print(
            f"❌ LỖI save_player(): {e}"
        )

        print("=" * 60)

        raise


# =========================================================
# DELETE PLAYER
# =========================================================
# =========================================================
# DELETE PLAYER
#
# Hỗ trợ:
#
# 1. Discord ID
# 2. Discord username
# 3. Tên nhân vật / IGame
#
# Cấu trúc Sheet hiện tại:
#
# A = Discord username
# B = Display name
# C = Tên nhân vật
# D = Môn phái
# =========================================================

def delete_player(
    discord_id=None,
    discord_username=None,
    ten_nv=None
):
    """
    Xóa người chơi khỏi Google Sheets.

    Có thể tìm bằng:

    - Discord ID
    - Discord username
    - Tên nhân vật / IGame

    Tìm theo thứ tự:

    1. Discord ID nếu Sheet có cột ID
    2. Discord username
    3. Tên nhân vật ở cột C
    """

    print("=" * 60)
    print("🗑️ DELETE PLAYER GOOGLE SHEETS")
    print("=" * 60)

    try:

        # =================================================
        # CHUẨN HÓA
        # =================================================

        if discord_id is not None:
            discord_id = str(
                discord_id
            ).strip()

        if discord_username:
            discord_username = str(
                discord_username
            ).strip()

        if ten_nv:
            ten_nv = str(
                ten_nv
            ).strip()

        print(
            f"🔎 Discord ID: {discord_id}"
        )

        print(
            f"🔎 Discord username: "
            f"{discord_username}"
        )

        print(
            f"🔎 IGame: "
            f"{ten_nv}"
        )

        # =================================================
        # LẤY DATA
        # =================================================

        rows = sheet.get_all_values()

        if not rows:

            print(
                "⚠️ Google Sheet không có dữ liệu."
            )

            return False

        # =================================================
        # HEADER
        # =================================================

        header = rows[0]

        print(
            f"📋 Header: {header}"
        )

        # =================================================
        # TÌM CỘT DISCORD ID
        # =================================================

        id_column = None

        for index, column_name in enumerate(header):

            normalized = (
                str(column_name)
                .strip()
                .lower()
            )

            if normalized in [
                "id discord",
                "discord id",
                "user id",
                "discordid"
            ]:

                id_column = index

                break

        # =================================================
        # TÌM CỘT USERNAME
        #
        # Nếu không tìm được header phù hợp
        # thì mặc định A = Discord username
        # =================================================

        username_column = None

        for index, column_name in enumerate(header):

            normalized = (
                str(column_name)
                .strip()
                .lower()
            )

            if normalized in [
                "discord",
                "discord username",
                "username",
                "tài khoản",
                "tai khoan",
                "tên discord",
                "ten discord"
            ]:

                username_column = index

                break

        # =================================================
        # SHEET HIỆN TẠI CỦA BẠN
        #
        # A = Discord username
        # =================================================

        if username_column is None:

            username_column = 0

        # =================================================
        # TÌM CỘT TÊN NHÂN VẬT
        #
        # Sheet hiện tại:
        #
        # C = Tên nhân vật
        #
        # Nếu header không nhận ra thì mặc định C.
        # =================================================

        character_column = None

        for index, column_name in enumerate(header):

            normalized = (
                str(column_name)
                .strip()
                .lower()
            )

            if normalized in [
                "tên nhân vật",
                "ten nhan vat",
                "tên nv",
                "ten nv",
                "igame",
                "tên game",
                "ten game",
                "nhân vật",
                "nhan vat"
            ]:

                character_column = index

                break

        # =================================================
        # MẶC ĐỊNH CỘT C
        # =================================================

        if character_column is None:

            character_column = 2

        print(
            f"📌 Cột username: "
            f"{column_to_letter(username_column + 1)}"
        )

        print(
            f"📌 Cột IGame: "
            f"{column_to_letter(character_column + 1)}"
        )

        if id_column is not None:

            print(
                f"📌 Cột Discord ID: "
                f"{column_to_letter(id_column + 1)}"
            )

        # =================================================
        # TÌM DÒNG
        # =================================================

        row_to_delete = None

        # =================================================
        # 1. TÌM BẰNG DISCORD ID
        # =================================================

        if (
            discord_id
            and id_column is not None
        ):

            for row_number, row in enumerate(
                rows[1:],
                start=2
            ):

                if len(row) <= id_column:
                    continue

                value = str(
                    row[id_column]
                ).strip()

                if value == discord_id:

                    row_to_delete = row_number

                    print(
                        f"✅ Tìm thấy bằng Discord ID "
                        f"ở dòng {row_number}"
                    )

                    break

        # =================================================
        # 2. TÌM BẰNG DISCORD USERNAME
        # =================================================

        if (
            row_to_delete is None
            and discord_username
        ):

            for row_number, row in enumerate(
                rows[1:],
                start=2
            ):

                if len(row) <= username_column:
                    continue

                value = str(
                    row[username_column]
                ).strip()

                if (
                    value.lower()
                    == discord_username.lower()
                ):

                    row_to_delete = row_number

                    print(
                        f"✅ Tìm thấy bằng Discord username "
                        f"ở dòng {row_number}"
                    )

                    break

        # =================================================
        # 3. TÌM BẰNG IGAME
        #
        # Đây là phần dành cho người đã OUT DISCORD.
        # =================================================

        if (
            row_to_delete is None
            and ten_nv
        ):

            for row_number, row in enumerate(
                rows[1:],
                start=2
            ):

                if len(row) <= character_column:
                    continue

                value = str(
                    row[character_column]
                ).strip()

                if (
                    value.lower()
                    == ten_nv.lower()
                ):

                    row_to_delete = row_number

                    print(
                        f"✅ Tìm thấy bằng IGame "
                        f"ở dòng {row_number}"
                    )

                    break

        # =================================================
        # KHÔNG TÌM THẤY
        # =================================================

        if row_to_delete is None:

            print(
                "⚠️ Không tìm thấy người dùng "
                "trong Google Sheets."
            )

            print("=" * 60)

            return False

        # =================================================
        # LẤY THÔNG TIN TRƯỚC KHI XÓA
        # =================================================

        deleted_row = rows[
            row_to_delete - 1
        ]

        print(
            f"📄 Dữ liệu bị xóa: "
            f"{deleted_row}"
        )

        # =================================================
        # XÓA DÒNG
        # =================================================

        sheet.delete_rows(
            row_to_delete
        )

        print(
            f"🗑️ Đã xóa dòng "
            f"{row_to_delete} "
            f"khỏi Google Sheets."
        )

        print("=" * 60)

        return True

    except Exception as e:

        print("=" * 60)

        print(
            f"❌ LỖI delete_player(): "
            f"{e}"
        )

        print("=" * 60)

        return False


# =========================================================
# DELETE PLAYER BY IGAME
#
# Hàm riêng để dễ gọi từ !lvkick IGame
# =========================================================

def delete_player_by_igame(
    ten_nv
):

    return delete_player(
        ten_nv=ten_nv
    )