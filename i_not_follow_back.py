from InstaBot import InstaBot
import boto3

SECRET_INSTA = "mickaelyoshua_insta"
SECRET_TELEGRAM = "mickaelyoshua_telegram_insta_bot"
AWS_REGION = "sa-east-1"
CHROME_DRIVER_PATH = "chromedriver.exe"

s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")

insta_bot = InstaBot(SECRET_INSTA, SECRET_TELEGRAM, AWS_REGION, CHROME_DRIVER_PATH)

followers, following = insta_bot.get_followers_following()
print(len(followers), len(following))
r = insta_bot.save_current_followers_following(s3_client, followers, following)
print("Response to saving json file:")
print(r)
i_not_follow_back = insta_bot.get_i_not_follow_back(followers, following)

i_not_follow_back_str = ""
for f in i_not_follow_back:
    if f != i_not_follow_back[-1]:
        i_not_follow_back_str += "instagram.com/" + f + "/" + "\n"
    else:
        i_not_follow_back_str += "instagram.com/" + f + "/"
insta_bot.send_telegram_message("You don't follow back:\n" + i_not_follow_back_str)