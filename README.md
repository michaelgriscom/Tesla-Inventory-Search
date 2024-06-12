# Tesla Inventory Search

## What this is

Tesla's used cars follow a dynamic pricing model, the first order approximation
of which is that the vehicle costs decrease by a few hundred dollars each day
until a sale occurs

This repo contains a Python script which:
- Runs a periodic search of used Tesla inventory
- Scores each vehicle based on its attributes (e.g. mileage, AWD, FSD, etc.)
- Updates an iCloud file with the best values
- Sends an iMessage to a phone number whenever the best one changes

## Disclaimer

It is unlikely I will ever update this, and it was written without any intention
of reuse/longevity

## Instructions

Update `search.py` with values that match you, e.g.:

- Your zip code and anything else you want in the base request (you can go to
Tesla's website and find the request in the network tab of your browser)
- Values for the different features/mileage/year/etc
- Add in additional options that you want to score

Note that the script just uses raw years which don't align with Tesla's model
updates; Tesla does provide the factory date for used vehicles, which could
be used to better score the vehicles based on

### How to run

```
python search.py 5551234567
```
