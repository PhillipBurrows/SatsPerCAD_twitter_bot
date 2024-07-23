import yfinance as yf, pandas as pd, plotly.express as px

# get stock info
BTCCAD = yf.Ticker("BTC-CAD")
print(BTCCAD.info)

# get historical market data
CADBTC_df = BTCCAD.history(period="1y", interval='1h')
CADBTC_df = CADBTC_df.drop(columns=['Dividends','Stock Splits','Volume'])

#from datetime import datetime
from dateutil import tz

def convert_UTC_to_NY(UTCdatetime):
    # METHOD 1: Hardcode zones:
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/New_York')

    # Tell the datetime object that it's in UTC time zone since datetime objects are 'naive' by default
    utc = UTCdatetime.replace(tzinfo=from_zone)

    # Convert time zone
    central_time = utc.astimezone(to_zone)
    return central_time

CADBTC_df.index = CADBTC_df.index.map(convert_UTC_to_NY)

#filter table for 4pm on fridays
CADBTC_df['Day_of_week'] = CADBTC_df.index.strftime("%A")
CADBTC_df = CADBTC_df[CADBTC_df['Day_of_week'] == "Friday"]
CADBTC_df = CADBTC_df.at_time('16:00')
CADBTC_df = CADBTC_df.drop(columns=["Day_of_week","Open","Low","High"])

### Convert to Sats nominator ###
def SatsConv(x):
  SatsPerCAD = 1/(x/100000000)
  return SatsPerCAD

#convert prices to sats
SATSCAD_df = CADBTC_df.map(SatsConv)

#capture data from table

close_sats_price = int(SATSCAD_df['Close'].loc[SATSCAD_df.index[-1]])
print(close_sats_price)

year_ago_sats_price = int(SATSCAD_df['Close'].loc[SATSCAD_df.index[1]])
print(year_ago_sats_price)

one_year_convertibility = int(((close_sats_price/year_ago_sats_price)*100)-100 / 1)
print(one_year_convertibility)

close_date = SATSCAD_df.index[-1]
close_date = close_date.strftime("%m/%d/%Y %H:%M")
print(close_date)

# Area chart
area_chart = px.area(SATSCAD_df['Close'], title = 'Satoshis per Canadian Dollar', color_discrete_map={"Close": "DarkOrange"})

area_chart.update_xaxes(title_text = 'Date')
area_chart.update_yaxes(title_text = 'Satoshis per CAD$')
area_chart.update_layout(showlegend = False)

#area_chart.show()

area_chart.write_image("images/SatsPerCAD_weekly.png")

import tweepy
# the below import is for calculating date. Not needed for you but I needed it.
from datetime import date
import shutil, pathlib, os

# take these from developer.twitter.com
from auth import (
    CONSUMER_KEY, 
    CONSUMER_SECRET, 
    ACCESS_KEY, 
    ACCESS_SECRET, 
    BEARER_TOKEN, 
    CLIENT_ID, 
    CLIENT_ID_SECRET
)

# Authenticate to Twitter
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(
    ACCESS_KEY,
    ACCESS_SECRET,
)
# this is the syntax for twitter API 2.0. It uses the client credentials that we created
newapi = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    access_token=ACCESS_KEY,
    access_token_secret=ACCESS_SECRET,
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
)

# Create API object using the old twitter APIv1.1
api = tweepy.API(auth)

# adding the tweet content in a multiline string. The {mydays} part is updated dynamically as the number of days from 6th Nov, 2023
if  one_year_convertibility < 0:
    convertibility = abs(one_year_convertibility)
    sampletweet = f"Current price is {close_sats_price} Satoshis per Canadian Dollar.\nOver the last year CAD to SAT convertability has worsened by {convertibility}%\n\nReported on NYSE/TSX weekly close - {close_date} ET"
else:
    sampletweet = f"Current price is {close_sats_price} Satoshis per Canadian Dollar.\nOver the last year CAD to SAT convertability has improved by {one_year_convertibility}%\n\nReported on NYSE/TSX weekly close - {close_date} ET"

# upload the media using the old api
media = api.media_upload("images/SatsPerCAD_weekly.png")
# create the tweet using the new api. Mention the image uploaded via the old api
post_result = newapi.create_tweet(text=sampletweet, media_ids=[media.media_id])
# the following line prints the response that you receive from the API. You can save it or process it in anyway u want. I am just printing it.
print(post_result)