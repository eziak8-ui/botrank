import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

# --- DANE BOTA I ROBLOXA ---
DISCORD_TOKEN = "TUTAJ_WKLEJ_TOKEN_BOTA_Z_DISCORDA"
ROBLOX_API_KEY = "ejymRU9lN0CmS1o0MoI7lvqu4nClhMCXCa+Pi8Q/+xk7j4PoZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNkluTnBaeTB5TURJeExUQTNMVEV6VkRFNE9qVXhPalE1V2lJc0luUjVjQ0k2SWtwWFZDSjkuZXlKaGRXUWlPaUpTYjJKc2IzaEpiblJsY201aGJDSXNJbWx6Y3lJNklrTnNiM1ZrUVhWMGFHVnVkR2xqWVhScGIyNVRaWEoyYVdObElpd2lZbUZ6WlVGd2FVdGxlU0k2SW1WcWVXMVNWVGxzVGpCRGJWTXhiekJOYjBrM2JIWnhkVFJ1UTJ4b1RVTllRMkVyVUdrNFVTOHJlR3MzYWpSUWJ5SXNJbTkzYm1WeVNXUWlPaUl4T1RFM09EZzJPVFE0SWl3aVpYaHdJam94Tnprd05UTTROakEyTENKcFlYUWlPakUzT1RBMU16VXdNRFlzSW01aVppSTZNVGM1TURVek5UQXdObjAuR0laVDZ0WGZMUk5reXpPOEFSbjNUTXhrbHFYcUtWZ2JmQWNvME1JdUJBOW5fLVlzXzJhN2JuTmUyTk5UT0QzQWg3a3FfNmxmRlJ1Sm9KQ0pQTUZFdkQzM2FTaFp1b3Z3UG40Y2lWTEU2ZWY3YUlPOERRWi05a05PdXJHR3dzNVNwWjhrSXJROGdZVFYxNDU0OVVLQVRpakI5ekhYejlNdTltMFNRd3Q5cDVYd3FHRmdyQXVFUnpFYWpCZHd4ekdBMkhvTWxMWUdjSTFyNEl0Q0RQeDN0TlM5ajRuQkl3VDV4a1d0cnJTQjZPR19UcjQxbW1MZXU1OG1PdkR5WVN6QVBTbTdLR2hLZ3kxVUlhVldROXBGS3VDQ1JLOTMxZGdvMGl2UWZ1d0dWOXd5N0R4X1hjaE5VcDZqZVZZQ1U5dUw3WFp6dldIZmV6X0RzSGthcm0wczZB"
GROUP_ID = "420651409"

# Podmień poniższe ID na prawdziwe Role ID z ustawień grupy na Robloxie:
ROLA_FOUNDER_ID = "11111111"       # Role ID dla: Group Founder
ROLA_CO_FOUNDER_ID = "22222222"    # Role ID dla: CO-Group Founder
ROLA_CAPO_ID = "33333333"          # Role ID dla: Capo

# Rola wymagana na Discordzie, żeby móc zarządzać swoim składem
ROLE_LEADER_DISCORD = "Group Founder"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Struktura do pilnowania limitów per lider:
# { lider_id: {"founder": [id], "co_founder": [id1, id2], "capo": [id1, id2]} }
limity_liderow = {}

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot PSB zalogowany jako {bot.user}")

@bot.tree.command(name="daj_range", description="Nadaj rangę swojemu członkowi ekipy na Robloxie")
@app_commands.describe(
    rola="Wybierz stanowisko do nadania",
    roblox_user_id="Wpisz Roblox ID gracza (same cyfry)"
)
@app_commands.choices(rola=[
    app_commands.Choice(name="Group Founder (limit: 1)", value="founder"),
    app_commands.Choice(name="CO-Group Founder (limit: 2)", value="co_founder"),
    app_commands.Choice(name="Capo (limit: 2)", value="capo")
])
async def daj_range(interaction: discord.Interaction, rola: app_commands.Choice[str], roblox_user_id: str):
    # 1. Sprawdzenie, czy piszący ma rolę lidera na Discordzie
    if not any(r.name == ROLE_LEADER_DISCORD for r in interaction.user.roles):
        await interaction.response.send_message("❌ Tylko liderzy (Group Founder) mają dostęp do tej komendy!", ephemeral=True)
        return

    lider_id = interaction.user.id
    if lider_id not in limity_liderow:
        limity_liderow[lider_id] = {
            "founder": [],
            "co_founder": [],
            "capo": []
        }

    dane_lidera = limity_liderow[lider_id]

    # 2. Definicja limitów i mapowanie ID rang Robloxa
    limity = {
        "founder": (1, ROLA_FOUNDER_ID, "Group Founder"),
        "co_founder": (2, ROLA_CO_FOUNDER_ID, "CO-Group Founder"),
        "capo": (2, ROLA_CAPO_ID, "Capo")
    }

    max_limit, role_id_do_nadania, nazwa_roli = limity[rola.value]

    # Sprawdzenie, czy gracz już nie dostał wcześniej tej rangi od tego lidera
    if roblox_user_id in dane_lidera[rola.value]:
        await interaction.response.send_message(f"❌ Ten gracz ma już przypisaną rangę **{nazwa_roli}**!", ephemeral=True)
        return

    # Sprawdzenie limitu slotów
    if len(dane_lidera[rola.value]) >= max_limit:
        await interaction.response.send_message(
            f"❌ Osiągnąłeś maksymalny limit dla rangi **{nazwa_roli}** ({max_limit}/{max_limit})!", 
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    # 3. Zapytanie do Roblox Open Cloud API v2
    url = f"https://apis.roblox.com/cloud/v2/groups/{GROUP_ID}/memberships/{roblox_user_id}"
    headers = {
        "x-api-key": ROBLOX_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "role": f"groups/{GROUP_ID}/roles/{role_id_do_nadania}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                dane_lidera[rola.value].append(roblox_user_id)
                uzyte = len(dane_lidera[rola.value])
                await interaction.followup.send(
                    f"✅ Pomyślnie nadano rangę **{nazwa_roli}** graczowi o ID `{roblox_user_id}`!\n"
                    f"Wykorzystane sloty: **{uzyte}/{max_limit}**."
                )
            else:
                blad = await resp.text()
                await interaction.followup.send(
                    f"❌ **Błąd Robloxa ({resp.status})**: Upewnij się, że gracz dołączył już do grupy!\n"
                    f"Szczegóły: `{blad}`"
                )

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
