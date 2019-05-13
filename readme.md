# Cyber Voting Webapp

Working on this: lig.red // Lito Goldmann

## Service Features

Users can take part in online votings about various topics and
can create their own votings for their personal benefit bypassing
the government and ignoring human rights and the constitution.

## Planned vulnerabilites

* (Done) Predictable session IDs, allowing anyone to become an any user
* Broken nginx config, allowing unintentional access to some log file leaking flags
* (PoC missing) Side channel attack using differences in respose time leaking an users login credentials
