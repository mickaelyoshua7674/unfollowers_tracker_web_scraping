from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import re
import boto3
import ast
import json

class InstaBot:
    def __init__(self, name_aws_secret_insta: str, aws_region: str, chrome_driver_path: str) -> None:
        # GET INSTA USERNAME AND PASSWORD FROM AWS SECRETS MANAGER
        self.CHROME_DRIVER_PATH = chrome_driver_path
        print("Getting username and login...")
        secrets_manager = boto3.session.Session().client(
                        service_name = "secretsmanager",
                        region_name = aws_region
                        )
        secret_response_insta = secrets_manager.get_secret_value(
                                SecretId = name_aws_secret_insta
                                )
        self.INSTA_USERNAME = ast.literal_eval(secret_response_insta["SecretString"])["username"]
        self.INSTA_PASSWORD = ast.literal_eval(secret_response_insta["SecretString"])["password"]
                                # ast.literal_eval() turns a string to a dict
        self.S3_BUCKET = "insta-followees-followers"

        # INITIALIZING CHROME DRIVER
        op = webdriver.ChromeOptions()
        op.add_argument("headless") # don't open a Chrome window
        driver = webdriver.Chrome(executable_path=self.CHROME_DRIVER_PATH, options=op)

        # GET NUMBER OF FOLLOWERS AND FOLLOWING
        print("Getting number of followers and following...")
        driver.get(f"https://www.instagram.com/{self.INSTA_USERNAME}/")
        time.sleep(5)
        num_followers = driver.find_elements(By.CSS_SELECTOR, "._ac2a")[1].text
        num_following = driver.find_elements(By.CSS_SELECTOR, "._ac2a")[2].text
        self.num_followers = int(re.sub("(\.)|(,)", "", num_followers)) # remove . or , from text and turning into a int
        self.num_following = int(re.sub("(\.)|(,)", "", num_following))
        driver.quit()

        self.css_selector_followers = ".x9f619.xjbqb8w.x1rg5ohu.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1n2onr6" + \
                                    ".x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.x1q0g3np.xqjyukv.x6s0dn4.x1oa3qoh.x1nhvcw1"
        self.css_selector_following = ".x9f619.xjbqb8w.x1rg5ohu.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1n2onr6" + \
                                    ".x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.x1q0g3np.xqjyukv.x6s0dn4.x1oa3qoh.x1nhvcw1"

    def get_num_followers_following(self) -> int:
        """Return the number of followers and following"""
        return self.num_followers, self.num_following

    def get_followers_following(self) -> list[str]:
        """Go on Chrome, make login on account and web scrap the followers and following returning a list of each"""

        # INITIALIZING CHROME DRIVER
        op = webdriver.ChromeOptions()
        op.add_argument("headless") # don't open a Chrome window
        driver = webdriver.Chrome(executable_path=self.CHROME_DRIVER_PATH, options=op)

        # LOGIN ON ACCOUNT
        print("Login on account...")
        driver.get("https://www.instagram.com/")
        time.sleep(4)
        login = driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[1]/div/label/input')
        login.send_keys(self.INSTA_USERNAME) # fill username
        passw = driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[2]/div/label/input')
        passw.send_keys(self.INSTA_PASSWORD) # fill password
        time.sleep(0.5)
        passw.send_keys(Keys.ENTER) # press Enter
        time.sleep(5)

        # WEB SCRAPING FOLLOWERS
        print("Getting followers list...")
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

        # WEB SCRAPING FOLLOWING
        print("Getting following list...")
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

        return followers, following
    
    def get_not_follow_back(self, followers: list[str], following: list[str]):
        not_follow_back = []
        for f in following:
            if f not in followers: # if the following is not on followers
                not_follow_back.append(f)
        return not_follow_back
    
    def save_current_followers_following(self, s3_client: boto3.client, followers: list[str], following: list[str]) -> dict:
        """
        Receive the followers and following, put the object 
        in Amazon S3 bucket and return the response for create a S3 object
        """
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
        return response
    
    def get_saved_followers_following(self, s3_resource: boto3.resource) -> list[str]:
        """
        Receive the boto3.resource object and get the data from
        the S3 Object.
        """
        data = s3_resource.Object(
            bucket_name = self.S3_BUCKET,
            key = self.INSTA_USERNAME + ".json"
        ).get()["Body"].read() # return a byte string
        
        dict_data = json.loads(data.decode('utf-8')) # decoding

        return dict_data["followers"], dict_data["following"]