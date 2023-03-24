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
saved_followers, _ = insta_bot.get_saved_followers_following(s3_resource)

unfollowers = insta_bot.get_unfollowers(followers, saved_followers)
unfollowers_str = ""
if len(unfollowers) > 0:
    for f in unfollowers:
        if f != unfollowers[-1]:
            unfollowers_str += "instagram.com/" + f + "/" + "\n"
        else:
            unfollowers_str += "instagram.com/" + f + "/"
else:
    unfollowers_str = "None"
insta_bot.send_telegram_message("Unfollowers / deleted account / changed username:\n" + unfollowers_str)

r = insta_bot.save_current_followers_following(s3_client, followers, following)
print("Response to saving json file:")
print(r)