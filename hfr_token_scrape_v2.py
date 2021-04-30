from mako.template import Template
from flask import Flask
from flask import render_template
from aiohttp.helpers import current_task
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from web3 import exceptions as w3exceptions
from dotenv import load_dotenv
import requests
import constants
import os
from datetime import datetime
import time

load_dotenv() # get .env
API_KEY = os.getenv('API_KEY') # load API_KEY

w3 = Web3(HTTPProvider(constants.BLOCKCHAIN_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3.clientVersion
w3.isConnected()

def return_latest_block():
    return {"jsonrpc":"2.0",
            "method":"eth_blockNumber",
            "params":[],
            "id":83 }

def format_logs_request(from_block, to_block):
    from_block =str(from_block)
    to_block = str(to_block)
    return {"jsonrpc":"2.0",
                "id":1,
                "method":"eth_getLogs",
                "params": [{"fromBlock": from_block,
                            "toBlock": to_block,
                            "topics": constants.TOPICS,
                            "address": constants.PCS_V2_FACTORY_ADDRESS}]}

# Get starting block by going back in time
def find_starting_block(since_minutes):
    current_block = int(requests.post(constants.BLOCKCHAIN_URL, json=return_latest_block()).json()['result'],16)
    starting_block = int(current_block - ((since_minutes * 60)/ constants.SECONDS_PER_BLOCK))
    return Web3.toHex(starting_block)

# Pull tokens from the blockchain over the last x minutes
def get_latest_tokens(minutes_to_scrape):
    requests_list = []
    if (minutes_to_scrape > 249):

        starting_block = find_starting_block(1440) # if we are over 4h lets just assume we go for a full 24h
        current_last_block = int(starting_block,16) + 4999
        get_logs_request = format_logs_request(starting_block, Web3.toHex(current_last_block))

        success = False
        while success == False:
            request = requests.post(constants.BLOCKCHAIN_URL, json=get_logs_request).json()
            if 'result' in request:
                success = True
                requests_list.append(request)
            else:
                success = False

        num_iter = int((1440*(60/constants.SECONDS_PER_BLOCK))/5000) - 1
        i = 0
        while i < num_iter:
            starting_block = current_last_block + 1
            current_last_block = starting_block + 4999
            get_logs_request = format_logs_request(Web3.toHex(starting_block), Web3.toHex(current_last_block))

            success = False
            while success == False:
                request = requests.post(constants.BLOCKCHAIN_URL, json=get_logs_request).json()
                if 'result' in request:
                    success = True
                    requests_list.append(request)
                    i += 1
                else:
                    success = False 

        starting_block = current_last_block + 1
        get_logs_request = format_logs_request(Web3.toHex(starting_block), 'latest')

        success = False
        while success == False:
            request = requests.post(constants.BLOCKCHAIN_URL, json=get_logs_request).json()
            if 'result' in request:
                success = True
                requests_list.append(request)
            else:
                success = False

    else:
        starting_block = find_starting_block(minutes_to_scrape)
        get_logs_request = format_logs_request(starting_block, 'latest')

        success = False
        while success == False:
            request = requests.post(constants.BLOCKCHAIN_URL, json=get_logs_request).json()
            if 'result' in request:
                success = True
                requests_list.append(request)
            else:
                success = False
        
    new_tokens_list = []
    token_count = 0
    for block_logs in requests_list:
        try:
            results = block_logs['result']
        except KeyError:
            print(block_logs)
            print(type(block_logs))
        #print(block_logs)
        for a_log in results:
            for a_topic in a_log['topics']:
                if ((a_topic != constants.TOPICS) & (a_topic != constants.WBNB_ADDRESS_LONG) & (a_topic[:8] == '0x000000')):
                    token_address = '0x'+ a_topic[26:]
                    token_block = a_log['blockNumber']
                    token_count += 1
                    new_tokens_list.append([token_address, token_block])
    print("Identified", token_count, "new tokens in the last ", minutes_to_scrape, "minutes")
    return new_tokens_list

# Encode function signature to get the hash using SHA3
def encode_fn_signature(function):
    return Web3.sha3(function.encode('utf-8'))

# Function returning True if the passed method signature is present in the contract's hashed code
def check_fn_exists(code, signature):
    signature = "63"+ signature.hex()[2:10]
    code = Web3.toHex(code)

    return signature in code

# Allows to call a function in a contract by submitting a particular data hash (the function's signature)
# contract: the token's address
# data: the function's signature
def call_function_with_hash(data, contract, w3):
    call_content = {
        'to': contract,
        'data': data
    }
    return w3.eth.call(call_content).hex()

# Allows to parse the hash from an RPL output from a called method
# returns bytes ; works for functions with one output
def parse_fn_single_output(fn_output):
    fn_output = fn_output[2:]
    position = '0x' + fn_output[:64]
    offset = (int(position,16)*2)

    length = '0x' + fn_output[offset:offset+64]
    length = int(length,16)*2

    main_output= fn_output[offset+64:offset+64+length]

    return Web3.toBytes(hexstr=main_output) # returns in Bytes

# Check whether the owner address is a contract, a wallet, or a dead address (or blank)
def check_owner_type(address, w3):
    try:
        code = w3.eth.getCode(address)
        if (Web3.toHex(code) == '0x'):
            if (address[-4:] == 'dEaD' or address[-10:] == '0000000000'):
                return 'dead'
            else:
                return 'wallet'
        else:
            return 'contract'
    except w3exceptions.InvalidAddress:
        print("EXCEPTION: ", address)
        return 'dead'

app = Flask(__name__)

@app.route('/')
def entry_page_render():
    return render_template('index.html')

@app.route('/footer')
def new():
    return render_template("footer.html")

@app.route('/tokens_filter/<num>')
def pull_tokens(num):
    last_minutes_to_scrape = int(num) # Max 249 for the time being (5000 blocks) - we can increase later

    latest_bsc_tokens_list = get_latest_tokens(last_minutes_to_scrape)

    mint_fn_signature = encode_fn_signature("mint(address,uint256)")
    newun_fn_signature = encode_fn_signature("transfernewun(address)")
    pause_fn_signature= encode_fn_signature("pause()")

    retained_tokens = []

    for token in latest_bsc_tokens_list[::-1]:
        token_address = w3.toChecksumAddress(token[0])
        token_block = token[1]
        token_code = w3.eth.getCode(token_address)

        mint = check_fn_exists(token_code, mint_fn_signature)
        newun = check_fn_exists(token_code, newun_fn_signature)
        pause = check_fn_exists(token_code, pause_fn_signature)

        owner_fn_signature= encode_fn_signature("owner()")
        token_owner = call_function_with_hash(owner_fn_signature, token_address,w3)
        if (token_owner == '0x'):
            owner_type = 'no_owner'
        else:
            token_owner = '0x' + token_owner[26:]
            owner_type = check_owner_type(w3.toChecksumAddress(token_owner),w3)

        if (mint or newun or pause or owner_type=='wallet' or owner_type=='no_owner'):
            print(token_address, " - Token DISCARDED -> scam functions in contract or dev is owner: ", token_owner)
        else:
            check_contract = "https://api.bscscan.com/api?module=contract&action=getabi&address=" + token_address + "&apikey=" + API_KEY
            token_abi = requests.get(check_contract).json()
            if (token_abi['status'] == "1"):

                contract_abi = token_abi['result']
                contract = w3.eth.contract(address=token_address, abi=contract_abi)

                transfer_minutes = 10 # Check for transfers in last 10 minutes
                transfer_start_block = find_starting_block(transfer_minutes)
                transfers = contract.events.Transfer.getLogs(fromBlock=transfer_start_block, toBlock='latest')
                token_transfers = len(transfers)
                if(token_transfers < 10):
                    transfer_color = 'table-danger'
                else:
                    transfer_color = ''
                pcs_v2_factory_contract = w3.eth.contract(address=w3.toChecksumAddress(constants.PCS_V2_FACTORY_ADDRESS), abi=constants.PCS_ABI)
                wbnb_address_short = w3.toChecksumAddress("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
                liquidity_v2_pair_address = pcs_v2_factory_contract.functions.getPair(token_address, wbnb_address_short).call()
                pair_creation_time = w3.eth.get_block(token_block).timestamp
                time_since_creation = int((time.time() - pair_creation_time)/60)
                approved_token = {
                    "name": contract.functions.name().call(),
                    "symbol": contract.functions.symbol().call(),
                    "address": token_address,
                    "bscscan": "https://bscscan.com/token/" + token_address,
                    "poocoin": "https://poocoin.app/tokens/" + token_address,
                    "top_holders": "https://bscscan.com/token/" + token_address + "#balances",
                    "lp_v2": "https://bscscan.com/token/" + liquidity_v2_pair_address + "#balances",
                    "contract_source": "https://bscscan.com/address/" + token_address + "#code",
                    "owner": token_owner,
                    "owner_type": owner_type,
                    "creation_time": time_since_creation,
                    "num_transfers": token_transfers,
                    "transfer_color": transfer_color
                }
                retained_tokens.append(approved_token)
                print(token_address, " - Token RETAINED")
            else:
                print(token_address, "- Token DISCARDED -> Source Code is NOT VERIFIED on BSC")

    num_total_tokens = len(latest_bsc_tokens_list)
    num_tokens_retained = len(retained_tokens)
    print("Finished Analysis, retained", num_tokens_retained, "tokens")

    auto_reload = False
    auto_reload = True if (int(num) < 250) else auto_reload == False

    return render_template('tokens_filter.html', auto_reload=auto_reload, final_tokens_list=retained_tokens, num_retained=num_tokens_retained, total_analysed=num_total_tokens, timeframe=last_minutes_to_scrape)
if __name__ == '__main__':
    app.run()