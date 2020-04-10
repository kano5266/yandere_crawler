# _*_coding:utf-8_*_

#original from https://zhuanlan.zhihu.com/p/80932642
import requests
import re
import queue
import threading
from bs4 import BeautifulSoup
import os
import time
import traceback
import sys
import urllib.parse

args = sys.argv #run [python yandere3.py 'tag']

image_save_path_base=None
# 目标网站
HOST = "https://yande.re"
# 当前目录设为根目录
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))# os.path.dirname(__file__)

# 请求头
headers = {
     "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
}

# 创建一个请求session
http = requests.Session()
http.headers.update(headers)

# 创建一个队列
q = queue.Queue()

#
init_q = queue.Queue()


def general_page_dir(page):
    """
    生成保存图片页面的目录
    :param page: 页数
    :return:
    """
    res = ""
    if 0 < page < 10:
        res = "000" + str(page)
    elif 10 <= page < 100:
        res = "00" + str(page)
    elif 100 <= page < 1000:
        res = "0" + str(page)
    elif page >= 1000:
        res = str(page)
    return res


def get_img_url(thread_id, min_score=2):
    """
    获取图片链接列表并下载
    :param min_score: 最低分数
    :param thread_id: 线程标示
    :return:
    """
    while not q.empty():

        data = q.get()
        dirname = data['dirname']
        urls = data['urls']
        print("正在爬取第{}页图片...".format(str(int(dirname))))
        count = 1
        try:
            for url in urls:
                time.sleep(1)
                print("线程ID:{}, 正在爬取第{}页, 第{}张图片...".format(thread_id, str(int(dirname)), str(count)))
                with http:
                    response = http.get(url).text
                soup = BeautifulSoup(response, "html.parser")
                img_info = soup.find("div", class_="vote-container")
                # 获取文件名
                img_id = re.findall(r"\d+", img_info.find_all("li")[0].string)[0]
                #file_name = img_id + ".jpg"
                # update_time = img_info.find_all("li")[1].a.string   # 更新时间,
                score = img_info.find_all("span", id="post-score-{}".format(img_id))[0].string  # 获取评分
                if int(score) < min_score:  # 如果评分低于指定评分则跳过该张图片
                    continue
                ##############
                img_url = soup.find("a", id="highres").attrs['href']
                file_name = urllib.parse.unquote(img_url)
                file_name = re.findall('/yande.re (.*?).jpg', file_name)[0] + '.jpg'
                ##############
                save_dir_path = image_save_path_base#os.path.join(ROOT_PATH, dirname)  # 待保存图片的文件夹完整路径
                if not os.path.exists(save_dir_path):
                    os.mkdir(save_dir_path)  # 不存在该文件夹则创建
                image_save_path = os.path.join(save_dir_path, file_name)
                # 保存图片
                download(img_url, image_save_path, thread_id)
                count += 1
                time.sleep(0.25)
        except Exception as e:
            print(traceback.format_exc())
            pass


def download(img_url, file_path, thread_id):
    """
    下载图片到指定路径
    :param img_url:
    :param file_path:
    :param dir_path:
    :return:
    """
    try:
        with http:
            content = http.get(img_url).content
        with open(file_path, "wb+") as f:
            f.write(content)
        print("线程ID:{}, 图片已保存至: {}".format(thread_id, file_path))
    except:
        pass


def init(st_page=1, end_page=10, tag="shintarou", thread_num=5, min_score=5):
    print("程序正在作初始化工作...")
    # 检查页面数合法性
    if st_page <= 1:
        st_page = 1
    if end_page > 1072:
        end_page = 1072
    ######
    init_page_url = HOST + "/post?page=1&tags=" + tag
    with http:
        response = http.get(init_page_url).text
        soup = BeautifulSoup(response, "html.parser")
        pagination = soup.find("div", class_="pagination")
        last_page = int(pagination.find_all("a")[-2].attrs['aria-label'].replace('Page ', ''))
    if last_page < end_page:
        end_page = last_page    
    ######

    for page in range(st_page, end_page+1):
        # 构造页面url链接
        page_url = HOST + "/post?page=" + str(page) + "&tags=" + tag
        init_q.put({"url": page_url, "page": page})

    for i in range(thread_num):
        t = threading.Thread(target=get_image_detail_url)
        t.start()


def get_image_detail_url():
    while not init_q.empty():
        data = init_q.get()
        response = http.get(data["url"]).text
        # 解析到图片详情页链接列表
        img_detail_url = re.findall('<a class="thumb" href="(.*?)" >', response)
        #print(img_detail_url)
        temp_list = []
        temp_dict = {}
        for url in img_detail_url:
            temp_list.append(HOST + url)  # 将完整的链接加到列表中
        temp_dict["urls"] = temp_list
        temp_dict["dirname"] = general_page_dir(data["page"])
        q.put(temp_dict)  # 入队
        del temp_list
        del temp_dict


def run(st_page=1, end_page=10, tag="dress", thread_num=5, min_score=5):
    """
    :param st_page:
    :param end_page:
    :param tag:
    :param thread_num:
    :param min_score:
    :return:
    """
    print("初始化完成, 开始爬取图片...")
    for t in range(thread_num):
        t = threading.Thread(target=get_img_url, args=(t, min_score))
        t.start()


if __name__ == '__main__':
    tag = args[1]
    image_save_path_base=ROOT_PATH+'/'+tag+'/'
    if not os.path.exists(image_save_path_base):
        os.mkdir(image_save_path_base)

    st_num = 1#int(input("请输入开始页数:[1-1071]:"))
    end_num = 150#int(input("请输入结束页数:[1-1072]:"))
    thread_number =5# int(input("请输入要使用的线程数量:"))
    min_score = 2#int(input("设置图片评分低于n时过滤该图片, 输入一个整数:"))
    init(tag=tag,st_page=st_num, end_page=end_num, min_score=min_score, thread_num=thread_number)
    time.sleep(10)
    run(st_page=st_num, end_page=end_num, min_score=min_score, thread_num=thread_number)
    print("程序正在运行...")
print("Finished")
