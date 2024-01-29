GLOSSARY = {
    "cbf": "Correlator Beam Former",
    "csp": "Central Signal Processor",
    "tmc": "Telescope Monitor and Control",
}

THESAURUS = {
    "csp": """
The Central Signal Processing (CSP) MID is an integrated real-time digital back-end 
for the MID Telescope. It receives astronomical signals coming from 133 
MID-Receptors and 64 MeerKAT-Receptors in the frequency range from 350Mhz up to 
13,8 Ghz in 5 different bands and produces in output visibility for each baseline 
and for each channel and each polarization product. Moreover it generates tied 
array beams and for each of it the time domain processor generates pulsar 
candidates, pulsar profiles, single short duration pulse detect. The CSP-MID also 
generates up to 4 VLBI tided array beams. It can support several observing mode 
commensally, in particular imaging and time domain processing. It consists of high
performance digital hardware and software for real-time processing."""
}


def get_ska_jargon(abbrev: str) -> str:
    """
    Look up acronym

    :param abbrev: multi letter acronym
    :return: meaning of acronym
    """
    try:
        rv = f"{GLOSSARY[abbrev.lower()]} ({abbrev.upper()})"
    except KeyError:
        rv = f"UNDEFINED ({abbrev.upper()})"
    return rv
