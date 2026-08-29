import discord
from discord.ext import commands

from channel_config import KICK_CHANNEL_ID
from sheets import delete_player

from discord_id import is_allowed_user


# =========================================================
# CẤU HÌNH
# =========================================================

ROLE_LAC_VIEN = "LẠC VIÊN"
ROLE_KHACH = "KHÁCH V.I.P"

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
# DEBUG
# =========================================================

print("============================================================")
print("🦵 LOAD KICK_MEM")
print("============================================================")

print(
    f"🦵 Kênh Kick: {KICK_CHANNEL_ID}"
)

print(
    f"🏷️ Role Lạc Viên: {ROLE_LAC_VIEN}"
)

print(
    f"🏷️ Role Khách: {ROLE_KHACH}"
)

print(
    f"⚔️ Số role môn phái: {len(MON_PHAI)}"
)

print("============================================================")


# =========================================================
# KIỂM TRA KÊNH
# =========================================================

if KICK_CHANNEL_ID is None:

    print(
        "❌ KICK_CHANNEL_ID chưa được cấu hình."
    )


# =========================================================
# COG
# =========================================================

class KickMember(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        print(
            "🦵 KickMember đã khởi tạo."
        )


    # =====================================================
    # COMMAND !lvkick
    #
    # Cách dùng:
    #
    # !lvkick @User
    #
    # !lvkick TênIGame
    #
    # !lvkick "Tên IGame"
    #
    # Người còn Discord:
    #   -> xử lý role
    #   -> xóa Sheet
    #
    # Người đã OUT:
    #   -> xóa Sheet bằng IGame
    # =====================================================

    @commands.command(
        name="lvkick"
    )
    async def kick(
        self,
        ctx,
        *args
    ):
        # =================================================
        # KIỂM TRA USER ĐƯỢC PHÉP SỬ DỤNG
        # =================================================

        if not is_allowed_user(ctx.author):

            await ctx.send(
                "❌ Bạn không có quyền sử dụng lệnh này.",
                delete_after=5
            )

            print(
                f"❌ Từ chối !lvkick: "
                f"{ctx.author} "
                f"(không có trong discord_ids.txt)"
            )

            return


        # =================================================
        # KIỂM TRA KÊNH
        # =================================================

        if KICK_CHANNEL_ID is None:

            await ctx.send(
                "❌ Chưa cấu hình kênh sử dụng lệnh `!lvkick`."
            )

            print(
                "❌ KICK_CHANNEL_ID = None"
            )

            return


        if ctx.channel.id != KICK_CHANNEL_ID:

            await ctx.send(
                f"❌ Lệnh `!lvkick` chỉ được sử dụng "
                f"trong <#{KICK_CHANNEL_ID}>."
            )

            print(
                f"❌ !lvkick sai kênh: "
                f"{ctx.channel.id}"
            )

            return


        # =================================================
        # KIỂM TRA SERVER
        # =================================================

        if ctx.guild is None:

            await ctx.send(
                "❌ Lệnh này chỉ sử dụng được trong server."
            )

            return


        # =================================================
        # BOT MEMBER
        # =================================================

        bot_member = ctx.guild.me

        if bot_member is None:

            await ctx.send(
                "❌ Không tìm thấy Bot Member."
            )

            return


        # =================================================
        # LẤY MENTION
        # =================================================

        mentions = list(
            ctx.message.mentions
        )


        # =================================================
        # LẤY IGAME
        #
        # Ví dụ:
        #
        # !lvkick Huyết Hà
        #
        # args sẽ là:
        #
        # ("Huyết", "Hà")
        #
        # ghép lại thành:
        #
        # Huyết Hà
        # =================================================

        igame = None

        if not mentions and args:

            igame = " ".join(
                args
            ).strip()


            # ---------------------------------------------
            # BỎ DẤU "
            #
            # !lvkick "Huyết Hà"
            # ---------------------------------------------

            if (
                len(igame) >= 2
                and igame.startswith('"')
                and igame.endswith('"')
            ):

                igame = igame[1:-1].strip()


            # ---------------------------------------------
            # BỎ DẤU '
            #
            # !lvkick 'Huyết Hà'
            # ---------------------------------------------

            elif (
                len(igame) >= 2
                and igame.startswith("'")
                and igame.endswith("'")
            ):

                igame = igame[1:-1].strip()


        # =================================================
        # KHÔNG CÓ INPUT
        # =================================================

        if not mentions and not igame:

            await ctx.send(
                "❌ Không tìm thấy người cần kick.\n\n"

                "**Người còn trong Discord:**\n"
                "`!lvkick @NgườiDùng`\n\n"

                "**Người đã out Discord:**\n"
                "`!lvkick TênIGame`\n\n"

                "**Ví dụ:**\n"
                "`!lvkick Huyết Hà`"
            )

            print(
                "❌ !lvkick không có mention hoặc IGame."
            )

            return


        # =================================================
        # TÌM ROLE
        # =================================================

        role_lac_vien = None
        role_khach = None


        for role in ctx.guild.roles:

            role_name = (
                role.name
                .strip()
                .lower()
            )


            # ---------------------------------------------
            # LẠC VIÊN
            # ---------------------------------------------

            if (
                role_name
                == ROLE_LAC_VIEN.lower()
            ):

                role_lac_vien = role


            # ---------------------------------------------
            # KHÁCH
            # ---------------------------------------------

            if (
                role_name
                == ROLE_KHACH.lower()
            ):

                role_khach = role


        # =================================================
        # KIỂM TRA ROLE LẠC VIÊN
        # =================================================

        if role_lac_vien is None:

            await ctx.send(
                f"❌ Không tìm thấy role "
                f"`{ROLE_LAC_VIEN}`."
            )

            print(
                f"❌ Không tìm thấy role "
                f"{ROLE_LAC_VIEN}"
            )

            return


        # =================================================
        # KIỂM TRA ROLE KHÁCH
        # =================================================

        if role_khach is None:

            await ctx.send(
                f"❌ Không tìm thấy role "
                f"`{ROLE_KHACH}`."
            )

            print(
                f"❌ Không tìm thấy role "
                f"{ROLE_KHACH}"
            )

            return


        # =================================================
        # KIỂM TRA QUYỀN BOT
        # =================================================

        if role_lac_vien >= bot_member.top_role:

            await ctx.send(
                f"❌ Bot không thể quản lý role "
                f"`{ROLE_LAC_VIEN}`.\n"
                f"Role cao nhất của Bot: "
                f"`{bot_member.top_role.name}`"
            )

            print(
                f"❌ Bot không thể quản lý "
                f"{ROLE_LAC_VIEN}"
            )

            return


        if role_khach >= bot_member.top_role:

            await ctx.send(
                f"❌ Bot không thể cấp role "
                f"`{ROLE_KHACH}`.\n"
                f"Role cao nhất của Bot: "
                f"`{bot_member.top_role.name}`"
            )

            print(
                f"❌ Bot không thể cấp role "
                f"{ROLE_KHACH}"
            )

            return


        # =================================================
        # DEBUG
        # =================================================

        print()
        print("============================================================")
        print("🦵 BẮT ĐẦU LVKICK")
        print("============================================================")

        print(
            f"👤 Người thực hiện: "
            f"{ctx.author} "
            f"(ID: {ctx.author.id})"
        )

        print(
            f"📍 Kênh: "
            f"{ctx.channel.name} "
            f"(ID: {ctx.channel.id})"
        )

        print(
            f"👥 Số người được tag: "
            f"{len(mentions)}"
        )

        if igame:

            print(
                f"🎮 IGame: "
                f"{igame}"
            )

        print("============================================================")


        # =================================================
        # KẾT QUẢ
        # =================================================

        success = []
        failed = []


        # =================================================
        # HÀM XỬ LÝ MEMBER ĐANG CÒN DISCORD
        # =================================================

        async def process_member(
            member
        ):

            print()
            print(
                "------------------------------------------------------------"
            )

            print(
                f"🎯 Đang xử lý: "
                f"{member} "
                f"(ID: {member.id})"
            )


            # =============================================
            # KHÔNG CHO KICK BOT
            # =============================================

            if member.bot:

                print(
                    f"⚠️ Bỏ qua bot: {member}"
                )

                failed.append(
                    f"{member.mention} → là Bot"
                )

                return


            # =============================================
            # KIỂM TRA ROLE USER
            # =============================================

            print(
                "🏷️ Role hiện tại:"
            )

            for role in member.roles:

                if role.is_default():
                    continue

                print(
                    f"   • {role.name}"
                )


            # =============================================
            # KIỂM TRA ROLE QUÁ CAO
            # =============================================

            unmanageable_roles = []

            for role in member.roles:

                if role.is_default():
                    continue

                if role >= bot_member.top_role:

                    unmanageable_roles.append(
                        role
                    )


            if unmanageable_roles:

                role_names = ", ".join(
                    role.name
                    for role in unmanageable_roles
                )

                print(
                    f"❌ Không thể quản lý role: "
                    f"{role_names}"
                )

                failed.append(
                    f"{member.mention} → "
                    f"role quá cao: {role_names}"
                )

                return


            # =============================================
            # XÁC ĐỊNH ROLE CẦN XÓA
            # =============================================

            roles_to_remove = []


            for role in member.roles:

                if role.is_default():
                    continue


                role_name = (
                    role.name
                    .strip()
                    .lower()
                )


                # -----------------------------------------
                # ROLE MÔN PHÁI
                # -----------------------------------------

                if role_name in [
                    mp.lower()
                    for mp in MON_PHAI
                ]:

                    roles_to_remove.append(
                        role
                    )

                    continue


                # -----------------------------------------
                # ROLE LẠC VIÊN
                # -----------------------------------------

                if (
                    role_name
                    == ROLE_LAC_VIEN.lower()
                ):

                    roles_to_remove.append(
                        role
                    )


            # =============================================
            # XÓA ROLE
            # =============================================

            if roles_to_remove:

                try:

                    await member.remove_roles(
                        *roles_to_remove,
                        reason=(
                            f"!lvkick bởi "
                            f"{ctx.author}"
                        )
                    )


                    for role in roles_to_remove:

                        print(
                            f"🗑️ Đã xóa role: "
                            f"{role.name}"
                        )


                except discord.Forbidden as e:

                    print(
                        f"❌ Không thể xóa role "
                        f"của {member}: {e}"
                    )

                    failed.append(
                        f"{member.mention} → "
                        f"không đủ quyền xóa role"
                    )

                    return


                except Exception as e:

                    print(
                        f"❌ Lỗi xóa role "
                        f"của {member}: {e}"
                    )

                    failed.append(
                        f"{member.mention} → "
                        f"lỗi xóa role"
                    )

                    return


            else:

                print(
                    "ℹ️ Người này không có "
                    "role Class/Lạc Viên."
                )


            # =============================================
            # CẤP ROLE KHÁCH
            # =============================================

            try:

                if role_khach not in member.roles:

                    await member.add_roles(
                        role_khach,
                        reason=(
                            f"!lvkick bởi "
                            f"{ctx.author}"
                        )
                    )

                    print(
                        "✅ Đã cấp role KHÁCH"
                    )

                else:

                    print(
                        "ℹ️ Người này đã có role KHÁCH."
                    )


            except discord.Forbidden as e:

                print(
                    f"❌ Không thể cấp role KHÁCH "
                    f"cho {member}: {e}"
                )

                failed.append(
                    f"{member.mention} → "
                    f"không thể cấp KHÁCH"
                )

                return


            except Exception as e:

                print(
                    f"❌ Lỗi cấp role KHÁCH: "
                    f"{e}"
                )

                failed.append(
                    f"{member.mention} → "
                    f"lỗi cấp KHÁCH"
                )

                return


            # =============================================
            # XÓA GOOGLE SHEETS
            # =============================================

            sheet_deleted = False

            try:

                sheet_deleted = delete_player(
                    member.id,
                    member.name
                )


                if sheet_deleted:

                    print(
                        f"🗑️ Đã xóa "
                        f"{member} "
                        f"khỏi Google Sheets."
                    )

                else:

                    print(
                        f"⚠️ Không tìm thấy "
                        f"{member} "
                        f"trong Google Sheets."
                    )


            except Exception as e:

                print(
                    f"❌ Lỗi xóa Google Sheets "
                    f"{member}: {e}"
                )


            # =============================================
            # THÀNH CÔNG
            # =============================================

            if sheet_deleted:

                success.append(
                    f"{member.mention} "
                    f"→ `KHÁCH` + 🗑️ Sheet"
                )

            else:

                success.append(
                    f"{member.mention} "
                    f"→ `KHÁCH`"
                )


            print(
                f"🎉 Hoàn tất xử lý: "
                f"{member}"
            )


        # =================================================
        # XỬ LÝ NGƯỜI ĐƯỢC TAG
        # =================================================

        for member in mentions:

            await process_member(
                member
            )


        # =================================================
        # XỬ LÝ IGAME
        #
        # !lvkick Huyết Hà
        #
        # Bước 1:
        # Tìm người đang còn trong server
        #
        # Bước 2:
        # Nếu không có -> người đã OUT
        #
        # Bước 3:
        # Xóa trực tiếp bằng tên nhân vật
        # =================================================

        if igame:

            print()
            print("============================================================")
            print(
                f"🔎 TÌM IGAME: {igame}"
            )
            print("============================================================")


            # =============================================
            # TÌM MEMBER TRONG SERVER
            #
            # Ưu tiên:
            # - username
            # - display name
            #
            # Nếu IGame trùng username/display name
            # thì xử lý member đó.
            # =============================================

            found_member = None

            igame_lower = (
                igame
                .strip()
                .lower()
            )


            for member in ctx.guild.members:

                if member.bot:
                    continue


                if (
                    member.name
                    .strip()
                    .lower()
                    == igame_lower
                ):

                    found_member = member

                    break


                if (
                    member.display_name
                    .strip()
                    .lower()
                    == igame_lower
                ):

                    found_member = member

                    break


            # =============================================
            # TÌM THẤY NGƯỜI TRONG SERVER
            # =============================================

            if found_member:

                print(
                    f"✅ Tìm thấy Discord member: "
                    f"{found_member}"
                )


                await process_member(
                    found_member
                )


            # =============================================
            # KHÔNG TÌM THẤY DISCORD MEMBER
            #
            # Người này có thể đã OUT.
            #
            # -> XÓA GOOGLE SHEETS BẰNG IGAME
            # =============================================

            else:

                print(
                    f"⚠️ Không tìm thấy "
                    f"{igame} "
                    f"trong Discord."
                )

                print(
                    "🔎 Giả định người này đã OUT Discord."
                )


                sheet_deleted = False


                try:

                    sheet_deleted = delete_player(
                        ten_nv=igame
                    )


                except Exception as e:

                    print(
                        f"❌ Lỗi xóa Google Sheets "
                        f"bằng IGame: {e}"
                    )


                # =========================================
                # XÓA THÀNH CÔNG
                # =========================================

                if sheet_deleted:

                    success.append(
                        f"`{igame}` "
                        f"→ ⚠️ Đã out Discord + 🗑️ Sheet"
                    )

                    print(
                        f"🗑️ Đã xóa "
                        f"{igame} "
                        f"khỏi Google Sheets."
                    )


                # =========================================
                # KHÔNG TÌM THẤY
                # =========================================

                else:

                    failed.append(
                        f"`{igame}` → "
                        f"không tìm thấy trong Sheet"
                    )

                    print(
                        f"⚠️ Không tìm thấy "
                        f"{igame} "
                        f"trong Google Sheets."
                    )


        # =================================================
        # KẾT QUẢ
        # =================================================

        print()
        print("============================================================")
        print("🦵 KẾT QUẢ LVKICK")
        print("============================================================")


        # =================================================
        # EMBED
        # =================================================

        embed = discord.Embed(
            title="🦵 KẾT QUẢ KICK",
            description=(
                f"Thực hiện bởi "
                f"{ctx.author.mention}"
            ),
            color=discord.Color.orange()
        )


        # =================================================
        # THÀNH CÔNG
        # =================================================

        if success:

            embed.add_field(
                name=(
                    f"✅ Thành công "
                    f"({len(success)})"
                ),
                value="\n".join(
                    success
                ),
                inline=False
            )

            print(
                "✅ Thành công:"
            )

            for item in success:

                print(
                    f"   {item}"
                )


        # =================================================
        # THẤT BẠI
        # =================================================

        if failed:

            embed.add_field(
                name=(
                    f"❌ Thất bại "
                    f"({len(failed)})"
                ),
                value="\n".join(
                    failed
                ),
                inline=False
            )

            print(
                "❌ Thất bại:"
            )

            for item in failed:

                print(
                    f"   {item}"
                )


        # =================================================
        # KHÔNG CÓ KẾT QUẢ
        # =================================================

        if not success and not failed:

            embed.description = (
                "❌ Không xử lý được người dùng nào."
            )


        # =================================================
        # GỬI KẾT QUẢ
        # =================================================

        await ctx.send(
            embed=embed
        )


        print(
            "============================================================"
        )

        print(
            "🏁 KẾT THÚC LVKICK"
        )

        print(
            "============================================================"


        )


# =========================================================
# SETUP DISCORD.PY 2.X
# =========================================================

async def setup(
    bot
):

    await bot.add_cog(
        KickMember(bot)
    )

    print(
        "🦵 Đã đăng ký module Kick."
    )