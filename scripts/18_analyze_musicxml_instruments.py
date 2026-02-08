#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze MusicXML files to extract instrument information
Helps determine instrument mapping for realistic sound synthesis
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter, defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "manual"  # MusicXML files are in data/manual/

def parse_musicxml_instruments(xml_path):
    """Extract instrument information from MusicXML file."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        instruments = []
        
        # MusicXML namespace handling
        ns = {'': 'http://www.musicxml.org/xsd/MusicXML'}
        
        # Try without namespace first
        score_parts = root.findall('.//score-part')
        if not score_parts:
            # Try with namespace
            score_parts = root.findall('.//{http://www.musicxml.org/xsd/MusicXML}score-part', ns)
        
        for part in score_parts:
            part_id = part.get('id', 'unknown')
            
            # Get part name
            part_name_elem = part.find('part-name')
            if part_name_elem is None:
                part_name_elem = part.find('.//{http://www.musicxml.org/xsd/MusicXML}part-name')
            part_name = part_name_elem.text if part_name_elem is not None else 'Unknown'
            
            # Get instrument name (if specified)
            score_instrument = part.find('.//score-instrument')
            if score_instrument is None:
                score_instrument = part.find('.//{http://www.musicxml.org/xsd/MusicXML}score-instrument')
            
            instrument_name = None
            if score_instrument is not None:
                inst_name_elem = score_instrument.find('instrument-name')
                if inst_name_elem is None:
                    inst_name_elem = score_instrument.find('.//{http://www.musicxml.org/xsd/MusicXML}instrument-name')
                instrument_name = inst_name_elem.text if inst_name_elem is not None else None
            
            # Get MIDI program/instrument
            midi_instrument = part.find('.//midi-instrument')
            if midi_instrument is None:
                midi_instrument = part.find('.//{http://www.musicxml.org/xsd/MusicXML}midi-instrument')
            
            midi_program = None
            midi_channel = None
            if midi_instrument is not None:
                program_elem = midi_instrument.find('midi-program')
                if program_elem is None:
                    program_elem = midi_instrument.find('.//{http://www.musicxml.org/xsd/MusicXML}midi-program')
                
                channel_elem = midi_instrument.find('midi-channel')
                if channel_elem is None:
                    channel_elem = midi_instrument.find('.//{http://www.musicxml.org/xsd/MusicXML}midi-channel')
                
                if program_elem is not None:
                    try:
                        midi_program = int(program_elem.text)
                    except (ValueError, TypeError):
                        pass
                
                if channel_elem is not None:
                    try:
                        midi_channel = int(channel_elem.text)
                    except (ValueError, TypeError):
                        pass
            
            instruments.append({
                'part_id': part_id,
                'part_name': part_name,
                'instrument_name': instrument_name,
                'midi_program': midi_program,
                'midi_channel': midi_channel
            })
        
        return instruments
    
    except Exception as e:
        print(f"Error parsing {xml_path.name}: {e}")
        return []

def normalize_instrument_name(name):
    """Normalize instrument names for mapping."""
    if not name:
        return "Unknown"
    
    name = name.strip().lower()
    
    # Common abbreviations
    abbrev_map = {
        'kl.': 'klavier',
        'kl': 'klavier',
        's.': 'sopran',
        's': 'sopran',
        'a.': 'alt',
        'a': 'alt',
        't.': 'tenor',
        't': 'tenor',
        'b.': 'bass',
        'b': 'bass',
        'instr.': 'instrument',
    }
    
    for abbrev, full in abbrev_map.items():
        if name == abbrev or name.startswith(abbrev + ' '):
            return full
    
    return name

def get_general_midi_instrument_name(program):
    """Map MIDI program number to General MIDI instrument name."""
    # General MIDI instrument mapping (0-127)
    gm_instruments = {
        0: "Acoustic Grand Piano",
        1: "Bright Acoustic Piano",
        2: "Electric Grand Piano",
        3: "Honky-tonk Piano",
        4: "Electric Piano 1",
        5: "Electric Piano 2",
        6: "Harpsichord",
        7: "Clavinet",
        # Chromatic Percussion (8-15)
        8: "Celesta",
        9: "Glockenspiel",
        10: "Music Box",
        11: "Vibraphone",
        12: "Marimba",
        13: "Xylophone",
        14: "Tubular Bells",
        15: "Dulcimer",
        # Organ (16-23)
        16: "Drawbar Organ",
        17: "Percussive Organ",
        18: "Rock Organ",
        19: "Church Organ",
        20: "Reed Organ",
        21: "Accordion",
        22: "Harmonica",
        23: "Tango Accordion",
        # Guitar (24-31)
        24: "Acoustic Guitar (nylon)",
        25: "Acoustic Guitar (steel)",
        26: "Electric Guitar (jazz)",
        27: "Electric Guitar (clean)",
        28: "Electric Guitar (muted)",
        29: "Overdriven Guitar",
        30: "Distortion Guitar",
        31: "Guitar harmonics",
        # ... (can be extended)
        73: "Flute",
        74: "Recorder",
        75: "Pan Flute",
        76: "Blown Bottle",
        77: "Shakuhachi",
        78: "Whistle",
        79: "Ocarina"
    }
    
    return gm_instruments.get(program, f"Program {program}")

def main():
    print("=" * 80)
    print("MUSICXML INSTRUMENT ANALYSIS")
    print("=" * 80)
    print()
    
    if not DATA_DIR.exists():
        print(f"ERROR: MusicXML directory not found: {DATA_DIR}")
        print("Please ensure MusicXML files are in: data/musicxml/")
        return
    
    # Find all MusicXML files
    xml_files = list(DATA_DIR.glob("*.xml")) + list(DATA_DIR.glob("*.musicxml"))
    
    if not xml_files:
        print(f"No MusicXML files found in: {DATA_DIR}")
        return
    
    print(f"Found {len(xml_files)} MusicXML files\n")
    
    # Analysis results
    all_instruments = []
    work_instruments = {}
    instrument_names = Counter()
    normalized_names = Counter()
    midi_programs = Counter()
    
    # Analyze each file
    for xml_file in sorted(xml_files):
        print(f"\n{'='*80}")
        print(f"File: {xml_file.name}")
        print(f"{'='*80}")
        
        instruments = parse_musicxml_instruments(xml_file)
        
        if not instruments:
            print("  No instruments found or parsing error")
            continue
        
        work_instruments[xml_file.stem] = instruments
        
        for inst in instruments:
            all_instruments.append(inst)
            
            # Count original names
            if inst['part_name']:
                instrument_names[inst['part_name']] += 1
            
            # Count normalized names
            normalized = normalize_instrument_name(inst['part_name'])
            normalized_names[normalized] += 1
            
            # Count MIDI programs
            if inst['midi_program'] is not None:
                midi_programs[inst['midi_program']] += 1
            
            # Display
            print(f"\n  Part: {inst['part_id']}")
            print(f"    Name: {inst['part_name']}")
            print(f"    Normalized: {normalized}")
            if inst['instrument_name']:
                print(f"    Instrument: {inst['instrument_name']}")
            if inst['midi_program'] is not None:
                gm_name = get_general_midi_instrument_name(inst['midi_program'])
                print(f"    MIDI Program: {inst['midi_program']} ({gm_name})")
            if inst['midi_channel'] is not None:
                print(f"    MIDI Channel: {inst['midi_channel']}")
    
    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\nTotal instruments found: {len(all_instruments)}")
    print(f"Total unique works: {len(work_instruments)}")
    
    print(f"\n\nMost common instrument names:")
    print("-" * 80)
    for name, count in instrument_names.most_common(20):
        normalized = normalize_instrument_name(name)
        print(f"  {name:30} → {normalized:20} ({count}x)")
    
    print(f"\n\nNormalized instrument distribution:")
    print("-" * 80)
    for name, count in normalized_names.most_common():
        print(f"  {name:30} ({count}x)")
    
    if midi_programs:
        print(f"\n\nMIDI Program usage:")
        print("-" * 80)
        for program, count in sorted(midi_programs.items()):
            gm_name = get_general_midi_instrument_name(program)
            print(f"  Program {program:3d}: {gm_name:30} ({count}x)")
    
    # Recommendations
    print(f"\n\n" + "=" * 80)
    print("RECOMMENDATIONS FOR IMPLEMENTATION")
    print("=" * 80)
    
    print("\n1. INSTRUMENT MAPPING STRATEGY:")
    print("   Create a mapping from normalized names to sound samples/synths")
    print("   Priority instruments (by frequency):")
    for name, count in list(normalized_names.most_common(10)):
        print(f"     - {name} ({count} occurrences)")
    
    print("\n2. ABBREVIATION HANDLING:")
    print("   Detected abbreviations that need expansion:")
    abbrevs = set()
    for name in instrument_names.keys():
        if name and (name.endswith('.') or len(name) <= 3):
            abbrevs.add(name)
    for abbrev in sorted(abbrevs):
        normalized = normalize_instrument_name(abbrev)
        print(f"     '{abbrev}' → '{normalized}'")
    
    print("\n3. SOUNDFONT APPROACH:")
    print("   Option A: Use General MIDI SoundFont (covers all MIDI programs)")
    print("   Option B: Custom sample library for common instruments")
    print("   Option C: Hybrid (SoundFont for fallback, custom for key instruments)")
    
    print("\n4. IMPLEMENTATION PRIORITY:")
    print("   Phase 1: Piano/Klavier (most common)")
    print("   Phase 2: Blockflöten (Sopran, Alt, Tenor)")
    print("   Phase 3: Orgel")
    print("   Phase 4: Other instruments via SoundFont fallback")
    
    # Save detailed report
    report_path = BASE_DIR / "data" / "musicxml_instrument_analysis.json"
    report = {
        "total_files": len(xml_files),
        "total_instruments": len(all_instruments),
        "instrument_names": dict(instrument_names),
        "normalized_names": dict(normalized_names),
        "midi_programs": dict(midi_programs),
        "work_instruments": {k: v for k, v in work_instruments.items()}
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n✅ Detailed report saved to: {report_path}")
    print()

if __name__ == "__main__":
    main()
