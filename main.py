import requests
import pymysql

free_api_key = 'c7a9fea03571e4119838f7d7091cf679'
base_url = 'https://api.the-odds-api.com/v4/sports/'
dbinstance_endpoint = 'database.cl4b0hojqcsj.us-east-1.rds.amazonaws.com'
db_username = 'admin'
db_pw = 'pinnacle'
db_name = 'bets'

class APIinterface():

    def __init__(self, hostendpoint, apikey, serverhost, uname, pw, db):
        self.endpoint = hostendpoint
        self.apikey = apikey
        self.sport_key_dict = {}
        self.connection = pymysql.connect(host = serverhost, user = uname, password = pw, database = db, autocommit=True)
        self.cursor = self.connection.cursor()
    
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
    
    def create_ML_table(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS moneyline (id VARCHAR(100), Home_Team VARCHAR(100), Home_Team_Dec_Odds FLOAT(7,2), Away_Team VARCHAR(100), Away_Team_Dec_Odds FLOAT(7,2), Start_Time TIMESTAMP')
    
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
        



