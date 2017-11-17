from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By as BY
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup as bs
import re
import csv
import time
import numpy as np

#postcodes = ['LS26 0UH']#, 'HD3 4AX', 'S17 4PU', 'LS2 7UA', 'SW1A 1AA']
output_path = 'C:/Users/James Crosbie/Desktop/'
delay = 10


def init_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    driver = webdriver.Chrome(executable_path='C:/Users/James Crosbie/Documents/Projects/webScraping/gekoDrivers/chromedriver.exe', chrome_options=chrome_options)
    driver.wait = WebDriverWait(driver, delay)
    return driver


def lookup(driver, query) :
    driver.get('http://cti.voa.gov.uk/cti/inits.asp')
    WebDriverWait(driver, delay).until(EC.presence_of_element_located((BY.ID, 'txtPostCode')))
    try:
        box = driver.find_element_by_xpath("//input[@id='txtPostCode' and @name='txtPostCode']")
        box.send_keys(query)

        button = driver.find_element_by_xpath("//span[@class='access' and contains(text(), 'your Council Tax band')]")
        button.submit()
    except TimeoutException:
        print("Box or Button not found")


def write_response_file(myLists):
    global counter
    myString = ''
    if counter == 1:
        myString = "Address\tCTBand\tImprovIndex\tRef\n"

    for i, j, k, l in zip(myLists[0], myLists[1], myLists[2], myLists[3]):
        myString = myString + str(i) + '\t' + str(j) + '\t' + str(k) +'\t' + str(l) + '\n'

    with open(output_path+"addressCTBands2.csv", "a") as text_file:
        text_file.write(myString)
    counter += 1
    return


def readfile():
    with open('C:/Users/James Crosbie/Desktop/allpostcodes2.txt', 'r') as f:
        reader = csv.reader(f)
        your_list = list(reader)
    return your_list[0]


def stripRegEx(myList):
    newList = []
    for i in myList:
        newList.append(re.sub('\n', '', i))
    return newList


def parsePage(soup):
    #parse results
    addressList = [str(address.string).strip() for address in soup.find_all('span', {'class': 'Custom'})][1:]
    tagList = [ct for ct in soup.find_all('td')]
    ctBandList  = [str(v.string).replace(" ", "") for i, v in enumerate(tagList) if i in range(1, 100, 4)]

    impIndList = []
    improvmentIndicatorLink = '<img alt="Improvement indicator" src="Images/info.gif"/>'
    for i, v in enumerate(tagList):
        if i in range(2, 100, 4):
            impIndList.append(0)
        if improvmentIndicatorLink in str(v.contents):
            impIndList[-1] = 1

    refList = [str(v.string).replace(" ", "") for i, v in enumerate(tagList) if i in range(3, 100, 4)]

    #remove any regular expressions from entries
    addressList = stripRegEx(addressList)
    ctBandList = stripRegEx(ctBandList)
    refList = stripRegEx(refList)
    return addressList, ctBandList, impIndList, refList


def write_error_log(s, mytype="timeout"):
    if mytype == 'missing':
        with open(output_path+"missingPostCodes.csv", "a") as text_file:
            text_file.write(str(s) + '\n')
    else:
        with open(output_path+"timeOutErrors.csv", "a") as text_file:
            text_file.write(str(s) + '\n')
    return


def get_data(driver, query):
    #wait for page to load
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((BY.CLASS_NAME, 'scl_complex')))
    except:
        write_error_log(query)

    try:
        driver.find_element_by_link_text("Next page")
        while  driver.find_element_by_link_text("Next page"):
            #parse page
            soup = bs(driver.page_source, 'lxml')
            addressList, ctBandList, impIndList, refList = parsePage(soup)
            #add to ouput file
            write_response_file([addressList, ctBandList, impIndList, refList])
            #move to next page
            driver.find_element_by_link_text("Next page").click()
            #wait for page to load

            try:
                WebDriverWait(driver, delay).until(EC.presence_of_element_located((BY.CLASS_NAME, 'scl_complex')))
            except:
                write_error_log(query)

    except:
        #check for data in page
        resultSearch = driver.find_element_by_xpath("//div[@id='Content']/div/div/h2").text
        if resultSearch != 'Search for your Council Tax band - no results':
            #parse page
            soup = bs(driver.page_source, 'lxml')
            addressList, ctBandList, impIndList, refList = parsePage(soup)
            #add to ouput file
            write_response_file([addressList, ctBandList, impIndList, refList])
        else:
            write_error_log(query, 'missing')
    return


def main():
    global counter
    counter = 2
    postcodes = readfile()
    driver = init_driver()

    for query in postcodes:
        query = query.replace("'", "")
        try:
            page = lookup(driver, query)
            get_data(driver, query)
        except:
            driver.quit()
            time.sleep(delay)
            driver = init_driver()

        #sleep random time
        time.sleep(np.random.randint(1, 3))

    driver.quit()

#run the web-scraper
main()
