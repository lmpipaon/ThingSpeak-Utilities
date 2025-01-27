# This script is part of the ThingSpeak-Utilities repository.
# Licensed under the MIT License.
# Copyright (c) 2025 Luis Pipaon
# See the LICENSE file in the project root for more information.
# Repository: https://github.com/lmpipaon/ThingSpeak-Utilities



import urllib.request
import json
import sys


# List of API keys
user_API_Key = ["XXXXXXXXXXXXXXXX", "XXXXXXXXXXXXXXXX"]


#******************************************************************************************************************************
pweb="""<!DOCTYPE html>
<html>
<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type">
    <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
    <script src="https://code.highcharts.com/stock/highstock.js"></script>
    <script src="https://code.highcharts.com/stock/modules/exporting.js"></script>
    <script src="https://rawgithub.com/highslide-software/export-csv/master/export-csv.js"></script>
    <script type="text/javascript">
        var dynamicChart;
        var channelsLoaded = 0;
        var channelKeys =[];
        channelKeys.push(%s);
        
        var myOffset = new Date().getTimezoneOffset();

        // Function to convert date from JSON format
        function getChartDate(d) {
            return Date.UTC(d.substring(0,4), d.substring(5,7)-1, d.substring(8,10), d.substring(11,13), d.substring(14,16), d.substring(17,19)) - (myOffset * 60000);
        }
        
        // Hide all series
        function HideAll() {
            dynamicChart.series.forEach(function(series) {
                if (series.name !== 'Navigator') {
                    series.hide();
                }
            });
        }

        $(document).ready(function() {
            // Show loading message
            $('#loading-message').show();

            // Set series numbers
            let seriesCounter = 0;
            channelKeys.forEach(function(channel) {
                channel.fieldList.forEach(function(field) {
                    field.series = seriesCounter++;
                });
            });
            
            // Load channel data
            channelKeys.forEach(function(channel, index) {
                channel.loaded = false;
                loadThingSpeakChannel(index, channel.channelNumber, channel.key, channel.fieldList);
            });

            // Load data from ThingSpeak channel
            function loadThingSpeakChannel(channelIndex, channelNumber, key, fieldList) {
                $.getJSON(`https://api.thingspeak.com/channels/${channelNumber}/feed.json?offset=0&key=${key}&results=8000`, function(data) {
                    if (data === '-1') {
                        $('#chart-container').append('This channel is not public. To embed charts, the channel must be public or a read key must be specified.');
                        console.log('Thingspeak Data Loading Error');
                        return;
                    }
                    
                    fieldList.forEach(function(field) {
                        field.data = [];
                        data.feeds.forEach(function(feed) {
                            var value = feed[`field${field.field}`];
                            if (!isNaN(parseInt(value))) {
                                field.data.push([getChartDate(feed.created_at), parseFloat(value)]);
                            }
                        });
                        field.name = data.channel[`field${field.field}`];
                    });
                    
                    channelKeys[channelIndex].fieldList = fieldList;
                    channelKeys[channelIndex].loaded = true;
                    channelsLoaded++;

                    if (channelsLoaded === channelKeys.length) {
                        createChart();
                    }
                }).fail(function() {
                    alert('getJSON request failed!');
                });
            }

            // Create chart when all data is loaded
            function createChart() {
                var chartOptions = {
                    chart: {
                        renderTo: 'chart-container',
                        zoomType: 'y',
                        height: 'calc(100vh - 50px)', // Use full height minus 50px for loading message
                        spacingTop: 10, // Minimal space at the top
                        spacingBottom: 60, // Space at the bottom for the legend
                        spacingLeft: 10, // Space on the left
                        spacingRight: 10 // Space on the right
                    },
                    rangeSelector: {
                        buttons: [
                            { count: 30, type: 'minute', text: '30M' },
                            { count: 12, type: 'hour', text: '12H' },
                            { count: 1, type: 'day', text: 'D' },
                            { count: 1, type: 'week', text: 'W' },
                            { count: 1, type: 'month', text: 'M' },
                            { count: 1, type: 'year', text: 'Y' },
                            { type: 'all', text: 'All' }
                        ],
                        inputEnabled: true,
                        selected: 4
                    },
                    title: { text: '' },
                    tooltip: {
                        valueDecimals: 1,
                        valueSuffix: '',
                        xDateFormat: '%%Y-%%m-%%d<br/>%%H:%%M:%%S %%p'
                    },
                    xAxis: {
                        type: 'datetime',
                        ordinal: false,
                        dateTimeLabelFormats: {
                            hour: '%%l %%p',
                            minute: '%%l:%%M %%p'
                        },
                        title: { text: 'Date' }
                    },
                    yAxis: [{
                        title: { text: '%s' },
                        id: '%s'
                    },
                    {
                        title: { text: '%s' },
                        opposite: true,
                        id: '%s'
                    }],
                    exporting: { enabled: true, csv: { dateFormat: '%%d/%%m/%%Y %%I:%%M:%%S %%p' } },
                    legend: { enabled: true, layout: 'horizontal', align: 'center', verticalAlign: 'bottom' },
                    series: []
                };

                // Add all channel data to the chart
                channelKeys.forEach(function(channel) {
                    channel.fieldList.forEach(function(field) {
                        chartOptions.series.push({
                            data: field.data,
                            index: field.series,
                            yAxis: field.axis,
                            name: field.name
                        });
                    });
                });
                
                // Draw the chart
                dynamicChart = new Highcharts.StockChart(chartOptions);

                // Hide loading message and show the chart
                $('#loading-message').hide();
            }
        });
    </script>
    <title>%s</title>
    <style>
        /* Make the chart container full screen, but adjust for margins */
        #chart-container {
            width: 100%%;
            height: 100vh; /* Full viewport height */
            margin: 0;
        }

        /* Style the loading message */
        #loading-message {
            position: fixed;
            top: 50%%;
            left: 50%%;
            transform: translate(-50%%, -50%%);
            font-size: 20px;
            color: #000;
            font-weight: bold;
            display: none;
        }
    </style>
</head>
<body>
    <div id="loading-message">Loading data, please wait...</div>
    <div id="chart-container"></div>
</body>
</html>
"""
# ****************************************************************************************


#   --------------Get channel names and API keys--------------------------
count = 0
channel_list = []

for api_key in user_API_Key:
    url = f"https://api.thingspeak.com/channels.json?api_key={api_key}"
    with urllib.request.urlopen(url) as response:
        html = response.read()
    json_all_data = json.loads(html)
    for json_data in json_all_data:
        name = json_data['name']
        id_ = str(json_data['id'])
        for api_keys in json_data['api_keys']:
            write_flag = api_keys['write_flag']
            if write_flag == False:
                api_key = api_keys['api_key']
        print(str(count).rjust(3), id_, api_key, name, sep='; ')
        count += 1
        channel_list.append([id_, api_key])

#----------------------------------------------------------------  

print()
print("Fetching data...")
for i in range(len(channel_list)):
    channel_list[i].append(i)
    url = "https://api.thingspeak.com/channels/" + channel_list[i][0] + "/feeds.json?api_key=" + channel_list[i][1] + "&results=0"
    TS = urllib.request.urlopen(url)
    response = TS.read()
    data = json.loads(response)
    f = data['channel']['name']
    channel_list[i].append(f)
    f = data['channel']['field1']
    channel_list[i].append(f)
    f = data['channel']['field2']
    channel_list[i].append(f)
    f = data['channel']['field3']
    channel_list[i].append(f)
    f = data['channel']['field4']
    channel_list[i].append(f)
    f = data['channel']['field5']
    channel_list[i].append(f)
    f = data['channel']['field6']
    channel_list[i].append(f)
    f = data['channel']['field7']
    channel_list[i].append(f)
    f = data['channel']['field8']
    channel_list[i].append(f)
    TS.close()
print("Data fetched\n")

yAxis1 = ""
yAxis2 = ""

variable_list = []
line = "────────────────────"
while True:
    print("\n")
    print(line.ljust(2)[:3] + line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], sep=("┬"))
    print("No. ".ljust(2)[:3] + "Channel".ljust(14)[:14], "Field 1".ljust(14)[:14], "Field 2".ljust(14)[:14], "Field 3".ljust(14)[:14], "Field 4".ljust(14)[:14], "Field 5".ljust(14)[:14], "Field 6".ljust(14)[:14], "Field 7".ljust(14)[:14], "Field 8".ljust(14)[:14], sep=("│"))
    print(line.ljust(2)[:3] + line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], sep=("┼"))
    for c in channel_list:
        # Check if the list has enough elements before accessing
        if len(c) >= 12:
            print((str(c[2]) + "  ").ljust(2)[:3] + c[3].ljust(14)[:14], c[4].ljust(14)[:14], c[5].ljust(14)[:14], c[6].ljust(14)[:14], c[7].ljust(14)[:14], c[8].ljust(14)[:14], c[9].ljust(14)[:14], c[10].ljust(14)[:14], c[11].ljust(14)[:14], sep=("│"))
            print(line.ljust(2)[:3] + line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], line.ljust(14)[:14], sep=("┼"))
        
    st = ""
    for i in variable_list:
        st += i[4].ljust(20)[:20] + i[5].ljust(14)[:14] + i[3].ljust(14)[:14] + "\n"
    print(st)
    print("\n")
    channel_input = input("Channel: ")
    if channel_input == "":
        if len(variable_list) > 0:
            break
        else:
            sys.exit()
    i = int(channel_input)
    print("\n") 
    for ii in range(1, 9):
        print(str(ii) + " " + channel_list[i][ii + 3])
    field = int(input("Field: "))

    field_name = channel_list[i][int(field) + 3]

    while True:
        axis = input("Axis (" + yAxis1 + " / " + yAxis2 + "): ")
        print(axis)
        if yAxis1 == "":
            yAxis1 = axis
            break
        elif (yAxis2 == "") and (yAxis1 != axis):
            yAxis2 = axis
            break
        elif axis in [yAxis1, yAxis2]:
            break
    variable = [channel_list[i][0], channel_list[i][1], field, axis, channel_list[i][3], field_name]
    variable_list.append(variable)

end_input = input("\n\nEnd: ")
if end_input != "":
    end_input += '%2000:00:00'

request = ""
first = True
for v in variable_list:
    if first:
        request += "{channelNumber:%s, name:'',key:'%s',fieldList:[{field:%s,axis:'%s'}]}" % (v[0], v[1], v[2], v[3])
        first = False
    else:
        request += ",{channelNumber:%s, name:'',key:'%s',fieldList:[{field:%s,axis:'%s'}]}" % (v[0], v[1], v[2], v[3])

title = input("Title: ")

print(request, end_input, yAxis1, yAxis1, yAxis2, yAxis2, title)
result = pweb % (request, yAxis1, yAxis1, yAxis2, yAxis2, title)

with open(title + ".html", "w") as f:
    f.write(result)

print(result)

input("\n\n\nPress return to finish")
