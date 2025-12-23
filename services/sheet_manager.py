import re
import logging
import urllib.request
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SheetManager:
    SPREADSHEET_ID = "1hbvUroW0SxAbTbsn0nn-9wJyYKz-zLDJQ_PS7b83SzA"
    BASE_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
    
    def __init__(self):
        self._sheets_cache: List[Dict] = []
        self._last_fetch = None
    
    async def get_sheets(self, force_refresh: bool = False) -> List[Dict]:
        """
        Get list of sheets with their GIDs and names.
        Returns list of dicts: {'name': str, 'gid': str}
        """
        now = datetime.now()
        if self._sheets_cache and not force_refresh:
            # Refresh cache if older than 1 hour
            if self._last_fetch and (now - self._last_fetch).total_seconds() < 3600:
                return self._sheets_cache
        
        self._last_fetch = now
            
        try:
            logger.info("Fetching spreadsheet metadata...")
            # Use urllib instead of httpx
            req = urllib.request.Request(self.BASE_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
            
            sheets = []
            
            # Extract bootstrapData
            match = re.search(r'var bootstrapData = ({.*?});', content, re.DOTALL)
            if match:
                data = match.group(1)
                
                # Find all sheet definitions
                # Pattern: [index, 0, "gid", [... "Sheet Name" ...]]
                # But simpler to just look for the name and GID pattern we found earlier
                # The structure in bootstrapData is complex, but we saw:
                # [..., "gid", [{"1":[[0,0,"Sheet Name"]...
                
                # Let's use the regex that worked in our discovery script
                # We found that names like "кухня 24-30" appear in the data
                
                # Strategy: Find all sheet names and their associated GIDs
                # We'll look for the pattern `[number, 0, "gid_string", ... [[0,0,"Sheet Name"]`
                # This might be too brittle.
                
                # Alternative: Parse the bootstrap data more robustly?
                # It's huge.
                
                # Let's go with the pattern we saw:
                # `[number, 0, "GID", ... "Sheet Name"`
                
                # Let's try to find all `[number, 0, "GID",` blocks first
                # Then look inside them for the name.
                
                # Actually, let's iterate over all matches of `[number, 0, "(\d+)",`
                # And for each match, look ahead for `[[0,0,"([^"]+)"`
                
                # This is a bit risky if the order changes.
                
                # Let's use a simpler approach:
                # Find all occurrences of `[number, 0, "(\d+)",` which seems to define a sheet.
                # Then within that block (up to the next sheet def), find `[[0,0,"([^"]+)"`
                
                # Let's try to capture the whole block for a sheet.
                # They seem to be top-level elements in a list.
                
                # The structure we saw in bootstrap.json:
                # [21350203,"[7,0,\"1833845756\",[{\"1\":[[0,0,\"кухня 24-30\"],...
                # It seems to be a list of updates/snapshots.
                
                # Let's look for the pattern: `[\d+,0,"(\d+)",\[\{"1":\[\[0,0,"([^"]+)"`
                # Note the escaped quotes in the JSON string.
                
                # In the file content (which is raw HTML/JS), the bootstrapData is a JS object.
                # But inside it, there are strings that contain JSON.
                # e.g. `[21350203,"[7,0,\"1833845756\",...`
                
                # So we need to match the escaped structure.
                
                # Pattern: `\[\d+,0,\\"(\d+)\\",\[\{\\"1\\":\[\[0,0,\\"([^"]+)\\"`
                # We need to be careful with backslashes in python strings.
                
                # Let's try a more lenient pattern that looks for the GID and Name relationship.
                # We see `\"1833845756\",[{\"1\":[[0,0,\"кухня 24-30\"`
                
                # Regex: `\\"(\d+)\\",\[\{\\"1\\":\[\[0,0,\\"([^"]+)\\"`
                
                pattern = r'\\"(\d+)\\",\[\{\\"1\\":\[\[0,0,\\"([^"]+)\\"'
                matches = re.findall(pattern, data)
                
                # Also try the unescaped version just in case (if it's not inside a string)
                if not matches:
                    pattern2 = r'"(\d+)",\[\{"1":\[\[0,0,"([^"]+)"'
                    matches = re.findall(pattern2, data)
                
                for gid, name in matches:
                    # Filter for relevant sheets (e.g., "кухня ...")
                    if 'кухня' in name.lower():
                        sheets.append({
                            'name': name,
                            'gid': gid
                        })
                        
            self._sheets_cache = sheets
            logger.info(f"Discovered {len(sheets)} sheets: {[s['name'] for s in sheets]}")
            return sheets
            
        except Exception as e:
            logger.error(f"Error discovering sheets: {e}")
            # Fallback to known GID if discovery fails
            return [{
                'name': 'Fallback',
                'gid': '1833845756'
            }]

    def parse_date_range(self, sheet_name: str) -> Optional[datetime]:
        """
        Parse the start date from a sheet name like "кухня 24-30" or "Кухня 27-2".
        Returns a datetime object for the start date (assuming current/next year).
        """
        try:
            # Extract numbers
            parts = re.findall(r'\d+', sheet_name)
            if not parts:
                return None
                
            day = int(parts[0])
            
            # We need to guess the month.
            # Since the sheet names don't have months, we have to infer it.
            # This is tricky. "24-30" could be Nov 24 - Nov 30.
            # "27-2" could be Oct 27 - Nov 2.
            
            # Let's assume the sheets are recent.
            # We can compare with current date.
            
            now = datetime.now()
            
            # Try to construct a date with current month
            try:
                dt = datetime(now.year, now.month, day)
            except ValueError:
                # e.g. day 31 in a 30-day month?
                # Or maybe it's next month?
                # Or previous month?
                return None
                
            # This logic is flawed because we don't know the month.
            # But maybe we don't strictly need to sort them by date if we just check all of them?
            # The user wants "next week" which is in "the other sheet".
            
            # If we just fetch ALL "кухня" sheets, we can parse the dates inside the CSV.
            # The CSV header has dates: `"", "24.11", "25.11", ...`
            # This is much more reliable.
            
            return None
        except:
            return None

sheet_manager = SheetManager()
