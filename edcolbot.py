import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import re

DATA_FILE = 'efforts.json'

def load_token():
    if os.path.exists('token.txt'):
        with open('token.txt', 'r') as file:
            return file.read().strip()
    return None


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    return {}


def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)


data = load_data()


def get_next_effort_id():
    return str(max(map(int, data.keys()), default=0) + 1)

client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)
group = app_commands.Group(name="eco", description="E:D Colonization Organizer")
tree.add_command(group)

@client.event
async def on_ready():
    await tree.sync()
    print(f'Logged in as {client.user}')
    
@group.command(
    name="efforts",
    description="List all active colonization efforts."
)
async def efforts(interaction: discord.Interaction):
    if not data:
        await interaction.response.send_message(content="No active colonization efforts.", ephemeral=True)
        return

    message = "**Active Colonization Efforts:**\n"
    for effort_id, effort in data.items():
        if not effort.get("completed", False):
            message += effort_message(effort_id, effort) + "\n"
    await interaction.response.send_message(content=message)


@group.command(
    name="update",
    description="Update the materials required for a colonization effort."
)
@app_commands.describe(
    effort_id="The ID of the effort to update.",
    material_block="A list of materials and amounts to update."
)
async def update(interaction: discord.Interaction, effort_id: str, *, material_block: str):
    if effort_id not in data or data[effort_id].get("completed", False):
        await interaction.response.send_message(content="Effort ID not found or completed.", ephemeral=True)
        return

    materials = {}    
    for match in re.finditer(r'(\D+)\s([\d,]+)', material_block, re.S):
        commodity = match.group(1).upper().strip()
        amount = int(match.group(2).replace(',', ''))
        materials[commodity] = amount

    data[effort_id]['materials'] = materials
    save_data(data)
    await interaction.response.send_message(content=f"Updated materials for effort {effort_id}.")


@group.command(
    name="deliver",
    description="Deliver materials for a colonization effort."
)
@app_commands.describe(
    effort_id="The ID of the effort to update.",
    material_block="A list of materials and amounts to update."
)
async def deliver(interaction: discord.Interaction, effort_id: str, *, material_block: str):
    
    if effort_id not in data or data[effort_id].get("completed", False):
        await interaction.response.send_message(content="Effort ID not found or completed.", ephemeral=True)
        return
    
    materials = data[effort_id]['materials']
    message = ""
    for match in re.finditer(r'(\D+)\s([\d,]+)', material_block, re.S):
        commodity = match.group(1).upper().strip()
        amount = int(match.group(2).replace(',', ''))
        if materials[commodity]:
            materials[commodity] = max(0, materials[commodity] - amount)
        else:
            message += f"Material {commodity} not required for this effort.\n"
            return
        
        if materials[commodity] == 0:
            del materials[commodity]
            message += f"Delivered {amount} units of {commodity}. Requirement fulfilled and removed from the list.\n"
        else:
            message += f"Delivered {amount} units of {commodity}. Remaining: {materials[commodity]}\n"
    
    if not materials:
        data[effort_id]['completed'] = True
        message += f"All materials delivered! Marking effort {effort_id} as completed.\n"

    data[effort_id]['materials'] = materials
    save_data(data)
    await interaction.response.send_message(content=message + f"Updated materials for effort {effort_id}.")


@group.command(
    name="add",
    description="Add a new colonization effort."
)
@app_commands.describe(
    system="The system where the colonization effort is taking place.",
    installation="The type of installation being built.",
    owner="The owner of the colonization effort."
)
async def add_effort(interaction: discord.Interaction, system: str, installation: str, owner: str):
    effort_id = get_next_effort_id()
    
    data[effort_id] = {
        "system": system,
        "installation": installation,
        "owner": owner,
        "materials": {},
        "completed": False
    }
    save_data(data)
    await interaction.response.send_message(content=f"Added new colonization effort with ID {effort_id}.")

@group.command(
    name="effort",
    description="Show details for a specific colonization effort."
)
@app_commands.describe(
    effort_id="The ID of the effort to show details for."
)
async def effort(interaction: discord.Interaction, effort_id: str):
    if effort_id not in data or data[effort_id].get("completed", False):
        await interaction.response.send_message(content="Effort ID not found or completed.", ephemeral=True)
        return

    effort = data[effort_id]

    await interaction.response.send_message(content=effort_message(effort_id, effort))


def effort_message(effort_id, effort):
    message = f"{effort_id}. **{effort['system']} - {effort['installation']} ({effort['owner']})**\n"
    for material, amount in effort['materials'].items():
        message += f"  - {material}: {amount}\n"
    return message

TOKEN = load_token()

client.run(TOKEN)
