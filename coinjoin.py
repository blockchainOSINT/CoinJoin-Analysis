# coinjoin.py
# by osint@aristaeus.tech - March 5, 2020

"""This script is designed to analyze a CoinJoin transaction and outputs a dictionary with the following format:

output_format = { txid_0: {address_0 : btc_amnt,
                           address_1: btc_amnt,...
                           address_n: btc_amnt}
                ...txid_n: {address_0 : btc_amnt,...}
                }

where: txids = every transactions that spent a CoinJoin UTXOs
       address = the CoinJoin output addresses from which each tx spent the UTXO
       btc_amnt is the amount spent"""


import json
import requests
from pprint import pprint

txid = '' # sample coinjoin - "ec28dcc449972aa6ff350dd4eec729d9bddea6a22367b274f6ad8287d0665368"

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

    """Note, another way to possibly ID common ownership of addresses is by unspent UTXOs, since almost all <redacted> are spent"""

    print("Unspent Indexes:", unspent)
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
        btcDict = {}

    return matchesDict


def main():

    print()

    save_file = open("Sample_CoinJoin.txt", "w")

    txids = getOutspends()
    outputsDict = getOutputAddrs()
    duplicatesDict = getDuplicates(txids)
    inputsDict = getInputAddrs(duplicatesDict)
    matchesDict = getMatches(outputsDict, inputsDict)

    pretty_json = str(pprint(matchesDict))

    print(pretty_json, file = save_file)

    save_file.close()

    print("\nFinished. Goodbye!\n\n")

main()

"""Notes: check if len(matchesDict[tx].values()) != duplicates[tx]

    (in English, if number of UTXOs spent by an outspend in matchesDict is not
     equal to the duplicate tx frequency in duplicatesDict, then
     the user only partially spent one or more of the UTXOs in the outspend.)"""
