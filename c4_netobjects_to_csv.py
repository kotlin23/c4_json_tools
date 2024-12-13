import csv
import glob
import json
from collections import defaultdict

netobjects = defaultdict(list)
groupsUuid = defaultdict(list)
groups = defaultdict(list)

for filename in glob.glob("./*.json"):
    with open(filename,"r",encoding='utf-8') as f:
        data = json.load(f)
#список сетевых объектов
        for elem in data['objects']:
            try:
                if not elem['is_deleted'] and elem['type'] == "netobject": netobjects[elem['uuid']]=[elem['name'], elem['ip'], elem['description']]
            except: pass
#список групп с идентификацией по uuid
            try:
                if not elem['is_deleted'] and elem['type'] == "group" and elem['subtype'] == "netobject": groups[elem['uuid']]=[elem['name'],elem['description']]
            except: pass
#база связей группа - сетевые объекты
            try:
                if elem["left_type"]=="baseobj.group" and elem["right_type"]=="consumer.netobject":
                    if not elem['right_uuid'] in groupsUuid[elem["left_uuid"]]: groupsUuid[elem["left_uuid"]].append(elem['right_uuid'])
            except: pass

#создаем массив для выгрузки csv файла
data = [['_IP/ELEMENT_', '_NAME_', '','_COMMENT_']]
#добавляем хосты и сети
for uuid in netobjects:
    data.append([netobjects[uuid][1], netobjects[uuid][0], '',netobjects[uuid][2]])
#добавляем группы
for uuid in groups:
    ne_list = ""
    for ne in groupsUuid[uuid]:
        if ne_list != "":
            ne_list=ne_list+"|"+netobjects[ne][0]
        else:
            ne_list=netobjects[ne][0]
    data.append([ne_list,groups[uuid][0],'',groups[uuid][1]])
#запись массива в файл
with open('result.csv', 'w', newline="") as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';')
    for row in data:
        csvwriter.writerow(row)
