import os
import yaml
import json
import time
import argparse
from collections import defaultdict
from kafka import KafkaConsumer, KafkaProducer


def make_feature(geom):
    return {
        # 'type': 'Feature',
        'geometry': geom
    }


def make_linestring(coordinates):
    return {
        'type': 'LineString',
        'coordinates': coordinates,
        'crs': {
            'type': 'EPSG',
            'properties': {
                'code': 4326
            }
        }
    }


def make_point(coordinates):
    return {
        'type': 'Point',
        'coordinates': coordinates,
        'crs': {
            'type': 'EPSG',
            'properties': {
                'code': 4326
            }
        }
    }


def parse_msg(js):

    sensor = js.get('sensor')
    obj = js.get('object')
    loc = obj.get('location')
    coordinates = [loc['lon'], loc['lat']]

    pt = make_point(coordinates)

    feat_pt = make_feature(pt)

    feat_pt['properties'].update({
        'vehicle_id': obj.get('id') + "__" + sensor.get('id'),
        'timestamp': js.get('@timestamp'),
        'speed': js.get('speed'),
        'direction': js.get('direction'),
        'bearing': js.get('bearing')
    })

    return feat_pt


def camera_counts(js):

    camera_id = js.get('sensor').get('id')
    object_id = js.get('object').get('id')
    uid = camera_id+'&&'+object_id

    row = {}
    row['x'] = js.get('sensor').get('location').get('lon')
    row['y'] = js.get('sensor').get('location').get('lat')

    pt = make_point([row['x'], row['y']])
    camera_counts_table[camera_id].add(object_id)

    counts = make_feature(pt)
    counts['camera_id'] = camera_id
    counts['timestamp'] = js.get('@timestamp')
    counts['count'] = len(camera_counts_table[camera_id])

    time_table[uid] = time.time()

    tn = time.time()

    uid_age_off_seconds = 5.0

    to_remove = []
    for uid, t in time_table.items():
        if (tn - t) < uid_age_off_seconds:
            continue

        cid, oid = uid.split('&&')
        camera_counts_table[cid].remove(oid)
        to_remove.append(uid)

    for uid in to_remove:
        time_table.pop(uid)

    return counts


def flatten_counts(counts):
    flat_json = {}
    flat_json['camera_id'] = counts['camera_id']
    flat_json['timestamp'] = counts['timestamp']
    flat_json['count'] = counts['count']
    flat_json['x'] = counts['geometry']['coordinates'][0]
    flat_json['y'] = counts['geometry']['coordinates'][1]
    flat_json['crs_code'] = counts['geometry']['crs']['properties']['code']

    return flat_json


def reform_counts(counts, to='geojson'):
    format_opts = ['geojson', 'json', 'jsongeomix', 'csv']

    if to not in format_opts:
        raise ValueError(f"argument `to` must be one of {', '.join(format_opts)}")

    if to == 'csv':
        flat = flatten_counts(counts)
        reformed = ','.join([str(i) for i in flat.values()])

    elif to == 'geojson':
        geojson_properties = ['camera_id', 'timestamp', 'count']
        reformed = {"type": "Feature"}
        reformed['geometry'] = counts['geometry']
        reformed['properties'] = {k: counts[k] for k in geojson_properties}
        reformed = json.dumps(reformed)

    elif to == 'json':
        reformed = flatten_counts(counts)
        reformed = json.dumps(reformed)

    else:
        reformed = json.dumps(counts)

    return reformed


if __name__ == '__main__':
    descrip = (
        "Parse messages from Deepstream for use with GeoEvent.\n" +
        "As is, this script will publish four different topics, " +
        "each with messages formatted slightly differently, " +
        "to accomodate the formats required by various GeoEvent connectors." +
        "These are: JSON, GeoJSON, CSV (comma-separated values, for GeoEvent10.6), " +
        "and jsongeomix (JSON with a GeoJSON geometry embedded as an entry). " +
        "Each topic will be <TopicNameFromConfigFile>-<format>; e.g.:\n" +
        "deepstream-counts-jsongeomix\n"
    )
    parser = argparse.ArgumentParser(description=descrip)

    parser.add_argument(
        '--cfg',
        dest='cfg',
        help="Configuration file to use.",
        default="kafka-geoevent.yml")

#    parser.add_argument(
#        '--csv',
#        dest='csv',
#        help="Output records as a single line of comma separated values?",
#        required=False,
#        action='store_true')

    args = parser.parse_args()

    cfg_path = os.path.abspath(args.cfg)

    with open(cfg_path, 'r') as fp:
        cfg = yaml.load(fp, Loader=yaml.SafeLoader)

    consumer = KafkaConsumer(
        cfg.get('in-topic'),
        bootstrap_servers=cfg.get('bootstrap_servers'),
        value_deserializer=lambda m: json.loads(m.decode('ascii'))
    )

    producer = KafkaProducer(
        bootstrap_servers=cfg.get('bootstrap_servers')
    )

    time_table = dict()

    camera_counts_table = defaultdict(set)

    t0 = time.time()

    out_topic_prefix = cfg.get('out-count-topic')
    format_opts = ['geojson', 'json', 'jsongeomix', 'csv']
    topics = [out_topic_prefix + '-' + f for f in format_opts]

    previous_message = None

    print(f"Reading from '{cfg.get('in-topic')}'")
    print(f"Publishing to: {', '.join([t for t in topics])}")

    for msg in consumer:

        js = msg.value

        try:
            counts = camera_counts(js)  # , csv=args.csv)
        except:
            counts = None
            pass

        if counts is None:
            continue

        if counts == previous_message:
            continue

        for fmt, t in zip(format_opts, topics):
            msg_out = reform_counts(counts, to=fmt)
            print(f"topic: {t}")
            msg_encoded = msg_out.encode(encoding='ascii', errors='strict')
            print(f"msg_out: {msg_out}")
            print(f"msg_enc: {msg_encoded}")
            producer.send(t,
                          key=msg.key,
                          value=msg_encoded)

        previous_message = counts
