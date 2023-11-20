import os, pprint
from yaml import safe_load, safe_dump

DISH_IDS = os.environ["DISH_IDS"]


def load_dishes():
    cur = os.path.dirname(os.path.abspath(__file__))
    with open(
        os.path.join(cur, "..", "..", "charts", "system-under-test", "tmc-values.yaml"),
        "r",
    ) as file:
        tmc_dishes = safe_load(file)
    return tmc_dishes


def instance(x):
    return x[-2:] if int(x[-3:]) < 100 else x[-3:]


def generate_instances(ids=DISH_IDS):
    # print(ids)
    ids = list(ids.split(" "))
    # instance = lambda x:
    instances = [instance(x) for x in ids]
    # print(instances)
    return instances


def single_dish_id_lowercase(id="SKA000"):
    return id.lower()


def generate_dish_ids_array_from_str(ids="SKA000"):
    return list(ids.split(" "))


def single_dish_fqdn(
    hostname="tango-databaseds",
    cluster_domain="miditf.internal.skao.int",
    namespace_prefix="dish-lmc-",
    dish_id="SKA000",
):
    id = single_dish_id_lowercase(id=dish_id)
    return f"tango://{hostname}.{namespace_prefix}{id}.svc.{cluster_domain}\
        :10000/{id}/elt/master"


tmc_dishes_1 = {
    "tmc": {
        "deviceServers": {
            "centralnode": {"DishIDs": generate_dish_ids_array_from_str(DISH_IDS)},
            "subarraynode": {"DishIDs": generate_dish_ids_array_from_str(DISH_IDS)},
            "dishleafnode": {"instances": generate_instances(DISH_IDS)},
        },
        "global": {
            "namespace_dish": {
                "dish_name": [
                    "tango://tango-databaseds.dish-lmc-ska001.svc.miditf.internal.skao.int:10000/ska001/elt/master",
                    "tango://tango-databaseds.dish-lmc-ska036.svc.miditf.internal.skao.int:10000/ska036/elt/master",
                    "tango://tango-databaseds.dish-lmc-ska063.svc.miditf.internal.skao.int:10000/ska063/elt/master",
                    "tango://tango-databaseds.dish-lmc-ska100.svc.miditf.internal.skao.int:10000/ska100/elt/master",
                ]
            }
        },
    }
}

tmc_dishes = load_dishes()

try:
    assert generate_dish_ids_array_from_str(DISH_IDS) == [
        "SKA001",
        "SKA036",
        "SKA063",
        "SKA100",
    ], f"Expected array of str:\n{['SKA001', 'SKA036', 'SKA063', 'SKA100']}"
    assert generate_dish_ids_array_from_str(ids="SKA000 SKA001") == [
        "SKA000",
        "SKA001",
    ], f"Expected array of str:\n{['SKA000', 'SKA001']}\nInstead received:\n \
        {generate_dish_ids_array_from_str(ids='SKA000 SKA001')}"
    assert (
        tmc_dishes["tmc"]["deviceServers"]["dishleafnode"]["instances"]
        == tmc_dishes_1["tmc"]["deviceServers"]["dishleafnode"]["instances"]
    ), f"ERROR:\nExpected:{tmc_dishes['tmc']['deviceServers']['dishleafnode']['instances']}\n \
        Actual:\n{tmc_dishes_1['tmc']['deviceServers']['dishleafnode']['instances']}"
    assert (
        tmc_dishes["tmc"]["deviceServers"]["dishleafnode"]["instances"]
        == tmc_dishes_1["tmc"]["deviceServers"]["dishleafnode"]["instances"]
    ), f"ERROR:\nExpected:{tmc_dishes['tmc']['deviceServers']['dishleafnode']['instances']}\n \
        Actual:\n{tmc_dishes_1['tmc']['deviceServers']['dishleafnode']['instances']}"
    assert (
        tmc_dishes == tmc_dishes_1
    ), f"Output not as expected: was expecting\n{tmc_dishes}\ninstead got\n{tmc_dishes_1}"
except:
    print("######## FROM FILE #######")
    pprint.pprint(tmc_dishes)
    print()
    print("######## FROM CODE #######")
    pprint.pprint(tmc_dishes_1)
