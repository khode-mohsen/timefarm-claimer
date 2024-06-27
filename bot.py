import os
import sys
import json
import time
import requests
from colorama import init, Fore, Style
from base64 import b64decode
from datetime import datetime
from urllib.parse import unquote
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

init(autoreset=True)

# Define colors
black = Fore.LIGHTBLACK_EX
green = Fore.LIGHTGREEN_EX
red = Fore.LIGHTRED_EX
yellow = Fore.LIGHTYELLOW_EX
blue = Fore.LIGHTBLUE_EX
white = Fore.LIGHTWHITE_EX
reset = Style.RESET_ALL

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))

# Construct the full paths to the files
data_file = os.path.join(script_dir, "data.txt")
tokens_file = os.path.join(script_dir, "tokens.json")


class TimeFarm:
    def __init__(self):
        self.headers = self._default_headers()
        self.line = white + "~" * 50

    def _default_headers(self):
        return {
            "Host": "tg-bot-tap.laborx.io",
            "Connection": "keep-alive",
            "User-Agent": "",
            "Content-Type": "text/plain;charset=UTF-8",
            "Accept": "*/*",
            "Origin": "https://tg-tap-miniapp.laborx.io",
            "X-Requested-With": "org.telegram.messenger",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://tg-tap-miniapp.laborx.io/",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en,en-US;q=0.9",
        }

    @staticmethod
    def cvdate(date):
        return datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z").timestamp()

    @staticmethod
    def get_random_user_agent():
        software = [
            SoftwareName.CHROME.value,
            SoftwareName.EDGE.value,
        ]
        operating = [
            OperatingSystem.ANDROID.value,
            OperatingSystem.WINDOWS.value,
            OperatingSystem.IOS.value,
        ]
        user_agent_rotator = UserAgent(
            software_names=software, operating_systems=operating, limit=100
        )
        return user_agent_rotator.get_random_user_agent()

    def get_task(self, token):
        url_task = "https://tg-bot-tap.laborx.io/api/v1/tasks"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {token}"
        res = self.http_request(url_task, headers)

        if not res.ok:
            self.log(f"{red}Failed to fetch tasks.")
            return

        try:
            tasks = res.json()
            for task in tasks:
                self.process_task(task, headers)
        except json.JSONDecodeError:
            self.log(f"{red}Failed to decode task response.")

    def process_task(self, task, headers):
        task_id = task["id"]
        task_title = task["title"]
        task_type = task["type"]
        if task_type == "TELEGRAM":
            return

        if "submission" in task.keys():
            status = task["submission"]["status"]
            if status == "CLAIMED":
                self.log(f"{yellow}Task completed: {task_title}")
                return

            if status == "COMPLETED":
                self.claim_reward(task_id, task_title, headers)
                return

        self.submit_task(task_id, task_title, headers)

    def claim_reward(self, task_id, task_title, headers):
        url_claim = f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}/claims"
        data = json.dumps({})
        headers["Content-Length"] = str(len(data))
        res = self.http_request(url_claim, headers, data)

        if res.text.lower() == "ok":
            self.log(f"{green}Claim reward successfully: {task_title}")
        else:
            self.log(f"{red}Failed to claim reward: {task_title}")

    def submit_task(self, task_id, task_title, headers):
        url_submit = f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}/submissions"
        data = json.dumps({})
        headers["Content-Length"] = str(len(data))
        res = self.http_request(url_submit, headers, data)

        if res.text.lower() != "ok":
            self.log(f"{red}Failed submission: {task_title}")
            return

        url_task = f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}"
        res = self.http_request(url_task, headers)

        if not res.ok:
            self.log(f"{red}Failed to fetch task status: {task_title}")
            return

        try:
            status = res.json()["submission"]["status"]
            if status != "COMPLETED":
                self.log(f"{red}Task is not completed: {task_title}")
                return

            self.claim_reward(task_id, task_title, headers)
        except json.JSONDecodeError:
            self.log(f"{red}Failed to decode task status response: {task_title}")

    def get_farming_info(self, token):
        url = "https://tg-bot-tap.laborx.io/api/v1/farming/info"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {token}"
        res = self.http_request(url, headers)

        if not res.ok:
            self.log(f"{red}Failed to fetch farming info.")
            return

        try:
            farming_info = res.json()
            balance = farming_info["balance"]
            self.log(f"{green}Balance: {white}{balance}")
            return farming_info
        except json.JSONDecodeError:
            self.log(f"{red}Failed to decode farming info response.")
            return

    def handle_farming(self, token):
        farming_info = self.get_farming_info(token)
        if not farming_info:
            return

        start_farming = farming_info["activeFarmingStartedAt"]
        if start_farming is None:
            return self.start_farming(token)

        return self.check_farming_status(
            token, start_farming, farming_info["farmingDurationInSec"]
        )

    def start_farming(self, token):
        url_start = "https://tg-bot-tap.laborx.io/api/v1/farming/start"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {token}"
        data = json.dumps({})
        res = self.http_request(url_start, headers, data)

        if not res.ok:
            self.log(f"{red}Failed to start farming.")
            return

        try:
            now = self.cvdate(res.headers["Date"])
            start_farming = res.json()["activeFarmingStartedAt"].replace("Z", "")
            start_farming_ts = int(datetime.fromisoformat(start_farming).timestamp())
            farming_duration = res.json()["farmingDurationInSec"]
            end_farming = start_farming_ts + farming_duration
            end_farming_iso = datetime.fromtimestamp(end_farming)
            countdown = end_farming - now
            self.log(f"{green}End farming at: {white}{end_farming_iso} (UTC)")
            return countdown
        except (json.JSONDecodeError, KeyError):
            self.log(f"{red}Failed to decode farming start response.")
            return

    def check_farming_status(self, token, start_farming, farming_duration):
        url_check = "https://tg-bot-tap.laborx.io/api/v1/farming/info"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {token}"
        res = self.http_request(url_check, headers)

        if not res.ok:
            self.log(f"{red}Failed to fetch current farming status.")
            return

        try:
            now = self.cvdate(res.headers["Date"])
            start_farming = start_farming.replace("Z", "")
            start_farming_ts = int(datetime.fromisoformat(start_farming).timestamp())
            end_farming = start_farming_ts + farming_duration
            end_farming_iso = datetime.fromtimestamp(end_farming)
            countdown = end_farming - now

            if now > end_farming:
                self.log(f"{green}Farming ended.")
                self.finish_farming(token)
                return self.start_farming(token)

            self.log(f"{yellow}Farming not ended yet.")
            self.log(f"{green}End farming at: {white}{end_farming_iso} (UTC)")
            return countdown
        except (json.JSONDecodeError, KeyError):
            self.log(f"{red}Failed to decode farming status response.")
            return

    def finish_farming(self, token):
        url_finish = "https://tg-bot-tap.laborx.io/api/v1/farming/finish"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {token}"
        data = json.dumps({})
        res = self.http_request(url_finish, headers, data)

        if not res.ok:
            self.log(f"{red}Failed to finish farming.")
            return

        try:
            balance = res.json()["balance"]
            self.log(f"{green}Balance after farming: {white}{balance}")
        except json.JSONDecodeError:
            self.log(f"{red}Failed to decode farming finish response.")

    def get_token(self, tg_data):
        url = "https://tg-bot-tap.laborx.io/api/v1/auth/validate-init"
        headers = self.headers.copy()
        res = self.http_request(url, headers, tg_data)

        if not res.ok:
            self.log(f"{red}Failed to get token.")
            return False

        try:
            token = res.json().get("token")
            if token:
                self.log(f"{green}Token found!")
                self.check_daily_reward(res, token, headers)
                return token
            else:
                self.log(f"{red}Token not found in response.")
                return False
        except json.JSONDecodeError:
            self.log(f"{red}Failed to decode token response.")
            return False

    def check_daily_reward(self, res, token, headers):
        try:
            daily = res.json().get("dailyRewardInfo")
            if daily is not None:
                reward = daily["reward"]
                headers["authorization"] = f"Bearer {token}"
                claim_url = "https://tg-bot-tap.laborx.io/api/v1/me/onboarding/complete"
                claim_res = self.http_request(claim_url, headers, json.dumps({}))
                if claim_res.status_code == 200:
                    self.log(f"{green}Success claim daily reward: {white}{reward}!")
            else:
                self.log(f"{yellow}Daily reward claimed")
        except json.JSONDecodeError:
            self.log(f"{red}Failed to decode daily reward response.")

    @staticmethod
    def parse_data(data):
        ret = {}
        for i in unquote(data).split("&"):
            key, value = i.split("=")
            ret[key] = value

        return ret

    @staticmethod
    def is_token_expired(token):
        try:
            header, payload, sign = token.split(".")
            depayload = b64decode(payload + "==")
            jeload = json.loads(depayload)
            expired = jeload["exp"]
            now = int(datetime.now().timestamp())
            return now > int(expired)
        except (ValueError, json.JSONDecodeError):
            return True

    def main(self):
        self.display_banner()
        while True:
            list_countdown = []
            datas = self.read_data_file()
            tokens = self.read_tokens_file()

            if not datas:
                self.log(f"{yellow}Add your data into data.txt to re-run this tool")
                sys.exit()

            self.log(f"{green}Number of accounts: {white}{len(datas)}")
            print(self.line)
            for data in datas:
                parser = self.parse_data(data)
                user = json.loads(parser["user"])
                userid = str(user["id"])

                user_token, user_ua = self.get_or_renew_token(userid, parser, tokens)
                if not user_token:
                    continue

                self.headers["User-Agent"] = user_ua
                self.log(f"{green}Account name: {white}{user['first_name']}")
                self.get_token(data)
                self.get_task(user_token)
                curse = self.handle_farming(user_token)
                list_countdown.append(curse)
                print(self.line)
                self.countdown(5)

            min_countdown = min(list_countdown, default=15 * 60)
            self.countdown(int(min_countdown))

    def get_or_renew_token(self, userid, parser, tokens):
        if userid not in tokens:
            user_ua = self.get_random_user_agent()
            self.headers["User-Agent"] = user_ua
            user_token = self.get_token(parser)
            if not user_token:
                return None, None

            tokens[userid] = {"token": user_token, "ua": user_ua}
            self.write_tokens_file(tokens)

        user_token = tokens[userid]["token"]
        user_ua = tokens[userid]["ua"]

        if self.is_token_expired(user_token):
            self.headers["User-Agent"] = user_ua
            user_token = self.get_token(parser)
            if not user_token:
                return None, None

            tokens[userid]["token"] = user_token
            self.write_tokens_file(tokens)

        return user_token, user_ua

    def display_banner(self):
        banner = f"""
        {blue}Smart Airdrop {white}Time Farm Auto Claimer
        t.me/smartairdrop2120
        """
        arg = sys.argv
        if "--no-clear" not in arg:
            os.system("cls" if os.name == "nt" else "clear")
        print(banner)
        print(self.line)

    @staticmethod
    def read_data_file():
        with open(data_file, "r") as file:
            return file.read().splitlines()

    @staticmethod
    def read_tokens_file():
        with open(tokens_file, "r") as file:
            return json.loads(file.read())

    @staticmethod
    def write_tokens_file(tokens):
        with open(tokens_file, "w") as file:
            file.write(json.dumps(tokens, indent=4))

    @staticmethod
    def countdown(t):
        while t:
            mins, secs = divmod(t, 60)
            hrs, mins = divmod(mins, 60)
            print(
                f"{white}Time left: {hrs:02d}:{mins:02d}:{secs:02d} ",
                flush=True,
                end="\r",
            )
            t -= 1
            time.sleep(1)
        print("                          ", flush=True, end="\r")

    def http_request(self, url, headers, data=None):
        while True:
            try:
                if data is None:
                    headers["Content-Length"] = "0"
                    return requests.get(url, headers=headers)
                if data == "":
                    return requests.post(url, headers=headers)
                return requests.post(url, headers=headers, data=data)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                self.log(f"{red}Connection error or timeout!")
                time.sleep(2)

    def log(self, msg):
        now = datetime.now().isoformat(" ").split(".")[0]
        print(f"{black}[{now}] {reset}{msg}")


if __name__ == "__main__":
    try:
        app = TimeFarm()
        app.main()
    except KeyboardInterrupt:
        sys.exit()
