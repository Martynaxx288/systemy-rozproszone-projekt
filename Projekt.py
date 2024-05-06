import win32evtlog  # Import modułu do pracy z dziennikami zdarzeń systemowych w systemie Windows
import xml.etree.ElementTree as ET  # Import modułu XML
import csv  # Import modułu do obsługi plików CSV
from openai import OpenAI  # Import modułu do komunikacji z API OpenAI

# Funkcja do analizowania dziennika zdarzeń za pomocą modelu językowego
def analyze_log_with_llm(log):
    completion = client.chat.completions.create(
        model="LM Studio Community/Meta-Llama-3-8B-Instruct-GGUF",  # Wybór modelu językowego
        messages=[
            {"role": "system", "content": "Give answer which not exceeds 20 characters"},  # Komunikat systemowy
            {"role": "user", "content": f"rate on a scale of 1 to 10 whether a log {log} is an anomaly. Your answer "
                                        f"should be shorter then 20 characters"}  # Pytanie do użytkownika
        ],
        temperature=0.7,  # Temperatura generacji odpowiedzi przez model
    )
    print("Anylize log ", log, completion.choices[0].message)  # Wyświetlenie wyniku analizy
    return completion.choices[0].message  # Zwrócenie odpowiedzi modelu

# Funkcja do pobierania dzienników zdarzeń systemowych
def get_system_logs():
    logs = []  # Lista na przechowywanie wpisów dziennika
    flags = win32evtlog.EvtQueryChannelPath  # Flaga dla zapytania o kanał zdarzeń
    channel_name = "System"  # Nazwa kanału "System" w dzienniku zdarzeń
    # Otwarcie pliku zdarzeń
    query_handle = win32evtlog.EvtQuery(
        channel_name, flags, None, None)

    read_count = 0  # Licznik odczytanych wpisów
    expected_number_of_logs = 1  # Oczekiwana liczba wpisów
    while read_count < expected_number_of_logs:
        # Odczyt 100 rekordów
        events = win32evtlog.EvtNext(query_handle, expected_number_of_logs)

        read_count += len(events)  # Aktualizacja licznika odczytanych wpisów
        # Jeśli nie ma wpisów, przerwij pętlę
        if len(events) == 0:
            break
        for event in events:

            xml_content = win32evtlog.EvtRender(event, win32evtlog.EvtRenderEventXml)


            xml = ET.fromstring(xml_content)
            # Przestrzeń nazw XML
            ns = '{http://schemas.microsoft.com/win/2004/08/events/event}'
            event_id = xml.find(f'.//{ns}EventID').text  # ID zdarzenia
            level = xml.find(f'.//{ns}Level').text  # Poziom logowania
            channel = xml.find(f'.//{ns}Channel').text  # Nazwa kanału
            execution = xml.find(f'.//{ns}Execution')  # Informacje o wykonaniu
            process_id = execution.get('ProcessID')  # ID procesu
            thread_id = execution.get('ThreadID')  # ID wątku
            time_created = xml.find(f'.//{ns}TimeCreated').get('SystemTime')  # Czas utworzenia zdarzenia
            provider = xml.find(f'.//{ns}Provider')  # Dostawca zdarzenia
            name = provider.get('Name')  # Nazwa
            guid = provider.get('Guid')  # GUID
            source_name = provider.get('EventSourceName')  # Nazwa źródła
            # Wyświetlenie informacji o zdarzeniu
            print(
                f'Time: {time_created}, Level: {level} Event Id: {event_id}, Channel: {channel}, '
                f'Process Id: {process_id}, Thread Id: {thread_id} Name: {name}, Guid: {guid}, Source name {source_name}')

            # Zapisanie informacji o zdarzeniu
            record = {
                'level': level,
                'event_id': event_id,
                'channel': channel,
                'process_id': process_id,
                'thread_id': thread_id,
                'time_created': time_created,
                'name': name,
                'guid': guid,
                'source_name': source_name
            }
            # Analiza zdarzenia za pomocą modelu językowego
            answer = analyze_log_with_llm(record)
            record['chat_answer'] = answer  # Dodanie odpowiedzi modelu do rekordu
            logs.append(record)  # Dodanie rekordu do listy dzienników

    print(f'Read {read_count} records')  # Wyświetlenie liczby odczytanych wpisów
    return logs  # Zwrócenie listy dzienników

# Funkcja do zapisywania dzienników do pliku CSV
def save_to_csv(logs, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['level', 'event_id', 'channel', 'process_id', 'thread_id', 'time_created', 'name', 'guid',
                      'source_name', 'chat_answer']  # Nagłówki kolumn w pliku CSV
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Zapisanie nagłówków
        writer.writerows(logs)  # Zapisanie wpisów dziennika

# Funkcja do zapisywania odpowiedzi czatu do pliku tekstowego
def save_chat_answers_to_txt(logs, filename):
    with open(filename, 'w', encoding='utf-8') as txtfile:
        for log in logs:
            txtfile.write(log['chat_answer'] + '\n')  # Zapisanie odpowiedzi czatu do pliku


if __name__ == "__main__":
    # Wskazanie lokalnego serwera
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

    logs = get_system_logs()  # Pobranie dzienników systemowych
    save_to_csv(logs, 'system_logs.csv')  # Zapisanie dzienników do pliku CSV
    save_chat_answers_to_txt(logs, 'chat_answers.txt')  # Zapisanie odpowiedzi czatu do pliku tekstowego

    print("Pobrano logi i zapisano do plików system_logs.csv oraz chat_answers.txt")  # Komunikat o zakończeniu operacji
