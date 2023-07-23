import requests
import json
import datetime
import re

auth = 'my auth code is mine and you cannot have it; get your own and put it here'
decktuner = 'decktuner channel ID'
unclaimed_ids = []
user_left_ids = []
workshop_list = []

class WORKSHOP:
    def __init__(self, raw):
        self.raw = raw
        self.name = " "
        self.user_alive = True
        self.active = True
        self.claimed = True
        self.new = False
        self.urgent = False
        self.deconstruct(raw)
    def killuser (self):
        self.user_alive = False
    def deactivate (self):
        self.active = False
    def flag_new (self):
        self.new = True
    def flag_urgent (self):
        self.urgent = True
    def deconstruct(self, raw):
        raw = raw.replace("\"", "\'")
        try:
            #get the id
            tmp_id = re.search("<#.*?>", raw).group()
            self.id = str(tmp_id[2:-1])

            #get the timestamp
            tmp_stamp = re.search("'timestamp': '.*?',", raw).group()
            self.stamp = str(tmp_stamp[14:-2])
            self.stamp = datetime.datetime.fromisoformat(self.stamp).timestamp()

            #get the budget
            tmp_budget = re.search("Budget', 'value': '.*?',", raw).group()
            self.budget =  str(tmp_budget[19:-2]).lower()
            if self.budget == "no budget":
                self.budget = "none"

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
                print (e)
                self.tip = 0

            #get the pilot
            tmp_pilot = re.search("Pilot', 'value': '<@.*?>',", raw).group()
            self.pilot = str(tmp_pilot[20:-3])
      
            print("\nNEW WORKSHOP:", raw)
        except Exception as e:
            print("\n Error in workshop: {:} \n {:}".format(e, raw))

def retrieve_messages(channel_ID, amount):
    headers={
        "authorization" : auth
    }
    r = requests.get("https://discord.com/api/v9/channels/{:}/messages?limit={:}".format(channel_ID, amount), headers=headers)
    message_raw = json.loads(r.text)
    return message_raw

def retrieve_channels(server_ID):
    headers={
        "authorization" : auth
    }
    r = requests.get("https://discord.com/api/v9/guilds/{:}/channels".format(server_ID), headers=headers)
    channel_raw = json.loads(r.text)
    #time info put outside of loop to increase scope
    check_time_stamp = datetime.datetime.now().timestamp()
    days = 86400
    for x in channel_raw:
        #check tuning boards for inactive workshops first
        if "tuning-board" in x["name"]:
            for y in retrieve_messages(x["id"], 100):
                #deconstruct raw message data from turning board into a workshop element and append it to the workshop list
                workshop_list.append(WORKSHOP(str(y["embeds"])))
                #get recent messages from tuning boards
                info = str(y["embeds"])
                tmp_id = re.search("<#.*?>", info).group()
                if "'name': 'Tuners', 'value': '*none*'" in str(y["embeds"]):
                    unclaimed_ids.append(str(tmp_id[2:-1])) #remove the <# and >
                    print("{:} appended to unclaimed IDs".format(tmp_id[2:-1]))
        #check spam logs for users that left
        if "spam-logs" in x["name"]:
            spam_messages = retrieve_messages(x["id"], 100)
            for y in spam_messages:
                spam_raw = str(y["embeds"])
                if "Member left" in spam_raw:
                    tmp_left_id = re.search("<@.*?>", spam_raw).group()
                    real_left_id = str(tmp_left_id[2:-1])
                    user_left_ids.append(real_left_id)
                    print("User {:} has left the server.".format(real_left_id))
    for x in channel_raw:
        #check workshop lists
        if "workshop" in x["name"]:
            #find workshop in list and set the name
            for y in workshop_list:
                if y.id == x["id"]:
                    y.name = x["name"]
            try:
                #find the workshop in the workshop list
                for y in workshop_list:
                    if y.id == x["id"]:
                        if y.pilot in user_left_ids:
                            #if pilot left, kill user
                            y.killuser()
                            print("Workshop {:} killed".format(x["id"]))
                        if y.id in unclaimed_ids:
                            #if id unclaimed, set unclaimed
                            y.claimed = False
                            print("Append {:} to unclaimed - ID match: {:}".format(x["name"], x["id"]))#check timestamp
                recent_activity = retrieve_messages(x["id"], 1)
                #check the messages timestamp and compare to now()
                for y in recent_activity:
                    message_time = datetime.datetime.fromisoformat(y["timestamp"]).timestamp()
                    if check_time_stamp - message_time > 20*days:
                        for z in workshop_list:
                            if z.id == x["id"]:
                                z.deactivate()
                #check the workshop creation 
                for z in workshop_list:
                    if check_time_stamp - z.stamp < 7*days:
                        z.flag_new()
                    if check_time_stamp - z.stamp > 20*days:
                        z.flag_urgent()
            except Exception as e:
                print("Error for {:}: {:}.".format(x["name"], e))

def cash(amount):
    #convert a string representing a cash amount into us'
    usd = int(re.sub('[^0-9]','', amount))
    amount = amount.lower()
    print(usd)
    if "-" in amount:
        l = amount.split("-")
        usd = int(re.sub('[^0-9]','', l[0]))
    if "to" in amount and "up to" not in amount:
        l = amount.split("to")
        usd = int(re.sub('[^0-9]','', l[0]))
    if "€" in amount or "eur" in amount:
        usd = usd*1.07
    if "£" in amount or "gbp" in amount:
        usd = usd*1.23
    return usd

def print_workshops():
    #create some counters for math and printing
    workshop_list.reverse()
    inactive_claimed = 0
    unclaimed = 0
    inactive = 0
    high_tip = 0
    high_name = "name"
    tip_tot = 0
    urgent = 0
    new = 0

    #print workshops with users that left
    print("\nWorkshops Whose Pilots Have Left:")
    for x in workshop_list:
        if x.user_alive == False:
            print(" - #{:}".format(x.name))

    #print inactive but claimed workshops and increment counter
    print("\nInactive (claimed) Workshops:")
    for x in workshop_list:
        if x.active == False:
            inactive += 1
            if x.claimed == True:
                print(" - #{:}".format(x.name))
                inactive_claimed += 1

    #print unclaimed workshops, varying formating based on if they have budget, tip, or both
    line_counter = 0
    print("\nUnclaimed Workshops:")
    for x in workshop_list:
        if x.claimed == False:
            entry="- #{:}: {:}".format(x.name, x.cat)
            if x.budget != "none":
                entry += " | {:}".format(x.budget)
            entry += " | __{:}__".format(x.commander)
            if x.tip != 0:
                entry += " | :dollar: **TIP: {:.2f} $$** ".format(x.tip)
                #add tip to tip total
                tip_tot += x.tip
                if x.tip > high_tip:
                    high_tip = x.tip
                    high_name = x.name
            if x.new == True:
                entry += " _(new)_"
                new += 1
            if x.urgent == True:
                entry += " `[URGENT]` :exclamation: "
                urgent += 1 
            line_counter += 1
            unclaimed += 1
            print (entry)
            if line_counter == 20:
                print("\n")
                line_counter = 0
    #print bounty report
    print("\n:dollar: **Workshop Bounty Board** :dollar: ")
    print("- **{:.2f} $$** total is available in unclaimed tips.".format(tip_tot))
    print("- Highest bounty amount: **{:.2f} $$** in #{:}".format(high_tip, high_name))

    #find active workshop count and latest unclaimed shop number for maths
    tot = len(workshop_list)
    newest_shop = workshop_list.pop()
    alltime_tot = int(newest_shop.name.replace("workshop-", ""))
    
    #do and print maths
    print("\n\nThere are {:} open workshops, and {:} ({:.2f}%) of them are unclaimed.".format(tot, unclaimed, 100*(unclaimed/tot)))
    print("- {:} ({:.2f}%) unclaimed workshops were created more than 30 days ago.".format(urgent, 100*(urgent/unclaimed)))
    print("- {:} ({:.2f}%) unclaimed workshops were made in the past 7 days.".format(new, 100*(new/unclaimed)))
    print("- {:} ({:.2f}%) total workshops have have been inactive for more than 20 days.".format(inactive, 100*(inactive/tot)))
    print("- {:} ({:.2f}%) of inactive workshops that have been claimed by a tuner already.".format(inactive_claimed, 100*(inactive_claimed/inactive)))
    print("- {:} total workshop requests received; {:} ({:.2f}%) of all-time workshops have been closed.".format(alltime_tot, alltime_tot - tot, 100*((alltime_tot - tot)/alltime_tot) ))


if __name__ == "__main__":
    retrieve_channels(decktuner)
    print_workshops()
