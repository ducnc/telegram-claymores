#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# Simple Bot to monitor machines using Claymores
# define your machines using config.json


from telegram.ext import Updater, CommandHandler
from threading import Thread
from blynkapi import Blynk
import requests
import json
import re
import time
import logging


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def read_config(conf_file):
    with open(conf_file, "r") as f:
        return json.loads(f.read())


conf = read_config("config.json")
TOKEN = conf["bot_token"]
CHANNEL = conf["telegram_channel_id"]
monitor_interval = conf["monitor_interval"]
miner_timeout = conf["miner_timeout"]
tolerance = conf["tolerance"]
temperature = conf["temperature"]
AUTO_RESTART = conf["auto_restart"]
AUTO_RESTART_AFTER = conf["restart_after"]
BLYNK_TOKEN = conf["blynk_token"]
blynk_server = "blynk-cloud.com"
blynk_protocol = "http"
blynk_port = "80"
LOCK = 0


def help(bot, update):
    msg_reply = """
    Using this Commands:
    /list: list all machines
    /check: check your mining machines status 
    /disable [MINUTE]: disable monitor for MINUTE
    /reset [NAME]: reset NAME
    /off [NAME]: Turn off NAME
    /help: display this help
    """
    update.message.reply_text(msg_reply)


def get_id(bot, update):
    test = '{}, {}'.format(update.message.chat_id, update.message.message_id)
    update.message.reply_text(test)


def list_machine(bot, update):
    machines = []
    for i in range(len(conf["miners"])):
        NAME = conf["miners"][i]["name"]
        machines.append(NAME)
    list_message = "Your Machines:\n---- {}".format('\n---- '.join(map(str, machines)))
    update.message.reply_text(list_message)


def error(bot, update, error):
    print error


def check(bot, update):
    online = []
    offline = []
    hash_rate = []
    low_hash = []
    for i in range(len(conf["miners"])):
        MAINTAIN = conf["miners"][i]["maintain"]
        HOST = conf["miners"][i]["host"]
        NAME = conf["miners"][i]["name"]
        PORT = conf["miners"][i]["port"]
        TARGET_ETH = conf["miners"][i]["target_eth"]
        if not MAINTAIN:
            url = "http://{}:{}".format(HOST, PORT)
            try:
                res = requests.get(url, verify=False, timeout=miner_timeout)
                if res.status_code == 200:
                    result_json = re.findall("\{\"result.*\]\}", res.text)                      # Parse response
                    result_dict = eval(result_json[0])                                          # Conver to dict
                    online_min = result_dict["result"][1]
                    eth_rate = float(int(result_dict["result"][2].split(";")[0])/1000)

                    if float((TARGET_ETH-eth_rate)*100/TARGET_ETH) > int(tolerance):
                        low_hash.append("{}: {} MHz".format(NAME, eth_rate))
                    hash_rate.append("{}: {} MHz".format(NAME, eth_rate))
                    online.append("{}: {} mins".format(NAME, online_min))
                else:
                    offline.append(NAME)
            except Exception as e:
                offline.append(NAME)
                print e

    msg_reply = "Online:\n---- {}\n\nOffline:\n---- {}\n\nHash Rate:\n---- {}\n\nLow Hash:\n---- {}" \
        .format("\n---- ".join(map(str, online)),
                '\n---- '.join(map(str, offline)),
                '\n---- '.join(map(str, hash_rate)),
                '\n---- '.join(map(str, low_hash)))
    update.message.reply_text(msg_reply)


def monitor(bot, job):
    offline = []
    blynk_pin = []
    global LOCK
    for i in range(len(conf["miners"])):
        MAINTAIN = conf["miners"][i]["maintain"]
        HOST = conf["miners"][i]["host"]
        NAME = conf["miners"][i]["name"]
        PORT = conf["miners"][i]["port"]
        PIN = conf["miners"][i]["blynk_pin"]
        if not MAINTAIN:
            url = "http://{}:{}".format(HOST, PORT)
            try:
                res = requests.get(url, verify=False, timeout=miner_timeout)
                if res.status_code != 200:
                    offline.append(NAME)
                    blynk_pin.append(PIN)
                else:
                    pass
            except Exception as e:
                offline.append(NAME)
                blynk_pin.append(PIN)
                print e

    off_message = "May dang Offline:\n---- {}".format('\n---- '.join(map(str, offline)))
    if len(offline) != 0:
        bot.send_message(CHANNEL, off_message)
        if AUTO_RESTART:
            thread = Thread(target=auto_reboot_machine, args=(bot, blynk_pin))
            thread.start()
    else:
        LOCK = 0


def auto_reboot_machine(bot, blynk_pin):
    global LOCK
    if LOCK:
        pass
    else:
        # bot.send_message(CHANNEL, "I will try to reset your mining machine after {} sec".format(AUTO_RESTART_AFTER))
        t = 0
        LOCK = 1
        while True:
            if t == int(AUTO_RESTART_AFTER) and LOCK:
                bot.send_message(CHANNEL, "Your machine still offline after {} sec, I will do automatic restart!"
                                 .format(AUTO_RESTART_AFTER))
                for pin in blynk_pin:
                    turn_off(pin)
                    turn_on(pin)
                LOCK = 0
                break
            elif t <= int(AUTO_RESTART_AFTER) and not LOCK:
                bot.send_message(CHANNEL, "You've reset manually OR your machine just UP. Cancelling auto reset")
                break
            else:
                time.sleep(1)
                t += 1


def disable(bot, update, job_queue, args):
    user_input = args[0]
    try:
        first_word = int(user_input)
    except Exception as e:
        update.message.reply_text("Wrong Input!")

    update.message.reply_text("OK! I will disable monitor for {} minutes".format(first_word))
    for job_mins in job_queue.jobs():
        job_mins.enabled = False
    time.sleep(first_word*60)
    update.message.reply_text("After {} minutes i will start monitor again".format(first_word))
    for job_mins in job_queue.jobs():
        job_mins.enabled = True


def enable(bot, update, job_queue):
    update.message.reply_text("I will start monitor again")
    for job_mins in job_queue.jobs():
        job_mins.enabled = True


def reset(bot, update, args):
    for i in range(len(conf["miners"])):
        MAINTAIN = conf["miners"][i]["maintain"]
        NAME = conf["miners"][i]["name"]
        PIN = conf["miners"][i]["blynk_pin"]
        global LOCK
        for miner in args:
            if miner == NAME and not MAINTAIN:
                update.message.reply_text("Reseting {}".format(miner))
                turn_off(PIN)
                turn_on(PIN)
                LOCK = 0
            elif miner == NAME and MAINTAIN:
                update.message.reply_text("Machine {} in Maintain Mode".format(miner))


def off(bot, update, args):
    for i in range(len(conf["miners"])):
        MAINTAIN = conf["miners"][i]["maintain"]
        NAME = conf["miners"][i]["name"]
        PIN = conf["miners"][i]["blynk_pin"]
        for miner in args:
            if miner == NAME and not MAINTAIN:
                update.message.reply_text("Turning Off {}".format(miner))
                turn_off(PIN)
            elif miner == NAME and MAINTAIN:
                update.message.reply_text("Machine {} in Maintain Mode".format(miner))


def turn_off(pin):
    machine = Blynk(token=BLYNK_TOKEN, server=blynk_server, protocol=blynk_protocol, port=blynk_port, pin=pin)
    machine.off()
    time.sleep(10)
    machine.on()
    time.sleep(3)


def turn_on(pin):
    machine = Blynk(token=BLYNK_TOKEN, server=blynk_server, protocol=blynk_protocol, port=blynk_port, pin=pin)
    machine.off()
    time.sleep(1)
    machine.on()


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    #
    job_queue = updater.job_queue
    job_queue.run_repeating(monitor, interval=monitor_interval, first=0)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("id", get_id))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("check", check))
    dp.add_handler(CommandHandler("disable", disable, pass_job_queue=True, pass_args=True))
    # dp.add_handler(CommandHandler("enable", enable, pass_job_queue=True, pass_args=True))
    dp.add_handler(CommandHandler("reset", reset, pass_args=True))
    dp.add_handler(CommandHandler("off", off, pass_args=True))
    dp.add_handler(CommandHandler("list", list_machine))

    # on non command i.e message - echo the message on Telegram log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
