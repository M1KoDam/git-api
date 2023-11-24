import requests
import pandas as pd


class GitAPIAccess:
    def __init__(self, username, token):
        self.TOKEN = token
        self.username = username
        self.repos = {}

        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

    def get_response_limit(self):
        """Показывает сколько запросов осталось"""
        response = requests.get('https://api.github.com/user', auth=(self.username, self.TOKEN))
        if response.status_code != 200:
            print("Response Error!")
            return None

        keys = []
        values = []
        for h in response.headers:
            if 'RateLimit' in h:
                keys.append(h)
                values.append(response.headers[h])

        return pd.Series(values, index=keys)

    def get_most_active_authors(self, org_name):
        """Возвращает таблицу Pandas с авторами"""
        org_repos = self.get_org_repos(org_name)['name']
        contributors = {}
        for repos in org_repos:
            response = requests.get(f"https://api.github.com/repos/{org_name}/{repos}/commits",
                                    auth=(self.username, self.TOKEN),
                                    params={'page': 1, 'per_page': 1000})
            if response.status_code != 200:
                print(f"Response Error on {repos} repository! It might be empty.")
                continue
            for i in response.json():
                name = i['commit']['author']['name']
                email = i['commit']['author']['email']
                if "[bot]" in name:
                    continue

                if (name, email) not in contributors.keys():
                    contributors[(name, email)] = 1
                else:
                    contributors[(name, email)] += 1

        contributors = {k: v for k, v in sorted(contributors.items(), key=lambda item: item[1], reverse=True)}
        pandas_dict = {"author": [], "email": [], "commits_count": []}
        for contributor_info, commits_count in contributors.items():
            pandas_dict["author"].append(contributor_info[0])
            pandas_dict["email"].append(contributor_info[1])
            pandas_dict["commits_count"].append(commits_count)

        return pd.DataFrame(pandas_dict).head(100)

    def make_repos_response(self, url_repos, name):
        """Делает запрос и возвращает таблицу Pandas с репозиториями"""
        if name in self.repos.keys():
            return self.repos[name]

        response_url = url_repos + "?page={1}&per_page={1}00"
        repos = {'name': [], 'private': [], 'created_at': []}
        data = []
        cur_page = 1
        while True:
            response = requests.get(response_url.format(name, cur_page), auth=(self.username, self.TOKEN))
            if response.status_code != 200:
                print("Response Error!")
                return None
            response_data = response.json()
            if len(response_data) == 0:
                break

            data += response_data
            cur_page += 1

        for repo in data:
            for key in repo.keys():
                if key in repos.keys():
                    repos[key].append(repo[key])

        pandas_repos = pd.DataFrame(repos)
        self.repos[name] = pandas_repos
        return pandas_repos

    def get_user_repos(self):
        """Возвращает Pandas таблицу репозиториев пользователя"""
        url_user = "https://api.github.com/users/{0}/repos"
        return self.make_repos_response(url_user, self.username)

    def get_org_repos(self, org_name):
        """Возвращает Pandas таблицу репозиториев организации"""
        url_org = "https://api.github.com/orgs/{0}/repos"
        return self.make_repos_response(url_org, org_name)


def main():
    username = 'M1KoDam'
    TOKEN = 'xxxxxxxxxx'  # your github token
    org = "Netflix"

    git_api = GitAPIAccess(username, TOKEN)

    print(f"Top 100 authors of {org} organization:")
    print(git_api.get_most_active_authors(org))
    print("\n")

    print(f"Repositories of {username}:")
    print(git_api.get_user_repos())
    print("\n")

    print(f"Repositories of {org} organization:")
    print(git_api.get_org_repos(org))
    print("\n")

    print(f"Response limit:")
    print(git_api.get_response_limit())


if __name__ == "__main__":
    main()
