from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By as BY
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup as bs
import re
import time
import numpy as np


postcodes = ['LS26 0UH'] # 'LS2 7UA', 'SW1A 1AA']
output_path = '/home/james/Desktop/'
delay = 10


def init_driver():
    driver = webdriver.Firefox()
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

    with open(output_path+"addressCTBands.csv", "a") as text_file:
        text_file.write(myString)
    counter += 1
    return


def write_error_log(s):
    with open(output_path+"errors.csv", "a") as text_file:
        text_file.write(str(s) + '\n')
    return


def readfile():
    f = open('C:/Users/James Crosbie/Desktop/landreg.html')
    data = f.read()
    f.close()
    return data


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


def main():
    global counter
    counter = 1
    #postcodes = readfile()
    driver = init_driver()
    for query in postcodes:
        page = lookup(driver, query)

        #wait for page to load
        try:
            WebDriverWait(driver, delay).until(EC.presence_of_element_located((BY.CLASS_NAME, 'scl_complex')))
        except TimeoutException:
            write_error_log(query)
            continue

        try:
            driver.find_element_by_link_text("Next page")
            while driver.find_element_by_link_text("Next page"):
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
                except TimeoutException:
                    write_error_log(query)
                    continue
        except:
            #parse page
            soup = bs(driver.page_source, 'lxml')
            addressList, ctBandList, impIndList, refList = parsePage(soup)
            #add to ouput file
            write_response_file([addressList, ctBandList, impIndList, refList])

        #wait random time so as not to overload server
        time.sleep(np.random.randint(2, 6))

    driver.quit()


#run the web-scraper
main()
