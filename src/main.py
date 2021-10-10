import platform
import socket
import discord, subprocess, os, json, multiprocessing, schedule, shutil, time, threading
from mcrcon import MCRcon

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
        
        # world directory
        try:
            self.world_dir = settings["world"]
        except KeyError:
            self.world_dir = "None"
            self.is_backup = False
            self.update_settings("world", self.world_dir)
            self.update_settings("backup", self.is_backup)
        
        # auto backup
        try:
            self.is_backup = settings["backup"]
            if self.is_backup and self.world_dir != "None":
                self.backup_schedule = schedule.every(1).hour.do(self.backup)

        except KeyError:
            self.is_backup = False
            self.update_settings("backup", self.is_backup)
        
        # rcon
        try:
            self.rcon_adress = settings["rcon_adress"]
            self.rcon_password = settings["rcon_password"]
        except KeyError:
            self.rcon_adress = "Nonn"
            self.rcon_password = "None"

        print("Bot logged in")
    
    # method message received
    async def on_message(self, message):
        # display all commands
        if message.content.lower() == f"{self.prefix}help":
            await message.channel.send(f"""**Here are all commands listed**\n
            prefix is set to: '{self.prefix}', use it before every command\n
            'help' to display this message\n
            'setServerFile:<server_file_path>' to set the path to the server start file\n
            'StartServer' to start the Server file\n
            'StopServer' to stop the server\n
            'SetWorldDir:<path/to/world> set the path to the worldsfolder\n
            'EnableBackup' enables auto backup function every hour\n
            'DisableBackup' disable auto backup function\n
            'BackupStatus' sends the backup status either off or on\n
            """)

        # only available if author has admin role
        if message.author.top_role.permissions.administrator:

            # Start server start script from server_file
            if message.content == f"{self.prefix}StartServer":
                # checks if server_start_file is set
                if self.server_start_file == "None":
                    await message.channel.send(f"[BOT] [INFO]: you need to first set server start file path with: {self.prefix}setServerFile:<server_file_path>")
                elif self.is_server_running == True:
                    await message.channel.send(f"[BOT] [INFO]: Server is running!")
                else:
                    try:
                        await message.channel.send(f"[BOT] [COMMAND]: starting Server...")
                        start_prozess = multiprocessing.Process(target=self.start_server, args=("sh", self.server_start_file))
                        start_prozess.start()
                        self.is_server_running = True
                    except FileNotFoundError as e:
                        await message.channel.send(f"[BOT] [ERROR]: raised {e}")
            # Stop Server currently running
            if message.content == f"{self.prefix}StopServer":
                if self.is_server_running == False:
                    await message.channel.send(f"[BOT] [INFO]: no Server running!")
                else:
                    # connect via rcon to server
                    if self.rcon_adress == "None" or self.rcon_password == "None":
                        await message.channel.send(f"[BOT] [ERROR]: Please set rcon_adress and rcon_password in settings.json to use rcon")
                        self.update_settings("rcon_adress", "None")
                        self.update_settings("rcon_password", "None")
                    else:
                        with MCRcon(self.rcon_adress, self.rcon_password) as mcr:
                            resp = mcr.command("/stop")
                            await message.channel.send(f"[MINECRAFT] [SERVER]: {resp}")
                        self.is_server_running = False

            # set server file path
            if message.content.startswith(f"{self.prefix}setServerFile:"):
                self.server_start_file = message.content.split(":")[1]
                self.update_settings("server_file", self.server_start_file)
                await message.channel.send(f"[BOT] [COMMAND]: changed start file to: '{self.server_start_file}'")
            
            # set minecraft world directory
            if message.content.startswith(f"{self.prefix}SetWorldDir:"):
                world_dir_list = message.content.split(":")
                self.world_dir = ""
                for index in range(1, len(world_dir_list)):
                    self.world_dir += world_dir_list[index]
                self.update_settings("world", self.world_dir)
                await message.channel.send(f"[BOT] [COMMAND]: changed world directory to: '{self.world_dir}'")
            
            # enable auto backup
            if message.content.startswith(f"{self.prefix}EnableBackup"):
                if self.world_dir == "None":
                    await message.channel.send(f"[BOT] [COMMAND]: You first need to set World directory: '{self.prefix}SetWorldDir:<path/to/world>'")
                else:
                    self.backup_schedule = schedule.every(1).hour.do(self.backup)
                    self.is_backup = True
                    self.update_settings("backup", self.is_backup)
                    await message.channel.send(f"[BOT] [COMMAND]: Enabled auto Backup every hour")
            
            # disable auto backup
            if message.content.startswith(f"{self.prefix}DisableBackup"):
                schedule.cancel_job(self.backup_schedule)
                self.is_backup = False
                self.update_settings("backup", self.is_backup)
                await message.channel.send(f"[BOT] [COMMAND]: Disabled auto Backup! At your own Risk!")
            
            # sends backup status
            if message.content.startswith(f"{self.prefix}BackupStatus"):
                if self.is_backup:
                    await message.channel.send(f"[BOT] [COMMAND]: World Backup enabled")
                else:
                    await message.channel.send(f"[BOT] [COMMAND]: World Backup disabled")
    
    
    # save a setting value to name in settings.settings
    def update_settings(self, settings_name, setting_value):
        # read settings data
        with open(f"{self.DIR_PATH}/settings.json", 'r') as f:
            settings = json.loads(f.read())
        settings[settings_name] = setting_value
        # write new settings data
        with open(f"{self.DIR_PATH}/settings.json", 'w') as f:
            f.write(json.dumps(settings))
    
    def start_server(self, sh, start_file):
        subprocess.call([sh, start_file])
    
    # backup minecraft world
    def backup(self):
        print("[BOT] [BACKUP]: Started backup")
        try:
            with MCRcon(self.rcon_adress, self.rcon_password) as mcr:
                mcr.command('/tellraw @a [{"text":"Starting Backup in 5","color":"aqua"}]')
                time.sleep(1)
                mcr.command('/tellraw @a [{"text":"Starting Backup in 4","color":"aqua"}]')
                time.sleep(1)
                mcr.command('/tellraw @a [{"text":"Starting Backup in 3","color":"aqua"}]')
                time.sleep(1)
                mcr.command('/tellraw @a [{"text":"Starting Backup in 2","color":"aqua"}]')
                time.sleep(1)
                mcr.command('/tellraw @a [{"text":"Starting Backup in 1","color":"aqua"}]')
                time.sleep(1)
                mcr.command('/tellraw @a [{"text":"Starting Backup","color":"aqua"}]')
                mcr.command('/stop')
                time.sleep(5)
        except socket.gaierror:
            print("[BOT] [INFO]: Server offline no need to stop")
        backup_path = f"{os.path.dirname(self.world_dir)}/backups"
        if platform.architecture() == 'Windows':
            backup_path.replace('/', '\\')
        if not os.path.exists(backup_path):
            os.mkdir(backup_path)
        if platform.architecture() == 'Windows':
            shutil.copytree(self.world_dir, f"{backup_path}\\world-{time.localtime()[2]}.{time.localtime()[1]}.{time.localtime()[0]}-{time.localtime()[3]}:{time.localtime()[4]}")
        else:
            shutil.copytree(self.world_dir, f"{backup_path}/world-{time.localtime()[2]}.{time.localtime()[1]}.{time.localtime()[0]}-{time.localtime()[3]}:{time.localtime()[4]}")

# run next method schuduled at scheduled time
def check_schedule():
    schedule.run_pending()
    TimerInstance = threading.Timer(60.0, check_schedule)
    TimerInstance.daemon = True
    TimerInstance.start()


if __name__ == '__main__':
    # schedule loop
    check_schedule()

    # directory path
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))

    # saves token in token variable
    with open(f"{DIR_PATH}/token.txt", 'r') as f:
        token = f.read()

    # create instance of Client and runs it
    BotClient = Client()
    BotClient.run(token)