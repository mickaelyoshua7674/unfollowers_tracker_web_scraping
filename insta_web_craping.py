from InstaBot import InstaBot

SECRET_INSTA = "mickaelyoshua_insta"
AWS_REGION = "sa-east-1"
CHROME_DRIVER_PATH = "chromedriver.exe"

insta_bot = InstaBot(SECRET_INSTA, AWS_REGION, CHROME_DRIVER_PATH)
print(insta_bot.INSTA_USERNAME, insta_bot.INSTA_PASSWORD)

followers, following = insta_bot.get_followers_following()
print(len(followers, following))

not_follow_back = insta_bot.get_not_follow_back(followers, following)
print(len(not_follow_back))

for f in not_follow_back:
    print("https://www.instagram.com/" + f + "/")