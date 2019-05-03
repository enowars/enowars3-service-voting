# Cyber Voting Webapp

Working on this: lig.red // Lito Goldmann

## Planned and Potential Service Features

Users can take part in online votings about various topics and
can create their own votings for their personal benefit bypassing
the government and ignoring human rights and the constitution.

Users can search for recently added votings, votings due for approval,
votings their not participated in jet and top votings of the day.

### More Ideas

Users may pay the page operators for displaying their votings to more people.

Users may earn some kind of points for participating.

## Planned vulnerabilites

* Predictable session IDs, allowing anyone to become an any user
* Broken nginx config, allowing unintentional access to some log file leaking flags
* (PoC missing) Side channel attack using differences in respose time leaking an users login credentials
