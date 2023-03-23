from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import re
import boto3
import ast
import json
import requests
import traceback
import sys

def print_error():
    """Print the error message and exit script."""
    traceback.print_exc()
    print("Closing...")
    sys.exit()

class InstaBot:
    def __init__(self, name_aws_secret_insta: str, name_aws_secret_telegram: str, aws_region: str, chrome_driver_path: str) -> None:
        # GET INSTA USERNAME AND PASSWORD FROM AWS SECRETS MANAGER
        self.CHROME_DRIVER_PATH = chrome_driver_path
        print(f"Getting Insta username and password from AWS Secrets Manager's secret '{name_aws_secret_insta}'...")
        try:
            secrets_manager = boto3.session.Session().client(service_name="secretsmanager", region_name=aws_region)
            secret_response_insta = secrets_manager.get_secret_value(SecretId=name_aws_secret_insta)
            self.INSTA_USERNAME = ast.literal_eval(secret_response_insta["SecretString"])["username"]
            self.INSTA_PASSWORD = ast.literal_eval(secret_response_insta["SecretString"])["password"]
                                    # ast.literal_eval() turns a string to a dict
            print("Insta username and password loaded.\n")
        except:
            print("Error getting secrets...\n")
            print_error()
        
        # GET TELEGRAM API TOKEN AND CHAT ID
        print(f"Getting telegram API Token and Telegram Chat ID from AWS Secrets Manager's secret '{name_aws_secret_telegram}'...")
        try:
            secret_response_telegram = secrets_manager.get_secret_value(SecretId=name_aws_secret_telegram)
            self.TELEGRAM_API_TOKEN = ast.literal_eval(secret_response_telegram["SecretString"])["telegram_api_token"]
            # to create your telegram bot https://sendpulse.com/knowledge-base/chatbot/telegram/create-telegram-chatbot
            self.TELEGRAM_CHAT_ID = ast.literal_eval(secret_response_telegram["SecretString"])["telegram_chat_id"]
            # send a message to your bot and get chat id https://api.telegram.org/bot<YourBOTToken>/getUpdates
            self.TELEGRAM_API_URL_MESSAGE = f"https://api.telegram.org/bot{self.TELEGRAM_API_TOKEN}/sendMessage"
            print("Telegram API Token and Telegram Chat ID loaded.\n")
        except:
            print("Error getting secrets...\n")
            print_error()

        self.S3_BUCKET = "insta-followees-followers"

        # INITIALIZING CHROME DRIVER
        print("Initializing Chrome driver...")
        try:
            op = webdriver.ChromeOptions()
            op.add_argument("headless") # don't open a Chrome window
            driver = webdriver.Chrome(executable_path=self.CHROME_DRIVER_PATH, options=op)
            print("Chrome driver initialized.\n")
        except:
            print("Error initializing Chrome driver...\n")
            print_error()

        # GET NUMBER OF FOLLOWERS AND FOLLOWING
        print("Getting number of followers and following...")
        try:
            driver.get(f"https://www.instagram.com/{self.INSTA_USERNAME}/")
            time.sleep(5)
            num_followers = driver.find_elements(By.CSS_SELECTOR, "._ac2a")[1].text
            num_following = driver.find_elements(By.CSS_SELECTOR, "._ac2a")[2].text
            self.num_followers = int(re.sub("(\.)|(,)", "", num_followers)) # remove . or , from text and turning into a int
            self.num_following = int(re.sub("(\.)|(,)", "", num_following))
            driver.quit()
            print("Number of followers and following loaded.\n")
        except:
            print("Error getting numbers...\n")
            print_error()

        self.css_selector_followers = ".x9f619.xjbqb8w.x1rg5ohu.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1n2onr6" + \
                                    ".x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.x1q0g3np.xqjyukv.x6s0dn4.x1oa3qoh.x1nhvcw1"
        self.css_selector_following = ".x9f619.xjbqb8w.x1rg5ohu.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1n2onr6" + \
                                    ".x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.x1q0g3np.xqjyukv.x6s0dn4.x1oa3qoh.x1nhvcw1"
        print("\n---------------------------------Object initialized successfully---------------------------------\n")

    def get_num_followers_following(self) -> int:
        """Return the number of followers and following"""
        return self.num_followers, self.num_following

    def get_followers_following(self) -> list[str]:
        """Go on Chrome, make login on account and web scrap the followers and following returning a list of each"""
        print("Getting list of followers and following...")
        # INITIALIZING CHROME DRIVER
        print("    Initializing Chrome driver...")
        try:
            op = webdriver.ChromeOptions()
            op.add_argument("headless") # don't open a Chrome window
            driver = webdriver.Chrome(executable_path=self.CHROME_DRIVER_PATH, options=op)
        except:
            print("    Error initializing Chrome driver...\n")
            print_error()

        # LOGIN ON ACCOUNT
        print("   Entering the account...")
        try:
            driver.get("https://www.instagram.com/")
            time.sleep(4)
            login = driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[1]/div/label/input')
            login.send_keys(self.INSTA_USERNAME) # fill username
            passw = driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[2]/div/label/input')
            passw.send_keys(self.INSTA_PASSWORD) # fill password
            time.sleep(0.5)
            passw.send_keys(Keys.ENTER) # press Enter
            time.sleep(5)
            print("    Login successfull.\n")
        except:
            print("    Login failed...\n")
            print_error()

        # WEB SCRAPING FOLLOWERS
        print("    Getting followers list...")
        try:
            driver.get(f"https://www.instagram.com/{self.INSTA_USERNAME}/followers/") # go to page of followers
            time.sleep(5)
            follower_obj = driver.find_elements(By.CSS_SELECTOR, self.css_selector_followers) # get initial list of followers
            driver.execute_script("arguments[0].scrollIntoView(true);", follower_obj[-1]) # scroll down to last follower showing on list

            while True:
                new_follower_obj = driver.find_elements(By.CSS_SELECTOR, self.css_selector_followers) # get new list of followers
                if len(new_follower_obj) >= self.num_followers-2: # when all followers are loaded on page exit the loop
                    break
                else:
                    driver.execute_script("arguments[0].scrollIntoView(true);", new_follower_obj[-1]) # scroll down to last follower showing on list
                    follower_obj = new_follower_obj # update previous followers to get the new followers

            follower_obj = driver.find_elements(By.CSS_SELECTOR, self.css_selector_followers) # get all followers
            followers = []
            for f in follower_obj:
                followers.append(f.text) # get username of all followers
            for i in range(len(followers)):
                followers[i] = re.sub("\n.*", "", followers[i]) # remove text of verified accounts
            print("    Followers list loaded.\n")
        except:
            print("    Load followers list failed...\n")
            print_error()

        # WEB SCRAPING FOLLOWING
        print("    Getting following list...")
        try:
            driver.get(f"https://www.instagram.com/{self.INSTA_USERNAME}/following/") # go to page of following
            time.sleep(5)
            following_obj = driver.find_elements(By.CSS_SELECTOR, self.css_selector_following) # get initial list of following
            driver.execute_script("arguments[0].scrollIntoView(true);", following_obj[-1]) # scroll down to last following showing on list

            while True:
                new_following_obj = driver.find_elements(By.CSS_SELECTOR, self.css_selector_following) # get new list of followers
                if len(new_following_obj) >= self.num_following-2: # when all following are loaded on page exit the loop
                    break
                else:
                    driver.execute_script("arguments[0].scrollIntoView(true);", new_following_obj[-1]) # scroll down to last following showing on list
                    following_obj = new_following_obj # update previous following to get the new following

            following_obj = driver.find_elements(By.CSS_SELECTOR, self.css_selector_following) # get all following
            following = []
            for f in following_obj:
                following.append(f.text) # get username of all following
            for i in range(len(following)):
                following[i] = re.sub("\n.*", "", following[i]) # remove text of verified accounts
            driver.quit()
            print("    Following list loaded.\n")
        except:
            print("    Load following list failed...\n")
            print_error()

        return followers, following
    
    def get_not_follow_back(self, followers: list[str], following: list[str]):
        """Return a list with all users tha don't follow you back."""
        print("Getting list of not following back...")
        try:
            not_follow_back = []
            for f in following:
                if f not in followers: # if the following is not on followers
                    not_follow_back.append(f)
            print("List of not following back generated.\n")
            return not_follow_back
        except:
            print("Error getting list of not following back...\n")
            print_error()
    
    def save_current_followers_following(self, s3_client: boto3.client, followers: list[str], following: list[str]) -> dict:
        """
        Receive the followers and following, put the object 
        in Amazon S3 bucket and return the response for create a S3 object
        """
        print("Saving json file with followers and following...")
        try:
            data = { # making dict format to store
                "username": self.INSTA_USERNAME,
                "followers": followers,
                "following": following
            }

            response = s3_client.put_object(
                Bucket = self.S3_BUCKET, # name of the bucket target
                Key = f"{self.INSTA_USERNAME}.json", # file name to be storage
                Body = json.dumps(data) # json.dumps to make a json format
            )
            print("File saved.\n")
            return response
        except:
            print("Error saving file...\n")
            print_error()
    
    def get_saved_followers_following(self, s3_resource: boto3.resource) -> list[str]:
        """
        Receive the boto3.resource object and get the data from
        the S3 Object.
        """
        print("Loading saved lists of followers and following...")
        try:
            data = s3_resource.Object(
                bucket_name = self.S3_BUCKET,
                key = self.INSTA_USERNAME + ".json"
            ).get()["Body"].read() # return a byte string
            
            dict_data = json.loads(data.decode('utf-8')) # decoding
            print("Lists loaded.\n")
            return dict_data["followers"], dict_data["following"]
        except:
            print("Error loading lists...\n")
            print_error()
    
    def send_telegram_message(self, message: str) -> None:
        """Send the input text to the telegram chat id"""
        print("Sending telegram message...")
        try:
            requests.post(self.TELEGRAM_API_URL_MESSAGE, json={"chat_id": self.TELEGRAM_CHAT_ID, "text": message})
            print("Message sended.\n")
        except:
            print("Error sending message...\n")
            print_error()
