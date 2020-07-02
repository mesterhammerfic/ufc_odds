import pandas as pd


def split(fighter_index, value):
    if type(value) != str:
        return value

    split_string = value.split(' ')
    length = len(split_string)
    if  length > 1:
        if fighter_index == 0:
            fighter_0_stats = split_string[:int(length/2)]
            return ' '.join(fighter_0_stats)
        elif fighter_index == 1:
            fighter_1_stats = split_string[int(length/2):]
            return ' '.join(fighter_1_stats)
    else:
        return value

def format_stats_table(df):
    """
    input: dataframe of stats table from ufc stats.com
    output: dataframe with column names fixed and round column added.
    """
    df['round'] = df.index+1

    new_columns = [column[0] for column in df.columns]
    new_columns = [column.strip() for column in new_columns]
    new_columns = [column.replace(' ', '_') for column in new_columns]
    new_columns = [column.replace('%', 'prcnt') for column in new_columns]
    new_columns = [column.replace('.', '') for column in new_columns]
    new_columns = [column.lower() for column in new_columns]
    df.columns = new_columns
    return df
