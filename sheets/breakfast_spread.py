def analyze_spread(csv):
    csv = csv.split('\n')
    columns = csv[0].split(',')
    content = ""
    for row in csv[1:]:
        data = row.split(',')
        content += "<h4>{}</h4><p><b>What did you eat for breakfast?</b></p><p>{}</p><p><b>What is your Breakfast philosophy?</b></p><p>{}</p>"\
            .format(data[0] + ', ' + data[1], data[2], data[3])
    print(content)




if __name__ == '__main__':
    with open('breakfast_spread.csv', 'r') as f:
        analyze_spread(f.read())