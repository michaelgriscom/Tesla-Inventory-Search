import requests
from pprint import pp


def makeRequest(params):
    headers = {
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    }

    response = requests.get(
        'https://www.tesla.com/inventory/api/v4/inventory-results',
        params=params,
        headers=headers,
    )

    return response.json()

# https://tesla-api.timdorr.com/vehicle/optioncodes
optionCodeValues = {
    "$APF2": 3500, # FSD
    "$DV4W": 3000, # AWD
    "$STY7S": 0, # 7 seater
    "$TW01": 1300, # towing
    "$PBSB": -2000, # black paint
}

def isLongRange(result):
    for codeData in result['OptionCodeData']:
        if(codeData['group'] == 'SPECS_RANGE'):
            return int(codeData['value']) > 300
    return False

def hasOptionCode(result, option):
    for codeData in result['OptionCodeData']:
        if(codeData['code'] == option):
            return True
    return False

def hasCleanHistory(result):
    return result['VehicleHistory'] == 'CLEAN'

def scoreResult(result):
    score = 33500

    price = result['InventoryPrice']

    odometer = result['Odometer']
    score -= (odometer / 5)

    year = result['Year']
    score -= ((2024 - year) * 4000)

    score -= result['TransportationFee']
    score -= result['OrderFee']['value']

    if(isLongRange(result)):
        score += 2000

    # check for accidents
    if(not hasCleanHistory(result)):
        score -= 10000

    for key, value in optionCodeValues.items():
        if(hasOptionCode(result, key)):
            score += value
    return score - price


params = {
    'query': '{"query":{"model":"my","condition":"used","arrangeby":"Year","order":"desc","market":"US","language":"en","super_region":"north america","PaymentType":"cash","lng":-79.9109,"lat":40.4725,"zip":"15206","range":0,"region":"PA"},"offset":0,"count":50,"outsideOffset":0,"outsideSearch":false,"isFalconDeliverySelectionEnabled":false,"version":null}',
}

data = makeRequest(params)


totalMatches = data['total_matches_found']
allScores = []
bestScores = []
totalScore = 0
matchThreshold = 2000

results = data['results']
for result in results:
    score = scoreResult(result)
    resultData = {'result': result, 'score': score}
    allScores.append(resultData)
    totalScore += score
    if(score >= matchThreshold):
        bestScores.append(resultData)

averageScore = totalScore / len(results)

print(f"Count {totalMatches}\nAverage score:{averageScore}")
print(f"Count of best scores: {len(bestScores)}")

sorted_scores = sorted(allScores, key=lambda x: x['score'], reverse=True)  # Sort by value (score)

def makeUrl(result):
    vin = result['VIN']
    url = f"https://www.tesla.com/my/order/{vin}?postal=15206&range=200&coord=40.4720642,-79.9136731&region=PA&titleStatus=used&redirect=no#overview"
    return url

# Access the sorted list
for result in list(sorted_scores)[:3]:
  url = makeUrl(result['result'])
  print(f"Score: {result['score']}\nUrl: {url}")

# for score in bestScores:
#     print(f"Best score: {score['score']}\nFull result:{score['result']}")