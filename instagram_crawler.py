import os
import re
import sys
import json
import time
import random
import requests
from hashlib import md5
from pyquery import PyQuery as pq

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
}
uri = 'https://www.instagram.com/graphql/query/?query_hash=a5164aed103f24b03e7b7747a2d94e3c&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A12%2C%22after%22%3A%22{cursor}%22%7D'


def get_html(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print('Error html path:', response.status_code)
            return False
    except Exception as e:
        print(e)
        return False

def get_json(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print('get json error:', response.status_code)
    except Exception as e:
        print(e)
        time.sleep(30 + float(random.randint(1, 400))/100)
        return get_json(url)

def get_content(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            print('get content error:', response.status_code)
    except Exception as e:
        print(e)
        return None
 
def get_urls(html):
    urls = []
    user_id = re.findall('"profilePage_([0-9]+)"', html, re.S)[0]
    print('user_id:' + user_id)
    doc = pq(html)
    items = doc('script[type="text/javascript"]').items()
    for item in items:
        if item.text().strip().startswith('window._sharedData'):
            js_data = json.loads(item.text()[21:-1], encoding='utf-8')
            edges = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]
            page_info = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]['page_info']
            cursor = page_info['end_cursor']
            flag = page_info['has_next_page']
            for edge in edges:
                if edge['node']['display_url']:
                    display_url = edge['node']['display_url']
                    #print(display_url)
                    urls.append(display_url)
            #print(cursor, flag)
    return urls

def get_full_urls(html,num):
    count = num//12 + 1
    urls = []
    user_id = re.findall('"profilePage_([0-9]+)"', html, re.S)[0]
    print('user_id：' + user_id)
    doc = pq(html)
    items = doc('script[type="text/javascript"]').items()
    for item in items:
        if item.text().strip().startswith('window._sharedData'):
            js_data = json.loads(item.text()[21:-1], encoding='utf-8')
            edges = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]
            page_info = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]['page_info']
            cursor = page_info['end_cursor']
            flag = page_info['has_next_page']
            for edge in edges:
                if edge['node']['display_url']:
                    display_url = edge['node']['display_url']
                    #print(display_url)
                    urls.append(display_url)
            #print(cursor, flag)
    while flag and count > 0:
        print("----download next page")
        url = uri.format(user_id=user_id, cursor=cursor)
        js_data = get_json(url)
        infos = js_data['data']['user']['edge_owner_to_timeline_media']['edges']
        cursor = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
        flag = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
        for info in infos:
            if info['node']['is_video']:
                video_url = info['node']['video_url']
                if video_url:
                    #print(video_url)
                    urls.append(video_url)
            else:
                if info['node']['display_url']:
                    display_url = info['node']['display_url']
                    #print(display_url)
                    urls.append(display_url)
        count = count - 1
        time.sleep(60 + float(random.randint(200, 800))/200)
    return urls

def check_account(account):
    url = 'https://www.instagram.com/' + account + '/'

    html = get_html(url)
    if html == False:
        return False
    urls = get_urls(html)
    
    print('check finished',account.strip())
    return True

def crawler_account(account,num):
    if num <= 0:
        print('error number')
        return False
    url = 'https://www.instagram.com/' + account + '/'
    html = get_html(url)
    urls = get_full_urls(html,num)
    user_id = re.findall('\"profilePage_([0-9]+)\"', html, re.S)[0]
    dirpath = './' + account

    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    for i in range(len(urls)):
        try:
            content = get_content(urls[i])
            file_path = './' + account + '/' + md5(content).hexdigest() + urls[i][-43:-39]
            if(urls[i][-43:-39] == ".jpg"):
                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as f:
                        f.write(content)
                        f.close()
            else:
                print ("ignore download :",md5(content).hexdigest(), urls[i][-43:-39])
        except Exception as e:
            print(e)
            print('fail to download picture')
    print('finsish download',account.strip())


