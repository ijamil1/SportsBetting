import requests
import pymysql
import datetime 


class APIinterface():

    def __init__(self, hostendpoint='https://api.the-odds-api.com/v4/sports/', apikey='c7a9fea03571e4119838f7d7091cf679', serverhost='database.cl4b0hojqcsj.us-east-1.rds.amazonaws.com', uname = 'admin', pw = 'pinnacle', db = 'bets'):
        self.endpoint = hostendpoint
        self.apikey = apikey
        self.sport_key_dict = {}
        self.connection = pymysql.connect(host = serverhost, user = uname, password = pw, database = db, autocommit=True)
        self.cursor = self.connection.cursor()
    
    def get_inseason_sports(self):
        if len(self.sport_key_dict) != 0:
             print(list(self.sport_key_dict.values()))
             return
        query_params = {'apiKey':self.apikey, 'all' :'false'}
        json = requests.get(self.endpoint, params = query_params).json()
        for sport in json:
            cur_sport = sport['title']
            cur_key = sport['key']
            self.sport_key_dict[cur_sport]=cur_key
        
        print(list(self.sport_key_dict.values()))
    
    def create_ML_table(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS moneyline (id VARCHAR(100), sport_key VARCHAR(50), Home_Team VARCHAR(100), Home_Team_Dec_Odds FLOAT(7,2), Away_Team VARCHAR(100), Away_Team_Dec_Odds FLOAT(7,2), book  VARCHAR(50), Start_Time DATETIME, Insert_Time DATETIME, CONSTRAINT id_book PRIMARY KEY (id,book))')

    def create_balance_table(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS balance (book VARCHAR(50), amount FLOAT(7,2))')
    
    def uploadMLodds(self, sport_key):
        if sport_key not in list(self.sport_key_dict.values()):
            print('error -- invalid sport key passed')
            return 
        
        json = requests.get(self.endpoint+sport_key+'/odds/', params = {'apiKey':self.apikey,'regions':'us','markets':'h2h'}).json()

        for game in json:
            game_id = game['id']
            home_team = game['home_team']
        
            away_team = game['away_team']
            
            start_time = datetime.datetime.fromisoformat(game['commence_time'][:-1]+'+00:00') #utc start_time 
            bookies = game['bookmakers']

            for book in bookies:
                book_name = book['title']
                outcomes = book['markets'][0]['outcomes']
                
                for outcome in outcomes:
                    cur_team = outcome['name']
                    cur_price = outcome['price']
                    if cur_team == home_team:
                        ht_price = cur_price
                    if cur_team == away_team:
                        at_price = cur_price
                
                utc_now = datetime.datetime.now(datetime.timezone.utc)
                if utc_now < start_time:
                    ls_commencetime =  game['commence_time'].split('T')
                    start_time_str = ls_commencetime[0] + ' ' + ls_commencetime[1][:-1]
                    utc_now_str = utc_now.strftime('%Y-%m-%d %H:%M:%S')
                    self.cursor.execute('INSERT into moneyline VALUES (\'{}\',\'{}\',\'{}\',{},\'{}\',{},\'{}\',\'{}\',\'{}\')'.format(game_id,sport_key,home_team,ht_price,away_team, at_price, book_name, start_time_str, utc_now_str))

    def getMLodds(self, sport_key):
        if sport_key not in list(self.sport_key_dict.values()):
            print('error -- invalid sport key passed')
            return 
        
        self.cursor.execute('SELECT * FROM moneyline WHERE sport_key = \'{}\' and Start_Time > \'{}\''.format(sport_key,datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')))

        rows = self.cursor.fetchall()
        for row in rows:
            print(row[2],row[3],row[4],row[5],row[6],row[7], sep=', ')
        

                 
        



