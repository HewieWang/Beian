#!/usr/bin/python3.7
# -*- coding: utf-8 -*-

import os
import re
import csv
import time
import requests
import tldextract
import winreg
from argparse import ArgumentParser

from colorama import init

init(autoreset=True)

from wcwidth import wcswidth as ww


def parseArgs():
    date = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    parser = ArgumentParser()
    parser.add_argument("-t", "--target", required=False, type=str, help=f"Target ip/domain")
    parser.add_argument("-f", "--file", dest="file", required=False, type=str, default="domain.txt", help=f"Target ip/domain file")
    parser.add_argument("-s", "--delay", dest="delay", required=False, type=int, default=3, help=f"Request delay (default 3s)")
    parser.add_argument("-T", "--Timeout", dest="timeout", required=False, type=int, default=3, help="Request timeout (default 3s)")
    parser.add_argument("-r", "--rank", required=False, type=int, default=0, help="Show baiduRank size (default 0)")
    parser.add_argument("-o", "--output", dest="output", required=False, type=str, default=f"{date}", help="output file (default ./output/ip2domain_{fileName}_{date}.csv)")
    parser.add_argument("--icp", required=False, action="store_true", default=True, help="With search icp (default false)")
    return parser

def searchDomain(ip, timeout):
    mainDomainNameList = []
    searchDomainResult = {"code": 0, "ip":ip, "domainList": []}

    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36"
    }
    try:
        rep = requests.get(url=f"http://api.webscan.cc/?action=query&ip={ip}", headers=headers, timeout=timeout)
        if rep.text != "null":
            results = rep.json()
            for result in results:
                domainName = result["domain"]
                if re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", domainName):
                    continue
                if domainName  in mainDomainNameList:
                    continue
                # 取主域
                val = tldextract.extract(domainName)
                if f"{val.domain}.{val.suffix}" not in mainDomainNameList:
                    mainDomainNameList.append(f"{val.domain}.{val.suffix}")
            searchDomainResult["code"] = 1
            searchDomainResult["domainList"] = mainDomainNameList
        else:
            searchDomainResult["code"] = 0
    except:
        searchDomainResult["code"] = -1

    return searchDomainResult

def searchRecord(domain, timeout):
    # By Vvhan
    header = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
    }
    resultDic = {"code":1, "domain":domain, "unitName": "", "unitType": "", "unitICP": "", "title": ""}
    try:
        rep = requests.get(url=f"https://api.vvhan.com/api/icp?url={domain}", headers=header, timeout=timeout)
        try:
            resultDic["unitName"] = rep.json()["info"]["name"]
        except:
            pass
        try:
            resultDic["unitType"] = rep.json()["info"]["nature"]
        except:
            pass
        try:
            resultDic["unitICP"] = rep.json()["info"]["icp"]
        except:
            pass
        try:
            resultDic["title"] = rep.json()["info"]["title"]
        except:
            pass
        return resultDic
    except:
        resultDic["code"] = -1
        return resultDic

def baiduRank(domain, timeout):
    """
    利用爱站接口查询权重信息
    """
    reqURL = f"https://www.aizhan.com/cha/{domain}/"
    headers = {
        "Host": "www.aizhan.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/61.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    baiduRankResult = {"code": 1, "rank": -1}
    try:
        rep = requests.get(url=reqURL, headers=headers, timeout=timeout)
    except:
        baiduRankResult["code"] = -1
        return baiduRankResult
    # 百度权重正则
    # baiduRankRegular = re.compile(r'/images/br/([0-9]+).png')
    baiduRankRegular = re.compile(r'aizhan.com/images/br/(.*?).png')
    try:
        baiduRankResult["rank"] = int(baiduRankRegular.findall(rep.text)[0])
        return baiduRankResult
    except:
        baiduRankResult["code"] = 0
        return baiduRankResult

def rpad(s, n, c=" "):
    return s + (n - ww(s)) * c


requests.packages.urllib3.disable_warnings()  # 抑制https错误信息



def init(parseClass):
    args = parseClass.parse_args()
    if not args.file and not args.target:
        print(parseClass.print_usage())
        exit(0)

    if args.file:
        if not os.path.isfile(args.file):
            print(
                f"\n[\033[36m{time.strftime('%H:%M:%S', time.localtime())}\033[0m] - \033[31m[ERRO] - Load file [{args.file}] Failed\033[0m")
            exit(0)

    targetList = loadTarget(args.file, args.target)  # 所有目标

    print(
        f"[\033[36m{time.strftime('%H:%M:%S', time.localtime())}\033[0m] - \033[36m[INFO] - Timeout:   {args.timeout}s\033[0m")
    print(
        f"[\033[36m{time.strftime('%H:%M:%S', time.localtime())}\033[0m] - \033[36m[INFO] - Delay:     {args.delay}s\033[0m")
    print(
        f"[\033[36m{time.strftime('%H:%M:%S', time.localtime())}\033[0m] - \033[36m[INFO] - Rank Size: >{args.rank}\033[0m")
    print(
        f"[\033[36m{time.strftime('%H:%M:%S', time.localtime())}\033[0m] - \033[36m[INFO] - ICP:       {args.icp}\033[0m")
    print(
        f"[\033[36m{time.strftime('%H:%M:%S', time.localtime())}\033[0m] - \033[36m[INFO] - ipCount:   {len(targetList)}\033[0m\n")

    return targetList


# 加载目标
def loadTarget(file, target):
    targetList = []

    # 解析输入目标数据
    def parseData(data):
        val = tldextract.extract(data)
        if not val.suffix:
            # 校验解析的数据
            if re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
                        val.domain):
                return f"{val.domain}"
            else:
                return ""
        else:
            return f"{val.domain}.{val.suffix}"

    if file:
        f = open(file, encoding="utf8")
        for line in f.readlines():
            target_ = parseData(line.strip())
            if target_:
                targetList.append(target_)
        f.close()

    if target:
        target_ = parseData(target.strip())
        if target_:
            targetList.append(target_)

    return list(set(targetList))

def desktop_path():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
    path = winreg.QueryValueEx(key, "Desktop")[0]
    return path

def outputResult(argsFile, argsOutput, resultList, icp):
    outputFile = desktop_path()+"/批量备案查询结果.csv"
    # if not os.path.isdir(r"./output"):
    #     os.mkdir(r"./output")
    with open(outputFile, "a", encoding="gbk", newline="") as f:
        csvWrite = csv.writer(f)
        if icp:
            csvWrite.writerow(["ip", "反查域名", "百度权重", "单位名称", "单位性质", "备案编号", "网站标题"])
        else:
            csvWrite.writerow(["ip", "反查域名", "百度权重"])
        for result in resultList:
            csvWrite.writerow(result)


def ip2domian(target, args, targetNum, targetCount):
    resultList = []
    if re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", target):
        searchDomainResult = searchDomain(target, args.timeout)
        time.sleep(args.delay)
        domainList = searchDomainResult["domainList"]
    else:
        domainList = [target]

    for domain in domainList:
        baiduRankResult = baiduRank(domain=domain, timeout=args.timeout)
        time.sleep(args.delay)
        if baiduRankResult["code"] == 1:
            if baiduRankResult["rank"] >= args.rank:
                resultList.append([target, domain, baiduRankResult["rank"]])
        elif baiduRankResult["code"] == -1:
            resultList.append([target, domain, "ConnError"])
        else: # 0 PageError
            resultList.append([target, domain, "PageError"])

    if args.icp:
        for result in resultList:
            icpResult = searchRecord(domain=result[1], timeout=args.timeout)
            time.sleep(args.delay)
            if icpResult["code"] == 1:
                result += [icpResult["unitName"], icpResult["unitType"], icpResult["unitICP"]]

    if len(resultList) == 0:
        print(f"\r({targetNum}/{targetCount})", end="", flush=True)

    return resultList


def printTitle(icp):
    if icp:
        msg = f"+{'-' * 17}+{'-' * 20}+{'-' * 10}+{'-' * 37}+{'-' * 10}+{'-' * 22}+\n"
        msg += f"|{rpad('ip/domain', 17)}|{rpad('反查域名', 20)}|{rpad('百度权重', 10)}|{rpad('单位名称', 37)}|{rpad('单位性质', 10)}|{rpad('备案编号', 22)}|\n"
        msg += f"+{'-' * 17}+{'-' * 20}+{'-' * 10}+{'-' * 37}+{'-' * 10}+{'-' * 22}+"
    else:
        msg = f"+{'-' * 17}+{'-' * 20}+{'-' * 10}+\n"
        msg += f"|{rpad('ip/domain', 17)}|{rpad('反查域名', 20)}|{rpad('百度权重', 10)}|\n"
        msg += f"+{'-' * 17}+{'-' * 20}+{'-' * 10}+"
    print(msg)


def printMsg(result, icp):
    rankColor = {
        0: "\033[37m",
        1: "\033[33m",
        2: "\033[32m",
        3: "\033[32m",
        4: "\033[34m",
        5: "\033[35m",
        6: "\033[36m",
        7: "\033[31m",
        8: "\033[31m",
        9: "\033[31m",
        10: "\033[31m",
        "ConnError": "\033[31m",
        "PageError": "\033[31m",
    }

    if icp:
        try:
            print(
                f"\r|{rpad(result[0], 17)}|{rpad(result[1], 20)}|{rankColor[result[2]]}{rpad('    ' + str(result[2]), 10)}\033[0m|{rpad(result[3], 37)}|{rpad(result[4], 10)}|{rpad(result[5], 22)}|")
            print(f"+{'-' * 17}+{'-' * 20}+{'-' * 10}+{'-' * 37}+{'-' * 10}+{'-' * 22}+")
        except Exception as e:
            pass  
    else:
        print(
                f"\r|{rpad(result[0], 17)}|{rpad(result[1], 20)}|{rankColor[result[2]]}{rpad('    ' + str(result[2]), 10)}\033[0m|")
        print(f"+{'-' * 17}+{'-' * 20}+{'-' * 10}+")



    # if icp:
    #     print(
    #         f"\r|{rpad(result[0], 17)}|{rpad(result[1], 20)}|{rankColor[result[2]]}{rpad('    ' + str(result[2]), 10)}\033[0m|{rpad(result[3], 37)}|{rpad(result[4], 10)}|{rpad(result[5], 22)}|")
    #     print(f"+{'-' * 17}+{'-' * 20}+{'-' * 10}+{'-' * 37}+{'-' * 10}+{'-' * 22}+")
    # else:
    #     print(
    #         f"\r|{rpad(result[0], 17)}|{rpad(result[1], 20)}|{rankColor[result[2]]}{rpad('    ' + str(result[2]), 10)}\033[0m|")
    #     print(f"+{'-' * 17}+{'-' * 20}+{'-' * 10}+")


if __name__ == "__main__":
    parseClass = parseArgs()
    args = parseClass.parse_args()
    targetList = init(parseClass)
    resultList = []
    printTitle(args.icp)
    targetCount = len(targetList)
    try:
        for i in range(len(targetList)):
            resultTmpList = []
            resultTmpList += ip2domian(targetList[i], args, targetNum=i+1, targetCount=targetCount)
            resultList += resultTmpList
            for i in resultTmpList:
                printMsg(i, args.icp)
        outputResult(args.file, args.output, resultList, args.icp)
    except KeyboardInterrupt:
        print("\nBye~")