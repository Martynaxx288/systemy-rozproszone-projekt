import win32evtlog  # Biblioteka do dziennika zdarzeń systemowych Windows
import xml.etree.ElementTree as ET  # Biblioteka XML
import csv  # Biblioteka do  plików CSV
from openai import OpenAI  # Biblioteka do łączenia z API OpenAI

# Funkcja do analizowania logów za pomocą modelu językowego OpenAI
def analyze_log_with_llm(log):
    # Generowanie odpowiedzi za pomocą modelu językowego OpenAI
    completion = client.chat.completions.create(
        model="LM Studio Community/Meta-Llama-3-8B-Instruct-GGUF",  # Określenie modelu do użycia
        messages=[
            {"role": "system", "content": "Podaj odpowiedź, która nie przekracza 20 znaków"},  # Komunikat systemowy
            {"role": "user", "content": f"Oceń na skali od 1 do 10, gdzie 10 oznacza anomalię, czy log {log} jest anomalią. Twoja odpowiedź "  # Komunikat użytkownika
                                        f"powinna być krótsza niż 20 znaków"}
        ],
        temperature=0.1,  # Wrażliwosc czatu
    )
    # Wyświetlenie zanalizowanego logu i odpowiedzi
    print("Analiza logu ", log, completion.choices[0].message)
    return completion.choices[0].message  # Zwrócenie komunikatu odpowiedzi

# Funkcja do pobierania logów systemowych
def get_system_logs():
    logs = []  # Lista do przechowywania rekordów logów
    flags = win32evtlog.EvtQueryChannelPath  # Flagi dla zapytania dziennika zdarzeń
    channel_name = "System"  # Określenie kanału dziennika zdarzeń

    # Otwarcie pliku dziennika zdarzeń
    query_handle = win32evtlog.EvtQuery(channel_name, flags, None, None)

    read_count = 0  # Licznik do śledzenia liczby odczytanych logów
    expected_number_of_logs = 5  # Określenie oczekiwanej liczby logów do odczytania
    while read_count < expected_number_of_logs:
        # Odczyt zdarzeń z dziennika zdarzeń
        events = win32evtlog.EvtNext(query_handle, expected_number_of_logs)

        read_count += len(events)  # Aktualizacja licznika odczytu
        # Jeśli nie ma rekordów, przerwij pętlę
        if len(events) == 0:
            break
        for event in events:
            # Renderowanie zdarzenia jako XML
            xml_content = win32evtlog.EvtRender(event, win32evtlog.EvtRenderEventXml)

            # Parsowanie zawartości XML
            xml = ET.fromstring(xml_content)
            ns = '{http://schemas.microsoft.com/win/2004/08/events/event}'  # Przestrzeń nazw XML
            # Wyciąganie istotnych informacji z XML
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
            # Wyświetlanie szczegółów logu
            print(
                f'Czas: {time_created}, Poziom: {level} Identyfikator zdarzenia: {event_id}, Kanał: {channel}, '
                f'ID procesu: {process_id}, ID wątku: {thread_id} Nazwa: {name}, GUID: {guid}, Nazwa źródła {source_name}')

            # Tworzenie słownika do przechowywania szczegółów logu
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
            # Analizowanie logu za pomocą modelu językowego
            answer = analyze_log_with_llm(record)
            record['chat_answer'] = answer  # Dodanie odpowiedzi modelu językowego do rekordu logu
            logs.append(record)  # Dodanie rekordu logu do listy

    # Wyświetlenie całkowitej liczby odczytanych rekordów
    print(f'Odczytano {read_count} rekordów')
    return logs  # Zwrócenie listy logów

# Funkcja do zapisywania logów do pliku CSV
def save_to_csv(logs, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['level', 'event_id', 'channel', 'process_id', 'thread_id', 'time_created', 'name', 'guid',
                      'source_name', 'chat_answer']  # Definicja nazw pól dla nagłówków CSV
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Zapisanie nagłówków CSV
        writer.writerows(logs)  # Zapisanie rekordów logów do pliku CSV

if __name__ == "__main__":
    #OpenAI
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

    # Pobranie logów systemowych
    logs = get_system_logs()

    # Zapisanie logów do pliku CSV
    save_to_csv(logs, 'system_logs.csv')

    print("Pobrano logi i zapisano do pliku csv o nazwie system_logs.csv")
