import requests
import datetime
import math
import json
import re

auth = 'my auth code is mine and you cannot have it; get your own and put it here'
decktuner = 'decktuner channel ID'
NOW = datetime.datetime.now()
days = 86400
unclaimed_ids = []
user_left_ids = []
workshop_list = []
tuner_list = []

class TUNER:
    def __init__(self, tuner, first_shop):
        self.active_workshops = [first_shop]
        self.runtime = first_shop.runtime
        self.id = tuner
    def add_workshop (self, shop):
        self.active_workshops.append(shop)
        self.runtime += shop.runtime
    def get_id(self):
        #return the id as a string
        return self.id.replace('\\n', ' & ')

class WORKSHOP:
    def __init__(self, raw):
        #set all the basic data
        self.close_attempted = False
        self.user_alive = True
        self.claimed = True
        self.active = True
        self.run_days = 0
        self.raw = raw
        self.name = ' '
        #get all the data from the raw data
        self.deconstruct(raw)
    def killuser (self):
        self.user_alive = False
    def deactivate (self):
        self.active = False
    def closefail (self):
        self.close_attempted = True
    def deconstruct(self, raw):
        raw = raw.replace('\"', '\'')
        print('\nNEW WORKSHOP:', raw)
        try:
            #get the id
            tmp_id = re.search('<#.*?>', raw).group()
            self.id = str(tmp_id[2:-1])

            #get the timestamp
            tmp_stamp = re.search("'timestamp': '.*?',", raw).group()
            self.stamp = str(tmp_stamp[14:-2])
            self.stamp = datetime.datetime.fromisoformat(self.stamp).timestamp()
            
            #get the runtime and daysfrom the timestamp
            self.runtime = NOW.timestamp() - self.stamp
            self.run_days = math.trunc(self.runtime / days)
            
            #get the budget
            tmp_budget = re.search("Budget', 'value': '.*?',", raw).group()
            self.budget =  str(tmp_budget[19:-2]).lower()
            if self.budget == 'no budget':
                self.budget = 'none'

            #get the catagory
            tmp_cat = re.search("Category', 'value': '.*?',", raw).group()
            self.cat = str(tmp_cat[21:-2]).lower()

            #get the commander
            tmp_cmdr = re.search("title': '.*?',", raw).group()
            self.commander = str(tmp_cmdr[9:-2])

            #get the tip
            try:
                tmp_tip = re.search("Tip Amount', 'value': '.*?',", raw).group()
                self.tip = cash(str(tmp_tip[23:-2]))
            except Exception as e:
                print ('Error in Tip Generation for workshop {:}: {:} (Tip set to 0)'.format(self.id, e))
                self.tip = 0

            #get the pilot
            tmp_pilot = re.search("Pilot', 'value': '<@.*?>',", raw).group()
            self.pilot = str(tmp_pilot[20:-3])

            #get the tuner
            try:
                tmp_tuner = re.search("Tuners', 'value': '<@.*?>',", raw).group()
                tmp_tuner = str(tmp_tuner[21:-3])
                added = False
                #search for the tuner in the tuner list and add the workshop to them
                for y in tuner_list:
                    if y.id == tmp_tuner:
                        y.add_workshop(self)
                        added = True
                #if workshop was not added to a tuner list, create a new tuner
                if added == False:
                    t = tuner_list.append(TUNER(tmp_tuner, self))
            except Exception as e:
                print('Error adding tuner to workshop {:}: {:} (No Tuner Set)'.format(self.id,e))
     
        except Exception as e:
            print('\n Error in workshop {:}: \n {:}'.format(e, raw))

def retrieve_messages(channel_ID, amount):
    headers={
        'authorization' : auth
    }
    r = requests.get('https://discord.com/api/v9/channels/{:}/messages?limit={:}'.format(channel_ID, amount), headers=headers)
    message_raw = json.loads(r.text)
    return message_raw

def retrieve_channels(server_ID):
    headers={
        'authorization' : auth
    }
    r = requests.get('https://discord.com/api/v9/guilds/{:}/channels'.format(server_ID), headers=headers)
    channel_raw = json.loads(r.text)
    #time info put outside of loop to increase scope
    check_time_stamp = NOW.timestamp()
    print (channel_raw)
    for x in channel_raw:
        #check tuning boards for inactive workshops first
        if 'tuning-board' in x['name']:
            for y in retrieve_messages(x['id'], 100):
                #deconstruct raw message data from turning board into a workshop element and append it to the workshop list
                workshop_list.append(WORKSHOP(str(y['embeds'])))
                #get recent messages from tuning boards
                info = str(y['embeds'])
                tmp_id = re.search('<#.*?>', info).group()
                if "'name': 'Tuners', 'value': '*none*'" in str(y['embeds']):
                    unclaimed_ids.append(str(tmp_id[2:-1])) #remove the <# and >
                    print('{:} appended to unclaimed IDs'.format(tmp_id[2:-1]))
        #check spam logs for users that left
        if 'spam-logs' in x['name']:
            print('')
            spam_messages = retrieve_messages(x['id'], 100)
            for y in spam_messages:
                spam_raw = str(y['embeds'])
                if 'Member left' in spam_raw:
                    tmp_left_id = re.search('<@.*?>', spam_raw).group()
                    real_left_id = str(tmp_left_id[2:-1])
                    user_left_ids.append(real_left_id)
                    print('User {:} has left the server.'.format(real_left_id))
    print('')
    for x in channel_raw:
        #check workshop lists
        if 'workshop' in x['name']:
            try:
                #find the workshop in the workshop list and set properties 
                for y in workshop_list:
                    if y.id == x['id']:
                        y.name = x['name']
                        if y.pilot in user_left_ids:
                            #if pilot left, kill user
                            y.killuser()
                            print('Workshop {:} killed'.format(x['id']))
                        if y.id in unclaimed_ids:
                            #if id unclaimed, set unclaimed
                            y.claimed = False
                            print('Append {:} to unclaimed - ID match: {:}'.format(x['name'], x['id']))#check timestamp
                #check the most recent timestamp and compare to now()
                recent_activity = retrieve_messages(x['id'], 1)
                for y in recent_activity:
                    message_time = datetime.datetime.fromisoformat(y['timestamp']).timestamp()
                    if check_time_stamp - message_time > 10*days:
                        for z in workshop_list:
                            if z.id == x['id']:
                                z.deactivate()
                #check recent five messages for !close
                recent_activity = retrieve_messages(x['id'], 5)
                for y in recent_activity:
                    if y['content'] == '!close':
                        for z in workshop_list:
                            if z.id == x['id']:
                                z.closefail()
            except Exception as e:
                print('Error for {:}: {:}.'.format(x['name'], e))

def cash(amount):
    #convert a string representing a cash amount into usd
    usd = int(re.sub('[^0-9]','', amount))
    amount = amount.lower()
    print(usd)
    if '-' in amount:
        l = amount.split('-')
        amount = str(re.sub('[^0-9]','', l[0]))
        usd = int(re.sub('[^0-9]','', l[0]))
    if '/' in amount:
        l = amount.split('/')
        amount = str(re.sub('[^0-9]','', l[0]))
        usd = int(re.sub('[^0-9]','', l[0]))
    if '\\' in amount:
        l = amount.split('\\')
        amount = str(re.sub('[^0-9]','', l[0]))
        usd = int(re.sub('[^0-9]','', l[0]))
    if 'or' in amount:
        l = amount.split('or')
        amount = str(re.sub('[^0-9]','', l[0]))
        usd = int(re.sub('[^0-9]','', l[0]))
    if '.' in amount:
        l = amount.split('.')
        amount = str(re.sub('[^0-9]','', l[1]))
        usd = int(re.sub('[^0-9]','', l[1]))
    if 'to' in amount and 'up to' not in amount:
        l = amount.split('to')
        usd = int(re.sub('[^0-9]','', l[0]))
    if '€' in amount or 'eur' in amount:
        usd = usd*1.07
    if '£' in amount or 'gbp' in amount:
        usd = usd*1.23
    if 'a$' in amount or 'au$' in amount or 'aud' in amount:
        usd = usd*0.64
    return usd

def print_workshops():
    print('\n\n\n ---- Lists generated at: {:} ---- '.format(NOW))
    
    #create some counters for math and printing
    workshop_list.reverse()
    inactive_claimed = 0
    high_name = 'name'
    unclaimed = 0
    inactive = 0
    high_tip = 0
    tip_tot = 0
    claimed = 0
    day_tot = 0
    urgent = 0
    new = 0

    #print workshops objects with no name
    print('\nWorkshops on tuning board with no room:')
    for x in workshop_list:
        if x.name == ' ':
            print(' - Room ID: {:}, Pilot: <@{:}>'.format(x.id, x.pilot))
            workshop_list.remove(x)

    #print workshops with users that left
    print('\nWorkshops whose pilots have left:')
    for x in workshop_list:
        if x.user_alive == False:
            print(' - #{:}'.format(x.name))
            workshop_list.remove(x)

    #print workshops with failed !close
    print('\nWorkshops that failed to !close:')
    for x in workshop_list:
        if x.close_attempted == True:
            print(' - #{:}'.format(x.name))
            workshop_list.remove(x)
            
    #print unclaimed workshops older than two months to delete 
    print('\nWorkshops flagged for deletion:')
    for x in workshop_list:
        if x.run_days >= 60  and x.claimed == False:
            print(' - #{:}'.format(x.name))

    #print inactive but claimed workshops and increment counter
    print('\nWorkshops flagged as inactive (claimed):')
    for x in workshop_list:
        if x.active == False:
            inactive += 1
            if x.claimed == True:
                print(' - #{:}'.format(x.name))
                inactive_claimed += 1
    
    #print unclaimed workshops, varying formating based on if they have budget, tip, or both
    line_counter = 0
    print('\n**Unclaimed workshop list:**')
    for x in workshop_list:
        if x.claimed == False:
            entry='- #{:}: {:}'.format(x.name, x.cat)
            if x.budget != 'none':
                entry += ' | {:}'.format(x.budget)
            entry += ' | __{:}__'.format(x.commander)
            if x.tip != 0:
                entry += ' | :dollar: **TIP: {:.2f} $$** '.format(x.tip)
                #add tip to tip total
                tip_tot += x.tip
                if x.tip > high_tip:
                    high_tip = x.tip
                    high_name = x.name
            day_tot = day_tot + (x.runtime / days)
            if x.run_days < 7:
                entry += ' _(new)_'
                new += 1
                line_counter += 1
                unclaimed += 1
                print (entry)
            elif x.run_days <= 30:
                entry += ' _({:.0f} days)_'.format(x.run_days)
                line_counter += 1
                unclaimed += 1
                print (entry)
            elif x.run_days < 60:
                entry += ' _(> 1 month)_ `[URGENT]` :exclamation: '
                urgent += 1
                line_counter += 1
                unclaimed += 1
                print (entry)
            else:
                entry = ' - DELETE BEFORE POSTING {:} DELETE BEFORE POSTING '.format(x.name)
            if line_counter == 16:
                print('\n')
                line_counter = 0
        else:
            claimed += 1
    
    #print bounty report
    print('\n:dollar: **Workshop Bounty Board** :dollar: ')
    print('- **{:.2f} $$** total is available in unclaimed tips.'.format(tip_tot))
    print('- Highest bounty amount: **{:.2f} $$** in #{:}'.format(high_tip, high_name))

    #print tuner list to show tuner activity
    tuner_list.sort(key=lambda x: len(x.active_workshops), reverse=True)
    print('\n**Tuner Activity in {:} claimed workshops:**'.format(claimed))
    for y in tuner_list:
        print('- <@{:}>: {:} active workshops. ({:.2f}%) AVG Time: {:.0f} days.'.format(y.get_id(), len(y.active_workshops), 100*(len(y.active_workshops)/claimed), (y.runtime/len(y.active_workshops))/days))

    #find active workshop count and latest unclaimed shop number for maths
    tot = len(workshop_list)
    newest_shop = workshop_list.pop()
    alltime_tot = int(newest_shop.name.replace('workshop-', ''))
    
    #do and print maths
    print('\n\n**Workshop Stats:**')
    print('- There are {:} open workshops, and {:} ({:.2f}%) of them are unclaimed.'.format(tot, unclaimed, 100*(unclaimed/tot)))
    print('- Unclaimed workshops have been open for an average of {:.0f} days (approx {:.0f} months).'.format((day_tot/unclaimed), ((day_tot/30)/unclaimed)))
    print('- {:} unclaimed workshops were created more than 30 days ago. ({:.2f}%)'.format(urgent, 100*(urgent/unclaimed)))
    print('- {:} unclaimed workshops were made in the past 7 days. ({:.2f}%)'.format(new, 100*(new/unclaimed)))
    print('- {:} total workshops have have been inactive for more than 20 days. ({:.2f}%)'.format(inactive, 100*(inactive/tot)))
    print('- {:} of inactive workshops that have been claimed by a tuner already. ({:.2f}%)'.format(inactive_claimed, 100*(inactive_claimed/inactive)))
    print('- {:} total workshop requests received; {:} of all-time workshops have been closed. ({:2f}%) '.format(alltime_tot, alltime_tot - tot, 100*((alltime_tot - tot)/alltime_tot) ))

if __name__ == '__main__':
    retrieve_channels(decktuner)
    print_workshops()
    
