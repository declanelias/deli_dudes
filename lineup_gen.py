import pandas as pd
import pulp
from pulp import *
import random


class LineupGenerator(object):

    def __init__(self, hitter_df, pitcher_df, salary_cap):
        '''
        Initializes object to generate different lineups

        :param hitter_df: dataframe with columns 'Name', 'Position_{3-7}', 'Salary', 'Projection', 'Points'
        :param pitcher_df: dataframe with columns 'Name', 'Salary', 'Projection', 'Points'
        '''
        self.hitter_df = hitter_df
        self.pitcher_df = pitcher_df
        self.salary_cap = salary_cap

        self.salary_dict = {}
        self.projection_dict = {}
        self.points_dict = {}
        self.team_dict = {}

        self._create_dicts()

        self.pos_num_available = {
            "1B": 1,
            "2B": 1,
            "3B": 1,
            "SS": 1,
            "OF": 3,
            "P": 2
        }

    def get_optim_prediction_lineup(self):
        lineup = self._get_optim_lineup(self.projection_dict)
        return self._get_lineup_df(lineup)

    def get_optim_real_lineup(self):
        lineup = self._get_optim_lineup(self.points_dict)
        return self._get_lineup_df(lineup)

    def get_maxed_salaryLineup(self):
        lineup = self._get_optim_lineup(self.salary_dict)
        return self._get_lineup_df(lineup)

    def get_random_lineup(self):
        lineup = []
        positions = []
        salaries = []
        points = []
        projections = []

        for position in ['1B', '2B', '3B', 'SS', 'OF', 'P']:
            n = 1
            if position == 'P':
                n = 2
            if position == 'OF':
                n = 3

            for i in range(0, n):
                players = list(self.salary_dict.get(position).keys())
                player = random.choice(players)
                lineup.append(player)

                salaries.append(self.salary_dict[position][player])
                points.append(self.points_dict[position][player])
                projections.append(self.projection_dict[position][player])
                positions.append(position)

        total_salary = sum(salaries)
        if total_salary > self.salary_cap:
            lineup = self.get_random_lineup()

        data = {
            'Name' : lineup,
            'Position' : positions,
            'Salary' : salaries,
            'Points' : points,
            'Projections' : projections
        }

        return pd.DataFrame(data)


    def _get_lineup_df(self, lineup):
        df = pd.DataFrame(data=lineup, columns=["Name"])
        df['Position'] = df.Name.apply(lambda x: x[0] if x[0] == 'P' else x[0:2])
        df['Name'] = df.Name.apply(lambda x: x[2:] if x[0] == 'P' else x[3:])
        df['Salary'] = df.apply(lambda row: self.salary_dict[row.Position][row.Name], axis=1)
        df['Points'] = df.apply(lambda row: self.points_dict[row.Position][row.Name], axis=1)
        df['Projections'] = df.apply(lambda row: self.projection_dict[row.Position][row.Name], axis=1)
        return df

    def _get_optim_lineup(self, optim_dict):

        SALARY_CAP = self.salary_cap
        _vars = {k: LpVariable.dict(k, v, cat="Binary") for k, v in optim_dict.items()}

        prob = LpProblem("Fantasy", LpMaximize)
        rewards = []
        costs = []
        team_counts = Counter()

        for k, v in _vars.items():
            costs += lpSum([self.salary_dict[k][i] * _vars[k][i] for i in v])
            rewards += lpSum([optim_dict[k][i] * _vars[k][i] for i in v])
            prob += lpSum([_vars[k][i] for i in v]) <= self.pos_num_available[k]

            for player in v:
                team = self.team_dict.get(player)
                team_counts[team] += _vars[k][player]

        for team, count in team_counts.items():
            prob += count <= 4

        prob += lpSum(rewards)
        prob += lpSum(costs) <= SALARY_CAP

        prob.solve()

        players = []
        for v in prob.variables():
            if v.varValue != 0:
                players.append(v.name)
        return players

    def _create_dicts(self):
        position_dict = {'1B': 'position_3',
                         '2B': 'position_4',
                         '3B': 'position_5',
                         'SS': 'position_6',
                         'OF': 'position_7'}

        self.salary_dict = {}
        self.points_dict = {}
        self.projection_dict = {}
        for position in position_dict.keys():
            col = position_dict.get(position)
            pos_df = hitter_df[hitter_df[col]]
            self.salary_dict[position], self.points_dict[position], self.projection_dict[
                position] = self._create_dict_by_pos(pos_df)

        self.salary_dict['P'], self.points_dict['P'], self.projection_dict['P'] = self._create_dict_by_pos(pitcher_df)

        for index, row in hitter_df.iterrows():
            self.team_dict[row.Name] = row.Team
        for index, row in pitcher_df.iterrows():
            self.team_dict[row.Name] = row.Team

    def _create_dict_by_pos(self, df):
        salaries = {}
        points = {}
        projection = {}
        for index, row in df.iterrows():
            salaries[row['Name']] = row.Salary
            points[row['Name']] = row.Points
            projection[row['Name']] = row.Projection

        return salaries, points, projection


if __name__ == "__main__":
    hitter_df = pd.read_csv("../valid_df.csv")
    pitcher_df = pd.read_csv('../pitchers_df_cleaned.csv')

    pitcher_df = pitcher_df[pitcher_df.year == 2021]

    hitter_df = hitter_df[hitter_df.game_date == "2021-04-11"]
    pitcher_df = pitcher_df[pitcher_df.game_date == "2021-04-11"]

    hitter_df["Projection"] = hitter_df.dk_points
    hitter_df["Salary"] = hitter_df.dk_salary
    pitcher_df["Projection"] = pitcher_df.dk_points
    pitcher_df["Salary"] = pitcher_df.dk_salary

    pitcher_df.Name = pitcher_df.Name.str.replace(" ", "_")
    hitter_df.Name = hitter_df.Name.str.replace(" ", "_")

    hitter_df = hitter_df.dropna(subset=['Projection'])
    pitcher_df = pitcher_df.dropna(subset=['Projection'])


    def extract_team(value):
        return value.split('(')[0].strip()


    pitcher_df['Opp'] = pitcher_df['Opp'].str.replace('@', '').str.replace('v', '')
    pitcher_df['Opp'] = pitcher_df['Opp'].apply(extract_team)
    pitcher_df['Opp'] = pitcher_df['Opp'].apply(lambda x: x.upper())

    hitter_df['Opp'] = hitter_df['Opp'].str.replace('@', '').str.replace('v', '')
    hitter_df['Opp'] = hitter_df['Opp'].apply(extract_team)
    hitter_df['Opp'] = hitter_df['Opp'].apply(lambda x: x.upper())

    hitter_df['Points'] = hitter_df.dk_points
    pitcher_df['Points'] = pitcher_df.dk_points

    hitter_df['Salary'] = hitter_df.dk_salary
    pitcher_df['Salary'] = pitcher_df.dk_salary

    hitter_df = hitter_df[hitter_df['order'] != 'PH']

    h_gen_df = hitter_df[['Name', 'Projection', 'Salary', 'position_3',
                          'position_4', 'position_5', 'position_6', 'position_7', 'Points']]
    p_gen_df = pitcher_df[['Name', 'Projection', 'Salary', 'Points']]

    optim_lineup = LineupGenerator(h_gen_df, p_gen_df, 50000)
    print(optim_lineup.get_maxed_salaryLineup())
