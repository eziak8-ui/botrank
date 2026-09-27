import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

# --- DANE BOTA I ROBLOXA ---
DISCORD_TOKEN = "TUTAJ_WKLEJ_TOKEN_BOTA_Z_DISCORDA"
ROBLOX_API_KEY = "ejymRU9lN0CmS1o0MoI7lvqu4nClhMCXCa+Pi8Q/+xk7j4PoZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNkluTnBaeTB5TURJeExUQTNMVEV6VkRFNE9qVXhPalE1V2lJc0luUjVjQ0k2SWtwWFZDSjkuZXlKaGRXUWlPaUpTYjJKc2IzaEpiblJsY201aGJDSXNJbWx6Y3lJNklrTnNiM1ZrUVhWMGFHVnVkR2xqWVhScGIyNVRaWEoyYVdObElpd2lZbUZ6WlVGd2FVdGxlU0k2SW1WcWVXMVNWVGxzVGpCRGJWTXhiekJOYjBrM2JIWnhkVFJ1UTJ4b1RVTllRMkVyVUdrNFVTOHJlR3MzYWpSUWJ5SXNJbTkzYm1WeVNXUWlPaUl4T1RFM09EZzJPVFE0SWl3aVpYaHdJam94Tnprd05UTTROakEyTENKcFlYUWlPakUzT1RBMU16VXdNRFlzSW01aVppSTZNVGM1TURVek5UQXdObjAuR0laVDZ0WGZMUk5reXpPOEFSbjNUTXhrbHFYcUtWZ2JmQWNvME1JdUJBOW5fLVlzXzJhN2JuTmUyTk5UT0QzQWg3a3FfNmxmRlJ1Sm9KQ0pQTUZFdkQzM2FTaFp1b3Z3UG40Y2lWTEU2ZWY3YUlPOERRWi05a05PdXJHR3dzNVNwWjhrSXJROGdZVFYxNDU0OVVLQVRpakI5ekhYejlNdTltMFNRd3Q5cDVYd3FHRmdyQXVFUnpFYWpCZHd4ekdBMkhvTWxMWUdjSTFyNEl0Q0RQeDN0TlM5ajRuQkl3VDV4a1d0cnJTQjZPR19UcjQxbW1MZXU1OG1PdkR5WVN6QVBTbTdLR2hLZ3kxVUlhVldROXBGS3VDQ1JLOTMxZGdvMGl2UWZ1d0dWOXd5N0R4X1hjaE5VcDZqZVZZQ1U5dUw3WFp6dldIZmV6X0RzSGthcm0wczZB"
GROUP_ID = "420651409"
TARGET_ROLE_ID = "12345678"  # Podmień na prawdziwe ID rangi z grupy Roblox

ROLE_FOUNDER_NAME = "Group Founder"  # Nazwa rangi lidera na Twoim Discordzie

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Słownik pilnujący limitu 2 osób na lidera
limity_ekip = {}

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot PSB zalogowany jako {bot.user}")

@bot.tree.command(name="daj_range", description="Nadaj rangę członkowi ekipy na Robloxie (limit: 2 osoby)")
@app_commands.describe(roblox_user_id="Wpisz Roblox ID gracza (same cyfry z profilu)")
async def daj_range(interaction: discord.Interaction, roblox_user_id: str):
    # 1. Sprawdzenie uprawnień na Discordzie
    if not any(role.name == ROLE_FOUNDER_NAME for role in interaction.user.roles):
        await interaction.response.send_message("❌ Tylko liderzy z rangą 'Group Founder' mogą nadawać rangi!", ephemeral=True)
        return

    lider_id = interaction.user.id
    if lider_id not in limity_ekip:
        limity_ekip[lider_id] = []

    # 2. Sprawdzenie limitu
    if len(limity_ekip[lider_id]) >= 2:
        await interaction.response.send_message("❌ Osiągnąłeś już limit 2 osób dla swojej ekipy!", ephemeral=True)
        return

    if roblox_user_id in limity_ekip[lider_id]:
        await interaction.response.send_message("❌ Ten gracz ma już przypisaną rangę od Ciebie!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    # 3. Wysłanie zapytania do Roblox Open Cloud
    url = f"https://apis.roblox.com/cloud/v2/groups/{GROUP_ID}/memberships/{roblox_user_id}"
    headers = {
        "x-api-key": ROBLOX_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "role": f"groups/{GROUP_ID}/roles/{TARGET_ROLE_ID}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                limity_ekip[lider_id].append(roblox_user_id)
                await interaction.followup.send(
                    f"✅ **Sukces!** Nadano rangę graczowi `{roblox_user_id}`.\n"
                    f"Zajęte miejsca w ekipie: **{len(limity_ekip[lider_id])}/2**."
                )
            else:
                blad = await resp.text()
                await interaction.followup.send(
                    f"❌ **Błąd Robloxa ({resp.status})**: Gracz musi najpierw dołączyć do grupy na Robloxie!\nSzczegóły: `{blad}`"
                )

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
