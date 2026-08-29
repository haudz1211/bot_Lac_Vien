import asyncio
import re
#from discord_id import add_discord_name#

import discord
from discord.ext import commands

from sheets import (
    save_player,
    sheet,
    spreadsheet,
    CLASS_MAP,
    CLASS_ROW_COLORS,
    column_to_letter
)
from channel_config import ROLE_CLASS_CHANNEL_ID


# =========================================================
# CẤU HÌNH
# =========================================================

REGISTER_CHANNEL_ID = ROLE_CLASS_CHANNEL_ID

ROLE_LAC_VIEN = "LẠC VIÊN"


# =========================================================
# CÁC MÔN PHÁI
# =========================================================

MON_PHAI = [
    "Thần Tương",
    "Tố Vấn",
    "Thiết Y",
    "Cửu Linh",
    "Huyết Hà",
    "Long Ngâm",
    "Tuyết Ẩn",
    "Toái Mộng"
]


# =========================================================
# COG ROLE CLASS
# =========================================================

class RoleClass(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        print(
            "✅ Đã load RoleClass."
        )


    # =====================================================
    # EVENT ĐĂNG KÝ NHÂN VẬT
    # =====================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message
    ):

        # =================================================
        # BỎ QUA BOT
        # =================================================

        if message.author.bot:

            return


        # =================================================
        # CHỈ XỬ LÝ KÊNH ĐĂNG KÝ
        # =================================================

        if (
            message.channel.id
            != REGISTER_CHANNEL_ID
        ):

            return


        # =================================================
        # KIỂM TRA SERVER
        # =================================================

        if message.guild is None:

            print(
                "❌ Tin nhắn không nằm trong server."
            )

            return


        # =================================================
        # DEBUG
        # =================================================

        print()
        print("=" * 60)
        print("📩 NHẬN ĐƯỢC ĐĂNG KÝ")

        print(
            f"👤 Người gửi: "
            f"{message.author} "
            f"(ID: {message.author.id})"
        )

        print(
            f"💬 Nội dung: "
            f"{message.content}"
        )

        print(
            f"🏷️ Số người được tag: "
            f"{len(message.mentions)}"
        )


        # =================================================
        # XÁC ĐỊNH NGƯỜI ĐĂNG KÝ
        # =================================================

        if message.mentions:

            target_member = message.mentions[0]

            registration_type = "CÓ TAG"

            print(
                f"🎯 Có tag → đăng ký cho: "
                f"{target_member} "
                f"(ID: {target_member.id})"
            )

        else:

            target_member = message.author

            registration_type = "KHÔNG TAG"

            print(
                f"🎯 Không tag → đăng ký cho: "
                f"{target_member} "
                f"(ID: {target_member.id})"
            )


        # =================================================
        # LẤY CONTENT
        # =================================================

        content = message.content.strip()


        # =================================================
        # XÓA MENTION
        # =================================================

        content_without_mention = content

        for mention in message.mentions:

            content_without_mention = re.sub(
                rf"<@!?{mention.id}>",
                "",
                content_without_mention,
                count=1
            )

        content_without_mention = (
            content_without_mention.strip()
        )


        print(
            f"📝 Sau khi bỏ tag: "
            f"{content_without_mention}"
        )


        # =================================================
        # KIỂM TRA DẤU -
        # =================================================

        if "-" not in content_without_mention:

            await message.add_reaction(
                "❌"
            )

            print(
                "❌ Sai định dạng."
            )

            print(
                "Ví dụ:"
            )

            print(
                "Tịch Long - Tố Vấn"
            )

            print(
                "@user Tịch Long - Tố Vấn"
            )

            print("=" * 60)

            return


        # =================================================
        # TÁCH TÊN NHÂN VẬT / MÔN PHÁI
        # =================================================

        try:

            ten_nv, mon_phai = map(
                str.strip,
                content_without_mention.split(
                    "-",
                    1
                )
            )

        except Exception as e:

            print(
                f"❌ Không thể tách dữ liệu: {e}"
            )

            await message.add_reaction(
                "❌"
            )

            return


        # =================================================
        # KIỂM TRA TÊN
        # =================================================

        if not ten_nv:

            print(
                "❌ Không có tên nhân vật."
            )

            await message.add_reaction(
                "❌"
            )

            return


        # =================================================
        # KIỂM TRA MÔN PHÁI
        # =================================================

        if not mon_phai:

            print(
                "❌ Không có môn phái."
            )

            await message.add_reaction(
                "❌"
            )

            return


        # =================================================
        # TÌM MÔN PHÁI HỢP LỆ
        # =================================================

        mon_phai_hop_le = None

        for mp in MON_PHAI:

            if (
                mp.lower().strip()
                == mon_phai.lower().strip()
            ):

                mon_phai_hop_le = mp

                break


        # =================================================
        # MÔN PHÁI KHÔNG HỢP LỆ
        # =================================================

        if mon_phai_hop_le is None:

            print(
                f"❌ Sai môn phái: {mon_phai}"
            )

            print(
                "📋 Môn phái hợp lệ: "
                + ", ".join(
                    MON_PHAI
                )
            )

            await message.add_reaction(
                "❌"
            )

            return


        print(
            f"⚔️ Môn phái: "
            f"{mon_phai_hop_le}"
        )

        print(
            f"📝 Tên nhân vật: "
            f"{ten_nv}"
        )


        # =================================================
        # TÌM ROLE
        # =================================================

        role_class = None

        role_lac_vien = None

        for role in message.guild.roles:

            role_name = (
                role.name
                .lower()
                .strip()
            )


            # ---------------------------------------------
            # ROLE MÔN PHÁI
            # ---------------------------------------------

            if (
                role_name
                == mon_phai_hop_le.lower()
            ):

                role_class = role


            # ---------------------------------------------
            # ROLE LẠC VIÊN
            # ---------------------------------------------

            if (
                role_name
                == ROLE_LAC_VIEN.lower()
            ):

                role_lac_vien = role


        # =================================================
        # KHÔNG CÓ ROLE CLASS
        # =================================================

        if role_class is None:

            print(
                f"❌ Không tìm thấy role môn phái: "
                f"{mon_phai_hop_le}"
            )

            await message.add_reaction(
                "❌"
            )

            return


        # =================================================
        # KHÔNG CÓ ROLE LẠC VIÊN
        # =================================================

        if role_lac_vien is None:

            print(
                f"❌ Không tìm thấy role: "
                f"{ROLE_LAC_VIEN}"
            )

            await message.add_reaction(
                "❌"
            )

            return


        print(
            f"🏷️ Role class: "
            f"{role_class.name}"
        )

        print(
            f"🏷️ Role Lạc Viên: "
            f"{role_lac_vien.name}"
        )


        # =================================================
        # BOT MEMBER
        # =================================================

        bot_member = message.guild.me

        if bot_member is None:

            print(
                "❌ Không tìm thấy Bot Member."
            )

            await message.add_reaction(
                "❌"
            )

            return


        print(
            f"🤖 Role cao nhất của Bot: "
            f"{bot_member.top_role.name}"
        )


        # =================================================
        # KIỂM TRA QUYỀN ROLE CLASS
        # =================================================

        if role_class >= bot_member.top_role:

            print(
                f"❌ Bot không thể quản lý role "
                f"{role_class.name}"
            )

            print(
                f"Role Bot: "
                f"{bot_member.top_role.name}"
            )

            print(
                f"Role Class: "
                f"{role_class.name}"
            )

            await message.add_reaction(
                "❌"
            )

            return


        # =================================================
        # KIỂM TRA QUYỀN ROLE LẠC VIÊN
        # =================================================

        if (
            role_lac_vien
            >= bot_member.top_role
        ):

            print(
                f"❌ Bot không thể quản lý role "
                f"{role_lac_vien.name}"
            )

            print(
                f"Role Bot: "
                f"{bot_member.top_role.name}"
            )

            print(
                f"Role LẠC VIÊN: "
                f"{role_lac_vien.name}"
            )

            await message.add_reaction(
                "❌"
            )

            return


        # =================================================
        # CẤP ROLE
        # =================================================

        try:

            # =============================================
            # XÓA CLASS CŨ
            # =============================================

            for role in target_member.roles:

                if role.name in MON_PHAI:

                    if role.id == role_class.id:

                        continue

                    try:

                        await target_member.remove_roles(
                            role,
                            reason="Đổi môn phái"
                        )

                        print(
                            f"🗑️ Đã xóa role cũ: "
                            f"{role.name}"
                        )

                    except discord.Forbidden:

                        print(
                            f"❌ Không thể xóa role: "
                            f"{role.name}"
                        )


            # =============================================
            # CẤP CLASS MỚI
            # =============================================

            if (
                role_class
                not in target_member.roles
            ):

                await target_member.add_roles(
                    role_class,
                    reason=(
                        f"Đăng ký môn phái: "
                        f"{mon_phai_hop_le}"
                    )
                )

                print(
                    f"✅ Đã cấp class: "
                    f"{role_class.name}"
                )

            else:

                print(
                    f"ℹ️ Đã có role: "
                    f"{role_class.name}"
                )


            # =============================================
            # CẤP ROLE LẠC VIÊN
            # =============================================

            if (
                role_lac_vien
                not in target_member.roles
            ):

                await target_member.add_roles(
                    role_lac_vien,
                    reason="Đăng ký nhân vật"
                )

                print(
                    f"✅ Đã cấp role: "
                    f"{role_lac_vien.name}"
                )

            else:

                print(
                    f"ℹ️ Đã có role: "
                    f"{role_lac_vien.name}"
                )


            # =============================================
            # LƯU GOOGLE SHEETS
            # =============================================

            save_player(
                target_member,
                ten_nv,
                mon_phai_hop_le
            )

            # discord_name = target_member.name

           

            print(
                "✅ Đã lưu người chơi vào Google Sheets."
            )


            # =============================================
            # THÀNH CÔNG
            # =============================================

            await message.add_reaction(
                "✅"
            )

            print("=" * 60)

            print(
                "🎉 ĐĂNG KÝ THÀNH CÔNG"
            )

            print(
                f"📌 Loại đăng ký: "
                f"{registration_type}"
            )

            print(
                f"👤 Người thực hiện: "
                f"{message.author} "
                f"(ID: {message.author.id})"
            )

            print(
                f"🎯 Người đăng ký: "
                f"{target_member} "
                f"(ID: {target_member.id})"
            )

            print(
                f"📝 Tên nhân vật: "
                f"{ten_nv}"
            )

            print(
                f"⚔️ Môn phái: "
                f"{mon_phai_hop_le}"
            )

            print(
                f"🏷️ Class: "
                f"{role_class.name}"
            )

            print(
                f"🏷️ Lạc Viên: "
                f"{role_lac_vien.name}"
            )

            print("=" * 60)


        # =================================================
        # DISCORD FORBIDDEN
        # =================================================

        except discord.Forbidden as e:

            print("=" * 60)

            print(
                "❌ DISCORD FORBIDDEN / "
                "MISSING PERMISSIONS"
            )

            print(
                e
            )

            print("=" * 60)

            await message.add_reaction(
                "❌"
            )


        # =================================================
        # LỖI KHÁC
        # =================================================

        except Exception as e:

            print("=" * 60)

            print(
                f"❌ LỖI KHÔNG XÁC ĐỊNH: {e}"
            )

            print("=" * 60)

            await message.add_reaction(
                "❌"
            )


    # =====================================================
    # !TOMAU
    #
    # TÔ LẠI MÀU TOÀN BỘ DATA ĐÃ CÓ
    # TRONG SHEET 1 - DANH SÁCH THÀNH VIÊN
    #
    # Cột D = Môn phái
    #
    # Chỉ thay đổi backgroundColor.
    # Không thay đổi nội dung.
    # =====================================================

    @commands.command(
        name="tomau"
    )
    @commands.has_permissions(
        administrator=True
    )
    async def tomau(
        self,
        ctx
    ):

        try:

            print()
            print("=" * 60)
            print(
                "🎨 BẮT ĐẦU TÔ MÀU SHEET 1"
            )
            print("=" * 60)

            # =================================================
            # LẤY DATA
            # =================================================

            rows = await asyncio.to_thread(
                sheet.get_all_values
            )

            if not rows:

                await ctx.send(
                    "⚠️ Sheet 1 không có dữ liệu.",
                    delete_after=5
                )

                return

            # =================================================
            # TẠO BATCH REQUEST
            #
            # Không format từng row bằng API riêng.
            # Gom tất cả vào 1 batch_update.
            # =================================================

            requests = []

            total = 0

            success = 0

            skipped = 0

            # =================================================
            # DUYỆT DATA TỪ DÒNG 2
            # =================================================

            for row_number, row in enumerate(
                rows[1:],
                start=2
            ):

                total += 1

                # =============================================
                # KIỂM TRA DATA
                # =============================================

                if not row:

                    skipped += 1

                    continue

                # =============================================
                # CỘT D = index 3
                # =============================================

                if len(row) < 4:

                    skipped += 1

                    print(
                        f"⚠️ Dòng {row_number}: "
                        "không đủ cột."
                    )

                    continue

                # =============================================
                # LẤY MÔN PHÁI
                # =============================================

                mon_phai = str(
                    row[3]
                ).strip()

                if not mon_phai:

                    skipped += 1

                    continue

                # =============================================
                # CHUẨN HÓA
                # =============================================

                mon_phai = CLASS_MAP.get(
                    mon_phai.lower(),
                    mon_phai
                )

                # =============================================
                # LẤY MÀU
                # =============================================

                color = CLASS_ROW_COLORS.get(
                    mon_phai
                )

                if color is None:

                    skipped += 1

                    print(
                        f"⚠️ Dòng {row_number}: "
                        f"không có màu cho {mon_phai}"
                    )

                    continue

                # =============================================
                # TÌM CỘT CUỐI CÓ DỮ LIỆU
                # =============================================

                last_column = 0

                for index, value in enumerate(
                    row,
                    start=1
                ):

                    if str(value).strip():

                        last_column = index

                if last_column == 0:

                    skipped += 1

                    continue

                # =============================================
                # CHUYỂN CỘT -> LETTER
                # =============================================

                end_column = column_to_letter(
                    last_column
                )

                # =============================================
                # BATCH FORMAT REQUEST
                #
                # startRowIndex = row - 1
                # endRowIndex = row
                #
                # startColumnIndex = 0  => A
                # endColumnIndex = last
                # =============================================

                requests.append({

                    "repeatCell": {

                        "range": {

                            "sheetId":
                                sheet.id,

                            "startRowIndex":
                                row_number - 1,

                            "endRowIndex":
                                row_number,

                            "startColumnIndex":
                                0,

                            "endColumnIndex":
                                last_column
                        },

                        "cell": {

                            "userEnteredFormat": {

                                "backgroundColor":
                                    color

                            }
                        },

                        "fields":
                            "userEnteredFormat.backgroundColor"
                    }
                })

                success += 1

                print(
                    f"🎨 Dòng {row_number}: "
                    f"{mon_phai} "
                    f"→ A:{end_column}"
                )

            # =================================================
            # KHÔNG CÓ REQUEST
            # =================================================

            if not requests:

                await ctx.send(
                    "⚠️ Không tìm thấy dòng nào "
                    "có môn phái hợp lệ để tô màu.",
                    delete_after=8
                )

                return

            # =================================================
            # GỬI BATCH REQUEST
            #
            # Chia batch tối đa 100 request/lần
            # =================================================

            batch_size = 100

            batch_count = 0

            for start in range(
                0,
                len(requests),
                batch_size
            ):

                batch = requests[
                    start:
                    start + batch_size
                ]

                await asyncio.to_thread(
                    spreadsheet.batch_update,
                    {
                        "requests":
                            batch
                    }
                )

                batch_count += 1

                print(
                    f"✅ Đã xử lý batch "
                    f"{batch_count}: "
                    f"{len(batch)} dòng"
                )

            # =================================================
            # HOÀN TẤT
            # =================================================

            print("=" * 60)

            print(
                "🎨 TÔ MÀU HOÀN TẤT"
            )

            print(
                f"📊 Tổng dòng: {total}"
            )

            print(
                f"✅ Đã tô: {success}"
            )

            print(
                f"⚠️ Bỏ qua: {skipped}"
            )

            print(
                f"📦 Batch: {batch_count}"
            )

            print("=" * 60)

            await ctx.send(
                "🎨 **TÔ MÀU SHEET 1 HOÀN TẤT!**\n\n"
                f"📊 Tổng dòng: **{total}**\n"
                f"✅ Đã tô màu: **{success}**\n"
                f"⚠️ Bỏ qua: **{skipped}**\n"
                f"📦 Số batch: **{batch_count}**",
                delete_after=15
            )

        except Exception as e:

            print()
            print("=" * 60)

            print(
                f"❌ LỖI !tomau: {e}"
            )

            print("=" * 60)

            await ctx.send(
                "❌ Không thể tô màu Sheet 1.\n"
                f"```{e}```",
                delete_after=10
            )


    # =====================================================
    # ERROR !TOMAU
    # =====================================================

    @tomau.error
    async def tomau_error(
        self,
        ctx,
        error
    ):

        if isinstance(
            error,
            commands.MissingPermissions
        ):

            await ctx.send(
                "❌ Bạn không có quyền "
                "sử dụng lệnh này.",
                delete_after=5
            )

        else:

            print(
                f"❌ Lỗi !tomau: {error}"
            )


# =========================================================
# SETUP
# =========================================================

async def setup(
    bot
):

    await bot.add_cog(
        RoleClass(bot)
    )

    print(
        "✅ Đã load role_class.py"
    )

    print(
        "🎨 Command: !tomau"
    )