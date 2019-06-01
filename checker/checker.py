from enochecker import *
import secrets
import random
import string
import urllib

def generate_content(amount):
    return "".join(random.choice(string.ascii_letters + string.digits + " ") for _ in range(amount))

def generate_content_no_whitespace(amount):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(amount))

class VotingChecker(BaseChecker):
    port = 80

    def putflag(self) -> None:

        # TODO generate fake user content
        user = generate_content_no_whitespace(random.randint(8, 32))
        password = secrets.token_hex(24)
        title = generate_content(random.randint(5, 48))
        description = generate_content(random.randint(6, 128))

        # register
        for i in range(6):  # try to find an unique username up to 5 times
            if i == 5:
                raise BrokenServiceException("usernames already used")

            response = self.http_post(route="/register.html", data={"user": user, "password": password},
                                      allow_redirects=False)

            if response.status_code != 302:
                if "Username already exists" in response.text:
                    user = generate_content_no_whitespace(random.randint(8, 32))
                else:
                    raise BrokenServiceException("registration is broken")
            else:
                break

        # create vote
        response = self.http_post(route="/create.html",
                                  data={"title": title, "description": description, "notes": self.flag},
                                  allow_redirects=False)

        if response.status_code != 302:
            raise BrokenServiceException("create is broken")

        try:
            response_query = urllib.parse.parse_qs(urllib.parse.urlparse(response.headers["Location"]).query,
                                                   strict_parsing=True)
            vote_id = int(response_query.get("v")[0])
        except Exception:
            raise BrokenServiceException("create redirects wrong")

        self.team_db[self.flag] = (vote_id, user, password)

    def getflag(self) -> None:

        (vote_id, user, password) = self.team_db[self.flag]

        # login
        response = self.http_post(route="/login.html", data={"user": user, "password": password}, allow_redirects=False)

        assert_equals(302, response.status_code, "login failed")

        # get vote
        response = self.http_get(route="/vote.html", params={"v": vote_id})

        assert_equals(200, response.status_code, "get vote failed")
        assert_in(self.flag, response.text, "flag not found")

    def putnoise(self) -> None:

        # TODO generate fake user content
        user = generate_content_no_whitespace(random.randint(8, 32))
        password = secrets.token_hex(24)
        title = generate_content(random.randint(5, 48))

        # register
        for i in range(6):  # try to find an unique username up to 5 times
            if i == 5:
                raise BrokenServiceException("usernames already used")

            response = self.http_post(route="/register.html", data={"user": user, "password": password},
                                      allow_redirects=False)

            if response.status_code != 302:
                if "Username already exists" in response.text:
                    user = generate_content_no_whitespace(random.randint(8, 32))
                else:
                    raise BrokenServiceException("registration is broken")
            else:
                break

        # create vote
        response = self.http_post(route="/create.html",
                                  data={"title": title, "description": self.flag, "notes": ""},
                                  allow_redirects=False)

        if response.status_code != 302:
            raise BrokenServiceException("create is broken")

        try:
            response_query = urllib.parse.parse_qs(urllib.parse.urlparse(response.headers["Location"]).query,
                                                   strict_parsing=True)
            vote_id = int(response_query.get("v")[0])
        except Exception:
            raise BrokenServiceException("create redirects wrong")

        self.team_db[self.flag + str(self.flag_idx)] = vote_id

    def getnoise(self) -> None:

        vote_id = self.team_db[self.flag + str(self.flag_idx)]

        # get vote
        response = self.http_get(route="/vote.html", params={"v": vote_id})

        assert_equals(200, response.status_code, "get vote failed")
        assert_in(self.flag, response.text, "noise not found")

    def havoc(self) -> None:

        # check "/" returns a permanent redirect to "/index.html"
        response = self.http_get(route="/", allow_redirects=False)
        assert_equals(301, response.status_code, "'/' broken")
        assert_equals("/index.html", urllib.parse.urlparse(response.headers["Location"]).path, "'/' broken")

        # check "/index.html"
        response = self.http_get(route="/index.html", allow_redirects=False)
        assert_equals(200, response.status_code, "'/index.html' broken")

        # check "/vote.html" for most recent vote found (if any)
        vote_link_start = response.text.find('href="/vote.html?v=')
        if vote_link_start > 0:
            vote_link_end = response.text.find('"', vote_link_start + len('href="/vote.html?v='))
            vote_id = response.text[vote_link_start + len('href="/vote.html?v='):vote_link_end]

            self.info("Parsed vote id: {}".format(vote_id))

            # check most recent vote reachable
            response = self.http_get(route="/vote.html", params={"v": vote_id}, allow_redirects=False)
            assert_equals(200, response.status_code, "'/vote.html' broken")

            # check vote created by
            user_start = response.text.find("<p>Vote created by: ")
            if user_start > 0:
                user_end = response.text.find("</p>", user_start + len("<p>Vote created by: "))
                parsed_user = response.text[user_start + len("<p>Vote created by: "):user_end]

                self.info("Parsed user: {}".format(parsed_user))
            else:
                raise BrokenServiceException("'/vote.html' created by broken")

            # check 404 for unused vote id
            response = self.http_get(route="/vote.html", params={"v": str(int(vote_id) + 1)}, allow_redirects=False)
            assert_equals(404, response.status_code, "'/vote.html' broken")

        # check "/login.html" reachable
        response = self.http_get(route="/login.html", allow_redirects=False)
        assert_equals(200, response.status_code, "'/login.html' broken")

        # login as parsed user with stupid passwords
        if "parsed_user" in locals():
            self.http_post(route="/login.html", data={"user": parsed_user, "password": ""}, allow_redirects=False)
            assert_equals(200, response.status_code, "'/login.html' broken")
            self.http_post(route="/login.html", data={"user": parsed_user, "password": " "}, allow_redirects=False)
            assert_equals(200, response.status_code, "'/login.html' broken")
            self.http_post(route="/login.html", data={"user": parsed_user, "password": "123"}, allow_redirects=False)
            assert_equals(200, response.status_code, "'/login.html' broken")

        # login with some stupid passwords
        self.http_post(route="/login.html", data={"user": "Admin", "password": "default"}, allow_redirects=False)
        self.http_post(route="/login.html", data={"user": "Admin", "password": "1234"}, allow_redirects=False)
        self.http_post(route="/login.html", data={"user": "Admin", "password": "123456"}, allow_redirects=False)
        self.http_post(route="/login.html", data={"user": "Admin", "password": ""}, allow_redirects=False)
        self.http_post(route="/login.html", data={"user": "", "password": ""}, allow_redirects=False)
        self.http_post(route="/login.html", data={"user": " ", "password": " "}, allow_redirects=False)

        # check "/register.html" reachable
        response = self.http_get(route="/register.html", allow_redirects=False)
        assert_equals(200, response.status_code, "'/register.html' broken")

        # register
        user = generate_content_no_whitespace(random.randint(8, 32))
        password = secrets.token_hex(24)

        for i in range(6):  # try to find an unique username up to 5 times
            if i == 5:
                raise BrokenServiceException("usernames already used")

            response = self.http_post(route="/register.html", data={"user": user, "password": password},
                                      allow_redirects=False)

            if response.status_code != 302:
                if "Username already exists" in response.text:
                    user = generate_content_no_whitespace(random.randint(8, 32))
                else:
                    raise BrokenServiceException("registration is broken")
            else:
                break

        # check auth'ed "/index.html"
        response = self.http_get(route="/index.html", allow_redirects=False)
        assert_equals(200, response.status_code, "'/index.html' broken")
        assert_in("<span>Welcome, {}!</span>".format(user), response.text, "'/index.html' broken")

        # logout
        response = self.http_post(route="/logout.html", allow_redirects=False)
        assert_equals(302, response.status_code, "'/logout.html' broken")
        assert_equals("/index.html", urllib.parse.urlparse(response.headers["Location"]).path, "'/logout.html' broken")

        response = self.http_get(route="/index.html", allow_redirects=False)
        assert_equals(200, response.status_code, "'/index.html' broken")
        if "<span>Welcome, {}!</span>".format(user) in response.text:
            raise BrokenServiceException("'/index.html' broken")

        # TODO create votes, vote

    def exploit(self) -> None:
        # TODO
        pass


app = VotingChecker.service

if __name__ == "__main__":
    run(VotingChecker)
