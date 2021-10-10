import discord, subprocess, os, json

class Client(discord.Client):
    def __init__(self, *, loop=None, **options):
        super().__init__(loop=loop, **options)
        # get directory of main.py
        self.REAL_PATH = os.path.realpath(__file__)
        self.DIR_PATH = os.path.dirname(self.REAL_PATH)
        self.is_server_running = False

    # method on loged in
    async def on_ready(self):
        # fetch settings data
        if not os.path.exists(f"{self.DIR_PATH}/settings.json"):
            json_init = {}
            with open(f"{self.DIR_PATH}/settings.json", 'w') as f:
                f.write(json.dumps(json_init))
        with open(f"{self.DIR_PATH}/settings.json", 'r') as f:
            settings = json.loads(f.read())
        
        # set settings variables
        # prefix
        try:
            self.prefix = settings["prefix"]
        except KeyError:
            self.prefix = "|"
            self.update_settings("prefix", self.prefix)
        # server start file
        try:
            self.server_start_file = settings["server_file"]
        except KeyError:
            self.server_start_file = "None"
            self.update_settings("server_file", self.server_start_file)        

        print("Bot logged in")
    
    # method message received
    async def on_message(self, message):
        # Start server start script from server_file
        if message.content == f"{self.prefix}StartServer":
            # checks if server_start_file is set
            if self.server_start_file == "None":
                await message.channel.send(f"[BOT] [INFO]: you need to first set server start file path with: |setServerFile:<server_file_path>")
            elif self.is_server_running == True:
                await message.channel.send(f"[BOT] [INFO]: Server is running!")
            else:
                try:
                    await message.channel.send(f"[BOT] [COMMAND]: starting Server...")
                    subprocess.call(["sh", self.server_start_file])
                    self.is_server_running = True
                except FileNotFoundError as e:
                    await message.channel.send(f"[BOT] [ERROR]: raised {e}")
        # Stop Server currently running
        if message.content == f"{self.prefix}StopServer":
            if self.is_server_running == False:
                await message.channel.send(f"[BOT] [INFO]: no Server running!")
            else:
                await message.channel.send(f"[BOT] [INFO]: stopping Server...")
                subprocess.call("stop")

        # set server file path
        if message.content.startswith("|setServerFile:"):
            self.server_start_file = message.content.split(":")[1]
            self.update_settings("server_file", self.server_start_file)
            await message.channel.send(f"[BOT] [COMMAND]: changed start file to: '{self.server_start_file}'")
    
    # save a setting value to name in settings.settings
    def update_settings(self, settings_name, setting_value):
        # read settings data
        with open(f"{self.DIR_PATH}/settings.json", 'r') as f:
            settings = json.loads(f.read())
        settings[settings_name] = setting_value
        # write new settings data
        with open(f"{self.DIR_PATH}/settings.json", 'w') as f:
            f.write(json.dumps(settings))

                


if __name__ == '__main__':
    # directory path
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))

    # saves token in token variable
    with open(f"{DIR_PATH}/token.txt", 'r') as f:
        token = f.read()

    # create instance of Client and runs it
    BotClient = Client()
    BotClient.run(token)