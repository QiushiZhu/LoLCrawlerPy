
from riotwatcher import RiotWatcher
import json
import os
import sys
import time
import requests
from requests import HTTPError
import gc
import tracemalloc

import logging
logging.basicConfig(filename='example.log',level=logging.DEBUG)

sys.setrecursionlimit(100000)

patchMillSecs = 1549440000000 #game version data @https://github.com/CommunityDragon/Data/blob/master/patches.json
path = 'F:/lolMatchData/data/matches/'

count = 0

matchIDsDownloaded = []
matchIDsDownloading = []
summonerIDsDownloaded = []
summonerIDsDownloading = []

watcher = RiotWatcher('RGAPI-440e0fae-6d34-4f84-9f16-d99fe51c30a4')



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
    matchId = matchIDsDownloading[0]    
    match = matchCrawler2(matchId)
        #将match转为json并存放至本地
    with open(path+'match'+str(matchId)+'.txt','w') as m:
        m.write(json.dumps(match))
     
    timeline = timelineCrawler(matchId)
    with open(path+'timeline'+str(matchId)+'.txt','w') as m:
        m.write(json.dumps(timeline))


    if len(summonerIDsDownloading)<1000:
        appendSummonerId(match)
    matchIDsDownloading.remove(matchId)
    matchIDsDownloaded.append(matchId)
    return

def matchCrawler2(matchId):
    for i in range(5):
        #下载match
        try:
            logging.debug('match downloading...')
            print('match '+str(matchId)+' is downloading now')
            match = watcher.match.by_id('kr',matchId)
            logging.debug('match downloaded...')
            print('match '+str(matchId)+' is downloaded now')
            return match
        except HTTPError as err:
            if err.response.status_code == 429:                
                print('429. We should retry in X seconds.')
                time.sleep(5)
            elif err.response.status_code == 404:
                print('404. No data found for match '+str(matchId))
                match = -1
                return match
            else:
                print(err.response.status_code)
        except :
            print('ConnectionError')
            logging.debug('ConnectionError...')
            time.sleep(30)
    return 

def timelineCrawler(matchId):
    for i in range(5):
        try:
            logging.debug('timeline downloading...')
            print('timeline '+str(matchId)+' is downloading now')
            timeline = watcher.match.timeline_by_match('kr',matchId)            
            logging.debug('timeline downloaded...')
            print('timeline '+str(matchId)+' is downloaded now')
            return timeline
        except HTTPError as err:
            if err.response.status_code == 429:                
                print('429. We should retry in X seconds.')
                time.sleep(5)
            elif err.response.status_code == 404:
                print('404. No data found for timeline '+str(matchId))
                timeline = -1
                return timeline
            else:
                print(err.response.status_code)
                time.sleep(5)
        except:
            print('ConnectionError')
            logging.debug('ConnectionError...')
            time.sleep(30)        
    return


def MatchListCrawler():
    summonerId = summonerIDsDownloading[0]
    for i in range(1):

        try:
            logging.debug('matchlist downloading...')
            print('matchlist '+str(summonerId)+' is downloading now')
            matchList = watcher.match.matchlist_by_account('kr',summonerId,420,begin_time=1548316800000)
            logging.debug('matchlist downloaded...')
        except HTTPError as err:
            if err.response.status_code == 429:                
                print('429. We should retry in X seconds.')
                time.sleep(5)
            elif err.response.status_code == 404:
                print('404. No data found for summoner '+str(summonerId))
                summonerIDsDownloading.remove(summonerId)
                summonerIDsDownloaded.append(summonerId)
            else:
                print(err.response.status_code)
                time.sleep(5)
        except :
            print('ConnectionError')
            time.sleep(30)
            crawlerIndicator()
        else:
            appendMatchId(matchList)
            del matchList
            summonerIDsDownloading.remove(summonerId)
            summonerIDsDownloaded.append(summonerId)
    return

#判断应该进行哪种爬取的入口函数
def crawlerIndicator():
    logging.debug('Choose which kind of file to download')
    global count
    count +=1
    print('Indica: '+str(count))

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
    logging.debug('Synchronizing...')
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
    matchlist = watcher.match.matchlist_by_account('kr','KkK8wy0p7zq_mtpcr-odeoTwCWnafhX64X8YYBpKrvMv_EZgicPLkA_K')    
    print('Good! matchlist API runs successfully with matches count at: '+str(len(matchlist['matches'])))
    return

#apiTest(watcher)
CollectionSynchronize(0)
for i in range(100000):
    print('h:'+str(i))
    crawlerIndicator()
