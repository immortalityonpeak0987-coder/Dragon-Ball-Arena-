import os
import random
import asyncio
import logging
from http import HTTPStatus
from datetime import datetime, timedelta

import uvicorn
from asgiref.wsgi import WsgiToAsgi
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

import psycopg2
from psycopg2.extras import RealDictCursor

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

FIGHT_GIF = "https://media.tenor.com/sN0v0yLgEPsAAAAC/goku-ultra-instinct.gif"
WELCOME_GIF = "https://media.tenor.com/F9lJaLPJAJAAAAAC/goku-dragon-ball.gif"

CHARACTER_ATTACKS = {

"Goku": [

"Kamehameha", "Spirit Bomb", "Dragon Fist",
"Instant Transmission Kamehameha"
],
"Vegeta":
["Galick Gun", "Final Flash", "Big Bang Attack", "Final Explosion"],
"Broly":
["Eraser Cannon", "Gigantic Meteor", "Blaster Shell", "Omega Blaster"],
"Gohan":
["Kamehameha", "Masenko", "Father-Son Kamehameha", "Ultimate Kamehameha"],
"Piccolo": [

"Special Beam Cannon", "Hellzone Grenade", "Light Grenade",
"Orange Kamehameha"
],
"Frieza": ["Death Beam", "Death Ball", "Supernova", "Golden Death Beam"],
"Cell":
["Kamehameha", "Special Beam Cannon", "Solar Flare", "Perfect Kamehameha"],
"Buu":
["Vanishing Ball", "Assault Rain", "Chocolate Beam", "Planet Burst"],
"Beerus":
["Sphere of Destruction", "Cataclysmic Orb", "Hakai", "Beerus Ball"],
"Whis": ["Kiai", "Staff Attack", "Temporal Rewind", "Angel Beam"],
"Jiren":
["Power Impact", "Glare", "Overheat Magnetron", "Ultimate Impact"],
"Hit":
["Time Skip", "Flash Fist Crush", "Vital Point Attack", "Cage of Time"],
"Gogeta": [

"Big Bang Kamehameha", "Stardust Breaker", "Soul Punisher",
"Meteor Explosion"
],
"Vegito":
["Final Kamehameha", "Spirit Sword", "Savage Strike", "Big Bang Attack"],
"Trunks":
["Burning Attack", "Finish Buster", "Sword Attack", "Final Hope Slash"],
"Goten": ["Kamehameha", "Assault", "Super Goten Strike", "Kikoha"],
"Gotenks": [

"Galactic Donut", "Super Ghost Kamikaze", "Charging Ultra Buu Buu",
"Victory Cannon"
],
"Krillin":
["Destructo Disc", "Kamehameha", "Solar Flare", "Scatter Kamehameha"],
"Tien": ["Tri-Beam", "Solar Flare", "Multi-Form", "Neo Tri-Beam"],
"Yamcha":
["Spirit Ball", "Wolf Fang Fist", "Kamehameha", "Neo Wolf Fang Fist"],
"Android": ["Energy Wave", "Photon Strike", "Barrier", "Hell Flash"],
"Cooler": [

"Death Beam", "Supernova Cooler", "Death Flash", "Golden Supernova"
],
"Janemba": [

"Bunkai Teleport", "Dimension Sword", "Lightning Shower Rain",
"Rakshasa Claw"
],
"Bojack": [

"Galactic Buster", "Grand Smasher", "Galactic Tyrant",
"Full Power Energy Wave"
],
"Zamasu": [

"Holy Wrath", "Divine Wrath", "Lightning of Absolution",
"Blades of Judgment"
],
"Black": [

"Black Kamehameha", "Black Power Ball", "Divine Lasso",
"Fierce God Slicer"
],
"Toppo": [

"Justice Flash", "Justice Tornado", "Hakai",
"God of Destruction's Wrath"
],
"Kefla": [

"Gigantic Burst", "Gigantic Breaker", "Ray Blast", "Gigantic Ray"
],
"Caulifla": [

"Crush Cannon", "Energy Wave", "Full Power Energy Wave",
"Super Saiyan Rage"
],
"Kale": ["Blaster Meteor", "Eraser Cannon", "Gigantic Omega", "Ray Blast"],
"Cabba":
["Galick Cannon", "Continuous Energy Bullet", "Galick Gun", "Final Flash"],
"Moro":
["Energy Drain", "Planet Destruction", "Copy Ability", "Earth Absorption"],
"Granolah": [

"Sniper Shot", "Hakai Sphere", "Clone Attack", "Full Power Blast"
],
"Gas": [
"Weapon Creation", "Telekinesis", "Power Strike", "Instinct Power"
],
"Omega": [

"Minus Energy Ball", "Dragon Thunder", "Whirlwind Spin",
"Gigantic Blaze"
],
"Baby": [

"Revenge Death Ball", "Super Galick Gun", "Revenge Blast",
"Final Flash"
],
"Super 17": [

"Flash Bomber", "Hell Storm", "Energy Absorption",
"Shocking Death Ball"
],
"default": [

"Energy Wave", "Ki Blast", "Power Strike", "Full Power Attack"
]
}

def get_character_attacks(char_name):
    for key in CHARACTER_ATTACKS:
        if key.lower() in char_name.lower():
            return CHARACTER_ATTACKS[key]
    return CHARACTER_ATTACKS["default"]


DRAGON_BALL_CHARACTERS = [

{

"name": "Goku (Base)",
"power": 100,
"rarity": "common"
},
{

"name": "Goku (Super Saiyan)",
"power": 500,
"rarity": "rare"
},
{

"name": "Goku (Super Saiyan 2)",
"power": 800,
"rarity": "rare"
},
{

"name": "Goku (Super Saiyan 3)",
"power": 1200,
"rarity": "epic"
},
{

"name": "Goku (Super Saiyan God)",
"power": 1800,
"rarity": "epic"
},
{

"name": "Goku (Super Saiyan Blue)",
"power": 2500,
"rarity": "legendary"
},
{

"name": "Goku (Ultra Instinct Sign)",
"power": 4000,
"rarity": "legendary"
},
{

"name": "Goku (Ultra Instinct)",
"power": 6000,
"rarity": "mythic"
},
{

"name": "Goku (Super Saiyan 4)",
"power": 3500,
"rarity": "legendary"
},
{

"name": "Vegeta (Base)",
"power": 95,
"rarity": "common"
},
{

"name": "Vegeta (Super Saiyan)",
"power": 480,
"rarity": "rare"
},
{

"name": "Vegeta (Super Saiyan 2)",
"power": 780,
"rarity": "rare"
},
{

"name": "Vegeta (Super Saiyan God)",
"power": 1750,
"rarity": "epic"
},
{

"name": "Vegeta (Super Saiyan Blue)",
"power": 2400,
"rarity": "legendary"
},
{

"name": "Vegeta (Super Saiyan Blue Evolution)",
"power": 3800,
"rarity": "legendary"
},
{

"name": "Vegeta (Ultra Ego)",
"power": 5800,
"rarity": "mythic"
},
{

"name": "Vegeta (Super Saiyan 4)",
"power": 3400,
"rarity": "legendary"
},
{

"name": "Broly (Base)",
"power": 150,
"rarity": "common"
},
{

"name": "Broly (Wrathful)",
"power": 1500,
"rarity": "epic"
},
{

"name": "Broly (Super Saiyan)",
"power": 3000,
"rarity": "legendary"
},
{

"name": "Broly (Legendary Super Saiyan)",
"power": 5000,
"rarity": "mythic"
},
{

"name": "Gohan (Kid)",
"power": 50,
"rarity": "common"
},
{

"name": "Gohan (Teen)",
"power": 200,
"rarity": "common"
},
{

"name": "Gohan (Super Saiyan 2 Teen)",
"power": 700,
"rarity": "rare"
},
{

"name": "Gohan (Ultimate)",
"power": 2000,
"rarity": "epic"
},
{

"name": "Gohan (Beast)",
"power": 6500,
"rarity": "mythic"
},
{

"name": "Piccolo",
"power": 200,
"rarity": "common"
},
{

"name": "Piccolo (Fused with Kami)",
"power": 600,
"rarity": "rare"
},
{

"name": "Piccolo (Orange)",
"power": 4500,
"rarity": "legendary"
},
{

"name": "Frieza (First Form)",
"power": 150,
"rarity": "common"
},
{

"name": "Frieza (Final Form)",
"power": 500,
"rarity": "rare"
},
{

"name": "Frieza (Golden)",
"power": 3200,
"rarity": "legendary"
},
{

"name": "Frieza (Black)",
"power": 7000,
"rarity": "mythic"
},
{

"name": "Cell (Imperfect)",
"power": 250,
"rarity": "common"
},
{

"name": "Cell (Perfect)",
"power": 600,
"rarity": "rare"
},
{

"name": "Cell (Super Perfect)",
"power": 750,
"rarity": "epic"
},
{

"name": "Cell Max",
"power": 5500,
"rarity": "mythic"
},
{

"name": "Majin Buu (Fat)",
"power": 700,
"rarity": "rare"
},
{

"name": "Super Buu",
"power": 850,
"rarity": "epic"
},
{

"name": "Kid Buu",
"power": 900,
"rarity": "epic"
},
{

"name": "Beerus",
"power": 8000,
"rarity": "mythic"
},
{

"name": "Whis",
"power": 10000,
"rarity": "mythic"
},
{

"name": "Jiren",
"power": 5500,
"rarity": "mythic"
},
{

"name": "Jiren (Full Power)",
"power": 7500,
"rarity": "mythic"
},
{

"name": "Hit",
"power": 2000,
"rarity": "legendary"
},
{

"name": "Trunks (Future)",
"power": 300,
"rarity": "rare"
},
{

"name": "Trunks (Super Saiyan Rage)",
"power": 2200,
"rarity": "legendary"
},
{

"name": "Goten",
"power": 150,
"rarity": "common"
},
{

"name": "Gotenks (Super Saiyan 3)",
"power": 800,
"rarity": "epic"
},
{

"name": "Vegito (Super Saiyan Blue)",
"power": 9000,
"rarity": "mythic"
},
{

"name": "Gogeta (Super Saiyan 4)",
"power": 8500,
"rarity": "mythic"
},
{

"name": "Gogeta (Super Saiyan Blue)",
"power": 9500,
"rarity": "mythic"
},
{

"name": "Krillin",
"power": 75,
"rarity": "common"
},
{

"name": "Tien",
"power": 80,
"rarity": "common"
},
{

"name": "Yamcha",
"power": 50,
"rarity": "common"
},
{

"name": "Android 17",
"power": 400,
"rarity": "rare"
},
{

"name": "Android 17 (DBS)",
"power": 2500,
"rarity": "legendary"
},
{

"name": "Android 18",
"power": 380,
"rarity": "rare"
},
{

"name": "Cooler (Final Form)",
"power": 550,
"rarity": "rare"
},
{

"name": "Cooler (Metal)",
"power": 1000,
"rarity": "epic"
},
{

"name": "Janemba",
"power": 900,
"rarity": "epic"
},
{

"name": "Super Janemba",
"power": 1300,
"rarity": "epic"
},
{

"name": "Bojack",
"power": 500,
"rarity": "rare"
},
{

"name": "Tapion",
"power": 350,
"rarity": "rare"
},
{

"name": "Bardock",
"power": 90,
"rarity": "common"
},
{

"name": "Zamasu (Fused)",
"power": 4000,
"rarity": "legendary"
},
{

"name": "Goku Black (Super Saiyan Rose)",
"power": 2800,
"rarity": "legendary"
},
{

"name": "Toppo (God of Destruction)",
"power": 4500,
"rarity": "legendary"
},
{

"name": "Kefla",
"power": 2200,
"rarity": "legendary"
},
{

"name": "Kefla (Super Saiyan 2)",
"power": 3500,
"rarity": "legendary"
},
{

"name": "Caulifla",
"power": 600,
"rarity": "rare"
},
{

"name": "Kale",
"power": 500,
"rarity": "rare"
},
{

"name": "Kale (Berserker)",
"power": 2500,
"rarity": "legendary"
},
{

"name": "Cabba",
"power": 700,
"rarity": "rare"
},
{

"name": "Master Roshi",
"power": 80,
"rarity": "common"
},
{

"name": "Mr. Satan",
"power": 10,
"rarity": "common"
},
{

"name": "Pan",
"power": 150,
"rarity": "common"
},
{

"name": "Omega Shenron",
"power": 4000,
"rarity": "legendary"
},
{

"name": "Baby Vegeta",
"power": 1500,
"rarity": "epic"
},
{

"name": "Super Baby 2",
"power": 2500,
"rarity": "legendary"
},
{

"name": "Super 17",
"power": 2800,
"rarity": "legendary"
},
{

"name": "Granolah",
"power": 5000,
"rarity": "legendary"
},
{

"name": "Gas",
"power": 5500,
"rarity": "mythic"
},
{

"name": "Moro",
"power": 4500,
"rarity": "legendary"
},
{

"name": "Gamma 1",
"power": 3000,
"rarity": "legendary"
},
{

"name": "Gamma 2",
"power": 3000,
"rarity": "legendary"
},
{

"name": "Goku (Mini - Daima)",
"power": 120,
"rarity": "rare"
},
{

"name": "Vegeta (Mini - Daima)",
"power": 115,
"rarity": "rare"
},
{

"name": "Glorio (Daima)",
"power": 200,
"rarity": "rare"
},
{

"name": "Gomah (Daima)",
"power": 50,
"rarity": "common"
},
{

"name": "Tamagami (Daima)",
"power": 1500,
"rarity": "epic"
},
{

"name": "Turles",
"power": 85,
"rarity": "common"
},
{

"name": "Lord Slug",
"power": 400,
"rarity": "rare"
},
{

"name": "Android 13",
"power": 450,
"rarity": "rare"
},
{

"name": "Super Android 13",
"power": 700,
"rarity": "epic"
},
{

"name": "Cumber",
"power": 4000,
"rarity": "legendary"
},
{

"name": "Hearts",
"power": 3500,
"rarity": "legendary"
},
{

"name": "Fu",
"power": 2500,
"rarity": "legendary"
},
{

"name": "Mechikabura",
"power": 8000,
"rarity": "mythic"
},
{

"name": "Xeno Goku",
"power": 7000,
"rarity": "mythic"
},
{

"name": "Xeno Vegeta",
"power": 6800,
"rarity": "mythic"
},
]

STARTER_CHARACTERS = [

{

"name": "Goku (Base)",
"power": 100,
"rarity": "common"
},
{

"name": "Vegeta (Base)",
"power": 95,
"rarity": "common"
},
{

"name": "Broly (Base)",
"power": 150,
"rarity": "common"
},
]

MAFUBA_TYPES = {

"ultra_pro": {

"name": "Mafuba Ultra Pro",
"catch_rate": 0.95,
"price": 500
},
"pro": {

"name": "Mafuba Pro",
"catch_rate": 0.75,
"price": 300
},
"power": {

"name": "Mafuba Power",
"catch_rate": 0.50,
"price": 150
},
"base": {

"name": "Mafuba Base",
"catch_rate": 0.30,
"price": 50
},
}

TOURNAMENT_ENTRY_FEE = 200
TOURNAMENT_MAFUBA_COUNT = 15
TOURNAMENT_CATCH_RATE = 0.30

MIN_DUEL_BET = 10

RARITY_EMOJIS = {

"common": "⚪",
"rare": "🔵",
"epic": "🟣",
"legendary": "🟡",
"mythic": "🔴"
}

def get_db_connection():

return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():

conn = get_db_connection()
cur = conn.cursor()

cur.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 100,
            mafuba_base INTEGER DEFAULT 3,
            mafuba_power INTEGER DEFAULT 1,
            mafuba_pro INTEGER DEFAULT 0,
            mafuba_ultra_pro INTEGER DEFAULT 0,
            tournament_mafuba INTEGER DEFAULT 0,
            in_tournament BOOLEAN DEFAULT FALSE,
            active_team INTEGER DEFAULT 1,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

cur.execute('''
        CREATE TABLE IF NOT EXISTS player_characters (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES players(user_id),
            name TEXT NOT NULL,
            power INTEGER NOT NULL,
            current_power INTEGER NOT NULL,
            rarity TEXT DEFAULT 'common',
            recruited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

cur.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES players(user_id),
            team_number INTEGER NOT NULL,
            character_id INTEGER REFERENCES player_characters(id),
            slot INTEGER NOT NULL,
            UNIQUE(user_id, team_number, slot)
        )
    ''')

cur.execute('''
        CREATE TABLE IF NOT EXISTS wild_spawns (
            user_id BIGINT PRIMARY KEY,
            name TEXT NOT NULL,
            power INTEGER NOT NULL,
            rarity TEXT DEFAULT 'common',
            spawned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

cur.execute('''
        CREATE TABLE IF NOT EXISTS duels (
            id SERIAL PRIMARY KEY,
            challenger_id BIGINT,
            defender_id BIGINT,
            bet_amount INTEGER,
            status TEXT DEFAULT 'pending',
            winner_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

cur.execute('''
        CREATE TABLE IF NOT EXISTS battle_sessions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            enemy_name TEXT,
            enemy_power INTEGER,
            enemy_current_power INTEGER,
            last_swap_time TIMESTAMP,
            active_char_slot INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

cur.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id BIGINT PRIMARY KEY,
            is_owner BOOLEAN DEFAULT FALSE,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

cur.execute('''
        CREATE TABLE IF NOT EXISTS approved_groups (
            group_id BIGINT PRIMARY KEY,
            approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

cur.execute('''
        CREATE TABLE IF NOT EXISTS daily_claims (
            user_id BIGINT PRIMARY KEY,
            last_claim TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

cur.execute('''
        CREATE TABLE IF NOT EXISTS duel_sessions (
            id SERIAL PRIMARY KEY,
            challenger_id BIGINT,
            defender_id BIGINT,
            bet_amount INTEGER,
            current_turn BIGINT,
            challenger_active_slot INTEGER DEFAULT 1,
            defender_active_slot INTEGER DEFAULT 1,
            last_action_time TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

conn.commit()
cur.close()
conn.close()

def is_owner(user_id):

conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT * FROM admins WHERE user_id = %s AND is_owner = TRUE",

(user_id, ))
result = cur.fetchone()
cur.close()
conn.close()
return result is not None

def is_admin(user_id):

conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT * FROM admins WHERE user_id = %s", (user_id, ))
result = cur.fetchone()
cur.close()
conn.close()
return result is not None

def is_approved_group(group_id):

conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT * FROM approved_groups WHERE group_id = %s",

(group_id, ))
result = cur.fetchone()
cur.close()
conn.close()
return result is not None

def can_use_admin_commands(user_id, chat_id, chat_type):

if not is_admin(user_id):

return False
if chat_type == "private":

return True
return is_approved_group(chat_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

welcome_msg = """
🐉 **DRAGON BALL ARENA** 🐉

Welcome, warrior! Begin your journey to become the greatest fighter in the universe!

🔥 **Commands:**
/register - Create your warrior profile
/open - Open battle menu
/catch - Find wild characters to catch
/shop - Buy Mafuba with coins
/team - Manage your teams
/stats - Check your progress
/daily - Claim daily rewards (bio required)
/tournament - Tournament of Power (Private only)
/duel - Challenge players (Reply to message)

Power up and become a legend! 💪
    """

await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):

user_id = update.effective_user.id
username = update.effective_user.username or update.effective_user.first_name or "Warrior"

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
existing = cur.fetchone()

if existing:

await update.message.reply_text(

"⚠️ You're already registered! Use /stats to see your profile."
)
return

keyboard = [[

InlineKeyboardButton("🔥 Goku (Power: 100)",

callback_data="starter_goku")
],

[

InlineKeyboardButton("👑 Vegeta (Power: 95)",

callback_data="starter_vegeta")
],
[

InlineKeyboardButton("💪 Broly (Power: 150)",

callback_data="starter_broly")
]]
reply_markup = InlineKeyboardMarkup(keyboard)

await update.message.reply_text(f"""
🎮 **WELCOME TO DRAGON BALL ARENA!** 🎮

Greetings, **{username}**! 🐉

You're about to embark on an epic journey through the Dragon Ball universe! 
Collect powerful warriors, battle fierce enemies, and become the ultimate champion!

**Choose your first warrior to begin:**
        """,

reply_markup=reply_markup,
parse_mode='Markdown')
except Exception as e:

logging.error(f"Registration error: {e}")
await update.message.reply_text("An error occurred. Please try again.")
finally:

cur.close()
conn.close()

async def starter_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

user_id = query.from_user.id
username = query.from_user.username or query.from_user.first_name or "Warrior"

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
if cur.fetchone():

await query.edit_message_text("⚠️ You're already registered!")
return

choice = query.data.replace("starter_", "")
starter_map = {"goku": 0, "vegeta": 1, "broly": 2}

if choice not in starter_map:

await query.edit_message_text(

"⚠️ Invalid selection. Please use /register again.")
return

starter = STARTER_CHARACTERS[starter_map[choice]]

cur.execute(
"""INSERT INTO players (user_id, username, level, xp, coins, mafuba_base, mafuba_power, mafuba_pro, mafuba_ultra_pro, is_admin) 
               VALUES (%s, %s, 1, 0, 100, 3, 1, 0, 0, FALSE)""",

(user_id, username))

cur.execute(
"""INSERT INTO player_characters (user_id, name, power, current_power, rarity) 
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",

(user_id, starter['name'], starter['power'], starter['power'],

starter['rarity']))
char_id = cur.fetchone()['id']

cur.execute(
"INSERT INTO teams (user_id, team_number, character_id, slot) VALUES (%s, 1, %s, 1)",

(user_id, char_id))

conn.commit()

welcome_message = f"""
🎉 **WELCOME TO DRAGON BALL ARENA, {username}!** 🎉

🐉✨ Your journey begins now! ✨🐉

You've chosen **{starter['name']}** as your first warrior!

📊 **Your Stats:**
- Level: 1
✨ XP: 0/50
💰 Coins: 100
🏺 Mafuba Base: 3
🏺 Mafuba Power: 1

🔥 **Quick Start:**
• Use /catch to find wild characters
• Use /open to access battle menu
• Use /team to manage your warriors
• Use /shop to buy more Mafuba

🌟 Train hard and become a legend! 🌟
May your power level rise beyond limits! 💪
        """

try:
await query.message.delete()
await context.bot.send_animation(chat_id=query.message.chat_id,

animation=WELCOME_GIF,
caption=welcome_message,
parse_mode='Markdown')
except Exception as gif_error:

logging.error(f"GIF error: {gif_error}")
await query.edit_message_text(welcome_message,

parse_mode='Markdown')

except Exception as e:

logging.error(f"Starter callback error: {e}")
conn.rollback()
await query.edit_message_text(

"An error occurred during registration. Please use /register again."
)
finally:

cur.close()
conn.close()

async def open_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

keyboard = [["/fight", "/close"]]
reply_markup = ReplyKeyboardMarkup(keyboard,
                                       resize_keyboard=True,
                                       one_time_keyboard=False)

await update.message.reply_text(
"🎮 **Battle Menu Opened!**\n\nChoose an action:",
reply_markup=reply_markup,
parse_mode='Markdown')

async def close_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

await update.message.reply_text("✅ Menu closed!",

reply_markup=ReplyKeyboardRemove())

async def catch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

user_id = update.effective_user.id

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()

if not player:

await update.message.reply_text("⚠️ You need to /register first!")
return

cur.execute("DELETE FROM wild_spawns WHERE user_id = %s", (user_id, ))
conn.commit()

if player.get('in_tournament'):

high_power_chars = [

c for c in DRAGON_BALL_CHARACTERS if c['power'] >= 1000
]
character = random.choice(high_power_chars)
else:

character = random.choice(DRAGON_BALL_CHARACTERS)

cur.execute(
"INSERT INTO wild_spawns (user_id, name, power, rarity) VALUES (%s, %s, %s, %s)",

(user_id, character['name'], character['power'],

character['rarity']))

conn.commit()

if player.get('in_tournament'):

keyboard = [[

InlineKeyboardButton("🏆 Tournament Mafuba (30%)",

callback_data="mafuba_tournament")
], [

InlineKeyboardButton("❌ Run Away", callback_data="mafuba_run")
]]
else:

keyboard = [[

InlineKeyboardButton("🏺 Mafuba Base (30%)",

callback_data="mafuba_base")
],

[

InlineKeyboardButton("⚡ Mafuba Power (50%)",

callback_data="mafuba_power")
],
[

InlineKeyboardButton("🔥 Mafuba Pro (75%)",

callback_data="mafuba_pro")
],
[

InlineKeyboardButton(

"💎 Mafuba Ultra Pro (95%)",
callback_data="mafuba_ultra_pro")
],
[

InlineKeyboardButton("❌ Run Away",

callback_data="mafuba_run")
]]

reply_markup = InlineKeyboardMarkup(keyboard)
rarity_emoji = RARITY_EMOJIS.get(character['rarity'], "⚪")

tournament_info = ""
if player.get('in_tournament'):

tournament_info = f"\n🏆 **Tournament Mafuba: {player.get('tournament_mafuba', 0)}**"

await update.message.reply_text(f"""
🌟 **WILD CHARACTER APPEARED!** 🌟

🐉 **{character['name']}**
💪 Power: {character['power']}
{rarity_emoji} Rarity: {character['rarity'].upper()}

Choose a Mafuba to catch!{tournament_info}

**Your Mafuba:**
🏺 Base: {player.get('mafuba_base', 0)}
⚡ Power: {player.get('mafuba_power', 0)}
🔥 Pro: {player.get('mafuba_pro', 0)}
💎 Ultra Pro: {player.get('mafuba_ultra_pro', 0)}
        """,

reply_markup=reply_markup,
parse_mode='Markdown')
except Exception as e:

logging.error(f"Catch error: {e}")
await update.message.reply_text("An error occurred. Please try again.")
finally:

cur.close()
conn.close()

async def mafuba_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

user_id = query.from_user.id
mafuba_type = query.data.replace("mafuba_", "")

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()

cur.execute("SELECT * FROM wild_spawns WHERE user_id = %s",

(user_id, ))
wild = cur.fetchone()

if not wild:

await query.edit_message_text(

"⚠️ No wild character here! Use /catch to find one.")
return

if mafuba_type == "run":

cur.execute("DELETE FROM wild_spawns WHERE user_id = %s",

(user_id, ))
conn.commit()
await query.edit_message_text(

"🏃 You ran away! Use /catch to find another character.")
return

if mafuba_type == "tournament":

if player.get('tournament_mafuba', 0) <= 0:

await query.edit_message_text(

"⚠️ No Tournament Mafuba left! Tournament ended.")
cur.execute(

"UPDATE players SET in_tournament = FALSE WHERE user_id = %s",

(user_id, ))
conn.commit()
return
catch_rate = TOURNAMENT_CATCH_RATE
cur.execute(

"UPDATE players SET tournament_mafuba = tournament_mafuba - 1 WHERE user_id = %s",

(user_id, ))
else:

mafuba_col = f"mafuba_{mafuba_type}"
if player.get(mafuba_col, 0) <= 0:

await query.edit_message_text(

f"⚠️ No {MAFUBA_TYPES[mafuba_type]['name']} left! Buy more at /shop"

)
return
catch_rate = MAFUBA_TYPES[mafuba_type]['catch_rate']
cur.execute(

f"UPDATE players SET {mafuba_col} = {mafuba_col} - 1 WHERE user_id = %s",

(user_id, ))

conn.commit()

success = random.random() < catch_rate

if success:

cur.execute(

"""INSERT INTO player_characters (user_id, name, power, current_power, rarity) 
                   VALUES (%s, %s, %s, %s, %s)""",

(user_id, wild['name'], wild['power'], wild['power'],

wild.get('rarity', 'common')))

xp_gain = max(10, wild['power'] // 50)
cur.execute("SELECT * FROM players WHERE user_id = %s",

(user_id, ))
player = cur.fetchone()

new_xp = player.get('xp', 0) + xp_gain
new_level = player.get('level', 1)
level_msg = ""

if new_xp >= 50:

new_level += 1
new_xp = 0
level_msg = f"\n\n🎉 **LEVEL UP!** You are now Level {new_level}!"

cur.execute(

"UPDATE players SET xp = %s, level = %s WHERE user_id = %s",

(new_xp, new_level, user_id))
cur.execute("DELETE FROM wild_spawns WHERE user_id = %s",

(user_id, ))
conn.commit()

await query.edit_message_text(f"""
✅ **CAUGHT!** ✅

🐉 **{wild['name']}** joined your team!
💪 Power: {wild['power']}
✨ +{xp_gain} XP!{level_msg}

Use /catch to find more!
            """,

parse_mode='Markdown')
else:

cur.execute("DELETE FROM wild_spawns WHERE user_id = %s",

(user_id, ))
conn.commit()

await query.edit_message_text(f"""
❌ **ESCAPED!** ❌

{wild['name']} broke free from the Mafuba!

Use /catch to try again!
            """,

parse_mode='Markdown')

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()
if player.get('in_tournament') and player.get('tournament_mafuba',
0) <= 0:
cur.execute(

"UPDATE players SET in_tournament = FALSE, tournament_mafuba = 0 WHERE user_id = %s",

(user_id, ))
conn.commit()
await query.message.reply_text(

"🏆 Tournament of Power ended! You're back to normal mode.")
except Exception as e:

logging.error(f"Mafuba callback error: {e}")
await query.edit_message_text(

"An error occurred. Please try /catch again.")
finally:

cur.close()
conn.close()

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):

user_id = update.effective_user.id

conn = get_db_connection()
cur = conn.cursor()
try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()

if not player:

await update.message.reply_text("⚠️ You need to /register first!")
return

keyboard = [[

InlineKeyboardButton("🏺 Base - 50 coins", callback_data="buy_base")
],

[

InlineKeyboardButton("⚡ Power - 150 coins",

callback_data="buy_power")
],
[

InlineKeyboardButton("🔥 Pro - 300 coins",

callback_data="buy_pro")
],
[

InlineKeyboardButton("💎 Ultra Pro - 500 coins",

callback_data="buy_ultra_pro")
],
[

InlineKeyboardButton("❌ Close",

callback_data="close_shop")
]]

reply_markup = InlineKeyboardMarkup(keyboard)

await update.message.reply_text(f"""
🛒 **MAFUBA SHOP** 🛒

💰 Your Coins: {player.get('coins', 0)}

**Available Mafuba:**
🏺 Base - 50 coins (30% catch rate)
⚡ Power - 150 coins (50% catch rate)
🔥 Pro - 300 coins (75% catch rate)
💎 Ultra Pro - 500 coins (95% catch rate)
        """,

reply_markup=reply_markup,
parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

if query.data == "close_shop":

await query.edit_message_text("Shop closed!")
return

user_id = query.from_user.id
mafuba_type = query.data.replace("buy_", "")

conn = get_db_connection()
cur = conn.cursor()
try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()

price = MAFUBA_TYPES[mafuba_type]['price']

if player.get('coins', 0) < price:

await query.edit_message_text(

f"⚠️ Not enough coins! You have {player.get('coins', 0)}, need {price}."

)
return

mafuba_col = f"mafuba_{mafuba_type}"
cur.execute(

f"UPDATE players SET coins = coins - %s, {mafuba_col} = {mafuba_col} + 1 WHERE user_id = %s",

(price, user_id))
conn.commit()
await query.edit_message_text(

f"✅ Bought {MAFUBA_TYPES[mafuba_type]['name']} for {price} coins!")
finally:

cur.close()
conn.close()

async def team(update: Update, context: ContextTypes.DEFAULT_TYPE):

user_id = update.effective_user.id

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()

if not player:

await update.message.reply_text("⚠️ You need to /register first!")
return

cur.execute(
"SELECT * FROM player_characters WHERE user_id = %s ORDER BY power DESC",

(user_id, ))
characters = cur.fetchall()

keyboard = []
for i in range(1, 7):

keyboard.append([

InlineKeyboardButton(f"📋 Team {i}",

callback_data=f"viewteam_{i}")
])
keyboard.append([

InlineKeyboardButton("🛠️ Build Team",

callback_data="buildteam_select")
])
keyboard.append([

InlineKeyboardButton("📋 All Characters",

callback_data="viewteam_all")
])
keyboard.append(

[InlineKeyboardButton("❌ Close", callback_data="close_shop")])

reply_markup = InlineKeyboardMarkup(keyboard)

await update.message.reply_text(f"""
📋 **YOUR COLLECTION** 📋

👥 Total Characters: {len(characters)}
🎯 Active Team: Team {player.get('active_team', 1)}

Select an option:
        """,

reply_markup=reply_markup,
parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def team_callback(update: Update,

context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

user_id = query.from_user.id
action = query.data.replace("viewteam_", "")

conn = get_db_connection()
cur = conn.cursor()

try:

if action == "all":

cur.execute(

"SELECT * FROM player_characters WHERE user_id = %s ORDER BY power DESC LIMIT 20",

(user_id, ))
chars = cur.fetchall()

if not chars:

await query.edit_message_text(

"No characters yet! Use /catch to find some.")
else:

char_list = "\n".join([

f"{RARITY_EMOJIS.get(c.get('rarity', 'common'), '⚪')} {c['name']} - Power: {c['power']}"

for c in chars
])
await query.edit_message_text(

f"📋 **All Characters (Top 20):**\n\n{char_list}",

parse_mode='Markdown')
else:

team_num = int(action)
cur.execute(

"""
                SELECT pc.*, t.slot FROM teams t 
                JOIN player_characters pc ON t.character_id = pc.id 
                WHERE t.user_id = %s AND t.team_number = %s 
                ORDER BY t.slot
""", (user_id, team_num))

team_chars = cur.fetchall()

keyboard = [[

InlineKeyboardButton("🔄 Set as Active",

callback_data=f"setactive_{team_num}")
], [InlineKeyboardButton("🔙 Back", callback_data="back_teams")]]
reply_markup = InlineKeyboardMarkup(keyboard)

if not team_chars:

await query.edit_message_text(

f"**Team {team_num}** is empty!\n\nUse 'Build Team' to add characters.",

reply_markup=reply_markup,
parse_mode='Markdown')
else:

char_list = "\n".join([

f"Slot {c['slot']}: 🐉 {c['name']} - Power: {c['power']}"

for c in team_chars
])
await query.edit_message_text(

f"**Team {team_num}:**\n\n{char_list}",

reply_markup=reply_markup,
parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def buildteam_callback(update: Update,

context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

user_id = query.from_user.id

if query.data == "buildteam_select":

keyboard = []
for i in range(1, 7):

keyboard.append([

InlineKeyboardButton(f"Team {i}",

callback_data=f"buildteam_{i}")
])
keyboard.append(

[InlineKeyboardButton("🔙 Back", callback_data="back_teams")])

await query.edit_message_text(

"Select a team to build:",

reply_markup=InlineKeyboardMarkup(keyboard))
return

team_num = int(query.data.replace("buildteam_", ""))
context.user_data['building_team'] = team_num
context.user_data['selected_chars'] = []

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute(

"DELETE FROM teams WHERE user_id = %s AND team_number = %s",

(user_id, team_num))
conn.commit()

cur.execute(

"SELECT * FROM player_characters WHERE user_id = %s ORDER BY power DESC LIMIT 20",

(user_id, ))
chars = cur.fetchall()

if not chars:

await query.edit_message_text(

"No characters available! Use /catch first.")
return

keyboard = []
for char in chars:

keyboard.append([

InlineKeyboardButton(f"{char['name']} ({char['power']})",

callback_data=f"selectchar_{char['id']}")
])
keyboard.append(

[InlineKeyboardButton("✅ Done", callback_data="buildteam_done")])
keyboard.append(

[InlineKeyboardButton("❌ Cancel", callback_data="back_teams")])

await query.edit_message_text(

f"🛠️ **Building Team {team_num}**\n\nSelect up to 4 characters:\n(Selected: 0/4)",

reply_markup=InlineKeyboardMarkup(keyboard),

parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def selectchar_callback(update: Update,

context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

user_id = query.from_user.id
char_id = int(query.data.replace("selectchar_", ""))

selected = context.user_data.get('selected_chars', [])
team_num = context.user_data.get('building_team', 1)

if char_id in selected:

selected.remove(char_id)
elif len(selected) < 4:

selected.append(char_id)
else:

await query.answer("Maximum 4 characters!", show_alert=True)
return

context.user_data['selected_chars'] = selected

conn = get_db_connection()
cur = conn.cursor()
try:

cur.execute(

"SELECT * FROM player_characters WHERE user_id = %s ORDER BY power DESC LIMIT 20",

(user_id, ))
chars = cur.fetchall()

keyboard = []
for char in chars:

prefix = "✅ " if char['id'] in selected else ""
keyboard.append([

InlineKeyboardButton(

f"{prefix}{char['name']} ({char['power']})",

callback_data=f"selectchar_{char['id']}"

)
])
keyboard.append(

[InlineKeyboardButton("✅ Done", callback_data="buildteam_done")])
keyboard.append(

[InlineKeyboardButton("❌ Cancel", callback_data="back_teams")])

await query.edit_message_text(

f"🛠️ **Building Team {team_num}**\n\nSelect up to 4 characters:\n(Selected: {len(selected)}/4)",

reply_markup=InlineKeyboardMarkup(keyboard),

parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def buildteam_done_callback(update: Update,

context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

user_id = query.from_user.id
selected = context.user_data.get('selected_chars', [])
team_num = context.user_data.get('building_team', 1)

if not selected:

await query.answer("Select at least 1 character!", show_alert=True)
return

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute(

"DELETE FROM teams WHERE user_id = %s AND team_number = %s",

(user_id, team_num))

for slot, char_id in enumerate(selected, 1):

cur.execute(

"INSERT INTO teams (user_id, team_number, character_id, slot) VALUES (%s, %s, %s, %s)",

(user_id, team_num, char_id, slot))

conn.commit()

context.user_data['selected_chars'] = []
context.user_data['building_team'] = None

await query.edit_message_text(

f"✅ Team {team_num} built with {len(selected)} characters!")
finally:

cur.close()
conn.close()

async def setactive_callback(update: Update,

context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

user_id = query.from_user.id
team_num = int(query.data.replace("setactive_", ""))

conn = get_db_connection()
cur = conn.cursor()
try:

cur.execute("UPDATE players SET active_team = %s WHERE user_id = %s",

(team_num, user_id))
conn.commit()
await query.edit_message_text(

f"✅ Team {team_num} is now your active team!")
finally:

cur.close()
conn.close()

async def back_teams_callback(update: Update,

context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

user_id = query.from_user.id

conn = get_db_connection()
cur = conn.cursor()
try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()
cur.execute(

"SELECT COUNT(*) as count FROM player_characters WHERE user_id = %s",

(user_id, ))
char_count = cur.fetchone()['count']

keyboard = []
for i in range(1, 7):

keyboard.append([

InlineKeyboardButton(f"📋 Team {i}",

callback_data=f"viewteam_{i}")
])
keyboard.append([

InlineKeyboardButton("🛠️ Build Team",

callback_data="buildteam_select")
])
keyboard.append([

InlineKeyboardButton("📋 All Characters",

callback_data="viewteam_all")
])
keyboard.append(

[InlineKeyboardButton("❌ Close", callback_data="close_shop")])

await query.edit_message_text(

f"""
📋 **YOUR COLLECTION** 📋

👥 Total Characters: {char_count}
🎯 Active Team: Team {player.get('active_team', 1)}

Select an option:
        """,

reply_markup=InlineKeyboardMarkup(keyboard),

parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def fight(update: Update, context: ContextTypes.DEFAULT_TYPE):

user_id = update.effective_user.id
chat_type = update.effective_chat.type

if chat_type != "private":

await update.message.reply_text(

"⚠️ Fighting is only available in private chat with the bot!")
return

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()

if not player:

await update.message.reply_text("⚠️ You need to /register first!")
return

cur.execute(

"""
            SELECT pc.* FROM teams t 
            JOIN player_characters pc ON t.character_id = pc.id 
            WHERE t.user_id = %s AND t.team_number = %s
            ORDER BY t.slot
        """, (user_id, player.get('active_team', 1)))

team_chars = cur.fetchall()

if not team_chars:

await update.message.reply_text(

f"⚠️ Team {player.get('active_team', 1)} is empty! Use /team to add characters."

)
return

enemy = random.choice(DRAGON_BALL_CHARACTERS)
your_fighter = team_chars[0]

cur.execute("DELETE FROM battle_sessions WHERE user_id = %s",

(user_id, ))
cur.execute(

"""
INSERT INTO battle_sessions (user_id, enemy_name, enemy_power, enemy_current_power, active_char_slot)
            VALUES (%s, %s, %s, %s, 1)
        """, (user_id, enemy['name'], enemy['power'], enemy['power']))

conn.commit()

attacks = get_character_attacks(your_fighter['name'])

keyboard = [[

InlineKeyboardButton(f"⚔️ {attacks[0]}",

callback_data="fight_attack_0")
],

[

InlineKeyboardButton(f"⚔️ {attacks[1]}",

callback_data="fight_attack_1")
],
[

InlineKeyboardButton(f"⚔️ {attacks[2]}",

callback_data="fight_attack_2")
],
[

InlineKeyboardButton(f"⚔️ {attacks[3]}",

callback_data="fight_attack_3")
],
[

InlineKeyboardButton("🔄 Swap Character",

callback_data="fight_swap")
],
[

InlineKeyboardButton("🏃 Run Away",

callback_data="fight_run")
]]

reply_markup = InlineKeyboardMarkup(keyboard)

try:

await update.message.reply_animation(animation=FIGHT_GIF,
                                                 caption=f"""
⚔️ **BATTLE BEGINS!** ⚔️

🔵 **YOUR FIGHTER:**
{your_fighter['name']}
💪 Power: {your_fighter.get('current_power', your_fighter['power'])}/{your_fighter['power']}

🔴 **ENEMY:**
{enemy['name']}
💪 Power: {enemy['power']}

Choose your attack!
                """,
                                                 reply_markup=reply_markup,
                                                 parse_mode='Markdown')

except Exception as e:

logging.error(f"GIF error: {e}")
await update.message.reply_text(f"""
⚔️ **BATTLE BEGINS!** ⚔️

🔵 **YOUR FIGHTER:**
{your_fighter['name']}
💪 Power: {your_fighter.get('current_power', your_fighter['power'])}/{your_fighter['power']}

🔴 **ENEMY:**
{enemy['name']}
💪 Power: {enemy['power']}

Choose your attack!
            """,

reply_markup=reply_markup,
parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def fight_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

user_id = query.from_user.id
action = query.data.replace("fight_", "")

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()

cur.execute("SELECT * FROM battle_sessions WHERE user_id = %s",

(user_id, ))
battle = cur.fetchone()

if not battle:

await query.edit_message_text(

"⚠️ No active battle! Use /fight to start one.")
return

cur.execute(

"""
            SELECT pc.*, t.slot FROM teams t 
            JOIN player_characters pc ON t.character_id = pc.id 
            WHERE t.user_id = %s AND t.team_number = %s AND t.slot = %s
        """, (user_id, player.get('active_team',

1), battle['active_char_slot']))

current_fighter = cur.fetchone()

if not current_fighter:

await query.edit_message_text("⚠️ Error finding your fighter!")
return

if action == "run":

cur.execute("DELETE FROM battle_sessions WHERE user_id = %s",

(user_id, ))
conn.commit()
await query.edit_message_text("🏃 You ran away from the battle!")
return

if action == "swap":

cur.execute(

"""
                SELECT pc.*, t.slot FROM teams t 
                JOIN player_characters pc ON t.character_id = pc.id 
                WHERE t.user_id = %s AND t.team_number = %s AND t.slot != %s AND pc.current_power > 0
            """, (user_id, player.get('active_team', 1), battle['active_char_slot']))

available = cur.fetchall()

if not available:

await query.answer("No other characters available!",

show_alert=True)
return

if battle.get('last_swap_time'):

elapsed = (datetime.now() -

battle['last_swap_time']).total_seconds()

if elapsed < 5:

await query.answer(

f"Swap cooldown! Wait {int(5 - elapsed)}s",

show_alert=True)
return

keyboard = []
for char in available:

keyboard.append([

InlineKeyboardButton(

f"{char['name']} ({char['current_power']} HP)",

callback_data=f"swap_{char['slot']}"

)
])
keyboard.append(

[InlineKeyboardButton("🔙 Back", callback_data="fight_back")])

await query.edit_message_text(

"🔄 Select a character to swap:",

reply_markup=InlineKeyboardMarkup(keyboard))
return

if action == "back":

attacks = get_character_attacks(current_fighter['name'])
keyboard = [

[

InlineKeyboardButton(f"⚔️ {attacks[0]}",

callback_data="fight_attack_0")
],

[

InlineKeyboardButton(f"⚔️ {attacks[1]}",

callback_data="fight_attack_1")
],
[

InlineKeyboardButton(f"⚔️ {attacks[2]}",

callback_data="fight_attack_2")
],
[

InlineKeyboardButton(f"⚔️ {attacks[3]}",

callback_data="fight_attack_3")
],
[

InlineKeyboardButton("🔄 Swap Character",

callback_data="fight_swap")
],
[

InlineKeyboardButton("🏃 Run Away",

callback_data="fight_run")
]

]
await query.edit_message_text(

f"""
⚔️ **BATTLE!** ⚔️

🔵 {current_fighter['name']} - {current_fighter['current_power']} HP
🔴 {battle['enemy_name']} - {battle['enemy_current_power']} HP

Choose your attack!
            """,

reply_markup=InlineKeyboardMarkup(keyboard),

parse_mode='Markdown')
return

if action.startswith("attack_"):

attack_idx = int(action.replace("attack_", ""))
attacks = get_character_attacks(current_fighter['name'])
attack_name = attacks[attack_idx]

instant_transmission_dodge = random.random() < 0.15

if instant_transmission_dodge:

enemy_damage = random.randint(

battle['enemy_current_power'] // 5,
battle['enemy_current_power'] // 3)
new_your_power = max(

0, current_fighter['current_power'] - enemy_damage)

cur.execute(

"UPDATE player_characters SET current_power = %s WHERE id = %s",

(new_your_power, current_fighter['id']))
conn.commit()

attacks = get_character_attacks(current_fighter['name'])
keyboard = [

[

InlineKeyboardButton(f"⚔️ {attacks[0]}",

callback_data="fight_attack_0")
],

[

InlineKeyboardButton(f"⚔️ {attacks[1]}",

callback_data="fight_attack_1")
],
[

InlineKeyboardButton(f"⚔️ {attacks[2]}",

callback_data="fight_attack_2")
],
[

InlineKeyboardButton(f"⚔️ {attacks[3]}",

callback_data="fight_attack_3")
],
[

InlineKeyboardButton("🔄 Swap Character",

callback_data="fight_swap")
],
[

InlineKeyboardButton("🏃 Run Away",

callback_data="fight_run")
]

]

await query.edit_message_text(

f"""
💨 **INSTANT TRANSMISSION!** 💨

{battle['enemy_name']} dodged your {attack_name}!
Enemy countered for {enemy_damage} damage!

🔵 {current_fighter['name']} - {new_your_power} HP
🔴 {battle['enemy_name']} - {battle['enemy_current_power']} HP
                """,

reply_markup=InlineKeyboardMarkup(keyboard),

parse_mode='Markdown')
return

your_damage = random.randint(current_fighter['current_power'] // 4,

current_fighter['current_power'] // 2)

enemy_damage = random.randint(battle['enemy_current_power'] // 6,

battle['enemy_current_power'] // 4)

new_enemy_power = max(0,

battle['enemy_current_power'] - your_damage)
new_your_power = max(

0, current_fighter['current_power'] - enemy_damage)

cur.execute(

"UPDATE battle_sessions SET enemy_current_power = %s WHERE user_id = %s",

(new_enemy_power, user_id))
cur.execute(

"UPDATE player_characters SET current_power = %s WHERE id = %s",

(new_your_power, current_fighter['id']))
conn.commit()

if new_enemy_power <= 0:

xp_gain = max(15, battle['enemy_power'] // 30)
coin_gain = max(10, battle['enemy_power'] // 20)
new_xp = player.get('xp', 0) + xp_gain
new_level = player.get('level', 1)
level_msg = ""

if new_xp >= 50:

new_level += 1
new_xp = 0
level_msg = f"\n🎉 **LEVEL UP!** Now Level {new_level}!"

cur.execute(

"UPDATE players SET xp = %s, level = %s, coins = coins + %s WHERE user_id = %s",

(new_xp, new_level, coin_gain, user_id))
cur.execute(

"UPDATE player_characters SET current_power = power WHERE user_id = %s",

(user_id, ))
cur.execute("DELETE FROM battle_sessions WHERE user_id = %s",

(user_id, ))
conn.commit()

await query.edit_message_text(f"""
🏆 **VICTORY!** 🏆

{current_fighter['name']} used {attack_name}!
{battle['enemy_name']} was defeated!

✨ +{xp_gain} XP
💰 +{coin_gain} Coins{level_msg}
                """,

parse_mode='Markdown')
elif new_your_power <= 0:

cur.execute(

"""
                    SELECT pc.*, t.slot FROM teams t 
                    JOIN player_characters pc ON t.character_id = pc.id 
                    WHERE t.user_id = %s AND t.team_number = %s AND pc.current_power > 0
                    ORDER BY t.slot LIMIT 1
                """, (user_id, player.get('active_team', 1)))

next_fighter = cur.fetchone()

if next_fighter:

cur.execute(

"UPDATE battle_sessions SET active_char_slot = %s WHERE user_id = %s",

(next_fighter['slot'], user_id))
conn.commit()

attacks = get_character_attacks(next_fighter['name'])
keyboard = [[

InlineKeyboardButton(f"⚔️ {attacks[0]}",

callback_data="fight_attack_0")
],

[

InlineKeyboardButton(

f"⚔️ {attacks[1]}",

callback_data="fight_attack_1")
],
[

InlineKeyboardButton(

f"⚔️ {attacks[2]}",

callback_data="fight_attack_2")
],
[

InlineKeyboardButton(

f"⚔️ {attacks[3]}",

callback_data="fight_attack_3")
],
[

InlineKeyboardButton(

"🔄 Swap Character",

callback_data="fight_swap")
],
[

InlineKeyboardButton(

"🏃 Run Away",

callback_data="fight_run")
]]

await query.edit_message_text(

f"""
💥 {current_fighter['name']} fainted!

{next_fighter['name']} enters the battle!

🔵 {next_fighter['name']} - {next_fighter['current_power']} HP
🔴 {battle['enemy_name']} - {new_enemy_power} HP
                    """,

reply_markup=InlineKeyboardMarkup(keyboard),

parse_mode='Markdown')
else:

cur.execute(

"UPDATE player_characters SET current_power = power WHERE user_id = %s",

(user_id, ))

cur.execute(

"DELETE FROM battle_sessions WHERE user_id = %s",

(user_id, ))
conn.commit()

await query.edit_message_text(f"""
💔 **DEFEAT!** 💔

All your fighters fainted!
{battle['enemy_name']} wins this round.

Train harder and try again!
                    """,

parse_mode='Markdown')
else:

attacks = get_character_attacks(current_fighter['name'])
keyboard = [

[

InlineKeyboardButton(f"⚔️ {attacks[0]}",

callback_data="fight_attack_0")
],

[

InlineKeyboardButton(f"⚔️ {attacks[1]}",

callback_data="fight_attack_1")
],
[

InlineKeyboardButton(f"⚔️ {attacks[2]}",

callback_data="fight_attack_2")
],
[

InlineKeyboardButton(f"⚔️ {attacks[3]}",

callback_data="fight_attack_3")
],
[

InlineKeyboardButton("🔄 Swap Character",

callback_data="fight_swap")
],
[

InlineKeyboardButton("🏃 Run Away",

callback_data="fight_run")
]

]

await query.edit_message_text(

f"""
⚔️ **BATTLE!** ⚔️

You used **{attack_name}** for {your_damage} damage!
Enemy countered for {enemy_damage} damage!

🔵 {current_fighter['name']} - {new_your_power} HP
🔴 {battle['enemy_name']} - {new_enemy_power} HP
                """,

reply_markup=InlineKeyboardMarkup(keyboard),

parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def swap_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

user_id = query.from_user.id
slot = int(query.data.replace("swap_", ""))

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute(

"UPDATE battle_sessions SET active_char_slot = %s, last_swap_time = NOW() WHERE user_id = %s",

(slot, user_id))
conn.commit()

cur.execute("SELECT * FROM battle_sessions WHERE user_id = %s",

(user_id, ))
battle = cur.fetchone()

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()

cur.execute("SELECT * FROM teams t "

"JOIN player_characters pc ON t.character_id = pc.id "

"WHERE t.user_id = %s AND t.team_number = %s AND t.slot = %s",

(user_id, player.get('active_team', 1), slot))

new_fighter = cur.fetchone()

attacks = get_character_attacks(new_fighter['name'])
keyboard = [[

InlineKeyboardButton(f"⚔️ {attacks[0]}",

callback_data="fight_attack_0")
],

[

InlineKeyboardButton(f"⚔️ {attacks[1]}",

callback_data="fight_attack_1")
],
[

InlineKeyboardButton(f"⚔️ {attacks[2]}",

callback_data="fight_attack_2")
],
[

InlineKeyboardButton(f"⚔️ {attacks[3]}",

callback_data="fight_attack_3")
],
[

InlineKeyboardButton("🔄 Swap Character",

callback_data="fight_swap")
],
[

InlineKeyboardButton("🏃 Run Away",

callback_data="fight_run")
]]

await query.edit_message_text(

f"""
🔄 **SWAPPED!**

{new_fighter['name']} enters battle!

🔵 {new_fighter['name']} - {new_fighter['current_power']} HP
🔴 {battle['enemy_name']} - {battle['enemy_current_power']} HP
        """,

reply_markup=InlineKeyboardMarkup(keyboard),

parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def tournament(update: Update, context: ContextTypes.DEFAULT_TYPE):

user_id = update.effective_user.id
chat_type = update.effective_chat.type

if chat_type != "private":

await update.message.reply_text(

"⚠️ Tournament of Power is only available in private chat!")
return

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()

if not player:

await update.message.reply_text("⚠️ You need to /register first!")
return

if player.get('in_tournament'):

await update.message.reply_text(f"""
🏆 **TOURNAMENT OF POWER** 🏆

You're in the tournament!
🏺 Tournament Mafuba: {player.get('tournament_mafuba', 0)}

Use /catch to find powerful characters!
            """,

parse_mode='Markdown')
return

keyboard = [[

InlineKeyboardButton(f"🏆 Enter ({TOURNAMENT_ENTRY_FEE} coins)",

callback_data="enter_tournament")
], [InlineKeyboardButton("❌ Cancel", callback_data="close_shop")]]

await update.message.reply_text(

f"""
🏆 **TOURNAMENT OF POWER** 🏆

Entry Fee: {TOURNAMENT_ENTRY_FEE} coins
Your Coins: {player.get('coins', 0)}

**Rewards:**
🏺 15 Tournament Mafuba
⚡ High-level characters spawn!
🎯 30% catch rate

Ready to enter?
        """,

reply_markup=InlineKeyboardMarkup(keyboard),

parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def tournament_callback(update: Update,

context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

user_id = query.from_user.id

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
player = cur.fetchone()

if player.get('coins', 0) < TOURNAMENT_ENTRY_FEE:

await query.edit_message_text(

f"⚠️ Not enough coins! Need {TOURNAMENT_ENTRY_FEE}, have {player.get('coins', 0)}."

)
return

cur.execute(

"""
            UPDATE players SET 
                coins = coins - %s, 
                in_tournament = TRUE, 
                tournament_mafuba = %s 
            WHERE user_id = %s
        """, (TOURNAMENT_ENTRY_FEE, TOURNAMENT_MAFUBA_COUNT, user_id))

conn.commit()

await query.edit_message_text(f"""
🏆 **WELCOME TO TOURNAMENT OF POWER!** 🏆

You received 15 Tournament Mafuba!

Use /catch to find powerful characters!
Good luck, warrior!
        """,

parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):

if not update.message.reply_to_message:

await update.message.reply_text(

"⚠️ Reply to a user's message with /duel to challenge them!")
return

challenger_id = update.effective_user.id
defender_id = update.message.reply_to_message.from_user.id
defender_name = update.message.reply_to_message.from_user.first_name or "Opponent"
challenger_name = update.effective_user.first_name or "Challenger"

if challenger_id == defender_id:

await update.message.reply_text("⚠️ You can't duel yourself!")
return

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM players WHERE user_id = %s",

(challenger_id, ))
challenger = cur.fetchone()
cur.execute("SELECT * FROM players WHERE user_id = %s",

(defender_id, ))
defender = cur.fetchone()

if not challenger:

await update.message.reply_text("⚠️ You need to /register first!")
return

if not defender:

await update.message.reply_text(

"⚠️ The other player needs to register first!")
return

cur.execute(

"""
            INSERT INTO duels (challenger_id, defender_id, bet_amount, status)
            VALUES (%s, %s, %s, 'pending') RETURNING id
        """, (challenger_id, defender_id, MIN_DUEL_BET))

duel_id = cur.fetchone()['id']
conn.commit()

keyboard = [

[

InlineKeyboardButton(f"🎲 Bet 10",

callback_data=f"duelbet_{duel_id}_10")
],

[

InlineKeyboardButton(f"💰 Bet 50",

callback_data=f"duelbet_{duel_id}_50")
],
[

InlineKeyboardButton(f"🔥 Bet 100",

callback_data=f"duelbet_{duel_id}_100")
],
[

InlineKeyboardButton(f"💎 Bet 200",

callback_data=f"duelbet_{duel_id}_200")
],
[

InlineKeyboardButton("❌ Cancel",

callback_data=f"duelcancel_{duel_id}")
]

]

await update.message.reply_text(

f"""
⚔️ **DUEL CHALLENGE!** ⚔️

**{challenger_name}** wants to duel **{defender_name}**!

{challenger_name}, choose your bet amount:
(Winner gets 2x the bet!)
        """,

reply_markup=InlineKeyboardMarkup(keyboard),

parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def duel_bet_callback(update: Update,

context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

user_id = query.from_user.id

parts = query.data.replace("duelbet_", "").split("_")
duel_id = int(parts[0])
bet_amount = int(parts[1])

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM duels WHERE id = %s", (duel_id, ))
duel = cur.fetchone()

if not duel:

await query.answer("Duel not found!", show_alert=True)
return

if user_id != duel['challenger_id']:

await query.answer("Only the challenger can set the bet!",

show_alert=True)
return

cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
challenger = cur.fetchone()

if challenger.get('coins', 0) < bet_amount:

await query.answer(f"Not enough coins! Need {bet_amount}.",

show_alert=True)
return

cur.execute("UPDATE duels SET bet_amount = %s WHERE id = %s",

(bet_amount, duel_id))
conn.commit()

keyboard = [[

InlineKeyboardButton("✅ Accept Duel",

callback_data=f"duelaccept_{duel_id}")
],

[

InlineKeyboardButton(

"❌ Decline",

callback_data=f"dueldecline_{duel_id}")
]]

await query.edit_message_text(

f"""
⚔️ **DUEL PENDING** ⚔️

💰 Bet Amount: {bet_amount} coins
🏆 Winner gets: {bet_amount * 2} coins!

Waiting for opponent to accept...
        """,

reply_markup=InlineKeyboardMarkup(keyboard),

parse_mode='Markdown')
finally:

cur.close()
conn.close()

async def duel_cancel_callback(update: Update,

context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

duel_id = int(query.data.replace("duelcancel_", ""))

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("UPDATE duels SET status = 'cancelled' WHERE id = %s",

(duel_id, ))
conn.commit()
await query.edit_message_text("❌ Duel cancelled!")
finally:

cur.close()
conn.close()

async def duel_accept_callback(update: Update,

context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

user_id = query.from_user.id

duel_id = int(query.data.replace("duelaccept_", ""))

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM duels WHERE id = %s", (duel_id, ))
duel = cur.fetchone()

if not duel:

await query.answer("Duel not found!", show_alert=True)
return

if user_id != duel['defender_id']:

await query.answer("Only the challenged player can accept!",

show_alert=True)
return

if duel['status'] != 'pending':

await query.answer("This duel is no longer active!",

show_alert=True)
return

cur.execute("SELECT * FROM players WHERE user_id = %s",

(duel['defender_id'], ))
defender = cur.fetchone()

if defender.get('coins', 0) < duel['bet_amount']:

await query.answer(f"Not enough coins! Need {duel['bet_amount']}.",

show_alert=True)
return

# Deduct bet from both

cur.execute("UPDATE players SET coins = coins - %s WHERE user_id = %s", (duel['bet_amount'], duel['challenger_id']))
cur.execute("UPDATE players SET coins = coins - %s WHERE user_id = %s", (duel['bet_amount'], duel['defender_id']))

# Reset current_power for both teams

cur.execute("UPDATE player_characters SET current_power = power WHERE user_id = %s", (duel['challenger_id'], ))
cur.execute("UPDATE player_characters SET current_power = power WHERE user_id = %s", (duel['defender_id'], ))

# Create duel session

cur.execute("""
            INSERT INTO duel_sessions (challenger_id, defender_id, bet_amount, current_turn)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (duel['challenger_id'], duel['defender_id'], duel['bet_amount'], duel['challenger_id']))

duel_session_id = cur.fetchone()['id']

# Update duel status

cur.execute("UPDATE duels SET status = 'ongoing' WHERE id = %s", (duel_id, ))

conn.commit()

await query.edit_message_text("✅ Duel accepted! Battle starts.")

# Send initial battle message

await send_duel_battle_message(context.bot, query.message.chat_id, duel_session_id)

finally:

cur.close()
conn.close()

async def duel_decline_callback(update: Update,

context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

user_id = query.from_user.id

duel_id = int(query.data.replace("dueldecline_", ""))

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM duels WHERE id = %s", (duel_id, ))
duel = cur.fetchone()

if not duel:

await query.answer("Duel not found!", show_alert=True)
return

if user_id != duel['defender_id']:

await query.answer("Only the challenged player can decline!",

show_alert=True)
return
cur.execute("UPDATE duels SET status = 'declined' WHERE id = %s",

(duel_id, ))
conn.commit()

await query.edit_message_text("❌ Duel declined!")
finally:

cur.close()
conn.close()

async def duel_attack_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

user_id = query.from_user.id
parts = query.data.replace("duel_attack_", "").split("_")
duel_session_id = int(parts[0])
attack_idx = int(parts[1])

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM duel_sessions WHERE id = %s", (duel_session_id, ))
duel_session = cur.fetchone()

if not duel_session:

await query.edit_message_text("⚠️ No active duel!")
return

if user_id != duel_session['current_turn']:

await query.answer("It's not your turn!", show_alert=True)
return

# Determine who is attacking

if user_id == duel_session['challenger_id']:

attacker_id = duel_session['challenger_id']
defender_id = duel_session['defender_id']
attacker_active_slot = duel_session['challenger_active_slot']
defender_active_slot = duel_session['defender_active_slot']
else:

attacker_id = duel_session['defender_id']
defender_id = duel_session['challenger_id']
attacker_active_slot = duel_session['defender_active_slot']
defender_active_slot = duel_session['challenger_active_slot']

cur.execute("SELECT * FROM players WHERE user_id = %s", (attacker_id, ))
attacker_player = cur.fetchone()

cur.execute(

"""
            SELECT pc.* FROM teams t 
            JOIN player_characters pc ON t.character_id = pc.id 
            WHERE t.user_id = %s AND t.team_number = %s AND t.slot = %s
        """, (attacker_id, attacker_player.get('active_team', 1), attacker_active_slot))

attacker_fighter = cur.fetchone()

cur.execute("SELECT * FROM players WHERE user_id = %s", (defender_id, ))
defender_player = cur.fetchone()

cur.execute(

"""
            SELECT pc.* FROM teams t 
            JOIN player_characters pc ON t.character_id = pc.id 
            WHERE t.user_id = %s AND t.team_number = %s AND t.slot = %s
        """, (defender_id, defender_player.get('active_team', 1), defender_active_slot))

defender_fighter = cur.fetchone()

attacks = get_character_attacks(attacker_fighter['name'])
attack_name = attacks[attack_idx]

instant_transmission_dodge = random.random() < 0.15

if instant_transmission_dodge:

enemy_damage = random.randint(

defender_fighter['current_power'] // 5,
defender_fighter['current_power'] // 3)
new_attacker_power = max(

0, attacker_fighter['current_power'] - enemy_damage)

cur.execute(

"UPDATE player_characters SET current_power = %s WHERE id = %s",

(new_attacker_power, attacker_fighter['id']))
conn.commit()

await query.edit_message_text(

f"""
💨 **INSTANT TRANSMISSION!** 💨

{defender_fighter['name']} dodged your {attack_name}!
Opponent countered for {enemy_damage} damage!

🔵 {attacker_fighter['name']} - {new_attacker_power} HP
🔴 {defender_fighter['name']} - {defender_fighter['current_power']} HP
                """,

parse_mode='Markdown')

# Switch turn

next_turn = defender_id
cur.execute("UPDATE duel_sessions SET current_turn = %s WHERE id = %s", (next_turn, duel_session_id))
conn.commit()

await send_duel_battle_message(context.bot, query.message.chat_id, duel_session_id, edit_message_id=query.message.id)

return

your_damage = random.randint(attacker_fighter['current_power'] // 4,

attacker_fighter['current_power'] // 2)

enemy_damage = random.randint(defender_fighter['current_power'] // 6,

defender_fighter['current_power'] // 4)

new_defender_power = max(0,

defender_fighter['current_power'] - your_damage)
new_attacker_power = max(

0, attacker_fighter['current_power'] - enemy_damage)

cur.execute(

"UPDATE player_characters SET current_power = %s WHERE id = %s",

(new_defender_power, defender_fighter['id']))
cur.execute(

"UPDATE player_characters SET current_power = %s WHERE id = %s",

(new_attacker_power, attacker_fighter['id']))
conn.commit()

if new_defender_power <= 0:

# Check if opponent has next fighter

cur.execute(

"""
                    SELECT pc.*, t.slot FROM teams t 
                    JOIN player_characters pc ON t.character_id = pc.id 
                    WHERE t.user_id = %s AND t.team_number = %s AND pc.current_power > 0
                    ORDER BY t.slot LIMIT 1
                """, (defender_id, defender_player.get('active_team', 1)))

next_defender = cur.fetchone()

if next_defender:

if attacker_id == duel_session['challenger_id']:

cur.execute(

"UPDATE duel_sessions SET defender_active_slot = %s WHERE id = %s",

(next_defender['slot'], duel_session_id))
else:

cur.execute(

"UPDATE duel_sessions SET challenger_active_slot = %s WHERE id = %s",

(next_defender['slot'], duel_session_id))
conn.commit()

await query.edit_message_text(

f"""
💥 {defender_fighter['name']} fainted!

{next_defender['name']} enters the battle!

🔵 {attacker_fighter['name']} - {attacker_fighter['current_power']} HP
🔴 {next_defender['name']} - {next_defender['current_power']} HP
                    """,

parse_mode='Markdown')

# Switch turn

next_turn = defender_id
cur.execute("UPDATE duel_sessions SET current_turn = %s WHERE id = %s", (next_turn, duel_session_id))
conn.commit()

await send_duel_battle_message(context.bot, query.message.chat_id, duel_session_id, edit_message_id=query.message.id)

else:

# Winner

winner_id = attacker_id
loser_id = defender_id

prize = duel_session['bet_amount'] * 2
cur.execute("UPDATE players SET coins = coins + %s WHERE user_id = %s", (prize, winner_id))
cur.execute("UPDATE player_characters SET current_power = power WHERE user_id = %s", (winner_id, ))
cur.execute("UPDATE player_characters SET current_power = power WHERE user_id = %s", (loser_id, ))
cur.execute("DELETE FROM duel_sessions WHERE id = %s", (duel_session_id, ))
cur.execute("SELECT * FROM duels WHERE challenger_id = %s AND defender_id = %s", (duel_session['challenger_id'], duel_session['defender_id']))
duel = cur.fetchone()
cur.execute("UPDATE duels SET status = 'completed', winner_id = %s WHERE id = %s", (winner_id, duel['id']))
conn.commit()

await query.edit_message_text(f"""
🏆 **DUEL COMPLETE!** 🏆

{attacker_fighter['name']} used {attack_name}!
{defender_fighter['name']} was defeated!

Winner: {attacker_player['username']} gets {prize} coins!
        """,

parse_mode='Markdown')
elif new_attacker_power <= 0:

# Check if attacker has next

cur.execute(

"""
                    SELECT pc.*, t.slot FROM teams t 
                    JOIN player_characters pc ON t.character_id = pc.id 
                    WHERE t.user_id = %s AND t.team_number = %s AND pc.current_power > 0
                    ORDER BY t.slot LIMIT 1
                """, (attacker_id, attacker_player.get('active_team', 1)))

next_attacker = cur.fetchone()

if next_attacker:

if attacker_id == duel_session['challenger_id']:

cur.execute(

"UPDATE duel_sessions SET challenger_active_slot = %s WHERE id = %s",

(next_attacker['slot'], duel_session_id))
else:

cur.execute(

"UPDATE duel_sessions SET defender_active_slot = %s WHERE id = %s",

(next_attacker['slot'], duel_session_id))
conn.commit()

await query.edit_message_text(

f"""
💥 {attacker_fighter['name']} fainted!

{next_attacker['name']} enters the battle!

🔵 {next_attacker['name']} - {next_attacker['current_power']} HP
🔴 {defender_fighter['name']} - {defender_fighter['current_power']} HP
                    """,

parse_mode='Markdown')

# Switch turn

next_turn = defender_id
cur.execute("UPDATE duel_sessions SET current_turn = %s WHERE id = %s", (next_turn, duel_session_id))
conn.commit()

await send_duel_battle_message(context.bot, query.message.chat_id, duel_session_id, edit_message_id=query.message.id)

else:

# Winner is defender

winner_id = defender_id
loser_id = attacker_id

prize = duel_session['bet_amount'] * 2
cur.execute("UPDATE players SET coins = coins + %s WHERE user_id = %s", (prize, winner_id))
cur.execute("UPDATE player_characters SET current_power = power WHERE user_id = %s", (winner_id, ))
cur.execute("UPDATE player_characters SET current_power = power WHERE user_id = %s", (loser_id, ))
cur.execute("DELETE FROM duel_sessions WHERE id = %s", (duel_session_id, ))
cur.execute("SELECT * FROM duels WHERE challenger_id = %s AND defender_id = %s", (duel_session['challenger_id'], duel_session['defender_id']))
duel = cur.fetchone()
cur.execute("UPDATE duels SET status = 'completed', winner_id = %s WHERE id = %s", (winner_id, duel['id']))
conn.commit()

await query.edit_message_text(f"""
🏆 **DUEL COMPLETE!** 🏆

All opponent's fighters fainted!

Winner: {defender_player['username']} gets {prize} coins!
        """,

parse_mode='Markdown')
else:

await query.edit_message_text(

f"""
⚔️ **DUEL!** ⚔️

You used **{attack_name}** for {your_damage} damage!
Opponent countered for {enemy_damage} damage!

🔵 {attacker_fighter['name']} - {new_attacker_power} HP
🔴 {defender_fighter['name']} - {new_defender_power} HP
                """,

parse_mode='Markdown')

# Switch turn

next_turn = defender_id if user_id == duel_session['challenger_id'] else duel_session['challenger_id']
cur.execute("UPDATE duel_sessions SET current_turn = %s WHERE id = %s", (next_turn, duel_session_id))
conn.commit()

await send_duel_battle_message(context.bot, query.message.chat_id, duel_session_id, edit_message_id=query.message.id)

finally:

cur.close()
conn.close()

async def send_duel_battle_message(bot, chat_id, duel_session_id, edit_message_id=None):

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM duel_sessions WHERE id = %s", (duel_session_id, ))
duel_session = cur.fetchone()

challenger_id = duel_session['challenger_id']
defender_id = duel_session['defender_id']
current_turn = duel_session['current_turn']

cur.execute("SELECT * FROM players WHERE user_id = %s", (challenger_id, ))
challenger_player = cur.fetchone()

cur.execute(

"""
            SELECT pc.* FROM teams t 
            JOIN player_characters pc ON t.character_id = pc.id 
            WHERE t.user_id = %s AND t.team_number = %s AND t.slot = %s
        """, (challenger_id, challenger_player.get('active_team', 1), duel_session['challenger_active_slot']))

challenger_fighter = cur.fetchone()

cur.execute("SELECT * FROM players WHERE user_id = %s", (defender_id, ))
defender_player = cur.fetchone()

cur.execute(

"""
            SELECT pc.* FROM teams t 
            JOIN player_characters pc ON t.character_id = pc.id 
            WHERE t.user_id = %s AND t.team_number = %s AND t.slot = %s
        """, (defender_id, defender_player.get('active_team', 1), duel_session['defender_active_slot']))

defender_fighter = cur.fetchone()

if current_turn == challenger_id:

attacker_fighter = challenger_fighter
attacks = get_character_attacks(attacker_fighter['name'])

keyboard = [[

InlineKeyboardButton(f"⚔️ {attacks[0]}",

callback_data=f"duel_attack_{duel_session_id}_0")
],

[

InlineKeyboardButton(f"⚔️ {attacks[1]}",

callback_data=f"duel_attack_{duel_session_id}_1")
],
[

InlineKeyboardButton(f"⚔️ {attacks[2]}",

callback_data=f"duel_attack_{duel_session_id}_2")
],
[

InlineKeyboardButton(f"⚔️ {attacks[3]}",

callback_data=f"duel_attack_{duel_session_id}_3")
],
[

InlineKeyboardButton("🔄 Swap Character",

callback_data=f"duel_swap_{duel_session_id}")
],
[

InlineKeyboardButton("🏃 Run Away",

callback_data=f"duel_run_{duel_session_id}")
]]

reply_markup = InlineKeyboardMarkup(keyboard)

caption = f"""
⚔️ **DUEL BATTLE!** ⚔️

🔵 {challenger_player['username']}: {challenger_fighter['name']} - {challenger_fighter['current_power']} HP
🔴 {defender_player['username']}: {defender_fighter['name']} - {defender_fighter['current_power']} HP

{challenger_player['username']}'s turn! Choose attack.
"""

else:

attacker_fighter = defender_fighter
attacks = get_character_attacks(attacker_fighter['name'])

keyboard = [[

InlineKeyboardButton(f"⚔️ {attacks[0]}",

callback_data=f"duel_attack_{duel_session_id}_0")
],

[

InlineKeyboardButton(f"⚔️ {attacks[1]}",

callback_data=f"duel_attack_{duel_session_id}_1")
],
[

InlineKeyboardButton(f"⚔️ {attacks[2]}",

callback_data=f"duel_attack_{duel_session_id}_2")
],
[

InlineKeyboardButton(f"⚔️ {attacks[3]}",

callback_data=f"duel_attack_{duel_session_id}_3")
],
[

InlineKeyboardButton("🔄 Swap Character",

callback_data=f"duel_swap_{duel_session_id}")
],
[

InlineKeyboardButton("🏃 Run Away",

callback_data=f"duel_run_{duel_session_id}")
]]

reply_markup = InlineKeyboardMarkup(keyboard)

caption = f"""
⚔️ **DUEL BATTLE!** ⚔️

🔵 {challenger_player['username']}: {challenger_fighter['name']} - {challenger_fighter['current_power']} HP
🔴 {defender_player['username']}: {defender_fighter['name']} - {defender_fighter['current_power']} HP

{defender_player['username']}'s turn! Choose attack.
"""

if edit_message_id:

await bot.edit_message_caption(chat_id=chat_id, message_id=edit_message_id, caption=caption, reply_markup=reply_markup, parse_mode='Markdown')
else:

await bot.send_message(chat_id=chat_id, text=caption, reply_markup=reply_markup, parse_mode='Markdown')

finally:

cur.close()
conn.close()

async def duel_swap_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

user_id = query.from_user.id
parts = query.data.replace("duel_swap_", "").split("_")
duel_session_id = int(parts[0]) if parts else None

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM duel_sessions WHERE id = %s", (duel_session_id, ))
duel_session = cur.fetchone()

if not duel_session:

await query.edit_message_text("⚠️ No active duel!")
return

if user_id != duel_session['current_turn']:

await query.answer("It's not your turn!", show_alert=True)
return

# Similar to fight swap

if user_id == duel_session['challenger_id']:

attacker_id = duel_session['challenger_id']
active_slot = duel_session['challenger_active_slot']
else:

attacker_id = duel_session['defender_id']
active_slot = duel_session['defender_active_slot']

cur.execute("SELECT * FROM players WHERE user_id = %s", (attacker_id, ))
attacker_player = cur.fetchone()

cur.execute(

"""
                SELECT pc.*, t.slot FROM teams t 
                JOIN player_characters pc ON t.character_id = pc.id 
                WHERE t.user_id = %s AND t.team_number = %s AND t.slot != %s AND pc.current_power > 0
            """, (attacker_id, attacker_player.get('active_team', 1), active_slot))

available = cur.fetchall()

if not available:

await query.answer("No other characters available!",

show_alert=True)
return

if duel_session.get('last_action_time'):

elapsed = (datetime.now() -

duel_session['last_action_time']).total_seconds()

if elapsed < 5:

await query.answer(

f"Swap cooldown! Wait {int(5 - elapsed)}s",

show_alert=True)
return

keyboard = []
for char in available:

keyboard.append([

InlineKeyboardButton(

f"{char['name']} ({char['current_power']} HP)",

callback_data=f"duel_swapto_{duel_session_id}_{char['slot']}"

)
])
keyboard.append(

[InlineKeyboardButton("🔙 Back", callback_data=f"duel_back_{duel_session_id}")])

await query.edit_message_text(

"🔄 Select a character to swap:",

reply_markup=InlineKeyboardMarkup(keyboard))
finally:

cur.close()
conn.close()

async def duel_swapto_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

user_id = query.from_user.id
parts = query.data.replace("duel_swapto_", "").split("_")
duel_session_id = int(parts[0])
slot = int(parts[1])

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("UPDATE duel_sessions SET last_action_time = NOW() WHERE id = %s", (duel_session_id, ))
if user_id == duel_session['challenger_id']:

cur.execute(

"UPDATE duel_sessions SET challenger_active_slot = %s WHERE id = %s",

(slot, duel_session_id))
else:

cur.execute(

"UPDATE duel_sessions SET defender_active_slot = %s WHERE id = %s",

(slot, duel_session_id))
conn.commit()

await query.edit_message_text(

f"""
🔄 **SWAPPED!**

New fighter enters battle!
        """,

parse_mode='Markdown')

await send_duel_battle_message(context.bot, query.message.chat_id, duel_session_id, edit_message_id=query.message.id)

finally:

cur.close()
conn.close()

async def duel_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

duel_session_id = int(query.data.replace("duel_back_", ""))

await send_duel_battle_message(context.bot, query.message.chat_id, duel_session_id, edit_message_id=query.message.id)

async def duel_run_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query
await query.answer()

user_id = query.from_user.id
duel_session_id = int(query.data.replace("duel_run_", ""))

conn = get_db_connection()
cur = conn.cursor()

try:

cur.execute("SELECT * FROM duel_sessions WHERE id = %s", (duel_session_id, ))
duel_session = cur.fetchone()

if not duel_session:

await query.edit_message_text("⚠️ No active duel!")
return

if user_id != duel_session['current_turn']:

await query.answer("It's not your turn!", show_alert=True
return

# --- DUEL RESOLUTION LOGIC (Yeh kisi existing function ke andar aayega) ---
    # The runner loses, opponent wins
    if user_id == duel_session['challenger_id']:
        winner_id = duel_session['defender_id']
        loser_id = duel_session['challenger_id']
    else:
        winner_id = duel_session['challenger_id']
        loser_id = duel_session['defender_id']

    prize = duel_session['bet_amount'] * 2
    
    cur.execute("UPDATE players SET coins = coins + %s WHERE user_id = %s", (prize, winner_id))
    cur.execute("UPDATE player_characters SET current_power = power WHERE user_id = %s", (winner_id, ))
    cur.execute("UPDATE player_characters SET current_power = power WHERE user_id = %s", (loser_id, ))
    cur.execute("DELETE FROM duel_sessions WHERE id = %s", (duel_session_id, ))
    cur.execute(
        "UPDATE duels SET status = 'completed', winner_id = %s WHERE challenger_id = %s AND defender_id = %s", 
        (winner_id, duel_session['challenger_id'], duel_session['defender_id'])
    )
    conn.commit()

    await query.edit_message_text(
        f"""
🏃 **RUN AWAY!** 🏃

You ran from the duel!
Opponent wins the prize of {prize} coins!
        """,
        parse_mode='Markdown'
    )
# finally block tabhi aayega agar upar try block ho, context ke hisaab se yahan rakha hai
finally:
    cur.close()
    conn.close()

# --- COMMAND FUNCTIONS START HERE ---

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
        player = cur.fetchone()

        if not player:
            await update.message.reply_text("⚠️ You need to /register first!")
            return

        cur.execute(
            "SELECT COUNT(*) as count, COALESCE(SUM(power), 0) as total FROM player_characters WHERE user_id = %s",
            (user_id, )
        )
        chars = cur.fetchone()

        tournament_status = "🏆 In Tournament!" if player.get('in_tournament') else "Not in tournament"

        await update.message.reply_text(
            f"""
📊 **WARRIOR STATS** 📊

👤 **{player.get('username', 'Unknown')}**

- Level: {player.get('level', 1)}
✨ XP: {player.get('xp', 0)}/50
💰 Coins: {player.get('coins', 0)}
👥 Characters: {chars['count']}
⚡ Total Power: {chars['total']}
🎯 Active Team: {player.get('active_team', 1)}

**Mafuba Inventory:**
🏺 Base: {player.get('mafuba_base', 0)}
⚡ Power: {player.get('mafuba_power', 0)}
🔥 Pro: {player.get('mafuba_pro', 0)}
💎 Ultra Pro: {player.get('mafuba_ultra_pro', 0)}

{tournament_status}
            """,
            parse_mode='Markdown'
        )
    finally:
        cur.close()
        conn.close()


DAILY_COINS_REWARD = 50
DAILY_MAFUBA_REWARD = 2
BIO_REQUIREMENT = "@Dragonball_gamingbot"

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
        player = cur.fetchone()

        if not player:
            await update.message.reply_text("⚠️ You need to /register first!")
            return

        try:
            user_full = await context.bot.get_chat(user_id)
            user_bio = user_full.bio or ""
        except Exception as e:
            logging.error(f"Error getting user bio: {e}")
            user_bio = ""

        if BIO_REQUIREMENT.lower() not in user_bio.lower():
            await update.message.reply_text(
                f"""
❌ **DAILY REWARD LOCKED** ❌

To claim your daily rewards, you must add this text to your Telegram bio:

📝 **{BIO_REQUIREMENT}**

**How to add:**
1. Go to Settings
2. Tap on your profile
3. Tap "Bio"
4. Add "{BIO_REQUIREMENT}" to your bio
5. Save and try /daily again!

🎁 Daily rewards: {DAILY_COINS_REWARD} coins + {DAILY_MAFUBA_REWARD} Mafuba Base
                """, 
                parse_mode='Markdown'
            )
            return

        cur.execute("SELECT * FROM daily_claims WHERE user_id = %s", (user_id, ))
        claim = cur.fetchone()
        now = datetime.now()

        if claim:
            last_claim = claim['last_claim']
            next_claim = last_claim + timedelta(days=1)

            if now < next_claim:
                time_left = next_claim - now
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)

                await update.message.reply_text(
                    f"""
⏳ **DAILY REWARD COOLDOWN** ⏳

You've already claimed your daily reward!

⏰ Next claim available in: **{hours}h {minutes}m {seconds}s**

Come back later! 🐉
                    """, 
                    parse_mode='Markdown'
                )
                return

            cur.execute("UPDATE daily_claims SET last_claim = %s WHERE user_id = %s", (now, user_id))
        else:
            cur.execute("INSERT INTO daily_claims (user_id, last_claim) VALUES (%s, %s)", (user_id, now))

        cur.execute(
            "UPDATE players SET coins = coins + %s, mafuba_base = mafuba_base + %s WHERE user_id = %s",
            (DAILY_COINS_REWARD, DAILY_MAFUBA_REWARD, user_id)
        )
        conn.commit()

        cur.execute("SELECT * FROM players WHERE user_id = %s", (user_id, ))
        updated_player = cur.fetchone()

        await update.message.reply_text(
            f"""
🎉 **DAILY REWARD CLAIMED!** 🎉

✅ You received:
💰 +{DAILY_COINS_REWARD} Coins
🏺 +{DAILY_MAFUBA_REWARD} Mafuba Base

📊 **Updated Balance:**
💰 Coins: {updated_player.get('coins', 0)}
🏺 Mafuba Base: {updated_player.get('mafuba_base', 0)}

Come back in 24 hours for more rewards! 🐉
            """, 
            parse_mode='Markdown'
        )

    except Exception as e:
        logging.error(f"Daily reward error: {e}")
        conn.rollback()
        await update.message.reply_text("An error occurred. Please try again.")
    finally:
        cur.close()
        conn.close()


async def admin_add_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    if not can_use_admin_commands(user_id, chat_id, chat_type):
        await update.message.reply_text("⚠️ You don't have permission to use this command!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message with /add <amount>")
        return

    try:
        amount = int(context.args[0])
    except:
        await update.message.reply_text("Usage: /add <amount>")
        return

    target_id = update.message.reply_to_message.from_user.id
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE players SET coins = coins + %s WHERE user_id = %s", (amount, target_id))
        conn.commit()
        await update.message.reply_text(f"✅ Added {amount} coins to user!")
    finally:
        cur.close()
        conn.close()


async def admin_remove_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    if not can_use_admin_commands(user_id, chat_id, chat_type):
        await update.message.reply_text("⚠️ You don't have permission to use this command!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message with /remove <amount>")
        return

    try:
        amount = int(context.args[0])
    except:
        await update.message.reply_text("Usage: /remove <amount>")
        return

    target_id = update.message.reply_to_message.from_user.id
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE players SET coins = coins - %s WHERE user_id = %s", (amount, target_id))
        conn.commit()
        await update.message.reply_text(f"✅ Removed {amount} coins from user!")
    finally:
        cur.close()
        conn.close()


async def admin_give_mafuba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    if not can_use_admin_commands(user_id, chat_id, chat_type):
        await update.message.reply_text("⚠️ You don't have permission to use this command!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message with /givemafuba <type> <amount>")
        return

    try:
        mafuba_type = context.args[0].lower()
        amount = int(context.args[1])
        if mafuba_type not in ['base', 'power', 'pro', 'ultra_pro']:
            raise ValueError("Invalid mafuba type")
    except:
        await update.message.reply_text("Usage: /givemafuba <base/power/pro/ultra_pro> <amount>")
        return

    target_id = update.message.reply_to_message.from_user.id
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            f"UPDATE players SET mafuba_{mafuba_type} = mafuba_{mafuba_type} + %s WHERE user_id = %s",
            (amount, target_id)
        )
        conn.commit()
        await update.message.reply_text(f"✅ Gave {amount} Mafuba {mafuba_type} to user!")
    finally:
        cur.close()
        conn.close()


async def admin_set_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    if not can_use_admin_commands(user_id, chat_id, chat_type):
        await update.message.reply_text("⚠️ You don't have permission to use this command!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message with /setlevel <level>")
        return

    try:
        level = int(context.args[0])
    except:
        await update.message.reply_text("Usage: /setlevel <level>")
        return

    target_id = update.message.reply_to_message.from_user.id
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE players SET level = %s WHERE user_id = %s", (level, target_id))
        conn.commit()
        await update.message.reply_text(f"✅ Set user level to {level}!")
    finally:
        cur.close()
        conn.close()


async def admin_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_owner(user_id):
        await update.message.reply_text("⚠️ Only the owner can add admins!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message with /addadmin")
        return

    target_id = update.message.reply_to_message.from_user.id
    target_name = update.message.reply_to_message.from_user.first_name or "User"

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO admins (user_id, is_owner) VALUES (%s, FALSE) ON CONFLICT (user_id) DO NOTHING",
            (target_id, )
        )
        conn.commit()
        await update.message.reply_text(f"✅ {target_name} has been added as admin!")
    finally:
        cur.close()
        conn.close()


async def admin_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_owner(user_id):
        await update.message.reply_text("⚠️ Only the owner can remove admins!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message with /removeadmin")
        return

    target_id = update.message.reply_to_message.from_user.id
    target_name = update.message.reply_to_message.from_user.first_name or "User"

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM admins WHERE user_id = %s", (target_id, ))
        conn.commit()
        await update.message.reply_text(f"✅ {target_name} has been removed from admins!")
        finally:
        cur.close()
        conn.close()

# --- FLASK KEEP-ALIVE SERVER (FOR UPTIMEROBOT) ---
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Dragon Ball Arena Bot is Alive!"

def run():
    # Render dynamic port assign karta hai
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()


# --- BOT INITIALIZATION ---
def main():
    # 1. Database initialize karein
    init_db()

    # 2. 24/7 web server start karein
    keep_alive()
    
    # 3. Telegram Bot engine banayein
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # --- COMMANDS LINKING (Handlers) ---
    # Ye handlers Telegram commands ko aapke define kiye functions se jodte hain
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("open", open_menu))
    application.add_handler(CommandHandler("close", close_menu))
    application.add_handler(CommandHandler("catch", catch_command))
    application.add_handler(CommandHandler("shop", shop))
    application.add_handler(CommandHandler("team", team))
    application.add_handler(CommandHandler("fight", fight))
    application.add_handler(CommandHandler("tournament", tournament))
    application.add_handler(CommandHandler("duel", duel))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("daily", daily))
    
    # Admin commands linking
    application.add_handler(CommandHandler("add", admin_add_coins))
    application.add_handler(CommandHandler("remove", admin_remove_coins))
    application.add_handler(CommandHandler("givemafuba", admin_give_mafuba))
    application.add_handler(CommandHandler("setlevel", admin_set_level))
    application.add_handler(CommandHandler("addadmin", admin_add_admin))
    application.add_handler(CommandHandler("removeadmin", admin_remove_admin))

    # --- BUTTON CLICKS LINKING (Callback Handlers) ---
    application.add_handler(CallbackQueryHandler(starter_callback, pattern="^starter_"))
    application.add_handler(CallbackQueryHandler(mafuba_callback, pattern="^mafuba_"))
    application.add_handler(CallbackQueryHandler(buy_callback, pattern="^buy_|^close_shop$"))
    application.add_handler(CallbackQueryHandler(team_callback, pattern="^viewteam_"))
    application.add_handler(CallbackQueryHandler(buildteam_callback, pattern="^buildteam_"))
    application.add_handler(CallbackQueryHandler(selectchar_callback, pattern="^selectchar_"))
    application.add_handler(CallbackQueryHandler(buildteam_done_callback, pattern="^buildteam_done$"))
    application.add_handler(CallbackQueryHandler(setactive_callback, pattern="^setactive_"))
    application.add_handler(CallbackQueryHandler(back_teams_callback, pattern="^back_teams$"))
    application.add_handler(CallbackQueryHandler(fight_callback, pattern="^fight_"))
    application.add_handler(CallbackQueryHandler(swap_callback, pattern="^swap_"))
    application.add_handler(CallbackQueryHandler(tournament_callback, pattern="^enter_tournament$"))
    application.add_handler(CallbackQueryHandler(duel_bet_callback, pattern="^duelbet_"))
    application.add_handler(CallbackQueryHandler(duel_cancel_callback, pattern="^duelcancel_"))
    application.add_handler(CallbackQueryHandler(duel_accept_callback, pattern="^duelaccept_"))
    application.add_handler(CallbackQueryHandler(duel_decline_callback, pattern="^dueldecline_"))
    application.add_handler(CallbackQueryHandler(duel_attack_callback, pattern="^duel_attack_"))
    application.add_handler(CallbackQueryHandler(duel_swap_callback, pattern="^duel_swap_"))
    application.add_handler(CallbackQueryHandler(duel_swapto_callback, pattern="^duel_swapto_"))
    application.add_handler(CallbackQueryHandler(duel_back_callback, pattern="^duel_back_"))
    application.add_handler(CallbackQueryHandler(duel_run_callback, pattern="^duel_run_"))

    # Reply keyboard texts linking
    application.add_handler(MessageHandler(filters.Regex("^/fight$"), fight))
    application.add_handler(MessageHandler(filters.Regex("^/close$"), close_menu))

    # Bot ko chalu karein
    print("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

