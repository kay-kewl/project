import csv

with open('making_csv.txt', encoding='utf8') as file:
    data = [i.strip('\n').split('\t') for i in file.readlines()]

with open('data_all.csv', 'w', encoding='utf8', newline='') as file:
    writer = csv.writer(file, delimiter=';')
    writer.writerows(data)

with open('data_ok.csv', 'w', encoding='utf8', newline='') as file:
    data1 = [i for i in data if i[-1] != 'bad']
    writer = csv.writer(file, delimiter=';')
    writer.writerows(data1)
