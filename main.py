import requests
import pymysql

free_api_key = 'c7a9fea03571e4119838f7d7091cf679'
base_url = 'https://api.the-odds-api.com/v4/sports/'

class APIinterface():

    def __init__(self, hostendpoint, apikey):
        self.endpoint = hostendpoint
        self.apikey = apikey
        self.sport_key_dict = {}
    
    def get_inseason_sports(self):
        if len(self.sport_key_dict) != 0:
             print(list(self.sport_key_dict.values()))
        query_params = {'apiKey':self.apikey, 'all' :'false'}
        json = requests.get(self.endpoint, params = query_params).json()
        for sport in json:
            cur_sport = sport['title']
            cur_key = sport['key']
            self.sport_key_dict[cur_sport]=cur_key
        
        print(list(self.sport_key_dict.values()))
    
    def getMLodds(self, sport_key):
        if sport_key not in list(self.sport_key_dict.values()):
            print('error -- invalid sport key passed')
            return 
        
        json = requests.get(self.endpoint+sport_key+'/odds/', params = {'apiKey':self.apikey,'regions':'us','markets':'h2h'}).json()

        for game in json:
            game_id = game['id']
            home_team = game['home_team']
            away_team = game['away_team']
            bookies = game['bookmakers']

            for book in bookies:
                book_name = book['title']
                outcomes = book['markets'][0]['outcomes']
                
                for outcome in outcomes:
                    cur_team = outcome['name']
                    cur_price = outcome['price']
        



