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
    "$DV4W": 1500, # AWD
    "$STY7S": 0, # 7 seater
    "$TW01": 800, # towing
    "$PBSB": -500, # black paint
    # Old models https://tesla-info.com/guide/tesla-model-y-buyers-guide.php
    "$MTY06": -500,
}

def isLongRange(result):
    for codeData in result['OptionCodeData']:
        if(codeData['group'] == 'SPECS_RANGE'):
            return int(codeData['value']) > 300
    return False

def hasOptionCode(result, option):
    return option in result['OptionCodeList']

def hasCleanHistory(result):
    return result['VehicleHistory'] == 'CLEAN'

def scoreResult(result):
    score = 38000

    price = result['InventoryPrice']

    odometer = result['Odometer']
    # $0.20-$0.25 cents/mile
    score -= (odometer / 4.5)

    year = result['Year']
    # year should probably be 2-3k
    score -= ((2024 - year) * 2500)

    score -= result['TransportationFee']
    score -= result['OrderFee']['value']

    if(isLongRange(result)):
        score += 2500

    # check for accidents
    if(not hasCleanHistory(result)):
        score -= 8000

    for key, value in optionCodeValues.items():
        if(hasOptionCode(result, key)):
            score += value
    return score - price


totalMatches = 0
offset = 0
results = []
increment = 50
while len(results) == 0 or len(results) < totalMatches:
  params = {
      'query': '{"query":{"model":"my","condition":"used","arrangeby":"Year","order":"desc","market":"US","language":"en","super_region":"north america","PaymentType":"cash","lng":-79.9109,"lat":40.4725,"zip":"15206","range":0,"region":"PA"},"offset":%d,"count":%d,"outsideOffset":0,"outsideSearch":false,"isFalconDeliverySelectionEnabled":false,"version":null}' % (offset, increment),
  }
  data = makeRequest(params)
  totalMatches = int(data['total_matches_found'])
  offset += increment
  results += data['results']

allScores = []
bestScores = []
totalScore = 0
matchThreshold = 0
for result in results:
    score = scoreResult(result)
    resultData = {'result': result, 'score': score}
    allScores.append(resultData)
    totalScore += score
    if(score >= matchThreshold):
        bestScores.append(resultData)

averageScore = totalScore / len(results)

print(f"Count {len(results)}\nAverage score:{averageScore}")
print(f"Count of best scores: {len(bestScores)}")

sorted_scores = sorted(allScores, key=lambda x: x['score'], reverse=True)  # Sort by value (score)

def makeUrl(result):
    vin = result['VIN']
    url = f"https://www.tesla.com/my/order/{vin}?postal=15206&range=200&coord=40.4720642,-79.9136731&region=PA&titleStatus=used&redirect=no#overview"
    return url

# Access the sorted list
for result in list(sorted_scores)[:5]:
  url = makeUrl(result['result'])
  print(f"Score: {result['score']}\nUrl: {url}")

# for result in list(sorted_scores)[:1]:
#   print("Top result")
#   url = makeUrl(result['result'])
#   print(url)
#   print(pp(result))
