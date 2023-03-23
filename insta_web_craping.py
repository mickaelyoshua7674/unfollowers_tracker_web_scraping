from InstaBot import InstaBot
import boto3

SECRET_INSTA = "mickaelyoshua_insta"
SECRET_TELEGRAM = "mickaelyoshua_telegram_insta_bot"
AWS_REGION = "sa-east-1"
CHROME_DRIVER_PATH = "chromedriver.exe"

s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")

insta_bot = InstaBot(SECRET_INSTA, SECRET_TELEGRAM, AWS_REGION, CHROME_DRIVER_PATH)

# followers, following = insta_bot.get_followers_following()
# print(len(followers), len(following))
followers = ["u2", "u3", "u4"]
following = ["u5", "u6", "u7"]

r = insta_bot.save_current_followers_following(s3_client, followers, following)
print(r)

saved_followers, saved_following = insta_bot.get_saved_followers_following(s3_resource)
print(saved_followers)
print(saved_following)

insta_bot.send_telegram_message("testando2")