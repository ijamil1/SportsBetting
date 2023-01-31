import requests
import pymysql
import datetime 


class API():

    def __init__(self, hostendpoint='https://api.the-odds-api.com/v4/sports/'):
        with open('credentials.txt') as f:
            lines = f.readlines()
        lines = lines[0]
        credentials = lines.split(',')
        self.endpoint = hostendpoint
        self.apikey = credentials[0]
        self.sport_key_dict = {}
        self.connection = pymysql.connect(host = credentials[1], user = credentials[2], password = credentials[3], database = credentials[4], autocommit=True)
        self.cursor = self.connection.cursor()
        self.mybooks = ['BetUS','DraftKings','Barstool Sportsbook','BetMGM','BetRivers','FanDuel','FOX Bet','Unibet','William Hill (US)']
    
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
    
    def create_scores_table(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS scores (id VARCHAR(100), Home_Team VARCHAR(100), Home_Team_Score FLOAT(7,2), Away_Team VARCHAR(100), Away_Team_Score  FLOAT(7,2) CONSTRAINT id_pk PRIMARY KEY (id))')

    def create_ML_table(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS moneyline (id VARCHAR(100), sport_key VARCHAR(50), Home_Team VARCHAR(100), Home_Team_Dec_Odds FLOAT(7,2), Away_Team VARCHAR(100), Away_Team_Dec_Odds FLOAT(7,2), book  VARCHAR(50), Start_Time DATETIME, Insert_Time DATETIME, CONSTRAINT id_book_time PRIMARY KEY (id,book, Insert_Time))')

    def delete_from_tables(self):
        score_ids = self.getIdsScoresTbl()
        for id in score_ids:
            self.cursor.execute('delete from moneyline where id = \'{}\''.format(id))
            self.cursor.execute('delete from spreads where id = \'{}\''.format(id))
        
    
    def create_spreads_table(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS spreads (id VARCHAR(100), sport_key VARCHAR(50), Home_Team VARCHAR(100), Home_Team_Spread FLOAT(7,2), Home_Team_Odds FLOAT(7,2), Away_Team VARCHAR(100), Away_Team_Spread FLOAT(7,2), Away_Team_Odds FLOAT(7,2), book  VARCHAR(50), Start_Time DATETIME, Insert_Time DATETIME, CONSTRAINT id_book_time PRIMARY KEY (id,book, Insert_Time))')


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
                if book_name not in self.mybooks:
                    continue
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
        
    def uploadSpreads(self, sport_key):
        if sport_key not in list(self.sport_key_dict.values()):
            print('error -- invalid sport key passed')
            return 
        
        json = requests.get(self.endpoint+sport_key+'/odds/', params = {'apiKey':self.apikey,'regions':'us','markets':'spreads'}).json()

        for game in json:
            id = game['id']
            start_time = datetime.datetime.fromisoformat(game['commence_time'][:-1]+'+00:00')
            ht = game['home_team']
            at = game['away_team']
            
            for bookie in game['bookmakers']:
                book = bookie['title']
                if book not in self.mybooks:
                    continue
                outcomes = bookie['markets'][0]['outcomes']
                for outcome in outcomes:
                    if outcome['name']==at:
                        away_spread = outcome['point']
                        away_price = outcome['price']
                    elif outcome['name']==ht:
                        home_spread = outcome['point']
                        home_price  = outcome['price']
                utc_now = datetime.datetime.now(datetime.timezone.utc)
                if utc_now < start_time:
                    ls_commencetime =  game['commence_time'].split('T')
                    start_time_str = ls_commencetime[0] + ' ' + ls_commencetime[1][:-1]
                    utc_now_str = utc_now.strftime('%Y-%m-%d %H:%M:%S')
                    self.cursor.execute('INSERT into spreads VALUES (\'{}\',\'{}\',\'{}\',{},{},\'{}\',{},{},\'{}\',\'{}\',\'{}\')'.format(id,sport_key,ht,home_spread,home_price,at,away_spread,away_price,book, start_time_str, utc_now_str)) 

    def  getSpreads(self, sport_key):
        if sport_key not in list(self.sport_key_dict.values()):
            print('error -- invalid sport key passed')
            return 
        
        self.cursor.execute('SELECT * FROM spreads WHERE sport_key = \'{}\' and Start_Time > \'{}\''.format(sport_key,datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')))

        rows = self.cursor.fetchall()
        for row in rows:
            print(row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9], sep=', ')


    def getBalance(self, book=None):
        if book:
            if book not in self.mybooks:
                print('error -- invalid book passed')
                return 
            self.cursor.execute('SELECT * FROM balance where book = \'{}\''.format(book))
            return float(self.cursor.fetchall()[0][0])
        self.cursor.execute('SELECT * FROM balance')
        rows = self.cursor.fetchall()

        for row in rows:
            print(row[0],'$'+str(row[1]),sep=',')
        return

    def updateBalance(self, book, amount):
        if book not in self.mybooks:
            print('error -- invalid book passed')
            return 
        self.cursor('select amount from balance where book = \'{}\''.format(book))
        row = self.cursor.fetchall()
        cur_amt = float(row[0][0])
        new_amt = cur_amt + amount
        self.cursor('update balance set amount = {} where book = \'{}\''.format(new_amt,book))
    
    def  initalizeBalance(self):
        for book in self.mybooks:
            self.cursor.execute('INSERT INTO balance VALUES (\'{}\',{})'.format(book,100.00))
    

    def createSpreadBetsTable(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS spread_bets (id VARCHAR(100),team_bet_on VARCHAR(100), book_bet_at VARCHAR(100), amount_bet FLOAT(7,2), spread_offered FLOAT(7,2), line_offered FLOAT(7,2) CONSTRAINT id_book_team PRIMARY KEY (id,team_bet_on,book_bet_at))')
    
    def uploadSpreadBets(self, id, team, book,amount,spread,dec_odds):
        if amount > self.getBalance(book):
            print('not enough money at book to bet this amount')
            return
        self.updateBalance(book, -1*amount)
        self.cursor.execute('INSERT INTO spread_bets VALUES (\'{}\',\'{}\',\'{}\',{},{},{})'.format(id,team,book,amount,spread,dec_odds))
        
    def createMLBetsTable(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS ml_bets (id VARCHAR(100),team_bet_on VARCHAR(100), book_bet_at VARCHAR(100), amount_bet FLOAT(7,2), line_offered FLOAT(7,2) CONSTRAINT id_book_team PRIMARY KEY (id,team_bet_on,book_bet_at))')

    def uploadMLBets(self, id, team, book, amt, dec_odds):
        if amt > self.getBalance(book):
            print('not enough money at book to bet this amount')
            return
        self.updateBalance(book, -1*amt)
        self.cursor.execute('INSERT INTO ml_bets VALUES (\'{}\',\'{}\',\'{}\',{},{})'.format(id, team, book, amt, dec_odds))
    
    def getIdsScoresTbl(self):
        self.cursor.execute('select id from scores')
        rows = self.cursor.fetchall()
        ls = []
        for row in rows:
            ls.append(row[0])
        return ls
    
    def uploadScores(self, sportkey):
        json = requests.get(self.endpoint+sportkey+'/scores/',params={'apiKey':self.apikey,'daysFrom':3}).json()
        spreadbet_ids = []
        mlbet_ids = []
        score_ids = self.getIdsScoresTbl()
        self.cursor.execute('select id from spread_bets')
        rows = self.cursor.fetchall()
        for row in rows:
            spreadbet_ids.append(row[0])
        self.cursor.execute('select id from ml_bets')
        rows = self.cursor.fetchall()
        for row in rows:
            if row[0] not in spreadbet_ids:
                mlbet_ids.append(row[0])
        ht = ''
        at = ''
        ht_score = -1
        at_score = -1
        for game in json:
            if game['completed'] and (game['id'] in spreadbet_ids or game['id'] in mlbet_ids) and game['id'] not in score_ids:
                scores = game['scores']
                for score in scores:
                    cur_team = score['name']
                    cur_score = score['score']
                    if cur_team == game['home_team']:
                        ht = cur_team
                        ht_score = float(cur_score)
                    elif cur_team == game['away_team']:
                        at = cur_team
                        at_score = float(cur_score)
                if game['id'] in spreadbet_ids:
                    self.cursor.execute('select * from spread_bets where id = \'{}\''.format(game['id']))
                    rows = self.cursor.fetchall()
                    self.processSpreadBetResults(rows, ht, ht_score, at, at_score)
                if game['id'] in mlbet_ids:
                    self.cursor.execute('select * from ml_bets where id = \'{}\''.format(game['id']))
                    rows = self.cursor.fetchall()
                    self.processMLBetResults(rows,ht,ht_score,at,at_score)
                self.cursor.execute('INSERT INTO scores VALUES (\'{}\',\'{}\',{},\'{}\',{})'.format(game['id'],ht,ht_score,at,at_score))
                 

    def processMLBetResults(self,ls,ht,hts,at,ats):
        for row in ls:
            team_bet_on = row[1]
            book = row[2]
            amt = float(row[3])
            odds = float(row[4])
            if team_bet_on == ht:
                if hts > ats:
                    #won bet
                    payout = amt * odds
                    self.updateBalance(book,payout)
            elif team_bet_on == at:
                if ats > hts:
                    payout = amt * odds
                    self.updateBalance(book,payout)

    def processSpreadBetResults(self,ls, ht, hts, at, ats):
        for row in ls:
            team_bet_on = row[1]
            book = row[2]
            amt = float(row[3])
            spread = float(row[4])
            price = float(row[5])

            if team_bet_on == ht:
                if spread > 0:
                    if ats-hts < spread:
                        #won bet!
                        payout = amt * price 
                        self.updateBalance(book,payout)
                elif spread < 0:
                    spread = -1*spread
                    if hts - ats > spread:
                        #won bet
                        payout = amt * price 
                        self.updateBalance(book,payout)
            elif team_bet_on == at:
                if spread > 0:
                    if hts-ats < spread:
                        #won bet!
                        payout = amt * price 
                        self.updateBalance(book,payout)
                elif spread < 0:
                    spread = -1*spread
                    if ats - hts > spread:
                        #won bet
                        payout = amt * price 
                        self.updateBalance(book,payout)




