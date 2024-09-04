import telebot
import pymongo
from pymongo import MongoClient

# Replace 'YOUR_BOT_TOKEN' with your bot's API token
API_TOKEN = 'YOUR_BOT_TOKEN'
bot = telebot.TeleBot(API_TOKEN)

# List of MongoDB URLs (add more URLs as needed)
mongodb_urls = [
    'YOUR_MONGODB_CONNECTION_STRING_1',
    'YOUR_MONGODB_CONNECTION_STRING_2'
]

# Dictionary to store filters, key = keyword, value = response and db index
filters = {}

# Initialize MongoDB clients
mongo_clients = [MongoClient(url) for url in mongodb_urls]
databases = [client['your_database_name'] for client in mongo_clients]
filters_collections = [db['filters'] for db in databases]

# Load filters from all MongoDB databases
def load_filters():
    filters.clear()  # Clear any existing filters in memory
    for db_index, collection in enumerate(filters_collections):
        for document in collection.find():
            filters[document['keyword']] = {
                'response': document['response'],
                'db_index': db_index
            }

# Save filter to the first database in the list
def save_filter(keyword, response):
    if keyword in filters:
        db_index = filters[keyword]['db_index']
    else:
        db_index = 0  # Default to first database if new keyword
    filters_collections[db_index].update_one(
        {'keyword': keyword},
        {'$set': {'response': response}},
        upsert=True
    )
    filters[keyword] = {'response': response, 'db_index': db_index}

# Remove filter from the corresponding database
def remove_filter(keyword):
    if keyword in filters:
        db_index = filters[keyword]['db_index']
        filters_collections[db_index].delete_one({'keyword': keyword})
        del filters[keyword]

# Initialize filters
load_filters()

# Command to add a filter
@bot.message_handler(commands=['addfilter'])
def add_filter(message):
    try:
        command, keyword, *response = message.text.split(maxsplit=2)
        if len(response) == 0:
            bot.reply_to(message, "Please provide a response for the filter.")
            return

        save_filter(keyword, response[0])
        bot.reply_to(message, f"Filter for '{keyword}' added successfully!")
    except Exception as e:
        bot.reply_to(message, "Error adding filter.")
        print(e)

# Command to remove a filter
@bot.message_handler(commands=['removefilter'])
def remove_filter_command(message):
    try:
        command, keyword = message.text.split(maxsplit=1)
        if keyword in filters:
            remove_filter(keyword)
            bot.reply_to(message, f"Filter for '{keyword}' removed successfully!")
        else:
            bot.reply_to(message, f"No filter found for '{keyword}'.")
    except Exception as e:
        bot.reply_to(message, "Error removing filter.")
        print(e)

# Respond to filters
@bot.message_handler(func=lambda message: True)
def filter_response(message):
    for keyword, data in filters.items():
        if keyword.lower() in message.text.lower():
            bot.reply_to(message, data['response'], parse_mode='Markdown')
            break

# Command to check MongoDB storage for all databases
@bot.message_handler(commands=['checkstorage'])
def check_storage(message):
    try:
        storage_report = []
        for index, client in enumerate(mongo_clients):
            db_stats = client.admin.command("dbstats")
            storage_size = db_stats['storageSize'] / (1024 * 1024)  # Convert bytes to MB
            storage_report.append(f"Database {index + 1}: {storage_size:.2f} MB")
        bot.reply_to(message, "\n".join(storage_report))
    except Exception as e:
        bot.reply_to(message, "Error checking storage.")
        print(e)

# Start the bot
bot.polling()
