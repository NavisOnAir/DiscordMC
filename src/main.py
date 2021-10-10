import discord, subprocess, os, json

class Client(discord.Client):
    # method on loged in
    async def on_ready(self):
        # fetch settings data
        if not os.path.exists("settings.json"):
            json_init = {}
            with open("settings.json", 'w') as f:
                f.write(json.dumps(json_init))
        with open("settings.json", 'r') as f:
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
            else:
                try:
                    await message.channel.send(f"[BOT] [COMMAND]: starting Server...")
                    subprocess.call(["sh", self.server_start_file])
                except FileNotFoundError as e:
                    await message.channel.send(f"[BOT] [ERROR]: raised {e}")
        
        # set server file path
        if message.content.startswith("|setServerFile:"):
            self.server_start_file == message.content.split(":")[1]
            self.update_settings("server_file", self.server_start_file)
            message.channel.send(f"[BOT] [COMMAND]: changed start file to: '{self.server_start_file}'")
    
    # save a setting value to name in settings.settings
    def update_settings(self, settings_name, setting_value):
        # read settings data
        with open("settings.json", 'r') as f:
            settings = json.loads(f.read())
        settings[settings_name] = setting_value
        # write new settings data
        with open("settings.json", 'w') as f:
            f.write(json.dumps(settings))

                


if __name__ == '__main__':
    # saves token in token variable
    with open("token.txt", 'r') as f:
        token = f.read()

    # create instance of Client and runs it
    BotClient = Client()
    BotClient.run(token)