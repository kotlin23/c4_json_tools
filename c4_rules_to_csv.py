import json
import glob
import csv
import sys
from collections import defaultdict
SERVICES_DICT = {1:"ICMP",6:"TCP",17:"UDP"}
ROWS_DELIMETER = chr(10)

def json_read(fn):
    netObjects = defaultdict(list)
    groups = defaultdict(list)
    groupsUuid = defaultdict(list)
    services = defaultdict(list)
    grServices = defaultdict(list)
    grServiceUuid = defaultdict(list)
    fwRules = defaultdict(list)
    with open(fn, "r", encoding='utf-8') as f:
        data = json.load(f)
        print("Reading file",fn)
        for elem in data['objects']:
            #некоторые объекты не содержат поле description. сразу проверяем на наличие. Запоминаем, иначе desc=""
            desc=""
            try:
                desc=elem["description"]
            except: pass
            #составляем список сетевых объектов netObjects
            try:
                if not elem['is_deleted'] and elem['type'] == "netobject": netObjects[elem['uuid']]=[elem['name'], elem['ip'], desc]
            except: pass
            #список групп сетевых объектов с идентификацией по uuid
            try:
                if not elem['is_deleted'] and elem['type'] == "group" and elem['subtype'] == "netobject": groups[elem['uuid']]=[elem['name'],desc]
            except: pass
            #база связей группа - сетевые объекты
            try:
                if elem["left_type"]=="baseobj.group" and elem["right_type"]=="consumer.netobject":
                    if not elem['right_uuid'] in groupsUuid[elem["left_uuid"]]: groupsUuid[elem["left_uuid"]].append(elem['right_uuid'])
            #                elif elem["right_type"]=="baseobj.group" and elem["left_type"]=="consumer.netobject":
            #                    if not elem['left_uuid'] in groupsUuid[elem["right_uuid"]]: groupsUuid[elem["right_uuid"]].append(elem['left_uuid'])
            except: pass
            # составляем базу сервисов
            try:
                if not elem['is_deleted'] and elem['type'] == "service":
                    services[elem['uuid']] = [elem['name'],elem['proto'],elem['src'],elem['dst'],desc]
            except: pass
            # список групп сервисов
            try:
                if not elem['is_deleted'] and elem['type'] == "group" and elem['subtype'] == "service": grServices[elem['uuid']]=[elem['name'],desc]
            except: pass
            #база связей группа сервисов - сервисы
            try:
                if elem["left_type"]=="baseobj.group" and elem["right_type"]=="param.service":
                    if not elem['right_uuid'] in grServiceUuid[elem["left_uuid"]]: grServiceUuid[elem["left_uuid"]].append(elem['right_uuid'])
            #                elif elem["right_type"]=="baseobj.group" and elem["left_type"]=="param.service":
            #                    if not elem['left_uuid'] in grServiceUuid[elem["right_uuid"]]: grServiceUuid[elem["right_uuid"]].append(elem['left_uuid'])
            except: pass
            #список правил фильтрации текущего УБ
            try:
                if not elem['is_deleted'] and elem['type'] == "fwrule" and not elem['is_delimiter']:
                    if not ((elem['uuid']) in fwRules): fwRules[elem["uuid"]]=[elem["name"], desc, elem["rule_action"],[],[],[],elem["priority"]]
            except: pass

        #повторно проходим конфиг и добавляем в базу правил информацию (uuid) source,destination,service
        for elem in data['objects']:
            try:
                if elem["left_type"]=="rule.fwrule" and (elem["right_type"]=="consumer.netobject" or elem["right_type"]=="baseobj.group"):
                    #sources
                    if elem["linkname"]=="clf_source":
                        if not elem['right_uuid'] in fwRules[elem["left_uuid"]][3]: fwRules[elem["left_uuid"]][3].append(elem['right_uuid'])
                    #destination
                    elif elem["linkname"]=="clf_destination":
                        if not elem['right_uuid'] in fwRules[elem["left_uuid"]][4]: fwRules[elem["left_uuid"]][4].append(elem['right_uuid'])
                #Сервисы и группы сервисов
                if elem["left_type"]=="rule.fwrule" and elem["linkname"]=="clf_service" and (elem["right_type"]=="param.service" or elem["right_type"]=="baseobj.group"):
                    if not elem['right_uuid'] in fwRules[elem["left_uuid"]][5]: fwRules[elem["left_uuid"]][5].append(elem['right_uuid'])
            except: pass
    data = [['PRIORITY', 'FWRULE_NAME', 'FWRULE_DESC', 'SOURCE', 'SOURCE_NAME', 'SOURCE_IP', 'DESTINATION', 'DEST_NAME', 'DEST_IP', 'SERVICE_NAME', 'PROTO', 'PORT', 'SERVICE_DESC']]
    for uuid in fwRules:
#добавляем хосты и сети
        src_name="any"
        src_ip="0.0.0.0/0"
        src_desc="any"
        for src in fwRules[uuid][3]:
            if src in netObjects:
                if src_name=="any": src_name=netObjects[src][0]
                else: src_name = src_name+ROWS_DELIMETER+netObjects[src][0]
                if src_ip=="0.0.0.0/0": src_ip=netObjects[src][1]
                else: src_ip = src_ip+ROWS_DELIMETER+netObjects[src][1]
                if src_desc=="any": src_desc=netObjects[src][2]
                else: src_desc = src_desc+ROWS_DELIMETER+netObjects[src][2]
            else:
                if src_name=="any":
                    src_name = groups[src][0]+"("
                    src_desc = groups[src][1]+"("
                    src_ip = ""
                else:
                    src_name = src_name+ROWS_DELIMETER+groups[src][0]+"("
                    src_desc = src_desc+ROWS_DELIMETER+groups[src][1]+"("
                for srcUuid in groupsUuid[src]:
                    src_name = src_name+ROWS_DELIMETER+netObjects[srcUuid][0]
                    src_ip = src_ip+ROWS_DELIMETER+netObjects[srcUuid][1]
                    src_desc = src_desc+ROWS_DELIMETER+netObjects[srcUuid][2]
                src_name=src_name+")"
                src_desc=src_desc+")"
        dst_name="any"
        dst_ip="0.0.0.0/0"
        dst_desc="any"
        for dst in fwRules[uuid][4]:
            if dst in netObjects:
                if dst_name=="any": dst_name=netObjects[dst][0]
                else: dst_name = dst_name+ROWS_DELIMETER+netObjects[dst][0]
                if dst_ip=="0.0.0.0/0": dst_ip=netObjects[dst][1]
                else: dst_ip = dst_ip+ROWS_DELIMETER+netObjects[dst][1]
                if dst_desc=="any": dst_desc=netObjects[dst][2]
                else: dst_desc = dst_desc+ROWS_DELIMETER+netObjects[dst][2]
            else:
                if dst_name=="any":
                    dst_name = groups[dst][0]+"("
                    dst_desc = groups[dst][1]+"("
                    dst_ip = ""
                else:
                    dst_name = dst_name+ROWS_DELIMETER+groups[dst][0]+"("
                    dst_desc = dst_desc+ROWS_DELIMETER+groups[dst][1]+"("
                for dstUuid in groupsUuid[dst]:
                    dst_name = dst_name+ROWS_DELIMETER+netObjects[dstUuid][0]
                    dst_ip = dst_ip+ROWS_DELIMETER+netObjects[dstUuid][1]
                    dst_desc = dst_desc+ROWS_DELIMETER+netObjects[dstUuid][2]
                dst_name=dst_name+")"
                dst_desc=dst_desc+")"
        #сервисы
        srv_name = ""
        proto = "any"
        port = ""
        srv_desc = "any"
        for srv in fwRules[uuid][5]:
            if srv in services:
                if proto=="any":
                    proto=SERVICES_DICT[services[srv][1]]
                    srv_desc=services[srv][4]
                    srv_name=services[srv][0]
                else:
                    proto = proto+ROWS_DELIMETER+SERVICES_DICT[services[srv][1]]
                    srv_desc=srv_desc+ROWS_DELIMETER+services[srv][4]
                    srv_name=srv_name+ROWS_DELIMETER+services[srv][0]
                if port=="": port=services[srv][3]
                else:
                    port = port+ROWS_DELIMETER+services[srv][3]
            else:
                if proto=="any":
                    proto = grServices[srv][0]+"("
                    srv_desc = grServices[srv][0]+"("
                    srv_name = grServices[srv][0]+"("
                else:
                    proto=proto+ROWS_DELIMETER+grServices[srv][0]+"("
                    srv_desc=grServices[srv][0]+"("
                    srv_name=grServices[srv][0]+"("
                for srvUuid in grServiceUuid[srv]:
                    proto=proto+ROWS_DELIMETER+SERVICES_DICT[services[srvUuid][1]]
                    srv_desc=srv_desc+ROWS_DELIMETER+services[srvUuid][4]
                    srv_name=srv_name+ROWS_DELIMETER+services[srvUuid][0]
                    port=port+ROWS_DELIMETER+services[srvUuid][3]
                proto=proto+")"
                srv_desc=srv_desc+")"
                srv_name=srv_name+")"
        data.append([fwRules[uuid][6], fwRules[uuid][0], fwRules[uuid][1], src_desc, src_name, src_ip, dst_desc, dst_name, dst_ip, srv_name, proto, port, srv_desc])
    return data

def write_csv(fn,data):
#запись массива в файл
    with open(fn, 'w', newline="") as csvfile:
        try:
            csvwriter = csv.writer(csvfile, delimiter=';')
            for row in data:
                csvwriter.writerow(row)
            print("Created file",fn)
        except: pass

if len(sys.argv) >= 2:
    write_csv(sys.argv[1][0:len(sys.argv[1])-5]+".csv",json_read(sys.argv[1]))
else:
    for fn in glob.glob("./*.json"): write_csv(fn[0:len(fn)-5]+".csv",json_read(fn))
