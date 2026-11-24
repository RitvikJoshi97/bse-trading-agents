import csv

file = open('results.csv')
csvreader = csv.reader(file)

rows = []
for row in csvreader:
    rows.append(row)

results = {'FARIMA':0.0,
            'FARIMASTM':0.0,
            'SARIMAX':0.0,
            'LSTM':0.0,
            'SGD':0.0}

result_non_zero = {'FARIMA':0,
            'FARIMASTM':0,
            'SARIMAX':0,
            'LSTM':0,
            'SGD':0}
total_number = {'FARIMA':0,
            'FARIMASTM':0,
            'SARIMAX':0,
            'LSTM':0,
            'SGD':0}


for each in rows:
    total_number[each[0]] += 1
    if float(each[1]) != 0.0:
        results[each[0]] += float(each[1])
        result_non_zero[each[0]] += 1


for each in results:
    if total_number[each] != 0.0: total_number[each] = int(results[each]/total_number[each])

for each in results:
    if result_non_zero[each] != 0.0: results[each] = int(results[each]/result_non_zero[each])

print("Results without removing sessions with zero profits:",total_number)
print("Results with removing sessions with zero profits:",results)