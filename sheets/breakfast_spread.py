def analyze_spread(csv):
    csv = csv.split('\n')
    columns = csv[0].split(',')
    content = ""
    for row in csv[1:]:
        data = row.split('\t')
        print("<h4>{}</h4>".format(data[0] + ', ' + data[1]))
        print("<p><b>What did you eat for breakfast?</b><br/>{}</p>".format(data[2].strip('"')))
        print("<p><b>What is your Breakfast philosophy?</b><br/>{}</p>".format(data[3].strip('"')))
        print('')




if __name__ == '__main__':
    with open('breakfast.tsv', 'r') as f:
        analyze_spread(f.read())