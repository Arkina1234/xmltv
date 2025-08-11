import requests
from datetime import datetime, timedelta
import json
from dateutil.parser import parse

class TVTVAPI:
    def __init__(self, lineup_id="USA-GNSTR-X"):
        self.base_url = "https://www.tvtv.us/api/v1"
        self.lineup_id = lineup_id
    
    def get_channel_grid(self, channel_id, days=3):
        """Get programming grid for a channel"""
        today = datetime.now()
        end_date = today + timedelta(days=days)
        
        url = f"{self.base_url}/lineup/{self.lineup_id}/grid/{today.isoformat()}/{end_date.isoformat()}/{channel_id}"
        response = requests.get(url)
        return response.json()
    
    def get_program_details(self, program_id):
        """Get detailed program information"""
        url = f"{self.base_url}/programs/{program_id}"
        response = requests.get(url)
        return response.json()

class XMLTVGenerator:
    @staticmethod
    def generate_xmltv(channels):
        """Generate XMLTV formatted output"""
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<!DOCTYPE tv SYSTEM "xmltv.dtd">\n'
        xml += '<tv source-info-url="https://www.tvtv.us" source-info-name="TVTV.us">\n'
        
        # Add channels
        for channel in channels:
            channel_id = channel['channel_id']
            xml += f'  <channel id="{channel_id}">\n'
            xml += f'    <display-name>{channel["channel_name"]}</display-name>\n'
            xml += '  </channel>\n'
            
            # Get program data
            api = TVTVAPI()
            grid = api.get_channel_grid(channel_id)
            
            # Add programs
            for program in grid.get('programs', []):
                start = parse(program['startTime']).strftime('%Y%m%d%H%M%S %z')
                end = parse(program['endTime']).strftime('%Y%m%d%H%M%S %z')
                
                xml += f'  <programme start="{start}" stop="{end}" channel="{channel_id}">\n'
                xml += f'    <title>{program["title"]}</title>\n'
                
                # Get additional program details
                details = api.get_program_details(program['programId'])
                if details.get('episodeTitle'):
                    xml += f'    <sub-title>{details["episodeTitle"]}</sub-title>\n'
                if details.get('shortDescription'):
                    xml += f'    <desc>{details["shortDescription"]}</desc>\n'
                if details.get('longDescription'):
                    xml += f'    <desc lang="en">{details["longDescription"]}</desc>\n'
                
                # Add categories if available
                for genre in details.get('genres', []):
                    xml += f'    <category>{genre}</category>\n'
                
                xml += '  </programme>\n'
        
        xml += '</tv>'
        return xml

# Example usage
if __name__ == "__main__":
    # Your channel data
    channels = [
        {
            "origin": "33453",
            "channel_name": "PBS HD",
            "channel_id": "33453"
        }
        # Add more channels as needed
    ]
    
    generator = XMLTVGenerator()
    xmltv_content = generator.generate_xmltv(channels)
    
    # Save to file
    with open('./guide/tvtv_guide.xml', 'w') as f:
        f.write(xmltv_content)
    
    print("XMLTV file generated successfully!")
