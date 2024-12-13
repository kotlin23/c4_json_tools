import json
import sys
import glob
from collections import defaultdict

dstIpUuid={}
netobjects = defaultdict(list)

#if len(sys.argv) < 2:
#    print("Укажите имя файла конфигурации json")
#    filename = input()
#else:
#    filename = sys.argv[1]

for filename in glob.glob("./*.json"):
    with open(filename,"r",encoding='utf-8') as f:
        data = json.load(f)
#составляем базу сетевых элементов
        for elem in data['objects']:
            try:
                if not elem['is_deleted'] and elem['type'] == "netobject": netobjects[elem['uuid']] = [elem['ip'],elem['name'],elem['description']]
            except: pass
#составляем базу связок маршрутов типа link
            try:
                if elem["left_type"]=="rule.routingtableentry" and elem["right_type"]=="consumer.netobject": dstIpUuid[elem["left_uuid"]]=elem['right_uuid']
#                elif elem["right_type"]=="rule.routingtableentry" and elem["left_type"]=="consumer.netobject": dstIpUuid[elem["right_uuid"]]=elem['left_uuid']
            except: pass
#перебираем все записи в json, выбираем только объекты типа routingtableentry
        print(f'{"dst": <40}{"gateway": <17}{"metric"}')
        for elem in data['objects']:
            try:
                if not elem['is_deleted'] and elem["type"]=="routingtableentry":
                    dst_ip = elem['dst_ip']
#если dst_ip пустая строка, значит маршрут создан в виде объекта, берем данные из базы объектов по ссылке из промежуточной базы линков
                    if dst_ip=="": dst_ip = netobjects[dstIpUuid[elem["uuid"]]][1]+"("+netobjects[dstIpUuid[elem["uuid"]]][0]+")"
                    print(f'{dst_ip: <40}{elem["nexthop"]: <17}{elem["metric"]}')
            except: pass
