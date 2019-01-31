
from riotwatcher import RiotWatcher
import json
import os
import sys
import time
import requests
from requests import HTTPError
import gc
import tracemalloc


sys.setrecursionlimit(100000)

patchMillSecs = 1548316800000 #game version 9.2
path = 'F:/lolMatchData/data/matches/'

count = 0

matchIDsDownloaded = []
matchIDsDownloading = []
summonerIDsDownloaded = []
summonerIDsDownloading = []

watcher = RiotWatcher('RGAPI-9c8430c4-2276-4466-80f5-1b59c48cd0a7')



#将match中的summonerId判断后，放入指定缓存容器
def appendSummonerId(match):
    SummonerIdInThisMatch = []
    playerNum = len(match['participantIdentities'])
    for i in range(0,playerNum):
        SummonerIdInThisMatch.append(match['participantIdentities'][i]['player']['accountId'])
    for SummonerId in SummonerIdInThisMatch:
        if SummonerId not in summonerIDsDownloaded and SummonerId not in summonerIDsDownloading:
            summonerIDsDownloading.append(SummonerId)
    return

#将matchlist中的matchId判断后，放入指定缓存容器
def appendMatchId(matchlist):
    MatchIdInThisMatch = []
    matchCount = len(matchlist['matches'])
    for i in range(0,matchCount):
        matchId = matchlist['matches'][i]['gameId']
        if matchId not in matchIDsDownloaded and matchId not in matchIDsDownloading:
            matchIDsDownloading.append(matchId)
    return

def MatchCrawler():
    for i in range(1):
        matchId = matchIDsDownloading[0]
        #下载match
        try:
            print('match '+str(matchId)+' is downloading now')
            match = watcher.match.by_id('kr',matchId)
        except HTTPError as err:
            if err.response.status_code == 429:                
                print('429. We should retry in X seconds.')
                time.sleep(5)
                crawlerIndicator()
            elif err.response.status_code == 404:
                print('404. No data found for match '+str(matchId))
                continue
            else:
                print(err.response.status_code)
                continue
        except requests.exceptions.SSLError as err:
            print('ConnectionError')
            time.sleep(5)
            crawlerIndicator()
        
        #将match转为json并存放至本地
        with open(path+'match'+str(matchId)+'.txt','w') as m:
            m.write(json.dumps(match))

        #下载timeline
        try:
            print('timeline '+str(matchId)+' is downloading now')
            timeline = watcher.match.timeline_by_match('kr',matchId)
        except HTTPError as err:
            if err.response.status_code == 429:                
                print('429. We should retry in X seconds.')
                time.sleep(5)
                crawlerIndicator()
            elif err.response.status_code == 404:
                print('404. No data found for timeline '+str(matchId))
                continue
            else:
                print(err.response.status_code)
                continue
        except requests.exceptions.SSLError as err:
            print('ConnectionError')
            time.sleep(5)
            crawlerIndicator()

        #将timeline转为json并存放至本地
        
        with open(path+'timeline'+str(matchId)+'.txt','w') as m:
            m.write(json.dumps(timeline))

        if len(summonerIDsDownloading)<1000:
            appendSummonerId(match)
        matchIDsDownloading.remove(matchId)
        matchIDsDownloaded.append(matchId)
        crawlerIndicator()
    return

def MatchListCrawler():
    for summonerId in summonerIDsDownloading:

        try:
            matchList = watcher.match.matchlist_by_account('kr',summonerId,420,begin_time=1548316800000)
        except HTTPError as err:
            if err.response.status_code == 429:                
                print('429. We should retry in X seconds.')
                time.sleep(5)
                crawlerIndicator()
            elif err.response.status_code == 404:
                print('404. No data found for summoner '+str(summonerId))
                summonerIDsDownloading.remove(summonerId)
                summonerIDsDownloaded.append(summonerId)
                crawlerIndicator()
            else:
                print(err.response.status_code)
                continue
        except requests.exceptions.SSLError as err:
            print('ConnectionError')
            time.sleep(5)
            crawlerIndicator()

        appendMatchId(matchList)
        summonerIDsDownloading.remove(summonerId)
        summonerIDsDownloaded.append(summonerId)
        crawlerIndicator()
    return

#判断应该进行哪种爬取的入口函数
def crawlerIndicator():
    global count
    count +=1
    print(count)

    if count % 15 == 0:
        CollectionSynchronize(1)
        
    if len(matchIDsDownloading)>0:
        MatchCrawler()
    elif len(summonerIDsDownloading)>0:
        MatchListCrawler()
    else :
        print('Error, no matchID or summonerId available. Check collection file please')
    return

#保持硬盘上容器和缓存中容器实时同步
def CollectionSynchronize(type):
    if type == 0:
         with open('F:\lolMatchData\data\matchIDsDownloaded.txt','r') as m:
             for line in m.readlines():
                 matchIDsDownloaded.append(line.strip())
         with open('F:\lolMatchData\data\matchIDsDownloading.txt','r') as m:
             for line in m.readlines():
                 matchIDsDownloading.append(line.strip())
         with open('F:\lolMatchData\data\summonerIDsDownloaded.txt','r') as m:
             for line in m.readlines():
                 summonerIDsDownloaded.append(line.strip())
         with open('F:\lolMatchData\data\summonerIDsDownloading.txt','r') as m:
             for line in m.readlines():
                 summonerIDsDownloading.append(line.strip())
             print(summonerIDsDownloading)
    else:
         saveNumberList(matchIDsDownloaded,'matchIDsDownloaded.txt')
         saveNumberList(matchIDsDownloading,'matchIDsDownloading.txt')
         saveNumberList(summonerIDsDownloaded,'summonerIDsDownloaded.txt')
         saveNumberList(summonerIDsDownloading,'summonerIDsDownloading.txt')
    return

def saveNumberList(list,fileName):
    strList = []
    with open('F:\lolMatchData\data\\'+fileName,'w') as m:
        for id in list:
            strList.append((str(id) + '\n'))
        m.writelines(strList)
    return


#测试API是否正常运作的函数，包含示例ID
def apiTest(watcher):
    match = watcher.match.by_id('kr',3421636538)
    print('Good! match API runs successfully with player one of this match called: ' + match['participantIdentities'][0]['player']['summonerName'])
    matchlist = watcher.match.matchlist_by_account('kr',202784392)    
    print('Good! matchlist API runs successfully with matches count at: '+str(len(matchlist['matches'])))
    return

#apiTest(watcher)
CollectionSynchronize(0)
crawlerIndicator()
