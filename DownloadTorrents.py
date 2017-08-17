#! python3
""" This program will automatically download torrents from http://linkomanija.net site.
    List of videos that to search for will be held in seperate file
    Program will check if new video is available and will provide the list to select which to download
"""

from multiprocessing import Queue
import logging, os, requests, bs4, re, json, shelve, sys, datetime, getpass

open('..\\debug_log.txt','w').close()
logging.basicConfig(level=logging.DEBUG, filename='..\\debug_log.txt', format='%(asctime)s - %(levelname)s - %(message)s')
#logging.disable(logging.DEBUG)


# DONE: have a file that has what torrent to look for. Open the file and create list. return list of items
def getNamesFromFile(fileName):
    try:
        searchFile = open(fileName, 'r')
        templist = searchFile.read().splitlines()
        searchFile.close()
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - INFO - \"%s\" opened and read successfully. List is the following: %s\n' % (
                      fileName, templist))
        return templist
    except Exception as err:
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - ERROR - Problems opening \"%s\". Error message: %s\n' % (fileName, err))
        sys.exit(err)


# DONE: loging to http://linkomanija.net. encrypt password. return logged in session
def login(httpAddress, session):
    # password = base64.b64encode('false1345'.encode('utf-8'))
    # print(password)
    credentials = {
        'username': 'dalienc',
        'password': getpass.getpass('Enter password:')
    }
    try:
        session.post(httpAddress, data=credentials).raise_for_status()
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - INFO - login to %s successful.\n' % (httpAddress))
        return session
    except Exception as err:
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - ERROR - login to %s unsuccessful. Error message: %s\n' % (httpAddress,err))
        sys.exit(err)


# DONE: search for torrents as per item name.
# DONE: itterate for each page of search results. return dictionary with all restuls
def searchForItems(session, item):
    try:
        htmlPage = session.get('https://www.linkomanija.net/browse.php?incldead=0&search=' + item)
        htmlPage.raise_for_status()
        soup = bs4.BeautifulSoup(htmlPage.text, 'html.parser')
        finalHtmlPage = htmlPage.text
        while soup.find_all('a', class_='pagelink', string=re.compile(r'Kitas')):
            htmlPage = session.get(
                'https://www.linkomanija.net/' + soup.find('a', class_='pagelink', string=re.compile(r'Kitas'))[
                    'href'])
            htmlPage.raise_for_status()
            soup = bs4.BeautifulSoup(htmlPage.text, 'html.parser')
            finalHtmlPage = finalHtmlPage + htmlPage.text
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - INFO - Complete HTML source code generated for item \"%s\". Parsing initiating.\n' % (
                          item))
        return parseHtml(finalHtmlPage, item)
    except Exception as err:
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - ERROR - failure while searching for \"%s\". HTML code file generated as html_out.txt. Error message: %s\n' % (
                      item, err))
        out = open('..\\html_out.txt','w', encoding="utf-8")
        out.write(finalHtmlPage)
        out.close()
        sys.exit(err)


# DONE: Iterate find_next_sibling function. return tag
def findNextSibling(tag, times):
    for i in range(times):
        tag = tag.find_next_sibling()
    return tag


# DONE: parse page and get all search results. store them in dictionary. return disctionary with all result items
def parseHtml(htmlString, item):
    try:
        logFile.write(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + ' - INFO - HTML code parsing started.\n')
        soupObject = bs4.BeautifulSoup(htmlString, 'html.parser')
        findResults = soupObject.find_all('a', style='display:none;')
        finalResults = []
        for item in findResults:
            finalResults.append(item.find_parents('tr')[0])
        resDic = {}
        for i in range(len(finalResults)):
            try:
                downloadLink = str(findNextSibling(findNextSibling(finalResults[i].td, 1).a, 1)['href'])
            except:
                downloadLink = str(findNextSibling(findNextSibling(finalResults[i].td, 1).a, 2)['href'])
            newElement = {str(findNextSibling(findNextSibling(finalResults[i].td, 1).a, 1)['href']): {
                'type': str(finalResults[i].td.a.img['title']),
                'name': str(findNextSibling(finalResults[i].td, 1).a.b.string),
                'added': str(list(findNextSibling(finalResults[i].td, 4).nobr)[0]),
                'size': str(list(findNextSibling(finalResults[i].td, 5))[0] + ' ' +
                            list(findNextSibling(finalResults[i].td, 5))[2]),
                'timesDownloaded': str(findNextSibling(finalResults[i].td, 6).string),
                'linkToDownload': 'https://www.linkomanija.net/' + downloadLink
            }}
            resDic.update(newElement)
        logFile.write(
            datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + ' - INFO - HTML code parsed successfully.\n')
        return resDic
    except Exception as err:
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - ERROR - failure while parsing HTML code. HTML code and additional info dumped to file \"html_out.txt\". Error message: %s\n' % (
                      err))
        out = open('..\\html_out.txt', 'a', encoding="utf-8")
        out.write(htmlString)
        out.write('\n----------------------------elements in findResults (<a> tags)--------------------------------')
        for elem in findResults:
            out.write('\n\n'+str(elem))
        out.write('\n\n-----------------------elements in findResults (parent <tr> tags)---------------------------')
        for elem in finalResults:
            out.write('\n\n'+str(elem))
        out.write('\n\n-------------------------------------------------------------------------------------------\n\n')
        out.write(str(finalResults[i])+'\n\n')
        out.write(str(finalResults[i].td) + '\n\n')
        out.write(str(findNextSibling(finalResults[i].td, 1)) + '\n\n')
        out.write(str(findNextSibling(finalResults[i].td, 1).a) + '\n\n')
        out.write(str(findNextSibling(findNextSibling(finalResults[i].td, 1).a, 1)) + '\n\n')
        out.write(str(findNextSibling(findNextSibling(finalResults[i].td, 1).a, 1)['href']) + '\n\n')
        out.write('\n\n-------------------------------------------------------------------------------------------\n\n')
        out.write(json.dumps(resDic, indent=2))
        out.close()
        sys.exit(err)


# DONE: store All results in shelve file on disk
def saveToFileAll(localDic, item):
    shelveFile = shelve.open('..\\data\\results')
    shelveFile[item] = localDic
    print('Updated local store with all found elements for \"%s\". Total in store: %s' % (item, len(shelveFile[item])))
    shelveFile.close()
    return True


# DONE: add new iteams in shelve file on disk
def saveToFileNew(newElement, item):
    try:
        shelveFile = shelve.open('..\\data\\results')
        tempDic = shelveFile[item]
        tempDic.update(newElement)
        shelveFile[item] = tempDic
        print('Added \"%s\" to local store' % newElement[list(newElement.keys())[0]]['name'])
        shelveFile.close()
        logFile.write(
            datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + ' - INFO - Added \"%s\" to local store\n' %
            newElement[list(newElement.keys())[0]]['name'])
        return True
    except Exception as err:
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - ERROR - failure while adding element \"%s\" to local store. Error message: %s\n' % (
                      newElement[list(newElement.keys())[0]]['name'], err))
        sys.exit(err)


# DONE: delete All from results file. ad-hoc use
def deleteFromFileAll():
    try:
        shelveFile = shelve.open('..\\data\\results')
        for item in shelveFile:
            del shelveFile[item]
        print('Local store fully cleaned.')
        shelveFile.close()
        logFile.write(
            datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + ' - INFO - Local store fully cleaned.\n')
    except Exception as err:
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - ERROR - failure while deleting all items from local store. Error message: %s\n' % (
                          err))
        sys.exit(err)


# DONE: delete single item from results file. ad-hoc use
def deleteFromFileSingle():
    try:
        shelveFile = shelve.open('..\\data\\results')
        indexList = shelveFile['itemIndex']
        print('which one to delete? \n %s' % indexList)
        item = input()
        try:
            indexList.remove(item)
            shelveFile['itemIndex'] = indexList
            del shelveFile[item]
        except:
            print('such item does not exist: %s \n Terminating...' % item)
            logFile.write(
                datetime.datetime.now().strftime(
                    '%Y/%m/%d %H:%M:%S') + ' - INFO - such item does not exist: %s \n Terminating...\n' % item)
            sys.exit()
        print('\"%s\" deleted from local store.' % item)
        shelveFile.close()
        logFile.write(
            datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + ' - INFO - \"%s\" deleted from local store.\n' % item)
    except Exception as err:
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - ERROR - failure while deleting \"%s\" item from local store. Error message: %s\n' % (
                          item, err))
        sys.exit(err)


# DONE: check if key exists in shelve file. if new add all to store and inform user
def checkIfNewSearchItem(item):
    try:
        shelveFile = shelve.open('..\\data\\results')
        if 'itemIndex' not in list(shelveFile.keys()):
            print('Local store index updated with new entry for \"%s\".' % item)
            indexList = [item]
            shelveFile['itemIndex'] = indexList
            shelveFile[item] = {}
            shelveFile.close()
            logFile.write(
                datetime.datetime.now().strftime(
                    '%Y/%m/%d %H:%M:%S') + ' - INFO - local store itemIndex created and element \"%s\" added to local store.\n' % item)
            return True
        else:
            indexList = shelveFile['itemIndex']
        if item not in indexList:
            indexList.append(item)
            print('Local store index updated with new entry for \"%s\".' % item)
            shelveFile['itemIndex'] = indexList
            shelveFile[item] = {}
            shelveFile.close()
            logFile.write(
                datetime.datetime.now().strftime(
                    '%Y/%m/%d %H:%M:%S') + ' - INFO - local store itemIndex updated and new element \"%s\" added to local store.\n' % item)
            return True
        else:
            shelveFile.close()
            logFile.write(
                datetime.datetime.now().strftime(
                    '%Y/%m/%d %H:%M:%S') + ' - INFO - item \"%s\" present in local store itemIndex.\n' % item)
            return False
    except Exception as err:
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - ERROR - failure while updating local store index or adding new element (%s) to local store. Error message: %s\n' % (
                          item, err))
        sys.exit(err)


# DONE: print new entries to screen and ask which to download or none to download
def printToScreenNew(localDic, localkey):
    newItemsKeys = getNewOnly(localDic, localkey)
    for item in newItemsKeys:
        print('\t ', newItemsKeys.index(item) + 1, localDic[item]['name'])
        print('\t\t', 'Type: ', localDic[item]['type'],
              '\n\t\t', 'Date Added: ', localDic[item]['added'],
              '\n\t\t', 'Size: ', localDic[item]['size'],
              '\n\t\t', 'Times Downloaded: ', localDic[item]['timesDownloaded'])
    return newItemsKeys


# DONE: compare results with local database to identify new entries only
def getNewOnly(localDic, key):
    try:
        shelveFile = shelve.open('..\\data\\results')
        returnNewItemList = []
        if shelveFile[key] == localDic:
            shelveFile.close()
            print('No new torrents found for \"%s\"' % key)
            logFile.write(
                datetime.datetime.now().strftime(
                    '%Y/%m/%d %H:%M:%S') + ' - INFO - No new torrents found for \"%s\".\n' % key)
            return returnNewItemList
        else:
            for item in localDic:
                if item in shelveFile[key].keys():
                    continue
                returnNewItemList.append(item)
            shelveFile.close()
            if returnNewItemList:
                print('\tNew items found (%s):' % len(returnNewItemList))
                logFile.write(
                    datetime.datetime.now().strftime(
                        '%Y/%m/%d %H:%M:%S') + ' - INFO - New torrents found for \"%s\". List is: %s\n' % (key,returnNewItemList))
            else:
                print('No new torrents found for \"%s\"' % key)
                logFile.write(
                    datetime.datetime.now().strftime(
                        '%Y/%m/%d %H:%M:%S') + ' - INFO - No new torrents found for \"%s\".\n' % key)
            return returnNewItemList
    except Exception as err:
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - ERROR - failure while comparing \"%s\" results with local store elements to local store. Error message: %s\n' % (
                          key, err))
        sys.exit(err)


# DONE: read input line which torrents to download and check if input is valid. return valid item list
def selectWhichToDownload(maxItemNumber):
    inputString = input('\nWhich torrent do you want to download? \
(type item numbers seperated with comma. 0 - for none. ALL - to download all) \ni.e. 1,5,7\nEnter Choise: ')
    itemsList = inputString.replace(' ', '').split(',')
    itemsList = list(set(itemsList))
    if '' in itemsList:
        itemsList.remove('')
    if itemsList in [['ALL'], ['ALl'], ['All'], ['aLL'], ['aLl'], ['all'], ['alL'], ['0']] or itemsList == []:
        return itemsList
    for item in itemsList:
        try:
            if int(item) > maxItemNumber:
                raise ValueError
        except ValueError as err:
            print('\"%s\" is not a valid choise. Try again.' % item)
            return 'repeat'
    return itemsList


# DONE: download selected torrents
def downloadTorrents(session, torrent):
    print('Downloading \"%s\"' % torrent['name'])
    try:
        content = session.get(torrent['linkToDownload'])
        content.raise_for_status()
        re.sub(r'[\\/*?:"<>|]', '', torrent['name'])
        filename = '..\\auto_downloaded_torrents\\' + re.sub(r'[\\/*?:"<>|]', '', torrent['name']) + '.torrent'
        file = open(filename, 'wb')
        for chunk in content.iter_content(10000):
            file.write(chunk)
        file.close()
        logFile.write(
            datetime.datetime.now().strftime(
                '%Y/%m/%d %H:%M:%S') + ' - INFO - download completed for \"%s\".\n' % torrent)
    except Exception as err:
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - ERROR - failure while downloading \"%s\".Additional info written to file error_log.txt. Error message: %s\n' % (torrent, err))
        out = open('..\\error_log.txt','w')
        out.write('-----------------------------Element info:-------------------------------\n\n')
        out.write(json.dumps(torrent, indent=2))
        out.write('\n\n-----------------------------Filename info:-------------------------------\n\n')
        out.write(filename)
        out.close()
        sys.exit(err)
    try:
        os.startfile(filename)
        logFile.write(
            datetime.datetime.now().strftime(
                '%Y/%m/%d %H:%M:%S') + ' - INFO - starting bittorent for \"%s\".\n' % filename)
        return True
    except Exception as err:
        print('Failed to open file %s' % filename)
        logFile.write(datetime.datetime.now().strftime(
            '%Y/%m/%d %H:%M:%S') + ' - ERROR - failure while opening file \"%s\". Error message: %s\n' % (filename, err))
        sys.exit(err)


# DONE: print local store content
def checkShelveFileContent():
    print('------------------------PRINTING SHELVE FILE CONTENT:------------------------')
    shelveFile = shelve.open('..\\data\\results')
    for item in list(shelveFile.keys()):
        print(json.dumps(shelveFile[item], indent=2), '\n')


""" MAIN PROGRAM STARTS HERE"""
global logFile
open('..\\log_file.txt','w').close()
open('..\\html_out.txt', 'w').close()
open('..\\error_log.txt', 'w').close()
logFile = open('..\\log_file.txt','a')
if len(sys.argv) > 1:
    if sys.argv[1].lower() == 'delete_all':
        deleteFromFileAll()
    elif sys.argv[1].lower() == 'print_local_store':
        checkShelveFileContent()
    elif sys.argv[1].lower() == 'delete':
        deleteFromFileSingle()
    else:
        print('\nWrong option \"%s\". \nAcceptable command line options are: \n delete_all - fully clean up local store\
\n delete - delete single item \n print_local_store - print all contents of local store' %sys.argv[1])
else:
    url = 'https://www.linkomanija.net/takelogin.php'
    searchList = getNamesFromFile('..\\search_list.txt')
    with requests.Session() as userSession:
        userSession = login(url, userSession)
        # running code against every item in the search list
        for searchItem in searchList:
            logFile.write('------------------------------------ %s ------------------------------------\n' %searchItem)
            resultDictionary = searchForItems(userSession, searchItem)
            print('RESULTS FOR ITEM \"%s\" (total on page: %s):' % (searchItem, len(resultDictionary)))
            checkIfNewSearchItem(searchItem)
            newTorrents = printToScreenNew(resultDictionary, searchItem)
            if newTorrents:
               # ask what to download and check if choises are valid
                itemsToDownload = selectWhichToDownload(len(newTorrents))
                while itemsToDownload == 'repeat':
                    itemsToDownload = selectWhichToDownload(len(newTorrents))

                # save selected torrents to disk
                if itemsToDownload == ['0'] or itemsToDownload == []:
                    print('0 torrent files downloaded')
                elif itemsToDownload in [['ALL'], ['ALl'], ['All'], ['aLL'], ['aLl'], ['all'], ['alL']]:
                    for item in newTorrents:
                        downloadTorrents(userSession, resultDictionary[item])
                else:
                    for item in itemsToDownload:
                        downloadTorrents(userSession, resultDictionary[newTorrents[int(item) - 1]])

                # ask if add new search results to local store
                storeNewItemsYesNo = 'none'
                while storeNewItemsYesNo not in ['Yes', 'yes', 'No', 'no', 'y', 'n', '']:
                    storeNewItemsYesNo = input('\nSave new torrent to local store? (Yes / No): ')
                if storeNewItemsYesNo in ['Yes', 'yes', 'y']:
                    for newItem in newTorrents:
                        saveToFileNew({newItem: resultDictionary[newItem]}, searchItem)
                else:
                    print('\nNew items not added to local store')
            print('\n-----------------------------------------------------------------------------------------\n')
logFile.close()
print('All tasks completed successfully! :):):)')
os.system('pause')