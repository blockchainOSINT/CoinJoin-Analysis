# coinjoin.py
# by osint@aristaeus.tech - 03/2020

"""This script is designed to analyze a CoinJoin transaction and outputs a dictionary with the following format:

output_format = { txid_0: {address_0 : btc_amnt,
                           address_1: btc_amnt,...
                           address_n: btc_amnt}
                           total: sum(btc_amnts)
                ...txid_n: {address_0 : btc_amnt,...}
                }

where: txids = every transactions that spent a CoinJoin UTXOs
       address = the CoinJoin output addresses from which each tx spent the UTXO
       btc_amnt = the amount spent from this address
       total = the btc sum spent by this tx"""


import json
import requests
from pprint import pprint

txid = 'ec28dcc449972aa6ff350dd4eec729d9bddea6a22367b274f6ad8287d0665368' # input coinjoin txid - example "ec28dcc449972aa6ff350dd4eec729d9bddea6a22367b274f6ad8287d0665368"

def getOutspends():

    txids = []
    unspent = []

    r = requests.get(f"https://blockstream.info/api/tx/{txid}/outspends")
    outspends_json = r.json()

    # store all txids that are one hop downstream
    for outspend in outspends_json:
        if 'txid' in outspend:
            txids.append(outspend['txid'])
        else:
            unspent.append(outspend)

    """Note, another way to possibly ID common ownership of addresses is by unspent UTXOs, since usually almost all are spent"""

    print("Spent Outputs:", len(txids))
    print("Unspent Outputs:", len(unspent))

    return txids


def getOutputAddrs():

    r = requests.get(f"https://blockstream.info/api/tx/{txid}")
    r_json = r.json()
    outputsDict = dict()

    for output in r_json['vout']:
        # store addr: btc in outputsDict
        addr = output["scriptpubkey_address"]
        btc = int(output["value"]) / 100000000
        outputsDict.update({addr: btc})

    return outputsDict


def getInputAddrs(duplicatesDict):

    inputsDict = dict()

    for tx in duplicatesDict.keys():
        r = requests.get(f"https://blockstream.info/api/tx/{tx}")
        r_json = r.json()
        addrList = []
        for txid in r_json["vin"]:
            addrList.append(txid["prevout"]["scriptpubkey_address"])

        inputsDict.update({tx: addrList})

    return inputsDict


def getDuplicates(txids):

    duplicatesDict = dict()

    for tx in txids:
    # If element exists in dict then increment its value else add it in dict
        if tx in duplicatesDict:
            duplicatesDict[tx] += 1
        else:
            duplicatesDict[tx] = 1

    # Filter key-value pairs in dict. Keep pairs whose value is greater than 1 i.e. only duplicate elements from list.
    duplicatesDict = {key:value for key, value in duplicatesDict.items() if value > 1}

    return duplicatesDict


def getMatches(outputsDict, inputsDict):

    matchesDict = dict()
    btcDict = dict()

    for txid, inputsList in inputsDict.items():
        for output, btc in outputsDict.items():
            for input in inputsList:
                if output == input:
                    btcDict[output] = btc

        matchesDict[txid] = btcDict
        btcDict['total'] = round(sum(btcDict.values()), 8)
        btcDict = {}

    return matchesDict

def compareInVSOut(matchesDict):

    pass

def main():

    print()

    save_file = open(f"{txid}_CoinJoin.txt", "w")

    txids = getOutspends()
    print("\nAnalyzing Outspends...\n")
    outputsDict = getOutputAddrs()
    duplicatesDict = getDuplicates(txids)
    inputsDict = getInputAddrs(duplicatesDict)
    matchesDict = getMatches(outputsDict, inputsDict)

    print("\nTransactions with multiple spent outputs from this CoinJoin:\n")
    pprint(matchesDict)

    save_file.write(str(matchesDict))
    save_file.close()
    
    print(f"\n\nOutput saved as {save_file.name}")
    print("\nFinished. Goodbye!\n\n")

if __name__=="__main__":    
  main()

"""Notes: check if len(matchesDict[tx].values()) != duplicates[tx]

    (if number of UTXOs spent by an outspend in matchesDict is not
     equal to the duplicate tx frequency in duplicatesDict, then
     the user only partially spent one or more of the UTXOs in the outspend.)"""
