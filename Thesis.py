import pandas as pd
import numpy as np
import string
import base64
import json
from requests import post, get

class Dataset:
    def __init__(self, file_path, credentials):
        self.df = pd.read_csv(file_path)
        self.credentials = credentials

        self.df = self.df.loc[(self.df.country == "us")]
        self.df.columns = self.df.columns.str.lower()
        self.df.date = self.df.date.apply(lambda x: pd.to_datetime(x))
        self.df.sort_values(by= ["date", "position"], inplace= True)
        self.df.drop_duplicates(subset= ["name", "position", "date"], keep= "first", inplace= True)
        self.df = self.df.loc[(self.df.date >= "2020-11-12")]

        self.df = DummyOne(self.df)
        self.df = ReleaseDate(self.df)
        self.df = DummyTwo(self.df, file_path)

class DummyOne:
    def __init__(self, df):
        self.df = df
        self.replace_artists_names()
        self.get_dummy_one()
    
    def replace_artists_names(self):
        try:
            artists = []
            for (index, row) in self.df.iterrows():
                artist = row["artists"].replace("[", "").replace("'", "").replace("]", "")
                artist = artist.split(",")
                artist = artist[0].strip()
                artists.append(artist)
            
            self.df.drop(columns= "artists", inplace= True)
            self.df.insert(2, "artists", artists)
        except Exception as ex:
            print(ex)
        
    def get_dummy_one(self):
        try:
            dummy1 = []
            songs = {}
            previous_date = {}

            for date in self.df.date.unique():
                temp_df = self.df.loc[(self.df.date == "date")]
                for (index, row) in temp_df.iterrows():
                    if row.name not in songs:
                        dummy1.append(0)
                        songs[row.name] = date
                    else:
                        if previous_date == songs.get(row.name):
                            dummy1.append(1)
                            songs[row.name] = date
                        elif previous_date != songs.get(row.name):
                            dummy1.append(0)
                            songs[row.name] = date
            
                previous_date = date
            
            self.df.insert(10, "dummy_1", dummy1)

            result = {"Dummy 1 built successfully": True}
            return result
        except Exception as ex:
            result = {"Dummy 1 built successfully": False}
            print(result)
            print(ex)

class ReleaseDate:
    def __init__(self, df, credentials):
        self.df = df
        self.credentials = credentials
        self.token = RequestAPI(self.credentials).get_token()

        self.get_release_date()
    
    def get_release_date(self):
        try:
            release_dates = []
            for id in self.df.track_id.to_list():
                track = RequestAPI(self.credentials).get_features(self.token)
                release_dates.append(track["album"]["release_date"])
            
            self.df.insert(11, "release_date", release_dates)

            result = {"Successful request": True}
            return result
        except Exception as ex:
            result = {"Successful request": False}
            print(result)
            print(ex)

class RequestAPI:
    def __init__(self, credentials):
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
    
    def get_token(self):
        auth_string= self.client_id + ':' + self.client_secret
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')

        url = 'https://accounts.spotify.com/api/token'
        headers = {"Authorization" : 'Basic '+ auth_base64,
                   'Content_type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'client_credentials'}
        result = post(url, headers = headers, data = data)
        json_result = json.loads(result.content)
        token = json_result['access_token']
        return token

    def get_auth_header(self, token):
        return {'Authorization': 'Bearer ' + token}

    def get_features(self, token, song_id):
        url = f'https://api.spotify.com/v1/tracks/{song_id}?market=US'
        headers = self.get_auth_header(token)
        result = get(url , headers= headers)
        self.json_result = json.loads(result.content)

        return self.json_result
    
class DummyTwo:
    def __init__(self, df, file_path):
        self.df = df
        self.temp_df = pd.read_csv(file_path)

        self.temp_df = self.temp_df.loc[(self.temp_df.country == "us")]
        self.temp_df.columns = self.temp_df.columns.str.lower()
        self.temp_df.date = self.temp_df.date.apply(lambda x: pd.to_datetime(x))
        self.temp_df.sort_values(by= ["date", "position"], inplace= True)
        self.temp_df.drop_duplicates(subset= ["name", "position", "date"], keep= "first", inplace= True)
        self.temp_df = self.temp_df.loc[(self.temp_df.date >= "2020-11-05")]
        self.chart_dates = self.temp_df.unique()

        self.get_dummy_two()
    
    def get_dummy_two(self):
        try:
            dummy2 = []
            previous_date = self.chart_dates[0]
            for date in self.chart_dates[1:]:
                data = self.df.loc[(self.df.date == date)]
                for (index, row) in data.iterrows():
                    if previous_date <= row.release_date <= date:
                        dummy2.append(1)
                    else:
                        dummy2.append(0)
                
                previous_date = date
            
            self.df.insert(12, "dummy_2", dummy2)

            result = {"Dummy 2 built successfully": True}
            return result
        except Exception as ex:
            result = {"Dummy 2 built successfully": False}
            print(result)
            print(ex)