# Claymore Telegram Bot


## 1 . Purpose

- Monitor Claymore mining software by monitoring port 3333
- Notify to your account or your channel on Telegram if something down
- Try to reset your machine by using Blynk and Arduino automatically (if have)
- Check/Reset/Turn off your machines by command line on Telegram


## 2. How to use?

### 2.1. Requirements

- A machine (laptop, PC, VPS) can reach your machines's monitoring port (default 3333)
- python2.7, pip, git
- Download this repo: `git clone https://github.com/ducnc/telegram-claymores.git`
- python libs in `requirements.txt`. Install by this command `pip install -r requirements.txt`

### 2.2. Configuration

You need to replace in `config. json` file some parameters as my sample. That's:

- bot_token: your bot ID in telegram
How to create your bot and get bot's token: https://core.telegram.org/bots#creating-a-new-bot

- telegram_channel_id: your account ID or channel ID that you want to send notify
```
To get your ID: chat with bot @userinfobot
To get your private channel ID: 
- Open your telegram channel at https://web.telegram.org to get URL
- Select numbers between "s" and "_" in the URL. Ex s1336534973_ => 1336534973
- Add -100 to the beginning of this string to get channel ID: -1001336534973
```

- blynk_token: your blink token to control Arduino. If you don't use this function, please do `"auto_restart": 0`

- miners: config all your miners as my sample

### 2.3. Start the Bot

```sh
cd telegram-claymores
python telegram_bot.py
```

### 2.4. Command to chat with bot

```
    /list: list all machines
    /check: check your mining machines status 
    /disable [MINUTE]: disable monitor for MINUTE
    /reset [NAME]: reset NAME
    /off [NAME]: Turn off NAME
    /help: display help
```

### 3. Bonus some pictures

- /help
<img src="https://image.prntscr.com/image/HmHLL5ZzR_WmL6oHXGVCJg.png">

- /check
<img src="https://image.prntscr.com/image/x47ioeHTTw2pozjTrrkQKg.png">

- Auto check interval and auto reset 
<img src="https://image.prntscr.com/image/Gu0-MfLKQtOfwgW2M7Kprg.png">

- manual reset
<img src="https://image.prntscr.com/image/qmO-hOgIR3WdcC5uNjKzLQ.png">