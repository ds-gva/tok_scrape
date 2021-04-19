import pandas as pd
import requests
import json
from selenium import webdriver
import time
from mako.template import Template
from flask import Flask
from flask import render_template

API_KEY = "XXX"  # put your bscscan api key here

# Check if the element exists in the HTML page
def hasXpath(xpath, driver):
    try:
        found_element = driver.find_element_by_xpath(xpath)
        return True
    except:
        return False

# Print some pretty JSON
def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

verified_tokens = []
verified_tokens_with_transactions = []
final_tokens_list = []

@app.route('/')
def entry_page_render():
    return render_template('index.html')

@app.route('/tokens')
def pull_tokens():

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1024, 600)
    driver.maximize_window()

    
    driver.get ("https://tokenfomo.io/")
    driver.find_element_by_tag_name('tfoot').click()
    fomo_tokens = driver.find_elements_by_xpath("//*[@class='Home_mainTable__d_JUm']/tbody/tr")
    num_new_tokens = len(fomo_tokens)


    for token in fomo_tokens[0:300]:
        token_name = token.find_elements_by_xpath(".//td")[0].text
        token_urls = token.find_elements_by_xpath(". //td/a")
        bsc_url = token_urls[0].get_attribute("href")
        pcs_url = token_urls[1].get_attribute("href")

        split_url = bsc_url.rsplit('/')

        if(split_url[2] == 'bscscan.com'):
            token_address = split_url[-1]
            check_contract = "https://api.bscscan.com/api?module=contract&action=getabi&address=" + token_address + "&apikey=" + API_KEY
            contract_response = requests.get(check_contract)
            verified = contract_response.json()['status']

            if(verified == "1"):
                poo_url = "https://poocoin.app/tokens/" + token_address
                token_to_append = [token_name, token_address, bsc_url, pcs_url, poo_url]
                verified_tokens.append(token_to_append)

    num_verified_tokens = len(verified_tokens)

    print("Found ", num_verified_tokens," verified tokens")

    driver.quit()

    return render_template('tokens.html', num_verified_tokens=num_verified_tokens)

@app.route('/filter')
def filter_tokens():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1024, 600)
    driver.maximize_window()

    for token in verified_tokens:
        check_tx = "https://api.bscscan.com/api?module=account&action=txlist&address=" + token[1] + "&apikey=" + API_KEY
        tx = requests.get(check_tx).json()
        num_tx = len(tx["result"])

        if(num_tx > 10):
            now = time.time()
            last_tx_time = (now - float(tx["result"][-1]["timeStamp"]))/60
            
            if (last_tx_time < 10):
                verified_tokens_with_transactions.append(token)

    num_tokens_with_transactions = len(verified_tokens_with_transactions)

    for token in verified_tokens_with_transactions:
        read_contract = "https://bscscan.com/readContract?a=" + token[1]
        driver.get(read_contract)

        if( (hasXpath("//*[contains(.,'. newun')]", driver) == False ) & (hasXpath("//*[contains(.,'. owner')]", driver) == True) & (hasXpath("//*[contains(.,'. uniswapV2Pair')]", driver) == True)):
            cards = driver.find_elements_by_class_name('card')
            
            owner_address = ''
            liquidity_pool = ''
            for card in cards:
                card_text = card.text

                if(". owner" in card_text):
                    owner_address = card_text.rsplit(' ')[1][6:]
                    
                if(". uniswapV2Pair" in card_text):
                    liquidity_pool = card_text.rsplit(' ')[1][14:]

            token.append(owner_address)
            token.append(liquidity_pool)
            

            read_holders = "https://bscscan.com/token/generic-tokenholders2?m=normal&a=" + token[1]
            driver.get(read_holders)
            holders_table = driver.find_elements_by_tag_name("tr")[1]
            main_holder_address = holders_table.find_elements_by_tag_name("td")[1].text

            token.append(main_holder_address)

            final_tokens_list.append(token)



        else:
            print("Either no owner or newun function present -> token discarded")


    return render_template('filter.html', num_tokens_with_transactions=num_tokens_with_transactions, final_tokens_list=final_tokens_list)

if __name__ == '__main__':
    app.run()
