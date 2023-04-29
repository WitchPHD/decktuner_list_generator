import requests
import json
import datetime
import re

auth = "your authenticator key here"
decktuner = "decktuner guild id here"
unclaimed_ids = ["000","000"]
user_left_ids = ["000","000"]

class WORKSHOP:
    def __init__(self, id, cat, bud, cmdr, tip, pilot):
        self.id = id
        self.cat = cat
        self.budget = bud
        self.commander = cmdr
        self.name = " "
        self.tip = tip
        self.pilot = pilot
        self.user_alive = True
        self.active = True
        self.claimed = True
    def killuser (self):
        self.user_alive = False

        
workshop_list = [WORKSHOP(101, "casual", "100$", "Sheoldred", "100$", "Witch"), WORKSHOP(101, "casual", "100$", "Jin Gitaxias", "100$", "Witch")]


def retrieve_messages(channel_ID, amount):
    headers={
        "authorization" : auth
    }
    r = requests.get("https://discord.com/api/v9/channels/{:}/messages?limit={:}".format(channel_ID, amount), headers=headers)
    message_raw = json.loads(r.text)
    return message_raw

def deconstruct_workshop(raw_text):
    raw_text = raw_text.replace("\"", "\'")
    print("\n", raw_text)
    try:
        #get the id
        tmp_id = re.search("<#.*?>", raw_text).group()
        real_id = str(tmp_id[2:-1])
    except:
        real_id = "Error"
    print("\n ID:", real_id)
    try:
        #get the budget
        tmp_budget = re.search("Budget', 'value': '.*?',", raw_text).group()
        real_budget =  str(tmp_budget[19:-2]).lower()
        if real_budget == "no budget":
            real_budget = "none"
    except:
        real_budget = "Error"
    print("\n Budget:", real_budget)
    try:
        #get the catagory
        tmp_cat = re.search("Category', 'value': '.*?',", raw_text).group()
        real_cat = str(tmp_cat[21:-2]).lower()
    except:
        real_cat = "Error"
    print("\n Catagory:", real_cat)
    try:
        #get the commander
        tmp_cmdr = re.search("title': '.*?',", raw_text).group()
        real_cmdr = str(tmp_cmdr[9:-2])
    except:
        real_cmdr = "Error"
    print("\n Commmander:", real_cmdr)
    try:
        #get the tip (not in practice yet)
        tmp_tip = "none"
        real_tip = "none"
    except:
        real_tip = "Error"
    print("\n Tip:", real_tip)
    try:
        #get the pilot
        tmp_pilot = re.search("Pilot', 'value': '<@.*?>',", raw_text).group()
        real_pilot = str(tmp_pilot[20:-3])
    except:
        real_pilot = "Error"
    print("\n Pilot:", real_pilot)

    #take all the deconstructed data and return a workshop element to be added to workshop list
    return WORKSHOP(real_id, real_cat, real_budget, real_cmdr, real_tip, real_pilot)

def retrieve_channels(server_ID):
    headers={
        "authorization" : auth
    }
    r = requests.get("https://discord.com/api/v9/guilds/{:}/channels".format(server_ID), headers=headers)
    channel_raw = json.loads(r.text)
    #time info put outside of loop to increase scope
    check_time_stamp = datetime.datetime.now().timestamp()
    twenty_days = 86400*20
    for x in channel_raw:
        #check tuning boards for unclaimed workshops first
        if "tuning-board" in x["name"]:
            for y in retrieve_messages(x["id"], 100):
                #deconstruct raw message data from turning board into a workshop element and append it to the workshop list
                workshop_list.append(deconstruct_workshop(str(y["embeds"])))
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
                    if check_time_stamp - message_time > twenty_days:
                        for z in workshop_list:
                            if z.id == x["id"]:
                                z.active = False
            except:
                print("Error for {}.".format(x["name"]))

#retrieve_messages(decktuner)
retrieve_channels(decktuner)


#remove the praetor sample WORKSHOP elements and create some counters
workshop_list.reverse()
for x in range(2): workshop_list.pop()
inactive = 0
unclaimed = 0
inactive_claimed = 0


#print workshops with users that left
print("\nWorkshops Whose Pilots Have Left:")
for x in workshop_list:
    if x.user_alive == False:
        print(" - #{:}".format(x.name))


#print inactive but claimed workshops and increment counter
print("\nInactive Workshops:")
for x in workshop_list:
    if x.active == False:
        inactive += 1
        if x.claimed == True:
            print(" - #{:}".format(x.name))
            inactive_claimed += 1

#print unclaimed workshops, varying formating based on if they have budget, tip, or both
print("\nUnclaimed Workshops:")
num = 0
for x in workshop_list:
    if x.claimed == False:
        if x.budget != "none" and x.tip != "none":
            print(" - #{:}: {:} | {:} | __{:}__ | **TIP: {:}**".format(x.name, x.cat, x.budget, x.commander, x.tip))
        elif x.budget != "none":
            print(" - #{:}: {:} | {:} | __{:}__".format(x.name, x.cat, x.budget, x.commander))
        elif x.tip != "none":
            print(" - #{:}: {:} | __{:}__ | **TIP: {:}**".format(x.name, x.cat, x.commander, x.tip))
        else:
            print(" - #{:}: {:} | __{:}__".format(x.name, x.cat, x.commander))
        num += 1
        unclaimed += 1
        if num == 20:
            print("\n")
            num = 0

#find active workshop count and latest unclaimed shop number for maths
tot = len(workshop_list)
newest_shop = workshop_list.pop()
alltime_tot = int(newest_shop.name.replace("workshop-", ""))

#do and print maths
print("\n\nThere are {:} open workshops:".format(tot))
print(" - {:} ({:.2f}%) of them are unclaimed.".format(unclaimed, 100*(unclaimed/tot)))
print(" - {:} ({:.2f}%) have been inactive for more than 20 days.".format(inactive, 100*(inactive/tot)))
print(" - {:} ({:.2f}%) are inactive workshops that have been claimed by a tuner already.".format(inactive_claimed, 100*(inactive_claimed/tot)))
print(" - {:} total workshop requests received; {:} ({:.2f}%) of requests completed.".format(alltime_tot, alltime_tot - tot, 100*((alltime_tot - tot)/alltime_tot) ))
