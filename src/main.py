import discord, subprocess, os

class Client(discord.Client):
    # method on loged in
    async def on_ready(self):
        # fetch settings data
        if not os.path.exists("settings.settings"):
            with open("settings.settings", 'w') as f:
                pass
        with open("settings.settings", 'r') as f:
            settings = f.read().split('\n')
        
        # set settings variables
        if settings[0].startswith('prefix'):
            self.prefix = settings[0].split(':')[1]
        else:
            self.prefix = "|"
            with open("settings.settings", 'a') as f:
                f.write(f"{self.prefix}\n")

        print("Bot logged in")
    
    # method message received
    async def on_message(self, message):
        if message.content == f"{self.prefix}StartServer":
            try:
                await message.channel.send(f"[BOT] [COMMAND]: starting Server...")
                subprocess.call(["sh","/home/minecraft_forge_server/ServerStart.sh"])
            except FileNotFoundError as e:
                await message.channel.send(f"[BOT] [ERROR]: raised {e}")
                


if __name__ == '__main__':
    # saves token in token variable
    with open("token.txt", 'r') as f:
        token = f.read()

    # create instance of Client and runs it
    BotClient = Client()
    BotClient.run(token)