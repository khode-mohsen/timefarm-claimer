import os
import sys
import time
import requests
from requests.auth import HTTPProxyAuth
from colorama import *
from datetime import datetime, timedelta, timezone
import json
import random
import brotli

red = Fore.LIGHTRED_EX
yellow = Fore.LIGHTYELLOW_EX
green = Fore.LIGHTGREEN_EX
black = Fore.LIGHTBLACK_EX
blue = Fore.LIGHTBLUE_EX
white = Fore.LIGHTWHITE_EX
reset = Style.RESET_ALL

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))

# Construct the full paths to the files
data_file = os.path.join(script_dir, "data-proxy.json")


class TimeFarm:
    def __init__(self):
        self.line = white + "~" * 50

        self.banner = f"""
        {blue}Smart Airdrop {white}TimeFarm Auto Claimer
        t.me/smartairdrop2120
        
        """

    # Clear the terminal
    def clear_terminal(self):
        # For Windows
        if os.name == "nt":
            _ = os.system("cls")
        # For macOS and Linux
        else:
            _ = os.system("clear")

    def headers(self, auth_data):
        return {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Authorization": f"Bearer {auth_data}",
            "Origin": "https://tg-tap-miniapp.laborx.io",
            "Pragma": "no-cache",
            "Priority": "u=1, i",
            "Referer": "https://tg-tap-miniapp.laborx.io/",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        }

    def proxies(self, proxy_info):
        return {"http": f"{proxy_info}", "https": f"{proxy_info}"}

    def check_ip(self, proxy_info):
        url = "https://api.ipify.org?format=json"

        proxies = self.proxies(proxy_info=proxy_info)

        # Parse the proxy credentials if present
        if "@" in proxy_info:
            proxy_credentials = proxy_info.split("@")[0]
            proxy_user = proxy_credentials.split(":")[1]
            proxy_pass = proxy_credentials.split(":")[2]
            auth = HTTPProxyAuth(proxy_user, proxy_pass)
        else:
            auth = None

        try:
            response = requests.get(url=url, proxies=proxies, auth=auth)
            response.raise_for_status()  # Raises an error for bad status codes
            return response.json().get("ip")
        except requests.exceptions.RequestException as e:
            print(f"IP check failed: {e}")
            return None

    def do_task(self, auth_data, proxy_info):
        url_task = "https://tg-bot-tap.laborx.io/api/v1/tasks"
        headers = self.headers(auth_data=auth_data)
        proxies = self.proxies(proxy_info=proxy_info)
        res = requests.get(url=url_task, headers=headers, proxies=proxies)
        try:
            for task in res.json():
                task_id = task["id"]
                task_title = task["title"]
                task_type = task["type"]
                if task_type == "TELEGRAM":
                    continue
                if "submission" in task.keys():
                    status = task["submission"]["status"]
                    if status == "CLAIMED":
                        self.log(f"{yellow}Task completed: {task_title}")
                        continue

                    if status == "COMPLETED":
                        url_claim = f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}/claims"
                        data = json.dumps({})
                        headers = self.headers(auth_data=auth_data)
                        headers["Content-Length"] = str(len(data))
                        res = requests.post(
                            url=url_claim, headers=headers, data=data, proxies=proxies
                        )
                        if res.text.lower() == "ok":
                            self.log(f"{green}Claim reward successfully: {task_title}")
                            continue

                url_submit = (
                    f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}/submissions"
                )
                data = json.dumps({})
                headers = self.headers(auth_data=auth_data)
                headers["Content-Length"] = str(len(data))
                res = requests.post(
                    url=url_submit, headers=headers, data=data, proxies=proxies
                )
                if res.text.lower() != "ok":
                    self.log(f"{red}Failed submission: {task_title}")
                    continue

                url_task = f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}"
                headers = self.headers(auth_data=auth_data)
                res = requests.get(url=url_task, headers=headers, proxies=proxies)
                status = res.json()["submission"]["status"]
                if status != "COMPLETED":
                    self.log(f"{red}task is not completed !")
                    continue

                url_claim = (
                    f"https://tg-bot-tap.laborx.io/api/v1/tasks/{task_id}/claims"
                )
                data = json.dumps({})
                headers = self.headers(auth_data=auth_data)
                headers["Content-Length"] = str(len(data))
                res = requests.post(
                    url=url_claim, headers=headers, data=data, proxies=proxies
                )
                if res.text.lower() == "ok":
                    self.log(f"{green}Claim reward successfully: {task_title}")
                    continue
        except Exception as e:
            self.log(f"{red}Claim reward error: {white}{e}")

    def ref_claim(self, auth_data, proxy_info):
        url = "https://tg-bot-tap.laborx.io/api/v1/balance/referral/claim"

        data = json.dumps({})

        headers = self.headers(auth_data=auth_data)
        headers["Content-Length"] = str(len(data))

        proxies = self.proxies(proxy_info=proxy_info)

        response = requests.post(url=url, headers=headers, data=data, proxies=proxies)

        return response

    def link(self, auth_data, proxy_info):
        url = "https://tg-bot-tap.laborx.io/api/v1/referral/link"

        headers = self.headers(auth_data=auth_data)

        proxies = self.proxies(proxy_info=proxy_info)

        response = requests.get(url=url, headers=headers, proxies=proxies)

        return response

    def info(self, auth_data, proxy_info):
        url = "https://tg-bot-tap.laborx.io/api/v1/farming/info"

        headers = self.headers(auth_data=auth_data)

        proxies = self.proxies(proxy_info=proxy_info)

        response = requests.get(url=url, headers=headers, proxies=proxies)

        return response

    def start_farming(self, auth_data, proxy_info):
        url = "https://tg-bot-tap.laborx.io/api/v1/farming/start"

        headers = self.headers(auth_data=auth_data)

        proxies = self.proxies(proxy_info=proxy_info)

        data = json.dumps({})

        response = requests.post(url=url, headers=headers, data=data, proxies=proxies)

        return response

    def finish_farming(self, auth_data, proxy_info):
        url = "https://tg-bot-tap.laborx.io/api/v1/farming/finish"

        headers = self.headers(auth_data=auth_data)

        proxies = self.proxies(proxy_info=proxy_info)

        data = json.dumps({})

        response = requests.post(url=url, headers=headers, data=data, proxies=proxies)

        return response

    def log(self, msg):
        now = datetime.now().isoformat(" ").split(".")[0]
        print(f"{black}[{now}]{reset} {msg}{reset}")

    def get_end_time(self, start_time, duration):

        try:
            start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")

            end_time = start_time + timedelta(seconds=duration)

            formatted_end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")

            return formatted_end_time
        except:
            return None

    def parse_proxy_info(self, proxy_info):
        try:
            stripped_url = proxy_info.split("://", 1)[-1]
            credentials, endpoint = stripped_url.split("@", 1)
            user_name, password = credentials.split(":", 1)
            ip, port = endpoint.split(":", 1)
            return {"user_name": user_name, "pass": password, "ip": ip, "port": port}
        except:
            return None

    def main(self):
        while True:
            self.clear_terminal()
            print(self.banner)
            accounts = json.load(open(data_file, "r"))["accounts"]
            num_acc = len(accounts)
            self.log(self.line)
            self.log(f"{green}Numer of account: {white}{num_acc}")
            end_at_list = []
            for no, account in enumerate(accounts):
                self.log(self.line)
                self.log(f"{green}Account number: {white}{no+1}/{num_acc}")
                auth_data = account["acc_info"]
                proxy_info = account["proxy_info"]
                parsed_proxy_info = self.parse_proxy_info(proxy_info)
                if parsed_proxy_info is None:
                    self.log(
                        f"{red}Check proxy format: {white}http://user:pass@ip:port"
                    )
                    break
                ip_adress = parsed_proxy_info["ip"]
                self.log(f"{green}Input IP Address: {white}{ip_adress}")

                ip = self.check_ip(proxy_info=proxy_info)
                self.log(f"{green}Actual IP Address: {white}{ip}")

                # Do task
                self.do_task(auth_data=auth_data, proxy_info=proxy_info)

                # Claim from ref
                try:
                    self.log(f"{yellow}Trying to claim from ref...")
                    ref_claim = self.ref_claim(
                        auth_data=auth_data, proxy_info=proxy_info
                    )
                    if ref_claim.status_code == 200:
                        self.log(f"{green}Claim from ref successful")
                    else:
                        self.log(f"{yellow}Nothing to claim")
                except Exception as e:
                    self.log(f"{red}Claim from ref error!!!")

                # Get user info and farm
                try:
                    while True:
                        info = self.info(
                            auth_data=auth_data, proxy_info=proxy_info
                        ).json()
                        balance = int(float(info["balance"]))
                        farm_start_at = info["activeFarmingStartedAt"]
                        farm_duration = info["farmingDurationInSec"]
                        farm_end_at = self.get_end_time(
                            start_time=farm_start_at, duration=farm_duration
                        )
                        self.log(f"{green}Balance: {white}{balance:,}")
                        self.log(f"{green}Farm end at: {white}{farm_end_at} (UTC)")

                        if farm_start_at is None:
                            start_farming = self.start_farming(
                                auth_data=auth_data, proxy_info=proxy_info
                            )
                            if start_farming.status_code == 200:
                                self.log(f"{green}Start farming successful")
                                info = self.info(
                                    auth_data=auth_data, proxy_info=proxy_info
                                ).json()
                                farm_start_at = info["activeFarmingStartedAt"]
                                farm_duration = info["farmingDurationInSec"]
                                farm_end_at = self.get_end_time(
                                    start_time=farm_start_at, duration=farm_duration
                                )
                                self.log(
                                    f"{green}New farm end at: {white}{farm_end_at} (UTC)"
                                )
                            else:
                                self.log(f"{yellow}Farming already started")

                        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

                        if farm_end_at < now:
                            self.log(f"{yellow}Trying to claim...")
                            finish_farming = self.finish_farming(
                                auth_data=auth_data, proxy_info=proxy_info
                            )
                            if finish_farming.status_code == 200:
                                self.log(f"{green}Claim successful")
                            else:
                                self.log(f"{red}Claim error")
                                break
                        else:
                            self.log(f"{yellow}In farming status, claim later")
                            end_at_list.append(farm_end_at)
                            break
                except Exception as e:
                    self.log(f"{red}Get user info error!!!")

            print()
            if end_at_list:
                now = datetime.now(timezone.utc).timestamp()
                wait_times = []
                for end_at_str in end_at_list:
                    end_at = datetime.strptime(end_at_str, "%Y-%m-%d %H:%M:%S").replace(
                        tzinfo=timezone.utc
                    )
                    if end_at.timestamp() > now:
                        wait_times.append(end_at.timestamp() - now)

                if wait_times:
                    wait_time = min(wait_times)
                else:
                    wait_time = 15 * 60
            else:
                wait_time = 15 * 60

            wait_hours = int(wait_time // 3600)
            wait_minutes = int((wait_time % 3600) // 60)
            wait_seconds = int(wait_time % 60)

            wait_message_parts = []
            if wait_hours > 0:
                wait_message_parts.append(f"{wait_hours} hours")
            if wait_minutes > 0:
                wait_message_parts.append(f"{wait_minutes} minutes")
            if wait_seconds > 0:
                wait_message_parts.append(f"{wait_seconds} seconds")

            wait_message = ", ".join(wait_message_parts)
            print(f"Wait for {wait_message}!")
            time.sleep(wait_time)


if __name__ == "__main__":
    try:
        timefarm = TimeFarm()
        timefarm.main()
    except KeyboardInterrupt:
        sys.exit()
