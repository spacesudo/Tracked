import telebot
import requests
import time
from collections import defaultdict

# Telegram Bot Token
BOT_TOKEN = "6859486178:AAGxUKf8WPR2o9HlbrRHVBYcwHB1BEmtrbg"
bot = telebot.TeleBot(BOT_TOKEN)

# Ethereum API Key (e.g., Etherscan API)
ETH_API_KEY = "1FABWFGJX3214QQVDTSTQ1UKB43KUWPE63"
ETH_API_URL = "https://api.etherscan.io/api"

# User data: mapping of user_id to a list of tracked wallets
tracked_wallets = defaultdict(list)

# Function to get transactions for an Ethereum address
def get_transactions(address):
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": ETH_API_KEY,
    }
    response = requests.get(ETH_API_URL, params=params)
    data = response.json()
    if data["status"] == "1":
        return data["result"]  # List of transactions
    return []

# Bot commands
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Welcome to PolySync Bot\n! Use /track to track a wallet \n/untrack to remove a wallet\n/list to see tracked wallets.")

@bot.message_handler(commands=["track"])
def track(message):
    try:
        wallet = message.text.split()[1]
        if wallet.startswith("0x") and len(wallet) == 42:
            tracked_wallets[message.chat.id].append(wallet)
            bot.reply_to(message, f"Wallet {wallet} is now being tracked!")
        else:
            bot.reply_to(message, "Invalid Ethereum wallet address.")
    except IndexError:
        bot.reply_to(message, "Please provide a wallet address. Example: /track 0x123...")

@bot.message_handler(commands=["untrack"])
def untrack(message):
    try:
        wallet = message.text.split()[1]
        if wallet in tracked_wallets[message.chat.id]:
            tracked_wallets[message.chat.id].remove(wallet)
            bot.reply_to(message, f"Wallet {wallet} is no longer being tracked.")
        else:
            bot.reply_to(message, "This wallet is not in your tracked list.")
    except IndexError:
        bot.reply_to(message, "Please provide a wallet address. Example: /untrack 0x123...")

@bot.message_handler(commands=["list"])
def list_wallets(message):
    wallets = tracked_wallets[message.chat.id]
    if wallets:
        bot.reply_to(message, "Your tracked wallets:\n" + "\n".join(wallets))
    else:
        bot.reply_to(message, "You are not tracking any wallets.")

# Background polling function
def poll_transactions():
    last_seen = defaultdict(dict)  # Stores the latest transaction hash for each wallet
    while True:
        for user_id, wallets in tracked_wallets.items():
            for wallet in wallets:
                transactions = get_transactions(wallet)
                if transactions:
                    latest_tx = transactions[0]
                    tx_hash = latest_tx["hash"]
                    if wallet not in last_seen[user_id] or last_seen[user_id][wallet] != tx_hash:
                        last_seen[user_id][wallet] = tx_hash
                        bot.send_message(user_id, f"🚨New transaction for wallet {wallet}:\n\nTx Hash: [Etherscan](https://etherscan.io/tx/{tx_hash})\nValue: {int(round(latest_tx['value']) / 1e18, 2)} ETH")
        time.sleep(10)  # Poll every 30 seconds

# Start the bot and background polling
if __name__ == "__main__":
    import threading

    # Start the polling in a separate thread
    polling_thread = threading.Thread(target=poll_transactions, daemon=True)
    polling_thread.start()

    # Start the bot
    bot.infinity_polling()
