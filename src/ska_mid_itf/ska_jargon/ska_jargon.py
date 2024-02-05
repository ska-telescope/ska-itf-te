GLOSSARY = {
    "cbf": "Correlator Beam Former",
    "csp": "Central Signal Processor",
    "ds": "Device Server",
    "elt": "Element",
    "fs": "Frequency Slice",
    "fsp": "Frequency Slice Processor",
    "lmc": "Local Monitor and Control",
    "lru": "Line Replaceable Unit",
    "oso": "Observatory Science Operations",
    "pst": "Pulsar timing",
    "pss": "Pulsar Search",
    "sdp": "Science Data Processing",
    "spf": "Single Pixel Feed",
    "spfc": "Single Pixel Feed Controller",
    "spfrx": "Single Pixel Feed Receiver",
    "tm": "Telescope Manager",
    "tmc": "Telescope Monitor and Control",
    "vcc": "Very Coarse Channelizer",
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
performance digital hardware and software for real-time processing.""",
    "lru": """
A product that may be replaced using procedures, skills, tools and facilities available
 on site, i.e. without the removal of a higher level product that incorporates it.""",
    "oso": """A suite of software tools that performs Observation execution. This is 
done either from a Scheduling Block or using low-level scripting functions e.g. from a
Jupyter Notebook. This aspect of operations is relevant to both execution of PI science
and observatory operations such as commissioning and calibration.""",
    "sdp": """
Computing system (both hardware and software) dedicated to producing science data 
products from observations. Housed in a Science Data Processing Facility. See 
Introduction , Module Decomposition and Dependency View Science Data Processor 
consortium. The SDP is a Consortium made up of astrophysicists, engineers and 
computer scientists mostly work for universities and research institutes which 
produced the design of the SDP system that passed the critical design review in 
Jan 2019 See: Consortium""",
    "tm": """
The telescope manager integrates operationally all the engineering entities in the 
system to form the telescope device, with a set of capabilities and behaviours. Its 
core functionality is coordination, monitoring, control and engineering lifecycle 
support for the entities to work together as a single instrument that can conduct 
observations. Can also refer to the Telescope Manager pre-construction consortium""",
    "pss": """
Pulsar Search is defined to mean the complete digital signal processing for detecting 
pulsars and transients. This includes, but is not limited to: Beam-forming of tied-
array beams at specified sky locations over a specified continuous bandwidth. 
Channelisation and temporal averaging of beamformed data to a specified number of 
channels and sampling interval. Averaging/correlating polarisation beams to form Stokes
vectors. De-dispersion of beamformed data at specified dispersion measures, to produce 
de-dispersed time-series. Detection of individual pulses in the de-dispersed 
time-series. Detection of periodic signals in the de-dispersed time-series, including 
corrections for binary motion of pulsars over a specified range of accelerations. 
Selection of candidates. Output of Pulsar Candidates and Non-imaging Transient 
Candidates into the SKA archive.""",
    "pst": """
PST refers to both the pulsar timing signal processing engine, a component of the 
Central Signal Processor (CSP) and the name of the Data Processing (DP) Agile Release 
Train (ART) team that is primarily focused on developing the PST software.""",
    "vcc": """
The Very Coarse Channelizer (VCC) takes the digitised data from a dish and creates 
coarse channels that then can be sent to one or more Frequency Slice Processors 
(FSPs)."""
}


def print_jargon() -> None:
    """
    Print known jargon
    """
    for tla in GLOSSARY:
        print(f"{tla.upper():6} : {GLOSSARY[tla]}")


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


def find_jargon(inp: str) -> str:
    """
    Look for jargon inside
    :param input: string that potentially contains jargon
    :return: fully expanded acronyms
    """
    rv = ""
    for key in GLOSSARY:
        if key in inp:
            if rv:
                rv += f", {GLOSSARY[key]} ({key.upper()})"
            else:
                rv = f"{GLOSSARY[key]} ({key.upper()})"
        else:
            key2 = f"{key[0].upper}{key[1:]}"
            if key2 in inp:
                if rv:
                    rv += f", {GLOSSARY[key]} ({key.upper()})"
                else:
                    rv = f"{GLOSSARY[key]} ({key.upper()})"
    return rv
