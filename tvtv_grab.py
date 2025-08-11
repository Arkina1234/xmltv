import requests
import json
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom

class XMLTVGenerator:
    def __init__(self):
        self.cors_proxy = "https://cors-anywhere.com/"
        self.base_url = "https://www.tvtv.us/api/v1/"
        self.lineup = "USA-GNSTR-X"
        self.channels_file = "./channels/tvtv.channels.json"
        self.output_file = "./guide/tvguide.xml"
        
    def generate_xmltv(self):
        """Main function to generate XMLTV file"""
        try:
            # Load channels data
            channels = self._load_channels()
            
            # Create XMLTV root element
            tv = self._create_xmltv_root()
            
            # Add channels to XML
            for channel in channels:
                self._add_channel_element(tv, channel)
            
            # Get program data for each channel
            for channel in channels:
                self._add_programmes(tv, channel)
            
            # Save XML to file
            self._save_xml(tv)
            print(f"Successfully generated XMLTV file: {self.output_file}")
            
        except Exception as e:
            print(f"Error generating XMLTV: {e}")

    def _load_channels(self):
        """Load channels from JSON file"""
        with open(self.channels_file) as f:
            return json.load(f)

    def _create_xmltv_root(self):
        """Create the root TV element with proper attributes"""
        tv = ET.Element('tv')
        tv.set('source-info-url', 'https://www.tvtv.us/')
        tv.set('source-info-name', 'TVTV.us')
        tv.set('generator-info-name', 'XMLTV Python Generator')
        return tv

    def _add_channel_element(self, tv, channel):
        """Add channel element to XML"""
        channel_elem = ET.SubElement(tv, 'channel')
        channel_elem.set('id', channel['channel_id'])
        
        display_name = ET.SubElement(channel_elem, 'display-name')
        display_name.text = channel['channel_name']
        
        # Optional: Add icon element if available
        # icon = ET.SubElement(channel_elem, 'icon')
        # icon.set('src', channel.get('icon_url', ''))

    def _add_programmes(self, tv, channel):
        """Add programme elements for a channel"""
        try:
            # Get current date and next day
            today = datetime.utcnow()
            tomorrow = today + timedelta(days=1)
            
            # Format dates for API request
            start_time = today.strftime('%Y-%m-%dT04:00:00.000Z')
            end_time = tomorrow.strftime('%Y-%m-%dT03:59:59.000Z')
            
            # Construct API URL with CORS proxy
            url = f"{self.cors_proxy}{self.base_url}lineup/{self.lineup}/grid/{start_time}/{end_time}/{channel['site_id']}"
            
            print(f"Fetching programs for {channel['channel_name']}...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            programs = response.json()
            
            for program in programs:
                self._add_programme_element(tv, channel, program)
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching programs for {channel['channel_name']}: {e}")

    def _add_programme_element(self, tv, channel, program):
        """Add individual programme element"""
        try:
            # Fetch detailed program info
            program_url = f"{self.cors_proxy}https://tvtv.us/api/v1/programs/{program['programId']}"
            program_detail = requests.get(program_url, timeout=10).json()
            
            # Create programme element
            programme = ET.SubElement(tv, 'programme')
            programme.set('start', self._format_time(program['startTime']))
            programme.set('stop', self._format_time(program['endTime']))
            programme.set('channel', channel['channel_id'])
            
            # Add title
            title = ET.SubElement(programme, 'title')
            title.set('lang', 'en')
            title.text = program_detail.get('title', 'Unknown Program')
            
            # Add description if available
            if 'description' in program_detail:
                desc = ET.SubElement(programme, 'desc')
                desc.set('lang', 'en')
                desc.text = program_detail['description']
            
            # Add episode title if available
            if 'episodeTitle' in program_detail and program_detail['episodeTitle']:
                sub_title = ET.SubElement(programme, 'sub-title')
                sub_title.set('lang', 'en')
                sub_title.text = program_detail['episodeTitle']
            
            # Add categories/genres if available
            if 'genres' in program_detail:
                for genre in program_detail['genres']:
                    category = ET.SubElement(programme, 'category')
                    category.set('lang', 'en')
                    category.text = genre
            
            # Add episode information if available
            if 'seasonNumber' in program_detail and 'episodeNumber' in program_detail:
                episode_num = f"{program_detail['seasonNumber']}.{program_detail['episodeNumber']}."
                episode_elem = ET.SubElement(programme, 'episode-num')
                episode_elem.set('system', 'onscreen')
                episode_elem.text = episode_num
            
        except Exception as e:
            print(f"Error processing program {program.get('programId')}: {e}")

    def _format_time(self, timestamp):
        """Convert timestamp to XMLTV format (UTC)"""
        dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime('%Y%m%d%H%M%S +0000')

    def _save_xml(self, tv_element):
        """Save XML to file with proper formatting"""
        rough_string = ET.tostring(tv_element, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

if __name__ == '__main__':
    generator = XMLTVGenerator()
    generator.generate_xmltv()