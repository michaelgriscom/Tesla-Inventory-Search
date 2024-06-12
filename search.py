import requests
from pprint import pp
import os
import csv
import subprocess
import sys
import time
import sched

matchThreshold = 0

def generateLeaderboard(sorted_scores):
  icloud_drive_path = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/")
  leaderboard_file_path = os.path.join(icloud_drive_path, "best_used_teslas.csv")
  shouldAlertNewValue = False

  # Read existing top score from CSV (if file exists)
  existing_top_score = -1
  if os.path.exists(leaderboard_file_path):
      with open(leaderboard_file_path, 'r') as csvfile:
          reader = csv.reader(csvfile)
          next(reader)  # Skip header row
          for row in reader:
              try:
                  existing_top_score = int(row[0])
                  break  # Stop after reading the first row
              except ValueError:
                  continue  # Ignore rows with invalid score form

  with open(leaderboard_file_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Score', 'URL', 'Info url'])  # Write header row
    for result in list(sorted_scores)[:10]:
      url = makePurchaseUrl(result['result'])
      infoUrl = makeTeslaInfoUrl(result['result'])
      score = result['score']
      writer.writerow([score, url, infoUrl])
      if(score > existing_top_score and score > matchThreshold):
          shouldAlertNewValue = True

  return shouldAlertNewValue

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
    "$APF2": 3250, # FSD
    "$DV4W": 1500, # AWD
    "$STY7S": 0, # 7 seater
    "$TW01": 750, # towing
    "$PBSB": -100, # black paint
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

def hasChargingConnector(result):
   return result['IsChargingConnectorIncluded']

def scoreResult(result):
    score = 39000

    price = result['InventoryPrice']

    odometer = result['Odometer']
    # $0.20-$0.25 cents/mile
    score -= (odometer / 4.5)

    year = result['Year']
    # year should probably be 2-3k
    score -= ((2024 - year) * 2500)

    score -= result['TransportationFee']
    score -= result['OrderFee']['value']

    if(hasChargingConnector(result)):
      score += 100

    if(isLongRange(result)):
        score += 2800

    # check for accidents
    if(not hasCleanHistory(result)):
        score -= 8000

    for key, value in optionCodeValues.items():
        if(hasOptionCode(result, key)):
            score += value
    return round(score - price)

def makePurchaseUrl(result):
    vin = result['VIN']
    url = f"https://www.tesla.com/my/order/{vin}?postal=15206&range=200&coord=40.4720642,-79.9136731&region=PA&titleStatus=used&redirect=no#overview"
    return url

def makeTeslaInfoUrl(result):
   vin = result['VIN']
   url = f"https://tesla-info.com/car/US-{vin}"
   return url

def search():
  print("Starting search...\n")

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
  for result in results:
      score = scoreResult(result)
      resultData = {'result': result, 'score': score}
      allScores.append(resultData)
      totalScore += score
      if(score >= matchThreshold):
          bestScores.append(resultData)

  averageScore = round(totalScore / len(results))

  print("\n")
  print(f"Count {len(results)}\nAverage score:{averageScore}")
  print(f"Count of best scores: {len(bestScores)}")
  print("\n")

  sorted_scores = sorted(allScores, key=lambda x: x['score'], reverse=True)

  print("Highest scores")

  # Access the sorted list
  for result in list(sorted_scores)[:5]:
    url = makeTeslaInfoUrl(result['result'])
    print(f"Score: {result['score']}\nUrl: {url}")

  print("\nLowest score")
  url = makeTeslaInfoUrl(sorted_scores[-1]['result'])
  print(f"Score: {sorted_scores[-1]['score']}\nUrl: {url}")

  shouldAlert = generateLeaderboard(sorted_scores)
  if(shouldAlert and len(sys.argv) > 1):
    phone_number = sys.argv[1]
    print(f"\nNew top score, sending text\n")
    url = makePurchaseUrl(sorted_scores[0]['result'])
    infoUrl = makeTeslaInfoUrl(sorted_scores[0]['result'])
    message = f"New top score: {sorted_scores[0]['score']}\n{url}\n{infoUrl}"
    applescript_command = f'''
    tell application "Messages"
        send "{message}" to buddy "{phone_number}"
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript_command], check=True)

  print("\nSearch complete\n")

def doSearch(scheduler):
  scheduler.enter(60 * 30, 1, doSearch, (scheduler,))
  search()

my_scheduler = sched.scheduler(time.time, time.sleep)
my_scheduler.enter(0, 1, doSearch, (my_scheduler,))
my_scheduler.run()

# search()
