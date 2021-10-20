from selenium import webdriver
from selenium.webdriver import chrome
import os
import requests
import json


def get_session_cookies():
    # chrome_options = options()
    # chrome_options.add_argument("--windows-size=1920x1080")
    currentdir = os.path.dirname(__file__)
    driverpath = os.path.join(currentdir, "chromedriver.exe").replace("\\", "/")
    if not os.path.exists(driverpath):
        print("Chrome Driver is missing")
    # caps = DesiredCapabilities().CHROME
    # caps["pageLoadStrategy"] = "eager"
    # print("Negotiating with server")
    driver = webdriver.Chrome(executable_path=driverpath)
    driver.get("https://www.nseindia.com")
    cookies = driver.get_cookies()
    cookie_dict = {}
    with open("cookies", 'w') as line:
        for cookie in cookies:
            cookie_dict[cookie['name']] = cookie['value']
        line.write(json.dumps(cookie_dict))
    print(cookie_dict)
    driver.quit()
    return cookie_dict

# try:
#     print("Reading cookie file")
#     cookie_dict = json.load(open('cookies').read())
# except:
#     print("Error Reading Cookies")
#     cookie_dict = get_session_cookies()
#
# session = requests.session()


def fetch_oi():
    global df_list, mp_list
    tries = 1
    max_retries = 3
    try:
        # logger.info("checking data")
        cookies = json.load(open('cookies').read())
    except Exception as error:
        cookies = get_session_cookies()

    while tries <= max_retries:
        # logger.info("Fetching data for {0} try".format(tries))
        # if "NIFTY" not in underlying_sp:
        #     url = 'https://www.nseindia.com/api/option-chain-indices?symbol={0}'.format(underlying_sp)
        # else:
        url = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'

        headers={
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
            'Upgrade-Insecure-Request' : "1", "DNT": "1",
            'Accept-Language' : 'en-IN,en; q=0.9, en-GB; q=0.8, en-US; q=0.7, mr; q=0.6, hi; q=0.5',
            'Accept-Encodong' : 'gzip, deflate, br'
            }

        session=requests.session()
        for cookie in cookies:
            if cookie == "bm_sv":
                session.cookies.set(cookie, cookies[cookie])
        try:
            r = session.get(url, headers=headers, timeout=20).json()
        except Exception as err:
            # logger.info("error Connecting to site, Regenerating")
            print("Error connecting to site, Regenerating")
            cookie_dict = get_session_cookies()
            try:
                r = session.get(url, headers=headers, timeout=25).json()
            except Exception as err:
                print(err)
                tries +=1
                continue
        if 'filtered' not in r:
            tries +=1
            print("not getting data")
        ce_values = [data["CE"] for data in r['filtered']['data'] if "CE" in data]
        pe_values = [data["PE"] for data in r['filtered']['data'] if "PE" in data]
        print(ce_values)

def main():
    fetch_oi()


if __name__ == '__main__':
    main()
