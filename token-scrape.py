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


@app.route('/')
def entry_page_render():
    return render_template('index.html')

@app.route('/tokens_filter/<num>')
def pull_tokens(num):

    final_verified_tokens_list = []
    num = int(num)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1024, 600)
    driver.maximize_window()

    driver.get ("https://tokenfomo.io/")
    driver.find_element_by_tag_name('tfoot').click()
    fomo_tokens = driver.find_elements_by_xpath("//*[@class='Home_mainTable__d_JUm']/tbody/tr")
    num_new_tokens = len(fomo_tokens)

    if (num == 9999):
        num = num_new_tokens - 1

    print("___________________STARTING ANALYSIS___________________")
    print("Found ", num_new_tokens," new tokens on tokenfomo")
    print("Running analysis on the last, ", num)
    print("_______________________________________________________")


 
    num_verified_tokens = 0
    num_verified_tokens_with_transactions = 0
    num_final_verified_tokens_list = 0


    for token in fomo_tokens[0:num]:
        token_name = token.find_element_by_xpath(".//td[@class='Home_name__3fbfx']").text
        token_symbol = token.find_element_by_xpath(".//td[@class='Home_symbol__-cNvY']").text
        token_urls = token.find_elements_by_xpath(". //td/a")
        bsc_url = token_urls[0].get_attribute("href")
        pcs_url = token_urls[1].get_attribute("href")

        
        print(f'\nAnalysing  token $' + token_symbol + ' - ' + token_name)

        split_url = bsc_url.rsplit('/')

        if(split_url[2] == 'bscscan.com'):
            token_address = split_url[-1]
            check_contract = "https://api.bscscan.com/api?module=contract&action=getabi&address=" + token_address + "&apikey=" + API_KEY
            contract_response = requests.get(check_contract)
            verified = contract_response.json()['status']
            

            if(verified == "1"):
                print('Token ' + token_symbol + ' - ' + token_name + ' has a verified contract on BSC')
                poo_url = "https://poocoin.app/tokens/" + token_address
                
                token_to_append = [token_name, token_symbol, token_address, bsc_url, pcs_url, poo_url]
                num_verified_tokens += 1

                check_tx = "https://api.bscscan.com/api?module=account&action=txlist&address=" + token_address + "&apikey=" + API_KEY
                tx = requests.get(check_tx).json()
                num_tx = len(tx["result"])

                if ( num_tx > 10):
                    now = time.time()
                    last_tx_time = (now - float(tx["result"][-1]["timeStamp"]))/60
                    
                    if (last_tx_time < 10):
                        num_verified_tokens_with_transactions += 1
                        print('Token ' + token_symbol + ' - ' + token_name + ' RETAINED -> has over 10 transactions, and transactions in the last 10 minutes')
                        
                        new_driver = webdriver.Chrome(options=chrome_options)
                        new_driver.set_window_size(1024, 600)
                        new_driver.maximize_window()
                        
                        ## Check contract and return owner, liquidity pool, etc.
                        read_contract = "https://bscscan.com/readContract?a=" + token_address
                        new_driver.get(read_contract)

                        if( (hasXpath("//*[contains(.,'. newun')]", new_driver) == False ) & (hasXpath("//*[contains(.,'. owner')]", new_driver) == True) & (hasXpath("//*[contains(.,'. uniswapV2Pair')]", new_driver) == True)): 
                            
                            cards = new_driver.find_elements_by_class_name('card')
                            owner_address = ''
                            liquidity_pool = ''
                            for card in cards:
                                card_text = card.text

                                if(". owner" in card_text):
                                    owner_address = card_text.rsplit(' ')[1][6:]
                                    
                                if(". uniswapV2Pair" in card_text):
                                    liquidity_pool = card_text.rsplit(' ')[1][14:]

                            token_to_append.append(owner_address)
                            token_to_append.append(liquidity_pool)
                            
                            read_holders = "https://bscscan.com/token/generic-tokenholders2?m=normal&a=" + token_address
                            new_driver.get(read_holders)

                            holders_table = new_driver.find_elements_by_tag_name("tr")[1]
                            main_holder_address = holders_table.find_elements_by_tag_name("td")[1].text
                            token_to_append.append(main_holder_address)

                            new_driver.quit()
                            num_final_verified_tokens_list += 1
                            final_verified_tokens_list.append(token_to_append)

                            print('Token ' + token_symbol + ' - ' + token_name + ' RETAINED -> has an owner, a liquidity pool, and no newun')
                        else:
                            print('Token ' + token_symbol + ' - ' + token_name + ' DISCARDED -> either no liquidity pool, no owner or newun scam')
                    else:
                        print('Token ' + token_symbol + ' - ' + token_name + ' DISCARDED -> no transaction in last 10 minutes')
                else:
                    print('Token ' + token_symbol + ' - ' + token_name + ' DISCARDED -> less than 10 transactions')                       

            else:
                print('Token ' + token_symbol + ' - ' + token_name + ' DISCARDED -> no verified contract on the BSC')
            

    print("___________________ANALYSIS COMPLETE___________________")
    print("Total Tokens Analyzed: ", num)
    print("Found ", num_verified_tokens," verified tokens")
    print("Of which, ", num_verified_tokens_with_transactions," with >10 Tx and at least 1 Tx in last 10min")
    print("And, ", num_final_verified_tokens_list, "Responding to contract criteria")
    print("_______________________________________________________")

    driver.quit()
    

    return render_template('tokens_filter.html', final_tokens_list=final_verified_tokens_list, num_new_tokens=num_new_tokens, num=num, num_verified_tokens=num_verified_tokens, num_verified_tokens_with_transactions=num_verified_tokens_with_transactions, num_final_verified_tokens_list=num_final_verified_tokens_list)

if __name__ == '__main__':
    app.run()
