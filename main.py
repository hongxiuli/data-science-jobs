import requests
import bs4
from bs4 import BeautifulSoup
import time
import csv

# if sys.setdefaultencoding() is not utf-8, set the encoding here
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')

def getPageContent(url):
    ''' Get HTML source for url
    
    :param url: url to parse 
    :return: response object
    :rtype: requests.Response
    '''
    response = requests.get(url)
    if(response.ok):
        response.decodedContent = response.content.decode('utf-8','ignore')
    return response

def getIndeedJobList(pageContent, exclude):
    ''' Get Indeed Job meta data, including id, title, company, and location
    
    :param pageContent: HTML source of the indeed job list page
    :param exclude: a list of job IDs to exclude (indeed puts sponsored jobs on the top of many different pages)
    :return: a list of job meta data
    :rtype: List
    '''
    jobList = []
    for div in pageContent.find_all("div", class_='result'):
        if(div['id'] in exclude):
            continue
        
        job = {}
        #get id
        job['id'] = div['id']
        exclude.add(div['id'])
        
        #get title
        title_tag = div.find('a', class_='turnstileLink')
        job['title'] = title_tag['title']
        
        #get company
        company_tag = div.find(class_='company')
        link=company_tag.find('a')
        if(link):
            job['company'] = link.text.strip()
        else:
            job['company'] = company_tag.text.strip()
        
        #get location
        location_tag = div.find(class_='location')
        job['location'] = location_tag.string
        jobList.append(job)
    
    return jobList

def getJobs(numPages):
    ''' driver function to get the indeed data scientist jobs
    
    :param numPages: scrape up to numPages 
    '''
    baseURL = 'https://www.indeed.ca/data-scientist-jobs'
    url = baseURL
    start = 0
    jobList = []
    exclude = set()
    while(True):
        # only process numPages
        if(numPages is not None and start >= numPages):
            break
        url = baseURL if start == 0 else baseURL + '?start='+str(start)
        print('Crawling ' + url)
        response = getPageContent(url)
        if(not response.ok):
            print('Problem get page content from %s, code: %d, reason: %s' % (url, response.status_code, response.reason))
            break
        pageContent = BeautifulSoup(response.decodedContent, 'html.parser', exclude_encodings=['gbk'])
        jobs = getIndeedJobList(pageContent, exclude)
        jobList.extend(jobs)
        pagination_tag = pageContent.find_all(class_='pn')
        last_tag = pagination_tag[-1]
        if(last_tag.find(class_='np')):
            #go to next page
            start+=20
            time.sleep(3)
        else:
            break
    #write result to csv file
    if(len(jobList)>0):
        csvHeaders = jobList[0].keys()
        filePath = 'jobs.csv'
        with open(filePath, 'w', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, csvHeaders)
            dict_writer.writeheader()
            dict_writer.writerows(jobList)
        print('%d result saved to %s' %(len(jobList), filePath))

#run the program
getJobs()