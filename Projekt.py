import win32evtlog
import xml.etree.ElementTree as ET
import csv


# import win32evtlogutil

def get_system_logs():
    logs = []
    flags = win32evtlog.EvtQueryChannelPath
    channel_name = "System"
    # open event file
    query_handle = win32evtlog.EvtQuery(
        channel_name, flags, None, None)

    read_count = 0
    while True:
        # read 100 records
        events = win32evtlog.EvtNext(query_handle, 100)
        read_count += len(events)
        # if there is no record break the loop
        if len(events) == 0:
            break
        for event in events:
            xml_content = win32evtlog.EvtRender(event, win32evtlog.EvtRenderEventXml)

            # parse xml content
            xml = ET.fromstring(xml_content)
            # xml namespace, root element has a xmlns definition, so we have to use the namespace
            ns = '{http://schemas.microsoft.com/win/2004/08/events/event}'
            event_id = xml.find(f'.//{ns}EventID').text
            level = xml.find(f'.//{ns}Level').text
            channel = xml.find(f'.//{ns}Channel').text
            execution = xml.find(f'.//{ns}Execution')
            process_id = execution.get('ProcessID')
            thread_id = execution.get('ThreadID')
            time_created = xml.find(f'.//{ns}TimeCreated').get('SystemTime')
            provider = xml.find(f'.//{ns}Provider')
            name = provider.get('Name')
            guid = provider.get('Guid')
            source_name = provider.get('EventSourceName')
            print(
                f'Time: {time_created}, Level: {level} Event Id: {event_id}, Channel: {channel}, Process Id: {process_id}, Thread Id: {thread_id} Name: {name}, Guid: {guid}, Source name {source_name}')

            record = {
                'level': level,
                # 'timestamp': timestamp,
                'event_id': event_id,
                'channel': channel,
                'process_id': process_id,
                'thread_id': thread_id,
                'time_created': time_created,
                'name': name,
                'guid': guid,
                'source_name': source_name
            }
            logs.append(record)

    print(f'Read {read_count} records')
    return logs


# Funkcja do zapisywania logów do pliku CSV
def save_to_csv(logs, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['level', 'event_id', 'channel', 'process_id', 'thread_id', 'time_created', 'name', 'guid',
                      'source_name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(logs)


if __name__ == "__main__":
    logs = get_system_logs()
    save_to_csv(logs, 'system_logs.csv')
    print("Pobrano logi i zapisano do pliku system_logs.csv")
