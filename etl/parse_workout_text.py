"""
Parser for OCR-extracted workout log data.
Uses coordinate/polygon data from Azure Document Intelligence to properly
associate exercises with their reps and weights from the table structure.
"""

import re
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
import json


def parse_date(text: str) -> Optional[datetime]:
    """Parse date from various formats."""
    patterns = [
        r'Date\s*:\s*(\d{1,2}/\d{1,2}/\d{2,4})',
        r'^(\d{1,2}/\d{1,2}/\d{2,4})\s*LIFTING',
        r'^(\d{1,2}/\d{1,2}/\d{2,4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            try:
                if len(date_str.split('/')[-1]) == 2:
                    return datetime.strptime(date_str, "%m/%d/%y").date()
                else:
                    return datetime.strptime(date_str, "%m/%d/%Y").date()
            except ValueError:
                continue
    return None


def parse_reps_value(text: str) -> Optional[Dict[str, Any]]:
    """Parse reps from text like '3×13', '4×25', '2 × 12', etc."""
    text = text.strip()
    
    if not text or text.upper() in ['REPS', '-', '--', '---']:
        return None
    
    # Pattern for sets × reps (handles ×, x, X with optional spaces)
    sets_reps_pattern = r'(\d+)\s*[×xX]\s*(\d+(?:-\d+)?)'
    match = re.search(sets_reps_pattern, text)
    
    if match:
        sets = int(match.group(1))
        reps_str = match.group(2)
        reps = int(reps_str.split('-')[0]) if '-' in reps_str else int(reps_str)
        
        each_side = bool(re.search(r'ea\.?|each', text, re.IGNORECASE))
        is_timed = bool(re.search(r'sec\.?|min\.?', text, re.IGNORECASE))
        
        return {
            'sets': sets,
            'reps': reps,
            'each_side': each_side,
            'is_timed': is_timed,
            'raw': text
        }
    
    return None


def parse_weight_value(text: str) -> Optional[Dict[str, Any]]:
    """Parse weight from text like '55 lbs', 'BW', 'Blue Band', etc."""
    text = text.strip()
    
    if not text or text.upper() in ['WEIGHT', '-', '--', '---', '']:
        return None
    
    # Body weight
    if re.search(r'\bBW\b|body\s*weight', text, re.IGNORECASE):
        return {'value': 0, 'unit': 'bodyweight', 'raw': text}
    
    # Resistance bands
    band_match = re.search(r'(blue|red|green|orange|black|olive)\s*band?', text, re.IGNORECASE)
    if band_match:
        return {'value': 0, 'unit': f'{band_match.group(1).lower()}_band', 'raw': text}
    
    # Just "band" without color
    if re.search(r'\bband\b', text, re.IGNORECASE):
        return {'value': 0, 'unit': 'band', 'raw': text}
    
    # Plates
    plates_match = re.search(r'(\d+)\s*plates?', text, re.IGNORECASE)
    if plates_match:
        return {'value': int(plates_match.group(1)), 'unit': 'plates', 'raw': text}
    
    # Bar only
    if re.search(r'\bbar\b', text, re.IGNORECASE) and not re.search(r'\d', text):
        return {'value': 45, 'unit': 'lbs', 'raw': text}
    
    # Numeric weight with "lbs" - be more specific to avoid confusion with reps
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lbs?\.?|pounds?|16s?\.?|165\.?|163\.?)', text, re.IGNORECASE)
    if weight_match:
        return {'value': float(weight_match.group(1)), 'unit': 'lbs', 'raw': text}
    
    # Just a number with no context - only if it's a reasonable weight (>= 10)
    just_number = re.match(r'^(\d+(?:\.\d+)?)\s*$', text)
    if just_number and float(just_number.group(1)) >= 10:
        return {'value': float(just_number.group(1)), 'unit': 'lbs', 'raw': text}
    
    return None


def get_line_bbox(line: Dict) -> Tuple[float, float, float, float]:
    """Get bounding box (left, top, right, bottom) from polygon."""
    polygon = line.get('polygon', [])
    if not polygon:
        return (0, 0, 0, 0)
    
    xs = [p.get('x', 0) for p in polygon]
    ys = [p.get('y', 0) for p in polygon]
    return (min(xs), min(ys), max(xs), max(ys))


def extract_table_rows_from_page(page: Dict) -> List[Dict[str, Any]]:
    """
    Extract exercises from a page by finding REPS and WEIGHT labels
    and associating them with nearby exercise names.
    """
    lines = page.get('lines', [])
    page_width = page.get('width', 6)
    
    if not lines:
        return []
    
    # Find page date
    page_date = None
    for line in lines:
        content = line.get('content', '')
        date = parse_date(content)
        if date:
            page_date = date
            break
    
    # Collect all text elements with their positions
    elements = []
    for line in lines:
        content = line.get('content', '').strip()
        if not content:
            continue
        
        left, top, right, bottom = get_line_bbox(line)
        center_y = (top + bottom) / 2
        center_x = (left + right) / 2
        
        elements.append({
            'content': content,
            'left': left,
            'top': top,
            'right': right,
            'bottom': bottom,
            'center_y': center_y,
            'center_x': center_x,
        })
    
    # Find REPS and WEIGHT label positions to understand column structure
    reps_labels = [e for e in elements if e['content'].upper() == 'REPS']
    weight_labels = [e for e in elements if e['content'].upper() == 'WEIGHT']
    
    if not reps_labels or not weight_labels:
        return []
    
    # Determine column boundaries based on REPS/WEIGHT label positions
    # Exercise column: 0 to first REPS label
    # REPS column: around REPS labels
    # WEIGHT column: around WEIGHT labels
    
    reps_x_positions = [e['center_x'] for e in reps_labels]
    weight_x_positions = [e['center_x'] for e in weight_labels]
    
    avg_reps_x = sum(reps_x_positions) / len(reps_x_positions) if reps_x_positions else 1.5
    avg_weight_x = sum(weight_x_positions) / len(weight_x_positions) if weight_x_positions else 2.2
    
    # Group elements into rows by y-coordinate
    Y_TOLERANCE = 0.2  # Lines within 0.2 inches are in the same row
    
    elements.sort(key=lambda e: e['center_y'])
    
    rows = []
    current_row = []
    current_y = None
    
    for elem in elements:
        if current_y is None or abs(elem['center_y'] - current_y) <= Y_TOLERANCE:
            current_row.append(elem)
            current_y = elem['center_y'] if current_y is None else (current_y + elem['center_y']) / 2
        else:
            if current_row:
                rows.append(current_row)
            current_row = [elem]
            current_y = elem['center_y']
    
    if current_row:
        rows.append(current_row)
    
    # Process each row to extract exercise + reps + weight
    exercises = []
    
    for row in rows:
        # Sort elements by x-position
        row.sort(key=lambda e: e['left'])
        
        # Find elements in each column
        exercise_parts = []
        reps_parts = []
        weight_parts = []
        
        # Determine column boundaries for this row
        # Exercise column: left < avg_reps_x - 0.3
        # REPS column: avg_reps_x - 0.3 < center < avg_weight_x - 0.3
        # WEIGHT column: center > avg_weight_x - 0.3
        
        for elem in row:
            content = elem['content']
            cx = elem['center_x']
            
            # Skip labels and section headers
            if content.upper() in ['REPS', 'WEIGHT', 'LIFTING', 'CARDIO', 'NOTES', 
                                    'ACTIVITY LOG', 'WATER INTAKE', 'WATER INTAKE:',
                                    'ACTIVITY/TIME', '-', '--', '---']:
                continue
            
            # Skip if in right side (cardio section)
            if elem['left'] > 3.5:
                continue
            
            # Classify by x-position
            if cx < avg_reps_x - 0.3:
                # This is in the exercise column
                # But first check if it looks like a reps or weight value
                if parse_reps_value(content):
                    # Looks like reps value in wrong column
                    reps_parts.append(content)
                elif parse_weight_value(content) and re.match(r'^\d+\s*lbs', content, re.IGNORECASE):
                    weight_parts.append(content)
                else:
                    exercise_parts.append(content)
            elif cx < avg_weight_x - 0.3:
                # REPS column
                reps_parts.append(content)
            else:
                # WEIGHT column
                weight_parts.append(content)
        
        # Combine exercise name
        exercise_name = ' '.join(exercise_parts).strip()
        
        # Clean up exercise name
        if not exercise_name:
            continue
        
        # Skip various non-exercise entries
        if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}', exercise_name):
            continue
        if exercise_name.upper() in ['LIFTING', 'CARDIO', 'NOTES', 'ACTIVITY LOG']:
            continue
        if re.match(r'^[>\+\-\*]', exercise_name):  # Notes markers
            continue
        if len(exercise_name) <= 2:
            continue
        
        # Parse reps
        reps_info = None
        for reps_text in reps_parts:
            parsed = parse_reps_value(reps_text)
            if parsed:
                reps_info = parsed
                break
        
        # Parse weight
        weight_info = None
        for weight_text in weight_parts:
            parsed = parse_weight_value(weight_text)
            if parsed:
                weight_info = parsed
                break
        
        exercises.append({
            'date': page_date,
            'name': exercise_name,
            'reps_info': reps_info,
            'weight_info': weight_info,
        })
    
    return exercises


def extract_cardio_from_page(page: Dict) -> List[Dict[str, Any]]:
    """Extract cardio activities from a page."""
    lines = page.get('lines', [])
    
    # Find date
    page_date = None
    for line in lines:
        date = parse_date(line.get('content', ''))
        if date:
            page_date = date
            break
    
    cardio_activities = []
    
    # Find lines in the CARDIO section (right side of page)
    for line in lines:
        left, top, right, bottom = get_line_bbox(line)
        content = line.get('content', '').strip()
        
        if left > 3.5:
            # Look for cardio patterns
            if re.search(r'(run|running|cycling|bike|biking|walk|swim)', content, re.IGNORECASE):
                activity = {
                    'date': page_date,
                    'activity': None,
                    'distance': None,
                    'duration': None,
                    'pace': None,
                    'raw': content
                }
                
                # Extract activity type
                if re.search(r'run', content, re.IGNORECASE):
                    activity['activity'] = 'running'
                elif re.search(r'cycl|bike', content, re.IGNORECASE):
                    activity['activity'] = 'cycling'
                elif re.search(r'walk', content, re.IGNORECASE):
                    activity['activity'] = 'walking'
                
                # Extract distance
                dist_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:mi|mile)', content, re.IGNORECASE)
                if dist_match:
                    activity['distance'] = float(dist_match.group(1))
                
                # Extract duration
                dur_match = re.search(r'(\d+)\s*(?:min|hr)', content, re.IGNORECASE)
                if dur_match:
                    activity['duration'] = int(dur_match.group(1))
                
                # Extract pace
                pace_match = re.search(r'@\s*([\d:]+)', content)
                if pace_match:
                    activity['pace'] = pace_match.group(1)
                
                cardio_activities.append(activity)
    
    return cardio_activities


def ocr_json_to_df(ocr_json: Dict[str, Any]) -> pd.DataFrame:
    """Main function to convert OCR JSON to a structured DataFrame."""
    pages = ocr_json.get("pages", [])
    
    if not pages:
        return pd.DataFrame()
    
    all_rows = []
    
    for page in pages:
        # Extract exercises from this page
        exercises = extract_table_rows_from_page(page)
        
        for ex in exercises:
            row = {
                'date': ex['date'],
                'exercise': ex['name'],
                'sets': None,
                'reps': None,
                'each_side': False,
                'is_timed': False,
                'weight': None,
                'weight_unit': None,
                'reps_raw': None,
                'weight_raw': None,
            }
            
            if ex['reps_info']:
                row['sets'] = ex['reps_info'].get('sets')
                row['reps'] = ex['reps_info'].get('reps')
                row['each_side'] = ex['reps_info'].get('each_side', False)
                row['is_timed'] = ex['reps_info'].get('is_timed', False)
                row['reps_raw'] = ex['reps_info'].get('raw')
            
            if ex['weight_info']:
                row['weight'] = ex['weight_info'].get('value')
                row['weight_unit'] = ex['weight_info'].get('unit')
                row['weight_raw'] = ex['weight_info'].get('raw')
            
            all_rows.append(row)
        
        # Extract cardio
        cardio_activities = extract_cardio_from_page(page)
        for cardio in cardio_activities:
            row = {
                'date': cardio['date'],
                'exercise': f"CARDIO: {cardio.get('activity', 'activity')}",
                'sets': None,
                'reps': None,
                'each_side': False,
                'is_timed': True,
                'weight': None,
                'weight_unit': None,
                'reps_raw': None,
                'weight_raw': None,
                'cardio_distance': cardio.get('distance'),
                'cardio_duration': cardio.get('duration'),
                'cardio_pace': cardio.get('pace'),
                'cardio_raw': cardio.get('raw'),
            }
            all_rows.append(row)
    
    df = pd.DataFrame(all_rows)
    
    # Ensure consistent columns
    expected_cols = [
        'date', 'exercise', 'sets', 'reps', 'each_side', 'is_timed',
        'weight', 'weight_unit', 'reps_raw', 'weight_raw',
        'cardio_distance', 'cardio_duration', 'cardio_pace', 'cardio_raw'
    ]
    
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None
    
    return df[expected_cols]


def process_all_ocr_files(ocr_dir: str = "data_samples/ocr_outputs") -> pd.DataFrame:
    """Process all OCR JSON files and combine into one DataFrame."""
    import os
    
    all_dfs = []
    
    for filename in sorted(os.listdir(ocr_dir)):
        if filename.endswith('.json'):
            filepath = os.path.join(ocr_dir, filename)
            print(f"Processing: {filename}")
            
            with open(filepath, 'r') as f:
                ocr_json = json.load(f)
            
            df = ocr_json_to_df(ocr_json)
            df['source_file'] = filename
            all_dfs.append(df)
    
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        # Sort by date and exercise
        combined_df = combined_df.sort_values(['date', 'exercise']).reset_index(drop=True)
        # Remove duplicates
        combined_df = combined_df.drop_duplicates(
            subset=['date', 'exercise', 'sets', 'reps', 'weight'],
            keep='first'
        ).reset_index(drop=True)
        return combined_df
    
    return pd.DataFrame()


if __name__ == "__main__":
    # Process all OCR files
    df = process_all_ocr_files()
    
    if len(df) > 0:
        print(f"\nTotal rows extracted: {len(df)}")
        
        # Handle dates safely
        df_with_dates = df[df['date'].notna()]
        if len(df_with_dates) > 0:
            min_date = df_with_dates['date'].min()
            max_date = df_with_dates['date'].max()
            print(f"Date range: {min_date} to {max_date}")
            print(f"Sessions with dates: {df_with_dates['date'].nunique()}")
        
        # Count exercises with data
        has_reps = df['sets'].notna().sum()
        has_weight = df['weight'].notna().sum()
        print(f"Exercises with reps data: {has_reps}")
        print(f"Exercises with weight data: {has_weight}")
        
        # Filter for actual exercises
        exercise_df = df[~df['exercise'].str.startswith('CARDIO', na=False)]
        unique_exercises = exercise_df['exercise'].nunique()
        print(f"Unique exercises: {unique_exercises}")
        
        # Show sample with complete data
        sample_cols = ['date', 'exercise', 'sets', 'reps', 'weight', 'weight_unit', 'reps_raw', 'weight_raw']
        
        print("\n=== Sample exercises with reps data ===")
        with_reps = df[df['sets'].notna()][sample_cols].head(30)
        print(with_reps.to_string())
        
        print("\n=== Sample exercises with weight data ===")
        with_weight = df[df['weight'].notna()][sample_cols].head(30)
        print(with_weight.to_string())
        
        # Save to CSV
        output_path = "data_samples/parsed_workouts.csv"
        df.to_csv(output_path, index=False)
        print(f"\nSaved to {output_path}")
        
        # Also save a summary by exercise
        exercise_summary = df.groupby('exercise').agg({
            'date': 'count',
            'sets': lambda x: x.notna().sum(),
            'weight': lambda x: x.notna().sum()
        }).rename(columns={'date': 'occurrences', 'sets': 'has_reps', 'weight': 'has_weight'})
        exercise_summary = exercise_summary.sort_values('occurrences', ascending=False)
        
        summary_path = "data_samples/exercise_summary.csv"
        exercise_summary.to_csv(summary_path)
        print(f"Saved exercise summary to {summary_path}")
    else:
        print("No data extracted!")
