"""Smoke-test the saspy -> SAS OnDemand for Academics connection.

Usage (from judge/):  uv run python connect_check.py [profile]
profile defaults to 'oda' (US); see ~/.config/saspy/sascfg_personal.py.
Prints the SAS version and the session's home directory, so we know which
path to substitute for the scripts' hardcoded /home/u64352077.
"""

import sys

import saspy

profile = sys.argv[1] if len(sys.argv) > 1 else "oda"
sas = saspy.SASsession(cfgname=profile)
try:
    print("SAS version:", sas.sasver)
    result = sas.submit(
        """
        %put HOME=%sysget(HOME);
        %put SYSUSERID=&sysuserid;
        """
    )
    for line in result["LOG"].splitlines():
        if line.startswith(("HOME=", "SYSUSERID=")):
            print(line)
finally:
    sas.endsas()
