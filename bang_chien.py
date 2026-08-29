import os
import asyncio
import json
from datetime import datetime, timedelta

import discord
from discord.ext import commands

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from channel_config import BANG_CHIEN_CHANNEL_ID
from discord_id import is_allowed_user

import random
import time
import threading
from gspread.exceptions import APIError
# =========================================================
# GOOGLE SHEETS RETRY
#
# Tự động thử lại khi Google API tạm thời lỗi:
# 503 - Service Unavailable
# 500 - Internal Server Error
# 502 - Bad Gateway
# 504 - Gateway Timeout
# 429 - Too Many Requests
# =========================================================
def get_worksheet_with_retry(spreadsheet, worksheet_name, retries=7):
    for attempt in range(retries):
        try:
            return spreadsheet.worksheet(worksheet_name)
        except APIError as e:
            error_text = str(e)
            retryable = any(
                code in error_text
                for code in ("[429]", "[500]", "[502]", "[503]", "[504]")
            )
            if not retryable:
                raise

            wait_time = min(5 * (2 ** attempt), 60) + random.uniform(0, 1)
            print(
                f"⚠️ Google Sheets API lỗi khi lấy worksheet "
                f"'{worksheet_name}': {error_text} | "
                f"Retry {attempt + 1}/{retries} sau {wait_time:.1f}s"
            )
            time.sleep(wait_time)

    raise RuntimeError(
        f"❌ Không thể lấy worksheet '{worksheet_name}' sau {retries} lần thử."
    )

def google_retry(
    func,
    *args,
    max_retries=5,
    base_delay=2,
    **kwargs
):

    for attempt in range(max_retries):

        try:

            return func(
                *args,
                **kwargs
            )

        except APIError as e:

            error_text = str(e)

            retryable = any(
                code in error_text
                for code in (
                    "[500]",
                    "[502]",
                    "[503]",
                    "[504]",
                    "[429]"
                )
            )

            # ---------------------------------------------
            # LỖI KHÔNG PHẢI LỖI TẠM THỜI
            # ---------------------------------------------

            if not retryable:

                raise

            # ---------------------------------------------
            # HẾT SỐ LẦN RETRY
            # ---------------------------------------------

            if attempt >= max_retries - 1:

                print(
                    f"❌ Google API vẫn lỗi "
                    f"sau {max_retries} lần retry."
                )

                raise

            # ---------------------------------------------
            # EXPONENTIAL BACKOFF
            # 2 -> 4 -> 8 -> 16 -> 32
            # ---------------------------------------------

            if "[429]" in error_text:
                # Per-user read quota is minute based. Retrying after 2s/4s
                # only creates another burst and often repeats the 429.
                delay = min(20 + (10 * attempt), 60) + random.uniform(0, 2)
            else:
                delay = (
                    base_delay * (2 ** attempt)
                    + random.uniform(0, 1)
                )

            print()
            print(
                "⚠️ GOOGLE SHEETS API TẠM THỜI LỖI"
            )

            print(
                f"   Error: {error_text}"
            )

            print(
                f"   🔄 Retry "
                f"{attempt + 1}/{max_retries}"
            )

            print(
                f"   ⏳ Chờ {delay:.1f} giây..."
            )

            time.sleep(delay)
# =========================================================
# CACHE
# =========================================================

# Cache row Google Sheets
# activity -> Discord ID -> row number
activity_row_cache = {}


# Cache answer Poll
# message_id -> activity + answer_id -> status
poll_answer_cache = {}


# =========================================================
#                    CẤU HÌNH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# =========================================================
# ID KÊNH HIỂN THỊ POLL
# =========================================================

BANG_CHIEN_POLL_CHANNEL_ID = 1540078272551845898

# =========================================================
# GOOGLE SHEETS
# =========================================================

SPREADSHEET_NAME = "Lạc Viên"

PLAYER_WORKSHEET_NAME = "Danh sách thành viên"

WAR_WORKSHEET_NAME = "Bang Chiến"

SCRIM_THU5_WORKSHEET_NAME = "Scrim Thứ 5"

SCRIM_THU6_WORKSHEET_NAME = "Scrim Thứ 6"

# =========================================================
# GOOGLE CREDENTIALS
# =========================================================

GOOGLE_CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json"
)

# =========================================================
# STATE FILE
# =========================================================

STATE_FILE = os.path.join(
    BASE_DIR,
    "bangchien_state.json"
)

# =========================================================
# HEADER A:H
# =========================================================

WAR_HEADERS = [
    "STT",
    "Discord ID",
    "Discord",
    "Tên nhân vật",
    "Môn phái",
    "Trạng thái",
    "Thời gian đăng ký",
    "Người đăng ký",
]

# =========================================================
# TRẠNG THÁI BANG CHIẾN
# =========================================================

POLL_JOIN = "⚔️ ĐÁNH BANG CHIẾN"

POLL_NOT_JOIN = "❌ KHÔNG ĐÁNH"

POLL_PENDING = "⏳ CHƯA BÌNH CHỌN"

# =========================================================
# TRẠNG THÁI SCRIM
# =========================================================

SCRIM_JOIN = "⚔️ THAM GIA SCRIM"

SCRIM_NOT_JOIN = "❌ KHÔNG THAM GIA SCRIM"

SCRIM_PENDING = "⏳ CHƯA BÌNH CHỌN"

# =========================================================
# THỜI GIAN POLL
# =========================================================

POLL_DURATION = timedelta(
    hours=72
)

# =========================================================
# CẤU HÌNH HOẠT ĐỘNG
# =========================================================

# =========================================================
# CẤU HÌNH HOẠT ĐỘNG
# =========================================================

ACTIVITY_CONFIG = {

    # =====================================================
    # BANG CHIẾN 1 TRẬN
    # =====================================================

    "bangchien1": {

        "kind": "bangchien",

        "type": 1,

        "sheet": WAR_WORKSHEET_NAME,

        "title":
            "⚔️ Bang Chiến tuần này - 1 TRẬN ⚔️",

        "description":
            "🏆 Tuần này bang có 1 trận Bang Chiến.\n\n"
            "💀 Anh em cố gắng sắp xếp thời gian tham gia "
            "để đảm bảo đủ người.\n\n"
            "⏰ Hạn đăng ký: sau 72 giờ\n\n"
            "🙏 MONG TẤT CẢ ANH EM SẮP XẾP THAM GIA!",

        "question":
            "Bạn có tham gia Bang Chiến tuần này (1 trận) không?",

        "join":
            "Có",

        "not_join":
            "Không",

        "emoji_join":
            "⚔️",

        "emoji_not_join":
            "❌",

        "join_status":
            POLL_JOIN,

        "not_join_status":
            POLL_NOT_JOIN,

        "pending_status":
            POLL_PENDING,
    },


    # =====================================================
    # BANG CHIẾN 2 TRẬN
    # =====================================================

    "bangchien2": {

        "kind": "bangchien",

        "type": 2,

        "sheet": WAR_WORKSHEET_NAME,

        "title":
            "⚔️⚔️⚔️ Thứ 7 - 2 TRẬN ⚔️⚔️⚔️",

        "description":
            "🔴 ĐÂY LÀ TUẦN QUAN TRỌNG!\n\n"
            "💀 Kết quả 2 trận quyết định bang "
            "THĂNG HẠNG hay XUỐNG HẠNG!\n\n"
            "💀 Thiếu người = Thua = XUỐNG HẠNG = "
            "ảnh hưởng CẢ BANG!\n\n"
            "⏰ Hạn đăng ký: sau 72 giờ\n\n"
            "🙏 MONG TẤT CẢ ANH EM SẮP XẾP THAM GIA!",

        "question":
            "Bạn có tham gia Bang Chiến Thứ 7 (2 trận) không?",

        "join":
            "Có",

        "not_join":
            "Không",

        "emoji_join":
            "⚔️",

        "emoji_not_join":
            "❌",

        "join_status":
            POLL_JOIN,

        "not_join_status":
            POLL_NOT_JOIN,

        "pending_status":
            POLL_PENDING,
    },


    # =====================================================
    # SCRIM THỨ 5
    #
    # Config này chỉ là config GỐC.
    # Số trận + đối thủ sẽ được build_scrim_config()
    # tạo động khi chạy:
    #
    # !scrimthu5 1 Cửu Thiên
    # !scrimthu5 2 Cửu Thiên, Phong Ưng
    # =====================================================

    "scrimthu5": {

        "kind": "scrim",

        "type": 5,

        "sheet": SCRIM_THU5_WORKSHEET_NAME,

        "title":
            "🎮 SCRIM THỨ 5 🎮",

        "description":
            "🎮 Tuần này có lịch SCRIM THỨ 5.",

        "question":
            "Bạn có tham gia SCRIM THỨ 5 không?",

        "join":
            "Có",

        "not_join":
            "Không",

        "emoji_join":
            "⚔️",

        "emoji_not_join":
            "❌",

        "join_status":
            SCRIM_JOIN,

        "not_join_status":
            SCRIM_NOT_JOIN,

        "pending_status":
            SCRIM_PENDING,
    },


    # =====================================================
    # SCRIM THỨ 6
    #
    # Config gốc, giống Thứ 5 nhưng ghi vào:
    # Scrim Thứ 6
    # =====================================================

    "scrimthu6": {

        "kind": "scrim",

        "type": 6,

        "sheet": SCRIM_THU6_WORKSHEET_NAME,

        "title":
            "🎮 SCRIM THỨ 6 🎮",

        "description":
            "🎮 Tuần này có lịch SCRIM THỨ 6.",

        "question":
            "Bạn có tham gia SCRIM THỨ 6 không?",

        "join":
            "Có",

        "not_join":
            "Không",

        "emoji_join":
            "⚔️",

        "emoji_not_join":
            "❌",

        "join_status":
            SCRIM_JOIN,

        "not_join_status":
            SCRIM_NOT_JOIN,

        "pending_status":
            SCRIM_PENDING,
    },
}


# =========================================================
#              TẠO CONFIG SCRIM ĐỘNG
# =========================================================

def build_scrim_config(
    activity,
    so_tran,
    doi_thu_list
):
    """
    Tạo config Scrim động theo số trận và đối thủ.

    Ví dụ:

        !scrimthu5 1 Cửu Thiên
        !scrimthu5 2 Cửu Thiên
        !scrimthu5 2 Cửu Thiên, Phong Ưng

        !scrimthu6 1 Cửu Thiên
        !scrimthu6 2 Cửu Thiên
        !scrimthu6 2 Cửu Thiên, Phong Ưng

    Nếu chỉ nhập 1 đối thủ nhưng chọn 2 trận:

        !scrimthu5 2 Cửu Thiên

    => Trận 1: Cửu Thiên
       Trận 2: Cửu Thiên
    """

    # =====================================================
    # KIỂM TRA ACTIVITY
    # =====================================================

    base_config = ACTIVITY_CONFIG.get(activity)

    if base_config is None:
        raise ValueError(
            f"Activity không tồn tại: {activity}"
        )

    # =====================================================
    # PHẢI LÀ SCRIM
    # =====================================================

    if base_config.get("kind") != "scrim":
        raise ValueError(
            f"{activity} không phải Scrim."
        )

    # =====================================================
    # KIỂM TRA SỐ TRẬN
    # =====================================================

    try:
        so_tran = int(so_tran)

    except (TypeError, ValueError):
        raise ValueError(
            "Số trận Scrim phải là 1 hoặc 2."
        )

    if so_tran not in (1, 2):
        raise ValueError(
            "Số trận Scrim chỉ được là 1 hoặc 2."
        )

    # =====================================================
    # LÀM SẠCH ĐỐI THỦ
    # =====================================================

    if isinstance(doi_thu_list, str):
        doi_thu_list = doi_thu_list.split(",")

    doi_thu_list = [
        str(x).strip()
        for x in doi_thu_list
        if str(x).strip()
    ]

    # =====================================================
    # KIỂM TRA CÓ ĐỐI THỦ
    # =====================================================

    if not doi_thu_list:
        raise ValueError(
            "Bạn chưa nhập đối thủ."
        )

    # =====================================================
    # XỬ LÝ ĐỐI THỦ
    # =====================================================
    #
    # 1 trận:
    #
    #   !scrimthu5 1 Cửu Thiên
    #
    #   => Cửu Thiên
    #
    #
    # 2 trận + 1 đối thủ:
    #
    #   !scrimthu5 2 Cửu Thiên
    #
    #   => Cửu Thiên
    #      Cửu Thiên
    #
    #
    # 2 trận + 2 đối thủ:
    #
    #   !scrimthu5 2 Cửu Thiên, Phong Ưng
    #
    #   => Cửu Thiên
    #      Phong Ưng
    # =====================================================

    if len(doi_thu_list) == 1:

        doi_thu_list = (
            doi_thu_list * so_tran
        )

    elif len(doi_thu_list) != so_tran:

        raise ValueError(
            f"Bạn chọn {so_tran} trận "
            f"nhưng nhập "
            f"{len(doi_thu_list)} đối thủ."
        )

    # =====================================================
    # TÊN THỨ
    # =====================================================

    if activity == "scrimthu5":

        thu_text = "THỨ 5"

    elif activity == "scrimthu6":

        thu_text = "THỨ 6"

    else:

        thu_text = activity.upper()

    # =====================================================
    # TẠO TITLE + DESCRIPTION
    # =====================================================

    if so_tran == 1:

        tran_text = (
            f"1 TRẬN VS "
            f"{doi_thu_list[0].upper()}"
        )

        description = (
            f"🎮 Tuần này có lịch SCRIM "
            f"{thu_text} gồm 1 trận.\n\n"

            f"⚔️ Đối thủ: "
            f"**{doi_thu_list[0]}**\n\n"

            f"⚔️ Anh em đăng ký để đội hình "
            f"có thể sắp xếp đầy đủ người.\n\n"

            f"⏰ Hạn đăng ký: sau 72 giờ\n\n"

            f"🙏 MONG ANH EM SẮP XẾP THAM GIA!"
        )

    else:

        # =================================================
        # 2 TRẬN CÙNG ĐỐI THỦ
        # =================================================

        if (
            doi_thu_list[0].strip().lower()
            == doi_thu_list[1].strip().lower()
        ):

            tran_text = (
                f"2 TRẬN VS "
                f"{doi_thu_list[0].upper()}"
            )

        # =================================================
        # 2 TRẬN KHÁC ĐỐI THỦ
        # =================================================

        else:

            tran_text = (
                f"2 TRẬN VS "
                f"{doi_thu_list[0].upper()} - "
                f"{doi_thu_list[1].upper()}"
            )

        description = (
            f"🎮 Tuần này có lịch SCRIM "
            f"{thu_text} gồm 2 trận.\n\n"

            f"⚔️ Trận 1: "
            f"**{doi_thu_list[0]}**\n"

            f"⚔️ Trận 2: "
            f"**{doi_thu_list[1]}**\n\n"

            f"⚔️ Anh em đăng ký để đội hình "
            f"có thể sắp xếp đầy đủ người.\n\n"

            f"⏰ Hạn đăng ký: sau 72 giờ\n\n"

            f"🙏 MONG ANH EM SẮP XẾP THAM GIA!"
        )

    # =====================================================
    # COPY CONFIG GỐC
    # =====================================================

    new_config = dict(base_config)

    # =====================================================
    # THÔNG TIN SCRIM
    # =====================================================

    new_config["match_count"] = so_tran

    new_config["opponents"] = list(
        doi_thu_list
    )

    # =====================================================
    # TITLE
    # =====================================================

    new_config["title"] = (
        f"🎮 SCRIM "
        f"{thu_text} - "
        f"{tran_text} 🎮"
    )

    # =====================================================
    # DESCRIPTION
    # =====================================================

    new_config["description"] = description

    # =====================================================
    # GIỮ CÁC CONFIG KHÁC
    # =====================================================

    new_config["question"] = base_config.get(
        "question",
        "Bạn có tham gia Scrim không?"
    )

    # =====================================================
    # RETURN
    # =====================================================

    return new_config
    # =====================================================
    # COPY CONFIG GỐC
    #
    # Không sửa ACTIVITY_CONFIG gốc.
    # =====================================================

    new_config = dict(
        base_config
    )

    # =====================================================
    # THÔNG TIN SCRIM
    # =====================================================

    new_config["match_count"] = (
        so_tran
    )

    new_config["opponents"] = (
        doi_thu_list
    )

    # =====================================================
    # TITLE
    # =====================================================

    new_config["title"] = (

        f"🎮 SCRIM "
        f"{thu_text} - "
        f"{tran_text} 🎮"
    )

    # =====================================================
    # DESCRIPTION
    # =====================================================

    new_config["description"] = (
        description
    )

    # =====================================================
    # QUESTION
    # =====================================================

    new_config["question"] = (

        f"Bạn có tham gia SCRIM "
        f"{thu_text} "
        f"({so_tran} trận) không?"
    )

    # =====================================================
    # DEBUG
    # =====================================================

    print()
    print("=" * 60)
    print("🎮 BUILD SCRIM CONFIG")
    print("=" * 60)

    print(
        f"📌 Activity: {activity}"
    )

    print(
        f"📌 Sheet: {new_config['sheet']}"
    )

    print(
        f"📌 Số trận: {so_tran}"
    )

    print(
        f"📌 Đối thủ: {doi_thu_list}"
    )

    print(
        f"📌 Title: {new_config['title']}"
    )

    print("=" * 60)

    return new_config

# =========================================================
# ACTIVE POLLS
# =========================================================

active_polls = {}


# =========================================================
# CACHE
#
# PLAYER_CACHE:
# Discord ID -> thông tin thành viên
#
# ACTIVITY_CACHE:
# activity -> {
#     "rows": {
#         Discord ID: {
#             "row_number": int,
#             "status": str,
#             "ten_nv": str,
#             ...
#         }
#     }
# }
#
# POLL_ANSWER_CACHE:
# message_id -> {
#     answer_id: status
# }
# =========================================================

PLAYER_CACHE = {}

ACTIVITY_CACHE = {}

POLL_ANSWER_CACHE = {}

# =========================================================
# GOOGLE OBJECT / WORKSHEET CACHE
# =========================================================
# These objects are intentionally reused for the lifetime of the bot.
# Looking up the worksheet and checking A1:H1 on every vote creates extra
# Sheets API read requests and is a major cause of HTTP 429.
GOOGLE_SPREADSHEET = None
PLAYER_WORKSHEET_CACHE = None
WORKSHEET_CACHE = {}
HEADERS_CHECKED = set()
GOOGLE_CLIENT_LOCK = threading.RLock()


# =========================================================
# LOCK
#
# Tránh 2 vote cùng lúc ghi đè nhau.
# =========================================================

ACTIVITY_LOCKS = {}


def get_activity_lock(activity):

    if activity not in ACTIVITY_LOCKS:

        ACTIVITY_LOCKS[activity] = asyncio.Lock()

    return ACTIVITY_LOCKS[activity]


# =========================================================
# LOAD STATE
# =========================================================

def load_state():

    global active_polls

    active_polls = {}

    if not os.path.exists(STATE_FILE):

        print(
            "📌 Chưa có bangchien_state.json."
        )

        return

    try:

        if os.path.getsize(STATE_FILE) == 0:

            print(
                "⚠️ bangchien_state.json đang trống."
            )

            return

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        polls = data.get("polls")

        if isinstance(polls, dict):

            for message_id, poll_data in polls.items():

                try:

                    message_id = str(
                        int(message_id)
                    )

                    activity = poll_data.get(
                        "activity"
                    )

                    if activity in ACTIVITY_CONFIG:

                        active_polls[message_id] = {
                            "activity": activity
                        }

                except Exception:

                    continue

        else:

            old_poll_id = data.get(
                "poll_message_id"
            )

            old_poll_type = data.get(
                "poll_type"
            )

            if (
                old_poll_id is not None
                and old_poll_type in (1, 2)
            ):

                old_activity = (
                    "bangchien1"
                    if int(old_poll_type) == 1
                    else "bangchien2"
                )

                active_polls[
                    str(int(old_poll_id))
                ] = {
                    "activity": old_activity
                }

        print(
            f"✅ Đã khôi phục "
            f"{len(active_polls)} Poll."
        )

        for message_id, poll_data in active_polls.items():

            print(
                f"🗳️ Poll {message_id} -> "
                f"{poll_data['activity']}"
            )

    except json.JSONDecodeError:

        print(
            "⚠️ bangchien_state.json bị hỏng."
        )

    except Exception as e:

        print(
            f"⚠️ Không đọc được state file: {e}"
        )


# =========================================================
# SAVE STATE
# =========================================================

def save_state():

    try:

        with open(
            STATE_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                {
                    "polls": active_polls
                },
                f,
                ensure_ascii=False,
                indent=4
            )

        print(
            f"💾 Đã lưu {len(active_polls)} Poll."
        )

    except Exception as e:

        print(
            f"⚠️ Không lưu được state: {e}"
        )


# =========================================================
# REGISTER POLL
# =========================================================

def register_poll(
    message_id,
    activity
):

    active_polls[
        str(int(message_id))
    ] = {
        "activity": activity
    }

    save_state()

    print(
        f"💾 Poll {message_id} -> {activity}"
    )


# =========================================================
# REMOVE POLL
# =========================================================

def remove_poll(
    message_id
):

    message_key = str(
        int(message_id)
    )

    if message_key in active_polls:

        del active_polls[
            message_key
        ]

        POLL_ANSWER_CACHE.pop(
            int(message_key),
            None
        )

        save_state()

        print(
            f"🗑️ Đã xóa Poll state: {message_id}"
        )


# =========================================================
# GET POLL ACTIVITY
# =========================================================

def get_poll_activity(
    message_id
):

    data = active_polls.get(
        str(int(message_id))
    )

    if not data:
        return None

    return data.get("activity")


# =========================================================
# TIME
# =========================================================

def now_string():

    return datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )


# =========================================================
# GOOGLE CONNECT
# =========================================================

def connect_google():
    """Return one shared gspread Spreadsheet object.

    The old code authenticated + opened the spreadsheet every time a vote
    arrived. That is unnecessary and creates extra Google API traffic.
    """
    global GOOGLE_SPREADSHEET

    if GOOGLE_SPREADSHEET is not None:
        return GOOGLE_SPREADSHEET

    with GOOGLE_CLIENT_LOCK:
        if GOOGLE_SPREADSHEET is not None:
            return GOOGLE_SPREADSHEET

        print("🔄 Đang kết nối Google Sheets...")

        if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
            raise FileNotFoundError(
                "Không tìm thấy credentials.json:\n"
                f"{GOOGLE_CREDENTIALS_FILE}"
            )

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            GOOGLE_CREDENTIALS_FILE,
            scope
        )

        client = gspread.authorize(credentials)
        GOOGLE_SPREADSHEET = client.open(SPREADSHEET_NAME)

        print(f"✅ Đã kết nối Google Sheet: {SPREADSHEET_NAME}")
        return GOOGLE_SPREADSHEET

# =========================================================
# GET PLAYER SHEET
# =========================================================

def get_player_sheet():
    """Return cached player worksheet; no repeated worksheet lookup."""
    global PLAYER_WORKSHEET_CACHE
    if PLAYER_WORKSHEET_CACHE is not None:
        return PLAYER_WORKSHEET_CACHE
    try:
        worksheet = connect_google().worksheet(PLAYER_WORKSHEET_NAME)
        PLAYER_WORKSHEET_CACHE = worksheet
        return worksheet
    except gspread.WorksheetNotFound:
        print(f"❌ Không tìm thấy tab '{PLAYER_WORKSHEET_NAME}'")
        return None
    except Exception as e:
        print(f"❌ Lỗi lấy Sheet thành viên: {e}")
        return None

# =========================================================
# GET ACTIVITY SHEET
# =========================================================

def get_activity_sheet(worksheet_name):
    """Return a cached worksheet object and check headers only once."""
    if worksheet_name in WORKSHEET_CACHE:
        return WORKSHEET_CACHE[worksheet_name]

    spreadsheet = connect_google()

    try:
        worksheet = get_worksheet_with_retry(spreadsheet, worksheet_name)
        ensure_activity_headers(worksheet)
        WORKSHEET_CACHE[worksheet_name] = worksheet
        return worksheet

    except gspread.WorksheetNotFound:
        print(f"⚠️ Chưa có tab '{worksheet_name}'.")
        print(f"🔨 Đang tạo tab '{worksheet_name}'...")

        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=8
        )
        worksheet.update("A1:H1", [WAR_HEADERS])
        HEADERS_CHECKED.add(worksheet_name)
        WORKSHEET_CACHE[worksheet_name] = worksheet

        print(f"✅ Đã tạo tab '{worksheet_name}'.")
        return worksheet

# =========================================================
# GET SHEETS
# =========================================================

def get_war_sheet():

    return get_activity_sheet(
        WAR_WORKSHEET_NAME
    )


def get_scrim_thu5_sheet():

    return get_activity_sheet(
        SCRIM_THU5_WORKSHEET_NAME
    )


def get_scrim_thu6_sheet():

    return get_activity_sheet(
        SCRIM_THU6_WORKSHEET_NAME
    )


# =========================================================
# HEADER
# =========================================================

def ensure_activity_headers(worksheet):
    """Check/update headers once per worksheet, never once per vote."""
    name = getattr(worksheet, "title", None)
    if name in HEADERS_CHECKED:
        return

    try:
        current = google_retry(
            worksheet.get,
            "A1:H1",
            max_retries=7,
            base_delay=3,
        )
        current = current[0] if current else []

        if current != WAR_HEADERS:
            worksheet.update("A1:H1", [WAR_HEADERS])
            print(f"✅ Đã sửa header A1:H1 tab '{worksheet.title}'.")

        HEADERS_CHECKED.add(name)
    except Exception as e:
        print(f"⚠️ Không kiểm tra được header '{getattr(worksheet, 'title', '?')}': {e}")

# =========================================================
# GET ACTIVITY RECORDS
#
# CHỈ DÙNG KHI:
# - startup cache
# - dongbo
# - bangchienstatus
# - restore
#
# KHÔNG DÙNG CHO MỖI VOTE NỮA.
# =========================================================

def get_activity_records(
    worksheet
):

    if worksheet is None:
        return []

    try:

        values = google_retry(
            worksheet.get,
            "A1:H",
            max_retries=7,
            base_delay=3,
        )

    except Exception as e:

        print(
            f"❌ Không đọc được A:H "
            f"'{worksheet.title}': {e}"
        )

        return []

    if not values:
        return []

    records = []

    for row in values[1:]:

        row = list(row)

        while len(row) < len(WAR_HEADERS):

            row.append("")

        row = row[:len(WAR_HEADERS)]

        if not any(
            str(value).strip()
            for value in row
        ):

            continue

        records.append(
            dict(
                zip(
                    WAR_HEADERS,
                    row
                )
            )
        )

    return records


# =========================================================
# GET PLAYER RECORDS
#
# Dùng để tạo PLAYER_CACHE.
# =========================================================

def get_player_records():

    worksheet = get_player_sheet()

    if worksheet is None:
        return []

    try:

        values = google_retry(
            worksheet.get_all_values,
            max_retries=7,
            base_delay=3,
        )

    except Exception as e:

        print(
            f"❌ Không đọc được Sheet thành viên: {e}"
        )

        return []

    if not values:
        return []

    headers = values[0]

    header_indexes = {}

    for index, header in enumerate(headers):

        header = str(header).strip()

        if not header:
            continue

        if header not in header_indexes:

            header_indexes[header] = index

    records = []

    for row in values[1:]:

        record = {}

        has_data = False

        for header, index in header_indexes.items():

            value = ""

            if index < len(row):

                value = row[index]

            value = str(value).strip()

            if value:

                has_data = True

            record[header] = value

        if has_data:

            records.append(record)

    return records


# =========================================================
# FIRST VALUE
# =========================================================

def get_first_value(
    row,
    *keys
):

    for key in keys:

        value = row.get(key)

        if value is not None:

            value = str(value).strip()

            if value:

                return value

    return ""


# =========================================================
# BUILD PLAYER CACHE
#
# GOOGLE READ:
# 1 lần khi gọi hàm này.
# =========================================================

def refresh_player_cache():

    global PLAYER_CACHE

    print()
    print("=" * 60)
    print("🔄 ĐANG LOAD PLAYER CACHE")
    print("=" * 60)

    records = get_player_records()
    new_cache = {}

    for row in records:

        discord_name = get_first_value(
            row,
            "Tên Discord",
            "Discord",
            "Discord Name",
            "Username",
            "Tài khoản Discord"
        )

        # Sheet thành viên có thể CHỈ lưu username Discord.
        # Không được bỏ qua dòng chỉ vì thiếu Discord ID.
        if not discord_name:
            continue

        discord_id = get_first_value(
            row,
            "ID discord",
            "Discord ID",
            "User ID",
            "ID"
        )

        ten_nv = get_first_value(
            row,
            "Tên Igame",
            "Tên nhân vật",
            "Tên NV",
            "Tên"
        )

        mon_phai = get_first_value(
            row,
            "Class",
            "Môn phái",
            "Môn Phái"
        )

        # Nếu Sheet không có ID, dùng username làm khóa ổn định.
        # Khi vote thật, get_player_info() sẽ ưu tiên member.id nếu có.
        effective_id = discord_id or discord_name

        player = {
            "discord_id": str(effective_id).strip(),
            "discord": str(discord_name).strip(),
            "ten_nv": str(ten_nv).strip(),
            "mon_phai": str(mon_phai).strip(),
        }

        # Luôn index theo username.
        new_cache[str(discord_name).strip().lower()] = player

        # Nếu Sheet có ID thì index thêm theo ID.
        if discord_id:
            new_cache[str(discord_id).strip().lower()] = player

    PLAYER_CACHE = new_cache

    print(
        f"👥 PLAYER CACHE: {len(PLAYER_CACHE)} khóa / "
        f"{len({id(v) for v in PLAYER_CACHE.values()})} thành viên"
    )

    print("=" * 60)
    return PLAYER_CACHE


# =========================================================
# GET PLAYER FROM CACHE
# =========================================================

def get_cached_player(
    discord_id
):

    if discord_id is None:
        return None

    key = str(
        discord_id
    ).strip().lower()

    return PLAYER_CACHE.get(
        key
    )


# =========================================================
# GET PLAYER INFO
#
# KHÔNG ĐỌC GOOGLE.
# Chỉ đọc RAM CACHE.
# =========================================================

def get_player_info(
    discord_username,
    member=None
):

    usernames = []

    if discord_username:

        usernames.append(
            str(discord_username).strip()
        )

    if member is not None:

        for attr in (
            "name",
            "display_name",
            "global_name"
        ):

            value = getattr(
                member,
                attr,
                None
            )

            if value:

                usernames.append(
                    str(value).strip()
                )

        user_id = getattr(
            member,
            "id",
            None
        )

        if user_id:

            usernames.append(
                str(user_id)
            )

    usernames = list(
        dict.fromkeys(
            x for x in usernames
            if x
        )
    )

    for username in usernames:

        player = get_cached_player(
            username
        )

        if player is not None:

            return player

    return None


# =========================================================
# GET ALL PLAYERS
#
# DÙNG CACHE.
#
# Nếu force_refresh=True:
# đọc Google 1 lần và refresh cache.
# =========================================================

def get_all_players(
    force_refresh=False
):

    if force_refresh or not PLAYER_CACHE:
        refresh_player_cache()

    players = []
    seen = set()

    for player in PLAYER_CACHE.values():
        identity = (
            str(player.get("discord", "")).strip().lower(),
            str(player.get("ten_nv", "")).strip().lower(),
        )

        if identity in seen:
            continue

        seen.add(identity)
        players.append(dict(player))

    print(
        f"👥 Tổng thành viên trong cache: {len(players)}"
    )

    return players


# =========================================================
# BUILD ACTIVITY CACHE
#
# GOOGLE READ:
# 1 lần / activity.
# =========================================================

def refresh_activity_cache(activity, worksheet=None):
    """Read one activity sheet once and index rows by BOTH Discord ID and username."""
    config = ACTIVITY_CONFIG.get(activity)
    if config is None:
        return {}

    if worksheet is None:
        worksheet = get_activity_sheet(config["sheet"])
    if worksheet is None:
        return {}

    print(f"🔄 Load cache: {activity}")
    records = get_activity_records(worksheet)
    rows = {}

    for row_number, row in enumerate(records, start=2):
        discord_id = str(row.get("Discord ID", "")).strip()
        discord_name = str(row.get("Discord", "")).strip()

        if not discord_id and not discord_name:
            continue

        row_data = {
            "row_number": row_number,
            "discord_id": discord_id or discord_name,
            "discord": discord_name,
            "ten_nv": str(row.get("Tên nhân vật", "")).strip(),
            "mon_phai": str(row.get("Môn phái", "")).strip(),
            "status": str(row.get("Trạng thái", "")).strip(),
            "time": str(row.get("Thời gian đăng ký", "")).strip(),
            "register": str(row.get("Người đăng ký", "")).strip(),
        }

        # Index bằng ID nếu có.
        if discord_id:
            rows[discord_id.lower()] = row_data

        # Quan trọng: Sheet có thể chỉ có username.
        if discord_name:
            rows[discord_name.lower()] = row_data

    ACTIVITY_CACHE[activity] = rows
    activity_row_cache[activity] = {
        key: value["row_number"] for key, value in rows.items()
    }

    print(f"📄 {activity}: {len(records)} dòng / {len(rows)} khóa cache")
    return rows

# =========================================================
# GET ACTIVITY CACHE
# =========================================================

def get_cached_activity_row(
    activity,
    discord_id
):

    rows = ACTIVITY_CACHE.get(
        activity,
        {}
    )

    return rows.get(
        str(discord_id).strip().lower()
    )


# =========================================================
# COPY FORMAT
# =========================================================

def copy_players_format(
    source_worksheet,
    target_worksheet,
    player_count
):

    if player_count <= 0:
        return True

    try:

        spreadsheet = target_worksheet.spreadsheet

        source_sheet_id = source_worksheet.id

        target_sheet_id = target_worksheet.id

        # -------------------------------------------------
        # SOURCE A:D -> TARGET A:D
        # -------------------------------------------------

        request_source_to_target = {

            "copyPaste": {

                "source": {

                    "sheetId":
                        source_sheet_id,

                    "startRowIndex":
                        1,

                    "endRowIndex":
                        player_count + 1,

                    "startColumnIndex":
                        0,

                    "endColumnIndex":
                        4
                },

                "destination": {

                    "sheetId":
                        target_sheet_id,

                    "startRowIndex":
                        1,

                    "endRowIndex":
                        player_count + 1,

                    "startColumnIndex":
                        0,

                    "endColumnIndex":
                        4
                },

                "pasteType":
                    "PASTE_FORMAT",

                "pasteOrientation":
                    "NORMAL"
            }
        }

        # -------------------------------------------------
        # TARGET A:D -> TARGET E:H
        # -------------------------------------------------

        request_a_to_e = {

            "copyPaste": {

                "source": {

                    "sheetId":
                        target_sheet_id,

                    "startRowIndex":
                        1,

                    "endRowIndex":
                        player_count + 1,

                    "startColumnIndex":
                        0,

                    "endColumnIndex":
                        4
                },

                "destination": {

                    "sheetId":
                        target_sheet_id,

                    "startRowIndex":
                        1,

                    "endRowIndex":
                        player_count + 1,

                    "startColumnIndex":
                        4,

                    "endColumnIndex":
                        8
                },

                "pasteType":
                    "PASTE_FORMAT",

                "pasteOrientation":
                    "NORMAL"
            }
        }

        spreadsheet.batch_update({
            "requests": [
                request_source_to_target,
                request_a_to_e
            ]
        })

        print(
            f"🎨 Đã copy format "
            f"A2:D{player_count + 1} -> A:D"
        )

        print(
            f"🎨 Đã copy format "
            f"A2:D{player_count + 1} -> E:H"
        )

        print(
            "🔒 Cột I trở đi không bị thay đổi."
        )

        return True

    except Exception as e:

        print(
            f"❌ Không copy được format: {e}"
        )

        return False


# =========================================================
# GET SHEET ACTIVITY
# =========================================================

def get_sheet_for_activity(
    activity
):

    config = ACTIVITY_CONFIG.get(
        activity
    )

    if config is None:

        raise ValueError(
            f"Activity không tồn tại: {activity}"
        )

    return get_activity_sheet(
        config["sheet"]
    )


# =========================================================
# UPDATE CACHE SAU KHI GHI
# =========================================================

def update_activity_cache_row(
    activity,
    discord_id,
    status,
    time_text,
    register
):

    row = get_cached_activity_row(
        activity,
        discord_id
    )

    if row is None:
        return

    row["status"] = status
    row["time"] = time_text
    row["register"] = register


# =========================================================
# UPDATE STATUS
#
# QUAN TRỌNG:
#
# KHÔNG ĐỌC GOOGLE ĐỂ TÌM DÒNG.
# Tìm trực tiếp từ ACTIVITY_CACHE.
# =========================================================

def update_activity_status(discord_username, status, member, activity):
    """Update one user's F:H using RAM caches; no Google read on vote."""
    config = ACTIVITY_CONFIG.get(activity)
    if config is None:
        return False, "❌ Activity không hợp lệ."

    player = get_player_info(str(discord_username).strip(), member)
    if player is None:
        return False, "❌ Không tìm thấy thông tin nhân vật của bạn trong hệ thống."

    player_discord_id = str(player["discord_id"]).strip()
    row = get_cached_activity_row(activity, player_discord_id)

    if row is None and member is not None:
        row = get_cached_activity_row(activity, str(getattr(member, "name", "")).strip())

    # Extremely rare: a member was added after the last sync. This is a WRITE,
    # not a READ. The normal vote path still does not consume read quota.
    if row is None:
        worksheet = get_sheet_for_activity(activity)
        if worksheet is None:
            return False, "❌ Không lấy được Sheet."

        rows = ACTIVITY_CACHE.setdefault(activity, {})
        row_number = max(
            [r.get("row_number", 1) for r in rows.values()] or [1]
        ) + 1

        google_retry(
            worksheet.append_row,
            [
                "",
                player["discord_id"],
                player["discord"],
                player["ten_nv"],
                player["mon_phai"],
                config["pending_status"],
                "",
                "",
            ],
            table_range="A:H",
            max_retries=7,
            base_delay=3,
        )

        row = {
            "row_number": row_number,
            "discord_id": player["discord_id"],
            "discord": player["discord"],
            "ten_nv": player["ten_nv"],
            "mon_phai": player["mon_phai"],
            "status": config["pending_status"],
            "time": "",
            "register": "",
        }
        rows[player_discord_id.lower()] = row
        activity_row_cache.setdefault(activity, {})[
            player_discord_id.lower()
        ] = row_number

        if player.get("discord"):
            rows[str(player["discord"]).strip().lower()] = row
            activity_row_cache.setdefault(activity, {})[
                str(player["discord"]).strip().lower()
            ] = row_number

    row_number = row["row_number"]
    ten_nv = str(row.get("ten_nv") or player.get("ten_nv") or "").strip()
    if not ten_nv:
        return False, "❌ Bạn chưa có tên nhân vật."

    current_status = str(row.get("status", "")).strip()
    now = now_string()
    discord_display = str(member or discord_username)

    # Avoid a write if Discord sends a duplicate event with the same status.
    if current_status == status and str(row.get("register", "")).strip() == discord_display:
        return True, f"⏭️ Trạng thái đã là **{status}**, không cần cập nhật."

    worksheet = get_sheet_for_activity(activity)
    if worksheet is None:
        return False, "❌ Không lấy được Sheet."

    google_retry(
        worksheet.update,
        values=[[status, now, discord_display]],
        range_name=f"F{row_number}:H{row_number}",
        max_retries=7,
        base_delay=3,
    )

    update_activity_cache_row(
        activity,
        player_discord_id,
        status,
        now,
        discord_display,
    )

    if status == config["join_status"]:
        title = "ĐÁNH BANG CHIẾN" if config["kind"] == "bangchien" else "THAM GIA SCRIM"
        message = (
            f"✅ **Đã ghi nhận bạn {title}!**\n\n"
            f"👤 Nhân vật: **{ten_nv}**\n"
            f"⚔️ Trạng thái: **{status}**\n"
            f"🕒 Thời gian: **{now}**"
        )
    elif status == config["not_join_status"]:
        title = "KHÔNG ĐÁNH BANG CHIẾN" if config["kind"] == "bangchien" else "KHÔNG THAM GIA SCRIM"
        message = (
            f"❌ **Đã ghi nhận bạn {title}!**\n\n"
            f"👤 Nhân vật: **{ten_nv}**\n"
            f"⚔️ Trạng thái: **{status}**\n"
            f"🕒 Thời gian: **{now}**"
        )
    else:
        message = (
            f"🔄 **Đã cập nhật trạng thái!**\n\n"
            f"👤 Nhân vật: **{ten_nv}**\n"
            f"⚔️ Trạng thái: **{status}**\n"
            f"🕒 Thời gian: **{now}**"
        )

    return True, message

# =========================================================
# SET USER PENDING
#
# KHÔNG ĐỌC TOÀN BỘ SHEET.
# =========================================================

def set_user_pending_sync(user, activity):
    """Set F:H to pending using only the activity row cache."""
    try:
        user_id = str(user.id).strip()
        config = ACTIVITY_CONFIG.get(activity)
        if config is None:
            return False

        row = get_cached_activity_row(activity, user_id)
        if row is None:
            row = get_cached_activity_row(
                activity,
                str(getattr(user, "name", "")).strip()
            )
        if row is None:
            # Do not fall back to get_all_values() here. A missing cache means
            # the startup/sync cache is stale; refresh the activity once.
            refresh_activity_cache(activity)
            row = get_cached_activity_row(activity, user_id)
            if row is None:
                row = get_cached_activity_row(
                    activity,
                    str(getattr(user, "name", "")).strip()
                )

        if row is None:
            print(f"❌ Không tìm thấy user {user} trong cache {activity}")
            return False

        row_number = row["row_number"]
        worksheet = get_sheet_for_activity(activity)
        if worksheet is None:
            return False

        google_retry(
            worksheet.update,
            values=[[config["pending_status"], "", ""]],
            range_name=f"F{row_number}:H{row_number}",
            max_retries=7,
            base_delay=3,
        )

        row["status"] = config["pending_status"]
        row["time"] = ""
        row["register"] = ""

        return True

    except Exception as e:
        print(f"❌ Lỗi set_user_pending_sync: {e}")
        return False

# =========================================================
# SYNC ACTIVITY SHEET
#
# Lệnh này được phép đọc Google.
#
# Sau khi sync xong:
# - refresh PLAYER_CACHE
# - refresh ACTIVITY_CACHE
# =========================================================

def sync_activity_sheet(activity, reset_status=False):
    """Full manual sync. This is intentionally read-heavy but only runs on
    !bangchien*, !scrim*, !dongbo or startup recovery, never on each vote.
    """
    config = ACTIVITY_CONFIG.get(activity)
    if config is None:
        raise ValueError(f"Activity không hợp lệ: {activity}")

    print("\n" + "=" * 60)
    print(f"🔄 ĐỒNG BỘ -> {config['sheet']}")
    print("=" * 60)

    refresh_player_cache()
    players = get_all_players()
    if not players:
        return {"total": 0, "new": 0, "updated": 0, "format_success": 0, "format_failed": 0}

    worksheet = get_sheet_for_activity(activity)
    records = get_activity_records(worksheet)

    existing_rows = {}
    for row_index, row in enumerate(records, start=2):
        discord_id = str(row.get("Discord ID", "")).strip()
        if discord_id:
            existing_rows[discord_id.lower()] = (row_index, row)

    new_count = sum(
        1 for p in players if str(p["discord_id"]).strip().lower() not in existing_rows
    )
    update_count = len(players) - new_count

    final_rows = []
    for index, player in enumerate(players, start=1):
        discord_id = str(player["discord_id"]).strip()
        old_status = config["pending_status"]
        old_time = ""
        old_register = ""

        if not reset_status and discord_id.lower() in existing_rows:
            _, old_row = existing_rows[discord_id.lower()]
            old_status = str(old_row.get("Trạng thái", old_status)).strip() or old_status
            old_time = str(old_row.get("Thời gian đăng ký", "")).strip()
            old_register = str(old_row.get("Người đăng ký", "")).strip()

        final_rows.append([
            index,
            discord_id,
            player["discord"],
            player["ten_nv"],
            player["mon_phai"],
            config["pending_status"] if reset_status else old_status,
            "" if reset_status else old_time,
            "" if reset_status else old_register,
        ])

    old_last_row = len(records) + 1
    if records:
        google_retry(
            worksheet.batch_clear,
            [f"A2:H{old_last_row}"],
            max_retries=7,
            base_delay=3,
        )

    if final_rows:
        google_retry(
            worksheet.update,
            values=final_rows,
            range_name=f"A2:H{len(final_rows)+1}",
            max_retries=7,
            base_delay=3,
        )

    # STT is already included in column A of final_rows.

    source_worksheet = get_player_sheet()
    format_success = 0
    format_failed = 0
    if source_worksheet is not None:
        if copy_players_format(source_worksheet, worksheet, len(players)):
            format_success = len(players)
        else:
            format_failed = len(players)
    else:
        format_failed = len(players)

    # Build cache from the data we already have instead of reading A:H again.
    rows = {}
    row_cache = {}
    for idx, row in enumerate(final_rows, start=2):
        discord_id = str(row[1]).strip()
        if not discord_id:
            continue
        key = discord_id.lower()
        rows[key] = {
            "row_number": idx,
            "discord_id": discord_id,
            "discord": str(row[2]).strip(),
            "ten_nv": str(row[3]).strip(),
            "mon_phai": str(row[4]).strip(),
            "status": str(row[5]).strip(),
            "time": str(row[6]).strip(),
            "register": str(row[7]).strip(),
        }
        row_cache[key] = idx

    ACTIVITY_CACHE[activity] = rows
    activity_row_cache[activity] = row_cache

    print(f"👥 Tổng: {len(players)}")
    print(f"🆕 Mới: {new_count}")
    print(f"🔄 Đã tồn tại: {update_count}")
    print(f"🎨 Format OK: {format_success}")
    print(f"⚠️ Format lỗi: {format_failed}")
    print("📌 A:H được đồng bộ. I trở đi giữ nguyên.")

    return {
        "total": len(players),
        "new": new_count,
        "updated": update_count,
        "format_success": format_success,
        "format_failed": format_failed,
    }

# =========================================================
# CREATE POLL
# =========================================================

def create_activity_poll(
    activity,
    config=None
):

    if config is None:
        config = ACTIVITY_CONFIG.get(
            activity
        )

    if config is None:
        raise ValueError(
            f"Activity không tồn tại: {activity}"
        )

    poll = discord.Poll(
        question=config["question"],
        duration=timedelta(hours=72),
        multiple=False
    )

    poll.add_answer(
        text=config["join"],
        emoji=config["emoji_join"]
    )

    poll.add_answer(
        text=config["not_join"],
        emoji=config["emoji_not_join"]
    )

    return poll


# =========================================================
# POLL CONTENT
# =========================================================

def create_activity_content(
    activity,
    config=None
):

    if config is None:
        config = ACTIVITY_CONFIG.get(
            activity
        )

    if config is None:
        raise ValueError(
            f"Activity không tồn tại: {activity}"
        )

    return (
        f"## {config['title']}\n\n"
        f"{config['description']}"
    )

# =========================================================
# CACHE POLL ANSWERS
#
# message_id -> answer_id -> status
#
# Ví dụ:
#
# {
#     "123456": {
#         0: "⚔️ ĐÁNH BANG CHIẾN",
#         1: "❌ KHÔNG ĐÁNH"
#     }
# }
# =========================================================

def cache_poll_answers(message_id, poll, activity):
    try:
        if message_id is None or poll is None:
            return False

        config = ACTIVITY_CONFIG.get(activity)
        if config is None:
            return False

        answer_cache = {}
        for answer in getattr(poll, "answers", []) or []:
            answer_id = getattr(answer, "id", None)
            text = str(getattr(answer, "text", "")).strip()
            if answer_id is None:
                continue

            if text == config.get("join"):
                status = config.get("join_status")
            elif text == config.get("not_join"):
                status = config.get("not_join_status")
            else:
                continue

            answer_cache[int(answer_id)] = status

        poll_answer_cache[int(message_id)] = {
            "activity": activity,
            "answers": answer_cache,
        }
        print(f"🧠 Poll {message_id}: answer cache = {answer_cache}")
        return bool(answer_cache)

    except Exception as e:
        print(f"❌ Lỗi cache_poll_answers: {e}")
        return False

# =========================================================
# GET STATUS FROM ANSWER CACHE
# =========================================================

def get_cached_vote_status(
    message_id,
    answer_id
):

    try:

        message_cache = poll_answer_cache.get(
            int(message_id)
        )

        if not message_cache:
            return None

        answers = message_cache.get(
            "answers",
            {}
        )

        return answers.get(
            int(answer_id)
        )

    except Exception as e:

        print(
            f"❌ Lỗi get_cached_vote_status: {e}"
        )

        return None


# =========================================================
# COG BANG CHIEN
# =========================================================

class BangChien(commands.Cog):

    def __init__(
        self,
        bot
    ):

        self.bot = bot

        # =================================================
        # LOAD STATE
        # =================================================

        load_state()

        # =================================================
        # CHỐNG RESTORE NHIỀU LẦN
        # =================================================

        self._restore_votes_done = False

        # =================================================
        # CHỐNG READY NHIỀU LẦN
        # =================================================

        self._ready_done = False

    # =====================================================
    # CHECK QUYỀN
    # =====================================================

    async def check_allowed_user(
        self,
        ctx
    ):

        try:

            if is_allowed_user(
                ctx.author
            ):

                print()
                print(
                    "✅ USER ĐƯỢC PHÉP"
                )

                print(
                    f"👤 User: {ctx.author}"
                )

                print(
                    f"🆔 Discord ID: "
                    f"{ctx.author.id}"
                )

                return True

            print()
            print(
                "🚫 USER KHÔNG ĐƯỢC PHÉP"
            )

            print(
                f"👤 User: {ctx.author}"
            )

            print(
                f"🆔 Discord ID: "
                f"{ctx.author.id}"
            )

            await ctx.send(
                "❌ **Bạn không có quyền sử dụng lệnh này.**",
                delete_after=5
            )

            return False

        except Exception as e:

            print(
                f"❌ Lỗi kiểm tra quyền: {e}"
            )

            await ctx.send(
                "❌ Không thể kiểm tra quyền sử dụng lệnh.",
                delete_after=5
            )

            return False

    # =====================================================
    # READY
    # =====================================================

    @commands.Cog.listener()
    async def on_ready(
        self
    ):

        if self._ready_done:

            return

        self._ready_done = True

        print("=" * 60)

        print(
            "⚔️ Module Bang Chiến / Scrim đã sẵn sàng"
        )

        print(
            f"🗳️ Poll đang theo dõi: "
            f"{len(active_polls)}"
        )

        print(
            f"🔔 Poll Intent: "
            f"{getattr(self.bot.intents, 'polls', False)}"
        )

        print(
            f"💬 Message Content Intent: "
            f"{getattr(self.bot.intents, 'message_content', False)}"
        )

        for message_id, poll_data in active_polls.items():

            print(
                f"   {message_id} -> "
                f"{poll_data['activity']}"
            )

        print("=" * 60)

        # =================================================
        # LOAD PLAYER CACHE
        #
        # CHỈ 1 LẦN KHI BOT START.
        # =================================================

        try:

            await asyncio.to_thread(
                refresh_player_cache
            )

        except Exception as e:

            print(
                f"⚠️ Không load được PLAYER CACHE: {e}"
            )

        # =================================================
        # RESTORE TOÀN BỘ VOTE
        #
        # CHỈ 1 LẦN.
        # =================================================

        if self._restore_votes_done:

            return

        self._restore_votes_done = True

        try:

            await restore_active_poll_votes(
                self.bot
            )

        except Exception as e:

            print(
                f"❌ Lỗi restore vote: {e}"
            )

        print()

        print(
            "👁️ BOT ĐANG THEO DÕI POLL."
        )

    # =====================================================
    # RAW POLL ADD
    #
    # KHÔNG ĐỌC TOÀN BỘ POLL.
    # KHÔNG answer.voters().
    # =====================================================

    @commands.Cog.listener()
    async def on_raw_poll_vote_add(
        self,
        payload
    ):

        print()
        print(
            "🔥 RAW POLL VOTE ADD"
        )

        message_id = getattr(
            payload,
            "message_id",
            None
        )

        user_id = getattr(
            payload,
            "user_id",
            None
        )

        answer_id = getattr(
            payload,
            "answer_id",
            None
        )

        print(
            f"🆔 Message ID: {message_id}"
        )

        print(
            f"👤 User ID: {user_id}"
        )

        print(
            f"🗳️ Answer ID: {answer_id}"
        )

        await self._handle_raw_poll_event(
            payload,
            "ADD"
        )

    # =====================================================
    # RAW POLL REMOVE
    #
    # KHÔNG ĐỌC TOÀN BỘ POLL.
    # =====================================================

    @commands.Cog.listener()
    async def on_raw_poll_vote_remove(
        self,
        payload
    ):

        print()
        print(
            "🔥 RAW POLL VOTE REMOVE"
        )

        message_id = getattr(
            payload,
            "message_id",
            None
        )

        user_id = getattr(
            payload,
            "user_id",
            None
        )

        answer_id = getattr(
            payload,
            "answer_id",
            None
        )

        print(
            f"🆔 Message ID: {message_id}"
        )

        print(
            f"👤 User ID: {user_id}"
        )

        print(
            f"🗳️ Answer ID: {answer_id}"
        )

        await self._handle_raw_poll_event(
            payload,
            "REMOVE"
        )

    # =====================================================
    # HANDLE RAW EVENT
    #
    # SAU START:
    #
    # ADD:
    #   answer_id -> cache -> update 1 user
    #
    # REMOVE:
    #   user -> PENDING
    #
    # KHÔNG FETCH POLL.
    # KHÔNG READ VOTERS.
    # =====================================================

    async def _handle_raw_poll_event(
        self,
        payload,
        event_type
    ):

        try:

            message_id = getattr(
                payload,
                "message_id",
                None
            )

            user_id = getattr(
                payload,
                "user_id",
                None
            )

            answer_id = getattr(
                payload,
                "answer_id",
                None
            )

            if (
                message_id is None
                or user_id is None
            ):

                return

            activity = get_poll_activity(
                message_id
            )

            if activity is None:

                print(
                    f"📌 Poll {message_id} "
                    f"không nằm trong active_polls."
                )

                return

            # =================================================
            # USER
            # =================================================

            user = self.bot.get_user(
                int(user_id)
            )

            if user is None:

                try:

                    user = await self.bot.fetch_user(
                        int(user_id)
                    )

                except Exception as e:

                    print(
                        f"❌ Không lấy được user "
                        f"{user_id}: {e}"
                    )

                    return

            # =================================================
            # LOCK ACTIVITY
            # =================================================

            lock = get_activity_lock(
                activity
            )

            async with lock:

                # =============================================
                # ADD
                # =============================================

                if event_type == "ADD":

                    if answer_id is None:

                        print(
                            "⚠️ ADD nhưng không có answer_id."
                        )

                        return

                    status = get_cached_vote_status(
                        message_id,
                        answer_id
                    )

                    # =================================================
                    # CACHE KHÔNG CÓ -> KHÔI PHỤC CACHE TỪ POLL
                    # =================================================

                    if status is None:

                        print(
                            f"⚠️ Không có answer_id "
                            f"{answer_id} trong cache."
                        )

                        print(
                            "🔄 Đang lấy Poll để khôi phục answer cache..."
                        )

                        try:

                            poll_channel = self.bot.get_channel(
                                BANG_CHIEN_POLL_CHANNEL_ID
                            )

                            if poll_channel is None:

                                poll_channel = await self.bot.fetch_channel(
                                    BANG_CHIEN_POLL_CHANNEL_ID
                                )

                            message = await poll_channel.fetch_message(
                                int(message_id)
                            )

                            poll = message.poll

                            if poll is None:

                                print(
                                    f"❌ Message {message_id} "
                                    f"không có Poll."
                                )

                                return

                            # ---------------------------------------------
                            # TẠO LẠI CACHE
                            # ---------------------------------------------

                            cache_ok = cache_poll_answers(
                                message_id,
                                poll,
                                activity
                            )

                            if not cache_ok:

                                print(
                                    "❌ Không thể tạo lại answer cache."
                                )

                                return

                            # ---------------------------------------------
                            # LẤY STATUS LẠI
                            # ---------------------------------------------

                            status = get_cached_vote_status(
                                message_id,
                                answer_id
                            )

                            if status is None:

                                print(
                                    f"❌ Vẫn không xác định được "
                                    f"answer_id {answer_id}."
                                )

                                return

                            print(
                                f"✅ Đã khôi phục cache: "
                                f"{answer_id} -> {status}"
                            )

                        except Exception as e:

                            print(
                                f"❌ Lỗi khôi phục Poll cache: {e}"
                            )

                            return

                    print()
                    print("=" * 60)

                    print(
                        "🗳️ XỬ LÝ 1 USER VOTE"
                    )

                    print(
                        f"👤 User: {user}"
                    )

                    print(
                        f"🆔 ID: {user.id}"
                    )

                    print(
                        f"📌 Activity: {activity}"
                    )

                    print(
                        f"🗳️ Status: {status}"
                    )

                    print("=" * 60)

                    success, message_text = await asyncio.to_thread(
                        update_activity_status,
                        str(user.id),
                        status,
                        user,
                        activity
                    )

                    print(
                        f"📄 Kết quả: {message_text}"
                    )

                    return

                # =============================================
                # REMOVE
                # =============================================

                if event_type == "REMOVE":

                    print()
                    print("=" * 60)

                    print(
                        "🗑️ XỬ LÝ USER BỎ VOTE"
                    )

                    print(
                        f"👤 User: {user}"
                    )

                    print(
                        f"🆔 ID: {user.id}"
                    )

                    print(
                        f"📌 Activity: {activity}"
                    )

                    print("=" * 60)

                    success = await asyncio.to_thread(
                        set_user_pending_sync,
                        user,
                        activity
                    )

                    if success:

                        print(
                            f"✅ {user} -> PENDING"
                        )

                    else:

                        print(
                            f"⚠️ Không thể set "
                            f"{user} -> PENDING"
                        )

        except Exception as e:

            print(
                f"❌ Lỗi raw poll "
                f"{event_type}: {e}"
            )

    # =====================================================
    # RUN ACTIVITY
    # =====================================================

    async def run_activity(
        self,
        ctx,
        activity,
        config_override=None
    ):
        config = (
            config_override
            if config_override is not None
            else ACTIVITY_CONFIG.get(activity)
        )

        if config is None:

            await ctx.send(
                "❌ Activity không tồn tại.",
                delete_after=5
            )

            return

        # =================================================
        # CHECK CHANNEL
        # =================================================

        if (
            ctx.channel.id
            != BANG_CHIEN_CHANNEL_ID
        ):

            await ctx.send(
                "❌ Hãy sử dụng lệnh này "
                "ở đúng kênh Bang Chiến.",
                delete_after=5
            )

            return

        # =================================================
        # SYNC + RESET
        # =================================================

        try:

            result = await asyncio.to_thread(
                sync_activity_sheet,
                activity,
                True
            )

        except Exception as e:

            print(
                f"❌ Lỗi đồng bộ "
                f"{activity}: {e}"
            )

            await ctx.send(
                "❌ Không thể đồng bộ Google Sheets.\n"
                f"```{e}```",
                delete_after=10
            )

            return

        # =================================================
        # CREATE POLL
        # =================================================

        message = None

        try:

            poll = create_activity_poll(
                activity,
                config
            )

            content = create_activity_content(
                activity,
                config
            )

            # =================================================
            # CHANNEL
            # =================================================

            poll_channel = self.bot.get_channel(
                BANG_CHIEN_POLL_CHANNEL_ID
            )

            if poll_channel is None:

                poll_channel = await self.bot.fetch_channel(
                    BANG_CHIEN_POLL_CHANNEL_ID
                )

            # =================================================
            # ROLE
            # =================================================

            lac_vien_role = discord.utils.get(
                poll_channel.guild.roles,
                name="LẠC VIÊN"
            )

            if lac_vien_role is None:

                await ctx.send(
                    "❌ Không tìm thấy role **LẠC VIÊN**.",
                    delete_after=10
                )

                return

            # =================================================
            # CONTENT
            # =================================================

            poll_content = (
                f"{lac_vien_role.mention}\n\n"
                f"{content}"
            )

            # =================================================
            # SEND POLL
            # =================================================

            message = await poll_channel.send(
                content=poll_content,
                poll=poll,
                allowed_mentions=discord.AllowedMentions(
                    roles=True
                )
            )

            # =================================================
            # CACHE ANSWER ID NGAY
            #
            # Không cần fetch message sau này.
            # =================================================

            cache_poll_answers(
                message.id,
                poll,
                activity
            )

            # =================================================
            # SAVE STATE
            # =================================================

            register_poll(
                message.id,
                activity
            )

            print()
            print("=" * 60)

            print(
                f"🎮 ĐÃ TẠO {activity.upper()}"
            )

            print(
                f"🆔 Message ID: {message.id}"
            )

            print(
                f"📄 Sheet: {config['sheet']}"
            )

            print(
                "🧠 Answer cache đã lưu"
            )

            print(
                "👁️ ĐANG THEO DÕI VOTE"
            )

            print("=" * 60)

            await ctx.send(
                f"✅ **Đã tạo {config['title']}!**\n\n"
                f"📄 Sheet: **{config['sheet']}**\n"
                f"👥 Thành viên: **{result['total']}**\n"
                f"🆕 Thành viên mới: **{result['new']}**\n"
                f"🔄 Đã tồn tại: **{result['updated']}**\n"
                f"🎨 Format đã copy: **{result['format_success']}** dòng\n\n"
                f"⏰ Poll có hiệu lực **72 giờ**."
            )

        except discord.Forbidden:

            await ctx.send(
                "❌ Bot không có quyền gửi Poll "
                "ở kênh này.",
                delete_after=10
            )

        except Exception as e:

            print(
                f"❌ Lỗi tạo Poll "
                f"{activity}: {e}"
            )

            await ctx.send(
                "❌ Không thể tạo Poll.\n"
                f"```{e}```",
                delete_after=10
            )

    # =====================================================
    # COMMAND BANGCHIEN1
    # =====================================================

    @commands.command(
        name="bangchien1"
    )
    async def bangchien1(
        self,
        ctx
    ):

        if not await self.check_allowed_user(
            ctx
        ):

            return

        await self.run_activity(
            ctx,
            "bangchien1"
        )

    # =====================================================
    # COMMAND BANGCHIEN2
    # =====================================================

    @commands.command(
        name="bangchien2"
    )
    async def bangchien2(
        self,
        ctx
    ):

        if not await self.check_allowed_user(
            ctx
        ):

            return

        await self.run_activity(
            ctx,
            "bangchien2"
        )

    # =====================================================
    # COMMAND SCRIM 5
    # =====================================================

    @commands.command(
    name="scrimthu5"
    )
    async def scrimthu5(
        self,
        ctx,
        so_tran: int,
        *,
        doi_thu: str
    ):

        if not await self.check_allowed_user(
            ctx
        ):
            return

        # =================================================
        # KIỂM TRA SỐ TRẬN
        # =================================================

        if so_tran not in (1, 2):

            await ctx.send(
                "❌ Số trận chỉ được là **1 hoặc 2**.\n\n"
                "Ví dụ:\n"
                "`!scrimthu5 1 Cửu thiên`\n"
                "`!scrimthu5 2 Cửu thiên, phong ưng`",
                delete_after=10
            )

            return

        # =================================================
        # TÁCH ĐỐI THỦ
        # =================================================

        doi_thu_list = [
            x.strip()
            for x in doi_thu.split(",")
            if x.strip()
        ]

        # =================================================
        # KIỂM TRA SỐ ĐỐI THỦ
        # =================================================

        if len(doi_thu_list) != so_tran:

            await ctx.send(
                f"❌ Bạn chọn **{so_tran} trận** "
                f"nhưng nhập **{len(doi_thu_list)} đối thủ**.\n\n"
                "Ví dụ:\n"
                "`!scrimthu5 1 Cửu thiên`\n"
                "`!scrimthu5 2 Cửu thiên, phong ưng`",
                delete_after=10
            )

            return

        try:

            config = build_scrim_config(
                "scrimthu5",
                so_tran,
                doi_thu_list
            )

        except Exception as e:

            await ctx.send(
                f"❌ {e}",
                delete_after=10
            )

            return

        await self.run_activity(
            ctx,
            "scrimthu5",
            config
        )

    # =====================================================
    # COMMAND SCRIM 6
    # =====================================================

    @commands.command(
    name="scrimthu6"
    )
    async def scrimthu6(
        self,
        ctx,
        so_tran: int,
        *,
        doi_thu: str
    ):

        if not await self.check_allowed_user(
            ctx
        ):
            return

        # =================================================
        # KIỂM TRA SỐ TRẬN
        # =================================================

        if so_tran not in (1, 2):

            await ctx.send(
                "❌ Số trận chỉ được là **1 hoặc 2**.\n\n"
                "Ví dụ:\n"
                "`!scrimthu6 1 Cửu thiên`\n"
                "`!scrimthu6 2 Cửu thiên, phong ưng`",
                delete_after=10
            )

            return

        # =================================================
        # TÁCH ĐỐI THỦ
        # =================================================

        doi_thu_list = [
            x.strip()
            for x in doi_thu.split(",")
            if x.strip()
        ]

        # =================================================
        # KIỂM TRA SỐ ĐỐI THỦ
        # =================================================

        if len(doi_thu_list) != so_tran:

            await ctx.send(
                f"❌ Bạn chọn **{so_tran} trận** "
                f"nhưng nhập **{len(doi_thu_list)} đối thủ**.\n\n"
                "Ví dụ:\n"
                "`!scrimthu6 1 Cửu thiên`\n"
                "`!scrimthu6 2 Cửu thiên, phong ưng`",
                delete_after=10
            )

            return

        try:

            config = build_scrim_config(
                "scrimthu6",
                so_tran,
                doi_thu_list
            )

        except Exception as e:

            await ctx.send(
                f"❌ {e}",
                delete_after=10
            )

            return

        await self.run_activity(
            ctx,
            "scrimthu6",
            config
        )

    # =====================================================
    # !DONGBO
    # =====================================================

    @commands.command(
    name="dongbo"
)
    @commands.has_permissions(
        administrator=True
    )
    async def dongbo(
        self,
        ctx
    ):

        activities = [
            "bangchien2",
            "scrimthu5",
            "scrimthu6"
        ]

        results = {}

        try:

            await ctx.send(
                "🔄 **Đang đồng bộ dữ liệu...**\n"
                "⚔️ Bang Chiến\n"
                "🎮 Scrim Thứ 5\n"
                "🎮 Scrim Thứ 6",
                delete_after=10
            )

            # =================================================
            # ĐỒNG BỘ TỪNG ACTIVITY
            # =================================================

            for activity in activities:

                print()
                print("=" * 60)
                print(
                    f"🔄 !dongbo -> {activity}"
                )
                print("=" * 60)

                result = await asyncio.to_thread(
                    sync_activity_sheet,
                    activity,
                    False
                )

                results[activity] = result

            # =================================================
            # KẾT QUẢ
            # =================================================

            war = results["bangchien2"]
            scrim5 = results["scrimthu5"]
            scrim6 = results["scrimthu6"]

            await ctx.send(
                "✅ **ĐỒNG BỘ HOÀN TẤT!**\n\n"

            )

        except Exception as e:

            print(
                f"❌ Lỗi !dongbo: {e}"
            )

            await ctx.send(
                "❌ **Đồng bộ thất bại.**\n"
                f"```{e}```",
                # delete_after=15
            )

            # =====================================================
    # COMMAND ERROR HANDLERS
    # =====================================================

    async def _permission_error(
        self,
        ctx,
        error,
        command_name
    ):

        if isinstance(
            error,
            commands.MissingPermissions
        ):

            await ctx.send(
                "❌ Bạn không có quyền sử dụng lệnh này.",
                delete_after=5
            )

        elif isinstance(
            error,
            commands.MissingRequiredArgument
        ):

            await ctx.send(
                f"❌ Thiếu tham số cho lệnh `{command_name}`.",
                delete_after=10
            )

        elif isinstance(
            error,
            commands.BadArgument
        ):

            await ctx.send(
                f"❌ Tham số không hợp lệ cho lệnh `{command_name}`.",
                delete_after=10
            )

        else:

            print(
                f"❌ Lỗi {command_name}: {error}"
            )

            await ctx.send(
                f"❌ Lỗi khi thực hiện `{command_name}`.",
                delete_after=10
            )


    # =====================================================
    # ERROR BANGCHIEN1
    # =====================================================

    @bangchien1.error
    async def bangchien1_error(
        self,
        ctx,
        error
    ):

        await self._permission_error(
            ctx,
            error,
            "!bangchien1"
        )


    # =====================================================
    # ERROR BANGCHIEN2
    # =====================================================

    @bangchien2.error
    async def bangchien2_error(
        self,
        ctx,
        error
    ):

        await self._permission_error(
            ctx,
            error,
            "!bangchien2"
        )


    # =====================================================
    # ERROR SCRIM THỨ 5
    # =====================================================

    @scrimthu5.error
    async def scrimthu5_error(
        self,
        ctx,
        error
    ):

        await self._permission_error(
            ctx,
            error,
            "!scrimthu5"
        )


    # =====================================================
    # ERROR SCRIM THỨ 6
    # =====================================================

    @scrimthu6.error
    async def scrimthu6_error(
        self,
        ctx,
        error
    ):

        await self._permission_error(
            ctx,
            error,
            "!scrimthu6"
        )


    # =====================================================
    # ERROR DONGBO
    # =====================================================

    @dongbo.error
    async def dongbo_error(
        self,
        ctx,
        error
    ):

        await self._permission_error(
            ctx,
            error,
            "!dongbo"
        )


# =========================================================
# RESTORE ACTIVE POLLS
#
# ĐÂY LÀ NƠI DUY NHẤT ĐỌC TOÀN BỘ VOTE.
#
# Chạy khi bot khởi động.
# =========================================================

async def restore_active_poll_votes(
    bot
):

    print()
    print("=" * 60)
    print("🔄 ĐANG KHÔI PHỤC VOTE CÁC POLL...")
    print("=" * 60)

    if not active_polls:

        print(
            "📌 Không có Poll nào trong state."
        )

        return

    poll_channel = bot.get_channel(
        BANG_CHIEN_POLL_CHANNEL_ID
    )

    if poll_channel is None:

        try:

            poll_channel = await bot.fetch_channel(
                BANG_CHIEN_POLL_CHANNEL_ID
            )

        except Exception as e:

            print(
                f"❌ Không lấy được kênh Poll: {e}"
            )

            return

    # =====================================================
    # CACHE PLAYER 1 LẦN
    # =====================================================

    if not PLAYER_CACHE:

        await asyncio.to_thread(
            refresh_player_cache
        )

    # =====================================================
    # TỪNG POLL
    # =====================================================

    for message_id, poll_data in list(
        active_polls.items()
    ):

        activity = poll_data.get(
            "activity"
        )

        config = ACTIVITY_CONFIG.get(
            activity
        )

        if config is None:
            continue

        print()
        print("-" * 60)

        print(
            f"🗳️ Khôi phục Poll: {message_id}"
        )

        print(
            f"📌 Activity: {activity}"
        )

        try:

            message = await poll_channel.fetch_message(
                int(message_id)
            )

        except discord.NotFound:

            print(
                f"⚠️ Không tìm thấy Poll "
                f"{message_id}."
            )

            remove_poll(
                message_id
            )

            continue

        except discord.Forbidden:

            print(
                "❌ Bot không có quyền đọc Poll."
            )

            continue

        except Exception as e:

            print(
                f"❌ Lỗi lấy Poll: {e}"
            )

            continue

        poll = message.poll

        if poll is None:

            print(
                "⚠️ Message không còn Poll."
            )

            continue

       

        # =================================================
        # CACHE ANSWER ID
        # =================================================

        cache_poll_answers(
            message_id,
            poll,
            activity
        )

        try:

            if poll.is_finalized():

                print(
                    f"⏰ Poll {message_id} đã kết thúc."
                )

                remove_poll(
                    message_id
                )

                continue

        except Exception:

            pass

        # =================================================
        # ĐỌC TOÀN BỘ VOTE
        #
        # ĐÂY LÀ LẦN DUY NHẤT.
        # =================================================

        voted_users = {}

        for answer in poll.answers:

            answer_id = getattr(
                answer,
                "id",
                None
            )

            answer_text = str(
                getattr(
                    answer,
                    "text",
                    ""
                )
            ).strip()

            if answer_text == config["join"]:

                status = config["join_status"]

            elif answer_text == config["not_join"]:

                status = config["not_join_status"]

            else:

                continue

            try:

                async for user in answer.voters():

                    voted_users[
                        user.id
                    ] = {

                        "user":
                            user,

                        "status":
                            status
                    }

            except Exception as e:

                print(
                    f"❌ Không đọc được voter: {e}"
                )

        print(
            f"🗳️ Tổng vote: "
            f"{len(voted_users)}"
        )

        # =================================================
        # SYNC TO SHEET
        # =================================================

        await sync_startup_votes_to_sheet(
            activity,
            voted_users
        )

    print()
    print("=" * 60)
    print("✅ HOÀN TẤT KHÔI PHỤC VOTE")
    print("=" * 60)

# =========================================================
# SYNC STARTUP VOTES
#
# Được gọi khi bot khởi động.
#
# Có thể đọc Sheet 1 lần / activity.
# Sau đó update những người đã vote.
# =========================================================


def find_activity_row_for_user(activity, user):
    """
    Tìm dòng Sheet của Discord user.

    Ưu tiên:
    1. Discord ID
    2. username
    3. display_name
    4. global_name

    Hỗ trợ Sheet chỉ lưu username, ví dụ:
        cuabro123

    Không bắt buộc Sheet phải có Discord ID.
    """

    if user is None:
        return None

    candidates = []

    # =====================================================
    # DISCORD ID
    # =====================================================

    user_id = getattr(
        user,
        "id",
        None
    )

    if user_id:

        candidates.append(
            str(user_id).strip()
        )

    # =====================================================
    # USERNAME
    # =====================================================

    username = getattr(
        user,
        "name",
        None
    )

    if username:

        candidates.append(
            str(username).strip()
        )

    # =====================================================
    # DISPLAY NAME
    # =====================================================

    display_name = getattr(
        user,
        "display_name",
        None
    )

    if display_name:

        candidates.append(
            str(display_name).strip()
        )

    # =====================================================
    # GLOBAL NAME
    # =====================================================

    global_name = getattr(
        user,
        "global_name",
        None
    )

    if global_name:

        candidates.append(
            str(global_name).strip()
        )

    # =====================================================
    # DISCORD OBJECT
    # =====================================================

    try:

        discord_text = str(
            user
        ).strip()

        if discord_text:

            candidates.append(
                discord_text
            )

    except Exception:
        pass

    # =====================================================
    # TÌM TRONG CACHE
    # =====================================================

    checked = set()

    for candidate in candidates:

        candidate = str(
            candidate
        ).strip()

        if not candidate:
            continue

        key = candidate.lower()

        if key in checked:
            continue

        checked.add(key)

        row = get_cached_activity_row(
            activity,
            key
        )

        if row is not None:

            print(
                f"🔎 MATCH USER: {candidate} "
                f"→ dòng {row['row_number']}"
            )

            return row

    return None


# =========================================================
# SYNC STARTUP VOTES
# =========================================================

# =========================================================
# SYNC STARTUP VOTES
# =========================================================

async def sync_startup_votes_to_sheet(
    activity,
    voted_users
):
    """
    Đồng bộ trạng thái vote hiện tại của Discord Poll
    với Google Sheets.

    NGUYÊN TẮC:

    1. Vote giống Sheet:
       -> KHÔNG UPDATE
       -> Giữ nguyên F:G:H

    2. Vote khác Sheet:
       -> UPDATE F:H

    3. User không còn vote:
       -> Nếu Sheet chưa phải PENDING
          thì chuyển về PENDING

    4. Chỉ batch_update những dòng thực sự thay đổi.

    5. Không sử dụng answer_cache.
    """

    config = ACTIVITY_CONFIG.get(
        activity
    )

    if config is None:

        print(
            f"❌ Activity không hợp lệ: {activity}"
        )

        return

    lock = get_activity_lock(
        activity
    )

    async with lock:

        print()
        print("=" * 60)
        print(
            f"🔄 SYNC STARTUP VOTE: {activity}"
        )
        print(
            f"🗳️ Discord có {len(voted_users)} user đã vote"
        )
        print("=" * 60)

        # =================================================
        # LẤY WORKSHEET
        # =================================================

        worksheet = await asyncio.to_thread(
            get_sheet_for_activity,
            activity
        )

        if worksheet is None:

            print(
                "❌ Không lấy được worksheet."
            )

            return

        # =================================================
        # LOAD CACHE TỪ GOOGLE SHEET
        # =================================================

        await asyncio.to_thread(
            refresh_activity_cache,
            activity,
            worksheet
        )

        rows = ACTIVITY_CACHE.get(
            activity,
            {}
        )

        print(
            f"📄 {activity}: "
            f"{len(rows)} dòng cache"
        )

        # =================================================
        # CHUẨN BỊ
        # =================================================

        updates = []

        total_join = 0
        total_not_join = 0
        total_pending = 0

        total_matched = 0
        total_not_found = 0

        total_unchanged = 0
        total_changed = 0

        matched_rows = set()

        # =================================================
        # DUYỆT USER ĐÃ VOTE
        # =================================================

        for vote_key, vote_data in voted_users.items():

            try:

                user = vote_data.get(
                    "user"
                )

                status = str(
                    vote_data.get(
                        "status",
                        ""
                    )
                ).strip()

            except Exception as e:

                print(
                    f"❌ Vote data lỗi: {e}"
                )

                continue

            # -------------------------------------------------
            # Không có user
            # -------------------------------------------------

            if user is None:

                print(
                    f"⚠️ Vote {vote_key} không có user."
                )

                continue

            # -------------------------------------------------
            # Không có status
            # -------------------------------------------------

            if not status:

                print(
                    f"⚠️ User {user} không có status."
                )

                continue

            # =================================================
            # TÌM ROW
            # =================================================

            row = find_activity_row_for_user(
                activity,
                user
            )

            if row is None:

                total_not_found += 1

                print(
                    f"⚠️ Không tìm thấy Sheet cho user: "
                    f"{user}"
                )

                continue

            row_number = row[
                "row_number"
            ]

            # =================================================
            # TRÁNH MATCH TRÙNG DÒNG
            # =================================================

            if row_number in matched_rows:

                print(
                    f"⚠️ Dòng {row_number} "
                    f"đã được match trước đó."
                )

                continue

            matched_rows.add(
                row_number
            )

            total_matched += 1

            # =================================================
            # LẤY STATUS HIỆN TẠI TRÊN SHEET
            # =================================================

            current_status = str(
                row.get(
                    "status",
                    ""
                )
            ).strip()

            # =================================================
            # THỐNG KÊ
            # =================================================

            if status == config[
                "join_status"
            ]:

                total_join += 1

            elif status == config[
                "not_join_status"
            ]:

                total_not_join += 1

            # =================================================
            # QUAN TRỌNG:
            # STATUS KHÔNG ĐỔI
            # =================================================

            if current_status == status:

                total_unchanged += 1

                print(
                    f"⏭️ {user}: "
                    f"không thay đổi "
                    f"({status}) → giữ nguyên Sheet"
                )

                # Không update
                continue

            # =================================================
            # STATUS ĐÃ THAY ĐỔI
            # =================================================

            total_changed += 1

            print()
            print(
                f"🔄 VOTE THAY ĐỔI: {user}"
            )

            print(
                f"   📄 Sheet cũ : {current_status}"
            )

            print(
                f"   🗳️ Discord   : {status}"
            )

            # =================================================
            # THỜI GIAN CHỈ TẠO KHI THỰC SỰ THAY ĐỔI
            # =================================================

            now = now_string()

            # =================================================
            # TÊN USER
            # =================================================

            register = str(
                user
            ).strip()

            if not register:

                register = str(
                    getattr(
                        user,
                        "name",
                        ""
                    )
                ).strip()

            # =================================================
            # UPDATE F:H
            # =================================================

            updates.append(
                {
                    "range":
                        f"F{row_number}:H{row_number}",

                    "values":
                        [[
                            status,
                            now,
                            register
                        ]],
                }
            )

            # =================================================
            # UPDATE CACHE LOCAL
            # =================================================

            row["status"] = status
            row["time"] = now
            row["register"] = register

        # =====================================================
        # NHỮNG ROW KHÔNG CÓ TRONG POLL
        #
        # -> USER HIỆN TẠI KHÔNG VOTE
        # =====================================================

        for key, row in rows.items():

            row_number = row[
                "row_number"
            ]

            # -------------------------------------------------
            # Đã có vote xử lý phía trên
            # -------------------------------------------------

            if row_number in matched_rows:

                continue

            current_status = str(
                row.get(
                    "status",
                    ""
                )
            ).strip()

            # =================================================
            # ĐÃ PENDING
            #
            # Không cần làm gì
            # =================================================

            if current_status == config[
                "pending_status"
            ]:

                total_pending += 1

                continue

            # =================================================
            # SHEET ĐANG CÓ VOTE
            #
            # Nhưng Discord hiện tại không còn vote
            #
            # -> RESET PENDING
            # =================================================

            print()
            print(
                f"🔄 USER BỎ VOTE: dòng {row_number}"
            )

            print(
                f"   📄 Sheet cũ: {current_status}"
            )

            print(
                f"   🗳️ Discord: không còn vote"
            )

            updates.append(
                {
                    "range":
                        f"F{row_number}:H{row_number}",

                    "values":
                        [[
                            config[
                                "pending_status"
                            ],
                            "",
                            ""
                        ]],
                }
            )

            # =================================================
            # UPDATE CACHE LOCAL
            # =================================================

            row["status"] = config[
                "pending_status"
            ]

            row["time"] = ""
            row["register"] = ""

            total_pending += 1

        # =====================================================
        # BATCH UPDATE
        # =====================================================

        print()
        print("=" * 60)
        print("📊 KẾT QUẢ SO SÁNH")
        print("=" * 60)

        print(
            f"🗳️ Discord đã vote      : "
            f"{len(voted_users)}"
        )

        print(
            f"🔗 Match được Sheet     : "
            f"{total_matched}"
        )

        print(
            f"⚠️ Không tìm thấy Sheet : "
            f"{total_not_found}"
        )

        print(
            f"⏭️ Không thay đổi        : "
            f"{total_unchanged}"
        )

        print(
            f"🔄 Có thay đổi           : "
            f"{total_changed}"
        )

        print(
            f"⏳ Chưa vote             : "
            f"{total_pending}"
        )

        print(
            f"⚔️ Đánh                  : "
            f"{total_join}"
        )

        print(
            f"❌ Không đánh            : "
            f"{total_not_join}"
        )

        print(
            f"📦 Cần update            : "
            f"{len(updates)} dòng"
        )

        print("=" * 60)

        # =====================================================
        # KHÔNG CÓ THAY ĐỔI
        # =====================================================

        if not updates:

            print(
                "✅ Không có dữ liệu thay đổi."
            )

            print(
                "⏭️ Không thực hiện Google Sheets update."
            )

            print("=" * 60)

            return

        # =====================================================
        # BATCH UPDATE GOOGLE SHEET
        # =====================================================

        print()
        print(
            f"📦 Chuẩn bị update "
            f"{len(updates)} dòng..."
        )

        try:

            await asyncio.to_thread(
                google_retry,
                worksheet.batch_update,
                updates,
                max_retries=7,
                base_delay=3,
            )

            print(
                f"✅ Đã batch update "
                f"{len(updates)} dòng."
            )

        except Exception as e:

            print(
                f"❌ Lỗi batch update Google Sheets: "
                f"{e}"
            )

            raise

        print("=" * 60)
# =========================================================
# SETUP
# =========================================================

async def setup(
    bot
):

    await bot.add_cog(
        BangChien(bot)
    )

    print(
        "✅ Đã load module bang_chien.py"
    )

    print(
        "⚔️ Commands: !bangchien1"
    )

    print(
        "⚔️ Commands: !bangchien2"
    )

    print(
        "🎮 Commands: !scrimthu5"
    )

    print(
        "🎮 Commands: !scrimthu6"
    )

    print(
        "🔄 Commands: !dongbo"
    )

    print(
        "📊 Commands: !bangchienstatus"
    )

    print(
        "🗳️ Poll listeners: "
        "RAW ADD / RAW REMOVE"
    )

    print(
        "🚀 Poll toàn bộ vote: "
        "CHỈ ĐỌC KHI BOT KHỞI ĐỘNG"
    )