import time
import requests
import aiohttp
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption

GROUP_ID = 0  # 여기에 실제 ROBLOX 그룹 ID 입력
ROLE_ID = 0  # 인증 성공시 부여할 역할 ID
REMOVE_ROLE_ID = 0  # 제거할 역할 ID
REMOVE_ROLE = True

intents = nextcord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.slash_command(name="인증", description="인증 절차를 진행합니다.")
async def verify(
    interaction: Interaction,
    닉네임: str = SlashOption(description="로블록스 닉네임을 입력하세요."),
    고유번호: int = SlashOption(description="고유번호를 입력하세요.")
):
    await interaction.response.defer(with_message=True)

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] /인증 사용: {interaction.user} - 채널: {interaction.channel.name}")

    roblox_username = 닉네임
    unique_number = 고유번호

    try:
        res = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames": [roblox_username]}
        )
        if res.status_code == 200:
            data = res.json()
            if data["data"]:
                roblox_username = data["data"][0]["name"]
                user_id = data["data"][0]["id"]
            else:
                raise ValueError("닉네임 존재하지 않음")
        else:
            raise Exception("API 호출 실패")
    except Exception as e:
        print(f"닉네임 확인 실패: {e}")
        error_embed = nextcord.Embed(
            title="닉네임 확인 실패",
            description="닉네임을 찾을 수 없습니다. 정확히 입력하셨는지 확인해주세요.",
            color=0xff0000
        )
        return await interaction.followup.send(embed=error_embed)

    in_group = False
    try:
        group_url = f"https://groups.roblox.com/v1/users/{user_id}/groups/roles"
        async with aiohttp.ClientSession() as session:
            async with session.get(group_url) as resp:
                if resp.status == 200:
                    group_data = await resp.json()
                    for group in group_data.get('data', []):
                        if group['group']['id'] == GROUP_ID:
                            in_group = True
                            break
    except Exception as e:
        print(f"그룹 확인 실패: {e}")

    if in_group:
        guild = interaction.guild
        member = interaction.user
        role = guild.get_role(ROLE_ID)
        remove_role = guild.get_role(REMOVE_ROLE_ID)

        try:
            if role:
                await member.add_roles(role)
            if REMOVE_ROLE and remove_role:
                await member.remove_roles(remove_role)

            try:
                new_nick = f"{unique_number} | {roblox_username} | 시민"
                await member.edit(nick=new_nick)
            except nextcord.Forbidden:
                print("닉네임 변경 권한 없음")

            success_embed = nextcord.Embed(
                title="인증 완료!",
                color=0x00ff00
            )
            success_embed.add_field(name="로블록스 닉네임", value=roblox_username, inline=True)
            success_embed.add_field(name="고유번호", value=unique_number, inline=True)
            await interaction.followup.send(embed=success_embed)
        except nextcord.Forbidden:
            await interaction.followup.send(content="❌ 봇에게 역할 부여 권한이 없습니다.")
    else:
        fail_embed = nextcord.Embed(
            title="그룹 미가입",
            color=0xff0000
        )
        fail_embed.add_field(name="로블록스 닉네임", value=roblox_username, inline=True)
        fail_embed.add_field(name="고유번호", value=unique_number, inline=True)
        fail_embed.set_footer(text="정확한 정보 입력 후 다시 시도해주세요.")
        await interaction.followup.send(embed=fail_embed)

@bot.event
async def on_ready():
    print(f"✅ 봇 로그인됨: {bot.user}")
    try:
        synced = await bot.sync_all_application_commands()
        print(f"🌐 슬래시 명령어 동기화 완료 ({len(synced)}개)")
    except Exception as e:
        print(f"명령어 동기화 실패: {e}")

bot.run("YOUR_DISCORD_BOT_TOKEN")
