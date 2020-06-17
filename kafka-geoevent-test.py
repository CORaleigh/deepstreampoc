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

    # if camera_id not in camera_info:
    #     return None

    # info = camera_info.get(camera_id)
    # counts = make_feature(info.get('pt'))

    counts = make_feature(pt)
    # counts['properties'].update(info.get('properties'))
    # counts['properties'].update({
    #     'camera_id': camera_id,
    #     'timestamp': js.get('@timestamp'),
    #     'counts': len(camera_counts_table[camera_id]),
    # })
    # counts = defaultdict(dict)
    counts['camera_id'] = camera_id
    # counts['camera_desc'] = js.get('sensor').get('description')
    counts['timestamp'] = js.get('@timestamp')
    counts['count'] = len(camera_counts_table[camera_id])
    # counts['x'] = js.get('sensor').get('location').get('lon')
    # counts['y'] = js.get('sensor').get('location').get('lat')

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


if __name__ == '__main__':
    descrip = "Parse messages from Metropolis/Deepstream for use with GeoEvent"
    parser = argparse.ArgumentParser(description=descrip)

    parser.add_argument(
        '--cfg',
        dest='cfg',
        help="Configuration file to use.",
        default="kafka-geoevent.yml")

    args = parser.parse_args()

    cfg_path = os.path.abspath(args.cfg)

    with open(cfg_path, 'r') as fp:
        cfg = yaml.load(fp, Loader=yaml.SafeLoader)

    # Camera metadata
    # camera_data = pd.read_csv('camera_metadata.csv').set_index('Name')

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

    print(f"Reading from '{cfg.get('in-topic')}'")

    previous_message = None

    for msg in consumer:
#        print("this msg is printed for every msg in consumer")

        js = msg.value
        print(f'msg received at {time.time()}')
        with open('testdata.json', 'a') as f:
            json.dump(js, f, ensure_ascii=False, indent=4)

        # if js.get('sensor').get('id') not in camera_info:
        #     continue
        
        try:
            counts = camera_counts(js)
            counts = json.dumps(counts)
        except:
            counts = None
            pass

        if counts is None:
            continue

        if counts == previous_message:
            continue

        producer.send(cfg.get('out-count-topic'),
                      key=msg.key, value=counts.encode('ascii'))
        previous_message = counts

    #    try:
    #        feat_pt = parse_msg(js)
    #        feat_pt = json.dumps(feat_pt)
    #    except:
    #        feat_pt = None
    #        pass

        # try:
        #    producer.send(cfg.get('out-point-topic'), key=msg.key, value=feat_pt.encode('ascii'))
        #except: pass

        # if not first:
        #     print("Received Message")
        #     print("message sent: {counts}")
        #     first=True

        #try:
        # print('bottom of the loop')
        #except: pass



###

    # camera_info = defaultdict(dict)
    # for camera_id, row in camera_data.iterrows():
    #     pt = make_point([row.Long, row.Lat])
    #
    #     camera_info[camera_id]['pt'] = pt
    #     camera_info[camera_id]['properties'] = {
    #         'depth_ft': row['Depth (feet)'],
    #         'direction': row['Direction'],
    #         'fov': row['Field of view']
    #     }

