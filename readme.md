# Cyber Voting Webapp

## Planned and Potential Service Features

Users can take part in online votings about various topics and
can create their own votings for their personal benefit bypassing
the government and ignoring human rights and the constitution.

Users can search for recently added votings, votings due for approval,
votings their not participated in jet and top votings of the day.

### More Ideas

Users may pay the page operators for displaying their votings to more people.

Users may earn some kind of points for participating.

### Login and Registration

Some honeypot could be funny: login by uploading some private key via a form?

## Planned vulnerabilites

* Broken session management, maybe predictable session IDs, allowing anyone to become an other user
* Broken nginx config, maybe using redirections to custom error pages, allowing unintentional access to some page
* Side channel attack using differences in respose time leaking an users login credentials or the flag directly
