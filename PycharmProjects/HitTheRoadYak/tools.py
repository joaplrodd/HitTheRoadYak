import sys
import pandas as pd
from lxml import etree
import numpy as np

# Globals
MAX_AGE_DAYS = 1000
MAX_AGE_YEARS = 10


# Definitions
def read_xml(file, tag):
    """
    Read the data from the xml file and store it in DataFrame
    :param file: file (path + name)
    :param tag:
    :return: DataFrame with yaks' data
    """
    df = pd.DataFrame(columns=["name", "age", "sex"])
    try:
        yaks = etree.parse(file).getroot()

        for yak in yaks.iter(tag):
            df = df.append(dict(yak.attrib), ignore_index=True)
    except Exception:
        sys.exit("Error: {0}".format(sys.exc_info()[0]))

    # Drop Nan
    df.dropna(inplace=True)
    # Convert data types
    df['name'] = df['name'].astype(str)
    df['sex'] = df['sex'].astype(str)
    df['age'] = df['age'].astype(float)
    df['age_days'] = df['age'].multiply(100).astype(int)
    df['last_shaved'] = df['age']


    return df


def create_order_df():
    """
    Initialize the sold logs DataFrame)
    :return: dataframe with dates and quantities of the sold goods
    """

    df_order = pd.DataFrame({"milk": [0.0], "skin": [0], "day": [0]})
    df_order['day'] = df_order['day'].astype(int)
    df_order['skin'] = df_order['skin'].astype(int)
    df_order['milk'] = df_order['milk'].astype(int)

    return df_order


def milk_per_elapsed_day(df, days):
    """
    Get quantity of milk at certain day in the future and update the yaks' data
    :param df: Yaks' data
    :param days: days that will go through
    :return: milk
    """
    milk = 0

    # Just alive female Yak produce milk
    df_milk = df['age_days'][(df['age_days'] < MAX_AGE_DAYS) & (df['sex'] == 'f')]

    for day in range(days):
        # Stop if all dead
        if df_milk.size == 0:
            break

        # Add milk
        milk += df_milk.map(lambda x: 50 - x * 0.03).sum()

        # Add day to age
        df_milk = df_milk.add(1)

        # Drop dead Yaks
        df_milk = df_milk[df_milk < MAX_AGE_DAYS]

    df['age_elapsed'] = (df['age'].add(0.01*days))

    return milk


def skin_per_elapsed_day(df, days):
    """
    Get quantity of skins at certain day in the future and update the yaks' data
    :param df:  Yaks' data
    :param days: days that will go through
    :return: skin quantity at that moment in time
    """
    skin = 0
    df_skin = pd.DataFrame()

    # yaks' age
    df_skin["age"] = df['age_days']

    # days accumulator
    df_skin["days"] = df['age_days'].multiply(0)

    # Elapse day offsets
    df_skin['last_shaved'] = df_skin['age'].sub(1)

    # Any dead Yaks??
    skin = df_skin[df_skin['age'] >= MAX_AGE_DAYS].values.sum()
    df_skin = df_skin[df_skin['age'] < MAX_AGE_DAYS]
    
    for day in range(days):
        # values filter
        can_shave = (df_skin["age"] < MAX_AGE_DAYS) & (df_skin['days'] < (days - 1))
        # Stop if all yaks are dead
        if can_shave.values.sum() == 0:
            break

        df_skin['last_shaved'] = np.where(can_shave,
                                          df_skin['days'],
                                          df_skin['last_shaved'])

        # Add skins
        skin += can_shave.values.sum()

        # Alter values for "next day"
        df_skin["days"] = df_skin['days'] + df_skin['age'].mul(0.01).add(8)
        df_skin["age"] = df_skin["age"].add(1)

    df['age_elapsed'] = (df['age'].add(0.01*days))
    df['last_shaved'] = df['age'] + df_skin['last_shaved'].mul(0.01)

    # Elapsed day offset
    df['last_shaved'] = np.where(df_skin['last_shaved'] != 0,
                                          df['last_shaved'].add(0.01),
                                          df['last_shaved'])
    return skin


def stock(df, T):
    """
    Obtain the amount of milk and skin of a specific day
    :param df: Yak DataFrame
    :param T: Day
    :return: Milk, Skin
    """
    return milk_per_elapsed_day(df, T), skin_per_elapsed_day(df, T)


def process_order(df, T, dfOrder, order):
    """
    Check the availability of the requested order and return the proper values
    :param df: Yak DataFrame
    :param T: Day of the order
    :param dfOrder: Already sold orders DataFrame
    :param order: Current order request
    :return: Amount of Milk and Skin that will be delivered pls the corresponding response code
    """
    calcMilk, calcSkin = stock(df, T)

    orderedMilk = float(order[0])
    orderedSkin = int(order[1])

    soldMilk = dfOrder[dfOrder['day'] <= T]['milk'].sum()
    soldSkin = dfOrder[dfOrder['day'] <= T]['skin'].sum()

    currentMilk = calcMilk - soldMilk
    currentSkin = calcSkin - soldSkin

    # Enough milk and skins
    if (orderedMilk <= currentMilk) and (orderedSkin <= currentSkin):
        dfOrder = dfOrder.append({'milk': orderedMilk, 'skin': orderedSkin, 'day': T}, ignore_index=True)
        return orderedMilk, orderedSkin, 201, dfOrder

    # Not enough of anything
    if (orderedMilk > currentMilk) and (orderedSkin > currentSkin):
        return '0', '0', 404, dfOrder

    # Not enough skin
    if orderedMilk <= currentMilk:
        dfOrder = dfOrder.append({'milk': orderedMilk, 'skin': 0, 'day': T}, ignore_index=True)
        return str(orderedMilk), "0", 206, dfOrder

    # Not enough milk
    else:
        dfOrder = dfOrder.append({'milk': 0, 'skin': orderedSkin, 'day': T}, ignore_index=True)
        return "0", str(orderedSkin), 206, dfOrder


def check_request(order):
    """
    Check the parameters of the requests
    :param order: list of milk, skin, day or dict milk, skin
    :return: True if everything is correct
    """
    try:
        if type(order) == list:
            milk = float(order[0])
            skin = int(order[1])
            day = int(order[2])
            if (milk <0) or (skin < 0) or (day < 0):
                return False
        else:
            milk = float(order['order']['milk'])
            skin = int(order['order']['skins'])
            if (milk <0) or (skin < 0):
                return False

    except:
        return False

    return True
