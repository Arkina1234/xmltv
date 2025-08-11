import requests
import json
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_xmltv():
    # Load channels data
    with open('./channels/tvtv.channels.json') as f:
        channels = json.load(f)
    
    # Create XMLTV root element
    tv = ET.Element('tv')
    tv.set('source-info-url', 'https://www.tvtv.us/')
    tv.set('source-info-name', 'TVTV.us')
    tv.set('generator-info-name', 'XMLTV Python Script')
    tv.set('generator-info-url', '')
    
    # Add channels
    for channel in channels:
        channel_elem = ET.SubElement(tv, 'channel')
        channel_elem.set('id', channel['channel_id'])
        
        display_name = ET.SubElement(channel_elem, 'display-name')
        display_name.text = channel['channel_name']
    
    # Get current date and next day
    today = datetime.utcnow()
    tomorrow = today + timedelta(days=1)
    
    # Format dates for API
    start_time = today.replace(hour=4, minute=0, second=0, microsecond=0).isoformat() + '.000Z'
    end_time = tomorrow.replace(hour=3, minute=59, second=59, microsecond=0).isoformat() + '.000Z'
    
    # Fetch program data for each channel
    for channel in channels:
        # Construct API URL with CORS proxy
        url = f"https://cors-anywhere.com/https://www.tvtv.us/api/v1/lineup/USA-GNSTR-X/grid/{start_time}/{end_time}/{channel['site_id']}"
        
        try:
            print(f"Fetching data for {channel['channel_name']}...")
            response = requests.get(url, headers={'X-Requested-With': 'XMLHttpRequest'})
            response.raise_for_status()
            programs = response.json()
            
            for program in programs:
                # Fetch detailed program info
                program_url = f"https://cors-anywhere.com/https://tvtv.us/api/v1/programs/{program['programId']}"
                try:
                    program_detail = requests.get(program_url, headers={'X-Requested-With': 'XMLHttpRequest'}).json()
                    
                    # Create program element
                    programme = ET.SubElement(tv, 'programme')
                    programme.set('start', format_time(program['startTime']))
                    programme.set('stop', format_time(program['endTime']))
                    programme.set('channel', channel['channel_id'])
                    
                    # Add program details
                    title = ET.SubElement(programme, 'title')
                    title.set('lang', 'en')
                    title.text = program_detail.get('title', 'Unknown')
                    
                    if 'description' in program_detail:
                        desc = ET.SubElement(programme, 'desc')
                        desc.set('lang', 'en')
                        desc.text = program_detail['description']
                    
                    if 'episodeTitle' in program_detail and program_detail['episodeTitle']:
                        sub_title = ET.SubElement(programme, 'sub-title')
                        sub_title.set('lang', 'en')
                        sub_title.text = program_detail['episodeTitle']
                    
                    # Add categories if available
                    if 'genres' in program_detail:
                        for genre in program_detail['genres']:
                            category = ET.SubElement(programme, 'category')
                            category.set('lang', 'en')
                            category.text = genre
                    
                    # Add episode info if available
                    if 'seasonNumber' in program_detail and 'episodeNumber' in program_detail:
                        episode_num = ET.SubElement(programme, 'episode-num')
                        episode_num.set('system', 'onscreen')
                        episode_num.text = f"S{program_detail['seasonNumber']}E{program_detail['episodeNumber']}"
                    
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching program details for {program.get('programId')}: {e}")
                    continue
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {channel['channel_name']}: {e}")
            continue
    
    # Generate XML string
    rough_string = ET.tostring(tv, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Save to file
    with open('./guide/tvguide.xml', 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    print("XMLTV file generated successfully!")

def format_time(timestamp):
    # Convert timestamp to XMLTV format
    dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
    return dt.strftime('%Y%m%d%H%M%S +0000')

if __name__ == '__main__':
    generate_xmltv()