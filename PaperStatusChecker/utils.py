from splinter import Browser
from bs4 import BeautifulSoup
import json
from datetime import datetime

def IEEEChecker(site, username, password):
    '''
    site: 期刊对应的网址
    username: 账号
    password: 密码
    '''
    with Browser('chrome', headless=False) as b:
        b.visit(site) # TODO: 期刊对应的网址
        # 等待元素出现（最长 10 秒）
        if b.is_element_present_by_name("USERID", wait_time=10):
            b.fill("USERID", username) # TODO: 填写账号
            b.fill("PASSWORD", password) # TODO: 填写密码
            b.find_by_id("logInButton").first.click()
            if b.is_element_present_by_css("a[href*='AUTHOR_VIEW_MANUSCRIPTS']", wait_time=10): 
                b.find_by_css("a[href*='AUTHOR_VIEW_MANUSCRIPTS']").first.click()
                if b.is_element_present_by_css("td[data-label='title']", wait_time=20):
                    html_obj = b.html
                    soup = BeautifulSoup(html_obj,"lxml")
                    table = soup.find("span", attrs={"class": "pagecontents"})
                    td = soup.find("td", {"data-label": "title"})
                    title = td.get_text(separator="\n", strip=True).split("\n")[0]
                    current_manuscript_status = table.string
                    print(f"Title: {title}")
                    print(f"Status: {current_manuscript_status}")
                else:
                    print("❌ Manuscript table not loaded")
            else:
                print("❌ Author button not found")
        else:
            print("❌ USERID input not found")
    return title, current_manuscript_status

def ElsevierChecker(site, username, password, stage):
    '''
    site: 期刊对应的网址
    username: 账号
    password: 密码
    stage: 状态
        如果是初审 - init
        如果是复审 - revision
    '''
    with Browser('chrome', headless=False) as b:
        b.visit(site) # TODO: 期刊对应的网址
        # 等待 iframe 出现
        if b.is_element_present_by_name("login", wait_time=10):
            # 切换到 iframe
            b.driver.switch_to.frame("login")

            # 等待用户名输入框
            if b.is_element_present_by_name("username", wait_time=10):
                b.fill("username", username) # TODO: 填写账号
                b.fill("password", password) # TODO: 填写密码

                try:
                    b.find_by_name("authorLogin").first.click()
                except:
                    b.execute_script("doLogin('author');")
            else:
                print("❌ username input not found inside iframe")


            # 登录后要切回主页面，否则找不到菜单
            b.driver.switch_to.default_content()
            # 再切换到 content iframe
            b.driver.switch_to.frame("content")
            # 等待并进入稿件页面
            if stage == 'revision' and b.is_element_present_by_css("a[href*='auth_RevisionsBeingProcessed.asp']", wait_time=10): 
                b.find_by_css("a[href*='auth_RevisionsBeingProcessed.asp']").first.click()
            elif stage == 'init' and b.is_element_present_by_css("a[href*='uth_pendSubmissions.asp']", wait_time=10): #TODO: Submissions Being Processed
                b.find_by_css("a[href*='uth_pendSubmissions.asp']").first.click()
            else:
                print("❌ The stage name is wrong")

            if b.is_element_present_by_css("tr[id^='row']", wait_time=20):
                html_obj = b.html
                soup = BeautifulSoup(html_obj, "lxml")

                rows = soup.select("tr[id^='row']")  # 匹配所有行
                for row in rows:
                    cols = row.find_all("td")
                    title = cols[2].get_text(strip=True)
                    current_manuscript_status = cols[-1].get_text(strip=True)
                    print(f"Title: {title}")
                    print(f"Status: {current_manuscript_status}")
            else:
                print("❌ No manuscript rows found")
        else:
            print("❌ login iframe not found")
    return title, current_manuscript_status

def check_status(journal_key, **kwargs):
    with open('myconfig.json', "r", encoding="utf-8") as f:
        config = json.load(f)

    publisher = config[journal_key]["publisher"]
    site = config[journal_key]["site"]
    username = config[journal_key]["username"]
    password = config[journal_key]["password"]

    if publisher == 'Elsevier':
        title, current_manuscript_status = ElsevierChecker(site, username, password, kwargs.get("stage"))
    elif publisher == 'IEEE':
        title, current_manuscript_status = IEEEChecker(site, username, password)
    else:
        raise ValueError(f"Unknown publisher: {publisher}")
    save_to_txt(title, current_manuscript_status, journal_key)
    return f"Journal: {journal_key}\nTitle: {title}\nStatus: {current_manuscript_status}"


def save_to_txt(title, status, journal_key, filename="check_history.txt"):
    """保存一条记录到文本表格"""
    today = datetime.now().strftime("%Y-%m-%d")
    header = ["Date", "Journal", "Status", "Title"]

    # 检查是否需要写表头
    try:
        with open(filename, "x", encoding="utf-8") as f:
            f.write("{:<10} | {:<10} | {:<20} | {:<20}\n".format(*header))
            f.write("-" * 70 + "\n")
            f.write("{:<10} | {:<10} | {:<20} | {:<20}\n".format(today, journal_key, status, title))
    except FileExistsError:
        with open(filename, "a", encoding="utf-8") as f:
            f.write("{:<10} | {:<10} | {:<20} | {:<20}\n".format(today, journal_key, status, title))