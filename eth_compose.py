import argparse
import json
import warnings
from multiprocessing import Pool

import hexbytes as hb
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from web3 import Web3
from web3.beacon import Beacon

warnings.filterwarnings("ignore")

beacon = Beacon(
    "https://alpha-broken-theorem.discover.quiknode.pro/92a9cef483100acc3ae5c8cd9d5467b0f30b6b7b/")
w3 = Web3(Web3.HTTPProvider(
    "https://alpha-broken-theorem.discover.quiknode.pro/92a9cef483100acc3ae5c8cd9d5467b0f30b6b7b/"))

parser = argparse.ArgumentParser()

parser.add_argument("--start", help="starting block number", default=15537394)
parser.add_argument("--end", help="ending block number",
                    default=15537394 + 10000)


def block2slot(block):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    URL = f"https://etherscan.io/block/{block}"
    html = requests.get(URL, headers=headers).text
    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all('a', href=True):
        if link.get('href').startswith('https://beaconscan.com/slot/'):
            link = link.get('href')
            slot_number = int(link.split('/')[-1])
            return slot_number
    print('failed to get slot number')
    return None


def get_block_from_slot(slot):
    block_header = beacon.get_block_header(slot)
    block = beacon.get_block(slot)
    payload = {
        'slot': slot,
        'block_header': block_header,
        'block': block,
    }
    return payload


def get_block_from_block_num(block_num):
    block_data = dict(w3.eth.get_block(block_num))
    for item, value in block_data.items():
        if isinstance(value, hb.HexBytes):
            block_data[item] = value.hex()
        if isinstance(value, list):
            for i, v in enumerate(value):
                if isinstance(v, hb.HexBytes):
                    value[i] = v.hex()
    return block_data


def compose(block_number):
    try:
        slot = block2slot(block_number)
        block_data = get_block_from_block_num(block_number)
        slot_data = get_block_from_slot(slot)
        composed_data = dict(
            block_num=block_number,
            slot_num=slot,
            block_data=block_data,
            slot_data=slot_data,
        )
        # print(f"block {block_number} composed")
    except:
        print(f"block {block_number} failed")
        composed_data = {
            'message': 'connot collect data',
        }
    return composed_data


def get_multiple_blocks(block_numbers: list):
    with Pool(processes=32) as p:
        results = list(tqdm(p.imap(compose, block_numbers),
                       total=len(block_numbers)))
    return results


def blocks2json(blocks, block_nums):
    filename = f'blocks_{block_nums[0]}_{block_nums[-1]}.json'
    with open(filename, 'w') as f:
        json.dump(blocks, f, indent=2, sort_keys=True, separators=(',', ': '))
    return


def main():
    # debug only
    args = parser.parse_args()
    numbers = list(range(int(args.start), int(args.end)))

    blocks = get_multiple_blocks(numbers)
    blocks2json(blocks, numbers)

    return


if __name__ == '__main__':
    main()
